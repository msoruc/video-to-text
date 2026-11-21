def find_turns(audio, assets, speaker_count=None):
    import sherpa_onnx as so

    config = so.OfflineSpeakerDiarizationConfig(
        segmentation=so.OfflineSpeakerSegmentationModelConfig(
            pyannote=so.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(assets / "segmentation.onnx"))),
        embedding=so.SpeakerEmbeddingExtractorConfig(model=str(assets / "speaker.onnx")),
        clustering=so.FastClusteringConfig(num_clusters=speaker_count or -1, threshold=0.5),
        min_duration_on=0.3, min_duration_off=0.5,
    )
    if not config.validate():
        raise RuntimeError("The bundled speaker models could not be loaded.")
    detector = so.OfflineSpeakerDiarization(config)
    return detector.process(audio).sort_by_start_time()


def timestamp(ticks):
    seconds, fraction = divmod(ticks, 100)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{fraction:02}"


def voice_regions(turns, samples):
    # Convert overlapping detections to one timeline. A brief interruption can
    # end before the original voice resumes. Decode each audio sample only once.
    events = []
    for i, turn in enumerate(turns):
        start = max(0, round(turn.start * 16000))
        end = min(samples, round(turn.end * 16000))
        if start < end:
            events.extend([(start, True, i, turn.speaker), (end, False, i, turn.speaker)])
    active = {}
    spans = []
    previous = 0
    for position, entering, key, speaker in sorted(events):
        if active and position > previous:
            voice = next(reversed(active.values()))
            if spans and spans[-1][2] == voice and previous - spans[-1][1] <= 24000:
                spans[-1][1] = position
            else:
                spans.append([previous, position, voice])
        if entering:
            active[key] = speaker
        else:
            active.pop(key, None)
        previous = position
    return spans


def refine_turns(audio, spans, assets):
    import numpy as np
    import sherpa_onnx as so

    # Compare a short utterance to longer examples of both voices. A nearby
    # turn alone is insufficient evidence to overwrite a genuine interjection.
    candidates = []
    references = {}
    for i, (start, end, voice) in enumerate(spans):
        if end - start >= 32000:
            references.setdefault(voice, []).append((start, end))
        if 8000 <= end - start < 32000:
            neighbors = set()
            if i and start - spans[i - 1][1] <= 4000:
                neighbors.add(spans[i - 1][2])
            if i + 1 < len(spans) and spans[i + 1][0] - end <= 4000:
                neighbors.add(spans[i + 1][2])
            neighbors.discard(voice)
            if neighbors:
                candidates.append((i, neighbors))
    boundaries = [i for i in range(1, len(spans))
                  if spans[i][0] - spans[i - 1][1] <= 4000
                  and spans[i][2] != spans[i - 1][2]]
    if not (candidates or boundaries) or len(references) < 2:
        return spans

    extractor = so.SpeakerEmbeddingExtractor(so.SpeakerEmbeddingExtractorConfig(
        model=str(assets / "speaker.onnx")))

    def embedding(start, end):
        stream = extractor.create_stream()
        stream.accept_waveform(16000, audio[start:end])
        stream.input_finished()
        if extractor.is_ready(stream):
            vector = np.asarray(extractor.compute(stream))
            norm = np.linalg.norm(vector)
            if norm > 0:
                return vector / norm
        return None

    profiles = {}
    for voice, examples in references.items():
        vectors = []
        for start, end in sorted(examples, key=lambda t: t[1] - t[0], reverse=True)[:4]:
            middle = (start + end) // 2
            vector = embedding(max(start, middle - 48000), min(end, middle + 48000))
            if vector is not None:
                vectors.append(vector)
        if vectors:
            mean = np.mean(vectors, axis=0)
            profiles[voice] = mean / max(np.linalg.norm(mean), 1e-10)

    revised = [list(span) for span in spans]
    for i, neighbors in candidates:
        start, end, voice = spans[i]
        if voice not in profiles or not neighbors.intersection(profiles):
            continue
        vector = embedding(start, end)
        if vector is None:
            continue
        scores = {key: float(vector @ profile) for key, profile in profiles.items()}
        best = max(scores, key=scores.get)
        if best in neighbors and scores[best] >= 0.4 and scores[best] > scores[voice] + 0.1:
            revised[i][2] = best

    # Diarization can put a boundary inside an utterance. Compare one-second
    # windows on either side against both profiles and look for a sustained
    # transition. Quiet windows carry no speaker evidence.
    hop = 4000
    for i in boundaries:
        left, right = revised[i - 1], revised[i]
        if left[2] == right[2] or left[2] not in profiles or right[2] not in profiles:
            continue
        original = (left[1] + right[0]) // 2
        centers = range(max(original - 40000, left[0] + 8000),
                        min(original + 40000, right[1] - 8000) + 1, hop)
        evidence = []
        for center in centers:
            local = audio[center - 1600:center + 1600]
            value = 0.0
            if np.mean(local * local) > 1e-7:
                vec = embedding(center - 8000, center + 8000)
                if vec is not None:
                    value = float(vec @ (profiles[left[2]] - profiles[right[2]]))
            evidence.append(value)
        if len(evidence) < 5:
            continue
        # Prefix sums score a single left-to-right change. Require support on
        # both sides and a measurable improvement over the original boundary.
        cumulative = np.cumsum([0.0, *evidence])
        k = int(np.argmax(cumulative))
        old = sum(c < original for c in centers)
        if k < 2 or k > len(centers) - 2 or cumulative[k] - cumulative[old] < 0.25:
            continue
        if max(evidence[:k]) < 0.1 or min(evidence[k:]) > -0.1:
            continue
        cut = centers[k] - hop // 2
        # Put the cut at the quietest 40 ms nearby to avoid clipping a word.
        probe = range(cut - hop, cut + hop + 1, 160)
        cut = min(probe, key=lambda t: float(np.mean(audio[t-320:t+320] ** 2)))
        left[1] = right[0] = cut

    merged = []
    for start, end, voice in revised:
        if merged and merged[-1][2] == voice and start - merged[-1][1] <= 4000:
            merged[-1][1] = end
        else:
            merged.append([start, end, voice])
    return merged


def transcribe_turns(model, audio, spans):
    import numpy as np

    if not spans:
        # Preserve transcription when speech is too faint or brief to identify.
        spans = [(0, len(audio), None)]
    labels = {}
    lines = []
    for i, (start, end, voice) in enumerate(spans):
        prev_end = spans[i - 1][1] if i else 0
        next_start = spans[i + 1][0] if i + 1 < len(spans) else len(audio)
        left = max(0, start - 3200, (prev_end + start) // 2)
        right = min(len(audio), end + 3200, (end + next_start) // 2)
        clip = audio[left:right]
        # whisper.cpp needs at least a second even for short interjections.
        if len(clip) < 16000:
            clip = np.pad(clip, (0, 16000 - len(clip)))
        segments = sorted(model.transcribe(clip), key=lambda s: (s.t0, s.t1))
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            a = min(end, max(start, left + 160 * segment.t0))
            b = min(end, max(a, left + 160 * segment.t1))
            if voice is None:
                label = "Speaker unclear"
            else:
                label = labels.setdefault(voice, f"Speaker {len(labels) + 1}")
            lines.append(f"[{timestamp(round(a / 160))} – {timestamp(round(b / 160))}] {label}: {text}")
    return "\n".join(lines)
