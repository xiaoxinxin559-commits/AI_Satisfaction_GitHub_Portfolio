import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from src.generate_demo import generate_demo
from src.audit import clean_sessions,field_inventory,check_gating,validate_feature_allowlist
from src.schema import COUNT_FEATURES,MODEL_FEATURES,POS_TAGS
from src.model import TrainOnlyTransform
from src.sql_demo import run_sql

@pytest.fixture(scope="module")
def sample():
    raw,events=generate_demo(600,42)
    clean,log=clean_sessions(raw)
    return raw,events,clean,log

def test_row_accounting(sample):
    raw,events,clean,log=sample
    assert log["raw_rows"]==log["duplicate_rows_removed"]+log["invalid_outcome_rows_removed"]+len(clean)
    assert log["duplicate_rows_removed"]==12
    assert log["invalid_outcome_rows_removed"]==14
    assert clean.session_id.is_unique

def test_anonymous_not_collapsed(sample):
    clean=sample[2]
    anonymous=clean.loc[clean.is_anonymous==1]
    assert len(anonymous)>1
    assert anonymous.participant_key.nunique()>1
    assert sample[3]["anonymous_sessions_retained"]==len(anonymous)

def test_all_columns_accounted_for(sample):
    inventory=field_inventory(sample[0])
    assert len(inventory)==len(sample[0].columns)
    assert set(inventory.field)==set(sample[0].columns)
    assert not (inventory.role=="needs_review").any()

def test_constant_and_empty_flagged(sample):
    d=field_inventory(sample[0]).set_index("field")
    assert "all_missing" in d.loc["unused_empty","flags"]
    assert "constant" in d.loc["return_next_day","flags"]

def test_gate_validation(sample):
    r=check_gating(sample[2])
    assert r["positive_tags_at_low_score"]==0
    assert r["negative_tags_at_high_score"]==0
    assert r["mixed_branch_tags"]==0

def test_gate_validation_detects_corruption(sample):
    d=sample[2].copy()
    i=d.index[d.score<=3][0]
    d.loc[i,POS_TAGS[0]]=1
    assert check_gating(d)["positive_tags_at_low_score"]==1

def test_allowlist_blocks_target_and_downstream():
    validate_feature_allowlist(MODEL_FEATURES)
    for wrong in ["score","has_positive_tag","order_flag",*POS_TAGS]:
        with pytest.raises(ValueError): validate_feature_allowlist(MODEL_FEATURES+[wrong])

def test_transform_fitted_only_on_train(sample):
    d=sample[2]
    train,test=d.iloc[:300].copy(),d.iloc[300:].copy()
    prep=TrainOnlyTransform().fit(train)
    cap=prep.caps.copy()
    test[COUNT_FEATURES]=10**9
    out=prep.transform(test)
    pd.testing.assert_series_equal(cap,prep.caps)
    assert np.isfinite(out.to_numpy()).all()

def test_sql_reproduces_pre_survey_counts(sample):
    raw,events,clean,_=sample
    path=Path(__file__).resolve().parents[1]/"sql/session_features.sql"
    out=run_sql(raw,events,path).set_index("session_id")
    expected=clean.set_index("session_id")
    assert set(out.index)==set(expected.index)
    for c in COUNT_FEATURES:
        np.testing.assert_array_equal(out.loc[expected.index,c],expected[c])

def test_missing_session_key_is_not_guessed(sample):
    raw=sample[0].copy()
    raw.loc[0,"session_id"]=np.nan
    with pytest.raises(ValueError): clean_sessions(raw)

def test_synthetic_reproducibility():
    a,e=generate_demo(400,42)
    b,f=generate_demo(400,42)
    pd.testing.assert_frame_equal(a,b)
    pd.testing.assert_frame_equal(e,f)

def test_no_silent_negative_counts(sample):
    raw=sample[0].copy()
    raw.loc[50,"quick_result_count"]=-1
    with pytest.raises(ValueError):clean_sessions(raw)
