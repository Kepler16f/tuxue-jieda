# -*- coding: utf-8 -*-
"""从 text.cst（Director 道具库）提取每个习题的题干文字。

原理（已实测）：
- KEY_ 块是索引表: {sectionID, castID, fourCC}; 每个文本成员有两段: Thum + XMED
- mmap 块给出 sectionID -> (offset, len)，偏移相对原始 text.cst 文件
- XMED 段 = 二进制样式头 + GBK 正文（正文里可能夹 ASCII 如 "φ30mm"）
- 成员名从 ProjectorRays 输出的 CASt-<id>.json 的 info.name 获得（TP<页>_<题>[_<步>]）

输出: site/data/texts.json  =  {"P13_1": "题干文字", "P22_19_1": "...", ...}
"""
import json
import pathlib
import re

TOOLS = pathlib.Path(__file__).resolve().parent
SITE = TOOLS.parent / "site"
STAGING = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging")
PR_OUT = STAGING / "_pr_work" / "text" / "chunks"
CST = STAGING / "text.cst"


def load_lenient_json(path: pathlib.Path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\1", raw)
    return json.loads(raw)


def extract_text_zone(blob: bytes) -> str:
    """取 blob 中最长的可读文字区（GBK 汉字/全角标点 + ASCII + 换行）。"""
    best = b""
    cur = bytearray()
    i = 0
    n = len(blob)
    while i < n:
        b = blob[i]
        if 0x20 <= b <= 0x7E or b in (0x0D, 0x0A, 0x09):
            cur.append(b)
            i += 1
        elif 0x81 <= b <= 0xFE and i + 1 < n and 0x40 <= blob[i + 1] <= 0xFE \
                and blob[i + 1] != 0x7F:
            cur.append(b)
            cur.append(blob[i + 1])
            i += 2
        else:
            if len(cur) > len(best):
                best = bytes(cur)
            cur = bytearray()
            i += 1
    if len(cur) > len(best):
        best = bytes(cur)
    try:
        s = best.decode("gbk")
    except UnicodeDecodeError:
        s = best.decode("gbk", "replace")
    return s.strip()


def main() -> None:
    key = load_lenient_json(PR_OUT / "KEY_-3.json")
    mm = load_lenient_json(PR_OUT / "mmap-2.json")
    map_array = mm["mapArray"]

    # castID -> 成员名
    names = {}
    for f in PR_OUT.glob("CASt-*.json"):
        cid = int(re.search(r"CASt-(\d+)", f.name).group(1))
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            nm = d.get("info", {}).get("name", "")
            if nm:
                names[cid] = nm
        except Exception as e:
            print(f"  warn: CASt-{cid} parse failed: {e}")

    data = CST.read_bytes()
    texts = {}
    skipped = []
    for e in key["entries"]:
        if e["fourCC"] != "XMED":
            continue
        cid, sid = e["castID"], e["sectionID"]
        nm = names.get(cid, f"?{cid}")
        if not nm.startswith("TP"):
            skipped.append(nm)
            continue
        if not (0 <= sid < len(map_array)):
            print(f"  warn: {nm} sectionID {sid} out of range")
            continue
        sec = map_array[sid]
        off, ln = sec["offset"], sec["len"]
        blob = data[off:off + ln]
        t = extract_text_zone(blob)
        keyname = nm[2:] if nm.startswith("TP") else nm   # TP13_1 -> 13_1
        texts[keyname] = t

    out = SITE / "data" / "texts.json"
    out.write_text(json.dumps(texts, ensure_ascii=False, indent=0,
                              sort_keys=True), encoding="utf-8")
    print(f"[texts] extracted: {len(texts)} members, skipped non-TP: {skipped}")
    empty = [k for k, v in texts.items() if not v]
    if empty:
        print(f"[texts] empty: {empty}")
    for k in ["13_1", "101_13", "74", "22_19_1"]:
        v = texts.get(k)
        print(f"[texts] {k}: {v[:90] if v else '(missing)'}")
    print(f"[texts] -> {out}")


if __name__ == "__main__":
    main()
