from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import run_legacy


def test_legacy_depotex_simple_mode_with_external_fee_and_plot(tmp_path: Path):
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 0.0, "Fee_External": 1.0},
            {"Date": "2024-01-05", "End_NAV": 100.5, "Cash_Flow": 10.0, "Fee_External": 0.0},
            {"Date": "2024-01-10", "End_NAV": 101.0, "Cash_Flow": 0.0, "Fee_External": 0.0},
        ]
    )
    p = tmp_path / "legacy.csv"
    df.to_csv(p, index=False)
    res = run_legacy(
        csv_file=p,
        nav_file=None,
        flows_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        csv_out_sep=",",
        csv_out_decimal=".",
        twr_mode="simple",
        window=5,
        business_days=False,
        annualize=True,
        money_weighted=False,
        tax_rate=0.25,
        tax_allowance=1000.0,
        church_tax=0.0,
        soli=False,
        include_tax=False,
        output=tmp_path / "legacy_out.csv",
        output_prefix=tmp_path,
        plot=True,
        save_svg=True,
    )
    assert res["out_path"].exists()
    assert res["out_path"].with_suffix(".png").exists()
    assert res["out_path"].with_suffix(".svg").exists()
