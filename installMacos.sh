#!/usr/bin/env bash
# install.sh -- installs every tool HackBar's command library references.
#
# Designed for Kali Linux (all packages are in Kali's default repos).
# Also runs on Debian/Ubuntu on a best-effort basis -- some tools aren't
# packaged there and will be listed as "not available" at the end, with a
# manual-install hint.
#
# Usage:
#   sudo bash install.sh
#
set -uo pipefail

BOLD="\033[1m"; GRN="\033[32m"; RED="\033[31m"; YEL="\033[33m"; RST="\033[0m"

if [[ $EUID -ne 0 ]]; then
    echo "Run this with sudo: sudo bash install.sh"
    exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This installer only supports apt-based systems (Kali, Debian, Ubuntu, Parrot)."
    echo "On another distro, install the tools listed in README.md manually."
    exit 1
fi

IS_KALI=0
if grep -qi '^ID=kali' /etc/os-release 2>/dev/null; then
    IS_KALI=1
fi

echo -e "${BOLD}Updating package lists...${RST}"
apt-get update -y

# Packages available on Kali (and usually Debian/Ubuntu too).
CORE_PKGS=(
    nmap            # scanning
    whois           # domain lookups
    dnsutils        # dig
    traceroute      # traceroute
    net-tools       # legacy ip/arp tools some scripts expect
    iproute2        # ip, ss
    network-manager # nmcli
    curl            # headers, web requests
    netcat-traditional  # nc
    binwalk         # embedded-file forensics
    libimage-exiftool-perl  # exiftool
    coreutils       # sha256sum etc (almost always present already)
    file            # file type identification
    hydra           # login brute force
    john            # password cracking
    hashcat         # GPU password cracking
    hashid          # hash type identification
    aircrack-ng     # full wireless suite (airmon-ng, airodump-ng, aireplay-ng)
    nikto           # web vuln scanning
    whatweb         # web tech fingerprinting
    sqlmap          # SQL injection testing
    gobuster        # directory/subdomain brute force
    ffuf            # web fuzzing
    theharvester    # OSINT
    arp-scan        # local network discovery
    wireshark       # tshark + GUI
    masscan         # fast port scanning
    exploitdb       # provides searchsploit
)

# Kali-only or Kali-first packages; may not exist on plain Debian/Ubuntu.
KALI_PKGS=(
    metasploit-framework
    burpsuite
)

install_list() {
    local -n pkgs=$1
    local failed=()
    for pkg in "${pkgs[@]}"; do
        echo -e "${BOLD}Installing ${pkg}...${RST}"
        if apt-get install -y "$pkg" >/tmp/hackbar_install_${pkg}.log 2>&1; then
            echo -e "  ${GRN}ok${RST}"
        else
            echo -e "  ${RED}failed${RST} (see /tmp/hackbar_install_${pkg}.log)"
            failed+=("$pkg")
        fi
    done
    printf '%s\n' "${failed[@]}"
}

echo -e "\n${BOLD}== Core tools ==${RST}"
FAILED_CORE=$(install_list CORE_PKGS)

echo -e "\n${BOLD}== Kali-specific tools ==${RST}"
FAILED_KALI=()
if [[ $IS_KALI -eq 1 ]]; then
    for pkg in "${KALI_PKGS[@]}"; do
        echo -e "${BOLD}Installing ${pkg}...${RST}"
        if apt-get install -y "$pkg" >/tmp/hackbar_install_${pkg}.log 2>&1; then
            echo -e "  ${GRN}ok${RST}"
        else
            echo -e "  ${RED}failed${RST} (see /tmp/hackbar_install_${pkg}.log)"
            FAILED_KALI+=("$pkg")
        fi
    done
else
    echo -e "${YEL}Not on Kali -- skipping metasploit-framework and burpsuite.${RST}"
    echo "On Debian/Ubuntu, install these manually:"
    echo "  Metasploit: https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html"
    echo "  Burp Suite Community: https://portswigger.net/burp/communitydownload"
    FAILED_KALI=("metasploit-framework" "burpsuite")
fi

# rockyou.txt wordlist -- shipped compressed on Kali, needs unzipping once.
echo -e "\n${BOLD}== Wordlists ==${RST}"
if [[ -f /usr/share/wordlists/rockyou.txt.gz ]] && [[ ! -f /usr/share/wordlists/rockyou.txt ]]; then
    echo "Unzipping rockyou.txt wordlist..."
    gunzip -k /usr/share/wordlists/rockyou.txt.gz
    echo -e "  ${GRN}ok${RST}"
elif [[ -f /usr/share/wordlists/rockyou.txt ]]; then
    echo -e "  ${GRN}already present${RST}"
else
    echo -e "  ${YEL}not found -- install the 'wordlists' package or download rockyou.txt manually${RST}"
    apt-get install -y wordlists >/tmp/hackbar_install_wordlists.log 2>&1 && echo -e "  ${GRN}installed wordlists package${RST}"
fi

if [[ ! -d /usr/share/wordlists/dirb ]]; then
    echo "Installing dirb (for its common.txt wordlist used by gobuster/ffuf)..."
    apt-get install -y dirb >/tmp/hackbar_install_dirb.log 2>&1 && echo -e "  ${GRN}ok${RST}" \
        || echo -e "  ${RED}failed${RST} (see /tmp/hackbar_install_dirb.log)"
fi

echo -e "\n${BOLD}== Summary ==${RST}"
ALL_FAILED=()
[[ -n "${FAILED_CORE:-}" ]] && while IFS= read -r line; do [[ -n "$line" ]] && ALL_FAILED+=("$line"); done <<< "$FAILED_CORE"
ALL_FAILED+=("${FAILED_KALI[@]}")

if [[ ${#ALL_FAILED[@]} -eq 0 ]]; then
    echo -e "${GRN}Everything installed successfully.${RST}"
else
    echo -e "${YEL}These didn't install automatically:${RST}"
    for f in "${ALL_FAILED[@]}"; do
        echo "  - $f"
    done
    echo "Check the logs in /tmp/hackbar_install_*.log, or install them manually."
fi

echo -e "\n${BOLD}Done.${RST} Run HackBar with: python3 hackbar.py --user yourname"
