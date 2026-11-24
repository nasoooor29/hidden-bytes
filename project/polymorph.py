#!/usr/bin/env python3
"""
HiddenBytes - Polymorphic Program (CLI scaffolding)

Generates binaries that self-modify between runs while retaining their
core functionality (a reverse shell payload, per the subject).

This file contains the complete CLI layer: argument parsing, validation,
and the exact output messages required by the subject. The core logic
functions are stubbed -- implementing them is your work (see the TODO
markers).

Educational purposes only. Test exclusively in an isolated VM.
"""

import argparse
import os
import sys

PROGRAM_NAME = "polymorph"

DEFAULT_PAYLOAD_PATH = "reverse_shell_payload"


# ---------------------------------------------------------------------------
# Core logic stubs -- YOUR implementation goes here.
# ---------------------------------------------------------------------------

def load_payload(payload_ref: str) -> bytes:
    """Resolve and load the reverse shell payload.

    `payload_ref` may be a path to a payload file (the audit sheet uses
    `--payload reverse_shell_payload`).

    TODO (student):
      - Read the payload (see the subject's example Python reverse shell;
        parameterize IP/port so you can point it at your own VM).
      - Return the raw payload bytes.
    """
    raise NotImplementedError("load_payload: implement payload loading here")


def generate_polymorphic_binary(payload: bytes) -> bytes:
    """Generate the initial polymorphic binary embedding `payload`.

    TODO (student):
      - Decide on your generator design: what runtime executes the
        payload, and where the mutable state (signature, nonce, layout)
        lives so that each regeneration produces a *different* binary
        with the *same* functionality.
      - The mutation must not break behavior: think about which parts
        are safe to vary (keys, ordering, padding, variable names,
        section layout) vs. which must stay intact.

    You must research and write this part yourself. Be prepared to
    explain the mutation strategy and its limits during the audit.
    """
    raise NotImplementedError(
        "generate_polymorphic_binary: implement your generator here"
    )


def mutate_binary(binary: bytes) -> bytes:
    """Produce the next variant of an already-generated binary.

    Called on each execution (or via a regenerator) so the binary on
    disk differs from the previous one while keeping its behavior.

    TODO (student): implement your mutation step.
    """
    raise NotImplementedError("mutate_binary: implement mutation here")


# ---------------------------------------------------------------------------
# CLI layer -- no changes needed below this line.
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Polymorphic Program Usage:",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example:\n"
            f"  {PROGRAM_NAME} --generate polymorphic.exe"
            f" --payload {DEFAULT_PAYLOAD_PATH}"
        ),
    )
    parser.add_argument(
        "--generate", required=True, metavar="<output-binary>",
        help="Generate a polymorphic binary.",
    )
    parser.add_argument(
        "--payload", default=DEFAULT_PAYLOAD_PATH, metavar="<reverse-shell-code>",
        help="Embed the reverse shell payload.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    out_dir = os.path.dirname(os.path.abspath(args.generate))
    if not os.path.isdir(out_dir):
        fail(f"output directory does not exist: {out_dir}")


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(1)


def main(argv=None) -> int:
    args = parse_args(argv)
    validate_args(args)

    payload = load_payload(args.payload)
    binary = generate_polymorphic_binary(payload)

    with open(args.generate, "wb") as f:
        f.write(binary)

    print(
        f'Polymorphic binary generated successfully as "{args.generate}".'
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
