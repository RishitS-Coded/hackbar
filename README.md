# HackBar

A search bar that teaches you the ethical-hacking command line by making you
need it less over time.

Type what you want in plain English — "show me every network I've ever
connected to" — and HackBar shows you the real command, explains each part,
and lets you run it. The more you type commands yourself instead of pressing
Enter, the more stars you earn. At 5 stars you sit a no-hints exam. Pass it
and the search bar disappears — you've graduated to a normal terminal.
Random spot checks keep you honest after that.

## ⚠️ Legal notice — read this

Every command in HackBar's library is a standard, publicly documented
security tool: `nmap`, `hydra`, `hashcat`, `aircrack-ng`, `sqlmap`,
`metasploit`, and others. HackBar does not add any offensive capability of
its own — it's a teaching layer on top of tools that already exist in every
penetration-testing distribution.

**Running these tools against a system you do not own, or do not have
explicit written authorization to test, is illegal in most countries**, even
if your intent is harmless curiosity. HackBar asks you to confirm
authorization before running anything against a non-local target. That
prompt is a reminder, not a legal safeguard — you, the user, are entirely
responsible for how and against what you use these tools.

Good places to practice legally: your own lab machines/VMs, `localhost`,
and intentionally vulnerable targets built for this purpose, such as
[DVWA](https://github.com/digininja/DVWA), [OWASP Juice
Shop](https://owasp.org/www-project-juice-shop/), and platforms like
[HackTheBox](https://www.hackthebox.com/) and
[TryHackMe](https://tryhackme.com/).

## What it does

- **Search → explain → run.** Describe a goal, see the real command with
  each flag explained, press Enter or type it yourself.
- **Stars per user.** Typing a command from memory earns the most mastery;
  letting the bar run it for you slowly erodes it.
- **Graduation exam.** At ~5 stars, pass a 3-task no-hints test and the
  search bar is retired — you get a plain shell.
- **Spot checks.** Occasional surprise questions, even after graduating, to
  catch rust before it sets in.
- **59 commands across 8 areas:** Network, System, Scanning, Web, Wireless,
  Password auditing, Exploitation, Forensics.
- **Authorization gate.** Any command capable of touching another system
  asks you to confirm authorization first (skipped for `localhost`/`127.0.0.1`).

## Requirements

- Python 3.7+ (standard library only — no pip installs needed for the app
  itself)
- The underlying security tools, if you want commands to actually run. Use
  `install.sh` to get them all at once (see below). **Kali Linux** ships
  almost everything already; on Debian/Ubuntu, a few tools (Metasploit,
  Burp Suite) aren't in the default repos and the script will tell you so.
  On macOS, these tools generally aren't available at all — use
  `--dry-run` there, or run HackBar inside a Kali VM.

## Installing the tools

```bash
sudo bash install.sh
```

This installs every tool HackBar's library references: `nmap`, `masscan`,
`arp-scan`, `whois`, `dig`, `traceroute`, `nikto`, `whatweb`, `gobuster`,
`sqlmap`, `ffuf`, `theHarvester`, `searchsploit` (via `exploitdb`),
`aircrack-ng` (the whole suite — `airmon-ng`, `airodump-ng`, `aireplay-ng`),
`hydra`, `john`, `hashcat`, `hashid`, `wireshark`/`tshark`, `binwalk`,
`exiftool`, `netcat`, and (on Kali) `metasploit-framework` and `burpsuite`.
It also unpacks the `rockyou.txt` password wordlist and installs `dirb`'s
wordlist for directory brute-forcing.

The script keeps going if one package fails rather than stopping the whole
run, and prints a summary at the end of anything it couldn't install, with
a log file and manual-install hint for each. **It needs internet access**
and is meant to run on the target machine (your Kali VM), not in a sandbox.

To check what's already installed at any time, without installing
anything:

```bash
bash check_tools.sh
```

## Usage

```bash
python3 hackbar.py --user yourname          # live: runs real commands
python3 hackbar.py --user yourname --dry-run # safe: prints commands only
```

Commands inside the session:
- `:stars` — show your current rating and stats
- `:help` — a reminder of how to use the search bar
- `:quit` — exit (progress is saved automatically)

Progress is stored per user at `~/.hackbar/profiles.json`. Delete it to
reset.

## Roadmap

- A disguised desktop shell (Mac-style interface, with HackBar as the
  system search bar) packaged as a bootable Kali-based live ISO
- Per-area graduation instead of one global rating
- A built-in local lab (DVWA/Juice Shop) for safe practice targets

## Contributing

Pull requests adding well-explained, real command entries are welcome.
Please do not submit anything that isn't a standard, publicly documented
tool, and keep the authorization gate intact on anything that can touch a
remote system.

## License

MIT — see `LICENSE`.

### macOS

HackBar runs natively on macOS — not just `--dry-run`. It automatically
swaps Linux-only commands for their real macOS equivalents (`ip addr` →
`ifconfig`, `nmcli` → `networksetup`/`system_profiler`, `ss -tuln` →
`lsof -i`, `sha256sum` → `shasum -a 256`, and so on), so the search bar
shows you the command that actually works on your machine.

\`\`\`bash
bash install_macos.sh
\`\`\`

Uses [Homebrew](https://brew.sh) (installed separately if you don't have
it) to install the same tool set as above, wherever Homebrew packages them,
plus the `common.txt` and `rockyou.txt` wordlists under `~/wordlists/`.
**Do not run this with `sudo`** — Homebrew refuses to run as root.

Two things Homebrew can't fully cover, which the script tells you about:
- **Metasploit** isn't on Homebrew — the script gives you Rapid7's official
  installer command.
- **Wi-Fi monitor mode** (needed by `airmon-ng`/`airodump-ng`/`aireplay-ng`)
  generally isn't supported by Apple's built-in Wi-Fi hardware, especially
  on Apple Silicon. You'll need an external USB adapter with a
  monitor-mode-capable chipset, or run those specific commands in a Linux
  VM instead.
  

