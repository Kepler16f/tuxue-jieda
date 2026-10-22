# -*- coding: utf-8 -*-
"""v7 索引：完全由用户 CSV 驱动页码和题号，未修正项按模块规律推算。"""
import json
import pathlib
import re
import csv
from datetime import datetime

TOOLS = pathlib.Path(__file__).resolve().parent
SITE = TOOLS.parent / "site"
STAGING = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging")
IMG_SRC = STAGING / "AnsSubTu"
JIETI_SRC = STAGING / "jieti"
AVI_SRC = STAGING / "avi"
NAV = json.loads((TOOLS / "nav_map.json").read_text(encoding="utf-8"))
texts = json.loads((SITE / "data" / "texts.json").read_text(encoding="utf-8"))

TYPE_RX = re.compile(r"(na|ns|a|s|e)(\d*)$")

# 读取用户 CSV（页码 + 题号 + 模块）
USER_PAGE = {}
USER_LABEL = {}
CSV_MODULE = {}
csv_path = pathlib.Path("C:/Users/胡天泽/Desktop/page_map.csv")
if csv_path.exists():
    for r in csv.reader(open(csv_path, encoding="utf-8-sig")):
        if len(r) >= 4:
            tihao = r[0].strip()
            try:
                if r[2].strip():
                    USER_PAGE[tihao] = int(r[2])
            except (ValueError, IndexError):
                pass
            try:
                if r[3].strip():
                    USER_LABEL[tihao] = r[3].strip()
            except (ValueError, IndexError):
                pass
            if len(r) >= 5 and r[4].strip():
                CSV_MODULE[tihao] = r[4].strip()


# tihao -> 所属模块电影（由 nav_map 反查）。同一 tihao 可能被多个电影引用
# （gct 与 zht 有 28 个交叉按钮），以用户 CSV 的"模块"列为准定归属。
MOVIES_OF = {}
for _movie, _scripts in NAV.items():
    for _sc in _scripts:
        for _t in (_sc["tihao"] or []):
            MOVIES_OF.setdefault(_t, set()).add(_movie)

BTN_MODULE = {}
for _t, _mv in MOVIES_OF.items():
    _c = CSV_MODULE.get(_t)
    BTN_MODULE[_t] = _c if (_c in _mv) else sorted(_mv)[0]

# 每模块非变式锚点 (prefix, page)，按 prefix 升序；同前缀兄弟页（CSV 已定）
def _is_variant(t):
    return "_n" in t or t.endswith("n")

ANCHORS = {}      # module -> sorted [(prefix, page)]
PREFIX_PAGE = {}  # prefix -> {pages}（非变式 CSV 锚点，供兄弟复制）
for _t, _p in USER_PAGE.items():
    if _is_variant(_t):
        continue
    _m = re.match(r"^(\d+)", _t)
    if not _m:
        continue
    _mod = BTN_MODULE.get(_t)
    if _mod is None:
        continue
    _pf = int(_m.group(1))
    ANCHORS.setdefault(_mod, []).append((_pf, _p))
    PREFIX_PAGE.setdefault(_pf, set()).add(_p)
for _mod in ANCHORS:
    ANCHORS[_mod] = sorted(set(ANCHORS[_mod]))


def _ramp_page(prefix, module):
    """模块完全无锚点时的兜底：旧的偏移阶梯。"""
    if module == "jcty": offset = 4
    elif module == "zht": offset = 5
    elif module == "gct": offset = 6
    else: offset = 0
    return max(1, min(prefix - offset, 126))


