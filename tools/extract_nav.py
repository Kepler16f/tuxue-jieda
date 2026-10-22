# -*- coding: utf-8 -*-
"""全量抽取 4 个模块电影的所有按钮行为脚本：
   脚本名 / tihao 赋值 / 引用的 cast 成员名 —— 建立"程序调用"视角的页-题表。
输出: tools/nav_map.json + 控制台抽样
"""
import json
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging\_pr_work")
STAGING = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging")
OUT = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_web\tools\nav_map.json")

modules = {}
for movie in ("gct", "jcty", "zht", "other", "txxt"):
    base = ROOT / movie
    if not base.exists():
        continue
    scripts = []
    for f in sorted(base.rglob("*.ls")):
        src = f.read_text(encoding="utf-8", errors="replace")
        name = f.stem.split(" - ")[-1]
        tihao = re.findall(r'tihao\s*=\s*"([^"]+)"', src)
        # 引用的成员名: "P..."&tihao 或字面 "P36_7a" 等
        members = set(re.findall(r'"([Pp][0-9][0-9a-zA-Z_]*)"', src))
        goto = re.findall(r'go(?:to)?\s+(?:movie\s+)?"?([\w ]+)"?', src, re.I)
        scripts.append({
            "script": name,
            "file": str(f.relative_to(ROOT)),
            "tihao": tihao,
            "members": sorted(members),
            "goto": goto,
        })
    modules[movie] = scripts

pathlib.Path(OUT).write_text(json.dumps(modules, ensure_ascii=False, indent=1),
                             encoding="utf-8")

# 抽样: 谁引用了 36_7 / 40_49 / 40_48
for movie, scripts in modules.items():
    for s in scripts:
        blob = " ".join(s["tihao"]) + " " + " ".join(s["members"]) + " " + s["script"]
        if re.search(r'36_7|40_4[89]|36_4[23]', blob):
            print(f"{movie}: {s['script']:16s} tihao={s['tihao']} members={s['members'][:8]}")

# 汇总统计
total = sum(len(v) for v in modules.values())
withtihao = sum(1 for v in modules.values() for s in v if s["tihao"])
print(f"\ntotal scripts={total}, with tihao={withtihao}")
all_t = set()
for v in modules.values():
    for s in v:
        all_t.update(s["tihao"])
print("unique tihao values:", len(all_t))
print(f"saved -> {OUT}")
