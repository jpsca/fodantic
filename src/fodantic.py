import typing as t

import pydantic
from pydantic.fields import FieldInfo
from pydantic_core import ErrorDetails


__all__ = ["BaseForm",]


class BaseForm:
    model_cls: t.Type[pydantic.BaseModel]
    orm_cls: t.Any = None

    fields: "dict[str, FormField]"
    prefix: str = ""
    is_valid: bool = False
    is_empty: bool = True
    errors: list[ErrorDetails]

    model: pydantic.BaseModel | None = None
    obj: t.Any = None

    def __init__(
        self,
        reqdata: t.Any = None,
        *,
        obj: t.Any = None,
        prefix: str = "",
    ):
        """
        A form handler that integrates pydantic models for data validation and can interact with ORM models.

        This class is designed to be subclassed and should not be instantiated directly.

        ## Arguments:

        - reqdata:
            Optional request data used for form submission.
        - obj:
            Optional ORM model instance to fill the form and be updated when saving.
        - prefix:
            An optional prefix to prepend to field names (separated with a dot). Defaults to an empty string

        ## Attributes:

        - model_cls (Type[pydantic.BaseModel]):
            The pydantic model class for data validation.
        - orm_cls (Any, optional):
            The ORM model class for database interaction. Defaults to None.

        - prefix (str):
            Optional prefix used in form field names. Defaults to an empty string.
        - fields (dict[str, FormField]):
            Dictionary mapping field names to FormField instances.
        - is_valid (bool):
            Indicates whether the form data passed validation. Defaults to True.
        - is_empty (bool):
            If the form was initialized with request or object data
        - errors (list[ErrorDetails]):
            List of validation errors encountered.
        - model (pydantic.BaseModel | None):
            The instantiated pydantic model after validation. Defaults to None.

        ## Example:

        ```python
        class UserModel(pydantic.BaseModel):
            name: str
            age: int
            tags: list[str]


        class UserForm(BaseForm):
            model_cls = UserModel
            orm_cls = None


        empty_form = UserForm()
        valid_form = UserForm({"name": "joe", "age": 33})
        invalid_form = UserForm({"age": "nan"})

        empty_form.fields
        # {
        #     'name': FormField(name='name', annotation=str, is_required=True),
        #     'age': FormField(name='age', annotation=int, is_required=True),
        #     'tags': FormField(name='tags', annotation=list[str], is_required=True),
        # }

        empty_form.fields["age"].value
        # ''

        valid_form.fields["age"].value
        # 33

        empty_form.save()
        # ValueError

        valid_form.save()
        # {'name': 'joe', 'age': 3, 'tags': []}

        invalid_form.save()
        # ValueError


        ```

        """
        if type(self) is BaseForm:
            raise TypeError(
                "BaseForm is an abstract base class and cannot be instantiated directly."
            )

        if not self.model_cls:
            raise ValueError(
                "Please add a `model_cls` attribute with the pydantic model."
            )

        self.prefix = f"{prefix}." if prefix else ""
        self.errors = []
        self.fields = {
            name: FormField(name=name, info=info, form=self)
            for name, info in self.model_cls.model_fields.items()
        }

        if reqdata is None and obj is None:
            return

        self.is_empty = False
        reqdata = DataWrapper(reqdata) if reqdata is not None else None
        if obj is not None:
            self.obj = obj = DataWrapper(obj)

        data: dict[str, t.Any] = {}

        for field in self.fields.values():
            model_name = field.model_name
            value: t.Any = None
            if reqdata:
                value = field.extract_value(reqdata)
            if value is None and obj:
                value = obj.get(model_name)
            if value is None:
                value = field.get_default()
            data[model_name] = value

        try:
            self.model = self.model_cls(**data)
            self.is_valid = True
        except pydantic.ValidationError as exc:
            self.is_valid = False
            for error in exc.errors():
                loc = error.get("loc")
                if not loc:
                    self.errors.append(error)
                for name in loc:
                    field = self.fields.get(str(name))
                    if field:
                        field.error = error

    def __repr__(self) -> str:
        if self.is_empty:
            return f"{self.__class__.__name__}({self.model_cls.__name__}<empty>)"

        if self.is_valid:
            return f"{self.__class__.__name__}({repr(self.model)})"
        else:
            return f"{self.__class__.__name__}({self.model_cls.__name__}<invalid>)"

    def save(self) -> t.Any:
        if not self.model or not self.is_valid:
            raise ValueError("Form is not valid")

        data = self.model.model_dump()

        if self.obj is not None:
            return self.obj.update(data)

        if self.orm_cls:
            return self.orm_cls(**data)

        return data

    # Private

    def _get_model_value(self, name: str) -> t.Any:
        if not self.model:
            return None
        return getattr(self.model, name, None)


class DataWrapper:
    def __init__(self, source: t.Any):
        """
        A utility class for wrapping request data and providing uniform access methods.

        This class abstracts away the differences between various request data sources, providing
        a consistent interface for accessing single values or lists of values.

        Arguments:

        - source (Any): The underlying data source.

        """
        self.source = source
        self.get = self._get_get_method()
        self.getall = self._get_getall_method()

    def update(self, data: dict[str, t.Any]) -> t.Any:
        if hasattr(self.source, "update"):
            self.source.update(data)
        else:
            for key, value in data.items():
                setattr(self.source, key, value)

        return self.source

    def _get_get_method(self) -> t.Callable[[str], t.Any]:
        if self.source and hasattr(self.source, "get"):
            return self.source.get

        def get_fallback(name: str) -> t.Any:
            if not self.source:
                return None
            return getattr(self.source, name)

        return get_fallback

    def _get_getall_method(self) -> t.Callable[[str], list[t.Any]]:
        if self.source:
            # WebOb, Bottle, and Proper uses `getall`
            if hasattr(self.source, "getall"):
                return self.source.getall
            # Django, Flask (Werkzeug), cgi.FieldStorage, etc. uses `getlist`
            if hasattr(self.source, "getlist"):
                return self.source.getlist

        def getall_fallback(name: str) -> list[t.Any]:
            if not self.source:
                return []
            values = self.get(name)
            if values is None:
                return []
            return [values]

        return getall_fallback


class FormField:
    def __init__(self, *, name: str, info: FieldInfo, form: BaseForm):
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

        self.error: ErrorDetails | None = None

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
