# -*- coding: utf-8 -*-
"""把 avi/ 里的 76 个 Director 导出动画转成 H.264 MP4，并抽首帧做封面图。
输出: site/assets/video/*.mp4 + site/assets/video/posters/*.jpg
报告: tools/transcode_report.json
"""
import json
import pathlib
import subprocess
import sys
import time

TOOLS = pathlib.Path(__file__).resolve().parent
FFMPEG = TOOLS / "ffmpeg" / "bin" / "ffmpeg.exe"
FFPROBE = TOOLS / "ffmpeg" / "bin" / "ffprobe.exe"
SRC = pathlib.Path(r"C:\Users\胡天泽\.zcode\workspace\default\_tuxue_pack\staging\avi")
DST = TOOLS.parent / "site" / "assets" / "video"
POST = DST / "posters"
DST.mkdir(parents=True, exist_ok=True)
POST.mkdir(parents=True, exist_ok=True)

report = {"ok": [], "fail": [], "probe": {}}


def probe(path: pathlib.Path) -> dict:
    r = subprocess.run(
        [str(FFPROBE), "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    info = {}
    if r.returncode == 0:
        j = json.loads(r.stdout)
        vs = [s for s in j.get("streams", []) if s.get("codec_type") == "video"]
        au = [s for s in j.get("streams", []) if s.get("codec_type") == "audio"]
        if vs:
            v = vs[0]
            info = {"codec": v.get("codec_name"), "w": v.get("width"),
                    "h": v.get("height"), "fps": v.get("r_frame_rate"),
                    "nb": v.get("nb_frames"), "dur": j.get("format", {}).get("duration")}
        info["has_audio"] = bool(au)
    return info


def main() -> None:
    files = sorted(SRC.glob("*.avi"))
    print(f"[transcode] {len(files)} files -> {DST}", flush=True)
    t0 = time.time()
    for i, f in enumerate(files, 1):
        stem = f.stem
        out = DST / (stem + ".mp4")
        info = probe(f)
        report["probe"][f.name] = info
        codec = info.get("codec", "?")
        print(f"[{i}/{len(files)}] {f.name} ({codec} {info.get('w')}x{info.get('h')}"
              f"@{info.get('fps')})", flush=True)
        cmd = [str(FFMPEG), "-y", "-v", "error", "-i", str(f),
               "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        if info.get("has_audio"):
            cmd += ["-c:a", "aac", "-b:a", "96k"]
        else:
            cmd += ["-an"]
        cmd += [str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
            report["ok"].append(f.name)
            # 封面: 0.3s 处一帧
            subprocess.run(
                [str(FFMPEG), "-y", "-v", "error", "-ss", "0.3", "-i", str(out),
                 "-frames:v", "1", "-q:v", "4", str(POST / (stem + ".jpg"))],
                capture_output=True)
        else:
            report["fail"].append({"file": f.name, "codec": codec,
                                   "err": (r.stderr or "")[-500:]})
            print(f"    FAILED: {(r.stderr or '')[-200:]}", flush=True)
    dt = time.time() - t0
    report["elapsed_sec"] = round(dt, 1)
    (TOOLS / "transcode_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[transcode] done: ok={len(report['ok'])} fail={len(report['fail'])} "
          f"in {dt/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
