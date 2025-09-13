from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depot import run_legacy


def test_legacy_depot_plot_and_sums(tmp_path: Path):
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Fee_Internal": 1.0, "Tax_Internal": 0.5},
            {"Date": "2024-01-10", "End_NAV": 101.0, "Fee_Internal": 0.0, "Tax_Internal": 0.0},
            {"Date": "2024-01-20", "End_NAV": 102.0, "Fee_Internal": 0.2, "Tax_Internal": 0.1},
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
        window=10,
        business_days=False,
        annualize=True,
        money_weighted=False,
        plot=True,
        save_svg=True,
        output=tmp_path / "out.csv",
        output_prefix=tmp_path,
    )
    assert res["out_path"].exists()
    # check images created
    assert res["out_path"].with_suffix(".png").exists()
    assert res["out_path"].with_suffix(".svg").exists()
