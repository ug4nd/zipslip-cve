#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import zipfile
from dataclasses import dataclass
from typing import List, Union


@dataclass
class FileEntry:
    """An entry sourced from an existing file on disk."""
    source_path: str
    arcname: str


@dataclass
class TextEntry:
    """An entry whose content is a literal string given on the command line."""
    content: str
    arcname: str


Entry = Union[FileEntry, TextEntry]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zipslip.py",
        description=(
            "Build a ZIP archive whose entries use arcnames you choose, "
            "independent of the real on-disk filename. Educational tool "
            "for testing ZIP-extraction code against path-traversal-style "
            "entry names (the 'Zip Slip' pattern)."
        ),
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        metavar="ARCHIVE.zip",
        help="Path of the ZIP archive to create.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="After writing the archive, print zipfile.namelist() for it.",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite the output archive if it already exists.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Repeatable sub-commands; combine several in one invocation "
             "by listing them one after another.",
    )

    # Note: argparse doesn't natively support "repeat this subcommand
    # many times in one invocation" the way git-style tools do, so we
    # implement our own lightweight multi-command parsing in main()
    # instead of relying on subparsers for the repeated case. We still
    # define them here so `--help` documents the sub-command syntax.
    add_p = subparsers.add_parser(
        "add", help="Add an existing file under a chosen arcname."
    )
    add_p.add_argument("source", help="Path to the file on disk to add.")
    add_p.add_argument(
        "--as", dest="arcname", required=True,
        help="Entry name (arcname) to store the file under in the archive.",
    )

    addtext_p = subparsers.add_parser(
        "add-text", help="Add a literal string as a file's content."
    )
    addtext_p.add_argument("text", help="Literal text content for the entry.")
    addtext_p.add_argument(
        "--as", dest="arcname", required=True,
        help="Entry name (arcname) to store the text under in the archive.",
    )

    return parser


def parse_entries(argv: List[str]) -> tuple[str, bool, bool, List[Entry]]:
    """Parse a command line that may contain multiple repeated
    `add ... --as ...` / `add-text ... --as ...` sub-commands, plus the
    global `-o/--output`, `--list`, and `-f/--force` flags, which may
    appear anywhere.

    Returns (output_path, list_flag, force_flag, entries).
    """
    output_path = None
    list_flag = False
    force_flag = False
    entries: List[Entry] = []

    i = 0
    n = len(argv)
    while i < n:
        tok = argv[i]
        if tok in ("-o", "--output"):
            if i + 1 >= n:
                raise SystemExit(f"error: {tok} requires a value")
            output_path = argv[i + 1]
            i += 2
            continue
        if tok == "--list":
            list_flag = True
            i += 1
            continue
        if tok in ("-f", "--force"):
            force_flag = True
            i += 1
            continue
        if tok in ("-h", "--help"):
            build_parser().print_help()
            raise SystemExit(0)
        if tok == "add":
            if i + 1 >= n:
                raise SystemExit("error: 'add' requires a source file path")
            source = argv[i + 1]
            j = i + 2
            arcname = None
            if j + 1 < n and argv[j] == "--as":
                arcname = argv[j + 1]
                j += 2
            else:
                raise SystemExit("error: 'add' requires --as <arcname>")
            entries.append(FileEntry(source_path=source, arcname=arcname))
            i = j
            continue
        if tok == "add-text":
            if i + 1 >= n:
                raise SystemExit("error: 'add-text' requires a text value")
            text = argv[i + 1]
            j = i + 2
            arcname = None
            if j + 1 < n and argv[j] == "--as":
                arcname = argv[j + 1]
                j += 2
            else:
                raise SystemExit("error: 'add-text' requires --as <arcname>")
            entries.append(TextEntry(content=text, arcname=arcname))
            i = j
            continue
        raise SystemExit(f"error: unexpected argument: {tok!r}")

    if output_path is None:
        raise SystemExit("error: -o/--output is required")
    if not entries:
        raise SystemExit("error: no entries given (use 'add' and/or 'add-text')")

    return output_path, list_flag, force_flag, entries


def build_archive(output_path: str, entries: List[Entry], force: bool) -> None:
    import os

    if os.path.exists(output_path) and not force:
        raise SystemExit(
            f"error: {output_path!r} already exists (use -f/--force to overwrite)"
        )

    with zipfile.ZipFile(output_path, mode="w") as zf:
        for entry in entries:
            if isinstance(entry, FileEntry):
                # Standard library call: arcname is stored as-is in the
                # archive's central directory, independent of source_path.
                zf.write(entry.source_path, arcname=entry.arcname)
            elif isinstance(entry, TextEntry):
                zf.writestr(entry.arcname, entry.content)
            else:  # pragma: no cover - exhaustive by construction
                raise TypeError(f"unknown entry type: {entry!r}")


def main(argv: List[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if not argv or argv[0] in ("-h", "--help"):
        build_parser().print_help()
        return 0

    output_path, list_flag, force_flag, entries = parse_entries(argv)
    build_archive(output_path, entries, force_flag)

    print(f"Wrote {output_path} with {len(entries)} entr"
          f"{'y' if len(entries) == 1 else 'ies'}.")

    if list_flag:
        with zipfile.ZipFile(output_path, mode="r") as zf:
            print("Archive namelist():")
            for name in zf.namelist():
                print(f"  {name!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
