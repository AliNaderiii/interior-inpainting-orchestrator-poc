from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "assets" / "social-preview.png"
WIDTH = 1200
HEIGHT = 630


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    else:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/local/share/fonts") / name,
        Path(name),
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    raise RuntimeError(f"A compatible TrueType font is required: {name}")


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=1)


def create_preview() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#07100f")
    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = (
            round(7 + 8 * ratio),
            round(16 + 20 * ratio),
            round(15 + 14 * ratio),
        )
        draw.line((0, y, WIDTH, y), fill=color)
    for x in range(0, WIDTH, 48):
        draw.line((x, 0, x, HEIGHT), fill=(15, 30, 26), width=1)
    for y in range(0, HEIGHT, 48):
        draw.line((0, y, WIDTH, y), fill=(15, 30, 26), width=1)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((750, -290, 1320, 280), fill=(71, 232, 158, 56))
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    draw = ImageDraw.Draw(image)

    accent = (119, 242, 181, 255)
    text = (241, 247, 244, 255)
    muted = (151, 171, 164, 255)
    faint = (102, 128, 119, 255)
    line = (39, 73, 62, 255)
    surface = (14, 29, 25, 255)

    draw.rounded_rectangle(
        (76, 72, 128, 124), radius=14, fill=(11, 32, 26, 255), outline=(38, 128, 93, 255)
    )
    draw.polygon(
        ((88, 88), (102, 80), (116, 88), (116, 111), (102, 119), (88, 111)), outline=accent, width=2
    )
    draw.line(((94, 101), (100, 107), (111, 92)), fill=accent, width=3, joint="curve")
    draw.text((144, 75), "INPAINT / ORCHESTRATOR", font=font(18, bold=True), fill=text)
    draw.text(
        (144, 103), "REFERENCE POC  ·  EXECUTABLE EVIDENCE", font=font(10, mono=True), fill=faint
    )

    draw.text((76, 200), "Controlled edits.", font=font(64, bold=True), fill=text)
    draw.text((76, 276), "Verifiable boundaries.", font=font(64, bold=True), fill=accent)
    draw.text(
        (76, 377),
        "Provider-neutral image inpainting orchestration with exact",
        font=font(21),
        fill=muted,
    )
    draw.text(
        (76, 411),
        "restoration of every protected pixel.",
        font=font(21),
        fill=muted,
    )

    cards = (
        (76, 506, 301, 562, "PROTECTED DRIFT", "0 PIXELS", True),
        (317, 506, 542, 562, "RUNTIME MATRIX", "PYTHON 3.11-3.13", False),
        (558, 506, 783, 562, "SECURITY POSTURE", "BOUNDARY-FIRST", False),
    )
    for left, top, right, bottom, label, value, highlighted in cards:
        fill = (11, 38, 30) if highlighted else surface[:3]
        border = (33, 137, 98) if highlighted else line[:3]
        rounded_card(draw, (left, top, right, bottom), fill=fill, outline=border)
        text_left = left + 20
        if highlighted:
            draw.ellipse((left + 20, top + 20, left + 34, top + 34), fill=accent)
            text_left = left + 47
        draw.text((text_left, top + 10), label, font=font(8, mono=True), fill=faint)
        draw.text((text_left, top + 27), value, font=font(13, bold=True, mono=True), fill=text)

    box = (1010, 480, 1096, 566)
    draw.rectangle(box, outline=(33, 117, 84, 255), width=1)
    center_x, center_y = 1053, 523
    draw.line((1019, center_y, 1087, center_y), fill=(56, 139, 105, 255), width=1)
    draw.line((center_x, 489, center_x, 557), fill=(56, 139, 105, 255), width=1)
    draw.ellipse(
        (center_x - 16, center_y - 16, center_x + 16, center_y + 16),
        fill=(11, 45, 34, 255),
        outline=(50, 159, 113, 255),
    )
    draw.line(
        ((center_x - 8, center_y), (center_x - 2, center_y + 6), (center_x + 10, center_y - 9)),
        fill=accent,
        width=3,
        joint="curve",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(OUTPUT, format="PNG", optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    create_preview()
