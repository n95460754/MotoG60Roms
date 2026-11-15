#!/usr/bin/env python3
"""Generate README.md for the Moto G60 ROM catalog from roms.json."""
import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
XDA = "https://xdaforums.com/t/{slug}.{thread}/"

STATUS = {"official": "🟢 Official", "unofficial": "🟡 Unofficial", "shared": "🔵 Shared", "closed": "⚫ Closed"}
TYPE = {"native": "Native", "gsi": "GSI", "port": "Port", "stock-mod": "Stock mod"}
GAPPS = {"included": "✅", "vanilla": "❌", "both": "✅ / ❌", None: "?"}
HOSTS = {
    "sourceforge.net": "SourceForge",
    "github.com": "GitHub",
    "git.pixelbuilds.org": "PixelBuilds",
    "www.pling.com": "Pling",
    "pixeldrain.com": "Pixeldrain",
    "mega.nz": "MEGA",
    "drive.google.com": "Google Drive",
    "onedrive.live.com": "OneDrive",
    "crdroid.net": "crDroid.net",
    "motorola-sm6150.github.io": "Website",
    "sozosha-dev.github.io": "Website",
}

# Picks shown at the top (thread id -> why).
PICKS = [
    (4704253, "Only **official** Android 15 build; the 120Hz Meteora kernels below are made for it."),
    (4807454, "Newest ROM in the forum (Android 16, Nov 2026). Unofficial, so expect some bugs."),
    (4791228, "Android 16 QPR2 GSI (flash via fastboot) with GApps, vanilla and microG builds."),
    (4693290, "Official Project Sakura (Android 14, LineageOS-based, GApps included)."),
]


def xda(item):
    return XDA.format(**item)


def downloads(rel):
    links = []
    for url in rel.get("download", []):
        host = urlparse(url).netloc
        label = HOSTS.get(host, "Mirror")
        links.append(f"[{label}]({url})")
    if links:
        return " · ".join(links)
    return f"_{rel['note']}_" if rel.get("note") else "_see thread_"


def date_key(r):
    return r.get("release", {}).get("date") or r["posted"]


def main():
    data = json.loads((HERE / "roms.json").read_text(encoding="utf-8"))
    roms = data["roms"]
    by_thread = {r["thread"]: r for r in roms}
    n_dl = sum(1 for r in roms if r["release"].get("download"))

    out = [
        "# 📱 Moto G60 — Custom ROMs & Releases",
        "",
        f"Every custom ROM for the **{data['device']}** (codename `{data['codename']}`) from",
        f"[XDA Forums]({data['source']}), with the **latest build, release date and download link** of each one.",
        "",
        "| | |",
        "|---|---|",
        f"| **SoC** | {data['soc']} |",
        f"| **ROMs** | {len(roms)} ({n_dl} with a direct download) |",
        f"| **Extras** | {len(data['recoveries'])} recoveries · {len(data['kernels'])} kernels · {len(data['guides'])} guides |",
        f"| **Last checked** | {data['releases_checked']} |",
        "",
        "> [!WARNING]",
        "> **Moto G60 (XT2135) only.** The Moto **G60s** (XT2133) is a different phone, so do not flash these on it.",
        "> Threads that say \"G40F\" are fine: the G40 Fusion has the same hardware and codename.",
        "",
        "> [!NOTE]",
        "> This repo is a **catalog of links**, not a mirror. ROM zips are 1–3 GB and are hosted by their developers.",
        "> Always read the XDA thread's install steps before you flash.",
        "",
        "## Contents",
        "",
        "- [Top picks](#-top-picks)",
        "- [Latest releases](#-latest-releases)",
        "- [All ROMs by Android version](#all-roms-by-android-version)",
        "- [Recoveries](#recoveries) · [Kernels](#kernels) · [Guides](#guides) · [Stock firmware](#stock-firmware)",
        "",
        "## ⭐ Top picks",
        "",
        "| ROM | Android | Latest build | Date | Download |",
        "|---|---|---|---|---|",
    ]
    for tid, why in PICKS:
        r = by_thread[tid]
        rel = r["release"]
        out.append(
            f"| [{r['name']}]({xda(r)}) | {r['android']} | {rel.get('version', '?')} | {rel.get('date', '?')} | {downloads(rel)} |"
        )
    out.append("")
    for tid, why in PICKS:
        out.append(f"- **{by_thread[tid]['name']}**: {why}")
    out += ["", "## 🆕 Latest releases", "", "The 10 newest builds with a working download link:", ""]
    out += ["| ROM | Android | Build | Date | Download |", "|---|---|---|---|---|"]
    latest = sorted((r for r in roms if r["release"].get("download")), key=date_key, reverse=True)[:10]
    for r in latest:
        rel = r["release"]
        out.append(
            f"| [{r['name']}]({xda(r)}) | {r['android']} | {rel.get('version', '?')} | {rel.get('date', '?')} | {downloads(rel)} |"
        )

    out += [
        "",
        "## All ROMs by Android version",
        "",
        "Legend: 🟢 Official · 🟡 Unofficial · 🔵 Shared (re-posted by a user) · ⚫ Closed thread · "
        "GApps ✅ included / ❌ vanilla",
        "",
    ]

    def ver_key(v):
        return (0, -int(v)) if v.isdigit() else (1, 0)

    for ver in sorted({r["android"] for r in roms}, key=ver_key):
        group = sorted((r for r in roms if r["android"] == ver), key=date_key, reverse=True)
        title = f"Android {ver}" if ver != "?" else "Android version not stated"
        out += [
            f"### {title} ({len(group)})",
            "",
            "| ROM | Type | Status | Latest build | Date | GApps | Download |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in group:
            rel = r["release"]
            out.append(
                f"| [{r['name']}]({xda(r)}) | {TYPE[r['type']]} | {STATUS[r['status']]} | "
                f"{rel.get('version', '?')} | {rel.get('date', r['posted'])} | {GAPPS[rel.get('gapps')]} | {downloads(rel)} |"
            )
        out.append("")

    for key, title in [
        ("recoveries", "Recoveries"),
        ("kernels", "Kernels"),
        ("guides", "Guides"),
        ("stock", "Stock firmware"),
    ]:
        out += [f"## {title}", ""]
        out += [f"- [{i['name']}]({xda(i)})" for i in data[key]]
        out.append("")

    out += [
        "## Updating this list",
        "",
        "1. Edit `roms.json` (each ROM has a `release` block with `version`, `date`, `download`, `gapps`).",
        "2. Run `python3 generate_readme.py`.",
        "",
    ]
    (HERE / "README.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote README.md: {len(roms)} ROMs, {n_dl} with downloads")


if __name__ == "__main__":
    main()
