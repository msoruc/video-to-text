import sys
from pathlib import Path
from importlib.metadata import distribution
from PyInstaller.utils.hooks import collect_dynamic_libs
import imageio_ffmpeg

# The wheel ships whisper and ggml shared libraries alongside its Python extension.
engine = distribution("pywhispercpp")
libraries = [(str(engine.locate_file(f)), str(f.parent))
             for f in engine.files if f.suffix.lower() in (".dll", ".dylib")]
libraries.extend(collect_dynamic_libs("sherpa_onnx"))
libraries.append((imageio_ffmpeg.get_ffmpeg_exe(), "tools"))
a = Analysis(["app.py"], binaries=libraries,
             datas=[("assets", "assets")], excludes=["imageio_ffmpeg"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Video to Text",
          console=False, upx=False)
folder = COLLECT(exe, a.binaries, a.datas, name="Video to Text", upx=False)
if sys.platform == "darwin":
    app = BUNDLE(folder, name="Video to Text.app", bundle_identifier="local.videototext.desktop",
                 icon="assets/VideoToText.icns",
                 info_plist={"NSHighResolutionCapable": True})
