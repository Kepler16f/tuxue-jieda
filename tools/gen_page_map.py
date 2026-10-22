# -*- coding: utf-8 -*-
"""生成页码映射模板文件 page_map.csv，用户可编辑后重建索引。

格式: tihao,默认页码,正确页码,显示题号
用户只需修改"正确页码"和"显示题号"列中不对的条目。
留空 = 使用默认值。
"""
import json
import pathlib
import csv

TOOLS = pathlib.Path(__file__).resolve().parent
SITE = TOOLS.parent / "site"
NAV = json.loads((TOOLS / "nav_map.json").read_text(encoding="utf-8"))
texts = json.loads((SITE / "data" / "texts.json").read_text(encoding="utf-8"))

rows = []
for movie, scripts in NAV.items():
    for s in scripts:
        if not s["tihao"]:
            continue
        for t in s["tihao"]:
            name = s["script"].lstrip("g")
            # 默认页码 = tihao 前缀（大多数正确）
            m = t.split("_")
            default_page = m[0] if m[0].isdigit() else ""
            # 显示题号 = tihao 第二段
            qnum = m[1] if len(m) > 1 else ""
            # 题干摘要
            txt = (texts.get(t) or "")[:40].replace(",", "，")
            rows.append([t, default_page, "", qnum, movie, txt])

# 去重
seen = set()
deduped = []
for r in rows:
    if r[0] not in seen:
        seen.add(r[0])
        deduped.append(r)

out = TOOLS / "page_map.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["tihao", "默认页码", "正确页码(留空=默认)", "显示题号", "模块", "题干摘要"])
    w.writerows(deduped)

print(f"生成 {out}，共 {len(deduped)} 行")
print("编辑方法：修改'正确页码'列中不对的页码，留空表示默认正确")
print("完成后运行: py -3 tools/build_index.py --page-map tools/page_map.csv")
