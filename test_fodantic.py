import pydantic
import pytest

from fodantic import BaseForm


DEFAULT_AV = 33


class UserModel(pydantic.BaseModel):
    name: str
    age: int = DEFAULT_AV
    tags: list[str]


class UserForm(BaseForm):
    model_cls = UserModel


def test_empty_form():
    form = UserForm()

    assert not form.is_valid
    assert not form.errors
    assert list(form.fields.keys()) == ["name", "age", "tags"]

    assert form.fields["name"].name == "name"
    assert form.fields["name"].value == ""
    assert form.fields["name"].is_required is True
    assert form.fields["name"].error is None

    assert form.fields["age"].name == "age"
    assert form.fields["age"].value == ""
    assert form.fields["age"].is_required is False
    assert form.fields["age"].error is None

    assert form.fields["tags"].name == "tags"
    assert form.fields["tags"].value == []

    assert form.fields["tags"].is_required is True
    assert form.fields["tags"].error is None

    with pytest.raises(ValueError):
        form.save()

    assert repr(form) == "UserForm(UserModel<empty>)"


def test_invalid_form():
    form = UserForm({"age": "nan"})

    assert not form.is_valid
    assert not form.errors

    assert form.fields["name"].error
    assert form.fields["name"].error["type"] == "string_type"

    assert form.fields["age"].error
    assert form.fields["age"].error["type"] == "int_parsing"

    assert form.fields["tags"].error is None

    with pytest.raises(ValueError):
        form.save()

    assert repr(form) == "UserForm(UserModel<invalid>)"


def test_valid_form():
    form = UserForm(
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

    assert form.fields["age"].value == 20
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["a"]
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": 20, "tags": ["a"]}
    assert repr(form) == "UserForm(UserModel(name='joe', age=20, tags=['a']))"


def test_missing_list_is_empty_list():
    form = UserForm(
        {
            "name": "joe",
        }
    )

    assert form.is_valid
    assert not form.errors

    assert form.fields["tags"].value == []
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": DEFAULT_AV, "tags": []}
    assert repr(form) == f"UserForm(UserModel(name='joe', age={DEFAULT_AV}, tags=[]))"


def test_default_value():
    form = UserForm({"name": "joe", "tags": "a"})

    assert form.is_valid
    assert not form.errors
    assert form.fields["age"].value == DEFAULT_AV


def test_prefix():
    form = UserForm({"u1.name": "joe", "u1.age": "20", "u1.tags": "a"}, prefix="u1")

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "joe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 20
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["a"]
    assert form.fields["tags"].error is None

    assert form.save() == {"name": "joe", "age": 20, "tags": ["a"]}
    assert repr(form) == "UserForm(UserModel(name='joe', age=20, tags=['a']))"


def test_prefix_with_default():
    form = UserForm({"u1.name": "joe", "u1.tags": "a"}, prefix="u1")

    assert form.is_valid
    assert not form.errors
    assert DEFAULT_AV == form.fields["age"].value


def test_obj_data():
    class User:
        name = "jon doe"
        age = 25
        tags = ["meh", "whatever"]

    user = User()
    form = UserForm(obj=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "jon doe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["meh", "whatever"]
    assert form.fields["tags"].error is None

    assert form.save() == user


def test_obj_updated():
    class User:
        name = "original"
        age = 25

    reqdata = {"name": "updated"}
    user = User()

    form = UserForm(reqdata, obj=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "updated"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    user = form.save()
    assert "updated" == user.name


def test_dict_obj_data():
    user = {
        "name": "jon doe",
        "age": 25,
        "tags": ["meh", "whatever"],
    }

    form = UserForm(obj=user)

    assert form.is_valid
    assert not form.errors

    assert form.fields["name"].value == "jon doe"
    assert form.fields["name"].error is None

    assert form.fields["age"].value == 25
    assert form.fields["age"].error is None

    assert form.fields["tags"].value == ["meh", "whatever"]
    assert form.fields["tags"].error is None

    assert user == form.save()


def test_dict_obj_updated():
    user = {"name": "original", "age": 25}
    reqdata = {"name": "updated"}

    form = UserForm(reqdata, obj=user)

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

    class Model(pydantic.BaseModel):
        name: str

    class Form(BaseForm):
        model_cls = Model
        orm_cls = User

    form = Form({"name": "Bobby Tables"})
    user = form.save()

    assert isinstance(user, User)
    assert user.name == "Bobby Tables"


def test_checkbox():
    class MyModel(pydantic.BaseModel):
        checkbox: bool

    class MyForm(BaseForm):
        model_cls = MyModel

    form = MyForm({})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()

    form = MyForm({"checkbox": ""})
    assert form.fields["checkbox"].value is True
    assert {"checkbox": True} == form.save()

    form = MyForm({"checkbox": "whatever"})
    assert form.fields["checkbox"].value is True
    assert {"checkbox": True} == form.save()


def test_checkbox_empty_override_default():
    class MyModel(pydantic.BaseModel):
        checkbox: bool = True

    class MyForm(BaseForm):
        model_cls = MyModel

    form = MyForm({})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()

    form = MyForm({}, obj={"checkbox": True})
    assert form.fields["checkbox"].value is False
    assert {"checkbox": False} == form.save()
