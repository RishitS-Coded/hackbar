#!/bin/bash
# Build HackBar OS on your own Linux machine or Linux VM (Debian/Ubuntu).
# Usage:  cd hackbar-os && sudo ./build-local.sh
# Copies hackbar.py from the folder above (the repo root) into the image first.
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo."; exit 1; fi

mkdir -p config/includes.chroot/opt/hackbar
for f in hackbar.py install.sh check_tools.sh LICENSE README.md; do
  if [ -f "../$f" ]; then cp "../$f" config/includes.chroot/opt/hackbar/; fi
done
[ -f config/includes.chroot/opt/hackbar/hackbar.py ] || { echo "hackbar.py not found next to this folder."; exit 1; }

# Ubuntu's own live-build is an old fork, so build inside a Debian container.
command -v docker >/dev/null || { echo "Install docker first (sudo apt install docker.io)."; exit 1; }
docker run --rm --privileged -v "$PWD:/build" debian:trixie bash /build/ci-build.sh
