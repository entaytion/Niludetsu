import io
from PIL import Image, ImageDraw

def LGBT(avatar_bytes: bytes) -> bytes:
    """Накладывает радужный полупрозрачный слой на изображение и возвращает PNG-байты"""
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert('RGBA')
    size = avatar.size
    overlay = Image.new('RGBA', size)
    draw = ImageDraw.Draw(overlay)
    colors = [
        (255, 0, 0, 128),
        (255, 127, 0, 128),
        (255, 255, 0, 128),
        (0, 255, 0, 128),
        (0, 255, 255, 128),
        (0, 0, 255, 128),
        (148, 0, 211, 128)
    ]
    stripe_height = size[1] // len(colors)
    for i, color in enumerate(colors):
        y0 = i * stripe_height
        y1 = (i + 1) * stripe_height if i < len(colors) - 1 else size[1]
        draw.rectangle([(0, y0), (size[0], y1)], fill=color)
    overlay.putalpha(int(255 * 0.2))
    result = Image.alpha_composite(avatar, overlay)
    buffer = io.BytesIO()
    result.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read() 

