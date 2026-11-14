#!/usr/bin/env python3
"""Check a Moto G60 (hanoip) live device tree against the values this port uses.

  tools/hanoip-check-fdt.py dtb/live-fdt.dtb

Get the live tree from TWRP/OrangeFox with tools/hanoip-backup.sh, which copies
/sys/firmware/fdt. Every check prints PASS, WARN or FAIL and the script exits 1
if any FAIL is found, so do not run `fastboot boot` until this is clean.
It also prints the upper DDR bank to put into tools/mkadt.py (HIGH_PHYS_BASE /
HIGH_MEM_SIZE) because that differs between the 4 GB and 6 GB models.
"""
import struct
import sys

FDT_MAGIC = 0xd00dfeed
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9

# Values the port is built with (tools/mkadt.py, shim/console.h, patch 0082)
EXPECT = {
    'fb_base': 0x9c000000,
    'fb_min_size': 1080 * 4 * 2460,
    'gicd': 0x17a00000,
    'gicr': 0x17a60000,
    'ufs': 0x01d84000,
    'timer_hz': 19200000,
    'touch_spi': 0x00a80000,   # QUP SE6, Ilitek ILI7807S (TDDI)
    'panel_h': 2460,
}


class Node:
    def __init__(self, name, parent=None):
        self.name, self.parent, self.props, self.children = name, parent, {}, []

    def path(self):
        parts, n = [], self
        while n is not None and n.parent is not None:
            parts.append(n.name)
            n = n.parent
        return '/' + '/'.join(reversed(parts))

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def cells(self, key, default):
        v = self.props.get(key)
        return struct.unpack('>I', v[:4])[0] if v and len(v) >= 4 else default


def parse(blob):
    magic, total, off_struct, off_strings = struct.unpack('>IIII', blob[:16])
    if magic != FDT_MAGIC:
        raise SystemExit(f'not a flattened device tree (magic {magic:#x})')
    if total > len(blob):
        raise SystemExit(f'truncated FDT: header says {total} bytes, file has {len(blob)}')

    def string(off):
        end = blob.index(b'\0', off_strings + off)
        return blob[off_strings + off:end].decode()

    pos, root, cur = off_struct, None, None
    while True:
        (tok,) = struct.unpack('>I', blob[pos:pos + 4])
        pos += 4
        if tok == BEGIN_NODE:
            end = blob.index(b'\0', pos)
            name = blob[pos:end].decode()
            pos = (end + 4) & ~3
            n = Node(name, cur)
            if cur is None:
                root = n
            else:
                cur.children.append(n)
            cur = n
        elif tok == END_NODE:
            cur = cur.parent
        elif tok == PROP:
            ln, nameoff = struct.unpack('>II', blob[pos:pos + 8])
            pos += 8
            cur.props[string(nameoff)] = blob[pos:pos + ln]
            pos = (pos + ln + 3) & ~3
        elif tok == NOP:
            continue
        elif tok == END:
            return root
        else:
            raise SystemExit(f'bad FDT token {tok:#x} at {pos - 4:#x}')


def regs(node):
    """(addr, size) pairs of a node's reg, using the parent's cell sizes."""
    p = node.parent
    ac, sc = (p.cells('#address-cells', 2), p.cells('#size-cells', 1)) if p else (2, 1)
    raw = node.props.get('reg', b'')
    step = 4 * (ac + sc)
    out = []
    for i in range(0, len(raw) - step + 1, step):
        words = struct.unpack('>%dI' % (ac + sc), raw[i:i + step])
        addr = 0
        for w in words[:ac]:
            addr = (addr << 32) | w
        size = 0
        for w in words[ac:]:
            size = (size << 32) | w
        out.append((addr, size))
    return out


def compat(node):
    return node.props.get('compatible', b'').split(b'\0')


results = []


