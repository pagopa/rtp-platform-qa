from hypothesis import given, strategies as st


@given(st.text())
def test_fuzz(text):
    assert isinstance(text, str)
