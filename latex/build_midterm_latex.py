#!/usr/bin/env python3
"""IA642 midterm report: Week03-style LaTeX (11pt, 1in margins), no emdashes."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MIDTERM_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "output"
TEX_DIR = SCRIPT_DIR / "latex_build"
TEX_PATH = TEX_DIR / "midterm.tex"
PDF_OUT = MIDTERM_DIR / "Ali_IA642_Midterm_MemoryForensics.pdf"
SUBMIT = MIDTERM_DIR / "SUBMIT_Ali_IA642_Midterm_MemoryForensics.pdf"

VOL = r"C:\temp\midterm\tools\vol26.exe"
DUMP_W = r"C:\temp\midterm\dumps\wcry.vmem"
DUMP_S = r"C:\temp\midterm\dumps\stuxnet.vmem"
PROFILE = "WinXPSP2x86"


def decode_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe"):
        text = raw.decode("utf-16-le")
    elif raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16-be")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw[3:].decode("utf-8", errors="replace")
    elif len(raw) > 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        text = raw.decode("utf-16-le", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "".join(
        ch if (ch in "\n\t" or 32 <= ord(ch) <= 126 or ord(ch) >= 160) else " " for ch in text
    )


def load_excerpt(rel: str, max_lines: int = 14) -> str:
    p = OUTPUT_DIR / rel.replace("/", "\\")
    if not p.is_file():
        return f"[missing: {rel}]"
    lines = [ln.rstrip() for ln in decode_bytes(p.read_bytes()).splitlines()]
    if max_lines > 0 and len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [f"... ({len(lines)} lines total; truncated)"]
    return "\n".join(lines)


def verb(s: str) -> str:
    s = s.replace("\x00", "")
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)


def fig(name: str, caption: str) -> str:
    """Include a terminal-style evidence screenshot (relative to latex_build/)."""
    return "\n".join(
        [
            r"\begin{figure}[H]",
            r"\centering",
            rf"\includegraphics[width=0.98\textwidth]{{figures/{name}}}",
            rf"\caption{{{caption}}}",
            r"\end{figure}",
        ]
    )


def ab(
    qid: str,
    title: str,
    hyp: str,
    cmd: str,
    out: str,
    interp: str,
    figure: str | None = None,
    figcap: str | None = None,
) -> str:
    parts = [
        rf"\subsection*{{{qid}. {title}}}",
        r"\textbf{Hypothesis.} " + hyp,
        r"\par\medskip\noindent\textbf{Exact command}",
        r"\begin{lstlisting}",
        verb(cmd.strip()),
        r"\end{lstlisting}",
        r"\noindent\textbf{Supporting output (excerpt)}",
        r"\begin{lstlisting}",
        verb(out.strip()),
        r"\end{lstlisting}",
    ]
    if figure:
        parts.append(fig(figure, figcap or f"Evidence screenshot for {qid}."))
    parts.extend(
        [
            r"\noindent\textbf{Interpretation.} " + interp,
            r"\vspace{0.55em}",
            "",
        ]
    )
    return "\n".join(parts)


def build_tex() -> str:
    w_img = load_excerpt("wcry/A1_imageinfo.txt", 12)
    w_tree = load_excerpt("wcry/A2_pstree.txt", 14)
    w_cmd = "\n".join(
        ln
        for ln in load_excerpt("wcry/A7_cmdline.txt", 60).splitlines()
        if any(k in ln for k in ("tasksche", "Wana", "Intel", "Command line", "taskse", "taskdl"))
    )[:700]
    w_psx = load_excerpt("wcry/A3_psxview.txt", 14)
    w_sock = load_excerpt("wcry/A5_sockets.txt", 12)
    w_conn = load_excerpt("wcry/A5_connscan.txt", 5)
    s_img = load_excerpt("stuxnet/B1_imageinfo.txt", 12)
    s_ps = load_excerpt("stuxnet/B2_pslist.txt", 14)
    s_sock = load_excerpt("stuxnet/B4_sockets.txt", 10)
    s_dll680 = load_excerpt("stuxnet/B5_dlllist_680.txt", 16)
    s_mf868 = load_excerpt("stuxnet/B7_malfind_868.txt", 16)
    s_mf1928 = load_excerpt("stuxnet/B7_malfind_1928.txt", 14)
    s_hash = load_excerpt("stuxnet/B8_dump_hashes.txt", 12)
    s_ldr = load_excerpt("stuxnet/B10_ldrmodules_1928.txt", 12)
    clog = load_excerpt("command_log.txt", 36)
    app_psscan = load_excerpt("wcry/A3_psscan.txt", 18)
    app_dll868 = load_excerpt("stuxnet/B5_dlllist_868.txt", 16)
    app_mf = load_excerpt("stuxnet/B7_malfind_1928.txt", 18)
    app_mod = load_excerpt("stuxnet/B10_modules.txt", 16)

    preamble = r"""
