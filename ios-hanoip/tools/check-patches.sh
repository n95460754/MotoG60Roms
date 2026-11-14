#!/bin/bash
# Apply blacktop + port patches to a clean xnu-8796.141.3 the way dxb/build.sh
# does, but FAIL on every patch that does not apply (dxb only warns).
# Usage: check-patches.sh <port-repo> <xnu-base> <dxb> <workdir>
set -uo pipefail
PORT=$1 BASE=$2 DXB=$3 WORK=$4
rm -rf "$WORK"; mkdir -p "$WORK/patches" "$WORK/fakesdk/usr/include" "$WORK/bin"
cp -a "$BASE" "$WORK/xnu"
cp "$DXB"/patches/*.patch "$WORK/patches/"
cp "$PORT"/xnu/patches/*.patch "$PORT"/xnu/patches/*.sh "$WORK/patches/"
# Linux stand-in for xcrun (only used to copy TargetConditionals.h)
printf '/* placeholder for patch-apply check */\n' > "$WORK/fakesdk/usr/include/TargetConditionals.h"
printf '#!/bin/sh\necho %s\n' "$WORK/fakesdk" > "$WORK/bin/xcrun"; chmod +x "$WORK/bin/xcrun"
export PATH="$WORK/bin:$PATH" MACHINE_CONFIG=SWEET MACOS_VERSION=13.5
cd "$WORK/xnu"
fail=0
for s in "$WORK"/patches/*.sh; do
  if out=$(bash "$s" 2>&1); then echo "OK   script $(basename "$s")"
  else echo "FAIL script $(basename "$s"): $out"; fail=1; fi
done
for p in "$WORK"/patches/*.patch; do
  name=$(basename "$p")
  if out=$(git apply --check "$p" 2>&1); then git apply "$p"; echo "OK   $name"
  elif [[ ! "$name" =~ ^[0-9]{4}- ]]; then
    # blacktop's own patches target other macOS releases; dxb skips them too
    echo "SKIP $name (blacktop patch for another xnu release)"
  else echo "FAIL $name: $(echo "$out" | head -3)"; fail=1; fi
done
echo "RESULT fail=$fail"
exit $fail
