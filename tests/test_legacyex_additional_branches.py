from pathlib import Path

import pandas as pd

from rolling_returns.legacy import depotex


def make_csv(tmp_path: Path, name: str, rows, sep=",", decimal="."):
    p = tmp_path / name
    pd.DataFrame(rows).to_csv(p, index=False, sep=sep, decimal=decimal)
    return p


def test_calculate_tax_rate_variants():
    r1 = depotex.calculate_tax_rate(base_rate=0.25, soli=False, church_tax=0.0)
    r2 = depotex.calculate_tax_rate(base_rate=0.25, soli=True, church_tax=0.09)
    assert r1 == 0.25 and r2 > r1


def test_aggregate_by_date_various_columns():
    rows = [
        {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 1.0, "Fee_Internal": 0.1},
        {"Date": "2024-01-01", "End_NAV": 101.0, "Cash_Flow": 2.0, "Fee_Internal": 0.2},
        {"Date": "2024-01-02", "End_NAV": 102.0, "Cash_Flow": 3.0, "Fee_Internal": 0.3},
    ]
    df = pd.DataFrame(rows)
    out = depotex.aggregate_by_date(df)

    end_nav = out.loc[out["Date"] == "2024-01-01", "End_NAV"].iloc[0]
    cf_sum = out.loc[out["Date"] == "2024-01-01", "Cash_Flow"].iloc[0]
    fi_sum = out.loc[out["Date"] == "2024-01-01", "Fee_Internal"].iloc[0]

    assert end_nav in (101.0, 101)
    assert cf_sum == 3.0
    assert abs(fi_sum - 0.3) < 1e-9


def test_run_legacy_single_combined_csv_all_flags(tmp_path: Path):
    rows = [
        {
            "Date": "2024-01-01",
            "End_NAV": 1000.0,
            "Cash_Flow": -100.0,
            "Fee_Internal": 1.0,
            "Fee_External": 0.5,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-02",
            "End_NAV": 1015.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.0,
            "Fee_External": 0.0,
            "Tax_Internal": 0.0,
        },
        {
            "Date": "2024-01-03",
            "End_NAV": 1020.0,
            "Cash_Flow": 50.0,
            "Fee_Internal": 0.2,
            "Fee_External": 0.3,
            "Tax_Internal": 1.0,
        },
        {
            "Date": "2024-01-06",
            "End_NAV": 1010.0,
            "Cash_Flow": 0.0,
            "Fee_Internal": 0.1,
            "Fee_External": 0.0,
            "Tax_Internal": 0.0,
        },
    ]
    csv = make_csv(tmp_path, "ex.csv", rows)

    out = depotex.run_legacy(
        csv_file=csv,
        nav_file=None,
        flows_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        csv_out_sep=";",
        csv_out_decimal=",",
        twr_mode="flow-adjusted",
        window=3,
        business_days=False,
        annualize=True,
        money_weighted=True,
        tax_rate=0.25,
        tax_allowance=801.0,
        church_tax=0.0,
        soli=True,
        include_tax=True,
        output=None,
        output_prefix=tmp_path,  # ensure output goes to tmp
        plot=True,
        plot_title="Test",
        save_svg=True,
    )
    assert "df" in out and "out_path" in out
    written = out["out_path"]
    assert (
        written.exists()
        and written.with_suffix(".png").exists()
        and written.with_suffix(".svg").exists()
    )


def test_run_legacy_nav_and_flows_files(tmp_path: Path):
    nav = [
        {"Date": "2024-01-01", "End_NAV": 1000.0},
        {"Date": "2024-01-02", "End_NAV": 1005.0},
        {"Date": "2024-01-03", "End_NAV": 990.0},
    ]
    flows = [
        {"Date": "2024-01-01", "Cash_Flow": -100.0},
        {"Date": "2024-01-03", "Cash_Flow": 30.0},
    ]
    nav_file = make_csv(tmp_path, "nav.csv", nav)
    flows_file = make_csv(tmp_path, "flows.csv", flows)

    out = depotex.run_legacy(
        csv_file=None,
        nav_file=nav_file,
        flows_file=flows_file,
        window=2,
        business_days=True,
        annualize=False,
        money_weighted=False,
        include_tax=False,
        plot=False,
        output_prefix=tmp_path,  # ensure output goes to tmp
    )
    assert "df" in out and out["df"].shape[0] >= 3
