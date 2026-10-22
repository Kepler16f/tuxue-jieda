# -*- coding: utf-8 -*-
"""从 Director 二进制文件里扫描可读字符串（GBK 中文 + ASCII），用于捞章节名/题干文本。
用法: py -3 -B extract_strings.py <file> [min_len]
"""
import re
import sys

GBK = re.compile(rb"[\x81-\xfe][\x40-\xfe](?:[\x81-\xfe][\x40-\xfe]|[\x20-\x7e])*")
ASCII = re.compile(rb"[\x20-\x7e]{4,}")


def scan(path: str, minlen: int = 4):
    data = open(path, "rb").read()
    out = []
    for m in GBK.finditer(data):
        try:
            s = m.group().decode("gbk")
        except UnicodeDecodeError:
            continue
        s = s.strip()
        if len(s) >= max(2, minlen // 2) and not s.isascii():
            out.append((m.start(), s))
    for m in ASCII.finditer(data):
        s = m.group().decode("ascii", "replace").strip()
        if len(s) >= minlen:
            out.append((m.start(), s))
    return out


def main():
    path = sys.argv[1]
    minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for off, s in scan(path, minlen):
        print(f"{off:08x} {s}")


if __name__ == "__main__":
    main()
