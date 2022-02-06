from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import html5lib
import unicodedata2
from lxml.etree import _Element as Element

TREE_TYPE = "lxml"

parser = html5lib.HTMLParser(
    tree=html5lib.treebuilders.getTreeBuilder(TREE_TYPE),
    namespaceHTMLElements=False,
)
walker = html5lib.getTreeWalker(TREE_TYPE)
serializer = html5lib.serializer.HTMLSerializer()

repo = Path(__file__).parent


@dataclass
class Builder:

    path_to_html: dict[Path, Element]

    @classmethod
    def from_source_dir(cls, directory: Path, /) -> Builder:
        return cls(
            path_to_html={
                i.relative_to(directory): parser.parse(i.read_bytes())
                for i in directory.rglob("*.html")
            }
        )

    def build(self, directory: Path):

        for relative_path, source in self.path_to_html.items():

            transformed = deepcopy(source)

            for element in transformed.iter(tag=None):
                self.transform_element(element)

            serialized = "".join(serializer.serialize(walker(transformed)) or [])

            path = directory / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(serialized)

    def transform_element(self, element: Element, /):

        match element.tag:

            case "char":
                self.transform_char(element)

            case ("h1" | "figcaption" | "a") as tag if (mode := "numbering") in element.keys():

                self.expand_placeholder_in_element(element, mode)

                if tag == "a":

                    wrap = element.makeelement("cite", {}, None)
                    wrap.tail, element.tail = element.tail, None  # type: ignore

                    element.getparent().replace(element, wrap)
                    wrap.append(element)

    PLACEHOLDER_MODE = Literal["numbering"]

    def expand_placeholder_in_element(self, element: Element, /, mode: PLACEHOLDER_MODE = None):

        # TODO

        text: str = element.text

        if "X.X" in text:
            text = text.replace("X.X", "1.1")
        elif "X-X" in text:
            text = text.replace("X-X", "1-1")

        element.text = text  # type: ignore
        del element.attrib[mode]

    def transform_char(self, element: Element, /):

        char_placeholder_pattern = re.compile(
            r"""
                (
                    (?P<u_plus> U\+ )?  # optional U+ prefix
                    (
                        (?P<code_point_placeholder> X{4} )  # XXXX as code point placeholder
                        | (?P<code_point> 1?[0-9A-F]?[0-9A-F]{4} )  # or actual code point
                    )
                )?
                (
                    \s
                    (?P<glyph_placeholder> \[X\] )  # [X] as glyph placeholder
                )?
                (
                    \s
                    (?P<name> [A-Z0-9 -]+ )  # actual name
                )?
            """,
            flags=re.VERBOSE,
        )

        transformed: Element = element.makeelement("span", {"class": "character"}, None)
        transformed.tail = element.tail  # type: ignore

        text: str = element.text
        element.getparent().replace(element, transformed)

        if match := char_placeholder_pattern.fullmatch(text):

            cps = set[int]()
            if name := match.group("name"):
                cps.add(ord(unicodedata2.lookup(name)))
            if cp_notation := match.group("code_point"):
                cps.add(int(cp_notation, 16))
            if len(cps) != 1:
                raise KeyError(text)
            (cp,) = cps

            if cp_notation or match.group("code_point_placeholder"):
                child = transformed.makeelement("span", {"class": "code-point"}, None)
                child.text = (match.group("u_plus") or "") + f"{cp:04X}"
                transformed.append(child)
            if match.group("glyph_placeholder"):
                if len(transformed):
                    transformed[-1].tail = " "
                child = transformed.makeelement("span", {"class": "glyph"}, None)
                child.text = chr(cp)
                transformed.append(child)
            if name:
                if len(transformed):
                    transformed[-1].tail = " "
                child = transformed.makeelement(
                    "span",
                    {"class": "name", "style": "font-variant: all-small-caps;"},
                    None,
                )
                child.text = name
                transformed.append(child)


if __name__ == "__main__":
    builder = Builder.from_source_dir(repo / "source")
    builder.build(repo / "distribution")
