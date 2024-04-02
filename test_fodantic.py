import pydantic
import pytest

from fodantic import formable


AGE_TEST_VALUE = 33


@formable
class UserModel(pydantic.BaseModel):
    name: str
    age: int = AGE_TEST_VALUE
    tags: list[str] = pydantic.Field(default_factory=list)


def test_empty_form():
    form = UserModel.as_form()

    assert not form.is_valid
    assert not form.errors
    assert list(form.fields.keys()) == ["name", "age", "tags"]

    assert form.fields["name"].name == "name"
    assert form.fields["name"].value == ""
    assert form.fields["name"].is_required is True
    assert form.fields["name"].error is None

    assert form.fields["age"].name == "age"
    assert form.fields["age"].value == AGE_TEST_VALUE
    assert form.fields["age"].is_required is False
    assert form.fields["age"].error is None

    assert form.fields["tags"].name == "tags"
    assert form.fields["tags"].value == []
    assert form.fields["tags"].is_required is False
    assert form.fields["tags"].error is None

    with pytest.raises(ValueError):
        form.save()

    assert repr(form) == "UserModel.as_form(<empty>)"


def test_invalid_form():
    form = UserModel.as_form({"age": "nan"})

    assert not form.is_valid
    assert not form.errors

    assert form.fields["name"].error
    assert form.fields["name"].error["type"] == "missing"

    assert form.fields["age"].error
    assert form.fields["age"].error["type"] == "int_parsing"
    assert form.fields["age"].value == "nan"

    assert form.fields["tags"].error is None

    with pytest.raises(ValueError):
        form.save()

    assert repr(form) == "UserModel.as_form(<invalid>)"


def test_valid_form():
    form = UserModel.as_form(
        {
            "name": "joe",
            "age": "20",
            "tags": "a",
        }
    )

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "joe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == "20"
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["a"]
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": 20, "tags": ["a"]}
    assert repr(form) == "UserModel.as_form(name='joe', age=20, tags=['a'])"


def test_missing_list_is_empty_list():
    form = UserModel.as_form({"name": "joe"})

    assert form.is_valid
    assert not form.errors

    assert form.fields["tags"].value == []
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": AGE_TEST_VALUE, "tags": []}
    assert repr(form) == f"UserModel.as_form(name='joe', age={AGE_TEST_VALUE}, tags=[])"


def test_default_value():
    form = UserModel.as_form({"name": "joe", "tags": "a"})

    assert form.is_valid
    assert not form.errors
    assert form.fields["age"].value == AGE_TEST_VALUE


def test_prefix():
    form = UserModel.as_form(
        {"u1.name": "joe", "u1.age": "20", "u1.tags": "a"},
        prefix="u1",
    )

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "joe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == "20"
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["a"]
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": 20, "tags": ["a"]}
    assert repr(form) == "UserModel.as_form(name='joe', age=20, tags=['a'])"


def test_prefix_with_default():
    form = UserModel.as_form({"u1.name": "joe", "u1.tags": "a"}, prefix="u1")

    assert form.is_valid
    assert not form.errors
    assert AGE_TEST_VALUE == form.fields["age"].value


def test_object_data():
    class User:
        name = "jon doe"
        age = 25
        tags = ["meh", "whatever"]

    user = User()
    form = UserModel.as_form({}, object=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "jon doe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["meh", "whatever"]
    assert form.fields["tags"].error is None

    assert form.save() == user


def test_only_validate_with_reqdata():
    class User:
        name = ""
        age = 55
        tags = []

    user = User()
    form = UserModel.as_form(object=user)

    assert not form.is_valid
    assert not form.errors

    assert form.fields["name"].value == ""
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 55
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == []
    assert form.fields["tags"].error is None

    with pytest.raises(ValueError):
        form.save()


def test_object_updated():
    class User:
        name = "original"
        age = 25

    reqdata = {"name": "updated"}
    user = User()

    form = UserModel.as_form(reqdata, object=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "updated"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    user = form.save()
    assert "updated" == user.name


def test_dict_object_data():
    user = {
        "name": "jon doe",
        "age": 25,
        "tags": ["meh", "whatever"],
    }

    form = UserModel.as_form({}, object=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "jon doe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["meh", "whatever"]
    assert form.fields["tags"].error is None

    assert user == form.save()


def test_dict_object_updated():
    user = {"name": "original", "age": 25}
    reqdata = {"name": "updated"}

    form = UserModel.as_form(reqdata, object=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "updated"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    assert "updated" == form.save()["name"]


def test_orm():
    class User:
        def __init__(self, name: str):
            self.name = name

    @formable(orm=User)
    class MyModel(pydantic.BaseModel):
        name: str

    form = MyModel.as_form({"name": "Bobby Tables"})
    user = form.save()

    assert isinstance(user, User)
    assert user.name == "Bobby Tables"


def test_checkbox():
    @formable
    class MyModel(pydantic.BaseModel):
        checkbox: bool

    form = MyModel.as_form({})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()

    form = MyModel.as_form({"checkbox": ""})
    assert form.fields["checkbox"].value is True
    assert {"checkbox": True} == form.save()

    form = MyModel.as_form({"checkbox": "whatever"})
    assert form.fields["checkbox"].value is True
    assert {"checkbox": True} == form.save()


def test_checkbox_empty_override_default():
    @formable
    class MyModel(pydantic.BaseModel):
        checkbox: bool = True

    form = MyModel.as_form({})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()

    form = MyModel.as_form({}, object={"checkbox": True})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()