def correct_page(tihao, module):
    """页码规律（按 2026-10-15 CSV 重析）：
    1) CSV 修正最优先；2) 变式题固定自身文件夹页；
    3) 同前缀有 CSV 兄弟 → 复制其页；4) 锚点夹逼线性插值（负斜率时取较近
    锚点偏移，平手取右）；5) 锚点范围外按首/末锚点偏移外推。"""
    if tihao in USER_PAGE:
        return USER_PAGE[tihao]
    m = re.match(r"^(\d+)", tihao)
    if not m:
        return 0
    prefix = int(m.group(1))
    if _is_variant(tihao):
        return prefix
    sib = PREFIX_PAGE.get(prefix)
    if sib and len(sib) == 1:
        return next(iter(sib))
    A = ANCHORS.get(module, [])
    if not A:
        return _ramp_page(prefix, module)
    if prefix < A[0][0]:
        return max(1, min(prefix - (A[0][0] - A[0][1]), 126))
    if prefix > A[-1][0]:
        return max(1, min(prefix - (A[-1][0] - A[-1][1]), 126))
    left = right = None
    for p, g in A:
        if p <= prefix:
            left = (p, g)
        if p >= prefix and right is None:
            right = (p, g)
    if left and left[0] == prefix:
        return left[1]
    lp, lc = left
    rp, rc = right
    if rc >= lc:
        page = lc + round((rc - lc) * (prefix - lp) / (rp - lp))
    else:
        # 负斜率（章节轴交错）：取较近锚点的偏移，平手取右
        off = (lp - lc) if (prefix - lp) < (rp - prefix) else (rp - rc)
        page = prefix - off
    return max(1, min(page, 126))


def correct_label(tihao, default_label):
    # 用户口头修正（覆盖 CSV）
    ORAL_FIX = {"36_7_n": "48"}
    if tihao in ORAL_FIX:
        ul = ORAL_FIX[tihao]
        return f"第{ul}题"
    if tihao in USER_LABEL:
        ul = USER_LABEL[tihao]
        m = re.fullmatch(r"(\d+)(n?)", ul)
        if m:
            label = f"第{m.group(1)}题"
            if m.group(2):
                label += "·变式"
            return label
        m2 = re.fullmatch(r"(\d+)\((\d+)\)", ul)
        if m2:
            return f"第{m2.group(1)}题({m2.group(2)})"
        return ul
    return default_label


