"""
generate_lisan_branding.py
Generates the custom, premium brand visual identity for LISAN (ልሳን):
- Android launcher icons (all mipmap densities: mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi)
- Master 1024x1024 icon
- Splash icon & in-app transparent badges
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def draw_squircle_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    return mask

def generate_master_icon(size=2048):
    # 2x supersampled canvas: 2048x2048
    center = size // 2

    # 1. Background Rounded Container
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)

    # Vertical gradient from rich deep graphite slate (#1C201C) to midnight obsidian (#0F110F)
    for y in range(size):
        t = y / size
        r = int(28 * (1 - t) + 15 * t)
        g = int(33 * (1 - t) + 18 * t)
        b = int(29 * (1 - t) + 16 * t)
        bg_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Top-center radial illumination
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [(center - 750, -250), (center + 750, 950)],
        fill=(68, 85, 72, 95)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    bg = Image.alpha_composite(bg, glow)

    # Squircle mask with radius ~ 450px
    corner_radius = int(size * 0.22)
    squircle_mask = draw_squircle_mask(size, corner_radius)

    squircle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    squircle.paste(bg, (0, 0), squircle_mask)

    # 2. Outer Luxury Bezel Border (Double rim: Gold & Titanium)
    border_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_layer)
    border_draw.rounded_rectangle(
        [(16, 16), (size - 17, size - 17)],
        radius=corner_radius - 8,
        outline=(216, 158, 53, 200), # Golden tone
        width=14
    )
    border_draw.rounded_rectangle(
        [(34, 34), (size - 35, size - 35)],
        radius=corner_radius - 20,
        outline=(85, 95, 85, 130), # Brushed titanium
        width=6
    )
    squircle = Image.alpha_composite(squircle, border_layer)

    # 3. Dynamic Acoustic Resonance Waves
    waves_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    waves_draw = ImageDraw.Draw(waves_layer)

    wave_colors = [
        (216, 241, 113, 220),  # Acid Lime (#D8F171)
        (245, 166, 35, 235),   # Sun Gold (#F5A623)
        (240, 90, 54, 225),    # Coral Flame (#F05A36)
        (55, 141, 104, 210),   # Ethiopian Emerald (#378D68)
    ]
    radii = [480, 600, 720, 840]
    widths = [26, 30, 32, 34]
    lens_cy = center - 80

    for (r, col, w) in zip(radii, wave_colors, widths):
        # Right sound arcs
        bbox_r = [(center - r, lens_cy - r), (center + r, lens_cy + r)]
        waves_draw.arc(bbox_r, start=-38, end=38, fill=col, width=w)
        # Left sound arcs
        bbox_l = [(center - r, lens_cy - r), (center + r, lens_cy + r)]
        waves_draw.arc(bbox_l, start=142, end=218, fill=col, width=w)

    waves_bloom = waves_layer.filter(ImageFilter.GaussianBlur(16))
    squircle = Image.alpha_composite(squircle, waves_bloom)
    squircle = Image.alpha_composite(squircle, waves_layer)

    # 4. Central Acoustic Disc / Lens
    lens_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    lens_draw = ImageDraw.Draw(lens_layer)
    lens_r = 380

    # Disc drop shadow
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [(center - lens_r - 20, lens_cy - lens_r + 25), (center + lens_r + 20, lens_cy + lens_r + 65)],
        fill=(0, 0, 0, 170)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    squircle = Image.alpha_composite(squircle, shadow)

    # Lens disc body
    lens_draw.ellipse(
        [(center - lens_r, lens_cy - lens_r), (center + lens_r, lens_cy + lens_r)],
        fill=(22, 26, 22, 255),
        outline=(216, 158, 53, 245), # Gold bezel
        width=18
    )
    # Inner coral ring
    lens_draw.ellipse(
        [(center - lens_r + 26, lens_cy - lens_r + 26), (center + lens_r - 26, lens_cy + lens_r - 26)],
        outline=(240, 90, 54, 180),
        width=6
    )
    squircle = Image.alpha_composite(squircle, lens_layer)

    # 5. Core Ethiopic Glyph: "ል" + Spark
    glyph_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glyph_draw = ImageDraw.Draw(glyph_layer)

    font_path_ethiopic = "C:/Windows/Fonts/ebrimabd.ttf"
    if not os.path.exists(font_path_ethiopic):
        font_path_ethiopic = "C:/Windows/Fonts/ebrima.ttf"
    font_glyph = ImageFont.truetype(font_path_ethiopic, 440)

    bbox_l = font_glyph.getbbox("ል")
    gw = bbox_l[2] - bbox_l[0]
    gh = bbox_l[3] - bbox_l[1]
    gx = center - (bbox_l[0] + bbox_l[2]) / 2
    gy = lens_cy - (bbox_l[1] + bbox_l[3]) / 2 + 18

    # Glyph shadow & text
    glyph_draw.text((gx + 6, gy + 12), "ል", font=font_glyph, fill=(0, 0, 0, 180))
    glyph_draw.text((gx, gy), "ል", font=font_glyph, fill=(255, 248, 235, 255))
    glyph_draw.text((gx - 2, gy - 2), "ል", font=font_glyph, fill=(255, 225, 140, 160))

    # Ethiopian Diamond Spark
    spark_cx = center
    spark_cy = lens_cy - 245
    spark_size = 40
    spark_pts = [
        (spark_cx, spark_cy - spark_size),
        (spark_cx + spark_size * 0.35, spark_cy - spark_size * 0.35),
        (spark_cx + spark_size, spark_cy),
        (spark_cx + spark_size * 0.35, spark_cy + spark_size * 0.35),
        (spark_cx, spark_cy + spark_size),
        (spark_cx - spark_size * 0.35, spark_cy + spark_size * 0.35),
        (spark_cx - spark_size, spark_cy),
        (spark_cx - spark_size * 0.35, spark_cy - spark_size * 0.35),
    ]
    glyph_draw.polygon(spark_pts, fill=(216, 241, 113, 245))

    squircle = Image.alpha_composite(squircle, glyph_layer)

    # 6. Typographic Wordmark
    text_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    font_path_sans = "C:/Windows/Fonts/segoeuib.ttf"
    if not os.path.exists(font_path_sans):
        font_path_sans = "C:/Windows/Fonts/arialbd.ttf"

    font_brand = ImageFont.truetype(font_path_sans, 138)
    font_sub = ImageFont.truetype(font_path_ethiopic, 64)

    # "LISAN"
    word = "LISAN"
    char_widths = [font_brand.getbbox(c)[2] - font_brand.getbbox(c)[0] for c in word]
    spacing = 38
    total_w = sum(char_widths) + spacing * (len(word) - 1)
    curr_x = center - total_w / 2
    word_y = center + 520

    for i, c in enumerate(word):
        text_draw.text((curr_x + 3, word_y + 6), c, font=font_brand, fill=(0, 0, 0, 160))
        text_draw.text((curr_x, word_y), c, font=font_brand, fill=(245, 240, 230, 255))
        curr_x += char_widths[i] + spacing

    # "ልሳን  •  SPEECH AI"
    sub_text = "ልሳን  •  SPEECH AI"
    sub_bbox = font_sub.getbbox(sub_text)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = center - sub_w / 2
    sub_y = word_y + 160
    text_draw.text((sub_x, sub_y), sub_text, font=font_sub, fill=(216, 158, 53, 220))

    squircle = Image.alpha_composite(squircle, text_layer)
    final_icon = squircle.resize((1024, 1024), Image.Resampling.LANCZOS)
    return final_icon

def generate_transparent_badge(size=512):
    # Circular emblem with waves and spark (no squircle, transparent background)
    canvas_size = 1024
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    center = canvas_size // 2
    draw = ImageDraw.Draw(img)

    # Acoustic wave rings
    wave_colors = [
        (216, 241, 113, 230), # Lime
        (245, 166, 35, 240),  # Gold
        (240, 90, 54, 230),   # Coral
        (55, 141, 104, 210),  # Emerald
    ]
    radii = [260, 320, 380, 440]
    widths = [16, 18, 20, 22]

    for (r, col, w) in zip(radii, wave_colors, widths):
        draw.arc([(center - r, center - r), (center + r, center + r)], start=-40, end=40, fill=col, width=w)
        draw.arc([(center - r, center - r), (center + r, center + r)], start=140, end=220, fill=col, width=w)

    # Central lens
    disc_r = 200
    draw.ellipse(
        [(center - disc_r, center - disc_r), (center + disc_r, center + disc_r)],
        fill=(22, 26, 22, 255),
        outline=(216, 158, 53, 255),
        width=12
    )
    draw.ellipse(
        [(center - disc_r + 14, center - disc_r + 14), (center + disc_r - 14, center + disc_r - 14)],
        outline=(240, 90, 54, 180),
        width=4
    )

    # Glyph "ል"
    font_ethiopic = ImageFont.truetype("C:/Windows/Fonts/ebrimabd.ttf", 230)
    bbox = font_ethiopic.getbbox("ል")
    gx = center - (bbox[0] + bbox[2]) / 2
    gy = center - (bbox[1] + bbox[3]) / 2 + 10

    draw.text((gx + 4, gy + 6), "ል", font=font_ethiopic, fill=(0, 0, 0, 160))
    draw.text((gx, gy), "ል", font=font_ethiopic, fill=(255, 248, 232, 255))
    draw.text((gx - 2, gy - 2), "ል", font=font_ethiopic, fill=(255, 225, 140, 180))

    # Spark above
    spark_cx = center
    spark_cy = center - 130
    spark_size = 20
    spark_pts = [
        (spark_cx, spark_cy - spark_size),
        (spark_cx + spark_size * 0.35, spark_cy - spark_size * 0.35),
        (spark_cx + spark_size, spark_cy),
        (spark_cx + spark_size * 0.35, spark_cy + spark_size * 0.35),
        (spark_cx, spark_cy + spark_size),
        (spark_cx - spark_size * 0.35, spark_cy + spark_size * 0.35),
        (spark_cx - spark_size, spark_cy),
        (spark_cx - spark_size * 0.35, spark_cy - spark_size * 0.35),
    ]
    draw.polygon(spark_pts, fill=(216, 241, 113, 245))

    badge = img.resize((size, size), Image.Resampling.LANCZOS)
    return badge

def generate_header_bar_logo():
    # Produces a clean 400x96 banner for the AppBar
    badge = generate_transparent_badge(96)
    img = Image.new("RGBA", (380, 96), (0, 0, 0, 0))
    img.paste(badge, (0, 0), badge)

    draw = ImageDraw.Draw(img)
    font_brand = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
    font_sub = ImageFont.truetype("C:/Windows/Fonts/ebrimabd.ttf", 17)

    # "LISAN"
    draw.text((106, 14), "LISAN", font=font_brand, fill=(32, 34, 31, 255))
    # "ልሳን  •  MODEL 01"
    draw.text((108, 56), "ልሳን  •  MODEL 01", font=font_sub, fill=(216, 158, 53, 255))

    return img

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flutter_dir = os.path.join(base_dir, "ethiopian_translator")
    res_dir = os.path.join(flutter_dir, "android", "app", "src", "main", "res")
    assets_icon_dir = os.path.join(flutter_dir, "assets", "icon")
    assets_images_dir = os.path.join(flutter_dir, "assets", "images")

    os.makedirs(assets_icon_dir, exist_ok=True)
    os.makedirs(assets_images_dir, exist_ok=True)

    print("[1/5] Generating Master 1024x1024 LISAN Icon...")
    master_1024 = generate_master_icon(2048)
    master_path = os.path.join(assets_icon_dir, "lisan_master_1024.png")
    master_1024.save(master_path, "PNG")

    densities = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }

    print("[2/5] Generating Android Launcher Icons...")
    for folder, dim in densities.items():
        target_dir = os.path.join(res_dir, folder)
        os.makedirs(target_dir, exist_ok=True)
        icon_dim = master_1024.resize((dim, dim), Image.Resampling.LANCZOS)
        out_file = os.path.join(target_dir, "ic_launcher.png")
        icon_dim.save(out_file, "PNG")
        print(f"      Saved {out_file} ({dim}x{dim})")

    print("[3/5] Generating In-App Badge & Splash Assets...")
    badge_512 = generate_transparent_badge(512)
    badge_path = os.path.join(assets_images_dir, "lisan_badge.png")
    badge_512.save(badge_path, "PNG")

    badge_128 = generate_transparent_badge(128)
    badge_128_path = os.path.join(assets_images_dir, "lisan_badge_128.png")
    badge_128.save(badge_128_path, "PNG")

    header_logo = generate_header_bar_logo()
    header_path = os.path.join(assets_images_dir, "lisan_header_logo.png")
    header_logo.save(header_path, "PNG")

    print("[4/5] All visual assets generated successfully!")

if __name__ == "__main__":
    main()
