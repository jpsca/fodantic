# Fodantic

<img align="right" height="200" src="fodantic.png">

Pydantic-based HTTP forms.

Pydantic is the most widely used data validation library for Python, but it's hard to use it with regular HTTP forms./. until now.

**Fodantic** allow you to quickly wrap your Pydantic models and use them as forms: with support for multiple values, checkboxes, error handling, and integration with your favorite ORM.


## A simple example

```py
from fodantic import BaseForm
from pydantic import BaseModel

class User(BaseModel):
    name: str
    friends: list[int]
    active: bool = True

class UserForm(BaseForm):
    model_cls = User

request_data = Multidict(('name', 'John Doe'), ('friends', '2'), ('friends', '3')}
form = UserForm(request_data, obj=None)

print(form)
#> UserForm(User(name='John Doe', friends=[2, 3], active=False))
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