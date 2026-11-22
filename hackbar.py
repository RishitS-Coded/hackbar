#!/usr/bin/env python3
"""HackBar: a search bar that teaches you out of needing it.

Type what you want in plain English. The bar shows the real command (and what
each part means). Press Enter to let it run, or type the command yourself to
earn stars. At 5 stars you sit a no-hints exam; pass it and the search bar is
gone for that user. Surprise spot checks can bring it back.

LEGAL: Every command here is a standard, publicly documented security tool
(nmap, hydra, hashcat, aircrack-ng, sqlmap, metasploit, etc.) exactly as you'd
find it in that tool's own manual. HackBar adds nothing offensive of its own.
Running any of them against a system you do not own or do not have explicit
written authorization to test is illegal in most countries. HackBar asks you
to confirm authorization before running anything against a non-local target,
but that prompt is a reminder, not a safeguard -- you are responsible for
how you use these tools.

    python3 hackbar.py --user alice
    python3 hackbar.py --user alice --dry-run     # print commands, run nothing
"""
import argparse
import json
import random
import re
import shlex
import shutil
import subprocess
from pathlib import Path

DIM, BOLD, GRN, RED, YEL, RST = "\033[2m", "\033[1m", "\033[32m", "\033[31m", "\033[33m", "\033[0m"
MAX_M = 3.0
GRAD = 4.95
FADE = 0.15
SPOT = 0.12
CONFIRM_PHRASE = "i am authorized"


def C(id, area, cmd, task, tags, parts, auth=False):
    return dict(id=id, area=area, cmd=cmd, task=task, tags=set(tags.split()),
                parts=parts, auth=auth)


