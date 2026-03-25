from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "assets" / "resultados"
OUTPUT_DIR = SOURCE_DIR / "google_ads"

LANDSCAPE = (1200, 628)
SQUARE = (1200, 1200)
JPEG_QUALITY = 92

# Antes/depois recomendados com melhor enquadramento entre as fotos reais.
BEFORE_AFTER_PAIRS = [
    ("sofa3a.webp", "sofa3d.webp", "sofa3_comparativo"),
    ("sofa1a.webp", "sofa1d.webp", "sofa1_comparativo"),
]

# Fotos limpas para capa principal.
HERO_IMAGES = [
    ("sofa3d.webp", "sofa3_capa"),
    ("sofa1d.webp", "sofa1_capa"),
]


def open_rgb(path: Path) -> Image.Image:
    image = Image.open(path)
    return ImageOps.exif_transpose(image).convert("RGB")


def crop_to_ratio(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    target_w, target_h = target_size
    src_w, src_h = image.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        return image.crop((left, 0, left + new_w, src_h))

    new_h = int(src_w / target_ratio)
    top = (src_h - new_h) // 2
    return image.crop((0, top, src_w, top + new_h))


def fit_size(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    cropped = crop_to_ratio(image, target_size)
    return cropped.resize(target_size, Image.Resampling.LANCZOS)


def save_jpg(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def make_hero_variants(filename: str, base_name: str) -> list[Path]:
    source_path = SOURCE_DIR / filename
    image = open_rgb(source_path)

    outputs: list[Path] = []
    for suffix, size in (("1200x628", LANDSCAPE), ("1200x1200", SQUARE)):
        out = OUTPUT_DIR / f"{base_name}_{suffix}.jpg"
        save_jpg(fit_size(image, size), out)
        outputs.append(out)

    return outputs


def make_before_after_variants(before_file: str, after_file: str, base_name: str) -> list[Path]:
    before = open_rgb(SOURCE_DIR / before_file)
    after = open_rgb(SOURCE_DIR / after_file)

    outputs: list[Path] = []
    for suffix, size in (("1200x628", LANDSCAPE), ("1200x1200", SQUARE)):
        left = fit_size(before, size)
        right = fit_size(after, size)

        combined = Image.new("RGB", size)
        width, height = size

        left_part = left.crop((0, 0, width // 2, height))
        right_part = right.crop((width // 2, 0, width, height))

        combined.paste(left_part, (0, 0))
        combined.paste(right_part, (width // 2, 0))

        # Linha divisoria para reforcar o efeito comparativo.
        divider_x = width // 2
        for y in range(height):
            combined.putpixel((divider_x, y), (255, 255, 255))

        out = OUTPUT_DIR / f"{base_name}_{suffix}.jpg"
        save_jpg(combined, out)
        outputs.append(out)

    return outputs


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Pasta nao encontrada: {SOURCE_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for filename, base_name in HERO_IMAGES:
        generated.extend(make_hero_variants(filename, base_name))

    for before_file, after_file, base_name in BEFORE_AFTER_PAIRS:
        generated.extend(make_before_after_variants(before_file, after_file, base_name))

    print("Arquivos gerados:")
    for path in generated:
        print(path.relative_to(BASE_DIR).as_posix())


if __name__ == "__main__":
    main()
