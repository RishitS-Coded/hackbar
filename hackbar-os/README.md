# HackBar OS

A Debian-based live OS built around [HackBar](../README.md): boots straight into a
desktop with HackBar, the security tools it wraps, a first-boot setup wizard, and an installer.

- **Base:** Debian 13 (trixie), Xfce desktop
- **Builds:** `amd64` (PCs, USB sticks) and `arm64` (UTM on Apple Silicon, Raspberry Pi 5 later)
- **Login:** user `hacker`, password `live` (change with `sudo passwd hacker`)

## Build it on GitHub (no Linux needed)

1. Put this whole folder in your repo as `hackbar-os/`.
2. Create the workflow: repo -> **Add file -> Create new file**, name it
   `.github/workflows/build-iso.yml` (type the slashes; GitHub makes the folders),
   and paste in the contents of `build-iso.yml`.
3. Open the **Actions** tab -> **Build HackBar OS ISO** -> **Run workflow**.
4. Wait ~30-60 minutes. Each architecture shows up under **Releases** (right side of
   the repo page) as a pre-release. If it came in parts, join them:
   `cat hackbar-os-arm64.iso.part* > hackbar-os-arm64.iso`
5. Boot the ISO in UTM (Apple Silicon: use the arm64 one, "Virtualize", Linux, pick the ISO).

The workflow copies `hackbar.py` (and `install.sh`, `check_tools.sh`) from the top of the
repo into the image, so rebuilding always includes your latest HackBar.

## Where to change things

| You want to change | Edit this |
|---|---|
| Software on the ISO | `config/package-lists/hackbar.list.chroot` (core) or the `TOOLS=` list in `config/hooks/live/0200-hackbar-tools.hook.chroot` (security tools) |
| OS name and version | `config/hooks/live/0100-hackbar-branding.hook.chroot` |
| Wallpaper and logo | `config/includes.chroot/usr/share/backgrounds/hackbar/wallpaper.png` and `.../pixmaps/hackbar-logo.png` (same file names) |
| Installer package list and boot loader | `config/package-lists/installer.list.chroot` (delete the file for a live-only ISO) |
| First-boot wizard | `config/includes.chroot/usr/local/bin/hackbar-setup` |
| Boot menu text | `config/hooks/normal/0100-hackbar-bootmenu.hook.binary` |
| Base, desktop, ISO name, boot options | `auto/config` |

Anything in `config/includes.chroot/` is copied straight into the OS, so a file at
`config/includes.chroot/etc/foo` ends up at `/etc/foo`.

## Build on your own Linux machine instead

```
cd hackbar-os && sudo ./build-local.sh
```
Needs docker. Output is the `.iso` file in this folder.

## Known gaps in this first version

- **Untested:** it was written without being able to run a build, so expect to fix an error or two on the first run. Send the log from the Actions tab and it can be fixed.
- **Installer:** a Calamares installer is included ("Install HackBar OS" in the menu and on the wizard's last page). It installs on UEFI machines; old BIOS-only PCs aren't supported yet. Its branding is made by copying Debian's, so if the names look wrong in the installer, check `config/hooks/live/0150-hackbar-installer.hook.chroot`.
- **Metasploit and rockyou.txt** are not in Debian's repos, so they are not included.
- Tools Debian doesn't package for a given architecture are skipped. After booting, see `/usr/share/hackbar/tools-skipped.txt`.
- Placeholder wallpaper and logo, and a plain boot menu (no custom boot image yet).