# ---------------------------------------------------------------------------
# Command library. auth=True => confirmation required for any non-local
# target. Every command is the tool's real, documented syntax.
# ---------------------------------------------------------------------------
LIB = [
    # ---------------- Network basics ----------------
    C("saved-nets", "Network", "nmcli connection show", "Show every network I've ever connected to",
      "saved networks connected connection wifi history known profiles",
      [("nmcli", "NetworkManager's command-line tool"), ("connection", "work with saved connections"), ("show", "list them")]),
    C("wifi-near", "Network", "nmcli device wifi list", "List Wi-Fi networks around me",
      "nearby wifi networks around available visible scan",
      [("nmcli", "NetworkManager's command-line tool"), ("device wifi", "the Wi-Fi hardware"), ("list", "show what it can see")]),
    C("my-ip", "Network", "ip addr", "Show my IP address",
      "ip address addresses interface card mine",
      [("ip", "the modern network tool"), ("addr", "show addresses")]),
    C("routes", "Network", "ip route", "Show where my traffic is routed",
      "route routes gateway router default path",
      [("ip", "the modern network tool"), ("route", "show the routing table")]),
    C("open-ports", "Network", "ss -tuln", "Show ports my computer is listening on",
      "ports listening open services sockets",
      [("ss", "socket statistics"), ("-t", "TCP"), ("-u", "UDP"), ("-l", "listening only"), ("-n", "numbers, not names")]),
    C("dns", "Network", "cat /etc/resolv.conf", "Show my DNS servers",
      "dns servers nameserver resolver",
      [("cat", "print a file"), ("/etc/resolv.conf", "where DNS servers are listed")]),
    C("ping", "Network", "ping -c 4 {target}", "Ping a machine four times",
      "ping reachable alive up test connection latency",
      [("ping", "send test packets"), ("-c 4", "stop after 4"), ("{target}", "machine to check")]),
    C("dns-lookup", "Network", "dig {target}", "Look up a domain's DNS records",
      "dig dns lookup domain records resolve",
      [("dig", "DNS lookup tool"), ("{target}", "domain to look up")]),
    C("traceroute", "Network", "traceroute {target}", "Show the path packets take to a host",
      "traceroute path hops route trace",
      [("traceroute", "trace the network path"), ("{target}", "destination")]),
    C("arp-scan", "Network", "arp-scan --localnet", "Find devices on my local network by ARP",
      "arp local network devices discover lan",
      [("arp-scan", "sends ARP requests"), ("--localnet", "scan the attached subnet")], auth=True),

    # ---------------- System basics ----------------
    C("whoami", "System", "whoami", "Show which user I am",
      "who user account name current me",
      [("whoami", "prints your username")]),
    C("pwd", "System", "pwd", "Show which folder I'm in",
      "folder directory where current path location",
      [("pwd", "print working directory")]),
    C("ls", "System", "ls -la", "List all files here with details",
      "list files folder contents hidden details",
      [("ls", "list files"), ("-l", "long format"), ("-a", "include hidden files")]),
    C("uname", "System", "uname -a", "Show my kernel and system info",
      "kernel system info version machine architecture",
      [("uname", "system information"), ("-a", "all of it")]),
    C("df", "System", "df -h", "Show free disk space",
      "disk space storage free full drive",
      [("df", "disk free"), ("-h", "human-readable sizes")]),
    C("ps", "System", "ps aux", "Show every running process",
      "processes running programs tasks all",
      [("ps", "process status"), ("aux", "all users, with details")]),
    C("os", "System", "cat /etc/os-release", "Show which operating system this is",
      "os operating system distro release linux version name",
      [("cat", "print a file"), ("/etc/os-release", "OS identity file")]),
    C("who", "System", "who", "Show who is logged in",
      "logged users sessions login who",
      [("who", "lists current login sessions")]),
    C("sudoers", "System", "sudo -l", "Show what I'm allowed to run as root",
      "sudo privileges permissions allowed root",
      [("sudo", "superuser do"), ("-l", "list my allowed commands")]),
    C("history", "System", "history", "Show my recent command history",
      "history past commands recent typed",
      [("history", "shows previously run commands")]),

    # ---------------- Scanning / recon ----------------
    C("sweep", "Scanning", "nmap -sn {target}", "Find which devices are alive on a network",
      "discover hosts devices alive network find sweep ping",
      [("nmap", "network scanner"), ("-sn", "ping scan, no port scan"), ("{target}", "network/host you own")], auth=True),
    C("nmap-quick", "Scanning", "nmap {target}", "Scan a machine's most common ports",
      "scan ports machine common target quick",
      [("nmap", "network scanner"), ("{target}", "machine you own")], auth=True),
    C("nmap-all-ports", "Scanning", "nmap -p- {target}", "Scan every port on a machine",
      "all ports full every scan complete",
      [("nmap", "network scanner"), ("-p-", "all 65535 ports"), ("{target}", "machine you own")], auth=True),
    C("nmap-version", "Scanning", "nmap -sV {target}", "Detect which service versions are running",
      "service versions detect software running fingerprint",
      [("nmap", "network scanner"), ("-sV", "probe service versions"), ("{target}", "machine you own")], auth=True),
    C("nmap-os", "Scanning", "nmap -O {target}", "Guess a machine's operating system",
      "os guess fingerprint operating system detect",
      [("nmap", "network scanner"), ("-O", "OS detection"), ("{target}", "machine you own")], auth=True),
    C("nmap-scripts", "Scanning", "nmap -sC -sV {target}", "Run nmap's default vulnerability/info scripts",
      "scripts default vuln info nse scan",
      [("nmap", "network scanner"), ("-sC", "default script set"), ("-sV", "version detection"), ("{target}", "machine you own")], auth=True),
    C("nmap-udp", "Scanning", "nmap -sU {target}", "Scan UDP ports instead of TCP",
      "udp ports scan",
      [("nmap", "network scanner"), ("-sU", "UDP scan"), ("{target}", "machine you own")], auth=True),
    C("masscan", "Scanning", "masscan -p1-65535 {target} --rate 1000", "Very fast full port scan",
      "fast scan masscan rate all ports",
      [("masscan", "very fast port scanner"), ("-p1-65535", "every port"), ("{target}", "machine you own"), ("--rate 1000", "packets per second")], auth=True),
    C("searchsploit", "Scanning", "searchsploit {target}", "Search known exploits for a piece of software",
      "exploit database search known vulnerability software version",
      [("searchsploit", "searches the Exploit-DB archive"), ("{target}", "software name/version")]),
    C("theharvester", "Scanning", "theHarvester -d {target} -b all", "Gather public info about a domain (OSINT)",
      "osint domain emails subdomains gather recon public",
      [("theHarvester", "OSINT gathering tool"), ("-d", "target domain"), ("-b all", "search all sources")], auth=True),
    C("whois", "Scanning", "whois {target}", "Look up who registered a domain",
      "whois registrar domain owner lookup",
      [("whois", "domain registration lookup"), ("{target}", "domain")]),

    # ---------------- Web application testing ----------------
    C("headers", "Web", "curl -I {target}", "Fetch a website's HTTP headers",
      "website headers http web server fetch",
      [("curl", "transfer data from a URL"), ("-I", "headers only"), ("{target}", "the site")]),
    C("whatweb", "Web", "whatweb {target}", "Identify the technology a website runs on",
      "technology stack identify cms framework website",
      [("whatweb", "web technology fingerprinter"), ("{target}", "site you own/are authorized to test")], auth=True),
    C("nikto", "Web", "nikto -h {target}", "Scan a website for common vulnerabilities",
      "web vulnerability scan common misconfig nikto",
      [("nikto", "web vulnerability scanner"), ("-h", "host to scan"), ("{target}", "site you're authorized to test")], auth=True),
    C("gobuster-dir", "Web", "gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt",
      "Discover hidden directories on a website",
      "hidden directories folders discover brute website",
      [("gobuster dir", "directory brute-forcer"), ("-u", "target URL"), ("{target}", "site you own"),
       ("-w ...", "wordlist of folder names to try")], auth=True),
    C("gobuster-dns", "Web", "gobuster dns -d {target} -w /usr/share/wordlists/dirb/common.txt",
      "Discover subdomains of a domain",
      "subdomains discover brute dns",
      [("gobuster dns", "subdomain brute-forcer"), ("-d", "target domain"), ("-w ...", "wordlist")], auth=True),
    C("sqlmap", "Web", "sqlmap -u {target} --batch", "Test a URL for SQL injection",
      "sql injection sqli test database vulnerability",
      [("sqlmap", "automated SQL injection tool"), ("-u", "target URL with a parameter"),
       ("{target}", "site you own"), ("--batch", "use default answers, no prompts")], auth=True),
    C("burp-note", "Web", "burpsuite", "Open Burp Suite to intercept and test web traffic",
      "burp proxy intercept requests web testing",
      [("burpsuite", "launches the Burp Suite GUI")], auth=True),
    C("ffuf", "Web", "ffuf -u {target}/FUZZ -w /usr/share/wordlists/dirb/common.txt",
      "Fuzz a URL for hidden paths quickly",
      "fuzz fuzzing paths hidden fast",
      [("ffuf", "fast web fuzzer"), ("-u .../FUZZ", "URL with a fuzzing position"), ("-w ...", "wordlist")], auth=True),

    # ---------------- Wireless ----------------
    C("wifi-monitor", "Wireless", "sudo airmon-ng start wlan0", "Put a Wi-Fi card into monitor mode",
      "monitor mode wifi card wireless airmon",
      [("airmon-ng", "manages monitor mode"), ("start wlan0", "the Wi-Fi interface to switch")], auth=True),
    C("wifi-scan", "Wireless", "sudo airodump-ng wlan0mon", "List nearby Wi-Fi networks and connected devices",
      "wifi scan networks nearby devices airodump",
      [("airodump-ng", "captures nearby wireless traffic"), ("wlan0mon", "the monitor-mode interface")], auth=True),
    C("wifi-capture", "Wireless", "sudo airodump-ng -w capture --bssid {target} wlan0mon",
      "Capture traffic from one Wi-Fi network for analysis",
      "capture handshake traffic record wifi network",
      [("airodump-ng", "captures traffic"), ("-w capture", "save to a file"),
       ("--bssid", "limit to one network's address"), ("{target}", "BSSID of a network you own")], auth=True),
    C("wifi-crack", "Wireless", "aircrack-ng capture.cap -w /usr/share/wordlists/rockyou.txt",
      "Test a captured Wi-Fi handshake against a wordlist",
      "crack password handshake wordlist wifi key",
      [("aircrack-ng", "tests a captured handshake against passwords"),
       ("capture.cap", "the file you captured"), ("-w ...", "password list to try")], auth=True),
    C("wifi-deauth", "Wireless", "sudo aireplay-ng --deauth 10 -a {target} wlan0mon",
      "Send deauthentication frames to force a reconnect handshake",
      "deauth disconnect reconnect handshake force",
      [("aireplay-ng", "sends crafted wireless frames"), ("--deauth 10", "send 10 deauth frames"),
       ("-a", "access point address"), ("{target}", "network you own")], auth=True),

    # ---------------- Password auditing ----------------
    C("hydra-ssh", "Password", "hydra -l {user} -P /usr/share/wordlists/rockyou.txt ssh://{target}",
      "Test SSH login against a password list",
      "password brute force ssh login crack test",
      [("hydra", "login brute-forcer"), ("-l user", "username to try"),
       ("-P ...", "password list"), ("ssh://{target}", "the host you own")], auth=True),
    C("hydra-web", "Password", "hydra -l {user} -P /usr/share/wordlists/rockyou.txt {target} http-post-form",
      "Test a website login form against a password list",
      "password brute force web login form crack",
      [("hydra", "login brute-forcer"), ("http-post-form", "target a web login form"), ("{target}", "site you own")], auth=True),
    C("john", "Password", "john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt",
      "Crack password hashes with a wordlist",
      "crack hash password john wordlist",
      [("john", "password hash cracker"), ("--wordlist", "list of passwords to try"), ("hashes.txt", "hashes you're authorized to test")], auth=True),
    C("hashcat", "Password", "hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt",
      "Crack password hashes using the GPU",
      "hashcat gpu crack hash fast password",
      [("hashcat", "GPU-accelerated hash cracker"), ("-m 0", "hash type, here MD5"),
       ("-a 0", "straight wordlist attack"), ("hashes.txt", "your hash file")], auth=True),
    C("hash-identify", "Password", "hashid {target}", "Identify what type of hash a string is",
      "identify hash type what kind",
      [("hashid", "guesses a hash's algorithm"), ("{target}", "the hash string")]),

    # ---------------- Exploitation framework ----------------
    C("msf-start", "Exploitation", "msfconsole", "Open the Metasploit console",
      "metasploit exploit framework console open start",
      [("msfconsole", "launches Metasploit's interactive shell")], auth=True),
    C("msf-search", "Exploitation", "msfconsole -q -x \"search {target}\"", "Search Metasploit for a usable exploit module",
      "metasploit module msfconsole framework",
      [("msfconsole -q -x", "run one command then stay open"), ("search", "search for modules"), ("{target}", "software/CVE to search")]),
    C("netcat-listen", "Exploitation", "nc -lvnp 4444", "Start a listener to catch an incoming connection",
      "listener netcat reverse shell catch connection",
      [("nc", "netcat"), ("-l", "listen"), ("-v", "verbose"), ("-n", "no DNS lookups"), ("-p 4444", "port to listen on")], auth=True),
    C("netcat-connect", "Exploitation", "nc {target} 4444", "Connect out to a listening port",
      "connect netcat port test",
      [("nc", "netcat"), ("{target}", "host you own"), ("4444", "port")], auth=True),

    # ---------------- Forensics / analysis ----------------
    C("strings", "Forensics", "strings {target}", "Pull readable text out of a binary file",
      "strings text binary file readable extract",
      [("strings", "extracts printable text"), ("{target}", "file to inspect")]),
    C("file-type", "Forensics", "file {target}", "Identify what type of file something really is",
      "file type identify what kind format",
      [("file", "identifies file types"), ("{target}", "file to check")]),
    C("exiftool", "Forensics", "exiftool {target}", "Read hidden metadata out of a file",
      "metadata exif hidden info photo file",
      [("exiftool", "reads file metadata"), ("{target}", "file, e.g. a photo")]),
    C("binwalk", "Forensics", "binwalk {target}", "Look for hidden files packed inside a file",
      "hidden files embedded extract firmware binwalk",
      [("binwalk", "finds embedded files/data"), ("{target}", "file to inspect")]),
    C("tshark", "Forensics", "tshark -i any", "Capture live network traffic from the terminal",
      "capture traffic packets live network wireshark",
      [("tshark", "Wireshark's command-line version"), ("-i any", "capture on all interfaces")], auth=True),
    C("hashsum", "Forensics", "sha256sum {target}", "Get a file's fingerprint to verify it hasn't changed",
      "checksum hash verify integrity fingerprint file",
      [("sha256sum", "computes a SHA-256 hash"), ("{target}", "file to check")]),
]

