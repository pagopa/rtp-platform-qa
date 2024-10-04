from hypothesis import given
from hypothesis import strategies as st


@given(st.text())
def test_fuzz(text):
    assert isinstance(text, str)
