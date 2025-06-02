import re
import typing as t


# Regex pattern for valid Python variable names with Unicode support
# (but NOT supplementary planes, like emojis).
re_valid_name = r"[_a-zA-Z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF][_a-zA-Z0-9\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF\.]*"
re_valid_key = rf"{re_valid_name}|\[{re_valid_name}\]|\[[0-9]+\]|\[\]"
rx_valid_key = re.compile(re_valid_key)


def parse_key(key: str) -> list[str | int | None]:
    key = key.strip()
    if not key or key.startswith("["):
        return []

    parts = rx_valid_key.findall(key)
    print("PARTS", parts)
    parsed = []
    for part in parts:
        if part.startswith("[") and part.endswith("]"):
            inner = part[1:-1].strip()
            if not inner:  # empty brackets
                parsed.append(None)
            elif inner.isdigit():
                parsed.append(int(inner))
            else:
                parsed.append(inner)
        else:
            parsed.append(part)
    return parsed


def insert(parsed_key: list[str | int | None], value: t.Any, target: dict[str, t.Any]) -> None:
    last_index = len(parsed_key) - 1
    ref: dict[str, t.Any] | list[t.Any] = target

    for i, part in enumerate(parsed_key):
        is_last = i == last_index
        next_part = parsed_key[i + 1] if not is_last else None

        if part is None:  # append a list element
            assert isinstance(ref, list)
            if is_last:
                ref.append(value)
            else:
                new_elem = {} if isinstance(next_part, str) else []
                ref.append(new_elem)
                ref = new_elem

        elif isinstance(part, int):  # int index of list
            assert isinstance(ref, list)
            while len(ref) <= part:
                ref.append(None)

            if is_last:
                ref[part] = value
            else:
                if ref[part] is None:
                    ref[part] = {} if isinstance(next_part, str) else []
                ref = ref[part]

        else:  # dict key
            if is_last:
                assert isinstance(ref, dict)
                ref[part] = value
            else:
                if part not in ref or not isinstance(ref[part], (dict, list)):
                    ref[part] = {} if isinstance(next_part, str) else []
                ref = ref[part]


def parse(reqdata: dict[str, t.Any]) -> dict[str, t.Any]:
    """parse a flat dict-like object into a nested structure based on keys."""
    if not reqdata:
        return {}

    result = {}
    for key, values in dict.items(reqdata):
        if not isinstance(values, list) or not values:
            values = [values]
        parsed_key = parse_key(key)
        for value in values:
          insert(parsed_key, value, result)

    return result

