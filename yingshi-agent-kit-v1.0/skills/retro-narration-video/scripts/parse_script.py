"""Parse a 口播稿 (版本A, `**第N章: 标题**` headings) into pipeline inputs.

Outputs:
  scripts/视频脚本_版本A_clean.md  (headings kept, metadata removed)
  scripts/口播流水_版本B.txt       (pure spoken text, no headings)
  audio/chapters.json             (TTS input; headings excluded from body)

Usage:
  python parse_script.py <project-dir>
"""
import json, os, re, sys

HEADING = re.compile(
    r"^\s*(?:#{1,6}\s*)?\**\s*第\s*([一二三四五六七八九十百0-9]+)\s*章(?:\s*[:：、.\-–—]\s*(.+?))?\s*\**\s*$"
)


def is_heading(line: str) -> bool:
    t = line.strip()
    if not t or len(t) > 60:
        return False
    if re.search(r"[。！？；…～]", t):
        return False
    return bool(HEADING.match(t))


def clean_line(line: str) -> str:
    t = line.strip()
    if re.fullmatch(r"[-*_—=\s]+", t):
        return ""
    t = re.sub(r"^#{1,6}\s*", "", t)
    t = t.replace("**", "")
    t = re.sub(r"^[-*•]\s+", "", t)
    return t


def main() -> None:
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    raw_path = os.path.join(project, "scripts", "视频脚本_版本A.md")
    with open(raw_path, encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r"(?s)^.*?Answer:\s*\n", "", raw)
    raw = re.sub(r"(?s)\n\s*Resumed conversation:.*$", "", raw)
    lines = raw.splitlines()
    flags = [is_heading(x) for x in lines]
    if any(flags):
        first = flags.index(True)
        lines, flags = lines[first:], flags[first:]
    with open(os.path.join(project, "scripts", "视频脚本_版本A_clean.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")

    chapters, title, block = [], None, []
    for ln, is_h in zip(lines, flags):
        if is_h:
            if title is not None:
                body = "\n".join(x for x in (clean_line(y) for y in block) if x).strip()
                chapters.append({"idx": len(chapters) + 1, "title": title, "text": body})
            title = (HEADING.match(ln.strip()).group(2) or "").strip() or "未命名"
            block = []
        else:
            block.append(ln)
    if title is not None:
        body = "\n".join(x for x in (clean_line(y) for y in block) if x).strip()
        chapters.append({"idx": len(chapters) + 1, "title": title, "text": body})

    flat = "\n".join(ch["text"] for ch in chapters).strip()
    os.makedirs(os.path.join(project, "audio"), exist_ok=True)
    os.makedirs(os.path.join(project, "scripts"), exist_ok=True)
    with open(os.path.join(project, "scripts", "口播流水_版本B.txt"), "w", encoding="utf-8") as f:
        f.write(flat + "\n")
    with open(os.path.join(project, "audio", "chapters.json"), "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=1)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", flat))
    print(f"{len(chapters)} chapters, {cjk} CJK chars")


if __name__ == "__main__":
    main()
