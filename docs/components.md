# Components and models

| Component | Role | Upstream |
| --- | --- | --- |
| Python and Tcl/Tk | Desktop runtime and interface | [Python](https://www.python.org/), [Tcl/Tk](https://www.tcl-lang.org/) |
| FFmpeg through imageio-ffmpeg | Local video and audio decoding | [FFmpeg](https://ffmpeg.org/), [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |
| whisper.cpp through pywhispercpp | Speech recognition | [whisper.cpp](https://github.com/ggml-org/whisper.cpp), [pywhispercpp](https://github.com/absadiki/pywhispercpp) |
| Whisper multilingual base | Local speech recognition model | [Model file](https://huggingface.co/ggerganov/whisper.cpp/blob/main/ggml-base.bin) |
| sherpa-onnx | Speaker analysis | [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) |
| pyannote segmentation 3.0 | Locates speech and speaker changes | [Model archive](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2), [included license](../assets/segmentation-LICENSE.txt) |
| 3D-Speaker ERes2Net | Compares voices across a recording | [Model download](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx) |
| PyInstaller and NSIS | App packaging and Windows setup | [PyInstaller](https://pyinstaller.org/), [NSIS](https://nsis.sourceforge.io/) |
| Python Build Standalone | Portable Windows Python runtime | [Python Build Standalone](https://github.com/astral-sh/python-build-standalone) |

Third-party software and models retain their respective licenses.
