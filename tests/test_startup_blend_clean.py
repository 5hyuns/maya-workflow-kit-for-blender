"""The bundled startup file names nothing from the machine that generated it, and no leftover image file name.

Blender keeps a text field's bytes after its end mark when it saves, so a name that once sat in a shading slot
can live on behind a shorter name. The shipped file's bytes (zstd frames unpacked) are searched as they are.
"""
import os

import kit

AUTO_ENABLE = False
STARTUP = os.path.join(kit.ROOT, "src", "allset", "app_template", "Maya_Workflow_Kit", "startup.blend")
FORBIDDEN = (b".jpg", b".jpeg", b".png", b"500x500", b"Users", b"AppData", b"Desktop")


def _plain_bytes(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data.startswith(b"\x28\xb5\x2f\xfd"):          # zstd (Blender's compressed .blend)
        import io
        import zstandard
        reader = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data), read_across_frames=True)
        data = reader.read()
    return data


def test_startup_file_names_no_local_image_or_path():
    data = _plain_bytes(STARTUP)
    assert data.startswith(b"BLENDER") and len(data) > 100_000, (data[:12], len(data))
    found = {}
    for word in FORBIDDEN:
        at = data.find(word)
        if at >= 0:
            found[word.decode()] = (data.count(word), data[max(0, at - 48):at + 24])
    assert not found, found
