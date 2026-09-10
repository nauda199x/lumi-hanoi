from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps

SRC = Path('assets/media/floor-plans/lumi-elite-masterplan.webp')
OUT = Path('assets/media/floor-plans/lumi-elite-masterplan-v2.webp')
HUB = Path('mat-bang-lumi-hanoi/index.html')
ELITE = Path('mat-bang-lumi-hanoi/lumi-elite/index.html')

W, H = 1800, 1200
BG = (244, 241, 234)
GREEN = (17, 48, 42)
GREEN2 = (28, 69, 58)
INK = (29, 34, 31)
MUTED = (96, 94, 87)
LINE = (220, 215, 205)
PAPER = (250, 248, 242)
WHITE = (255, 255, 255)

REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def render():
    src = Image.open(SRC).convert('RGB')
    canvas = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    # Premium header. Underlying plan geometry is kept untouched.
    draw.rounded_rectangle((36, 32, W - 36, 168), radius=24, fill=GREEN)
    draw.text((72, 52), 'MẶT BẰNG TỔNG KHU E · LUMI ELITE', font=font(BOLD, 48), fill=(247, 244, 236))
    draw.text((74, 116), 'E1 · E2  |  Stella Zone  |  Sơ đồ tra cứu từ tài liệu dự án', font=font(REGULAR, 24), fill=(214, 208, 193))

    # Main plan card: crop only outer white space/legacy legend, keep all mapped geometry.
    map_x, map_y, map_w, map_h = 36, 192, 1320, 972
    draw.rounded_rectangle((map_x, map_y, map_x + map_w, map_y + map_h), radius=28, fill=WHITE, outline=LINE, width=2)
    crop = src.crop((80, 45, 1740, 1110))
    crop = ImageEnhance.Contrast(crop).enhance(1.05)
    crop = ImageEnhance.Sharpness(crop).enhance(1.18)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))
    fit = ImageOps.contain(crop, (map_w - 36, map_h - 36), method=Image.Resampling.LANCZOS)
    fx = map_x + 18 + (map_w - 36 - fit.width) // 2
    fy = map_y + 18 + (map_h - 36 - fit.height) // 2
    canvas.paste(fit, (fx, fy))

    # Editorial side panel. It adds hierarchy without inventing new site-plan geometry.
    sx = 1390
    draw.rounded_rectangle((sx, 192, W - 36, 1164), radius=28, fill=PAPER, outline=LINE, width=2)
    draw.text((sx + 34, 228), 'LUMI ELITE', font=font(BOLD, 36), fill=GREEN)
    draw.text((sx + 34, 282), 'Tra cứu nhanh khu E', font=font(REGULAR, 22), fill=MUTED)
    draw.line((sx + 34, 326, W - 70, 326), fill=(211, 205, 193), width=2)

    def tower_card(y, code, title):
        draw.rounded_rectangle((sx + 28, y, W - 64, y + 124), radius=18, fill=WHITE, outline=(218, 211, 200), width=2)
        draw.rounded_rectangle((sx + 44, y + 26, sx + 110, y + 92), radius=14, fill=GREEN2)
        draw.text((sx + 58, y + 38), code, font=font(BOLD, 24), fill=WHITE)
        draw.text((sx + 130, y + 26), title, font=font(BOLD, 20), fill=INK)
        draw.text((sx + 130, y + 62), f'Định vị {code} trước khi', font=font(REGULAR, 15), fill=MUTED)
        draw.text((sx + 130, y + 84), 'xem mặt bằng tầng', font=font(REGULAR, 15), fill=MUTED)

    tower_card(360, 'E1', 'E1 · Elite 1')
    tower_card(510, 'E2', 'E2 · Elite 2')

    draw.text((sx + 34, 680), 'CÁCH DÙNG', font=font(BOLD, 20), fill=GREEN)
    steps = [
        '1  Xác định đúng E1 hoặc E2',
        '2  Mở nhóm tầng tương ứng',
        '3  Đối chiếu mã căn & layout',
    ]
    y = 724
    for text in steps:
        draw.text((sx + 34, y), text, font=font(REGULAR, 18), fill=INK)
        y += 48

    draw.rounded_rectangle((sx + 28, 890, W - 64, 1038), radius=18, fill=(235, 239, 233))
    draw.text((sx + 46, 914), 'Nguồn đối chiếu', font=font(BOLD, 18), fill=GREEN)
    draw.text((sx + 46, 948), 'CapitaLand Development', font=font(REGULAR, 17), fill=INK)
    draw.text((sx + 46, 978), 'eBrochure / Floor Plans', font=font(REGULAR, 17), fill=INK)
    draw.text((sx + 46, 1008), 'Biên tập lại để tra cứu', font=font(REGULAR, 16), fill=MUTED)
    draw.text((sx + 34, 1092), 'Không thay thế bản vẽ HĐMB/phụ lục.', font=font(REGULAR, 14), fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, 'WEBP', quality=88, method=6)


def update_html():
    old = '/assets/media/floor-plans/lumi-elite-masterplan.webp'
    new = '/assets/media/floor-plans/lumi-elite-masterplan-v2.webp'
    for path in (HUB, ELITE):
        s = path.read_text(encoding='utf-8')
        s = s.replace(old, new)
        # Correct intrinsic/meta dimensions for the new 3:2 render.
        s = s.replace('width="1800" height="1350" alt="Mặt bằng tổng Lumi Elite', 'width="1800" height="1200" alt="Mặt bằng tổng Lumi Elite')
        if path == ELITE:
            s = s.replace('<meta property="og:image:height" content="1350">', '<meta property="og:image:height" content="1200">')
            s = s.replace('"width":1800,"height":1350}', '"width":1800,"height":1200}')
            s = s.replace('Mặt bằng phân khu Lumi Elite, dùng để định vị E1 và E2 trước khi xem mặt bằng tầng.', 'Mặt bằng tổng khu E được biên tập lại để tra cứu E1 và E2; hình học mặt bằng gốc được giữ nguyên.')
        path.write_text(s, encoding='utf-8')


if __name__ == '__main__':
    render()
    update_html()
    print(f'Rendered {OUT} ({OUT.stat().st_size} bytes)')
