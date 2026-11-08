"""Check relative links and their anchors in the repository Markdown files.

Run from the repository root: python3 .github/scripts/check_doc_links.py
Exits with 1 and lists the broken links when any relative link or anchor does not resolve.
"""

import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", ".angular", "dist"}
LINK = re.compile(r"\]\(([^)\s]+)\)")
PLACEHOLDER = "NNNN"  # ADR template links


def slug(heading: str) -> str:
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


def headings(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {slug(line.lstrip("#")) for line in lines if line.startswith("#")}


def broken_links(root: Path) -> list[str]:
    files = markdown_files(root)
    anchors = {p.resolve(): headings(p) for p in files}
    problems = []
    for path in files:
        for match in LINK.finditer(path.read_text(encoding="utf-8")):
            url = match.group(1)
            if url.startswith(("http://", "https://", "mailto:")) or PLACEHOLDER in url:
                continue
            target_part, _, anchor = url.partition("#")
            target = (path.parent / target_part).resolve() if target_part else path.resolve()
            where = path.relative_to(root)
            if not target.exists():
                problems.append(f"{where}: missing target {url}")
            elif anchor and target.suffix == ".md" and anchor not in anchors.get(target, set()):
                problems.append(f"{where}: missing anchor {url}")
    return problems


def main() -> int:
    problems = broken_links(Path.cwd())
    for problem in problems:
        print(problem)
    print(f"{len(problems)} broken link(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
