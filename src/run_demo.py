"""Rebuild the public demonstration without credentials or external calls.
Run from the repository root: python -m src.run_demo
"""
import argparse
import json
import platform
from pathlib import Path
from importlib.metadata import version
import pandas as pd
import numpy as np
from .generate_demo import generate_demo
from .audit import field_inventory,clean_sessions,check_gating
from .model import run_models
from .sql_demo import run_sql
from .plots import make_plots
from .weekly_report import render_weekly
from .render_site import render_site
from .schema import COUNT_FEATURES


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--samples",type=int,default=2400)
    p.add_argument("--seed",type=int,default=42)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    data=root/"data/synthetic";out=root/"outputs"
    data.mkdir(parents=True,exist_ok=True);out.mkdir(exist_ok=True)
    raw,events=generate_demo(args.samples,args.seed)
    raw.to_csv(data/"sessions.csv",index=False)
    events.to_csv(data/"events.csv",index=False)
    inventory=field_inventory(raw)
    inventory.to_csv(out/"field_inventory.csv",index=False)
    clean,quality=clean_sessions(raw)
    clean.to_csv(out/"cleaned_synthetic_sessions.csv",index=False)
    gates=check_gating(clean)
    sql=run_sql(raw,events,root/"sql/session_features.sql")
    expected=clean.set_index("session_id")
    actual=sql.set_index("session_id").loc[expected.index]
    for c in COUNT_FEATURES:
        np.testing.assert_array_equal(actual[c].to_numpy(),expected[c].to_numpy())
    sql.to_csv(out/"sql_features.csv",index=False)
    model,tables=run_models(clean,args.seed)
    for name,table in tables.items():table.to_csv(out/f"{name}.csv",index=False)
    payload={"provenance":"Wholly synthetic demo; reconstructed code, not original execution.",
             "quality":quality,"gating":gates,"models":model,"sql_count_check":"passed",
             "environment":{"python":platform.python_version(),**{k:version(k) for k in ["numpy","pandas","scipy","statsmodels","scikit-learn","matplotlib"]}}}
    (out/"run_summary.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    make_plots(clean,model,tables["coefficients"],root/"assets")
    (out/"weekly_report_demo.md").write_text(render_weekly(root/"memory/decision_log.example.json"),encoding="utf-8")
    render_site(root,clean,inventory,payload,tables)
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
