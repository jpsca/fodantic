"""
Fodantic
Copyright (c) 2024 Juan-Pablo Scaletti
"""
import typing as t
from collections.abc import Iterable

from pydantic_core import PydanticUndefined


if t.TYPE_CHECKING:
    from pydantic.fields import FieldInfo
    from pydantic_core import ErrorDetails

    from .form import Form


class FormField:
    model_name: str
    is_required: bool
    is_multiple: bool
    value: str | list[str] | bool

    def __init__(self, *, name: str, info: "FieldInfo", form: "Form"):
        """
        A form field

        Attributes:
            model_name:
                The name used in the pydantic Model (different than the one in
                the HTML form if a prefix is used).
            name:
                The name, maybe with a prefix, used in the HTML form.
            value:
                The current (potentially invalid) field value.
            is_required:
                Whether the field is required or optional.
            is_multiple:
                Whether the field expects a list of values instead of just one.
            is_bool:
                Whether the field is of type boolean.

            annotation:
                The type annotation of the field.
            alias:
                The alias name of the field.
            alias_name:
                The alias, maybe with a prefix, that can be also used in the
                HTML form.
            alias_priority:
                The priority of the field's alias.
            default:
                The default value of the field.
            default_factory:
                The factory function used to construct the default for the field.
            description:
                The description of the field.
            examples:
                List of examples of the field.
            title:
                The title of the field.

        """
        self._form = form
        self.model_name = name
        self.is_required = info.is_required()

        annotation_origin = t.get_origin(info.annotation)
        self.is_multiple = annotation_origin in (list, tuple, Iterable)
        self.is_bool = info.annotation is bool or annotation_origin is bool

        self.annotation = info.annotation
        self.alias = info.alias
        self.alias_priority = info.alias_priority or 2
        self.default = info.default
        self.default_factory = info.default_factory
        self.description = info.description
        self.examples = info.examples
        self.title = info.title

        self.value = self.get_default()
        self.error: "ErrorDetails | None" = None

        _str = ", ".join(str(info).replace(" required", " is_required").split(" "))
        self._str = f"name='{self.name}', {_str}"

    def __repr__(self) -> str:
        return f"FormField({self._str})"

    @property
    def name(self) -> str:
        return f"{self._form.prefix}{self.model_name}"

    @property
    def alias_name(self) -> str:
        if self.alias:
            return f"{self._form.prefix}{self.alias}"
        return ""

    def set_value(self, value: t.Any):
        if self.is_bool:
            if value is None:
                self.value = False
            elif value == "":
                self.value = True
            else:
                self.value = bool(value)
        if value is None:
            return
        self.value = value

    def extract_value(self, reqdata: t.Any) -> t.Any:
        if self.is_bool and (self.name not in reqdata):
            return False

        value = reqdata.get(self.name)
        alias_value = reqdata.get(self.alias_name)
        if self.alias_priority > 1:
            value, alias_value = alias_value, value

        extracted = alias_value if value is None else value

        if self.is_bool:
            if extracted is None:
                return False
            if extracted == "":
                return True
            return bool(extracted)

        return extracted

    def get_default(self, **kw) -> t.Any:
        default = self.default_factory() if self.default_factory else self.default
        if default == PydanticUndefined:
            default = None
        if default is None:
            default = [] if self.is_multiple else ""
        return default