def report(level, what, detail):
    results.append(level)
    print(f'{level:4}  {what}: {detail}')


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = parse(open(sys.argv[1], 'rb').read())
    nodes = list(root.walk())

    model = root.props.get('model', b'?').rstrip(b'\0').decode(errors='replace')
    print(f'model: {model}')
    if b'qcom,sdmmagpie' not in b''.join(compat(root)) and 'magpie' not in model.lower():
        report('WARN', 'SoC', 'root is not qcom,sdmmagpie (Snapdragon 730/732G); is this a hanoip tree?')

    # Memory: the port gives XNU the whole upper DDR bank (above 4 GiB).
    banks = [r for n in nodes if n.props.get('device_type', b'').startswith(b'memory') for r in regs(n)]
    high = [b for b in banks if b[0] >= 0x100000000]
    if not banks:
        report('FAIL', 'memory', 'no memory node')
    elif not high:
        report('FAIL', 'memory', f'no bank above 4 GiB: {[(hex(a), hex(s)) for a, s in banks]}')
    else:
        base, size = max(high, key=lambda b: b[1])
        report('PASS', 'memory', f'upper bank {base:#x} + {size:#x} ({size / 2**30:.2f} GiB)')
        print(f'      -> tools/mkadt.py: HIGH_PHYS_BASE = {base:#x}  HIGH_MEM_SIZE = {size:#x}')
        res = [r for n in nodes if n.parent is not None and n.parent.name == 'reserved-memory' for r in regs(n)]
        clash = [(a, s) for a, s in res if a < base + size and a + s > base]
        if clash:
            report('FAIL', 'memory', f'reserved regions inside the upper bank: {[(hex(a), hex(s)) for a, s in clash]}')
        else:
            report('PASS', 'memory', 'no fixed reserved-memory region overlaps the upper bank')

    # Boot framebuffer left on by ABL
    fb = [r for n in nodes if 'splash' in n.name for r in regs(n)]
    if any(a == EXPECT['fb_base'] and s >= EXPECT['fb_min_size'] for a, s in fb):
        report('PASS', 'framebuffer', f'cont_splash at {EXPECT["fb_base"]:#x}, big enough for 1080x2460')
    else:
        report('FAIL', 'framebuffer', f'expected {EXPECT["fb_base"]:#x}, found {[(hex(a), hex(s)) for a, s in fb]}')

    # Interrupt controller
    gic = [n for n in nodes if b'arm,gic-v3' in compat(n)]
    if gic and len(regs(gic[0])) >= 2 and regs(gic[0])[0][0] == EXPECT['gicd'] and regs(gic[0])[1][0] == EXPECT['gicr']:
        report('PASS', 'GICv3', f'GICD {EXPECT["gicd"]:#x}, GICR {EXPECT["gicr"]:#x}')
    else:
        report('FAIL', 'GICv3', f'found {[(hex(a), hex(s)) for a, s in regs(gic[0])] if gic else "none"}')

    # Timer
    timer = [n for n in nodes if b'arm,armv8-timer' in compat(n)]
    hz = timer[0].cells('clock-frequency', None) if timer else None
    if hz in (None, EXPECT['timer_hz']):
        report('PASS', 'timer', f'{EXPECT["timer_hz"]} Hz' + (' (from CNTFRQ, not in DT)' if hz is None else ''))
    else:
        report('FAIL', 'timer', f'{hz} Hz, port assumes {EXPECT["timer_hz"]}')

    # UFS storage
    ufs = [n for n in nodes if any(c.startswith(b'qcom,ufshc') for c in compat(n))]
    if any(r[0] == EXPECT['ufs'] for n in ufs for r in regs(n)):
        report('PASS', 'UFS', f'ufshc at {EXPECT["ufs"]:#x}')
    else:
        report('FAIL', 'UFS', f'no ufshc at {EXPECT["ufs"]:#x} (eMMC phone? the port needs UFS)')

    # Touch: G60 uses an Ilitek TDDI on SPI, not the Goodix I2C chip of sweet
    ilitek = [n for n in nodes if any(b'ilitek' in c for c in compat(n))]
    goodix = [n for n in nodes if any(b'goodix' in c for c in compat(n)) and n.props.get('status', b'okay')[:2] == b'ok']
    if ilitek:
        bus = ilitek[0].parent
        where = regs(bus)[0][0] if bus is not None and regs(bus) else None
        lvl = 'PASS' if where == EXPECT['touch_spi'] else 'WARN'
        report(lvl, 'touch', f'Ilitek on {bus.path() if bus else "?"} '
               f'({hex(where) if where is not None else "?"}); no XNU driver yet, boot with sweettouch=0')
    elif goodix:
        report('WARN', 'touch', f'Goodix found at {goodix[0].path()}: different touch panel variant than expected')
    else:
        report('WARN', 'touch', 'no Ilitek or Goodix node found')

    # Panel resolution
    heights = {n.cells('qcom,mdss-dsi-panel-height', 0) for n in nodes if 'qcom,mdss-dsi-panel-height' in n.props}
    heights.discard(0)
    if not heights:
        report('WARN', 'panel', 'no panel timing in the live tree (ABL may strip it); port assumes 1080x2460')
    elif EXPECT['panel_h'] in heights:
        report('PASS', 'panel', 'a 2460-row panel timing is present')
    else:
        report('FAIL', 'panel', f'panel heights {sorted(heights)}; port is built for 2460')

    fails = results.count('FAIL')
    print(f'\n{len(results)} checks: {results.count("PASS")} pass, {results.count("WARN")} warn, {fails} fail')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
