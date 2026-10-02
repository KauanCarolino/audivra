from audivra.utils.masking import mask_text


def test_should_keep_the_last_digits_and_separators() -> None:
    assert mask_text("123.456.789-12") == "***.***.***-12"
    assert mask_text("123.456.789-34") == "***.***.***-34"


def test_should_mask_short_values_completely() -> None:
    assert mask_text("ab") == "**"
    assert mask_text(None) is None
    assert mask_text("") == ""
