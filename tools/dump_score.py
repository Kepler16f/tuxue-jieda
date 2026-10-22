# -*- coding: utf-8 -*-
"""dump 指定 Director 电影 mmap 中 score 相关块的原始字节。"""
import json
import pathlib
import re
import struct
import sys

movie = sys.argv[1] if len(sys.argv) > 1 else "gct"
STAGING = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging")
mmapf = STAGING / "_pr_work" / movie / movie / "chunks" / "mmap-2.json"
mm = json.load(open(mmapf, encoding="utf-8"))["mapArray"]
data = (STAGING / f"{movie}.dir").read_bytes()

WANT = ("VWFI", "VWLB", "Sord", "SCRF", "Cinf", "VWSC", "GRID", "FCOL", "DRCF", "FXmp")

def show(tag, off, ln):
    blob = data[off:off + ln]
    printable = re.sub(rb"[^\x20-\x7e]", b".", blob[:200]).decode()
    print(f"== {tag} off={off} len={ln}")
    print(f"   head: {printable}")
    # 若开头像块树（tag+len 序列），尝试递归 walk
    if tag == "VWSC":
        p = 0
        while p + 8 <= len(blob):
            t = blob[p:p + 4]
            if re.match(rb"^[\x20-\x7e]{4}$", t):
                ln2 = struct.unpack(">I", blob[p + 4:p + 8])[0]
                print(f"   child: {t.decode()} len={ln2} @off+{p}")
                p += 8 + ln2 + (ln2 & 1)
            else:
                break

for e in mm:
    if e["fourCC"] in WANT:
        show(e["fourCC"], e["offset"], e["len"])

# VWSC 头部再细看
for e in mm:
    if e["fourCC"] == "VWSC":
        blob = data[e["offset"]:e["offset"] + min(e["len"], 4096)]
        print("\n== VWSC full hex head 256:")
        for i in range(0, 256, 16):
            row = blob[i:i + 16]
            asc = re.sub(rb"[^\x20-\x7e]", b".", row).decode()
            print(f"   {i:04x} {row.hex(' ')}  {asc}")
