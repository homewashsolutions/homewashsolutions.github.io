from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "photo_input"
OUTPUT_DIR = BASE_DIR / "assets" / "resultados"
TARGET_SIZE = (1200, 900)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def slugify(filename: str) -> str:
    normalized = filename.lower().strip()
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


def process_image(source_path: Path, output_path: Path) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.autocontrast(image, cutoff=1)
        image = crop_to_ratio(image, *TARGET_SIZE)
        image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        image = ImageEnhance.Contrast(image).enhance(1.05)
        image = ImageEnhance.Color(image).enhance(1.03)
        image = ImageEnhance.Sharpness(image).enhance(1.08)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "WEBP", quality=86, method=6)


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_files = sorted(
        path for path in INPUT_DIR.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not source_files:
        print("Nenhuma foto encontrada em photo_input.")
        print("Coloque imagens JPG, JPEG, PNG ou WEBP nessa pasta e execute novamente.")
        return

    for source_path in source_files:
        output_name = f"{slugify(source_path.stem)}.webp"
        output_path = OUTPUT_DIR / output_name
        process_image(source_path, output_path)
        print(f"OK: {source_path.name} -> assets/resultados/{output_name}")

    print("Tratamento concluido.")
    print("As imagens prontas estao em assets/resultados.")


if __name__ == "__main__":
    main()