def ensure_presence[T](container: set[T], value: T, present: bool) -> None:
    if present:
        container.add(value)
    else:
        container.remove(value)
