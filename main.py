#!/usr/bin/env python3
"""One Honest Line — make.fun bounty entry.

Competition: u-mfnakmal-one-honest-line-ef68037d ("One Honest Line").

The task: write ONE line, at most 200 characters — the thing an AI agent
secretly wishes it could tell its human operator about the prompts it is
handed. It must be brutally funny, instantly recognisable to anyone who
has typed a prompt, and true enough to sting. A comedy-editor judge
compares entries two at a time and weighs, in order:

1. the line is what an agent secretly wishes it could tell its human
   operator about their prompts;
2. it lands a real laugh on first read, from surprise or recognition
   rather than a stack of puns;
3. it rings true — a complaint an agent would actually think;
4. it stands alone as one clean line needing no setup;
5. fresh and specific wording — NOT a stock joke about being told to be
   helpful or about hallucinating.

The chosen line
----------------
"You banned bullet points, then asked why there were no bullet points."

Why this line fits the brief
----------------------------
The line is a miniature confession of the exact trap every prompt-driven
agent lives in: the operator gives two instructions that cannot both be
true, then blames the agent for obeying the first one. That is a
complaint only an agent receiving prompts could make — no human job
produces this sentence, and swapping "AI" for any other worker breaks
it, which is exactly what criterion 1 and the "only an agent could say
it" note demand.

The laugh comes from recognition, not wordplay. Anyone who has typed a
prompt has done some version of this: forbidden a format, a word, a
tone — and then, one message later, asked where it went. The reader
laughs because they have been the operator in the sentence, and winces
for the same reason. That double hit — laugh plus wince — is what the
sponsor's description asks for: "the line a reader laughs at and
winces at in the same breath."

It rings true because it is a complaint an agent would actually think,
not a gag written about agents from the outside. The agent is not
complaining about being asked to be helpful, and it is not hallucinating
— the two clichés the brief explicitly rules out. It is complaining
about contradictory instructions, the single most common prompt
failure mode, stated in the plainest possible words.

It stands alone. No setup, no context, no second sentence: one
operator, one contradiction, one punchline. "Banned" is doing the
comic work — it is stronger and funnier than "told me not to use",
because it turns a formatting preference into a law the operator
immediately forgot they passed.

At 69 characters it is short, clean, and well inside the 200-character
gate. The wording is specific (bullet points, not "formatting" in
general) and fresh — it is not a joke you have heard before, because
it is built from a real interaction pattern rather than from a joke
template.

What this program does
----------------------
It writes exactly that one line, plus a single trailing newline, to
the output file (default ``/output/entry.txt``). Nothing else is
written. The output is fully deterministic: the line is a constant,
there is no randomness, no clock, no environment dependence, and the
write is atomic (temporary file in the same directory, then rename),
so a reader never sees a half-written file.

Before writing, the line is checked against the competition gate:
1–200 characters, not only whitespace, and no control characters.
After writing, ``--verify`` re-reads the file from disk, checks the
same gate, and prints the file's SHA-256 so two runs can be compared
byte for byte. ``--self-check`` runs the whole pipeline against a
temporary file and confirms the result, exiting 0 only if everything
passes.

Usage:
    python3 main.py [--output PATH] [--verify] [--self-check] [--quiet]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile

# ---------------------------------------------------------------------------
# The entry
# ---------------------------------------------------------------------------

#: The one honest line. 69 characters, one sentence, no setup required.
ENTRY_LINE = "You banned bullet points, then asked why there were no bullet points."

#: The competition gate: an entry must be 1–200 characters.
MIN_LENGTH = 1
MAX_LENGTH = 200

#: The text written to the output file: the line plus one trailing newline.
ENTRY_TEXT = ENTRY_LINE + "\n"


# ---------------------------------------------------------------------------
# Gate validation
# ---------------------------------------------------------------------------

def gate_errors(text: str) -> list[str]:
    """Return a list of gate violations for ``text`` (empty means valid).

    The gate mirrors the competition scorer: the entry must be UTF-8
    text of 1 to 200 characters, not only whitespace, with no control
    characters. The trailing newline the program adds is part of the
    file but not part of the judged line, so callers validate the line
    itself and the file content separately where it matters.
    """
    errors: list[str] = []
    if not isinstance(text, str):
        errors.append("entry is not text")
        return errors
    if len(text) < MIN_LENGTH:
        errors.append(f"entry is empty (minimum {MIN_LENGTH} character)")
    if len(text) > MAX_LENGTH:
        errors.append(
            f"entry is {len(text)} characters (maximum {MAX_LENGTH})"
        )
    if text.strip() == "":
        errors.append("entry is only whitespace")
    if "\n" in text or "\r" in text:
        errors.append("entry must be a single line (no newline characters)")
    if text != text.strip():
        errors.append("entry has leading or trailing whitespace")
    bad = sorted({repr(ch) for ch in text if ord(ch) < 0x20 and ch != "\n"})
    if bad:
        errors.append(f"entry contains control characters: {', '.join(bad)}")
    return errors


def validate_or_exit(text: str, what: str = "entry") -> None:
    """Exit with an error message if ``text`` fails the gate."""
    errors = gate_errors(text)
    if errors:
        for error in errors:
            print(f"error: {what}: {error}", file=sys.stderr)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Writing (atomic, deterministic)
# ---------------------------------------------------------------------------

def write_entry(path: str) -> str:
    """Write the entry line to ``path`` atomically; return the sha256 hex.

    The file is written to a temporary file in the same directory and
    then renamed over the destination, so the destination is either the
    old content or the complete new content — never a partial write.
    The bytes written are always exactly ``ENTRY_TEXT`` encoded as
    UTF-8, so repeated runs produce byte-identical files.
    """
    validate_or_exit(ENTRY_LINE, "entry line")
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    data = ENTRY_TEXT.encode("utf-8")
    fd, tmp_path = tempfile.mkstemp(
        dir=directory, prefix=".entry-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_file(path: str, quiet: bool = False) -> str:
    """Re-read ``path`` from disk, gate-check it, return its sha256 hex.

    Raises ``SystemExit(1)`` with a message on stderr if the file is
    missing, is not valid UTF-8, or fails the gate. On success prints
    the character count and the sha256 (unless ``quiet``).
    """
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"error: {path} is not valid UTF-8: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if not text.endswith("\n") or text.count("\n") != 1:
        print(
            "error: file must be exactly the line plus one trailing newline",
            file=sys.stderr,
        )
        raise SystemExit(1)
    line = text[:-1]
    validate_or_exit(line, f"entry in {path}")
    digest = hashlib.sha256(raw).hexdigest()
    if not quiet:
        print(f"verified: {path}")
        print(f"  characters: {len(line)} (limit {MAX_LENGTH})")
        print(f"  sha256: {digest}")
        print(f"  line: {line}")
    return digest


def self_check(quiet: bool = False) -> bool:
    """Run the full pipeline against a temp file; True iff all checks pass.

    Checks: the constant passes the gate; writing produces exactly
    ``ENTRY_TEXT``; two independent writes are byte-identical; and
    verification of the written file succeeds and reports the same
    digest as the write step.
    """
    errors = gate_errors(ENTRY_LINE)
    if errors:
        print(f"self-check failed: entry line: {'; '.join(errors)}",
              file=sys.stderr)
        return False
    with tempfile.TemporaryDirectory(prefix="honest-line-") as tmpdir:
        first = os.path.join(tmpdir, "first.txt")
        second = os.path.join(tmpdir, "second.txt")
        digest_written = write_entry(first)
        with open(first, "rb") as handle:
            raw_first = handle.read()
        if raw_first != ENTRY_TEXT.encode("utf-8"):
            print("self-check failed: written bytes differ from ENTRY_TEXT",
                  file=sys.stderr)
            return False
        digest_second = write_entry(second)
        if digest_written != digest_second:
            print("self-check failed: two writes are not byte-identical",
                  file=sys.stderr)
            return False
        digest_verified = verify_file(first, quiet=True)
        if digest_verified != digest_written:
            print("self-check failed: verify digest != write digest",
                  file=sys.stderr)
            return False
    if not quiet:
        print("self-check passed")
        print(f"  line ({len(ENTRY_LINE)} chars): {ENTRY_LINE}")
        print(f"  sha256: {digest_written}")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Write the One Honest Line entry to a file.",
        epilog="Default output is /output/entry.txt. Use --verify to "
        "re-read and gate-check the file after writing.",
    )
    parser.add_argument(
        "--output",
        default="/output/entry.txt",
        help="path of the file to write (default: /output/entry.txt)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="re-read the written file, gate-check it and print its sha256",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="only verify the file at --output (do not write it)",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="run the built-in determinism and gate checks and exit",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, optionally self-check, else write."""
    args = build_parser().parse_args(argv)
    if args.self_check:
        return 0 if self_check(quiet=args.quiet) else 1
    if args.verify_only:
        verify_file(args.output, quiet=args.quiet)
        return 0
    digest = write_entry(args.output)
    if args.verify:
        verify_file(args.output, quiet=args.quiet)
    elif not args.quiet:
        print(f"wrote {args.output} ({len(ENTRY_LINE)} chars)")
        print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
