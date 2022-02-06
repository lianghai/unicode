from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import html5lib
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
class Source:

    directory: Path
    path_to_html: dict[Path, Element]

    def __init__(self, directory: Path):
        self.directory = directory
        self.path_to_html = {
            i.relative_to(self.directory): parser.parse(i.read_bytes())
            for i in self.directory.rglob("*.html")
        }

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

                transformed = element.makeelement("span", {"class": "char"}, None)
                transformed.text, transformed.tail = element.text, element.tail

                element.getparent().replace(element, transformed)

            case "h1" | "figcaption" if (mode := "numbering") in element.keys():

                self.expand_placeholder_text_in_element(element, mode)

            case "a" if (mode := "referencing") in element.keys():

                self.expand_placeholder_text_in_element(element, mode)

                wrap = element.makeelement("cite", {}, None)
                wrap.tail, element.tail = element.tail, None  # type: ignore

                element.getparent().replace(element, wrap)
                wrap.append(element)

    PLACEHOLDER_MODE = Literal["numbering", "referencing"]

    def expand_placeholder_text_in_element(
        self, element: Element, /, mode: PLACEHOLDER_MODE = None
    ):

        text: str = element.text

        if "X.X" in text:
            text = text.replace("X.X", "1.1")  # TODO
        elif "X-X" in text:
            text = text.replace("X-X", "1-9")  # TODO

        element.text = text  # type: ignore
        del element.attrib[mode]


if __name__ == "__main__":
    Source(repo / "source").build(repo / "distribution")
