from routes.speech import _is_low_quality_transcript


def test_valid_short_transcript_is_not_rejected():
    assert _is_low_quality_transcript("I went to the market with my family") is False
    assert _is_low_quality_transcript("I am reading clearly today") is False


def test_repeated_gibberish_still_gets_rejected():
    assert _is_low_quality_transcript("you you you you you") is True
    assert _is_low_quality_transcript("hello hello hello") is True
