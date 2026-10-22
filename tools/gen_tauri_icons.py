"""从 assets/icon-only.png 生成 Tauri 全套图标（PNG + ICO + ICNS）。"""
import os
import struct
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon-only.png')
OUT = os.path.join(os.path.dirname(__file__), '..', 'src-tauri', 'icons')
os.makedirs(OUT, exist_ok=True)

src = Image.open(SRC).convert('RGBA')

# --- PNG 尺寸 ---
png_sizes = {
    '32x32.png': 32,
    '128x128.png': 128,
    '128x128@2x.png': 256,
    'icon.png': 512,
}
for name, size in png_sizes.items():
    im = src.resize((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name))

# --- Square 150 logo for Windows Store (tauri 约定) ---
src.resize((150, 150), Image.LANCZOS).save(os.path.join(OUT, 'Square150x150Logo.png'))
src.resize((44, 44), Image.LANCZOS).save(os.path.join(OUT, 'Square44x44Logo.png'))

# --- ICO（多分辨率内嵌）---
ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ico_path = os.path.join(OUT, 'icon.ico')
imgs = [src.resize(s, Image.LANCZOS) for s in ico_sizes]
imgs[0].save(ico_path, format='ICO', sizes=ico_sizes, append_images=imgs[1:])

# --- ICNS（macOS，支持最大 1024x1024）---
# ICNS 支持的元素类型
ICNS_TYPES = {
    16: b'is32', 32: b'il32', 48: b'ih32', 128: b'ic07',
    256: b'ic08', 512: b'ic09', 1024: b'ic10',
}
icns_path = os.path.join(OUT, 'icon.icns')
blocks = []
for size in (16, 32, 48, 128, 256, 512, 1024):
    if size not in ICNS_TYPES:
        continue
    ostype = ICNS_TYPES[size]
    im = src.resize((size, size), Image.LANCZOS)
    # ICNS 的 PNG 条目：直接存 PNG 数据，长度 = 8 + png 字节数
    import io
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    data = buf.getvalue()
    blocks.append(ostype + struct.pack('>I', len(data) + 8) + data)

total = 8 + sum(len(b) for b in blocks)
with open(icns_path, 'wb') as f:
    f.write(b'icns' + struct.pack('>I', total))
    for b in blocks:
        f.write(b)

print('icons written to', OUT)
for fn in sorted(os.listdir(OUT)):
    print(' ', fn, os.path.getsize(os.path.join(OUT, fn)))
