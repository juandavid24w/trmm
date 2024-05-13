from .registry import CSVIORegistry


def register(model, serializer, **kwargs):
    CSVIORegistry.register(model, serializer, **kwargs)
