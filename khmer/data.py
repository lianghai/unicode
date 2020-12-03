from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Optional, Union

import yaml

project_dir = Path(__file__).parent
data_dir = project_dir / "data"


@dataclass
class Category:

    _members: Union[list[str], dict[str, Category]]

    def __getattr__(self, name) -> Category:
        if isinstance(self._members, dict):
            return self._members[name]
        else:
            raise AttributeError

    def members(self) -> list[str]:
        if isinstance(self._members, list):
            return self._members
        else:
            return list(chain.from_iterable(sc.members() for sc in self._members.values()))

    @classmethod
    def load(cls, data) -> Category:
        _members = []
        if isinstance(data, list):
            _members = [validate_case(i) for i in data]
        elif isinstance(data, dict):
            _members = {k: Category.load(v) for k, v in data.items()}
        return cls(_members)


def parse_yaml(filename: str):
    path = (data_dir / filename).with_suffix(".yaml")
    return yaml.safe_load(path.read_text())

def validate_case(case: str, /) -> str:
    if case.startswith("."):
        return case.removeprefix(".")
    else:
        raise Exception("Not a valid case expression.")


CATEGORIZATION = Category.load(parse_yaml("categorization"))