def main():
    entries = []
    seen = set()
    for movie, scripts in NAV.items():
        for s in scripts:
            if not s["tihao"]:
                continue
            for t in s["tihao"]:
                name = s["script"].lstrip("g")
                # 交叉按钮：只认 CSV/优先级定下的归属模块，其余模块的同名按钮忽略
                if BTN_MODULE.get(t, movie) != movie:
                    continue
                dk = (t, movie)
                if dk in seen:
                    continue
                seen.add(dk)
                m = re.fullmatch(r"(\d+)_(.+)", name)
                if m:
                    nums = [int(n) for n in re.findall(r"\d+", m.group(2))]
                    variant = m.group(2).endswith("n") or m.group(2).endswith("_n")
                    page = correct_page(t, movie)
                    entries.append({
                        "page": page,
                        "qnum": nums[0] if nums else 0,
                        "sub": nums[1] if len(nums) > 1 else 0,
                        "variant": variant, "tihao": t, "module": movie,
                    })
                else:
                    m2 = re.fullmatch(r"(\d+)n?", name)
                    if m2:
                        page = correct_page(t, movie)
                        entries.append({
                            "page": page, "qnum": 0, "sub": 0,
                            "variant": True, "tihao": t, "module": movie,
                        })

    entries.sort(key=lambda e: (e["page"], e["qnum"], e["sub"], 1 if e["variant"] else 0))
    items = {}
    order = [0]

    def get(tihao, page, label):
        if tihao in items:
            return items[tihao]
        order[0] += 1
        txt = texts.get(tihao)
        if txt and txt.startswith("FFFF"):
            txt = None
        it = {
            "id": tihao, "tihao": tihao, "label": label, "order": order[0],
            "page": page,
            "question": [], "answer": [], "n_question": [], "n_answer": [],
            "frames_s": [], "frames_a": [], "e_series": [], "letters": {},
            "movies": [], "videos": [],
            "text": txt,
        }
        items[tihao] = it
        return it

    for e in entries:
        if e["variant"]:
            default = f"第{e['qnum']}题" + (f"({e['sub']})" if e["sub"] else "") + "·变式"
        elif e["sub"]:
            default = f"第{e['qnum']}题({e['sub']})"
        else:
            default = f"第{e['qnum']}题"
        label = correct_label(e["tihao"], default)
        get(e["tihao"], e["page"], label)
    # ---------- 素材挂载 ----------
    btn_to_tihao = {}
    for movie, scripts in NAV.items():
        for sc in scripts:
            if not sc["tihao"]:
                continue
            bn = sc["script"].lstrip("g")
            for t in sc["tihao"]:
                btn_to_tihao[bn] = t

    def slot_of(tail):
        """返回 (归属tihao, 匹配方式)。'canon'=文件名主体与题号同名；
        'fallback'=经按钮名兜底命中（如 P40_48s 落到按钮 g40_48 的题 36_7_n）。"""
        cands = [tail]
        if tail.endswith("_n"):
            cands.append(tail[:-2])
        elif tail.endswith("n"):
            cands.append(tail[:-1])
        cands.append(tail + "_n")
        cands.append(tail + "n")
        for c in cands:
            if c in items:
                return c, "canon"
        for c in cands:
            if c in btn_to_tihao:
                th = btn_to_tihao[c]
                if th in items:
                    return th, "fallback"
        return None, None

    unclassified = []
    for f in sorted(IMG_SRC.glob("*.jpg")):
        src = f"assets/img/{f.name}"
        rest = f.stem[1:] if f.stem[:1] in "Pp" else f.stem
        letter = None
        lm = re.search(r"_([A-C])$", rest)
        if lm:
            letter = lm.group(1); rest = rest[:lm.start()]
        tm = TYPE_RX.search(rest)
        if not tm:
            unclassified.append(f.stem); continue
        core = rest[:tm.start()]
        typ, frame = tm.group(1), tm.group(2)
        if typ in ("na", "ns"):
            core = core[:-1] if core.endswith("_") else core
        base_type = "a" if typ in ("a", "na") else ("s" if typ in ("s", "ns") else "e")
        t, match = slot_of(core)
        if t is None:
            continue
        it = items[t]
        if base_type == "e":
            it["e_series"].append({"frame": int(frame) if frame else 0, "img": src})
        elif letter:
            it["letters"][letter] = src
        elif frame:
            (it["frames_a"] if base_type == "a" else it["frames_s"]).append((int(frame), src))
        else:
            # _n 项：canon(题号同名图)=题目，fallback(按钮名兜底图)=变式。
            # 非 _n 项：按图后缀 ns/na 判变式。
            if it["tihao"].endswith("_n"):
                is_var = (match == "fallback")
            else:
                is_var = typ in ("na", "ns")
            if base_type == "a":
                (it["n_answer"] if is_var else it["answer"]).append(src)
            else:
                (it["n_question"] if is_var else it["question"]).append(src)

    jie_unmapped = []
    for f in sorted(JIETI_SRC.glob("*.dir")):
        s = f.stem
        if not s.startswith("jieP"):
            jie_unmapped.append(s); continue
        t, _match = slot_of(s[4:])
        if t is None:
            continue
        items[t]["movies"].append({"stem": s})

    avi_unmapped = []
    for f in sorted(AVI_SRC.glob("*.avi")):
        if f.stem == "nodio":
            continue
        s = f.stem
        tail = s[1:] if s.startswith("a") else s
        if not tail.startswith("P"):
            avi_unmapped.append(s); continue
        t, _match = slot_of(tail[1:])
        if t is None:
            continue
        it = items[t]
        vsrc = f"assets/video/{s}.mp4"
        if vsrc not in [v["src"] for v in it["videos"]]:
            it["videos"].append({"src": vsrc, "poster": f"assets/video/posters/{s}.jpg"})

    # ---------- 清理 ----------
    for t in list(items):
        it = items[t]
        has = (it["question"] or it["answer"] or it["n_question"] or it["n_answer"] or
               it["frames_s"] or it["frames_a"] or it["e_series"] or it["letters"] or
               it["movies"] or it["videos"] or
               (it["text"] and not it["text"].startswith("FFFF")))
        if not has:
            del items[t]

    # ---------- 严格一页两题 ----------
    # 原则：每页最多两道主题（变式·变式 不占名额）。超员的页挪走代价最小的项：
    # 推算项代价 1/页、CSV 项 50/页（尽量不动用户数据），挪到最近的有空位页。
    def _prob_num(it):
        m = re.match(r"第(\d+)题", it.get("label") or "")
        return int(m.group(1)) if m else None

    def _is_var_label(it):
        return "·变式" in (it.get("label") or "")

    by_page = {}
    for it in items.values():
        by_page.setdefault(it["page"], []).append(it)

    def _mains(pg):
        s = set()
        for x in by_page.get(pg, []):
            if _is_var_label(x):
                continue
            pn = _prob_num(x)
            if pn is not None:
                s.add(pn)
        return s

    moves_log = []
    for _round in range(20):
        moved = False
        for pg in sorted(by_page):
            if len(_mains(pg)) <= 2:
                continue
            best = None  # (cost, tihao, new_page)
            for it in by_page[pg]:
                if _is_var_label(it) or _prob_num(it) is None:
                    continue
                w = 50 if it["tihao"] in USER_PAGE else 1
                for d in range(1, 9):
                    hit = None
                    for npg in (pg + d, pg - d):
                        if not (1 <= npg <= 126):
                            continue
                        if _prob_num(it) in _mains(npg):
                            continue
                        if len(_mains(npg)) < 2:
                            hit = npg
                            break
                    if hit is not None:
                        cost = w * d
                        if best is None or cost < best[0]:
                            best = (cost, it, hit)
                        break
            if best:
                _, it, npg = best
                by_page[pg].remove(it)
                it["page"] = npg
                by_page.setdefault(npg, []).append(it)
                src = "CSV" if it["tihao"] in USER_PAGE else "推算"
                moves_log.append(f"{it['tihao']}: {pg} -> {npg} [{src}]")
                moved = True
        if not moved:
            break

    # ---------- 输出 ----------
    def finalize(it):
        for key in ("frames_s", "frames_a"):
            it[key].sort(key=lambda t: t[0]); it[key] = [t[1] for t in it[key]]
        it["e_series"].sort(key=lambda e: e["frame"])
        for lst in (it["question"], it["answer"], it["n_question"], it["n_answer"]):
            lst.sort()

    pages = {}
    for it in sorted(items.values(), key=lambda i: (i.get("page", 9999), i["order"])):
        finalize(it)
        pages.setdefault(it["page"], []).append(it)

    placed_img = sum(len(i["question"]) + len(i["answer"]) + len(i["n_question"]) +
                     len(i["n_answer"]) + len(i["frames_s"]) + len(i["frames_a"]) +
                     len(i["e_series"]) + len(i["letters"]) for i in items.values())
    stats = {
        "items": len(items), "pages": len(pages), "images": placed_img,
        "jieti": sum(len(i["movies"]) for i in items.values()),
        "videos": sum(len(i["videos"]) for i in items.values()),
    }
    data = {
        "app": "图学基础教程习题解答", "version": 7,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "pages": [{"page": p_, "items": pages[p_]} for p_ in sorted(pages)],
        "stats": stats,
    }
    out = SITE / "data" / "index.json"
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text(payload, encoding="utf-8")
    (SITE / "data" / "index.js").write_text("window.INDEX_DATA=" + payload + ";\n", encoding="utf-8")

    print(f"[index7] items={stats['items']} pages={stats['pages']}")
    print(f"[index7] images={stats['images']}/496, jieti={stats['jieti']}/203, videos={stats['videos']}/75")
    if moves_log:
        print(f"[两题规则] 调整 {len(moves_log)} 项：")
        for m_ in moves_log:
            print("  ", m_)
    for p_ in (11, 18, 20, 31, 32, 36, 44, 62, 80, 86):
        if p_ in pages:
            print(f"  P{p_}: {[(i['label'], i['tihao']) for i in pages[p_]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
