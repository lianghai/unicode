from pathlib import Path

from fontTools import unicodedata
from ruamel import yaml

directory = Path(__file__).parent
version = "14.0.0"

for property_name in "IndicPositionalCategory", "IndicSyllabicCategory":

    source = (directory / version / property_name).with_suffix(".txt")

    cps_to_value = dict[range, str]()
    for line in source.read_text().splitlines():

        if not (content := line.partition("#")[0].strip()):
            continue

        field_0, value = [i.strip() for i in content.split(";")]
        start, _, stop = field_0.partition("..")

        cps_to_value[range(int(start, 16), int(stop or start, 16) + 1)] = value

    script_to_value_to_cps = dict[str, dict[str, list[int]]]()
    for cp, value in sorted((i, v) for k, v in cps_to_value.items() for i in k):
        value_to_cps = script_to_value_to_cps.setdefault(
            unicodedata.script_name(unicodedata.script(chr(cp))), {}
        )
        value_to_cps.setdefault(value, list()).append(cp)

    # yaml.add_representer(
    #     int,
    #     lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:int", f"0x{data:04X}"),
    # )
    with source.with_suffix(".yaml").open("w") as f:
        yaml.dump(
            {
                k: {value: [{i: unicodedata.name(chr(i))} for i in cps] for value, cps in v.items()}
                for k, v in script_to_value_to_cps.items()
            },
            f,
            # sort_keys=False,
        )
