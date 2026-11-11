"""Evaluation and stratified, paired bootstrap at intervention-block granularity."""
from __future__ import annotations

from collections import Counter, defaultdict
import numpy as np
import pandas as pd
from .core import HYPOTHESES, DECISIONS, loss_matrix

POLICIES = [
    'B0_passive_P0','B1_passive_P1','B2_exhaustive','B3_random',
    'B4_entropy_greedy','B5_naive_independence','B6_EACLD'
]


def per_policy_metrics(df:pd.DataFrame) -> dict:
    total=len(df)
    exact=df['decision'].isin(HYPOTHESES)
    correct=df['correct_exact'].astype(bool)
    result={
        'episodes':total,
        'exact_accuracy':float(correct.mean()),
        'exact_coverage':float(exact.mean()),
        'abstention_rate':float(1-exact.mean()),
        'selective_accuracy':float(correct.sum()/exact.sum()) if exact.any() else float('nan'),
        'mean_realized_loss':float(df['realized_loss'].mean()),
        'mean_loss_plus_probe_cost':float((df['realized_loss']+df['cost_observed']).mean()),
        'mean_posterior_risk':float(df['risk_posterior'].mean()),
        'mean_probes':float(df['probe_count'].mean()),
        'mean_cost':float(df['cost_observed'].mean()),
        'mean_latency_ms':float(df['latency_ms'].mean()),
        'latency_p50_ms':float(df['latency_ms'].median()),
        'latency_p95_ms':float(df['latency_ms'].quantile(.95)),
        'mean_bytes':float(df['bytes'].mean()),
        'mean_brier':float(df['brier'].mean()),
    }
    precisions, recalls, f1s=[] ,[],[]
    for h in HYPOTHESES:
        tp=((df['decision']==h)&(df['cause']==h)).sum()
        fp=((df['decision']==h)&(df['cause']!=h)).sum()
        fn=((df['decision']!=h)&(df['cause']==h)).sum()
        prec=tp/(tp+fp) if tp+fp else 0.
        recall=tp/(tp+fn) if tp+fn else 0.
        f1=2*prec*recall/(prec+recall) if prec+recall else 0.
        precisions.append(prec); recalls.append(recall); f1s.append(f1)
    result.update({'macro_f1':float(np.mean(f1s)),'balanced_accuracy':float(np.mean(recalls))})
    return result


def add_truth_metrics(records: list[dict], private_index: dict, cfg: dict) -> pd.DataFrame:
    losses=loss_matrix(cfg)
    out=[]
    for r in records:
        truth=private_index[r['episode_id']]['cause']
        hidx=HYPOTHESES.index(truth)
        d=DECISIONS.index(r['decision'])
        realized=float(losses[d,hidx])
        probs=np.array(r['probabilities_h'], dtype=float)
        onehot=np.zeros(len(HYPOTHESES)); onehot[hidx]=1.
        row={k:v for k,v in r.items() if k != 'trace'}
        row['cause']=truth
        row['actual_unhealthy'] = private_index[r['episode_id']]['verifier_trust']=='unhealthy'
        row['correct_exact']=(r['decision']==truth)
        row['realized_loss']=realized
        row['brier']=float(np.sum((probs-onehot)**2))
        row['max_posterior']=float(probs.max())
        row['argmax_correct']=(HYPOTHESES[int(np.argmax(probs))]==truth)
        row['actions']='|'.join(r['actions'])
        row['probabilities_h']='|'.join(f'{float(p):.8f}' for p in probs)
        out.append(row)
    return pd.DataFrame(out)


