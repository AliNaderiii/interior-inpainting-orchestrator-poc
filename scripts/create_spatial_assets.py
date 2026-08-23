"""Create clean-room synthetic assets for the Phase 05 Spatial Studio demo."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE_ASSETS = ROOT / "site" / "assets"
DOC_ASSETS = ROOT / "docs" / "assets"
SCALE = 2
WIDTH = 1200
HEIGHT = 800


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, ...],
    outline: tuple[int, ...] | None = None,
    width: int = 1,
) -> None:
    scaled = tuple(value * SCALE for value in box)
    draw.rounded_rectangle(
        scaled, radius=radius * SCALE, fill=fill, outline=outline, width=width * SCALE
    )


def _ellipse(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, ...]
) -> None:
    draw.ellipse(tuple(value * SCALE for value in box), fill=fill)


def _line(
    draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: tuple[int, ...], width: int
) -> None:
    draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=fill, width=width * SCALE)


def _polygon(
    draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: tuple[int, ...]
) -> None:
    draw.polygon([(x * SCALE, y * SCALE) for x, y in points], fill=fill)


def _gradient(
    size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]
) -> Image.Image:
    width, height = size
    image = Image.new("RGB", (width * SCALE, height * SCALE))
    draw = ImageDraw.Draw(image)
    for y in range(height * SCALE):
        amount = y / max(height * SCALE - 1, 1)
        color = tuple(
            round(top[index] * (1 - amount) + bottom[index] * amount) for index in range(3)
        )
        draw.line((0, y, width * SCALE, y), fill=color)
    return image


def _draw_sofa(target: Image.Image) -> None:
    draw = ImageDraw.Draw(target, "RGBA")
    _ellipse(draw, (390, 548, 1005, 700), (18, 22, 25, 42))
    _rounded(draw, (404, 385, 1000, 604), 82, (76, 93, 94, 255), (45, 59, 61, 255), 2)
    _rounded(draw, (427, 420, 977, 587), 64, (91, 108, 108, 255), (114, 130, 127, 140), 2)
    _rounded(draw, (414, 500, 990, 641), 55, (64, 78, 80, 255), (37, 50, 52, 255), 2)
    _line(draw, [(688, 429), (688, 589)], (44, 58, 59, 150), 2)
    _rounded(draw, (451, 444, 655, 569), 48, (101, 117, 116, 255))
    _rounded(draw, (716, 444, 948, 569), 48, (91, 107, 107, 255))
    _rounded(draw, (500, 478, 610, 558), 34, (172, 125, 91, 255))
    _line(draw, [(460, 615), (450, 666)], (38, 41, 41, 255), 14)
    _line(draw, [(944, 615), (957, 666)], (38, 41, 41, 255), 14)


def _draw_table(target: Image.Image) -> None:
    draw = ImageDraw.Draw(target, "RGBA")
    _ellipse(draw, (508, 586, 827, 715), (16, 19, 21, 55))
    _line(draw, [(647, 592), (624, 710)], (48, 40, 34, 255), 15)
    _line(draw, [(698, 592), (731, 710)], (48, 40, 34, 255), 15)
    _ellipse(draw, (514, 544, 830, 636), (60, 49, 42, 255))
    _ellipse(draw, (523, 548, 821, 621), (138, 114, 91, 255))
    _ellipse(draw, (566, 554, 652, 588), (187, 165, 130, 255))
    _ellipse(draw, (574, 556, 644, 579), (201, 184, 151, 255))
    _rounded(draw, (720, 527, 755, 584), 7, (39, 70, 69, 255))
    _ellipse(draw, (704, 510, 770, 550), (58, 98, 83, 220))


def create_room() -> tuple[Image.Image, Image.Image]:
    image = _gradient((WIDTH, HEIGHT), (231, 229, 221), (197, 195, 186)).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    # wall / floor envelope
    _polygon(draw, [(0, 0), (1200, 0), (1200, 433), (0, 456)], (220, 217, 208, 255))
    _polygon(draw, [(0, 456), (1200, 433), (1200, 800), (0, 800)], (157, 149, 136, 255))
    for index in range(1, 9):
        x = index * 150
        _line(draw, [(600, 443), (x, 800)], (104, 97, 87, 34), 2)
    for y in (525, 624, 722):
        _line(draw, [(0, y), (1200, max(440, y - 22))], (93, 86, 78, 25), 2)

    # architectural reveals
    _polygon(draw, [(0, 0), (36, 0), (36, 800), (0, 800)], (67, 72, 70, 255))
    _polygon(draw, [(1148, 0), (1200, 0), (1200, 800), (1174, 800)], (71, 75, 72, 255))
    _line(draw, [(0, 456), (1200, 433)], (98, 94, 87, 150), 5)

    # window and landscape
    _rounded(draw, (82, 66, 393, 410), 7, (67, 73, 72, 255))
    _rounded(draw, (94, 78, 381, 398), 3, (158, 186, 187, 255))
    window = Image.new("RGBA", image.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(window, "RGBA")
    _polygon(wd, [(98, 82), (377, 82), (377, 393), (98, 393)], (153, 185, 188, 255))
    _polygon(wd, [(98, 248), (377, 191), (377, 393), (98, 393)], (82, 116, 99, 255))
    for x, y, r, color in [
        (126, 228, 80, (72, 109, 87, 255)),
        (222, 211, 105, (58, 95, 76, 255)),
        (329, 235, 93, (79, 118, 90, 255)),
        (267, 294, 113, (48, 83, 69, 255)),
    ]:
        _ellipse(wd, (x - r, y - r // 2, x + r, y + r // 2), color)
    image.alpha_composite(window)
    draw = ImageDraw.Draw(image, "RGBA")
    _line(draw, [(238, 78), (238, 398)], (62, 68, 68, 255), 8)
    _line(draw, [(94, 238), (381, 238)], (62, 68, 68, 255), 8)
    _line(draw, [(105, 88), (220, 88)], (233, 243, 240, 90), 4)

    # art and sconces
    _rounded(draw, (824, 98, 1008, 308), 4, (82, 77, 70, 255))
    _rounded(draw, (835, 109, 997, 297), 2, (221, 205, 177, 255))
    _polygon(draw, [(855, 265), (900, 150), (959, 270)], (66, 83, 82, 255))
    _ellipse(draw, (888, 128, 947, 187), (171, 114, 74, 255))
    _line(draw, [(862, 222), (976, 183)], (235, 227, 210, 180), 8)

    for x in (477, 1090):
        _line(draw, [(x, 157), (x, 224)], (93, 82, 69, 255), 5)
        _ellipse(draw, (x - 29, 198, x + 29, 244), (239, 200, 132, 90))
        _rounded(draw, (x - 25, 205, x + 25, 240), 12, (178, 133, 86, 255))

    # planter
    _ellipse(draw, (93, 536, 270, 675), (22, 28, 29, 54))
    _rounded(draw, (119, 469, 237, 637), 24, (80, 71, 60, 255))
    _ellipse(draw, (120, 451, 237, 493), (103, 91, 76, 255))
    for points in [
        [(176, 468), (124, 347), (159, 421)],
        [(181, 467), (215, 331), (203, 429)],
        [(176, 462), (99, 389), (152, 442)],
        [(184, 459), (269, 370), (209, 443)],
    ]:
        _polygon(draw, points, (48, 89, 70, 255))

    # furniture plus shadow
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    _draw_sofa(shadow)
    _draw_table(shadow)
    image.alpha_composite(shadow)

    # subtle color grade and vignette
    grade = Image.new("RGBA", image.size, (19, 30, 31, 0))
    gd = ImageDraw.Draw(grade, "RGBA")
    for step in range(24):
        alpha = max(0, 26 - step)
        gd.rectangle(
            (step * SCALE, step * SCALE, (WIDTH - step) * SCALE, (HEIGHT - step) * SCALE),
            outline=(12, 24, 26, alpha),
            width=SCALE * 2,
        )
    image = Image.alpha_composite(image, grade)

    occlusion = Image.new("RGBA", image.size, (0, 0, 0, 0))
    _draw_sofa(occlusion)
    _draw_table(occlusion)

    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("RGB"), occlusion.resize(
        (WIDTH, HEIGHT), Image.Resampling.LANCZOS
    )


def create_carpet() -> Image.Image:
    width, height = 720, 440
    carpet = Image.new("RGBA", (width * SCALE, height * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(carpet, "RGBA")
    _rounded(
        draw, (12, 12, width - 12, height - 12), 35, (31, 48, 51, 255), (217, 196, 159, 255), 7
    )
    _rounded(
        draw, (34, 34, width - 34, height - 34), 26, (45, 68, 70, 255), (185, 151, 105, 255), 4
    )

    # Original abstract contour motif.
    palette = [(190, 125, 75, 255), (213, 180, 119, 255), (103, 131, 127, 255), (114, 70, 76, 255)]
    for index, color in enumerate(palette):
        inset = 64 + index * 29
        draw.arc(
            (
                inset * SCALE,
                (49 + index * 22) * SCALE,
                (width - inset) * SCALE,
                (height - 49 - index * 22) * SCALE,
            ),
            start=186 + index * 13,
            end=516 - index * 8,
            fill=color,
            width=(25 - index * 3) * SCALE,
        )
    _ellipse(draw, (246, 127, 472, 313), (215, 190, 148, 255))
    _ellipse(draw, (274, 148, 442, 292), (74, 98, 98, 255))
    _polygon(draw, [(354, 80), (434, 214), (354, 360), (272, 214)], (169, 96, 73, 225))
    _polygon(draw, [(354, 119), (405, 214), (354, 318), (301, 214)], (224, 181, 111, 235))
    for x in range(61, width - 50, 31):
        _line(draw, [(x, 38), (x + 4, 55)], (226, 208, 177, 210), 3)
        _line(draw, [(x, height - 55), (x + 4, height - 38)], (226, 208, 177, 210), 3)

    texture = Image.new("RGBA", carpet.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(texture, "RGBA")
    for y in range(18 * SCALE, (height - 18) * SCALE, 7):
        td.line((22 * SCALE, y, (width - 22) * SCALE, y), fill=(245, 239, 222, 12), width=1)
    carpet = Image.alpha_composite(carpet, texture)
    return carpet.resize((width, height), Image.Resampling.LANCZOS)


def create_product_card(carpet: Image.Image) -> Image.Image:
    card = Image.new("RGB", (1400, 900), (232, 229, 221))
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow, "RGBA")
    sd.rounded_rectangle((670, 178, 1285, 723), radius=55, fill=(14, 28, 31, 58))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    card.paste(shadow, (0, 0), shadow)
    preview = carpet.resize((610, 372), Image.Resampling.LANCZOS)
    card.paste(preview, (655, 205), preview)
    draw = ImageDraw.Draw(card)
    draw.text((95, 116), "CONTOUR 01", fill=(23, 42, 45), font=_font(54, bold=True))
    draw.text(
        (98, 189), "Hero carpet / synthetic catalog sample", fill=(75, 86, 84), font=_font(22)
    )
    draw.text((98, 365), "720 x 440 PX", fill=(38, 111, 112), font=_font(19, bold=True))
    draw.text((98, 417), "IMMUTABLE SOURCE", fill=(38, 111, 112), font=_font(19, bold=True))
    draw.text(
        (98, 519), "Original clean-room asset for deterministic", fill=(75, 86, 84), font=_font(20)
    )
    draw.text((98, 552), "perspective-placement evidence.", fill=(75, 86, 84), font=_font(20))
    draw.rounded_rectangle((95, 662, 508, 733), radius=20, fill=(23, 42, 45))
    draw.text((127, 681), "CATALOG-FAITHFUL PATH", fill=(235, 232, 220), font=_font(18, bold=True))
    return card


def main() -> None:
    SITE_ASSETS.mkdir(parents=True, exist_ok=True)
    DOC_ASSETS.mkdir(parents=True, exist_ok=True)
    room, occlusion = create_room()
    carpet = create_carpet()
    card = create_product_card(carpet)

    outputs = {
        SITE_ASSETS / "spatial-lounge-source.png": room,
        SITE_ASSETS / "spatial-lounge-occlusion.png": occlusion,
        SITE_ASSETS / "spatial-hero-carpet.png": carpet,
        SITE_ASSETS / "spatial-product-card.png": card,
        DOC_ASSETS / "spatial-lounge-source.png": room,
        DOC_ASSETS / "spatial-hero-carpet.png": carpet,
    }
    for path, image in outputs.items():
        image.save(path, format="PNG", optimize=True)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
