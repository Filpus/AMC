from amc import llm


def test_overflow():
    assert llm.overflow(4098, 500, 8192) == "przepelnienie"
    assert llm.overflow(7650, 635, 8192) == "przesuniecie"
    assert llm.overflow(7650, 500, 8192) is None
    assert llm.overflow(None, None, 8192) is None
