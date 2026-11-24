#!/usr/bin/env python3
"""
Generates simple_program.exe / simple_program.py -- the benign "Hello,
World!" target binary the audit sheet asks you to prepare for testing
the evasion program.

Usage:
    python3 make_test_program.py [output.py]
"""

import sys


TEMPLATE = '''#!/usr/bin/env python3
"""Simple benign test program (prints Hello, World!)."""

print("Hello, World!")
'''


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "simple_program.py"
    with open(out, "w") as f:
        f.write(TEMPLATE)
    print(f"Test program written to {out!r}.")
    print("Run it with: python3 " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
