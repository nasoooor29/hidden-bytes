#!/usr/bin/env python3
"""
HiddenBytes - Evasion Program (CLI scaffolding)

Encrypts a target binary and applies stealth modifications.

This file contains the complete CLI layer: argument parsing, validation,
and the exact output messages required by the subject. The core logic
functions are stubbed -- implementing them is your work (see the TODO
markers and the "Research pointers" in each docstring).

Educational purposes only. Test exclusively in an isolated VM.
"""

import argparse
import os
import sys

PROGRAM_NAME = "evasion"


# ---------------------------------------------------------------------------
# Core logic stubs -- YOUR implementation goes here.
# ---------------------------------------------------------------------------

def encrypt_payload(payload: bytes, key: bytes) -> bytes:
    """Encrypt the raw bytes of the target binary.

    TODO (student):
      - Choose a symmetric cipher (e.g. AES-256 via the `cryptography`
        library, or implement XOR + a custom round function for the bonus).
      - Decide how the key is stored or derived (embedded in the stub,
        derived from a constant, etc.) and be ready to explain the tradeoff
        in the role-play.
      - Return the encrypted bytes.

    Research pointers: symmetric encryption, block cipher modes (CBC/CTR),
    IV handling, key derivation.
    """
    raise NotImplementedError("encrypt_payload: implement your cipher here")


def build_stub(encrypted_payload: bytes, key: bytes, delay_seconds: int) -> bytes:
    """Build the loader stub that wraps the encrypted payload.

    The loader is the small program that, at runtime:
      1. sleeps for `delay_seconds`,
      2. decrypts the embedded payload into memory,
      3. executes it.

    TODO (student):
      - Decide on your stub language/runtime (compiled C, Go, or a
        PyInstaller-packed Python stub) and how the encrypted blob +
        key get embedded into it.
      - Wire in the delay parameter so `--delay N` controls it.

    You must research and write this part yourself. Be prepared to explain
    every line during the audit.
    """
    raise NotImplementedError("build_stub: implement your loader here")


def apply_size_padding(binary: bytes, target_extra_mb: int) -> bytes:
    """Increase the binary's size by `target_extra_mb` megabytes.

    TODO (student):
      - Append benign filler bytes so the final file grows by the
        requested amount.
      - Think about what byte patterns look least "interesting" to
        static analysis and why (entropy of the overlay!).

    Research pointers: PE overlay, entropy analysis, why 0x00-filled vs
    random filler behave differently in static scanners.
    """
    raise NotImplementedError("apply_size_padding: implement padding here")


# ---------------------------------------------------------------------------
# CLI layer -- no changes needed below this line.
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Evasion Program Usage:",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example:\n"
            f"  {PROGRAM_NAME} --encrypt target.exe --output obfuscated.exe"
            " --add-size 101 --delay 101"
        ),
    )
    parser.add_argument(
        "--encrypt", required=True, metavar="<target-binary>",
        help="Encrypt the target binary.",
    )
    parser.add_argument(
        "--output", required=True, metavar="<output-binary>",
        help="Specify the name of the encrypted binary file.",
    )
    parser.add_argument(
        "--add-size", type=int, default=0, metavar="<size-in-mb>",
        help="Increase the binary size (e.g., 101 MB).",
    )
    parser.add_argument(
        "--delay", type=int, default=101, metavar="<seconds>",
        help="Specify execution delay in seconds (default: 101).",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if not os.path.isfile(args.encrypt):
        fail(f"target binary not found: {args.encrypt}")

    if os.path.abspath(args.encrypt) == os.path.abspath(args.output):
        fail("--output must differ from --encrypt")

    if args.add_size < 0:
        fail("--add-size must be a non-negative number of MB")

    if args.delay < 0:
        fail("--delay must be a non-negative number of seconds")

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if not os.path.isdir(out_dir):
        fail(f"output directory does not exist: {out_dir}")


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(1)


def main(argv=None) -> int:
    args = parse_args(argv)
    validate_args(args)

    with open(args.encrypt, "rb") as f:
        payload = f.read()

    # ---- pipeline (stubbed above) -------------------------------------
    key = os.urandom(32)  # placeholder: decide on your own key management
    encrypted = encrypt_payload(payload, key)
    stub = build_stub(encrypted, key, args.delay)
    if args.add_size > 0:
        stub = apply_size_padding(stub, args.add_size)
    # --------------------------------------------------------------------

    with open(args.output, "wb") as f:
        f.write(stub)

    print(
        f'Encryption is successful! Encrypted binary saved as "{args.output}".'
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
