# Install and use Video to Text

## Install on a Mac

Download the Apple silicon DMG from the [release downloads](https://github.com/msoruc/video-to-text/releases/latest). Quit any older running copy. Open the DMG, drag **Video to Text** onto **Applications**, eject the disk image, then launch the app from Applications. This version is locally signed and has not been notarized by Apple.

## Install on Windows

On a Windows x64 PC, open the setup EXE from the release downloads, follow Setup, and launch **Video to Text** from Start. Setup installs for the current Windows account. The EXE is unsigned. To remove it, use **Settings → Apps → Installed apps → Video to Text → Uninstall**.

For portable use, extract the entire Windows x64 ZIP. Open **Start Video to Text.cmd**. Keep the launcher, app and runtime folders together when moving it to another computer.

The release includes a SHA-256 checksum file. To check a downloaded file, use `shasum -a 256 filename` in macOS Terminal or `Get-FileHash -Algorithm SHA256 "filename"` in Windows PowerShell, and compare the result to its entry.

## Transcribe a conversation

Choose a local video with audible speech, set the speaker count, then click **Transcribe**. The app detects the spoken language automatically. It reads the first audio track and lists the speech in playback order. Times use hours, minutes, seconds and hundredths. Speaker numbers apply within each recording.

For example, the sample video contains this turn:

```text
[00:00:03.42 – 00:00:07.78] Speaker 2: Thank you for the directions. I will bring the bicycle back tomorrow morning.
```

Click in the transcript to fix wording or speaker labels. Click **Save Text…** to choose a destination for the UTF-8 text file. Save edits before choosing another video or running transcription again.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| Too many speaker labels | Set the known speaker count and transcribe again. |
| A speaker changes halfway through a sentence | Listen around the timestamp and edit the label before saving. Short turns and overlapping voices can be difficult to distinguish. |
| The video has no audio track | Select a version containing the conversation on its first audio track. |
| Missing model or FFmpeg | Reinstall the app or extract a fresh copy of the entire portable ZIP. |
| A long recording fails during audio extraction | Check free space on the drive used for temporary files. Decoded audio takes about 230 MB per hour and is removed after processing. |

For a reproducible issue, include the app version, operating system, speaker-count setting and the relevant timestamp. Share a short clip only if you have permission to share it.
