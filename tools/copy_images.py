# -*- coding: utf-8 -*-
"""把 AnsSubTu 的 496 张 jpg 复制到 site/assets/img，规范化小写 p 前缀为 P。
报告: tools/copy_images_report.json
"""
import json
import pathlib
import shutil

TOOLS = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging\AnsSubTu")
DST = TOOLS.parent / "site" / "assets" / "img"
DST.mkdir(parents=True, exist_ok=True)


def main() -> None:
    files = sorted(SRC.glob("*.jpg"))
    report = {"copied": 0, "renamed": [], "collisions": [], "total": len(files)}
    print(f"[copy] {len(files)} jpg -> {DST}")
    for f in files:
        name = f.name
        new = ("P" + name[1:]) if name[:1] == "p" else name
        t = DST / new
        if t.exists():
            if t.stat().st_size == f.stat().st_size:
                report["copied"] += 1
                continue
            report["collisions"].append(new)
            continue
        shutil.copy2(f, t)
        report["copied"] += 1
        if new != name:
            report["renamed"].append([name, new])
    (TOOLS / "copy_images_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[copy] done: {report['copied']} copied, "
          f"{len(report['renamed'])} renamed, {len(report['collisions'])} collisions")


if __name__ == "__main__":
    main()
