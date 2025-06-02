"""
Fodantic
Copyright (c) 2024 Juan-Pablo Scaletti
"""
import typing as t


class ObjectWrapper:
    def __init__(self, source: t.Any):
        """
        A utility class for wrapping request data and providing a consistent interface
        for updating, accessing single values, or lists of values.

        Args:
            source:
                The underlying data source. Can be a Multidict
                implementation or a regular dict.

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