# ---------------------------------------------------------------------------
# Sentence bank: several real ways someone might ask for each command. This
# is what makes the search bar forgiving -- you don't have to hit one exact
# phrasing, just say it close to how you'd actually talk.
# ---------------------------------------------------------------------------
EXAMPLES = {
    "saved-nets": ["show me every network i ever connected to", "what wifi have i joined before",
                   "list my saved wifi networks", "networks i've connected to in the past"],
    "wifi-near": ["what wifi networks are around me", "show nearby wifi", "scan for wifi networks",
                  "what networks can i see right now"],
    "my-ip": ["what's my ip address", "show my ip", "what is my local ip"],
    "routes": ["where does my traffic go", "show my default gateway", "what's my routing table"],
    "open-ports": ["what ports are open on my machine", "show my listening ports",
                   "what services are running on my computer"],
    "dns": ["what dns server am i using", "show my dns settings"],
    "ping": ["check if a machine is online", "is this host reachable", "ping this ip", "test if a server is up"],
    "dns-lookup": ["look up this domain's dns records", "what does this domain resolve to"],
    "traceroute": ["show the path to this server", "trace the route to this host", "how many hops to this ip"],
    "arp-scan": ["find devices on my local network", "what's connected to my lan"],
    "whoami": ["who am i logged in as", "what user am i", "show my username"],
    "pwd": ["what folder am i in", "show my current directory", "where am i right now"],
    "ls": ["list everything in this folder", "show all files here including hidden ones"],
    "uname": ["what kernel version am i running", "show my system info"],
    "df": ["how much disk space do i have left", "show free storage"],
    "ps": ["show everything that's running", "list all processes on this machine"],
    "os": ["what linux distro is this", "show my os version"],
    "who": ["who else is logged into this machine", "show active sessions"],
    "sudoers": ["what am i allowed to run as root", "check my sudo permissions"],
    "history": ["show my past commands", "what have i typed recently"],
    "sweep": ["find every device alive on this network", "discover hosts on my network",
              "which devices are online on this subnet"],
    "nmap-quick": ["scan this machine for open ports", "what ports does this server have open",
                   "run a basic port scan"],
    "nmap-all-ports": ["scan every single port on this host", "do a full port scan"],
    "nmap-version": ["figure out what software versions are running on this server",
                      "detect service versions on this host"],
    "nmap-os": ["guess what os this server is running", "fingerprint the operating system"],
    "nmap-scripts": ["run a deeper scan with nmap's default scripts", "check for common issues with nmap"],
    "nmap-udp": ["scan the udp ports on this host"],
    "masscan": ["do a really fast full port scan", "scan all ports quickly"],
    "searchsploit": ["find known exploits for this software", "is there a public exploit for this version",
                     "find exploits for this software version", "search the exploit database"],
    "theharvester": ["gather public info on this domain", "do osint on this company's domain",
                      "find emails and subdomains for this domain"],
    "whois": ["who owns this domain", "look up domain registration info"],
    "headers": ["show this website's http headers", "what headers does this server send"],
    "whatweb": ["what technology does this website run on", "identify the cms this site uses"],
    "nikto": ["scan this website for vulnerabilities", "check this site for common web issues"],
    "gobuster-dir": ["find hidden folders on this website", "discover directories on this site",
                      "brute force the folder structure of this site"],
    "gobuster-dns": ["find subdomains of this domain", "discover other subdomains"],
    "sqlmap": ["test this url for sql injection", "check if this page is vulnerable to sqli"],
    "burp-note": ["open burp suite", "intercept this website's traffic"],
    "ffuf": ["fuzz this url for hidden paths", "quickly brute force paths on this site"],
    "wifi-monitor": ["put my wifi card into monitor mode", "enable monitor mode on my adapter"],
    "wifi-scan": ["show nearby wifi networks and connected devices", "scan wireless networks in monitor mode"],
    "wifi-capture": ["capture traffic from this wifi network", "record packets from this network for analysis"],
    "wifi-crack": ["crack this wifi handshake", "test this captured handshake against a password list"],
    "wifi-deauth": ["force devices to reconnect to this network", "send deauth frames to capture a handshake"],
    "hydra-ssh": ["brute force this ssh login", "test ssh password against a wordlist"],
    "hydra-web": ["brute force this website's login form", "test this login page against a password list"],
    "john": ["crack these password hashes", "run john the ripper on this hash file"],
    "hashcat": ["crack these hashes with my gpu", "run hashcat on this hash file",
                "crack this hash using my graphics card"],
    "hash-identify": ["what type of hash is this", "identify this hash format"],
    "msf-start": ["open metasploit", "start the metasploit console"],
    "msf-search": ["search metasploit for an exploit", "find a metasploit module for this"],
    "netcat-listen": ["start a listener for an incoming connection", "open a port and wait for a connection"],
    "netcat-connect": ["connect to this open port", "test connecting to this service with netcat"],
    "strings": ["pull readable text out of this binary", "find text strings in this file"],
    "file-type": ["what kind of file is this really", "identify this file's real type"],
    "exiftool": ["show hidden metadata in this photo", "check this file's exif data"],
    "binwalk": ["check if there's anything hidden inside this file", "look for embedded files in this firmware"],
    "tshark": ["capture live network traffic", "watch packets going across my network right now"],
    "hashsum": ["get this file's checksum", "verify this file hasn't been tampered with"],
}
for _e in LIB:
    _e["examples"] = EXAMPLES.get(_e["id"], [])

