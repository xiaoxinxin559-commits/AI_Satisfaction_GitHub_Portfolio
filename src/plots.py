"""Four separate Matplotlib figures, using default chart colors and styling."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def make_plots(df: pd.DataFrame, model: dict, coefficients: pd.DataFrame, out: Path) -> None:
    out.mkdir(parents=True,exist_ok=True)
    # No user-specific fonts or remote assets are required.
    fig,ax=plt.subplots(figsize=(7.8,4.5))
    frequency=df.score.value_counts().reindex(range(1,6),fill_value=0)
    bars=ax.bar(frequency.index,frequency.values)
    ax.bar_label(bars,padding=4)
    ax.set(xticks=range(1,6),xlabel="Satisfaction score (ordered categories)",
           ylabel="Synthetic sessions",title="Score distribution | SYNTHETIC DATA")
    ax.set_ylim(0,max(frequency.values)*1.18)
    fig.tight_layout();fig.savefig(out/"score_distribution.png",dpi=160);plt.close(fig)

    fig,ax=plt.subplots(figsize=(7.8,4.5))
    values=[model["baseline"]["test_r2"],model["leakage_demonstration"]["test_r2"]]
    bars=ax.bar(["Pre-outcome features","+ Post-score tag (INVALID)"],values)
    ax.bar_label(bars,labels=[f"{v:.3f}" for v in values],padding=5)
    ax.set(ylabel="Holdout R² on the same synthetic score",title="Why a better score can be misleading | DEMO")
    ax.set_ylim(min(0,min(values)-.05),max(values)+.16)
    fig.tight_layout();fig.savefig(out/"leakage_demo.png",dpi=160);plt.close(fig)

    fig,ax=plt.subplots(figsize=(8.7,5.1))
    c=coefficients.sort_values("standardized_beta").copy()
    labels={"quick_result_count":"Quick-result displays", "consult_result_count":"Consultation-result displays",
            "followup_shown_count":"Follow-up prompts shown", "followup_click_count":"Follow-up clicks",
            "is_returning":"Returning-user flag", "age_level":"Age-group ordinal approximation", "age_unknown":"Age unknown"}
    beta=c.standardized_beta.to_numpy()
    error=np.vstack([beta-c.ci_low.to_numpy(),c.ci_high.to_numpy()-beta])
    ax.errorbar(beta,np.arange(len(c)),xerr=error,fmt="o",capsize=4)
    ax.axvline(0,linestyle="--",linewidth=1)
    ax.set(yticks=np.arange(len(c)),yticklabels=[labels[x] for x in c.feature],
           xlabel="Standardized coefficient; 95% participant-clustered CI",
           title="Conditional associations, NOT causal lift | SYNTHETIC")
    fig.tight_layout();fig.savefig(out/"coefficient_associations.png",dpi=160);plt.close(fig)

    paired=df.loc[df.expert_score.notna()].copy()
    cells=[((paired.score>=4)&(paired.expert_score>=2)).sum(),
           ((paired.score>=4)&(paired.expert_score<2)).sum(),
           ((paired.score<4)&(paired.expert_score>=2)).sum(),
           ((paired.score<4)&(paired.expert_score<2)).sum()]
    fig,ax=plt.subplots(figsize=(8.6,4.6))
    names=["User high\nReview high","User high\nReview below threshold",
           "User below threshold\nReview high","Both below\nthreshold"]
    bars=ax.bar(names,cells);ax.bar_label(bars,padding=4)
    ax.set(ylabel="Paired synthetic sessions",title=f"Two signals answer different questions | DEMO n={len(paired)}")
    ax.set_ylim(0,max(cells)*1.2)
    fig.tight_layout();fig.savefig(out/"dual_signal_review.png",dpi=160);plt.close(fig)
