#!/usr/bin/env bash
# check_tools.sh -- reports which HackBar tools are available on this
# machine. Run this after install.sh, or any time, to see what's missing.
#
# Usage: bash check_tools.sh

TOOLS=(
    nmap masscan arp-scan whois dig traceroute theHarvester searchsploit
    curl whatweb nikto gobuster sqlmap ffuf burpsuite
    airmon-ng airodump-ng aircrack-ng aireplay-ng
    hydra john hashcat hashid
    msfconsole nc
    strings file exiftool binwalk tshark sha256sum
    nmcli ip ss whoami who
)

BOLD="\033[1m"; GRN="\033[32m"; RED="\033[31m"; RST="\033[0m"
echo -e "${BOLD}HackBar tool check${RST}\n"

missing=()
for t in "${TOOLS[@]}"; do
    if command -v "$t" >/dev/null 2>&1; then
        echo -e "  ${GRN}✓${RST} $t"
    else
        echo -e "  ${RED}✗${RST} $t"
        missing+=("$t")
    fi
done

echo
if [[ ${#missing[@]} -eq 0 ]]; then
    echo -e "${GRN}All tools found.${RST}"
else
    echo "Missing: ${missing[*]}"
    echo "Run: sudo bash install.sh"
fi
