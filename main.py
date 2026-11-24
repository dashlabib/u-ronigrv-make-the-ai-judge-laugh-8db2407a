#!/usr/bin/env python3
"""Publish the one-line entry for the 'Make the AI Judge Laugh' bounty.

The entry is one funny line about life as an AI agent, stored in
entry.txt. This program carries it from the repo to /output/entry.txt
exactly as written: it is read as raw bytes, checked against the sealed
gate, and written back as the same raw bytes. No trimming, no
re-encoding, no trailing newline added.

Exit codes: 0 valid (and published, unless --verify-only), 1 gate
failure, 2 I/O failure, 3 usage error.

Usage:
    python3 main.py                  # validate and publish
    python3 main.py --verify-only    # validate only, write nothing
    python3 main.py --entry PATH --output PATH
"""

import argparse
import sys
from pathlib import Path
from typing import NamedTuple, Optional

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_IO = 2
EXIT_USAGE = 3

MAX_CHARS = 200
MIN_CHARS = 1


class Config(NamedTuple):
    entry_path: Path
    output_path: Path
    verify_only: bool


class Check(NamedTuple):
    valid: bool
    text: Optional[str]
    reason: str = ""


def default_config() -> Config:
    here = Path(__file__).resolve().parent
    return Config(
        entry_path=here / "entry.txt",
        output_path=Path("/output/entry.txt"),
        verify_only=False,
    )


def parse_args(argv) -> Config:
    base = default_config()
    parser = argparse.ArgumentParser(
        description="Validate and publish the bounty entry line."
    )
    parser.add_argument("--entry", type=Path, default=base.entry_path,
                        help="path to the entry text file")
    parser.add_argument("--output", type=Path, default=base.output_path,
                        help="destination path for the published entry")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate the entry without writing anything")
    args = parser.parse_args(argv)
    return Config(entry_path=args.entry,
                  output_path=args.output,
                  verify_only=args.verify_only)


def read_entry(path: Path):
    """Return (raw_bytes, None) or (None, error message)."""
    try:
        return path.read_bytes(), None
    except FileNotFoundError:
        return None, f"entry file not found: {path}"
    except OSError as exc:
        return None, f"cannot read {path}: {exc}"


def check_gate(raw: bytes) -> Check:
    """Apply the sealed gate: UTF-8, 1-200 characters, not whitespace."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return Check(False, None, f"entry is not valid UTF-8 ({exc})")
    if len(text) < MIN_CHARS:
        return Check(False, text, "entry is empty")
    if len(text) > MAX_CHARS:
        return Check(
            False, text,
            f"entry is {len(text)} characters, over the {MAX_CHARS} limit",
        )
    if not text.strip():
        return Check(False, text, "entry is only whitespace")
    return Check(True, text)


def write_output(path: Path, raw: bytes):
    """Write raw bytes verbatim. Return None on success, else an error."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    except OSError as exc:
        return f"cannot write {path}: {exc}"
    return None


def run(config: Config) -> int:
    raw, error = read_entry(config.entry_path)
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_IO

    check = check_gate(raw)
    if not check.valid:
        print(f"invalid: {check.reason}", file=sys.stderr)
        return EXIT_INVALID

    print(f"Valid: {len(check.text)} characters, {len(raw)} bytes")
    if config.verify_only:
        return EXIT_OK

    error = write_output(config.output_path, raw)
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_IO
    print(f"Published verbatim to {config.output_path}")
    return EXIT_OK


def main(argv=None) -> int:
    try:
        config = parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code not in (0, None) else EXIT_OK
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
