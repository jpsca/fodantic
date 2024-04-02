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
        self.get = self._find_get_method()
        self.getall = self._find_getall_method()

    def __contains__(self, __name: str) -> bool:
        return __name in self.source

    def _find_get_method(self) -> t.Callable[[str], t.Any]:
        if hasattr(self.source, "get"):
            return self.source.get

        def get_fallback(name: str) -> t.Any:
            return getattr(self.source, name, None)

        return get_fallback

    def _find_getall_method(self) -> t.Callable[[str], list[t.Any]]:
        # WebOb, Bottle, and Proper uses `getall`
        if hasattr(self.source, "getall"):
            return self.source.getall
        # Django, Flask (Werkzeug), cgi.FieldStorage, etc. uses `getlist`
        if hasattr(self.source, "getlist"):
            return self.source.getlist

        def getall_fallback(name: str) -> list[t.Any]:
            values = self.get(name)
            if values is None:
                return []
            if isinstance(values, list):
                return values
            return [values]

        return getall_fallback


class ObjectWrapper:
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
        self.get = self._find_get_method()

    def _find_get_method(self) -> t.Callable[[str], t.Any]:
        if self.is_dict:
            return self.source.get

        def get_fallback(name: str) -> t.Any:
            return getattr(self.source, name, None)

        return get_fallback

    def update(self, data: dict[str, t.Any]) -> t.Any:
        if self.is_dict:
            self.source.update(data)
        else:
            for key, value in data.items():
                setattr(self.source, key, value)

        return self.source
