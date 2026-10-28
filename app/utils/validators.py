def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email


def is_valid_text(text: str, min_len: int = 3) -> bool:
    return bool(text and len(text.strip()) >= min_len)