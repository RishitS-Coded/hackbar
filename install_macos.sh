#!/usr/bin/env bash
# install_macos.sh -- installs every tool HackBar's command library
# references, using Homebrew, plus the wordlists several commands expect.
#
# Usage:
#   bash install_macos.sh
#
# Do NOT run this with sudo -- Homebrew refuses to run as root.
set -uo pipefail

BOLD="\033[1m"; GRN="\033[32m"; RED="\033[31m"; YEL="\033[33m"; RST="\033[0m"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This installer is for macOS. On Linux/Kali, use: sudo bash install.sh"
    exit 1
fi

if [[ $EUID -eq 0 ]]; then
    echo "Don't run this with sudo -- Homebrew installs as your normal user."
    exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
    echo -e "${YEL}Homebrew isn't installed.${RST} Install it first:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

echo -e "${BOLD}Updating Homebrew...${RST}"
brew update

# Formulae available on Homebrew that cover HackBar's command library.
FORMULAE=(
    nmap            # scanning
    masscan         # fast port scanning
    arp-scan        # local network discovery
    whois           # domain lookups (dig/traceroute/ping/ifconfig/netstat/lsof/sw_vers/shasum are built into macOS)
    exploitdb       # searchsploit
    nikto           # web vulnerability scanning
    whatweb         # web tech fingerprinting
    gobuster        # directory/subdomain brute force
    sqlmap          # SQL injection testing
    ffuf            # web fuzzing
    theharvester    # OSINT
    aircrack-ng     # wireless suite (airmon-ng, airodump-ng, aireplay-ng)
    hydra           # login brute force
    john-jumbo      # password cracking (extended build with more formats)
    hashcat         # GPU password cracking
    binwalk         # embedded-file forensics
    exiftool        # file metadata
    wireshark       # tshark (CLI) -- GUI needs the cask below
    netcat          # nc, in case the BSD built-in behaves differently
)

CASKS=(
    wireshark       # the GUI app (the formula above only gives CLI tools)
    burp-suite      # Burp Suite Community
)

echo -e "\n${BOLD}== Homebrew formulae ==${RST}"
FAILED=()
for f in "${FORMULAE[@]}"; do
    echo -e "${BOLD}Installing ${f}...${RST}"
    if brew install "$f" >/tmp/hackbar_install_${f}.log 2>&1; then
        echo -e "  ${GRN}ok${RST}"
    else
        echo -e "  ${RED}failed${RST} (see /tmp/hackbar_install_${f}.log)"
        FAILED+=("$f")
    fi
done

echo -e "\n${BOLD}== Homebrew casks (GUI apps) ==${RST}"
for c in "${CASKS[@]}"; do
    echo -e "${BOLD}Installing --cask ${c}...${RST}"
    if brew install --cask "$c" >/tmp/hackbar_install_${c}.log 2>&1; then
        echo -e "  ${GRN}ok${RST}"
    else
        echo -e "  ${RED}failed${RST} (see /tmp/hackbar_install_${c}.log)"
        FAILED+=("$c (cask)")
    fi
done

# hashid isn't on Homebrew -- install via pipx if available, else pip3.
echo -e "\n${BOLD}== hashid (via pip) ==${RST}"
if command -v pipx >/dev/null 2>&1; then
    pipx install hashid >/tmp/hackbar_install_hashid.log 2>&1 \
        && echo -e "  ${GRN}ok${RST}" || { echo -e "  ${RED}failed${RST}"; FAILED+=("hashid"); }
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --user hashid >/tmp/hackbar_install_hashid.log 2>&1 \
        && echo -e "  ${GRN}ok${RST}" || { echo -e "  ${RED}failed${RST}"; FAILED+=("hashid"); }
else
    echo -e "  ${YEL}no pip/pipx found -- skipping hashid${RST}"
    FAILED+=("hashid")
fi

# Metasploit: official installer script (not on Homebrew).
echo -e "\n${BOLD}== Metasploit Framework ==${RST}"
if command -v msfconsole >/dev/null 2>&1; then
    echo -e "  ${GRN}already installed${RST}"
else
    echo "Metasploit isn't on Homebrew. Install it with Rapid7's official installer:"
    echo "  curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall"
    echo "  chmod 755 msfinstall && ./msfinstall"
    echo "See: https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html"
    FAILED+=("metasploit-framework (manual install required)")
fi

# Wordlists: Homebrew doesn't ship rockyou.txt or dirb's common.txt.
# HackBar's macOS commands look for these under ~/wordlists/.
echo -e "\n${BOLD}== Wordlists (~/wordlists/) ==${RST}"
mkdir -p "$HOME/wordlists"

if [[ ! -f "$HOME/wordlists/common.txt" ]]; then
    echo "Downloading dirb's common.txt wordlist..."
    if curl -fsSL -o "$HOME/wordlists/common.txt" \
        "https://raw.githubusercontent.com/v0re/dirb/master/wordlists/common.txt"; then
        echo -e "  ${GRN}ok${RST}"
    else
        echo -e "  ${RED}download failed${RST} -- get it manually from a dirb/SecLists mirror"
        FAILED+=("common.txt wordlist")
    fi
else
    echo -e "  ${GRN}already present${RST}"
fi

if [[ ! -f "$HOME/wordlists/rockyou.txt" ]]; then
    echo -e "${YEL}rockyou.txt isn't bundled here${RST} (it's a large, widely-mirrored leaked password list)."
    echo "Download it yourself and save it to: $HOME/wordlists/rockyou.txt"
    echo "  e.g. from the SecLists project: https://github.com/danielmiessler/SecLists/tree/master/Passwords/Leaked-Databases"
    FAILED+=("rockyou.txt wordlist (manual download)")
else
    echo -e "  ${GRN}already present${RST}"
fi

echo -e "\n${BOLD}== Summary ==${RST}"
if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo -e "${GRN}Everything installed successfully.${RST}"
else
    echo -e "${YEL}These need attention:${RST}"
    for f in "${FAILED[@]}"; do
        echo "  - $f"
    done
fi

echo -e "\n${BOLD}Note:${RST} Apple's built-in Wi-Fi hardware (especially on Apple Silicon) generally"
echo "does not support monitor mode, which the Wireless commands (airmon-ng, airodump-ng,"
echo "aireplay-ng) need. You'll want an external USB Wi-Fi adapter with a supported chipset,"
echo "or run those specific commands in a Linux VM instead."

echo -e "\n${BOLD}Done.${RST} Run HackBar with: python3 hackbar.py --user yourname"
