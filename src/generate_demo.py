"""Generate wholly synthetic sessions/events. Never reads private source data."""
from pathlib import Path
import numpy as np
import pandas as pd
from .schema import COUNT_FEATURES, POS_TAGS, NEG_TAGS


def generate_demo(n: int = 2400, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    if n < 400:
        raise ValueError("Use at least 400 sessions for the demonstration.")
    rng = np.random.default_rng(seed)
    people = rng.integers(0, max(200, int(n * .65)), size=n)
    anonymous = people % 5 == 0
    age_by_person = rng.choice(4, size=people.max()+1)
    age = age_by_person[people].astype(float)
    age[people % 11 == 0] = np.nan
    old = (people % 3 != 0).astype(int)
    period = rng.choice(["P1", "P2", "P3", "P4"], n)
    entry = rng.choice(["self", "search", "feed"], n, p=[.40, .40, .20])
    quick = rng.poisson(np.where(entry == "self", 1.7, .8), n)
    consult = rng.poisson(.55, n)
    shown = rng.poisson(.8 + .65*quick + .45*consult)
    clicks = rng.binomial(shown, .35)
    content_quality = rng.normal(size=n)
    difficulty = rng.normal(size=n)
    # This DGP is newly invented. Its coefficients do not approximate any actual system.
    latent = (1.75 + .45*np.log1p(quick) + .22*np.log1p(consult)
              + .28*np.log1p(shown) - .18*np.log1p(clicks)
              + .12*old + .07*np.nan_to_num(age, nan=1.5)
              + .75*content_quality - .35*difficulty + rng.normal(0,.80,n))
    score = np.digitize(latent, [.2, .9, 1.55, 2.65]) + 1
    dates = pd.Timestamp("2020-01-01") + pd.to_timedelta(rng.integers(0, 120*24*60, n), unit="m")
    # Period markers are derived from these synthetic dates so both stay consistent.
    period = (pd.Series(dates).dt.dayofyear.sub(1).floordiv(30).clip(upper=3)
              .map({0:"P1",1:"P2",2:"P3",3:"P4"}).to_numpy())
    df = pd.DataFrame({
        "session_id": [f"demo_session_{i:05d}" for i in range(n)],
        "user_id": np.where(anonymous, "0", np.array([f"demo_user_{i}" for i in people])),
        "anonymous_id": np.where(anonymous, [f"demo_anon_{i}" for i in people], ""),
        "survey_time": dates.strftime("%Y-%m-%d %H:%M:%S"),
        "period":period, "entry_source":entry, "score":score.astype(float),
        "age_level":age, "is_returning":old,
        "quick_result_count":quick, "consult_result_count":consult,
        "followup_shown_count":shown, "followup_click_count":clicks,
        "order_flag":rng.binomial(1, np.clip(.02+.025*score,0,1)),
        "return_next_day":0,
        "legacy_card_count":np.where(np.isin(period,["P1","P2"]),rng.poisson(.5,n),np.nan),
        "unused_empty":np.nan,
        "expert_score":np.nan,
    })
    for c,p in zip(POS_TAGS,[.27,.64,.38,.34]):
        df[c] = ((score>=4) & (rng.random(n)<p)).astype(int)
    for c,p in zip(NEG_TAGS,[.40,.21,.35,.20]):
        df[c] = ((score<=3) & (rng.random(n)<p)).astype(int)
    eval_idx = rng.choice(n,120,replace=False)
    expert = np.clip(np.rint(.8 + .85*content_quality[eval_idx] + rng.normal(0,1,120)), -2,3)
    df.loc[eval_idx,"expert_score"] = expert
    # Deliberate quality faults. Never impute a missing outcome.
    df.loc[np.arange(8),"score"] = np.nan
    df.loc[np.arange(8,14),"score"] = -99
    # Events have timestamps before the survey. Add two future events as a SQL guard test.
    event_rows=[]
    for c in COUNT_FEATURES:
        for i,k in enumerate(df[c].astype(int)):
            for j in range(k):
                event_rows.append((df.at[i,"session_id"], c, (dates[i]-pd.Timedelta(minutes=j+1)).strftime("%Y-%m-%d %H:%M:%S")))
    for i in [20,21]:
        event_rows.append((df.at[i,"session_id"],"quick_result_count",(dates[i]+pd.Timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))
    events=pd.DataFrame(event_rows,columns=["session_id","event_name","event_time"])
    duplicate = df.iloc[30:42].copy()
    duplicate["survey_time"] = (pd.to_datetime(duplicate["survey_time"])-pd.Timedelta(seconds=1)).dt.strftime("%Y-%m-%d %H:%M:%S")
    return pd.concat([df,duplicate],ignore_index=True), events


def save_demo(folder: Path, n: int = 2400, seed: int = 42) -> None:
    folder.mkdir(parents=True,exist_ok=True)
    raw, events = generate_demo(n,seed)
    raw.to_csv(folder/"sessions.csv",index=False)
    events.to_csv(folder/"events.csv",index=False)
