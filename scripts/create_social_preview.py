from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site" / "assets"
OUTPUT = ASSETS / "social-preview.png"
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


def cover(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_width, target_height = size
    scale = max(target_width / source.width, target_height / source.height)
    resized = source.resize(
        (round(source.width * scale), round(source.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = max(0, (resized.width - target_width) // 2)
    top = max(0, (resized.height - target_height) // 2)
    return resized.crop((left, top, left + target_width, top + target_height))


def add_vignette(image: Image.Image) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(HEIGHT):
        vertical = max(abs((y / HEIGHT) - 0.5) * 2 - 0.52, 0) / 0.48
        for x in range(WIDTH):
            horizontal = max(0.0, 1 - x / 820)
            alpha = round(min(242, 18 + horizontal**1.55 * 218 + vertical * 36))
            pixels[x, y] = (2, 14, 16, alpha)
    image.alpha_composite(overlay)


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    accent: tuple[int, int, int, int],
) -> None:
    left, top, _, _ = box
    draw.rounded_rectangle(
        box,
        radius=13,
        fill=(6, 23, 25, 218),
        outline=(220, 245, 237, 38),
    )
    draw.ellipse((left + 15, top + 20, left + 23, top + 28), fill=accent)
    draw.text((left + 34, top + 11), label, font=font(7, mono=True), fill=(105, 132, 127, 255))
    draw.text(
        (left + 34, top + 29),
        value,
        font=font(10, bold=True, mono=True),
        fill=(224, 236, 229, 255),
    )


def create_preview() -> None:
    room = Image.open(ASSETS / "cinematic-lounge-concept.jpg").convert("RGB")
    image = cover(room, (WIDTH, HEIGHT)).convert("RGBA")
    image = image.filter(ImageFilter.GaussianBlur(0.12))
    add_vignette(image)
    draw = ImageDraw.Draw(image, "RGBA")

    ink = (241, 246, 238, 255)
    soft = (189, 207, 200, 255)
    faint = (102, 132, 126, 255)
    cyan = (103, 232, 225, 255)
    lime = (185, 237, 131, 255)
    amber = (241, 195, 126, 255)

    # Original repository mark and product identity.
    draw.rounded_rectangle(
        (68, 50, 114, 96),
        radius=13,
        fill=(10, 37, 39, 235),
        outline=(103, 232, 225, 58),
    )
    draw.line((82, 65, 100, 65), fill=ink, width=4)
    draw.line((86, 73, 101, 87), fill=cyan, width=4)
    draw.line((81, 87, 97, 87), fill=ink, width=4)
    draw.text((130, 51), "INPAINT / ORCHESTRATOR", font=font(17, bold=True), fill=ink)
    draw.text(
        (130, 78),
        "SPATIAL POC  ·  v0.3 RELEASE",
        font=font(8, mono=True),
        fill=faint,
    )

    draw.ellipse((69, 130, 78, 139), fill=cyan)
    draw.text(
        (89, 128),
        "SCROLL-DIRECTED SPATIAL STORY",
        font=font(8, bold=True, mono=True),
        fill=soft,
    )

    draw.text((67, 161), "Direct the space.", font=font(61, bold=True), fill=ink)
    draw.text((67, 231), "Prove", font=font(65, bold=True), fill=amber)
    prove_width = draw.textlength("Prove", font=font(65, bold=True))
    draw.text((79 + prove_width, 231), "every", font=font(65, bold=True), fill=(143, 226, 211, 255))
    draw.text((67, 303), "decision.", font=font(65, bold=True), fill=cyan)
    draw.text(
        (70, 396),
        "Structured briefs, scene authority and catalog-faithful placement—",
        font=font(15),
        fill=soft,
    )
    draw.text(
        (70, 422),
        "composed as one professional art-direction workflow.",
        font=font(15),
        fill=soft,
    )

    rounded_card(draw, (68, 487, 243, 548), "INTERVENTION", "CONCEPT + PLACE", amber)
    rounded_card(draw, (257, 487, 425, 548), "PROTECTED DRIFT", "0 PIXELS", lime)
    rounded_card(draw, (439, 487, 588, 548), "RUNTIME", "BROWSER-LOCAL", cyan)

    # Truth boundary in the visual itself.
    note = (860, 531, 1135, 579)
    draw.rounded_rectangle(note, radius=12, fill=(5, 21, 23, 222), outline=(224, 245, 238, 42))
    draw.rounded_rectangle((873, 542, 899, 568), radius=7, fill=(77, 63, 37, 235))
    draw.text((882, 547), "I", font=font(8, bold=True, mono=True), fill=amber)
    draw.text((910, 540), "ILLUSTRATIVE CONCEPT FRAME", font=font(7, bold=True), fill=soft)
    draw.text((910, 554), "Local art direction · not live-model evidence", font=font(7), fill=faint)

    draw.line((68, 592, 1135, 592), fill=(225, 245, 238, 28), width=1)
    draw.text(
        (68, 603),
        "ATMOSPHERE  →  ANALYZE  →  PLACE  →  PROVE",
        font=font(8, bold=True, mono=True),
        fill=(116, 159, 151, 255),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Adaptive palette keeps the photographic Open Graph card below a practical static-host budget.
    output = image.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    output.save(OUTPUT, format="PNG", optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    create_preview()
