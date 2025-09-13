from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.legacy.depotex import run_legacy


def test_legacy_error_when_end_nav_missing(tmp_path: Path):
    # CSV file with wrong columns
    df = pd.DataFrame([{"Date": "2024-01-01", "Cash_Flow": 10.0}])
    p = tmp_path / "bad.csv"
    df.to_csv(p, index=False)
    with pytest.raises(ValueError):
        run_legacy(
            csv_file=p,
            nav_file=None,
            flows_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            twr_mode="simple",
            window=30,
            business_days=False,
            annualize=False,
            money_weighted=False,
            tax_rate=0.25,
            tax_allowance=1000.0,
            church_tax=0.0,
            soli=False,
            include_tax=False,
            output=tmp_path / "out.csv",
            output_prefix=tmp_path,
            plot=False,
            save_svg=False,
        )


def test_legacy_nav_and_flows_paths(tmp_path: Path):
    # separate nav and flows inputs, covering merge branch and plotting off
    nav = pd.DataFrame(
        [{"Date": "2024-01-01", "End_NAV": 100.0}, {"Date": "2024-01-10", "End_NAV": 101.0}]
    )
    flows = pd.DataFrame(
        [{"Date": "2024-01-05", "Cash_Flow": 50.0}, {"Date": "2024-01-06", "Cash_Flow": -10.0}]
    )
    nav_p = tmp_path / "nav.csv"
    fl_p = tmp_path / "flows.csv"
    nav.to_csv(nav_p, index=False)
    flows.to_csv(fl_p, index=False)

    # csv_file can be a dummy (not used when nav/flows provided) but required by signature
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("Date,End_NAV\n2024-01-01,100", encoding="utf-8")

    res = run_legacy(
        csv_file=None,
        nav_file=nav_p,
        flows_file=fl_p,
        csv_in_sep=",",
        csv_in_decimal=".",
        csv_out_sep=",",
        csv_out_decimal=".",
        twr_mode="flow-adjusted",
        window=5,
        business_days=True,
        annualize=True,
        money_weighted=True,
        tax_rate=0.25,
        tax_allowance=1000.0,
        church_tax=0.0,
        soli=False,
        include_tax=True,
        output=tmp_path / "legacy_out.csv",
        output_prefix=tmp_path,
        plot=False,
        save_svg=False,
    )
    assert "df" in res and res["out_path"].exists()