STOP = {"i", "me", "my", "the", "a", "an", "to", "of", "is", "are", "what", "can", "you", "please", "ever", "every"}


def stem(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def norm(s):
    return " ".join(s.split())


def placeholders(cmd):
    return re.findall(r"\{(\w+)\}", cmd)


def match(text):
    """Return (entry, {field: value}) if text is exactly a library command."""
    t = norm(text)
    for e in LIB:
        fields = placeholders(e["cmd"])
        pattern = re.escape(e["cmd"])
        for f in fields:
            pattern = pattern.replace(re.escape("{" + f + "}"), r"(\S+)")
        m = re.fullmatch(pattern, t)
        if m:
            return e, dict(zip(fields, m.groups()))
    return None, {}


def words_of(text):
    return {stem(w) for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in STOP}


def search(query):
    """Fuzzy-match free text against tags, the task description, and the
    sentence bank of example phrasings. The sentence bank carries the most
    weight since it's real phrasings, not single keywords."""
    q = words_of(query)
    if not q:
        return None
    best, top = None, 0.0
    for e in LIB:
        tags = {stem(t) for t in e["tags"]}
        task = words_of(e["task"])
        # best overlap against any one example sentence, as a fraction of
        # that sentence's own words -- rewards queries that closely match a
        # known phrasing, not just ones that share a rare keyword.
        ex_best = 0.0
        for ex in e.get("examples", []):
            ew = words_of(ex)
            if not ew:
                continue
            overlap = len(q & ew) / len(ew)
            ex_best = max(ex_best, overlap)
        score = 6 * ex_best + sum(2 if w in tags else 1 if w in task else 0 for w in q)
        if score > top:
            best, top = e, score
    return best if top > 0 else None


def find_target(text):
    m = re.search(r"\b(?:\d{1,3}(?:\.\d{1,3}){3}|localhost|[a-z0-9-]+(?:\.[a-z0-9-]+)+)\b", text.lower())
    return m.group(0) if m else None


def is_local(t):
    return t in ("localhost", "::1") or (t or "").startswith("127.")


# ---------- profiles & stars ----------
class Store:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {"users": {}}

    def user(self, name):
        return self.data["users"].setdefault(
            name, dict(mastery={}, graduated=False, assisted=0, typed=0, passed=0, failed=0))

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))


