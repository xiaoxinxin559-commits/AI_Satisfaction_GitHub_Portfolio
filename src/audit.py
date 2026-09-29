"""Explicit field inventory, survey gating checks, and session-level cleaning."""
import numpy as np
import pandas as pd
from .schema import CATALOG, COUNT_FEATURES, POS_TAGS, NEG_TAGS, FORBIDDEN_FEATURES


def field_inventory(raw: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for c in raw.columns:
        title,role,reason=CATALOG.get(c,(c,"needs_review","未知字段：先确认口径，不可自动入模"))
        nonempty=raw[c].replace(r"^\s*$",np.nan,regex=True)
        n_unique=int(nonempty.nunique(dropna=True))
        missing=float(nonempty.isna().mean())
        flags=[]
        if missing==1: flags.append("all_missing")
        elif n_unique<=1: flags.append("constant")
        if role=="gated_label": flags.append("target_leakage_risk")
        if role=="versioned": flags.append("cross_period_break")
        rows.append(dict(field=c,title=title,role=role,reason=reason,
                         missing_pct=missing*100,n_unique=n_unique,flags=";".join(flags)))
    return pd.DataFrame(rows)


def clean_sessions(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required=set(CATALOG)
    if missing:=required-set(raw.columns):
        raise ValueError(f"Missing demo columns: {sorted(missing)}")
    df=raw.copy()
    if df["session_id"].isna().any():
        raise ValueError("A session_id is required; do not deduplicate on user_id.")
    df["survey_time"]=pd.to_datetime(df["survey_time"],errors="raise")
    df=df.sort_values(["session_id","survey_time"],kind="stable").drop_duplicates("session_id",keep="last")
    after_dedup=len(df)
    df["score"]=pd.to_numeric(df["score"],errors="coerce")
    valid=df["score"].isin([1,2,3,4,5])
    invalid=int((~valid).sum())
    df=df.loc[valid].copy()
    df["score"]=df["score"].astype(int)
    for c in COUNT_FEATURES:
        values=pd.to_numeric(df[c],errors="coerce")
        if values.isna().any() or (values<0).any():
            raise ValueError(f"Unconfirmed missing/negative count in {c}; do not silently fill.")
        df[c]=values
    uid=df["user_id"].fillna("0").astype(str)
    is_anon=uid.isin(["0","0.0",""])
    anonymous=df["anonymous_id"].fillna("").astype(str)
    fallback=is_anon & anonymous.eq("")
    df["is_anonymous"]=is_anon.astype(int)
    df["participant_key"]=np.where(~is_anon,"u:"+uid,
            np.where(~fallback,"a:"+anonymous,"s:"+df["session_id"].astype(str)))
    # Missing age is modeled explicitly; this is not a universal missing-data remedy.
    df["age_unknown"]=df["age_level"].isna().astype(int)
    df["age_level"]=df["age_level"].fillna(0)
    log={"raw_rows":len(raw),"unique_sessions_before_outcome_filter":after_dedup,
         "duplicate_rows_removed":len(raw)-after_dedup,"invalid_outcome_rows_removed":invalid,
         "valid_sessions":len(df),"anonymous_sessions_retained":int(is_anon.sum()),
         "session_key_fallbacks":int(fallback.sum()),"unit":"session/questionnaire, not unique persons"}
    return df.sort_values("session_id").reset_index(drop=True), log


def check_gating(df: pd.DataFrame) -> dict:
    pos=df[POS_TAGS].sum(axis=1)>0
    neg=df[NEG_TAGS].sum(axis=1)>0
    return {"positive_tags_at_low_score":int((pos & (df.score<=3)).sum()),
            "negative_tags_at_high_score":int((neg & (df.score>=4)).sum()),
            "mixed_branch_tags":int((pos & neg).sum()),
            "no_tag_selected":int((~pos & ~neg).sum()),
            "warning":"Rules must be checked against the questionnaire; zero violations do not prove causality or independence."}


def validate_feature_allowlist(features: list[str]) -> None:
    if bad:=set(features)&set(FORBIDDEN_FEATURES):
        raise ValueError(f"Outcome/post-outcome features are forbidden: {sorted(bad)}")
