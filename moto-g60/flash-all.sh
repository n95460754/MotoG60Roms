#!/usr/bin/env bash
# LineageOS 23.2 GSI -> Moto G60 / G40 Fusion (hanoip) — fastboot installer
# Phone must be in BOOTLOADER mode (Power + Vol Down), bootloader UNLOCKED.
set -u
cd "$(dirname "$0")"
FB="${FASTBOOT:-fastboot}"

command -v "$FB" >/dev/null || { echo "fastboot not found. Install Android platform-tools."; exit 1; }
[ -f system.img ] || { echo "system.img missing next to this script."; exit 1; }

echo "== Device =="
"$FB" devices
PRODUCT=$("$FB" getvar product 2>&1 | awk -F': *' '/^product:/{print $2}')
echo "product: ${PRODUCT:-unknown}"
if [ "${PRODUCT:-}" != "hanoip" ]; then
  echo "WARNING: this package is made for hanoip (Moto G60/G40 Fusion)."
  read -r -p "Continue anyway? [y/N] " a; [ "$a" = "y" ] || exit 1
fi

echo
echo "This will ERASE ALL DATA on the phone (factory reset)."
read -r -p "Type YES to continue: " ok
[ "$ok" = "YES" ] || { echo "Aborted."; exit 1; }

set -e
echo "== 1/4 Disable verified boot (bootloader) =="
"$FB" --disable-verity --disable-verification flash vbmeta vbmeta_disabled.img
"$FB" --disable-verity --disable-verification flash vbmeta_system vbmeta_disabled.img || true

echo "== 2/4 Reboot to fastbootd =="
"$FB" reboot fastboot
sleep 8

echo "== 3/4 Make room in super and flash GSI =="
set +e
for p in product system_ext; do
  "$FB" delete-logical-partition "$p"
done
"$FB" erase system
set -e
"$FB" flash system system.img

echo "== 4/4 Wipe data and reboot =="
"$FB" -w
"$FB" reboot
echo "Done. First boot can take 2-5 minutes."