def stars(u):
    total = sum(min(MAX_M, u["mastery"].get(e["id"], 0)) for e in LIB)
    return 5 * total / (MAX_M * len(LIB))


def bump(u, id, delta):
    u["mastery"][id] = max(0.0, min(MAX_M, u["mastery"].get(id, 0) + delta))


def stars_line(u):
    s = stars(u)
    return f"{'★' * int(s)}{'☆' * (5 - int(s))} {s:.2f}/5"


# ---------- running ----------
def fill_fields(e, fields):
    """Ask for any missing placeholders ({target}, {user}, ...)."""
    out = dict(fields)
    for f in placeholders(e["cmd"]):
        if not out.get(f):
            out[f] = input(f"{f}? > ").strip()
    return out


def authorised(e, fields):
    target = fields.get("target")
    if not e["auth"] or (target and is_local(target)):
        return True
    print(f"{YEL}Authorization check:{RST} you're about to run a tool that can affect another system.")
    if target:
        print(f"  Target: {target}")
    print(f"  This is only legal against systems you own or have written permission to test.")
    ans = input(f"  Type '{CONFIRM_PHRASE}' to continue > ").strip().lower()
    return ans == CONFIRM_PHRASE


def run(e, fields, dry):
    fields = fill_fields(e, fields)
    if any(not v or v.startswith("-") for v in fields.values()):
        print("Missing or invalid input, skipping.")
        return
    if not authorised(e, fields):
        print("Skipped. Only test systems you're allowed to test.")
        return
    cmd = e["cmd"]
    for f, v in fields.items():
        cmd = cmd.replace("{" + f + "}", v)
    tool = shlex.split(cmd.replace("sudo ", ""))[0]
    if shutil.which(tool) is None and not dry:
        print(f"{RED}'{tool}' isn't installed on this system.{RST} (On macOS, many of these are Kali/Linux-only tools.)")
        return
    if dry:
        print(f"{DIM}[dry-run] would run: {cmd}{RST}")
        return
    try:
        subprocess.run(shlex.split(cmd), timeout=300)
    except FileNotFoundError:
        print(f"{RED}'{tool}' isn't installed here.{RST}")
    except subprocess.TimeoutExpired:
        print(f"{RED}Timed out.{RST}")
    except KeyboardInterrupt:
        print(f"{YEL}Stopped.{RST}")


