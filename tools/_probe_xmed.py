# -*- coding: utf-8 -*-
"""探针: 查看指定文本成员的 XMED blob 中正文起点前后的原始字节。"""
import glob
import json
import pathlib
import re

STAGING = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging")
CHUNKS = STAGING / "_pr_work" / "text" / "chunks"

raw = (CHUNKS / "KEY_-3.json").read_text(encoding="utf-8", errors="replace")
key = json.loads(re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\1", raw))
mm = json.load(open(CHUNKS / "mmap-2.json", encoding="utf-8"))["mapArray"]

names = {}
for f in glob.glob(str(CHUNKS / "CASt-*.json")):
    cid = int(re.search(r"CASt-(\d+)", f).group(1))
    d = json.load(open(f, encoding="utf-8"))
    nm = d.get("info", {}).get("name", "")
    if nm:
        names[cid] = nm
rev = {v: k for k, v in names.items()}

data = (STAGING / "text.cst").read_bytes()

targets = {
    "TP13_1": "已知空间点",
    "TP104_16": "已知零件图配合部位",
    "TP101_13": "标注零件表面粗糙度",
    "TP115_22_2": "球阀",
}
for want, anchor in targets.items():
    cid = rev.get(want)
    sid = None
    for e in key["entries"]:
        if e["castID"] == cid and e["fourCC"] == "XMED":
            sid = e["sectionID"]
    if sid is None:
        print(f"== {want}: no XMED")
        continue
    sec = mm[sid]
    blob = data[sec["offset"]:sec["offset"] + sec["len"]]
    pos = blob.find(anchor.encode("gbk"))
    print(f"== {want} len={len(blob)} textpos={pos}")
    if pos >= 0:
        print("   before:", repr(blob[max(0, pos - 70):pos]))
        print("   after :", repr(blob[pos:pos + 50]))
        print("   tail  :", repr(blob[-60:]))
