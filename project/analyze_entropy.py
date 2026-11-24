#!/usr/bin/env python3
"""
analyze_entropy.py -- defensive file analysis (HiddenBytes project).

Reports file size, overall Shannon entropy, per-slice entropy, and simple
binary-format observations (MZ/ELF magic, overlay size estimate). This is a
standard static-triage tool in a Binary Analyst's toolkit: it's how you *see*
the effects of encryption and padding on a file.

Usage:
    python3 analyze_entropy.py <file> [--slices 16]
"""

import argparse
import math
import os
import sys

MZ_MAGIC = b"MZ"
ELF_MAGIC = b"\x7fELF"


def shannon_entropy(data: bytes) -> float:
    """Shannon entropy in bits/byte over the given byte string."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    n = len(data)
    h = 0.0
    for count in freq:
        if count:
            p = count / n
            h -= p * math.log2(p)
    return h


def entropy_verdict(h: float) -> str:
    if h >= 7.2:
        return "very high -- likely encrypted or compressed"
    if h >= 6.5:
        return "high -- packed or encoded content possible"
    if h >= 4.0:
        return "typical for code/data"
    if h > 0.05:
        return "low -- repetitive content"
    return "near-zero -- padding or filler"


def histogram_bar(h: float, width: int = 30) -> str:
    filled = int(round(h / 8.0 * width))
    return "#" * filled + "." * (width - filled)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="analyze_entropy",
        description="Defensive static analysis: size, entropy, format hints.",
    )
    parser.add_argument("file", help="file to analyze")
    parser.add_argument("--slices", type=int, default=16,
                        help="number of slices for per-slice entropy (default: 16)")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.file):
        print(f"[ERROR] file not found: {args.file}", file=sys.stderr)
        return 1

    size = os.path.getsize(args.file)
    with open(args.file, "rb") as f:
        data = f.read()

    print(f"file      : {args.file}")
    print(f"size      : {size:,} bytes ({size / (1024 * 1024):.2f} MB)")
    if size == 0:
        print("entropy   : n/a (empty file)")
        return 0

    with open(args.file, "rb") as f:
        head = f.read(4)
    if head[:2] == MZ_MAGIC:
        print("format    : PE/MZ executable (Windows)")
    elif head[:4] == ELF_MAGIC:
        print("format    : ELF executable (Linux)")
    else:
        print("format    : not a known executable format (raw data)")

    overall = shannon_entropy(data)
    print(f"entropy   : {overall:.3f} bits/byte  [{histogram_bar(overall)}]")
    print(f"            verdict: {entropy_verdict(overall)}")

    print(f"\nper-slice entropy ({args.slices} slices):")
    slice_size = max(1, size // args.slices)
    for i in range(args.slices):
        chunk = data[i * slice_size:(i + 1) * slice_size]
        h = shannon_entropy(chunk)
        offset = i * slice_size
        print(f"  {offset:>12,}  {h:6.3f}  [{histogram_bar(h, 24)}]")

    # crude overlay estimate for PE files: report size after last non-zero run
    tail = data.rstrip(b"\x00")
    overlay_hint = size - len(tail)
    if overlay_hint > 1024:
        print(f"\nnote      : ~{overlay_hint:,} trailing zero bytes "
              f"(~{overlay_hint / (1024 * 1024):.2f} MB) -- possible padding/filler")

    return 0


if __name__ == "__main__":
    sys.exit(main())
