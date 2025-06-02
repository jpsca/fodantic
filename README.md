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

# This is just an example. Here you would use the
# request POST data of your web framework instead.
# For example, for Flask: `request_data = request.form`
from multidict import MultiDict
request_data = MultiDict([
  ("name", "John Doe"),
  ("friends", "2"),
  ("friends", "3"),
])

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

- Python > 3.10
- Pydantic 2.*

## Form Fields Parsing with Nested Notation

Fodantic supports parsing nested form fields using bracket notation ([]), similar to how Ruby on Rails and PHP handle form data. This allows you to easily create complex nested data structures from flat form submissions.

### Nested Object Notation

You can use brackets to define nested objects in your form fields:

```html
<input name="user[name]" value="Alice">
<input name="user[email]" value="alice@example.com">
<input name="user[address][city]" value="New York">
<input name="user[address][zip]" value="10001">
```

This will be parsed into a nested structure:

```python
{
    "user": {
        "name": "Alice",
        "email": "alice@example.com",
        "address": {
            "city": "New York",
            "zip": "10001"
        }
    }
}
```

### Array Notation

You can create arrays using numeric indexes or empty brackets:

#### Indexed Arrays

```html
<input name="contacts[0][name]" value="John">
<input name="contacts[0][phone]" value="555-1234">
<input name="contacts[1][name]" value="Jane">
<input name="contacts[1][phone]" value="555-5678">
```

#### Array Append (Empty Brackets)

```html
<input name="tags[]" value="important">
<input name="tags[]" value="urgent">
<input name="tags[]" value="follow-up">
```

### Mixed Structures

You can combine these notations to create complex data structures:

```html
<input name="user[name]" value="Bob">
<input name="user[skills][]" value="Python">
<input name="user[skills][]" value="JavaScript">
<input name="user[projects][0][name]" value="Project A">
<input name="user[projects][0][status]" value="active">
<input name="user[projects][1][name]" value="Project B">
<input name="user[projects][1][status]" value="pending">
```

This will be parsed into:

```python
{
    "user": {
        "name": "Bob",
        "skills": ["Python", "JavaScript"],
        "projects": [
            {"name": "Project A", "status": "active"},
            {"name": "Project B", "status": "pending"}
        ]
    }
}
```

### Usage with Pydantic Models

This nested notation works seamlessly with Pydantic models, allowing you to map complex form structures to nested models:

```python
from fodantic import formable
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    city: str
    zip: str

class Project(BaseModel):
    name: str
    status: str

@formable
class UserModel(BaseModel):
    name: str
    skills: List[str] = []
    address: Address
    projects: List[Project] = []

# Your form data with nested structure
form = UserModel.as_form(request_data)
```

The parser handles all the complexity of transforming the flat form structure into the nested objects your models expect.

## Booleans fields

Boolean fields are treated special because of how browsers handle checkboxes:

- If not checked: the browser doesn't send the field at all, so the missing field will be interpreted as `False`.
- If checked: It sends the "value" attribute, but this is optional, so it could send an empty string instead. So any value other than None will be interpreted as `True`.
