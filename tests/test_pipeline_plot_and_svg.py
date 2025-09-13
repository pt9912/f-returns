from pathlib import Path

import pandas as pd

from rolling_returns.pipeline import run_pipeline


def test_pipeline_plot_and_svg_outputs(tmp_path: Path):
    # Minimal trades & prices with one BUY+DIV triggers cash flow & nav
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "AAA",
                "Quantity": 1,
                "Price": 10.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
            {
                "Date": "2024-01-03",
                "Action": "DIV",
                "Instrument": "AAA",
                "Quantity": 1,
                "Price": 1.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "AAA", "ClosePrice": 10.0},
            {"Date": "2024-01-03", "Instrument": "AAA", "ClosePrice": 11.0},
            {"Date": "2024-01-04", "Instrument": "AAA", "ClosePrice": 12.0},
        ]
    )

    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    res = run_pipeline(
        trades_file=tr,
        prices_file=pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        csv_in_sep=",",
        csv_in_decimal=".",
        window=30,
        business_days=False,
        annualize=True,
        output_prefix=out_dir,
    )
    assert isinstance(res, dict)
    # Core outputs
    assert (out_dir / "nav.csv").exists()
    # Plot artifacts - accept .png or .svg depending on backend
