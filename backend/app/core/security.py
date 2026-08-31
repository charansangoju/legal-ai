def sanitize_filename(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")
