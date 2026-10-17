#!/usr/bin/env python3

from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
BASE_PATH = "/smaTassar-site"


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.title_depth = 0
        self.title = ""
        self.html_lang = ""
        self.has_charset = False
        self.has_viewport = False
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        values = dict(attrs)

        if identifier := values.get("id"):
            if identifier in self.ids:
                self.errors.append(f"duplicate id #{identifier}")
            self.ids.add(identifier)

        if tag == "html":
            self.html_lang = values.get("lang", "")
        elif tag == "meta":
            if values.get("charset", "").lower() == "utf-8":
                self.has_charset = True
            if values.get("name", "").lower() == "viewport":
                self.has_viewport = True
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "link" and values.get("rel") == "stylesheet":
            self.links.append(values.get("href", ""))
        elif tag == "script" and values.get("src"):
            self.errors.append(f"external script is not allowed: {values['src']}")
        elif tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title_depth = max(0, self.title_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title += data


def route_to_file(path: str) -> Path:
    clean_path = unquote(path)
    if clean_path.startswith(BASE_PATH):
        clean_path = clean_path[len(BASE_PATH):]
    clean_path = clean_path.lstrip("/")

    target = ROOT / clean_path
    if clean_path == "" or clean_path.endswith("/"):
        target = target / "index.html"
    return target


def main() -> int:
    failures: list[str] = []
    documents: dict[Path, DocumentParser] = {}

    for path in sorted(ROOT.rglob("*.html")):
        parser = DocumentParser()
        parser.feed(path.read_text(encoding="utf-8"))
        documents[path.resolve()] = parser

        label = path.relative_to(ROOT)
        if parser.errors:
            failures.extend(f"{label}: {error}" for error in parser.errors)
        if not parser.html_lang:
            failures.append(f"{label}: missing html lang attribute")
        if not parser.has_charset:
            failures.append(f"{label}: missing UTF-8 charset metadata")
        if not parser.has_viewport:
            failures.append(f"{label}: missing viewport metadata")
        if not parser.title.strip():
            failures.append(f"{label}: missing document title")

    for source, parser in documents.items():
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme in {"http", "https", "mailto"} or href.startswith("//"):
                continue

            target = route_to_file(parsed.path) if parsed.path.startswith("/") else (source.parent / parsed.path)
            if target.is_dir():
                target = target / "index.html"
            target = target.resolve()
            label = source.relative_to(ROOT)

            if not target.exists():
                failures.append(f"{label}: broken internal link {href}")
                continue

            if parsed.fragment and target.suffix == ".html":
                target_parser = documents.get(target)
                if target_parser is None:
                    target_parser = DocumentParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    documents[target] = target_parser
                if parsed.fragment not in target_parser.ids:
                    failures.append(f"{label}: missing fragment #{parsed.fragment} in {target.relative_to(ROOT)}")

    if failures:
        print("Site validation failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"Validated {len(documents)} HTML pages and all internal links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
