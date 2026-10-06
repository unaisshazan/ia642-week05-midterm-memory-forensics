# IA 642 Week 05 Midterm - Memory Forensics (WannaCry / Stuxnet)

Eastern Michigan University · Defensive Security · Fall 2026

**Author:** Unais Ali (E02805019)

**Public repo:** https://github.com/unaisshazan/ia642-week05-midterm-memory-forensics

## What this is

Week 05 midterm: Volatility 2.6 analysis of two Windows XP classroom memory images (`wcry.vmem`, `stuxnet.vmem`), with confirmation runs inside SIFT Workstation (`vol.py`), plus Parts C-D dossier / ATT&CK / CISO memo.

## Submission

| File | Description |
|------|-------------|
| `Ali_IA642_Midterm_MemoryForensics.pdf` | Graded midterm report (LaTeX) |
| `SUBMIT_Ali_IA642_Midterm_MemoryForensics.pdf` | Same PDF (Canvas submit copy) |
| `figures/` | Evidence screenshots used in the report (host Vol2 + SIFT GUI) |
| `output/wcry/` | WannaCry Volatility 2.6 text outputs |
| `output/stuxnet/` | Stuxnet Volatility 2.6 text outputs (hashes only for malfind dumps) |
| `output/sift/` | SIFT `vol.py` confirmation outputs |
| `output/command_log.txt` | Analysis command log excerpt |
| `EVIDENCE_HASHES.txt` | SHA-256 of Canvas dumps (dumps not published) |
| `latex/` | Report build sources |

## Not published

- Raw memory images (`wcry.vmem`, `stuxnet.vmem`, `memory_dump.zip`)
- Extracted malfind region binaries (`.dmp`)
- Symantec dossier PDF (course handout)

Hashes of the dumps are in `EVIDENCE_HASHES.txt` so results can be verified against Canvas artifacts.

## Tools

- Volatility 2.6 (`vol26.exe` / SIFT `vol.py`), profile `WinXPSP2x86`
- SIFT Workstation (VirtualBox import of course OVA)
- VirusTotal hash-only lookups (no sample upload)

## Key findings (summary)

**WannaCry (`wcry.vmem`):** `tasksche.exe` (PID 1940) → `@WanaDecryptor@` (PID 740); exited helpers via psscan/ExitTime; TCP/445 on System PID 4.

**Stuxnet (`stuxnet.vmem`):** triple `lsass.exe` (genuine PID 680 under winlogon; counterfeits 868 / 1928 under services.exe); malfind RWX/MZ in counterfeits; `mrxnet.sys` / `mrxcls.sys` in modules/modscan.
