from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.legacy import depot


def make_csv(tmp_path: Path, name: str, rows):
    p = tmp_path / name
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_run_legacy_with_external_tax_and_plots(tmp_path: Path):
    rows = [
        {
            "Date": "2024-01-01",
            "End_NAV": 1000.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-02",
            "End_NAV": 1010.0,
            "Cash_Flow": -50.0,
            "Fee_Internal": 1.0,
            "Tax_Internal": 0.5,
        },
        {
            "Date": "2024-01-03",
            "End_NAV": 1020.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-04",
            "End_NAV": 1030.0,
            "Cash_Flow": 25.0,
            "Fee_Internal": 0.5,
            "Tax_Internal": 0.2,
        },
        {
            "Date": "2024-01-05",
            "End_NAV": 1040.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-06",
            "End_NAV": 1035.0,
            "Cash_Flow": -10.0,
            "Fee_Internal": 0.2,
            "Tax_Internal": 0.1,
        },
    ]
    csv = make_csv(tmp_path, "legacy.csv", rows)
    df = pd.read_csv(csv)
    df["Tax_External"] = [0, 0.2, 0, 0, 0.1, 0]
    df.to_csv(csv, index=False)

    out = depot.run_legacy(
        csv_file=csv,
        external_tax_column="Tax_External",
        csv_in_sep=",",
        csv_in_decimal=".",
        csv_out_sep=";",
        csv_out_decimal=",",
        window=3,
        business_days=False,
        annualize=True,
        money_weighted=True,
        plot=True,
        save_svg=True,
        output=None,
        output_prefix=tmp_path,  # ensure output goes to tmp
    )
    assert "df" in out and "out_path" in out
    written = out["out_path"]
    assert written.exists()
    assert written.with_suffix(".png").exists()
    assert written.with_suffix(".svg").exists()

    df2 = out["df"]
    assert "Rolling_TWR" in df2.columns and "Rolling_TWR_exFees" in df2.columns
    assert df2.loc[df2.index[1], "Cash_Flow"] == pytest.approx(-49.8, abs=1e-6)
    assert df2.loc[df2.index[4], "Cash_Flow"] == pytest.approx(0.1, abs=1e-6)


def test_run_legacy_business_days_branch(tmp_path: Path):
    rows = [
        {
            "Date": "2024-01-01",
            "End_NAV": 100.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-02",
            "End_NAV": 101.0,
            "Cash_Flow": -10.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-03",
            "End_NAV": 102.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-04",
            "End_NAV": 103.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-05",
            "End_NAV": 104.0,
            "Cash_Flow": 5.0,
            "Fee_Internal": 0.0,
            "Tax_Internal": 0.0,
        },
    ]
    csv = make_csv(tmp_path, "legacy_bd.csv", rows)
    out = depot.run_legacy(
        csv_file=csv,
        window=3,
        business_days=True,
        annualize=False,
        money_weighted=False,
        plot=False,
        output_prefix=tmp_path,  # ensure output goes to tmp
    )
    assert "df" in out and "Rolling_TWR" in out["df"].columns
