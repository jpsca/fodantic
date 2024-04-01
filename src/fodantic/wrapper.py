"""
Fodantic
Copyright (c) 2024 Juan-Pablo Scaletti
"""
import typing as t


class DataWrapper:
    def __init__(self, source: t.Any):
        """
        A utility class for wrapping request data and providing a consistent interface
        for updating, accessing single values, or lists of values.

        ## Arguments:

        - source: The underlying data source. Can be a Multidict implementation
            or a regular dict.

        """
        self.source: t.Any = {} if source is None else source
        self.is_dict = isinstance(source, dict)
        self.get = self._get_get_method()
        self.getall = self._get_getall_method()

    def __contains__(self, __name: str) -> bool:
        return __name in self.source

    def update(self, data: dict[str, t.Any]) -> t.Any:
        if self.is_dict:
            self.source.update(data)
        else:
            for key, value in data.items():
                setattr(self.source, key, value)

        return self.source

    def _get_get_method(self) -> t.Callable[[str], t.Any]:
        if self.is_dict:
            return self.source.get

        def get_fallback(name: str) -> t.Any:
            if not self.source:
                return None
            return getattr(self.source, name, None)

        return get_fallback

    def _get_getall_method(self) -> t.Callable[[str], list[t.Any]]:
        if not self.is_dict:
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
