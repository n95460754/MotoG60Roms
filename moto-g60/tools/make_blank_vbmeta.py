#!/usr/bin/env python3
"""Write an empty AVB vbmeta image with verification disabled (flags=2).

Same result as:  avbtool make_vbmeta_image --flags 2 --padding_size 4096
Header layout follows AvbVBMetaImageHeader (256 bytes, big-endian).
"""
import struct
import sys

FMT = "!4s2L2QL2Q2Q2Q2Q2QQLL47sx80x"
FLAG_VERIFICATION_DISABLED = 2


def build() -> bytes:
    header = struct.pack(
        FMT,
        b"AVB0", 1, 0,          # magic, libavb version major/minor
        0, 0,                   # auth / aux block sizes
        0,                      # algorithm: NONE
        0, 0, 0, 0,             # hash, signature
        0, 0, 0, 0,             # public key, public key metadata
        0, 0,                   # descriptors
        0,                      # rollback index
        FLAG_VERIFICATION_DISABLED,
        0,                      # rollback index location
        b"avbtool 1.3.0",
    )
    assert len(header) == 256
    return header.ljust(4096, b"\0")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "vbmeta_disabled.img"
    with open(out, "wb") as f:
        f.write(build())
    print(f"wrote {out}")