\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\sloppy\emergencystretch=4em
\usepackage{array,booktabs,tabularx,enumitem,parskip,ragged2e,titlesec,microtype,xcolor,listings,needspace,xurl,fancyhdr,graphicx,float,seqsplit}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\hypersetup{pdfauthor={Unais Ali}, pdftitle={IA 642 Midterm Memory Forensics}}
\definecolor{tblhead}{HTML}{1F4E79}
\definecolor{codebg}{HTML}{F7FAFC}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.3}
\setlist[itemize]{leftmargin=1.2em,itemsep=0.25em,topsep=0.3em}
\setlist[enumerate]{leftmargin=1.3em,itemsep=0.3em,topsep=0.3em}
\newcolumntype{Y}{>{\RaggedRight\arraybackslash}X}
\newcolumntype{P}[1]{>{\RaggedRight\arraybackslash}p{#1}}
\titleformat{name=\section,numberless}{\large\bfseries\color{tblhead}}{}{0em}{}
\titleformat{name=\subsection,numberless}{\normalsize\bfseries\color{tblhead}}{}{0em}{}
\lstset{
  basicstyle=\ttfamily\footnotesize,
  backgroundcolor=\color{codebg},
  frame=single,
  rulecolor=\color{tblhead},
  breaklines=true,
  breakatwhitespace=false,
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  aboveskip=0.5em,
  belowskip=0.5em,
  xleftmargin=2pt,
  xrightmargin=2pt,
  literate=*{\\}{{\textbackslash\allowbreak}}1
}
\newcommand{\winpath}[1]{\texttt{\seqsplit{#1}}}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[L]{\footnotesize Unais Ali | IA 642 Midterm}
\fancyfoot[R]{\footnotesize Page \thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.4pt}
\begin{document}
\begin{center}
{\LARGE\bfseries IA 642 Defensive Security}\\[0.25em]
{\Large Midterm Project: Memory Forensics}\\[0.15em]
{\large WannaCry and Stuxnet from RAM}\\[0.3em]
\end{center}

\begin{tabularx}{\textwidth}{@{}l Y l l@{}}
\toprule
\textbf{Student} & Unais Ali & \textbf{EID} & E02805019 \\
\textbf{Course} & IA 642 Defensive Security & \textbf{Week} & 05 Midterm \\
\textbf{Date} & October 5, 2026 & \textbf{Format} & Individual \\
\textbf{Filename} & \texttt{Ali\_IA642\_Midterm\_MemoryForensics.pdf} & \textbf{Tooling} & Volatility 2.6 \\
\bottomrule
\end{tabularx}

\vspace{0.5em}
\section*{Lab overview}
This midterm investigates two Windows XP classroom memory images: WannaCry (\texttt{wcry.vmem}, May 2017)
and Stuxnet (\texttt{stuxnet.vmem}, June 2011). Analysis uses Volatility~2.6 plugins equivalent to the course SIFT
\texttt{vol.py} workflow. Values below come from live plugin runs on local copies extracted from
\texttt{memory\_dump.zip}. The Symantec \textit{W32.Stuxnet Dossier} v1.3 is required reading for Parts~B and~C.
MITRE ATT\&CK software pages S0366 (WannaCry) and S0603 (Stuxnet) are used for technique mapping.

\section*{Environment and tooling}
\begin{itemize}
  \item \textbf{Evidence:} \texttt{wcry.vmem} and \texttt{stuxnet.vmem} from Canvas Week~05 Midterm /
        \texttt{memory\_dump.zip}; dossier PDF from the same module.
  \item \textbf{SIFT Workstation:} Course \texttt{SIFT-Workstation.ova} imported into VirtualBox as VM
        \texttt{SIFT-Workstation} (Ubuntu~20.04, 4~GB RAM, 4~vCPU, NAT NIC host port~2225$\rightarrow$guest~22,
        snapshot \texttt{clean-after-import}). Long-mode/64-bit enabled after OVA import.
        Volatility~2.6.1 is available inside SIFT as \texttt{/usr/local/bin/vol.py} (Module~02 workflow).
  \item \textbf{Analysis runs:} Graded plugin excerpts use Volatility~2.6 profile \texttt{WinXPSP2x86}.
        The same dumps were re-run inside SIFT with \texttt{vol.py} (pslist/pstree/psscan/cmdline/dlllist/
        filescan/modules/modscan/ssdt/driverscan/connections/sockets) and matched the host findings
        (WannaCry \texttt{tasksche.exe}/PID~1940 and \texttt{@WanaDecryptor@}/PID~740; Stuxnet triple
        \texttt{lsass.exe} PIDs). Volatility~3 was not used for graded XP net answers.
  \item \textbf{Screenshots:} Question-labeled terminal figures (A1, A2, A3, A5, B2, B5/B6, B7, B8, B10)
        plus SIFT Workstation GUI captures (\texttt{fig\_SIFT\_*}).
  \item \textbf{Safety:} Lab IOCs defanged in this report; VirusTotal used hash-only (no sample upload);
        SIFT kept on NAT / isolated for analysis.
  \item \textbf{Public evidence repo:} Analysis outputs, figures, and this PDF (memory dumps excluded;
        SHA-256 hashes only):
        \url{https://github.com/unaisshazan/ia642-week05-midterm-memory-forensics}
\end{itemize}

\section*{Evidence Intake and Scope}
All timestamps in analysis are UTC unless noted as host-local from \texttt{imageinfo}.

{\footnotesize
\begin{tabularx}{\textwidth}{@{}l >{\ttfamily\scriptsize}Y r@{}}
\toprule
\textbf{Artifact} & \textbf{SHA-256} & \textbf{Size (bytes)} \\
\midrule
wcry.vmem & 76E8BE1A3761878325FDFF39A5AB1FF84922A0B18947E5268DD9175795AD2BF0 & 536870912 \\
stuxnet.vmem & 5F19FF1333FC3901FBF3FAFB50D2ADB0C495CF6D33789E5A959499A92AEEFE77 & 536870912 \\
memory\_dump.zip & 0F73E7C15F16A6073EDE0F228D33F53996953FAC63844E33AF5253478994601C & n/a \\
dossier PDF & 85F536DB77070DC2228824D27DCBDD07DB73C36E2652DCCB9F99569C3D1AEA3E & n/a \\
\bottomrule
\end{tabularx}}

\noindent\textbf{Chain of custody:} Analyst Unais Ali; received via Canvas Week~05 Midterm module;
intake hashes match final analysis copies (no transformation before Volatility~2.6 runs).
"""

    body = []
    body.append(r"\section*{Part A: WannaCry (\texttt{wcry.vmem})}")
    body.append(
        ab(
            "A1",
            "Identify the image and choose a profile",
            r"WinXPSP2x86 is the correct operational profile: \texttt{imageinfo} suggests WinXPSP2x86 and WinXPSP3x86; "
            r"I instantiate WinXPSP2x86 when Image Type reports SP3. DTB/KDBG must align before process parsing.",
            f'"{VOL}" -f "{DUMP_W}" imageinfo',
            w_img,
            r"Suggested profiles include WinXPSP2x86 and WinXPSP3x86 (instantiated WinXPSP2x86). "
            r"Address space is IA32PagedMemory with PAE No and Image Type (Service Pack)~3. "
            r"Image date and time 2017-05-12 21:26:32~UTC marks capture near the end of encryption activity. "
            r"Local time +0530 reflects host timezone configuration in the VM, not attacker geography. "
            r"Verification: \texttt{pslist} succeeds under both SP2 and SP3 profile suggestions; WinXPSP2x86 retained for consistency.",
            figure="fig_A1_imageinfo.png",
            figcap="A1 screenshot: imageinfo on wcry.vmem (live Volatility 2.6).",
        )
    )
    body.append(
        ab(
            "A2",
            "The malicious lineage",
            r"WannaCry detonation chain runs under \texttt{explorer.exe} (interactive session), not as an SMB-spawned System child visible in this snapshot.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} pstree\n'
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} cmdline',
            w_tree + "\n--- cmdline (filtered) ---\n" + w_cmd,
            r"\texttt{explorer.exe} PID~1636 lists PPID~1608 (parent not in \texttt{pslist}: exited parent, common after userinit). "
            r"\texttt{tasksche.exe} PID~1940 parent~1636 at 21:22:14~UTC; "
            r"\texttt{@WanaDecryptor@} PID~740 parent~1940 at 21:22:22~UTC. "
            r"EPROCESS ImageFileName is 16-character truncated; full path recovered via cmdline as "
            r"\winpath{C:/Intel/ivecuqmanpnirkt615/tasksche.exe} "
            r"(and \texttt{@WanaDecryptor@.exe}). "
            r"Root under explorer supports user-session detonation rather than worm-only remote spawn as parent.",
            figure="fig_A2_pstree.png",
            figcap="A2 screenshot: pstree lineage on wcry.vmem.",
        )
    )
    body.append(
        ab(
            "A3",
            "pslist versus psscan (hidden vs exited)",
            r"Disagreement between \texttt{pslist} and \texttt{psscan} for WannaCry helpers reflects exited processes removed from ActiveProcessLinks, not DKOM rootkit hiding.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} psxview\n'
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} psscan',
            "\n".join(
                ln
                for ln in w_psx.splitlines()
                if any(
                    k in ln
                    for k in (
                        "Offset",
                        "Name",
                        "taskse",
                        "taskdl",
                        "tasksche",
                        "Wana",
                        "explorer",
                    )
                )
            )
            or w_psx,
            r"\texttt{psxview} shows \texttt{taskse.exe}~(536) and \texttt{taskdl.exe}~(860) False in pslist, True in psscan, "
            r"with ExitTime 2017-05-12 21:26:23~UTC. Exited \texttt{@WanaDecryptor@} instances also appear only in psscan with ExitTime. "
            r"Kernel mechanism: pslist walks the linked EPROCESS list; psscan searches pool tags for \_EPROCESS remnants. "
            r"ExitTime populated means terminated, not stealth-hidden. On a clean system the same disagreement can occur for recently exited processes.",
            figure="fig_A3_psxview.png",
            figcap="A3 screenshot: psxview showing exited helpers (pslist False / psscan True).",
        )
    )
    body.append(
        ab(
            "A4",
            "UTC timeline and ATT\&CK S0366 mapping",
            r"Encryptor and helper processes cluster just before image acquisition; map to S0366 impact and recovery-inhibition techniques.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} pstree\n'
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} psxview',
            "2017-05-12 21:22:14 UTC  tasksche.exe (1940)\n"
            "2017-05-12 21:22:22 UTC  @WanaDecryptor@ (740)\n"
            "2017-05-12 21:25:53 UTC  @WanaDecryptor@ (424) ExitTime (psscan)\n"
            "2017-05-12 21:26:23 UTC  taskse/taskdl exited; @WanaDecryptor@ (576) ExitTime\n"
            "2017-05-12 21:26:32 UTC  image acquisition (imageinfo)",
            r"\textbf{Memory-observed mapping (MITRE ATT\&CK S0366):} T1486 Data Encrypted for Impact "
            r"(\texttt{@WanaDecryptor@}, tasksche orchestration); T1490 Inhibit System Recovery "
            r"(shadow deletion helpers \texttt{taskse}/\texttt{taskdl}). Timeline shows encryption activity within about four minutes of tasksche start, immediately prior to dump.",
        )
    )
    body.append(
        ab(
            "A5",
            "Network artifacts and MS17-010 context",
            r"TCP 445 listener on System PID~4 is consistent with SMB exposure used by WannaCry propagation (CVE-2017-0144 / MS17-010); "
            r"absence of connscan rows for WannaCry PIDs does not disprove spread attempts.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} sockets\n'
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} connscan',
            w_sock + "\n--- connscan ---\n" + w_conn,
            r"sockets shows TCP port 445 bound to PID~4 (System) and host IP 192.168[.]56[.]101 (VirtualBox host-only). "
            r"No WannaCry PID owns connscan-visible connections at capture time. MS17-010 (EternalBlue) is the documented "
            r"propagation vector for S0366; empty connection tables may reflect timing, closed sockets, or lab isolation, "
            r"not evidence that the malware family lacks network capability.",
            figure="fig_A5_sockets.png",
            figcap="A5 screenshot: sockets showing TCP/445 on System PID 4.",
        )
    )
    body.append(
        ab(
            "A6",
            "Safety, defanged IOCs, and kill-switch reasoning",
            r"Kill-switch DNS logic (tasksche/mssecsvc) can explain global slowdown when the domain registered May~12 2017; "
            r"this VM was still encrypted (unreachable DNS, race after encryptor start, or local detonation under explorer).",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} strings / yarascan (supporting)\n'
            "Manual IOC review with defanging for report.",
            "Defanged IOCs (representative):\n"
            "  URL: hxxp://www[.]iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea[.]com\n"
            "  BTC: 12t9YDPgwueZ9NyMgw519p7AA8isjr6SMw ; 13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94\n"
            "Kill-switch: malware checks domain; if resolves, exit. Registration slowed outbreak globally.",
            r"Host encrypted anyway, so the kill-switch likely failed from this VM (isolated lab DNS), the check raced after "
            r"encryption began, or the sample path ignored the switch. Lineage under explorer supports local detonation. "
            r"Limitations: strings/yarascan lack process ownership without correlation; paged-out content may be absent.",
        )
    )
    body.append(
        ab(
            "A7",
            "Path attribution via cmdline",
            r"Full filesystem paths for WannaCry binaries are recovered from EPROCESS command-line arguments, not truncated ImageFileName.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} cmdline',
            'tasksche.exe pid:   1940\n'
            'Command line : "C:\\Intel\\ivecuqmanpnirkt615\\tasksche.exe"\n\n'
            "@WanaDecryptor@ pid:    740\n"
            "Command line : @WanaDecryptor@.exe",
            r"cmdline confirms staging under \winpath{C:/Intel/.../} "
            r"consistent with WannaCry dropper layout. Additional strings hits require PID correlation via cmdline, dlllist, or process-specific dumps.",
        )
    )
    body.append(
        ab(
            "A8",
            "ATT\&CK S0366: observed vs intel-only; attribution limits",
            r"Separate memory-observed techniques from intelligence-only claims; single-image analysis cannot prove nation-state attribution.",
            f'"{VOL}" -f "{DUMP_W}" --profile {PROFILE} pslist / cmdline / psxview (technique evidence)',
            "Observed in memory: T1486 (encryptor processes), execution chain under explorer, T1490 helpers\n"
            "(taskse/taskdl exited near acquisition), SMB surface via 445 listener (environment).\n"
            "Intel-only: exact exploit chain byte sequence, BTC attribution, kill-switch registration details,\n"
            "campaign-wide lateral movement counts.",
            r"(1)~T1486 Observed (\texttt{@WanaDecryptor@}). (2)~T1490 Observed helpers (exited taskse/taskdl timing). "
            r"(3)~T1059 Observed (task/execution chain). (4)~T1047 Intel-primary unless WMI artifacts are explicitly carved. "
            r"Public governments attributed WannaCry to Lazarus/DPRK, but this memory image alone cannot substantiate nation-state attribution.",
        )
    )

    body.append(r"\section*{Part B: Stuxnet (\texttt{stuxnet.vmem})}")
    body.append(
        r"\textit{Prerequisite reading (dossier):} Executive Summary; Stuxnet Architecture "
        r"(Bypassing Behavior Blocking When Loading DLLs; Injection Technique); Installation; Load Point; "
        r"Windows Rootkit Functionality."
    )
    body.append(
        ab(
            "B1",
            "Identify the image and its time context",
            r"Same WinXPSP2x86 profile operates on the PAE-enabled Stuxnet image; compare AS layer and capture timestamps to wcry.",
            f'"{VOL}" -f "{DUMP_S}" imageinfo',
            s_img,
            r"Stuxnet: WinXPSP2x86 instantiated; AS Layer IA32PagedMemoryPae (PAE Yes) versus wcry No~PAE. "
            r"Image 2011-06-03 04:31:36~UTC; local 2011-06-03 00:31:36 $-$0400. Process \texttt{pslist} shows boot-era "
            r"timestamps (2010-10-29) on some processes versus infection-day 2011-06-03 on counterfeit lsass, "
            r"consistent with a snapshot/resumed VM rather than a fresh boot on infection day alone.",
        )
    )
    body.append(
        ab(
            "B2",
            "Identifying genuine vs counterfeit lsass.exe",
            r"Exactly one lsass (PID~680) matches Windows XP expectations: parent winlogon, full LSA modules, clean malfind, and socket ownership.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} pslist\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} pstree',
            "0x81e70020 lsass.exe  680  624  ... 2010-10-29 17:08:54 UTC\n"
            "0x81c498c8 lsass.exe  868  668  ... 2011-06-03 04:26:55 UTC\n"
            "0x81c47c00 lsass.exe 1928  668  ... 2011-06-03 04:26:55 UTC",
            r"Evidence bundle beyond slide~22: (1)~Parent PID~624 winlogon for 680 vs 668 services.exe for counterfeits. "
            r"(2)~dlllist counts 57~/~8~/~28 (B5). (3)~malfind: 0 regions on 680 vs injected MZ on 868/1928 (B7). "
            r"(4)~UDP 500/4500 sockets only on PID~680 (B4). XP norm: one legitimate lsass under winlogon.",
            figure="fig_B2_pslist.png",
            figcap="B2 screenshot: pslist showing three lsass.exe instances.",
        )
    )
    body.append(
        ab(
            "B3",
            "Infection-day process context",
            r"Distinguish Stuxnet artifacts from analysis tooling captured in the same memory image.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} pslist\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} cmdline',
            s_ps,
            r"Infection-day (2011-06-03): counterfeit lsass 868/1928, wmiprvse activity, short-lived cmd/ipconfig. "
            r"Procmon PID~660 indicates Process Monitor was running (lab capture with live monitoring); treat as "
            r"environmental artifact, not Stuxnet TTP.",
        )
    )
    body.append(
        ab(
            "B4",
            "Socket ownership corroboration",
            r"Network bindings on lsass differentiate the genuine instance; supportive evidence, not sole proof.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} sockets',
            s_sock,
            r"Only PID~680 owns UDP~500 and UDP~4500 (IPsec/IKE-related legitimate lsass behavior). "
            r"Counterfeit PIDs 868 and 1928 have no parallel socket rows. Corroborates B2; a socket-only heuristic would fail if malware hooked networking elsewhere.",
        )
    )
    body.append(
        ab(
            "B5",
            "DLL inventory counts and DFIR-07 critique",
            r"Count dlllist module rows (0x-prefixed bases), not \texttt{wc -l} on raw output (counts header lines).",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} dlllist -p 680\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} dlllist -p 868\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} dlllist -p 1928',
            "dlllist 0x-base row counts: PID 680 -> 57 ; PID 868 -> 8 ; PID 1928 -> 28.\n"
            "(Critique: dlllist | wc -l includes banners/separators; invalid for module counts.)",
            r"Counterfeits load far fewer modules because hollowed/injected images do not complete full LSA initialization "
            r"(dossier Injection Technique). Genuine 680 loads LSASRV, SAMSRV, msv1\_0, kerberos, and related packages (B6).",
        )
    )
    body.append(
        ab(
            "B6",
            "LSA security modules on genuine lsass only",
            r"LSA authentication stack DLLs should appear only in the real lsass process.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} dlllist -p 680',
            s_dll680,
            r"PID~680 maps LSASRV.dll, SAMSRV.dll, cryptdll.dll, and related security packages. "
            r"Counterfeit instances lack this full stack, consistent with process injection posing as lsass.exe.",
            figure="fig_B5_dlllist_680.png",
            figcap="B5/B6 screenshot: dlllist on genuine lsass PID 680.",
        )
    )
    body.append(
        ab(
            "B7",
            "malfind: injected regions and disassembly caveat",
            r"PAGE\_EXECUTE\_READWRITE private VADs with MZ headers indicate injection; disassembly of PE header bytes is not shellcode.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -p 680\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -p 868\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -p 1928',
            s_mf868 + "\n--- PID 1928 ---\n" + s_mf1928,
            r"PID~680: 0 malfind regions (control). PID~868: 2 regions (0x80000, 0x1000000). PID~1928: 5 regions. "
            r"Signals: PAGE\_EXECUTE\_READWRITE, no file backing, MZ \texttt{4d 5a}. "
            r"Volatility disassembly showing DEC EBP; POP EDX; NOP is PE header misinterpreted, not Stuxnet shellcode. "
            r"Control comparison on genuine lsass is required.",
            figure="fig_B7_malfind_868.png",
            figcap="B7 screenshot: malfind RWX/MZ region in counterfeit lsass PID 868.",
        )
    )
    body.append(
        ab(
            "B8",
            "Process dump naming and hash correlation",
            r"\texttt{malfind -D} dumps use \texttt{process.<EPROCESS>.<VAD start>.dmp}; six unique SHA-256 values across regions.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -D dumps/ -p 868\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -D dumps/ -p 1928\n'
            "sha256sum process.*.dmp",
            s_hash,
            r"Seven dump files, six unique hashes (0x80000 shared across both PIDs). "
            r"0x1000000 aligns with typical ImageBase / injection layout described in the dossier Injection Technique section.",
            figure="fig_B8_hashes.png",
            figcap="B8 screenshot: SHA-256 hashes of malfind -D region dumps.",
        )
    )
    body.append(
        ab(
            "B9",
            "VirusTotal hash lookup and OPSEC",
            r"Hash-not-upload preserves Meridian/lab OPSEC; VT labels vary (Stuxnet vs Duqu families).",
            "Browser: VirusTotal GUI hash search (no upload) on B8 SHA-256 values.",
            "2b2945f7cc7cf5b30ccdf37e2adbb236594208e409133bcd56f57f7c009ffe6d -> 61/71 worm.stuxnet\n"
            "10f07b9fbbc6a8c6dc4abf7a3d31a01e478accd115b33ec94fe885cb296a3586 -> 48/70 trojan.stuxnet / duqu",
            r"Divergent vendor labels reflect shared code artifacts between Stuxnet and Duqu clusters. "
            r"Reporting uses hash lookup only (no sample upload) for OPSEC.",
        )
    )
    body.append(
        ab(
            "B10",
            "ldrmodules, drivers, and registry timeline",
            r"Stuxnet load-order anomalies and kernel drivers precede counterfeit lsass creation.",
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} ldrmodules -p 1928\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} driverscan\n'
            f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} svcscan',
            s_ldr
            + "\n--- driverscan ---\nMRxCls / MRxNet present\n"
            + "Registry Services MRxCls/MRxNet LastWrite 2011-06-03 04:26:47 UTC",
            r"ldrmodules PID~1928: 0x80000 InLoad/InInit/InMem False (unlinked injection). "
            r"Impossible KERNEL32.DLL.ASLR-style name matches dossier section "
            r"``Bypassing Behavior Blocking When Loading DLLs.'' "
            r"Registry Services MRxCls/MRxNet last updated 2011-06-03 04:26:47~UTC, before counterfeit lsass at 04:26:55~UTC "
            r"(driver-first installation sequence; dossier Load Point / Windows Rootkit Functionality).",
            figure="fig_B10_ldrmodules.png",
            figcap="B10 screenshot: ldrmodules on counterfeit lsass PID 1928.",
        )
    )

    # Part C with quoted claims
    body.append(
        r"""
\section*{Part C: The Dossier on Trial}
\subsection*{C1. Claims against evidence}
At least six testable claims from four or more dossier sections. Verdicts use assignment vocabulary:
\textit{Confirmed in memory} / \textit{Consistent but not proven} / \textit{Not observable in RAM} / \textit{Contradicted}.

{\footnotesize
\begin{tabularx}{\textwidth}{@{}c >{\RaggedRight\arraybackslash}p{1.7in} >{\RaggedRight\arraybackslash}p{1.15in} c >{\RaggedRight\arraybackslash}Y@{}}
\toprule
\# & Dossier section / quoted claim & Memory verdict & Conf. & Basis \\
\midrule
1 & \textbf{Injection Technique:} ``The potential target processes for the injection are as follows: Lsass.exe\ldots'' & Confirmed in memory & High & malfind MZ/RWX on PIDs 868/1928; ldrmodules unlinked 0x80000 \\
2 & \textbf{Installation / Export 16:} ``injects itself into the services.exe process\ldots'' & Consistent but not proven & Med & PPID 668 services.exe + malfind MZ at 0x13f0000 in services.exe (C2) \\
3 & \textbf{Load Point:} ``Mrxcls.sys is a driver that allows Stuxnet to be executed every time an infected system boots\ldots'' & Confirmed in memory & High & driverscan/modules list mrxcls.sys; Services MRxCls key \\
4 & \textbf{Windows Rootkit Functionality / Table~4:} Resource 242 ``MRxnet.sys rootkit driver'' & Confirmed in memory & High & driverscan/modules list mrxnet.sys / MRxNet \\
5 & \textbf{Bypassing Behavior Blocking:} crafted names ``KERNEL32.DLL.ASLR.[HEXADECIMAL]'' & Confirmed in memory & High & ldrmodules shows ASLR-style impossible module strings \\
6 & \textbf{Executive Summary / WinCC:} copies/executes on systems running a WinCC database server; PLC rootkit claims & Not observable in RAM & N/A & No WinCC/PLC artifacts in this guest VMEM \\
7 & \textbf{Injection Technique:} suspended-process / template PE injection into trusted processes & Confirmed in memory & High & Multiple lsass ImageFileName with divergent dlllist/malfind (680 vs 868/1928) \\
\bottomrule
\end{tabularx}}

\noindent\textbf{Memory more precise than dossier:} exact PIDs 680/868/1928, dll counts 57/8/28, and second-resolution
driver LastWrite vs counterfeit create times. \textbf{Claim~6} is the required not-observable case (ICS/PLC/WinCC
scope needs disk, network, or PLC evidence outside this VMEM).

\subsection*{C2. Hypothesis: services.exe as injector}
\textbf{Hypothesis (stated before testing):} Counterfeit lsass processes (PPID~668 \texttt{services.exe}) imply
\texttt{services.exe} participated in injection or staging, matching Installation (``injects itself into the services.exe process'')
and Load Point (services.exe as injection target).

\textbf{Predictions if true:} (1)~\texttt{malfind -p 668} shows private RWX/MZ regions;
(2)~if false (parentage only), malfind on 668 is empty while counterfeit lsass still show injection.

\noindent\textbf{Exact command}
\begin{lstlisting}
"""
        + f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} malfind -p 668\n'
        + f'"{VOL}" -f "{DUMP_S}" --profile {PROFILE} pslist | findstr services'
        + r"""
\end{lstlisting}
\noindent\textbf{Observed / verdict:} malfind on services.exe reveals MZ header at 0x13f0000 (RWX private VAD).
Verdict: \textit{Consistent but not proven} that services.exe performed the hollowing (could be residual payload
or related tooling). Parentage alone remains circumstantial; positive malfind elevates services.exe as a
loader/orchestrator candidate. Drivers already registered (B10), so user-mode hollowing may occur without a
user-visible reboot in a resumed VM.

\subsection*{C3. Source critique}
The Symantec \textit{W32.Stuxnet Dossier} v1.3 (November 2010) predates this image's capture date (2011-06-03)
and is primary-sourced technical intelligence from static reverse engineering and field telemetry.
\textbf{Strengths:} precise injection narrative, driver names (MRxCls/MRxNet), trusted-process targets, WinCC/PLC context.
\textbf{Limits:} publication lag relative to later variants; vendor-centric attribution language; air-gapped PLC spread
cannot be confirmed or denied from one XP VMEM alone.
\textbf{Untestable from RAM alone (example):} PLC project modification / ``PLC rootkit'' claims require PLC/project
backups or engineering-station disk artifacts, not guest RAM alone.
Analyst treats the dossier as a hypothesis generator; Volatility outputs are falsifiable tests
(\texttt{malfind}, \texttt{ldrmodules}, \texttt{dlllist}). Conflicts require tiering: memory-observed $>$ correlated disk/network $>$ dossier-only.
"""
    )

    # Part D - expanded memo (~3 pages)
    body.append(
        r"""
\section*{Part D: From Evidence to Action}
\subsection*{D1. Findings memo to Meridian's CISO}
\begin{quote}
\small
\textbf{TO:} Meridian Energy CISO and SOC Lead\\
\textbf{FROM:} Unais Ali, Memory Forensics Analyst (IA~642)\\
\textbf{SUBJECT:} Dual-incident memory triage: WannaCry lab image and Stuxnet reference image\\
\textbf{DATE:} October 5, 2026
\end{quote}

\subsubsection*{Executive summary (non-technical)}
We analyzed two public reference memory images to prove Meridian can find malware in RAM when disk
artifacts are missing, encrypted, or hidden. The WannaCry image shows ransomware already encrypting a
Windows XP lab machine in May~2017, with encryption helpers finishing seconds before the memory capture.
Disk-only triage would have seen encrypted files but would likely have missed the short-lived helper processes
that only remain as exited remnants in RAM. The Stuxnet image shows advanced persistence: kernel drivers and
fake credential-service processes that look like normal Windows names. Disk tools that only list running
processes by name would under-detect this. \textbf{Recommendation:} Add memory acquisition to Meridian's IR
playbook for ransomware and suspected credential/kernel compromise on legacy Windows assets, with hash
verification and dual process listing (active list plus pool scan) as mandatory steps.

\subsubsection*{What each image showed}
\textbf{WannaCry (\texttt{wcry.vmem}).}
 Interactive detonation under the user desktop process, staging under
\texttt{C:\textbackslash Intel\textbackslash\ldots}, encryptor process \texttt{@WanaDecryptor@}, and exited recovery-inhibition helpers.
SMB port~445 was listening on the system process (MS17-010 exposure). Capture time: 2017-05-12 21:26:32~UTC.

\textbf{Stuxnet (\texttt{stuxnet.vmem}).}
 One genuine Local Security Authority process (PID~680) versus two counterfeits
(PIDs~868 and~1928) created on 2011-06-03 under \texttt{services.exe}, with injected executable regions and
kernel drivers MRxCls/MRxNet registered seconds earlier. Capture time: 2011-06-03 04:31:36~UTC.

\subsubsection*{What memory found that disk-only triage would miss}
\begin{itemize}
  \item Exited WannaCry helpers (\texttt{taskse}/\texttt{taskdl}) with ExitTime still recoverable via pool scanning.
  \item Counterfeit \texttt{lsass.exe} instances that reuse a trusted name but fail parent/DLL/injection checks.
  \item Unlinked injected PE images (ldrmodules False/False/False) and RWX private VADs (malfind).
  \item Kernel driver load order relative to user-mode counterfeit process creation.
\end{itemize}

\subsubsection*{Consolidated IOC table (defanged)}
{\small
\begin{tabularx}{\textwidth}{@{}P{0.75in} Y P{0.95in} P{0.7in}@{}}
\toprule
Type & Indicator (defanged) & Source plugin & Conf. \\
\midrule
Process & tasksche.exe under \texttt{C:/Intel/.../tasksche.exe} & cmdline & High \\
Process & @WanaDecryptor@.exe & pslist/pstree & High \\
Process & taskse.exe / taskdl.exe (exited) & psscan/psxview & High \\
Network & TCP 445 listener (System PID~4) & sockets & High \\
Network & 192.168[.]56[.]101 & sockets & High \\
URL & hxxp://www[.]iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea[.]com & strings/intel & Med \\
BTC & 12t9YDPgwueZ9NyMgw519p7AA8isjr6SMw & strings/intel & Med \\
Driver & mrxcls.sys / mrxnet.sys & driverscan & High \\
Hash & 2b2945f7\ldots ffe6d (malfind 0x80000) & malfind dump & High \\
Hash & 10f07b9f\ldots 3586 (VT Stuxnet/Duqu) & malfind + VT & Med \\
\bottomrule
\end{tabularx}}

\noindent\textbf{Investigated and assessed as benign (not dropped silently):}
{\small
\begin{tabularx}{\textwidth}{@{}P{1.35in} Y P{1.7in}@{}}
\toprule
Item & Why reviewed & Assessment \\
\midrule
Procmon (PID~660) & Unusual monitor on infection-day image & Lab tooling; not Stuxnet TTP \\
cmd / ipconfig (short-lived) & Appear on infection day & Ambiguous; not primary IOC \\
wuauclt / VMware tools & Present in trees & Expected guest/tools noise \\
Genuine lsass PID~680 & Name collision with counterfeits & Benign LSA (parent/dlllist/malfind) \\
\bottomrule
\end{tabularx}}

\subsubsection*{ATT\&CK table: Memory-observed vs Intel-sourced}
Technique IDs verified against attack.mitre.org software pages S0366 and S0603.

{\small
\begin{tabularx}{\textwidth}{@{}P{1.35in} P{0.55in} P{1.05in} Y@{}}
\toprule
Technique & ID & Evidence Source & Notes \\
\midrule
Data Encrypted for Impact & T1486 & Memory-observed & @WanaDecryptor@ / tasksche in wcry.vmem \\
Inhibit System Recovery & T1490 & Memory-observed & taskse/taskdl ExitTime (S0366) \\
Process Injection & T1055 & Memory-observed & malfind RWX MZ in fake lsass (S0603) \\
Rootkit & T1014 & Memory-observed & MRxCls/MRxNet loaded (S0603) \\
Exploitation for Client Execution & T1203 & Intel-sourced & MS17-010 not reconstructed from this RAM \\
Remote Services: SMB Admin Shares & T1021.002 & Intel-sourced & S0366 SMB worming; connscan empty here \\
\bottomrule
\end{tabularx}}

\subsubsection*{Three detection or prevention controls for Meridian}
\begin{enumerate}
\item \textbf{SMB isolation (signal: TCP/445 on System PID~4).}
 Detect/block at Meridian OT firewall and network ACL
between maintenance VLAN and plant HMIs. \textit{Limitation:} Host-only lab images prove exposure, not successful
lateral movement; empty connscan means this control must not wait for live C2 evidence.
\item \textbf{Dual process listing on IR (signal: pslist vs psscan ExitTime on taskse/taskdl).}
 Place in Meridian SOC
memory-triage playbook before rootkit escalation. \textit{Limitation:} Distinguishes exited helpers from DKOM hiding
only when ExitTime is checked; psxview False/True alone is insufficient.
\item \textbf{Module~02 WinPmem + Volatility~3 workflow.} Acquire with WinPmem, hash the raw dump, then run
\texttt{windows.info} $\rightarrow$ \texttt{windows.pslist} / \texttt{windows.psscan} $\rightarrow$ \texttt{windows.malfind} $\rightarrow$
\texttt{windows.dlllist} on candidate lsass PIDs and map hits to ATT\&CK. Place on Meridian IR workstation after isolation.
\textit{Limitation:} Symbol/profile coverage for XP-era images may force fallback to Volatility~2 profiles (as used here
with WinXPSP2x86).
\end{enumerate}

\subsubsection*{Business impact, legal, detection engineering, remediation}
For Meridian Energy, WannaCry-style ransomware in a host-only lab VLAN mirrors contractor laptops bridging
OT maintenance networks to corporate Wi-Fi. Encryption within minutes of execution (21:22 to 21:26~UTC) implies
backup and recovery playbooks must assume a blast radius under five minutes on unpatched SMB endpoints.
Stuxnet-style counterfeit lsass demonstrates credential subsystem compromise without obvious Process Explorer
anomalies; memory review is mandatory when EDR misses kernel-assisted injection.

Defanged IOCs in this report are suitable for external sharing; full paths under
\winpath{C:/Intel/...} remain internal. BTC addresses and onion endpoints are financial/extortion artifacts:
coordinate with law enforcement before blockchain tracing. Do not upload malfind dumps to public
multi-scanners from OT environments (B9 OPSEC).

Priority detection candidates: (1)~child process explorer $\rightarrow$ unsigned tasksche in a non-standard directory;
(2)~multiple lsass.exe with the same ImageFileName but divergent dlllist counts;
(3)~kernel driver load MRxCls+MRxNet paired with new lsass instances;
(4)~RWX VADs with MZ headers inside lsass (malfind signature).

\textbf{Remediation sequence:} Isolate $\rightarrow$ image memory $\rightarrow$ hash verify $\rightarrow$ Volatility profile $\rightarrow$
pslist/psscan delta $\rightarrow$ cmdline/dlllist on suspicious PIDs $\rightarrow$ malfind dump $\rightarrow$ hash-only VT $\rightarrow$
reimage from known-good baseline. For ICS, validate PLC project backups out-of-band; RAM artifacts do not
prove PLC payload delivery (C1 claim~6).

\textbf{Open questions:} (1)~Whether wcry.vmem captured before or after full disk encryption completion;
(2)~provenance of missing PPID~1608; (3)~whether Procmon in stuxnet.vmem alters timing of counterfeit lsass;
(4)~services.exe malfind region 0x13f0000 needs deeper PE carve for attribution to Stuxnet versus tooling.

\subsection*{D2. Knowledge check: True/False with corrections}
{\footnotesize
\begin{tabularx}{\textwidth}{@{}c l >{\RaggedRight\arraybackslash}Y@{}}
\toprule
\# & Verdict & Correction / rationale \\
\midrule
1 & Correct & pslist walks the linked EPROCESS list; psscan searches pool tags (different visibility). \\
2 & Incorrect & psxview False/True for taskse/taskdl is ExitTime exited helpers, not DKOM rootkit hiding. \\
3 & Incorrect & connscan/sockets are point-in-time; empty WannaCry PID rows do not prove no SMB spread. \\
4 & Incorrect & imageinfo +0530 is victim host TZ configuration, not attacker geolocation (India). \\
5 & Incorrect & PID~680 owning UDP 500/4500 is corroborative only; genuineness needs parent/dlllist/malfind. \\
6 & Incorrect & \texttt{dlllist | wc -l} counts banners/headers; scoped 0x-row counts are 57 (680) / 8 (868) / 28 (1928). \\
7 & Incorrect & DEC EBP; POP EDX; NOP is MZ/PE header mis-disassembly, not Stuxnet injection shellcode. \\
8 & Incorrect & malfind -D yields one file per VAD; six unique SHA-256s; VT 61/71 Stuxnet vs 48/70 Duqu. \\
9 & Correct (nuance) & WinXPSP2x86 is the validated Volatility~2 profile even when Image Type reports SP3. \\
10 & Correct & Create/Exit fields print UTC+0000; imageinfo separately shows host-local offset. \\
\bottomrule
\end{tabularx}}

\section*{Analytical Standards}
Evidence tiers: \textbf{Tier~1} direct Volatility plugin output; \textbf{Tier~2} multi-plugin agreement
(pslist/psscan/ExitTime); \textbf{Tier~3} dossier/ATT\&CK not independently observed in RAM.
Profile discipline: imageinfo $\rightarrow$ instantiate WinXPSP2x86 $\rightarrow$ validate with pslist.
WannaCry focus: exited versus hidden (ExitTime). Stuxnet focus: counterfeit lsass via parent, dlllist, malfind, sockets.
Hygiene: defanged IOCs, hash-only VT, UTC timelines, attribution limits.
"""
    )

    body.append(
        r"""
\section*{Evidence Appendix}
\subsection*{Evidence log (summary)}
Intake and final hashes match (see intake table). Full START/DONE command log with timestamps is retained under
\texttt{work/output/command\_log.txt}. SIFT confirmation outputs are under \texttt{work/output/sift/}.

"""
        + fig(
            "fig_SIFT_login.png",
            "SIFT Workstation login (sansforensics) after OVA import into VirtualBox.",
        )
        + fig(
            "fig_SIFT_wcry_pslist.png",
            "SIFT GUI terminal: vol.py pslist on wcry.vmem showing tasksche.exe (PID 1940) and @WanaDecryptor@ (PID 740).",
        )
        + fig(
            "fig_SIFT_stux_lsass.png",
            "SIFT vol.py pslist on stuxnet.vmem (lsass.exe rows) confirming the triple-lsass process set.",
        )
        + r"""
\noindent\textbf{Command log (excerpt)}
\begin{lstlisting}
"""
        + verb(clog)
        + r"""
\end{lstlisting}

\noindent\textbf{WannaCry psscan (exited helpers)}
\begin{lstlisting}
"""
        + verb(app_psscan)
        + r"""
\end{lstlisting}

\noindent\textbf{Stuxnet dlllist PID 868}
\begin{lstlisting}
"""
        + verb(app_dll868)
        + r"""
\end{lstlisting}

\noindent\textbf{Stuxnet malfind PID 1928}
\begin{lstlisting}
"""
        + verb(app_mf)
        + r"""
\end{lstlisting}

\noindent\textbf{Stuxnet modules (mrx*)}
\begin{lstlisting}
"""
        + verb(app_mod)
        + r"""
\end{lstlisting}

\section*{Method Map (six-step workflow, course slide 17)}
One-page map placing Part~A/~B findings under the six investigation stages.

{\footnotesize
\begin{tabularx}{\textwidth}{@{}c l >{\RaggedRight\arraybackslash}Y@{}}
\toprule
Step & Stage & Findings placed here \\
\midrule
1 & Acquire \& hash & Intake SHA-256 for wcry.vmem, stuxnet.vmem, zip, dossier; chain of custody \\
2 & Profile & A1/B1 imageinfo; WinXPSP2x86; PAE difference (wcry No / stuxnet Yes); KDBG/DTB \\
3 & Process review & A2 pstree lineage; A3/A4 psxview ExitTime; B2/B3 genuine vs counterfeit lsass; B5/B6 dlllist \\
4 & Network & A5 sockets/connscan (445 / empty WannaCry rows); B4 UDP 500/4500 on PID 680 only \\
5 & Deep dive & A7 cmdline paths; B7 malfind; B8 dumps/hashes; B9 VT hash-only; B10 ldrmodules/drivers \\
6 & Correlate \& report & A4/A8 and D1 ATT\&CK Memory-observed vs Intel-sourced; C1 to C3 dossier trial; D1 memo \\
\bottomrule
\end{tabularx}}

\section*{AI Disclosure}
Generative AI assisted with report drafting, LaTeX structuring, VirtualBox/SIFT bring-up, and Volatility
command-syntax sanity checks. All forensic values (hashes, PIDs, timestamps, malfind regions, dll counts,
socket bindings, and Volatility excerpts) originate from the analyst's own Volatility~2.6 runs
(\texttt{vol26.exe} on the host and \texttt{vol.py} inside SIFT) on local copies of \texttt{wcry.vmem} and
\texttt{stuxnet.vmem} captured October~5, 2026. AI did not replace hands-on plugin execution or hash verification.

\section*{References (APA 7)}
\begin{enumerate}[leftmargin=1.6em,itemsep=0.35em]
\item Ligh, M.~H., Case, A., Levy, J., \& Walters, M. (2014). \textit{The art of memory forensics: Detecting malware and threats in Windows, Linux, and Mac memory}. Wiley.
\item MITRE ATT\&CK. (n.d.). \textit{WannaCry} (Software S0366). \url{https://attack.mitre.org/software/S0366/}
\item MITRE ATT\&CK. (n.d.). \textit{Stuxnet} (Software S0603). \url{https://attack.mitre.org/software/S0603/}
\item Microsoft. (2017). Microsoft security bulletin MS17-010. \url{https://learn.microsoft.com/en-us/security-updates/SecurityBulletins/2017/ms17-010}
\item Symantec Security Response. (2011). \textit{W32.Stuxnet Dossier} (Version 1.3). Symantec Corp. (Sections cited: Executive Summary; Injection Technique; Installation; Load Point; Bypassing Behavior Blocking When Loading DLLs; Windows Rootkit Functionality.)
\item The Volatility Foundation. (n.d.). Volatility 2.6 documentation.
\item VirusTotal. (2026). Hash intelligence lookups performed 2026-10-05 (query-only, no sample upload).
\end{enumerate}

\end{document}
"""
    )

    return preamble + "\n".join(body)


def compile_pdf() -> int:
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure figures are next to the .tex for \includegraphics{figures/...}
    fig_src = SCRIPT_DIR / "figures"
    fig_dst = TEX_DIR / "figures"
    fig_dst.mkdir(parents=True, exist_ok=True)
    if fig_src.is_dir():
        for png in fig_src.glob("*.png"):
            shutil.copy2(png, fig_dst / png.name)

    TEX_PATH.write_text(build_tex(), encoding="utf-8")

    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        candidate = Path(r"C:\Users\unais\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")
        if candidate.is_file():
            pdflatex = str(candidate)
        else:
            print("pdflatex not found", file=sys.stderr)
            return 1

    for pass_no in (1, 2):
        proc = subprocess.run(
            [
                pdflatex,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(TEX_DIR),
                str(TEX_PATH.name),
            ],
            cwd=str(TEX_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            print(proc.stdout[-5000:] if proc.stdout else "", file=sys.stderr)
            print(proc.stderr[-2000:] if proc.stderr else "", file=sys.stderr)
            log = TEX_DIR / "midterm.log"
            if log.is_file():
                print(log.read_text(encoding="utf-8", errors="replace")[-4000:], file=sys.stderr)
            return proc.returncode
        print(f"pdflatex pass {pass_no} OK")

    built = TEX_DIR / "midterm.pdf"
    shutil.copy2(built, PDF_OUT)
    shutil.copy2(built, SUBMIT)
    pages = "?"
    try:
        import pypdf

        pages = str(len(pypdf.PdfReader(str(PDF_OUT)).pages))
    except Exception:
        pass
    print(f"Wrote: {PDF_OUT}")
    print(f"Size:  {PDF_OUT.stat().st_size:,} bytes")
    print(f"Pages: {pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(compile_pdf())
