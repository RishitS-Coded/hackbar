#!/bin/bash
# Runs INSIDE a Debian container (GitHub Actions does this for you).
# Installs the build tools, then builds the ISO into this folder.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

ARCH="$(dpkg --print-architecture)"
PKGS="live-build debootstrap xorriso squashfs-tools mtools dosfstools cpio zstd gnupg ca-certificates curl git grub-common"
case "$ARCH" in
  amd64) PKGS="$PKGS grub-efi-amd64-bin grub-pc-bin syslinux syslinux-common isolinux" ;;
  arm64) PKGS="$PKGS grub-efi-arm64-bin" ;;
esac

apt-get update
apt-get install -y --no-install-recommends $PKGS

cd "$(dirname "$0")"
chmod +x auto/* config/hooks/*/* config/includes.chroot/usr/local/bin/* 2>/dev/null || true

lb clean --purge || true
lb config
lb build

echo
echo "=== Build finished ==="
ls -lh ./*.iso
