from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import run_legacy


def test_legacyex_nav_and_flows_with_fee_external(tmp_path: Path):
    nav = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "End_NAV": [100, 98, 99, 101],
        }
    )
    flows = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            # negative = Kauf, positive = Verkauf
            "Cash_Flow": [0, -10, 0, +12],
            "Fee_External": [0, 2, 0, 1],
        }
    )
    navf = tmp_path / "nav.csv"
    flowf = tmp_path / "flows.csv"
    nav.to_csv(navf, index=False)
    flows.to_csv(flowf, index=False)
    out = tmp_path / "out.csv"
    res = run_legacy(
        csv_file=None,
        nav_file=navf,
        flows_file=flowf,
        output=out,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
    )
    assert out.exists()
    df = res["df"]
    # Aktuelles Verhalten: Cash_Flow bleibt wie geliefert (Fee_External wird separat ausgewiesen).
    cf = df.set_index("Date")["Cash_Flow"]
    assert cf.loc["2024-01-02"] == -10
    assert cf.loc["2024-01-04"] == 12
    # Steuer-bezogene Spalten vorhanden
    assert "Taxable_Income" in df.columns
    assert "Tax_Paid" in df.columns
    assert "Taxable_Income_Window" in df.columns
