#!/usr/bin/env bash
# check_tools.sh -- reports which HackBar tools are available on this
# machine. Run this after install.sh / install_macos.sh, or any time, to
# see what's missing. Auto-detects Linux vs macOS.
#
# Usage: bash check_tools.sh

BOLD="\033[1m"; GRN="\033[32m"; RED="\033[31m"; YEL="\033[33m"; RST="\033[0m"

if [[ "$(uname -s)" == "Darwin" ]]; then
    IS_MAC=1
    TOOLS=(
        nmap masscan arp-scan whois dig traceroute theHarvester searchsploit
        curl whatweb nikto gobuster sqlmap ffuf burpsuite
        airmon-ng airodump-ng aircrack-ng aireplay-ng
        hydra john hashcat hashid
        msfconsole nc
        strings file exiftool binwalk tshark shasum
        networksetup ifconfig netstat lsof scutil sw_vers whoami who
    )
    WORDLISTS=("$HOME/wordlists/common.txt" "$HOME/wordlists/rockyou.txt")
    INSTALL_HINT="bash install_macos.sh"
else
    IS_MAC=0
    TOOLS=(
        nmap masscan arp-scan whois dig traceroute theHarvester searchsploit
        curl whatweb nikto gobuster sqlmap ffuf burpsuite
        airmon-ng airodump-ng aircrack-ng aireplay-ng
        hydra john hashcat hashid
        msfconsole nc
        strings file exiftool binwalk tshark sha256sum
        nmcli ip ss whoami who
    )
    WORDLISTS=("/usr/share/wordlists/rockyou.txt" "/usr/share/wordlists/dirb/common.txt")
    INSTALL_HINT="sudo bash install.sh"
fi

echo -e "${BOLD}HackBar tool check${RST} ($( [[ $IS_MAC -eq 1 ]] && echo macOS || echo Linux ))\n"

missing=()
for t in "${TOOLS[@]}"; do
    if command -v "$t" >/dev/null 2>&1; then
        echo -e "  ${GRN}✓${RST} $t"
    else
        echo -e "  ${RED}✗${RST} $t"
        missing+=("$t")
    fi
done

echo -e "\n${BOLD}Wordlists${RST}"
missing_wl=()
for w in "${WORDLISTS[@]}"; do
    if [[ -f "$w" ]]; then
        echo -e "  ${GRN}✓${RST} $w"
    else
        echo -e "  ${RED}✗${RST} $w"
        missing_wl+=("$w")
    fi
done

if [[ $IS_MAC -eq 1 ]]; then
    echo -e "\n${YEL}Note:${RST} airmon-ng/airodump-ng/aireplay-ng need a Wi-Fi adapter that supports"
    echo "monitor mode. Apple's built-in Wi-Fi hardware generally does not."
fi

echo
if [[ ${#missing[@]} -eq 0 && ${#missing_wl[@]} -eq 0 ]]; then
    echo -e "${GRN}All tools and wordlists found.${RST}"
else
    [[ ${#missing[@]} -gt 0 ]] && echo "Missing tools: ${missing[*]}"
    [[ ${#missing_wl[@]} -gt 0 ]] && echo "Missing wordlists: ${missing_wl[*]}"
    echo "Run: $INSTALL_HINT"
fi
