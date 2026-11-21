# Run or build from source

Use Python 3.12 with Tk support, a native Apple silicon Mac or a Windows x64 PC, and the source files from this repository. Building requires an internet connection to install dependencies.

## Prepare the models

Download the Windows portable ZIP for the same [release](https://github.com/msoruc/video-to-text/releases/latest). On either platform, extract the three files below from **Video to Text/app/assets/** into the source tree’s **assets/** folder. The [component list](components.md) also links to their upstream sources.

| File | SHA-256 |
| --- | --- |
| ggml-base.bin | 60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe |
| segmentation.onnx | 220ad67ca923bef2fa91f2390c786097bf305bceb5e261d4af67b38e938e1079 |
| speaker.onnx | f1ee61be04000b50392a63442e5dd9feaea7e81dddd494d3647cf1c3d88a1498 |

## macOS

Install Xcode Command Line Tools and open Terminal in the repository folder.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv/bin/python app.py
```

To package the app, run `.venv/bin/python -m PyInstaller --noconfirm VideoToText.spec`. The output is **dist/Video to Text.app**.

## Windows

Install x64 Python 3.12 with Tcl/Tk and the Python launcher, then run **Build-Windows.cmd** in the repository folder. Launch **dist-windows/Video to Text/Video to Text.exe**. Keep its supporting files with it. For source development, the script also creates a virtual environment that can run the app with `.venv-win\Scripts\python.exe app.py`.

## Verify transcription

With dependencies installed and models in place, the same application supports file-to-file transcription:

```sh
python app.py --transcribe "Sample/Two speakers.mp4" example.txt --speakers 2
```

Run this inside the project’s virtual environment. Compare the output to **Sample/Two speakers.txt** and check that the speakers appear in the order 1, 2, 1.
