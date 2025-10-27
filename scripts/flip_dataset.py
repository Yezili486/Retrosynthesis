"""Utility script to flip FlowER dataset files for retrosynthesis.

Input files are plain-text FlowER datasets where each non-empty line looks like
```
reactant1.reactant2>>product|sequence_idx
```
The script swaps the fragments around the ``>>`` arrow and writes new text files
with
```
product>>reactant1.reactant2|sequence_idx
```
so that the *output* directory holds retrosynthesis-ready files.

Example directory-to-directory usage::

    python scripts/flip_dataset.py \
        --input-dir data/USPTO \
        --output-dir data/USPTO_retrosyn \
        --files train.txt val.txt test.txt beam.txt

中文使用示例：

1. 确保当前目录在项目根目录（含有 ``scripts/`` 文件夹）。
2. 执行命令：

   ``python scripts/flip_dataset.py --input-dir data/USPTO --output-dir data/USPTO_retrosyn --files train.txt val.txt test.txt beam.txt``

   - ``--input-dir`` 指向原始正向数据所在的文件夹。
   - ``--output-dir`` 指向想要保存翻转后数据的文件夹（不存在会自动创建）。
   - ``--files`` 后面列出需要翻转的文件名，可以一次写多个。
3. 如果想先预览结果，可在命令末尾加上 ``--dry-run``，脚本只会打印示例而不写入文件。

Every file is copied to the output directory with its original name but with
the arrow direction flipped. Blank lines and comments (starting with ``#``) are
preserved byte-for-byte.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flip FlowER dataset files so that products appear on the left "
            "of the reaction arrow."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory that contains the original FlowER dataset files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "Directory where flipped files will be written. It will be "
            "created if it does not exist."
        ),
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help=(
            "One or more dataset filenames (e.g. train.txt val.txt beam.txt) "
            "to flip."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, preview the first flipped line for each file without writing.",
    )
    return parser.parse_args()


def flip_reaction_line(line: str) -> str:
    """Flip a single FlowER reaction line.

    Args:
        line: The raw line (including trailing newline).

    Returns:
        The flipped line with left/right sides swapped, keeping suffixes such as
        sequence indices intact.
    """
    stripped = line.rstrip("\n")
    if not stripped or stripped.startswith("#"):
        return line

    reaction_part: str
    suffix: str
    if "|" in stripped:
        reaction_part, suffix = stripped.split("|", 1)
        suffix = "|" + suffix
    else:
        reaction_part, suffix = stripped, ""

    if ">>" not in reaction_part:
        raise ValueError(f"Line does not contain '>>': {line!r}")

    left, right = reaction_part.split(">>", 1)
    flipped = f"{right}>>{left}{suffix}"
    return flipped + ("\n" if line.endswith("\n") else "")


def flip_file(input_path: Path, output_path: Path, dry_run: bool = False) -> None:
    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    flipped: Iterable[str] = (flip_reaction_line(line) for line in lines)

    if dry_run:
        for original, converted in zip(lines, flipped):
            print(f"[DRY-RUN] {input_path.name}: {original.strip()} -> {converted.strip()}")
            break
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(flipped), encoding="utf-8")
    print(f"Wrote flipped file: {output_path}")


def main() -> None:
    args = parse_args()

    if not args.input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")

    if args.dry_run:
        print("Performing dry run. No files will be written.")

    for filename in args.files:
        input_path = args.input_dir / filename
        if not input_path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {input_path}")
        output_path = args.output_dir / filename
        flip_file(input_path, output_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
