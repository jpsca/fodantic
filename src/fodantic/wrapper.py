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