# ---------- tests ----------
def ask(u, e, label):
    hint = " (use localhost)" if "target" in placeholders(e["cmd"]) else ""
    print(f"\n{BOLD}{label}{RST} {e['task']}{hint}")
    m, _ = match(input("no hints > "))
    ok = bool(m and m["id"] == e["id"])
    if ok:
        bump(u, e["id"], 0.5)
        u["passed"] += 1
        print(f"{GRN}Correct.{RST}")
    else:
        bump(u, e["id"], -1)
        u["failed"] += 1
        print(f"{RED}Not quite.{RST} It was: {e['cmd']}")
    return ok


def aftermath(u, rng):
    pool = [e for e in LIB if u["mastery"].get(e["id"], 0) >= 1]
    if pool and rng.random() < SPOT:
        ask(u, rng.choice(pool), "Surprise check:")
    if u["graduated"] and stars(u) < GRAD:
        u["graduated"] = False
        print(f"{YEL}Your rating slipped below 5 stars. The search bar is back.{RST}")
    if not u["graduated"] and stars(u) >= GRAD:
        print(f"\n{BOLD}You're at {stars(u):.2f} stars. Graduation exam: 3 tasks, no hints, all must pass.{RST}")
        results = [ask(u, e, f"Task {i}:") for i, e in enumerate(rng.sample(LIB, 3), 1)]
        if all(results):
            u["graduated"] = True
            print(f"\n{GRN}{BOLD}Graduated. The search bar is gone for good... unless a surprise check catches you.{RST}")
        else:
            print(f"\n{YEL}Not this time. Keep practising and you'll get another shot.{RST}")


