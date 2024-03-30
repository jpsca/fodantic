"""
Fodantic
Copyright (c) 2024 Juan-Pablo Scaletti
"""
import typing as t


if t.TYPE_CHECKING:
    from pydantic.fields import FieldInfo
    from pydantic_core import ErrorDetails

    from .form import Form


class FormField:
    def __init__(self, *, name: str, info: "FieldInfo", form: "Form"):
        """
        A form field

        ## Attributes:

        - model_name:
            The name used in the pydantic Model (different than the one in the HTML form if
            a prefix is used).
        - is_required:
            Whether the field is required or optional.
        - is_multiple:
            Whether the field expects a list of values instead of just one.
        - annotation:
            The type annotation of the field.
        - default:
            The default value of the field.
        - default_factory:
            The factory function used to construct the default for the field.
        - alias:
            The alias name of the field.
        - alias_priority:
            The priority of the field's alias.
        - validation_alias:
            The validation alias of the field.
        - serialization_alias:
            The serialization alias of the field.
        - title:
            The title of the field.
        - description:
            The description of the field.
        - examples:
            List of examples of the field.

        """
        self._form = form

        self.model_name = name
        self.is_required = info.is_required()
        self.annotation_origin = t.get_origin(info.annotation)
        self.is_multiple = self.annotation_origin in (list, tuple)

        self.annotation = info.annotation
        self.default = info.default
        self.default_factory = info.default_factory
        self.alias = info.alias
        self.alias_priority = info.alias_priority or 2
        self.validation_alias = info.validation_alias
        self.serialization_alias = info.serialization_alias
        self.title = info.title
        self.description = info.description
        self.examples = info.examples

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

    @property
    def value(self) -> t.Any:
        model_value = self._form._get_model_value(self.model_name)
        if model_value is None:
            return [] if self.is_multiple else ""
        return model_value

    def extract_value(self, reqdata: t.Any) -> str | bool | None | list[str]:
        return (
            self._extract_many(reqdata)
            if self.is_multiple
            else self._extract_one(reqdata)
        )

    def get_default(self) -> t.Any:
        if self.default_factory:
            return self.default_factory()
        return self.default

    # Private

    def _extract_one(self, reqdata: t.Any) -> str | bool | None:
        value = reqdata.get(self.name)
        alias_value = reqdata.get(self.alias_name)
        if self.alias_priority > 1:
            value, alias_value = alias_value, value

        extracted = alias_value if value is None else value

        if self.annotation == bool or self.annotation_origin == bool:
            if extracted is None:
                return False
            if extracted == "":
                return True
            return bool(extracted)

        return extracted

    def _extract_many(self, reqdata: t.Any) -> list[str]:
        value = reqdata.getall(self.name)
        alias_value = reqdata.getall(self.alias_name)
        if self.alias_priority > 1:
            value, alias_value = alias_value, value

        return alias_value if value == [] else value
