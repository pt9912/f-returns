from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depot import run_legacy


def test_legacy_depot_money_weighted_business_days(tmp_path: Path):
    df = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "End_NAV": 100.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-05",
                "End_NAV": 101.0,
                "Cash_Flow": -10.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-10",
                "End_NAV": 100.5,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-15",
                "End_NAV": 102.0,
                "Cash_Flow": 5.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
        ]
    )
    p = tmp_path / "in.csv"
    df.to_csv(p, index=False)
    res = run_legacy(
        csv_file=p,
        csv_in_sep=",",
        csv_in_decimal=".",
        csv_out_sep=",",
        csv_out_decimal=".",
        window=3,
        business_days=True,
        annualize=False,
        money_weighted=True,
        plot=False,
        save_svg=False,
        output=tmp_path / "out.csv",
        output_prefix=tmp_path,
    )
    assert res["out_path"].exists()
    out = res["df"]
    assert "Rolling_MWR" in out.columns
