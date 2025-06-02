from multidict import MultiDict
from pydantic import BaseModel

from fodantic import formable


@formable
class UserModel(BaseModel):
    name: str
    friends: list[int]
    active: bool = True


# This is just an example.
# You would use the request POST data of your web framework instead,
# for example `request_data = request.form` in Flask
request_data = MultiDict(
    [
        ("name", "John Doe"),
        ("friends", "2"),
        ("friends", "3"),
    ]
)

# The magic
form = UserModel.as_form(request_data, object=None)

print(form)
# > UserModel.as_form(name='John Doe', friends=[2, 3], active=False)
print(form.fields["name"].value)
# > John Doe
print(form.fields["name"].error)
# > None
print(form.save())  # Can also update the `object` passed as an argument
# > {'name': 'John Doe', 'friends': [2, 3], 'active': False}
