"""Build one self-contained offline HTML page from computed synthetic outputs."""
import base64
import html
import json
from pathlib import Path
import pandas as pd


def render_site(root: Path,df: pd.DataFrame,inventory: pd.DataFrame,summary: dict,tables: dict) -> None:
    data=df[["period","entry_source","is_returning","score","is_anonymous"]].copy()
    grouped=data.groupby(["period","entry_source","is_returning","score"],as_index=False).agg(n=("score","size"),anon=("is_anonymous","sum"))
    payload={"groups":json.loads(grouped.to_json(orient="records")),
             "fields":json.loads(inventory.to_json(orient="records",force_ascii=False)),
             "summary":summary,
             "ordinal":json.loads(tables["ordinal_sensitivity"].to_json(orient="records"))}
    template=(root/"src/site_template.html").read_text(encoding="utf-8")
    replacements={"__DATA_JSON__":json.dumps(payload,ensure_ascii=False).replace("</","<\\/"),
                  "__SQL_CODE__":html.escape((root/"sql/session_features.sql").read_text(encoding="utf-8")),
                  "__PYTHON_CODE__":html.escape((root/"src/audit.py").read_text(encoding="utf-8")),
                  "__SKILL_TEXT__":html.escape((root/"skills/satisfaction-analysis/SKILL.md").read_text(encoding="utf-8"))}
    for key in ["score_distribution","leakage_demo","coefficient_associations","dual_signal_review"]:
        replacements[f"__IMG_{key}__"]="data:image/png;base64,"+base64.b64encode((root/f"assets/{key}.png").read_bytes()).decode()
    for key,val in replacements.items():template=template.replace(key,val)
    (root/"docs/index.html").write_text(template,encoding="utf-8")
