import pytest

from fodantic.parser import parse, parse_key


@pytest.mark.parametrize(
    "input_key, expected",
    [
        ("simple", ["simple"]),
        ("under_score", ["under_score"]),
        ("π_unicode", ["π_unicode"]),
        ("pre.fix", ["pre.fix"]),
        ("a[b][c]", ["a", "b", "c"]),
        ("arr[0]", ["arr", 0]),
        ("arr[10][x]", ["arr", 10, "x"]),
        ("list[]", ["list", None]),
        ("nested[list][]", ["nested", "list", None]),
        ("mixed[0][]", ["mixed", 0, None]),
    ],
)
def test_parse_key_various(input_key, expected):
    assert parse_key(input_key) == expected


def test_parse_key_invalid():
    assert [] == parse_key("")
    assert [] == parse_key("[no_root]")


def test_parse_single_simple_key():
    flat = {"foo": ["bar"]}
    expected = {"foo": "bar"}
    assert parse(flat) == expected


def test_parse_basic_nested():
    flat = {"a[b][c]": [1]}
    expected = {"a": {"b": {"c": 1}}}
    assert parse(flat) == expected


def test_parse_indexed_list():
    flat = {
        "arr[0]": ["x"],
        "arr[1]": ["y"],
        "arr[5]": ["z"],
    }
    expected = {"arr": ["x", "y", None, None, None, "z"]}
    assert parse(flat) == expected


def test_parse_list_append_simple():
    flat = {"items[]": ["p", "q", "r"]}
    expected = {"items": ["p", "q", "r"]}
    assert parse(flat) == expected



def test_parse_mixed_dict_and_list():
    flat = {
        "user[name]": ["Alice"],
        "user[roles][]": ["admin", "user"],
        "user[scores][0]": [10],
        "user[scores][2]": [30],
        "user[scores][1]": [20],
    }
    expected = {
        "user": {
            "name": "Alice",
            "roles": ["admin", "user"],
            "scores": [10, 20, 30],
        }
    }
    assert parse(flat) == expected


def test_parse_multiple_independent_branches():
    flat = {
        "a[x]": [100],
        "b[y]": [200],
        "c[]": ["foo", "bar"],
    }
    expected = {
        "a": {"x": 100},
        "b": {"y": 200},
        "c": ["foo", "bar"],
    }
    assert parse(flat) == expected


def test_parse_complex_structure():
    flat = {
        "person[name]": ["Bob"],
        "person[age]": [30],
        "person[tags][]": ["x", "y"],
        "person[address][city]": ["Lima"],
        "person[address][zip]": ["05001"],
        "headers[0][name]": ["h1"],
        "headers[0][value]": ["v1"],
        "headers[2][name]": ["h3"],  # index 2 skips index 1
        "headers[2][value]": ["v3"],
        "headers[1][name]": ["h2"],
        "headers[1][value]": ["v2"],
    }
    expected = {
        "person": {
            "name": "Bob",
            "age": 30,
            "tags": ["x", "y"],
            "address": {"city": "Lima", "zip": "05001"},
        },
        "headers": [
            {"name": "h1", "value": "v1"},
            {"name": "h2", "value": "v2"},
            {"name": "h3", "value": "v3"},
        ],
    }
    assert parse(flat) == expected
