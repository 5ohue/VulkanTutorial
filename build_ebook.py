#!/usr/bin/python
"""Generate EPUB and PDF ebooks from sources."""

from datetime import datetime
import json
import logging
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import subprocess
from dataclasses import dataclass
from subprocess import CalledProcessError
from re import Match
import shutil
import argparse
import sys
from make_parser import make_parser

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def convert_images(images_dir: Path, converted_image_dir: Path) -> None:
    """Convert all SVG images to PNGs."""

    if not converted_image_dir.exists():
        converted_image_dir.mkdir()

    for source_file in images_dir.glob("*"):
        if source_file.suffix == ".svg":
            dest_file = converted_image_dir / source_file.with_suffix(".png").name

            try:
                subprocess.check_output(
                    [
                        "inkscape",
                        f"--export-filename={dest_file.as_posix()}",
                        source_file.as_posix(),
                    ],
                    stderr=subprocess.STDOUT,
                )
            except FileNotFoundError:
                raise RuntimeError(
                    f"failed to convert {source_file.name} to {dest_file.name}: "
                    "inkscape not installed"
                )
            except CalledProcessError as e:
                raise RuntimeError(
                    f"failed to convert {source_file.name} to {dest_file.name}: "
                    f"inkscape failed: {e.output.decode()}"
                )
        else:
            shutil.copy(source_file, converted_image_dir / source_file.name)

    return converted_image_dir


@dataclass
class MarkdownChapter:
    title: str
    depth: int
    contents: str


def find_markdown_chapters(markdown_dir: Path) -> list[Path]:
    """Find all Markdown files and interpret them as chapters."""

    markdown_entries = list(markdown_dir.rglob("*"))
    markdown_entries.sort()

    markdown_chapters = []

    for markdown_path in markdown_entries:
        # Skip privacy policy (regardless of language)
        if markdown_path.name.startswith("95_"):
            continue

        title = markdown_path.stem.partition("_")[-1].replace("_", " ")
        depth = len(markdown_path.relative_to(markdown_dir).parts) - 1

        markdown_chapters.append(
            MarkdownChapter(
                title=title,
                depth=depth,
                contents=markdown_path.read_text() if markdown_path.is_file() else "",
            )
        )

    return markdown_chapters


def generate_markdown_preface() -> str:
    current_date = datetime.now().strftime("%B %Y")

    return "\n".join(
        [
            "% Vulkan Tutorial",
            "% Alexander Overvoorde",
            f"% {current_date}",
        ]
    )


def generate_markdown_chapter(
    chapter: MarkdownChapter, converted_image_dir: Path
) -> str:
    contents = f"# {chapter.title}\n\n{chapter.contents}"

    # Adjust titles based on depth of chapter itself
    if chapter.depth > 0:
        def adjust_title_depth(match: Match) -> str:
            return ("#" * chapter.depth) + match.group(0)

        contents = re.sub(r"#+ ", adjust_title_depth, contents)

    # Remove `C++ code` links
    contents = re.sub(r"\[C\+\+ code\](.*)", "", contents)

    # Fix image links
    contents = contents.replace("/images/", f"{converted_image_dir.as_posix()}/")
    contents = contents.replace(".svg", ".png")

    # Fix remaining relative links
    contents = contents.replace("(/code", "(https://vulkan-tutorial.com/code")
    contents = contents.replace("(/resources", "(https://vulkan-tutorial.com/resources")

    # Fix chapter references
    def fix_chapter_reference(match: Match) -> str:
        target = match.group(1).lower().replace("_", "-").split("/")[-1]
        return f"](#{target})"

    contents = re.sub(r"\]\(!([^)]+)\)", fix_chapter_reference, contents)

    return contents


def compile_full_markdown(
    markdown_dir: Path, markdown_file: Path, converted_image_dir: Path
) -> Path:
    """Combine Markdown source files into one large file."""

    markdown_fragments = [generate_markdown_preface()]

    for chapter in find_markdown_chapters(markdown_dir):
        markdown_fragments.append(
            generate_markdown_chapter(chapter, converted_image_dir)
        )

    markdown_file.write_text("\n\n".join(markdown_fragments))

    return markdown_file


def build_pdf(markdown_file: Path, tmp_dir: Path, lang: str, args: argparse.Namespace) -> Path:
    """Build combined Markdown file into a PDF."""

    pdf_file = tmp_dir / f"{lang}.pdf"
    ebook_dir = Path("ebook")

    try:
        typst_file1 = tmp_dir / f"{lang}.typ"

        # Initial file
        subprocess.check_output(
            [
                "pandoc",
                markdown_file.as_posix(),
                "-o",
                typst_file1.as_posix(),
            ]
        )

        # Add preamble
        ps = subprocess.Popen(
            [
                "cat",
                (ebook_dir / Path("preamble.typ")).as_posix(),
                (ebook_dir / Path("beginning.typ")).as_posix(),
                typst_file1.as_posix(),
            ],
            stdout=subprocess.PIPE
        )

        subprocess.check_output(
            [
                "typst",
                "compile",
                "-",
                pdf_file.as_posix()
            ],
            stdin=ps.stdout
        )

    except CalledProcessError as e:
        raise RuntimeError(
            f"failed to build {pdf_file}: pandoc failed: {e.output.decode()}"
        )

    return pdf_file


def main() -> None:
    parser = make_parser()
    args = parser.parse_args(sys.argv[1:])

    """Build ebooks."""
    raw_out_dir = Path("./tmp/")
    raw_out_dir.mkdir(parents=True, exist_ok=True)

    out_dir = Path(raw_out_dir)

    logging.info("converting svg images to png...")
    converted_image_dir = convert_images(
        Path("images"), out_dir / "converted_images"
    )

    languages = json.loads(Path("config.json").read_text())["languages"].keys()
    logging.info(f"building ebooks for languages {'/'.join(languages)}")

    for lang in languages:
        logging.info(f"{lang}: generating markdown...")
        markdown_file = compile_full_markdown(
            Path(lang), out_dir / f"{lang}.md", converted_image_dir
        )

        logging.info(f"{lang}: building pdf...")
        pdf_file = build_pdf(markdown_file, out_dir, lang, args)

        shutil.copy(pdf_file, f"ebook/vulkan_tutorial_{lang}.pdf")

    logging.info("done")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        logging.error(str(e))
