#!/bin/bash
# Back up the partitions that are unique to YOUR Moto G60 and pull the live
# device tree, before anything else in this port is tried.
#
#   1. Boot TWRP/OrangeFox (fastboot boot twrp.img is enough, nothing flashed)
#   2. On the PC:  tools/hanoip-backup.sh backup/
#
# Nothing on the phone is written. Keep backup/ OFF git and OFF the cloud:
# it contains your IMEI calibration (modemst*, fsg) and serial numbers.
set -euo pipefail

OUT="${1:-backup}"
command -v adb >/dev/null || { echo "adb not found (install Android platform-tools)"; exit 1; }

state="$(adb get-state 2>/dev/null || true)"
[ "$state" = recovery ] || { echo "Phone is not in recovery (adb state: '${state:-none}'). Boot TWRP first."; exit 1; }
[ "$(adb shell id -u | tr -d '\r')" = 0 ] || { echo "Recovery adb is not root."; exit 1; }

device="$(adb shell getprop ro.product.device | tr -d '\r')"
case "$device" in
  *hanoi*) echo "Device: $device" ;;
  *) echo "This is '$device', not hanoip (Moto G60). Stopping."; exit 1 ;;
esac

mkdir -p "$OUT/partitions" "$OUT/dtb"
chmod 700 "$OUT"

BYNAME=/dev/block/bootdevice/by-name
# Calibration / identity data that cannot be downloaded again, plus the boot chain.
WANT="persist modemst1 modemst2 fsg fsg_a fsg_b fsc utags utagsBackup hw cid frp \
      boot_a boot_b dtbo_a dtbo_b vbmeta_a vbmeta_b vbmeta_system_a vbmeta_system_b"

present="$(adb shell ls "$BYNAME" | tr -d '\r')"
failed=0
for p in $WANT; do
  if ! grep -qx "$p" <<<"$present"; then
    echo "  skip  $p (not on this phone)"
    continue
  fi
  dst="$OUT/partitions/$p.img"
  adb exec-out "dd if=$BYNAME/$p bs=1M 2>/dev/null" > "$dst"
  size_dev="$(adb shell blockdev --getsize64 "$BYNAME/$p" | tr -d '\r')"
  size_got="$(stat -c %s "$dst")"
  if [ "$size_dev" = "$size_got" ]; then
    echo "  ok    $p ($size_got bytes)"
  else
    echo "  FAIL  $p: phone $size_dev bytes, file $size_got bytes"
    failed=1
  fi
done

adb exec-out cat /sys/firmware/fdt > "$OUT/dtb/live-fdt.dtb"
echo "  ok    live device tree -> $OUT/dtb/live-fdt.dtb"

(cd "$OUT" && sha256sum partitions/*.img dtb/*.dtb > SHA256SUMS)

if [ "$failed" = 1 ]; then
  echo "Some partitions did not copy completely. Do NOT continue; run this again."
  exit 1
fi
echo
echo "Backup done. Copy $OUT/ to a USB stick or a second computer."
echo "Next: python3 tools/hanoip-check-fdt.py $OUT/dtb/live-fdt.dtb"