# ---------- the two modes ----------
def assisted(u, line, dry, rng):
    e, fields = match(line)
    if e:
        bump(u, e["id"], 1.0)
        u["typed"] += 1
        print(f"{GRN}Typed it yourself: +1 mastery.{RST}")
        run(e, fields, dry)
        return aftermath(u, rng)
    e = search(line)
    if not e:
        print("No match in the library yet.")
        return
    t = find_target(line) if "target" in placeholders(e["cmd"]) else None
    shown = e["cmd"]
    for f in placeholders(e["cmd"]):
        shown = shown.replace("{" + f + "}", t if f == "target" and t else f"<{f}>")
    print(f"\n  {DIM}{shown}{RST}")
    for tok, meaning in e["parts"]:
        print(f"    {tok:<16} {meaning}")
    ans = input("\nEnter = run it for me | or type the command yourself > ").strip()
    if ans == "":
        bump(u, e["id"], -FADE)
        u["assisted"] += 1
        run(e, {"target": t} if t else {}, dry)
    else:
        m, fields2 = match(ans)
        if m:
            bump(u, m["id"], 0.5)
            u["typed"] += 1
            print(f"{GRN}Typed it with help: +0.5 mastery (cold typing earns +1).{RST}")
            run(m, fields2, dry)
        else:
            print("That didn't match a known command. Try again, or just press Enter.")
            return
    aftermath(u, rng)


