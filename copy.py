def deepcopy(obj):
    """Pure Python recursive deepcopy.
    By OpenAI. (2026). Python (ChatGPT) [Large language model]. https://chatgpt.com
    """
    # Immutable types (safe to return as-is).
    #if isinstance(obj, (int, float, str, bool, None.__class__)):
        #return obj
    if obj is None:
        return obj
    for item in (int, float, complex, str, bool):
        if obj.__class__ == item:
            return obj

    # Lists.
    if obj.__class__ is list:
        return [deepcopy(item) for item in obj]

    # Tuples.
    if obj.__class__ is tuple:
        return tuple(deepcopy(item) for item in obj)

    # Sets.
    if obj.__class__ is set:
        return {deepcopy(item) for item in obj}

    # Frozensets.
    if obj.__class__ is frozenset:
        return frozenset({deepcopy(item) for item in obj})

    # Bytes.
    if obj.__class__ is bytes:
        return bytes(deepcopy(item) for item in obj)

    # Bytearrays.
    if obj.__class__ is bytearray:
        return bytearray(deepcopy(item) for item in obj)

    # Dictionaries.
    if obj.__class__ is dict:
        return {deepcopy(key): deepcopy(value) for key, value in obj.items()}

    # Custom objects.
    if hasattr(obj, "__dict__"):
        new_obj = obj.__class__()
        for key, value in obj.__dict__.items():
            setattr(new_obj, key, deepcopy(value))
        return new_obj
