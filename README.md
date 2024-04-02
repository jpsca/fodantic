# Fodantic

<img align="right" height="200" src="https://github.com/jpsca/fodantic/blob/1620ae934be26ce1ef2a57aeebfb820e52461305/fodantic.png">

Pydantic-based HTTP forms.

[Pydantic](https://docs.pydantic.dev) is the most widely used data validation library for Python, but it's hard to use it with regular HTTP forms... until now.

**Fodantic** allow you to quickly wrap your Pydantic models and use them as forms: with support for multiple values, checkboxes, error handling, and integration with your favorite ORM.


## A simple example

```py
from fodantic import formable
from pydantic import BaseModel

@formable
class UserModel(BaseModel):
    name: str
    friends: list[int]
    active: bool = True

request_data = Multidict(('name', 'John Doe'), ('friends', '2'), ('friends', '3')}

# The magic
form = UserModel.as_form(request_data, object=None)

print(form)
#> UserModel.as_form(name='John Doe', friends=[2, 3], active=False)
print(form.fields["name"].value)
#> John Doe
print(form.fields["name"].error)
#> None
print(form.save())  # Can also update the `object` passed as an argument
#> {'name': 'John Doe', 'friends': [2, 3], 'active': False}

```

## Installation

  pip install fodantic

### Requirements

- Python 3.10+
- Pydantic 2.*


## Documentation

### List fields

Fields defined as of type list, tuple, or a derivated type, will be marked as expecting multiple values. A `<select multiple>` and a group of checkboxes charing the same name (but different values) are the most common examples of how these fields look on a form. Fodantic will use the `getall`(*) method on the request data to get a list of all the values under the same name.

(*) Also called `getlist` in many web frameworks.


### Booleans fields

Boolean fields are treated special because of how browsers handle checkboxes:

- If not checked: the browser doesn't send the field at all, so the missing field will be interpreted as `False`.
- If checked: It sends the "value" attribute, but this is optional, so it could send an empty string instead. So any value other than None will be interpreted as `True`.

