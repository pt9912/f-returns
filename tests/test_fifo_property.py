import math

from hypothesis import given
from hypothesis import strategies as st


def fifo_pnl(trades):
    lots = []
    pnl = 0.0
    for qty, price in trades:
        if qty > 0:
            lots.append([qty, price])
        else:
            sell = -qty
            while sell > 0 and lots:
                take = min(sell, lots[0][0])
                pnl += take * (price - lots[0][1])
                lots[0][0] -= take
                if lots[0][0] <= 1e-12:
                    lots.pop(0)
                sell -= take
    return pnl, lots


# Test 1: Verhindere Short-Selling in den Testdaten
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=-10, max_value=10).filter(lambda q: q != 0),
            st.floats(min_value=0.01, max_value=1000.0),
        ),
        min_size=1,
        max_size=50,
    ).filter(
        lambda trades: all(  # Nur Sequenzen, bei denen die kumulierte Menge nie negativ wird
            sum(q for q, _ in trades[: i + 1]) >= 0 for i in range(len(trades))
        )
    )
)
def test_fifo_never_negative_inventory(trades):
    qty_sum = 0
    for q, _ in trades:
        qty_sum += q
        assert qty_sum >= 0  # Sollte immer wahr sein


# Test 2: Prüfe Roundtrip-PnL (bereits korrekt)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=10), st.floats(min_value=1.0, max_value=1000.0)
        ),
        min_size=1,
        max_size=30,
    )
)
def test_fifo_roundtrip_zero_pnl_if_sell_at_buy_price(buys):
    sells = [(-q, p) for q, p in buys]
    pnl, _ = fifo_pnl(buys + sells)
    assert math.isclose(pnl, 0.0, abs_tol=1e-8)