def summarize(df:pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for name in POLICIES:
        row={'policy':name, **per_policy_metrics(df[df.policy==name])}
        rows.append(row)
    return pd.DataFrame(rows)


def stratified_paired_bootstrap(df: pd.DataFrame, cfg: dict, seed: int=123456) -> pd.DataFrame:
    """Vectorized paired block bootstrap, stratified by network mode.

    Each sampled block retains all four causes and all seven policies. Macro-F1
    is recomputed from aggregated TP/FP/FN, never averaged over blocks.
    """
    rng=np.random.default_rng(seed)
    n=int(cfg['bootstrap_replicates'])
    compared=['B1_passive_P1','B2_exhaustive','B3_random','B4_entropy_greedy','B5_naive_independence']
    keys=['realized_loss','loss_plus_cost','probe_count','cost_observed','latency_ms','brier']
    slots={mode:[] for mode in cfg['modes']}
    for mode in cfg['modes']:
        for block in sorted(df[df['mode']==mode]['block_id'].unique()):
            rows=[]
            for name in POLICIES:
                q=df[(df['block_id']==block)&(df['policy']==name)]
                assert len(q)==4, (block,name,len(q))
                vals=[float(q['realized_loss'].sum()),
                      float((q['realized_loss']+q['cost_observed']).sum()),
                      float(q['probe_count'].sum()),float(q['cost_observed'].sum()),
                      float(q['latency_ms'].sum()),float(q['brier'].sum())]
                for h in HYPOTHESES:
                    tp=((q['decision']==h)&(q['cause']==h)).sum()
                    fp=((q['decision']==h)&(q['cause']!=h)).sum()
                    fn=((q['decision']!=h)&(q['cause']==h)).sum()
                    vals.extend((tp,fp,fn))
                rows.append(vals)
            slots[mode].append(rows)
    by_mode={mode:np.array(slots[mode],dtype=float) for mode in cfg['modes']}
    # Bootstrap dimensions: replicate x policy x aggregate feature.
    aggregates=[]
    for mode in cfg['modes']:
        source=by_mode[mode]
        indexes=rng.integers(0,len(source),size=(n,len(source)))
        aggregates.append(source[indexes].sum(axis=1))
    agg=sum(aggregates)
    sample_size=4*sum(len(x) for x in slots.values())
    avg=agg[:,:,:len(keys)]/sample_size
    tp=agg[:,:,len(keys)::3];fp=agg[:,:,len(keys)+1::3];fn=agg[:,:,len(keys)+2::3]
    denom=2*tp+fp+fn
    f1=np.divide(2*tp,denom,out=np.zeros_like(tp),where=denom>0).mean(axis=2)
    metric_series={
       'macro_f1':f1,
       'mean_realized_loss':avg[:,:,0],
       'mean_loss_plus_probe_cost':avg[:,:,1],
       'mean_probes':avg[:,:,2],
       'mean_cost':avg[:,:,3],
       'mean_latency_ms':avg[:,:,4],
       'mean_brier':avg[:,:,5]
    }
    rows=[]
    best_idx=POLICIES.index('B6_EACLD')
    for comp in compared:
        j=POLICIES.index(comp)
        for metric,series in metric_series.items():
            diffs=series[:,best_idx]-series[:,j]
            rows.append({'comparison':f'B6_EACLD_minus_{comp}','metric':metric,
                         'estimate':float(diffs.mean()),
                         'ci_low_95':float(np.quantile(diffs,.025)),
                         'ci_high_95':float(np.quantile(diffs,.975)),
                         'bootstrap_replicates':n,
                         'resampling_unit':'paired intervention block stratified by network mode'})
    return pd.DataFrame(rows)


def conditional_summary(df:pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for (mode,policy),group in df.groupby(['mode','policy']):
        rows.append({'mode':mode,'policy':policy,**per_policy_metrics(group)})
    return pd.DataFrame(rows)


def confusion_matrix(df:pd.DataFrame, policy='B6_EACLD') -> pd.DataFrame:
    q=df[df.policy==policy].copy()
    q['decision_grouped']=q['decision'].where(q['decision'].isin(HYPOTHESES),'partial_or_unresolved')
    return pd.crosstab(q.cause,q.decision_grouped).reindex(index=HYPOTHESES,columns=HYPOTHESES+('partial_or_unresolved',),fill_value=0)


def probe_frequencies(df:pd.DataFrame) -> pd.DataFrame:
    out=[]
    for policy in POLICIES:
        rows=df[df.policy==policy]
        for action in ('reference_read','node_challenge','message_verify','sequence_check'):
            n=sum(action in a.split('|') for a in rows.actions)
            out.append({'policy':policy,'action':action,'episodes':len(rows),'executed_count':n,
                        'rate':float(n/len(rows))})
    return pd.DataFrame(out)


def selective_risk_curve(df:pd.DataFrame, policy: str) -> pd.DataFrame:
    q=df[df.policy==policy]
    rows=[]
    for threshold in np.linspace(.25,1.0,41):
        selected=q[q.max_posterior>=threshold]
        rows.append({'policy':policy,'threshold':float(threshold),
                     'coverage':float(len(selected)/len(q)),
                     'selective_argmax_error':float(1-selected.argmax_correct.mean()) if len(selected) else np.nan,
                     'selected_n':len(selected)})
    return pd.DataFrame(rows)
