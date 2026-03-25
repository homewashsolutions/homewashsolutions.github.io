from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = BASE_DIR / "assets" / "resultados"
DEFAULT_OUTPUT_DIR = DEFAULT_SOURCE_DIR / "google_ads"

LANDSCAPE = (1200, 628)
SQUARE = (1200, 1200)
DEFAULT_JPEG_QUALITY = 92

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


def make_hero_variants(filename: str, base_name: str, source_dir: Path, output_dir: Path, quality: int) -> list[Path]:
    source_path = source_dir / filename
    image = open_rgb(source_path)

    outputs: list[Path] = []
    for suffix, size in (("1200x628", LANDSCAPE), ("1200x1200", SQUARE)):
        out = output_dir / f"{base_name}_{suffix}.jpg"
        fitted = fit_size(image, size)
        out.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
        outputs.append(out)

    return outputs


def make_before_after_variants(
    before_file: str,
    after_file: str,
    base_name: str,
    source_dir: Path,
    output_dir: Path,
    quality: int,
) -> list[Path]:
    before = open_rgb(source_dir / before_file)
    after = open_rgb(source_dir / after_file)

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
        draw = ImageDraw.Draw(combined)
        draw.line((divider_x, 0, divider_x, height), fill=(255, 255, 255), width=2)

        out = output_dir / f"{base_name}_{suffix}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        combined.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
        outputs.append(out)

    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera imagens JPG para Google Ads a partir das fotos tratadas.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Pasta com imagens base")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Pasta de saida para Ads")
    parser.add_argument("--quality", type=int, default=DEFAULT_JPEG_QUALITY, help="Qualidade JPEG (0-100)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir: Path = args.source_dir
    output_dir: Path = args.output_dir
    quality = max(0, min(100, args.quality))

    if not source_dir.exists():
        raise FileNotFoundError(f"Pasta nao encontrada: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for filename, base_name in HERO_IMAGES:
        generated.extend(make_hero_variants(filename, base_name, source_dir, output_dir, quality))

    for before_file, after_file, base_name in BEFORE_AFTER_PAIRS:
        generated.extend(
            make_before_after_variants(before_file, after_file, base_name, source_dir, output_dir, quality)
        )

    print("Arquivos gerados:")
    for path in generated:
        print(path.relative_to(BASE_DIR).as_posix())


if __name__ == "__main__":
    main()
