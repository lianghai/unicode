from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import html5lib
from lxml.etree import _Element as Element

TREE_TYPE = "lxml"

repo = Path(__file__).parent


@dataclass
class Source:

    directory: Path
    path_to_html: dict[Path, Element]

    def __init__(self, directory: Path):
        self.directory = directory
        self.path_to_html = {
            i.relative_to(self.directory): html5lib.parse(
                i.read_bytes(), treebuilder=TREE_TYPE, namespaceHTMLElements=False
            )
            for i in self.directory.rglob("*.html")
        }

    def transform_element(self, element: Element, /, parent: Element):

        print(element.tag)
        match element.tag:
            case "char":
                parent.replace(element, element.makeelement("x", {}, None))
            case _:
                if (attribute := "placeholder") in element.keys() and element.text:
                    transformed = element.text.replace("X.X", "1.1").replace("X-X", "1-9")  # TODO
                    element.text = transformed  # type: ignore
                    del element.attrib[attribute]

    def build(self, directory: Path):

        walker = html5lib.getTreeWalker(TREE_TYPE)
        serializer = html5lib.serializer.HTMLSerializer()

        for relative_path, source in self.path_to_html.items():

            if relative_path.stem not in {
                "Unicode Design Principles",
                # "Compatibility Characters",
                # "Han",
            }:
                continue

            transformed = deepcopy(source)
            for parent in transformed.iter():  # type: ignore
                for element in parent:
                    self.transform_element(element, parent)

            serialized = "".join(serializer.serialize(walker(transformed)) or [])

            path = directory / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(serialized)


if __name__ == "__main__":

    source = Source(repo / "source")
    source.build(repo / "distribution")
