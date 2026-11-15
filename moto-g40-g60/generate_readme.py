#!/usr/bin/env python3
"""Generate README.md for the Moto G40/G60 ROM catalog from roms.json."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
XDA = "https://xdaforums.com/t/{slug}.{thread}/"

STATUS_BADGE = {
    "official": "🟢 Official",
    "unofficial": "🟡 Unofficial",
    "shared": "🔵 Shared",
    "closed": "⚫ Closed",
}
TYPE_LABEL = {"native": "Native", "gsi": "GSI", "port": "Port", "stock-mod": "Stock mod"}


def link(item):
    return f"[{item['name']}]({XDA.format(**item)})"


def main():
    data = json.loads((HERE / "roms.json").read_text(encoding="utf-8"))
    roms = data["roms"]
    out = [
        f"# Custom ROMs — {data['device']} (`{data['codename']}`)",
        "",
        f"SoC: **{data['soc']}**  ",
        f"Source: [XDA Forums — Moto G40 / G60]({data['source']})  ",
        f"Collected: {data['collected']} · **{len(roms)} ROMs**, "
        f"{len(data['recoveries'])} recoveries, {len(data['kernels'])} kernels",
        "",
        "> ⚠️ This is a **catalog of links**, not a mirror. ROM zips are 1–3 GB each, exceed",
        "> GitHub's 100 MB file limit, and are distributed by their developers. Always download",
        "> from the original XDA thread and read the install instructions there.",
        "",
        "> ⚠️ Moto **G60s** (XT2133) is a *different* device — these ROMs are only for **hanoip**",
        "> (G40 Fusion XT2147 / G60 XT2135).",
        "",
        "Legend: 🟢 Official · 🟡 Unofficial · 🔵 Shared (re-posted by a user) · ⚫ Closed thread",
        "",
    ]

    def sort_key(v):
        return (0, -int(v)) if v.isdigit() else (1, 0)

    for ver in sorted({r["android"] for r in roms}, key=sort_key):
        group = [r for r in roms if r["android"] == ver]
        title = f"Android {ver}" if ver != "?" else "Android version not stated"
        out += [f"## {title} ({len(group)})", "", "| ROM | Type | Status | Posted |", "|---|---|---|---|"]
        for r in group:
            out.append(
                f"| {link(r)} | {TYPE_LABEL[r['type']]} | {STATUS_BADGE[r['status']]} | {r['posted']} |"
            )
        out.append("")

    for key, title in [
        ("recoveries", "Custom recoveries"),
        ("kernels", "Custom kernels"),
        ("guides", "Guides & lists"),
        ("stock", "Stock firmware (to go back)"),
    ]:
        out += [f"## {title}", ""]
        out += [f"- {link(i)}" for i in data[key]]
        out.append("")

    out += [
        "## Updating",
        "",
        "Edit `roms.json`, then run `python3 generate_readme.py`.",
        "",
    ]
    (HERE / "README.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote README.md with {len(roms)} ROMs")


if __name__ == "__main__":
    main()
