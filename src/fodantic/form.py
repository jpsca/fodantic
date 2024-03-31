"""
Fodantic
Copyright (c) 2024 Juan-Pablo Scaletti
"""

import typing as t

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from .form_field import FormField
from .wrapper import DataWrapper


__all__ = ["formable", "Form"]


class Form:
    fields: "dict[str, FormField]"
    prefix: str = ""
    is_valid: bool = False
    is_empty: bool = True
    errors: list[ErrorDetails]

    obj: t.Any = None
    model: BaseModel | None = None

    def __init__(
        self,
        reqdata: t.Any = None,
        *,
        model_cls: t.Type[BaseModel],
        obj: t.Any = None,
        prefix: str = "",
        orm_cls: t.Any = None,
    ):
        """
        A form handler that integrates pydantic models for data validation and can
        interact with ORM models.

        ## Arguments:

        - reqdata:
            Optional request data used for form submission.
        - model_cls:
            The pydantic model class for data validation.
        - obj:
            Optional ORM model instance to fill the form and be updated when saving.
        - prefix:
            An optional prefix to prepend to field names (separated with a dot).
            Defaults to an empty string.
        - orm_cls:
            The ORM model class for database interaction. If `None`, the `Form.save()`
            returns a dict when the form is valid.

        ## Attributes:

        - model_cls (t.Type[pydantic.BaseModel]):
            The pydantic model class for data validation.
        - orm_cls (Any, optional):
            The ORM model class for database interaction. Defaults to None.

        - prefix (str):
            Optional prefix used in form field names. Defaults to an empty string.
        - fields (dict[str, FormField]):
            Dictionary mapping field names to FormField instances.
        - is_valid (bool):
            Indicates whether the form data passed validation. Defaults to True.
        - is_invalid (bool):
            The opposite to `is_valid`.
        - is_empty (bool):
            If the form was initialized with request or object data
        - errors (list[ErrorDetails]):
            List of validation errors encountered.
        - model (pydantic.BaseModel | None):
            The instantiated pydantic model after validation. Defaults to None.

        ## Example:

        ```python
        from fodantic import formable

        @formable
        class UserForm(pydantic.BaseModel):
            name: str
            age: int
            tags: list[str]


        empty_form = UserForm()
        valid_form = UserForm({"name": "joe", "age": 33})
        invalid_form = UserForm({"age": "nan"})

        print(empty_form.fields)
        '''
        {
           'name': FormField(name='name', annotation=str, is_required=True),
           'age': FormField(name='age', annotation=int, is_required=True),
           'tags': FormField(name='tags', annotation=list[str], is_required=True),
        }
        '''

        print(empty_form.fields["age"].value)
        #> ''

        print(valid_form.fields["age"].value)
        #> 33

        print(empty_form.save())
        #> ValueError

        print(valid_form.save())
        #> {'name': 'joe', 'age': 3, 'tags': []}

        print(invalid_form.save())
        #> ValueError

        ```

        """
        self.model_cls = model_cls
        self.orm_cls = orm_cls

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
                value = (
                    field.default_factory() if field.default_factory else field.default
                )
            data[model_name] = value

        for model_name, value in data.items():
            self.fields[model_name].value = value

        try:
            self.model = self.model_cls(**data)
            self.is_valid = True
        except ValidationError as exc:
            self.is_valid = False
            for error in exc.errors():
                loc = error.get("loc") or []
                if not loc:
                    self.errors.append(error)
                for name in loc:
                    field = self.fields.get(str(name))
                    if field:
                        field.error = error

    def __repr__(self) -> str:
        model_name = self.model_cls.__name__
        model_form = f"{model_name}.as_form"

        if self.is_empty:
            return f"{model_form}(<empty>)"

        if self.is_valid:
            return repr(self.model).replace(model_name, model_form)
        else:
            return f"{model_form}(<invalid>)"

    @property
    def is_invalid(self):
        return not self.is_valid

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


class FormableBaseModel(BaseModel):
    @classmethod
    def as_form(
        cls,
        reqdata: t.Any = None,
        *,
        obj: t.Any = None,
        prefix: str = "",
    ) -> "Form": ...


BM = t.Type[BaseModel]
FBM = t.Type[FormableBaseModel]


@t.overload
def formable(model_cls: BM) -> FBM: ...


@t.overload
def formable(*, orm: t.Any = None) -> t.Callable[[BM], FBM]: ...


def formable(
    model_cls: BM | None = None,
    *,
    orm: t.Any = None,
) -> FBM | t.Callable[[BM], FBM]:
    """
    Decorator to add a `as_form` class method to a Pydantic model.
    This decorator can be used with or without parenthesis.

    Arguments:

    - orm: Optional class of an ORM model

    """

    def decorator(model_cls: BM) -> FBM:
        """The actual decorator logic that adds the `as_form` method."""

        def as_form(
            cls,
            reqdata: t.Any = None,
            *,
            obj: t.Any = None,
            prefix: str = "",
        ) -> Form:
            return Form(reqdata, obj=obj, prefix=prefix, model_cls=cls, orm_cls=orm)

        setattr(model_cls, "as_form", classmethod(as_form))  # noqa
        model_cls = t.cast(FBM, model_cls)
        return model_cls

    return decorator if model_cls is None else decorator(model_cls)
