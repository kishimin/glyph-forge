import regex

_GRAPHEME_PATTERN = regex.compile(r"\X")
_MAX_CODEPOINTS_PER_ALLOWED_GRAPHEME = 1_024


def split_graphemes(text: str) -> list[str]:
    return _GRAPHEME_PATTERN.findall(text)


def exceeds_grapheme_limit(text: str, maximum_graphemes: int) -> bool:
    if len(text) > maximum_graphemes * _MAX_CODEPOINTS_PER_ALLOWED_GRAPHEME:
        return True

    return next(
        (
            True
            for count, _ in enumerate(_GRAPHEME_PATTERN.finditer(text), start=1)
            if count > maximum_graphemes
        ),
        False,
    )