def direct(u, line, dry, rng):
    e, fields = match(line)
    if e:
        run(e, fields, dry)
        return aftermath(u, rng)
    print(f"{DIM}(graduated users get a normal shell in the full OS; this prototype only runs library commands){RST}")


BANNER = f"""{BOLD}HackBar{RST}
Every tool here is a real, publicly documented security tool. Only use them
on systems you own or have explicit written permission to test. Unauthorized
use against systems you don't control is illegal in most countries.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="me")
    ap.add_argument("--data", default="~/.hackbar/profiles.json")
    ap.add_argument("--dry-run", action="store_true", help="print commands instead of running them")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    store = Store(a.data)
    u = store.user(a.user)
    print(BANNER)
    print(f"user: {a.user} | {stars_line(u)} | :stars  :help  :quit\n")
    while True:
        prompt = "$ " if u["graduated"] else "search or type a command > "
        try:
            line = input(prompt).strip()
        except EOFError:
            break
        if not line:
            continue
        if line in (":q", ":quit"):
            break
        if line == ":stars":
            print(f"{stars_line(u)} | typed {u['typed']} | assisted {u['assisted']} | "
                  f"checks passed {u['passed']} / failed {u['failed']}")
        elif line == ":help":
            print("Describe what you want, e.g. 'show every network I ever connected to'.")
        elif u["graduated"]:
            direct(u, line, a.dry_run, rng)
        else:
            assisted(u, line, a.dry_run, rng)
        store.save()
    store.save()


if __name__ == "__main__":
    main()
