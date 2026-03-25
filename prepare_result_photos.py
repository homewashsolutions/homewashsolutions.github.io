from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = BASE_DIR / "photo_input"
DEFAULT_OUTPUT_DIR = BASE_DIR / "assets" / "resultados"
DEFAULT_TARGET_SIZE = (1200, 900)
DEFAULT_QUALITY = 86
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def slugify(filename: str) -> str:
    normalized = unicodedata.normalize("NFKD", filename)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_-]", "", normalized)
    return normalized or "imagem"


def crop_to_ratio(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    source_width, source_height = image.size
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        new_width = int(source_height * target_ratio)
        left = (source_width - new_width) // 2
        return image.crop((left, 0, left + new_width, source_height))

    new_height = int(source_width / target_ratio)
    top = (source_height - new_height) // 2
    return image.crop((0, top, source_width, top + new_height))


def process_image(source_path: Path, output_path: Path, target_size: tuple[int, int], quality: int) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.autocontrast(image, cutoff=1)
        image = crop_to_ratio(image, *target_size)
        image = image.resize(target_size, Image.Resampling.LANCZOS)

        image = ImageEnhance.Contrast(image).enhance(1.05)
        image = ImageEnhance.Color(image).enhance(1.03)
        image = ImageEnhance.Sharpness(image).enhance(1.08)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "WEBP", quality=quality, method=6)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepara fotos para a pasta de resultados do site.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="Pasta com fotos originais")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Pasta de saida WEBP")
    parser.add_argument("--width", type=int, default=DEFAULT_TARGET_SIZE[0], help="Largura de saida")
    parser.add_argument("--height", type=int, default=DEFAULT_TARGET_SIZE[1], help="Altura de saida")
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY, help="Qualidade WEBP (0-100)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    target_size = (args.width, args.height)
    quality = max(0, min(100, args.quality))

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = sorted(
        path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not source_files:
        print(f"Nenhuma foto encontrada em {input_dir.as_posix()}.")
        print("Coloque imagens JPG, JPEG, PNG ou WEBP nessa pasta e execute novamente.")
        return

    for source_path in source_files:
        output_name = f"{slugify(source_path.stem)}.webp"
        output_path = output_dir / output_name
        process_image(source_path, output_path, target_size, quality)
        print(f"OK: {source_path.name} -> {output_path.relative_to(BASE_DIR).as_posix()}")

    print("Tratamento concluido.")
    print(f"As imagens prontas estao em {output_dir.relative_to(BASE_DIR).as_posix()}.")


if __name__ == "__main__":
    main()