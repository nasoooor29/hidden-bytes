# Binary Analyst — Role-Play Preparation

Prepared answers for every question in `AUDIT.md`, plus deeper material to
handle follow-ups. Practice saying these out loud; the audit grades
communication as much as knowledge.

---

## 1. "How does your evasion program encrypt and modify binaries to bypass detection?"

**Short answer:** It's a three-stage crypter. Stage 1 encrypts the target with
AES-256-CBC (fresh random IV, key embedded in the stub). Stage 2 wraps the
ciphertext in a small loader stub that sleeps for the configured delay,
decrypts the payload *in memory*, and executes it — so on disk the file only
ever contains ciphertext. Stage 3 appends padding to reach the requested size
via the PE overlay, which the Windows loader ignores.

**If pressed:** The detection-bypass mechanism is not magic — it's exploiting
*cost heuristics*. AV pipelines triage huge volumes with cheap proxies: static
signatures (defeated by encryption), file size (defeated by padding — some
scanners skip or shallow-scan very large files), and sandbox execution time
(defeated by the delay — the interesting behavior happens after the budget
expires). Each feature maps to one proxy. I can name which one for each flag
in my CLI.

## 2. "What techniques did you use to evade antivirus detection, and how do they work?"

1. **Encryption of the payload** → defeats exact-byte signature matching,
   because the malicious bytes never exist statically on disk.
2. **In-memory decryption** → the plaintext payload only exists in memory,
   so disk-scanning engines see nothing.
3. **Execution delay** → outlives sandbox wall-clock budgets (typically 1–5
   min); documented in the CIA "Bypassing Antivirus Dynamics" memo.
4. **File-size manipulation** → pushes the sample past triage thresholds and
   alters entropy profile; filler entropy is a deliberate choice (see Q6).

**Honest limitation (say this proactively — it earns trust):** none of this
defeats behavioral detection, memory scanning, or ML classifiers. Modern
Defender does all three, which is why such crypters have a short shelf life.

## 3. "Can you explain how your polymorphic program generates self-modifying binaries?"

**Short answer:** I separate the program into an *immutable behavioral core*
(payload logic, control flow, IP/port constants) and a *mutable shell*
(per-variant key/IV, padding nonce, dead-code ordering, names). Each generation
or regeneration re-randomizes the mutable shell, so two variants share zero
meaningful static signature bytes while passing the same functional test —
connect to my lab IP:port and spawn the shell. I verify every variant against
that functional test, because "polymorphic but broken" is the classic failure
mode.

**If pressed on how mutation happens:** the generator writes variant N; on
execution it can call the mutation routine to rewrite variant N+1 to disk.
The mutation surface is strictly limited to the safe set (I keep a table of
mutable vs. immutable components — see README) precisely so behavior cannot
break.

## 4. "What are the ethical and legal implications of developing such programs?"

- Legal: unauthorized computer access is criminalized broadly (CFAA in the US,
  French Penal Code art. 323-1 ff., Moroccan Law 07-03, EU Directive 2013/40).
  Malware *distribution* is separately criminalized even without intrusion.
- Ethical: dual-use knowledge is legitimate when scoped — isolated lab,
  consented targets, minimal payload, documentation of limitations, and a
  defensive counterpart. My repository deliberately pairs every offensive
  technique with its detection strategy (DETECTION.md).
- I state plainly that I did not (and would not) optimize this for real-world
  stealth, and that VirusTotal submissions of lab-made files are shared
  publicly with vendors, so nothing beyond my own generated artifacts was ever
  uploaded.

## 5. "How would you recommend detecting and defending against similar techniques?"

(Summary — full detail in DETECTION.md)
1. **Entropy monitoring**: encrypted payloads push sections above ~7.2
   bits/byte. Flag executables with uniformly high-entropy sections, and
   *low-entropy* giant overlays too (my padding trick).
2. **Behavior over bytes**: YARA rules on structure/behavior, not exact bytes;
   memory scanning after unpacking; emulate past sleeps with time acceleration.
3. **Watch the sleeps**: score samples that delay execution out of sandbox
   budgets as suspicious instead of skipping them.
4. **For SOC**: EDR telemetry on process spawning shell from unsigned binaries;
   AppLocker/WDAC allowlisting; keep Defender cloud protection and tamper
   protection on.

## 6. Follow-ups you should be ready for

**"Why AES and not your own cipher?"** — Correctness. Hand-rolled ciphers fail
in ways that are hard to verify; AES-256-CBC with random IV is
correct-by-construction. I implemented a toy Feistel network as the bonus to
*demonstrate* the concepts (key scheduling, diffusion), but I'd never trust it
with confidentiality.

**"Where is your key stored and is that secure?"** — Embedded in the stub, so
security-by-analysis-cost, not secrecy. An analyst who has the stub can
recover it. This is the fundamental limit of every on-host crypter: the
defender has the binary. I can show exactly where in my code this happens.

**"What does entropy actually measure and why do you care?"** — Shannon
entropy of the byte distribution: H = −Σ p·log2(p), 0–8 bits/byte. Native code
sits ~5–7; AES ciphertext ~7.8+; 0x00 padding = 0. Static engines flag both
extremes in the wrong places — which is why my padding strategy and my
`analyze_entropy.py` tool both exist.

**"How did you verify functionality is preserved across variants?"** — One
canonical functional test: listener up on the lab IP:port, run variant, assert
shell connects and responds to `id`. Hash differs, behavior identical — that's
the acceptance criterion from the audit sheet, executed every regeneration.

**"What would you add with more time?"** — Per-variant section-layout
randomization, API hashing instead of plaintext imports in the stub, and — on
the defensive side — a YARA rule pack published alongside the tooling.

## 7. Demo script (rehearse this 5-minute flow)

1. Show the repo layout; name each file's role in one sentence.
2. Build the benign target (`make_test_program.py`), run evasion with
   `--add-size 101 --delay 101`, show the size delta with `ls -l`.
3. Run `analyze_entropy.py` on the original vs. the padded output — narrate
   the entropy numbers.
4. Start `nc -lvnp 4444`, generate the polymorphic binary, run it, show the
   shell. Regenerate → new sha256 → still works.
5. Close with DETECTION.md: "here's how I'd catch my own tool" — that's the
   Binary Analyst's actual job.
