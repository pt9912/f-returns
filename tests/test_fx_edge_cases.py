import math

import pytest


def convert(amount, rate):
    return amount * rate


@pytest.mark.parametrize(
    "amt,rate,expect",
    [
        (100.0, 0.0, 0.0),
        (0.0, 1.2345, 0.0),
        (100.0, 1.0, 100.0),
        (100.0, 0.85, 85.0),
        (100.0, 1e-9, 1e-7),
    ],
)
def test_fx_multiplicative_edges(amt, rate, expect):
    assert math.isclose(convert(amt, rate), expect, rel_tol=0, abs_tol=1e-12)


def test_fx_divide_by_zero_guard():
    rate = 0.0
    with pytest.raises(ZeroDivisionError):
        _ = 1.0 / rate  # replace with your FX inversion logic handling
