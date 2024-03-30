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
form = UserModel.as_form(request_data, obj=None)

print(form)
#> UserModel.as_form(name='John Doe', friends=[2, 3], active=False)
print(form.fields["name"].value)
#> John Doe
print(form.fields["name"].error)
#>
```


## Installation

  pip install fodantic

### Requirements

- Python 3.10+
- Pydantic 2.*
