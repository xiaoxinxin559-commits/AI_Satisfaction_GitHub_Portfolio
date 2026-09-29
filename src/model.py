"""Transparent demo models: grouped holdout OLS + an ordinal sensitivity fit.
All outputs are synthetic. Observational associations are not intervention effects.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import r2_score, mean_absolute_error
from .schema import COUNT_FEATURES, MODEL_FEATURES, POS_TAGS
from .audit import validate_feature_allowlist


@dataclass
class TrainOnlyTransform:
    caps: pd.Series | None = None
    means: pd.Series | None = None
    scales: pd.Series | None = None

    def fit(self,train: pd.DataFrame):
        self.caps=train[COUNT_FEATURES].quantile(.99)
        z=self._raw(train)
        self.means=z.mean()
        self.scales=z.std(ddof=0)
        if (self.scales<=0).any():
            raise ValueError("A constant model feature needs an explicit decision.")
        return self

    def _raw(self,df: pd.DataFrame) -> pd.DataFrame:
        if self.caps is None: raise RuntimeError("Call fit() on training data first.")
        z=df[MODEL_FEATURES].astype(float).copy()
        z[COUNT_FEATURES]=np.log1p(z[COUNT_FEATURES].clip(upper=self.caps,axis=1))
        return z

    def transform(self,df: pd.DataFrame) -> pd.DataFrame:
        if self.means is None or self.scales is None: raise RuntimeError("Transformer is not fitted.")
        return (self._raw(df)-self.means)/self.scales


def run_models(df: pd.DataFrame,seed: int=42) -> tuple[dict,dict[str,pd.DataFrame]]:
    validate_feature_allowlist(MODEL_FEATURES)
    splitter=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed)
    tr,te=next(splitter.split(df,groups=df["participant_key"]))
    train,test=df.iloc[tr].copy(),df.iloc[te].copy()
    if set(train.participant_key)&set(test.participant_key):
        raise AssertionError("Participants overlap across training and holdout sets.")
    prep=TrainOnlyTransform().fit(train)
    xt,xv=prep.transform(train),prep.transform(test)
    yt,yv=train.score.astype(float),test.score.astype(float)
    X=sm.add_constant(xt,has_constant="add")
    V=sm.add_constant(xv,has_constant="add")
    fit=sm.OLS(yt,X).fit(cov_type="cluster",cov_kwds={"groups":train.participant_key},use_t=True)
    pred=fit.predict(V)
    yscale=float(yt.std(ddof=0))
    ci=fit.conf_int()
    coefficients=pd.DataFrame({"feature":MODEL_FEATURES,
        "standardized_beta":fit.params[MODEL_FEATURES].to_numpy()/yscale,
        "ci_low":ci.loc[MODEL_FEATURES,0].to_numpy()/yscale,
        "ci_high":ci.loc[MODEL_FEATURES,1].to_numpy()/yscale,
        "p_value_clustered":fit.pvalues[MODEL_FEATURES].to_numpy()})
    baseline={"train_r2":float(fit.rsquared),"test_r2":float(r2_score(yv,pred)),
              "test_mae":float(mean_absolute_error(yv,pred))}
    # Deliberately invalid comparator: positive labels were displayed after the score.
    # A higher holdout R² cannot make a post-outcome feature available before the outcome.
    xt_bad=xt.assign(has_positive_tag=(train[POS_TAGS].sum(axis=1)>0).astype(int))
    xv_bad=xv.assign(has_positive_tag=(test[POS_TAGS].sum(axis=1)>0).astype(int))
    bad=sm.OLS(yt,sm.add_constant(xt_bad,has_constant="add")).fit()
    badpred=bad.predict(sm.add_constant(xv_bad,has_constant="add"))
    leakage={"train_r2":float(bad.rsquared),"test_r2":float(r2_score(yv,badpred)),
             "test_mae":float(mean_absolute_error(yv,badpred)),"valid_for_prediction":False}
    # Ordinal logit preserves score ordering. It assumes proportional odds and is exploratory.
    # No intercept: thresholds supply the location parameters.
    ordinal_model=OrderedModel(train.score,xt,distr="logit")
    ordinal=ordinal_model.fit(method="bfgs",maxiter=300,disp=False)
    converged=bool(ordinal.mle_retvals.get("converged",False))
    if not converged: raise RuntimeError("Ordinal fit failed to converge; do not publish estimates.")
    probability=np.asarray(ordinal.model.predict(ordinal.params,exog=xv))
    ordinal_pred=probability@np.sort(train.score.unique())
    ordinal_table=pd.DataFrame({"feature":MODEL_FEATURES,
        "ordinal_log_odds_per_sd":ordinal.params[MODEL_FEATURES].to_numpy(),
        "same_direction_as_ols":np.sign(ordinal.params[MODEL_FEATURES].to_numpy())==np.sign(fit.params[MODEL_FEATURES].to_numpy())})
    diagnostics=[]
    for i,c in enumerate(MODEL_FEATURES,1):
        r,p=spearmanr(train[c],train.score)
        diagnostics.append(dict(feature=c,spearman_r=float(r),p_value=float(p),
                                vif=float(variance_inflation_factor(X.to_numpy(),i))))
    diagnostics=pd.DataFrame(diagnostics)
    diagnostics["q_value_bh"]=multipletests(diagnostics.p_value,method="fdr_bh")[1]
    audit={"provenance":"synthetic reconstruction; not historical project results",
       "seed":seed,"train_sessions":len(train),"test_sessions":len(test),
       "participant_overlap":0,"baseline":baseline,"leakage_demonstration":leakage,
       "ordinal_sensitivity":{"converged":converged,"test_mae_expected_score":float(mean_absolute_error(yv,ordinal_pred)),
                              "note":"Model-based exploratory fit; not an ordered SEM or a reproduction of the original model."},
       "scaled_design_condition_number":float(np.linalg.cond(X.to_numpy())),
       "preprocessing":{"fit_on":"training only","p99_caps":prep.caps.to_dict()},
       "interpretation":"OLS approximates the ordinal score as equally spaced; coefficients are conditional associations, not causal lifts."}
    membership=df[["session_id","participant_key"]].copy()
    membership["split"]="test"
    membership.loc[tr,"split"]="train"
    return audit,{"coefficients":coefficients,"ordinal_sensitivity":ordinal_table,
                  "feature_diagnostics":diagnostics,"split_membership":membership}
