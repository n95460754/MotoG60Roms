#!/usr/bin/env bash
# Packs every APK in <apk-dir> into a TWRP-flashable zip.
# Usage: ./build.sh <apk-dir> [output.zip]
# Needs: zip, and aapt (Android build-tools) on PATH or in $ANDROID_HOME.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APKDIR="${1:?usage: build.sh <apk-dir> [output.zip]}"
OUT="${2:-$HERE/out/TrackPack-MotoG60.zip}"

AAPT="$(command -v aapt || true)"
if [ -z "$AAPT" ] && [ -n "${ANDROID_HOME:-}" ]; then
  AAPT="$(ls -1 "$ANDROID_HOME"/build-tools/*/aapt 2>/dev/null | sort -V | tail -1)"
fi
[ -x "$AAPT" ] || { echo "aapt not found (install Android build-tools)"; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -r "$HERE/zip/." "$STAGE/"
mkdir -p "$STAGE/apks"

echo "# apk|package|minSdk|Name" > "$STAGE/apps.list"
shopt -s nullglob
count=0
for apk in "$APKDIR"/*.apk; do
  badge="$("$AAPT" dump badging "$apk")"
  pkg="$(sed -n "s/^package: name='\([^']*\)'.*/\1/p" <<<"$badge")"
  min="$(sed -n "s/^sdkVersion:'\([0-9]*\)'.*/\1/p" <<<"$badge")"
  name="$(basename "$apk" .apk | tr -cd 'A-Za-z0-9_-')"
  cp "$apk" "$STAGE/apks/$name.apk"
  echo "$name.apk|$pkg|$min|$name" >> "$STAGE/apps.list"
  echo "  + $name  ($pkg, minSdk $min)"
  count=$((count + 1))
done
[ "$count" -gt 0 ] || { echo "No APKs in $APKDIR"; exit 1; }

chmod 755 "$STAGE/META-INF/com/google/android/update-binary"
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
rm -f "$OUT"
(cd "$STAGE" && zip -qr9 -X "$OUT" META-INF apks system apps.list)
echo "Built: $OUT ($count apps)"
