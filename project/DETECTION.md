# Detection & Defense Guide (DETECTION.md)

The defensive counterpart to this project. A "Binary Analyst" presents offense
*and* defense — this document is the defense half, and it's also how you'd
catch the exact tools in this repository.

---

## 1. Static triage: what analysts look at first

| Signal | Healthy binary | Suspicious |
|---|---|---|
| Section entropy | ~5–7 bits/byte (code/data mix) | Uniform >7.2 (packed/encrypted) or a huge 0.0-entropy overlay (padding trick) |
| File size | Matches its imports/sections | Tens–hundreds of MB with no corresponding resources |
| Import table | Rich, meaningful imports | Empty/minimal imports (all resolved at runtime) + `VirtualAlloc`/`CreateProcess` |
| Overlay | Absent or small (certs) | Large arbitrary blob appended after last section |
| Timestamps/sections | Consistent | Mismatched compiler signatures, renamed sections |

Tools: `pestudio`, `pefile` (Python), `Detect It Easy`, `diec`, or the included
`analyze_entropy.py` for the entropy picture.

## 2. Entropy analysis in practice

Shannon entropy per section:

```
H = -Σ p(b) · log2(p(b))    # p(b) = frequency of byte b, H ∈ [0, 8]
```

- Native x64 `.text`: typically 5.5–6.5
- AES/compressed blob: 7.5–7.9 (near-random)
- 0x00-filled padding: 0.0

**Rule of thumb:** an executable whose code section is *also* uniformly
high-entropy is packed or encrypted until proven otherwise. Conversely, an
executable with a giant zero-entropy overlay is padding-bombed. My evasion
program triggers exactly these two signals — run:

```sh
python3 analyze_entropy.py evaded_program.exe
python3 analyze_entropy.py simple_program.py   # compare with the benign original
```

## 3. YARA rules for crypter-like artifacts

Example rules an analyst could write against this class of tool (structure-
and behavior-based, *not* byte-exact — so polymorphism doesn't beat them):

```yara
rule Suspicious_Large_Zero_Overlay {
    meta:
        description = "Executable with anomalously large low-entropy overlay"
        author = "Binary Analyst (HiddenBytes project)"
    condition:
        uint16(0) == 0x5A4D and                       // MZ
        filesize > 50 * 1024 * 1024 and
        math.mean(0, filesize) < 1                    // overlay of ~zero bytes
}

rule Suspicious_High_Entropy_Code_Section {
    meta:
        description = "Code section is uniformly high-entropy (packed/encrypted)"
        author = "Binary Analyst (HiddenBytes project)"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0 .. pe.number_of_sections - 1) :
            ( pe.section[i].name == ".text" and
              math.entropy(pe.section[i].raw_data_offset,
                           pe.section[i].raw_data_size) > 7.2 )
}
```

The lesson (and an audit talking point): **byte-exact signatures die to
polymorphism; structural/behavioral rules survive it.**

## 4. Behavioral detection

- **Memory scanning**: engines (Defender AMSI/ETW integration, EDR) inspect
  process memory after allocation — the decrypted payload is visible even when
  the disk copy isn't.
- **Emulation with time acceleration**: sandboxes fast-forward sleeps instead
  of abandoning the sample; my `--delay 101` trick fails against elastic time.
- **EDR telemetry**: unsigned binary → spawns interpreter → opens socket →
  redirects stdio: a chain of events no legitimate program needs.
- **Cloud verdicts**: Defender cloud protection correlates unknown samples
  with telemetry from millions of endpoints.

## 5. Mitigations for stakeholders (the "recommendations" the audit asks for)

1. **Application control**: AppLocker/WDAC allowlisting kills unsigned
   user-written executables regardless of obfuscation.
2. **Keep Defender cloud + tamper protection ON** — the local scan is only
   half the engine.
3. **Least privilege**: users without admin rights can't disable protections
   or run most payloads usefully.
4. **Network egress control**: reverse shells need outbound sockets; a
   lab/corp network default-deny egress policy makes them inert.
5. **Monitor for the triage-evasion tells**: oversized executables, binaries
   with empty import tables, samples that sleep past analysis budgets —
   treat "boring-looking" as a signal, not an exemption.
6. **User education**: the delivery vector is still usually the user.

## 6. Responsible disclosure position

We publish detection logic *alongside* the offensive scaffolding because that
pairing is the point of the exercise. If you operate a SOC and encounter
artifacts resembling this project's output, the rules in §3 and the triage
table in §1 are a starting point for your own tuning — validate against your
own baseline before deploying.
