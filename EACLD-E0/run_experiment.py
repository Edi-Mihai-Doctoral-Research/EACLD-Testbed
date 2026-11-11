#!/usr/bin/env python3
"""End-to-end EACLD-E0: simulate, fit on training only, evaluate, bootstrap, plot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eacld.core import HYPOTHESES, ACTIONS, PolicyEngine
from eacld.simulator import build_dataset, fit_supervised_emission_model, save_dataset, Environment
from eacld.evaluation import (POLICIES, add_truth_metrics, summarize,
    stratified_paired_bootstrap, conditional_summary, confusion_matrix,
    probe_frequencies, selective_risk_curve)


def write_json(path, value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def stable_rng(seed, eid, policy):
    hash_value=int.from_bytes(hashlib.sha256((eid+'|'+policy).encode()).digest()[:8],'little')
    return np.random.default_rng((seed+hash_value)%2**63)


def run_policies(episodes, fitted, cfg, include_trace=False):
    engine=PolicyEngine(fitted,cfg)
    records=[]
    traces=[]
    for e in sorted(episodes,key=lambda e:e.public['episode_id']):
        for policy in POLICIES:
            r=engine.run(policy,Environment(e),stable_rng(cfg['seed'],e.public['episode_id'],policy))
            traces.append({'episode_id':r['episode_id'],'policy':policy,'stop_reason':r['stop_reason'],
                           'trace':r['trace'],'final_posterior_h':r['probabilities_h']})
            records.append(r)
    return records,traces


def create_figures(results, out_dir):
    out=Path(out_dir);out.mkdir(exist_ok=True,parents=True)
    chart_names={'B0_passive_P0':'B0 P0', 'B1_passive_P1':'B1 P1',
       'B2_exhaustive':'B2 exhaustive', 'B3_random':'B3 random',
       'B4_entropy_greedy':'B4 entropy', 'B5_naive_independence':'B5 naive',
       'B6_EACLD':'B6 EACLD'}
    d=results['summary']
    fig,ax=plt.subplots(figsize=(8.0,5.3))
    offsets={'B5_naive_independence':(5,18),'B6_EACLD':(5,-21),
             'B2_exhaustive':(-75,-17),'B3_random':(-32,13)}
    for _,r in d.iterrows():
        ax.scatter(r.mean_cost,r.macro_f1,s=65)
        ax.annotate(chart_names[r.policy], (r.mean_cost,r.macro_f1),
                    xytext=offsets.get(r.policy,(5,6)),textcoords='offset points',fontsize=8)
    ax.set(xlabel='Mean realized probe cost (normalized units per episode)',ylabel='Macro-F1 (exact causal attribution)',
            title='E0: diagnostic performance and active-probing cost')
    ax.set_ylim(-.05,1.05)
    ax.grid(alpha=.22);fig.tight_layout();fig.savefig(out/'01_performance_vs_cost.png',dpi=170);plt.close(fig)

    fig,ax=plt.subplots(figsize=(8.0,5.3))
    for policy in ('B0_passive_P0','B1_passive_P1','B5_naive_independence','B6_EACLD'):
        curve=selective_risk_curve(results['df'],policy)
        curve=curve[curve.selected_n>=5]
        ax.plot(curve.coverage,curve.selective_argmax_error,label=chart_names[policy],marker='.',markersize=3)
    ax.set(xlabel='Fraction of episodes above posterior-confidence threshold',
            ylabel='Error rate for maximum-posterior hypothesis',
            title='E0: selective risk–coverage curves',xlim=(0,1),ylim=(0,1))
    ax.legend(fontsize=8);ax.grid(alpha=.22);fig.tight_layout();fig.savefig(out/'02_risk_coverage.png',dpi=170);plt.close(fig)

    cm=confusion_matrix(results['df'])
    fig,ax=plt.subplots(figsize=(7.6,4.8))
    im=ax.imshow(cm.to_numpy(),cmap='Blues',aspect='auto')
    ax.set(xticks=np.arange(cm.shape[1]),yticks=np.arange(cm.shape[0]),
           xticklabels=['H1','H2','H3','H4','Partial / unresolved'],yticklabels=HYPOTHESES,
           xlabel='Issued diagnosis',ylabel='Injected cause',title='E0: EACLD exact and partial decisions')
    for (i,j),v in np.ndenumerate(cm.to_numpy()):
        ax.text(j,i,str(v),ha='center',va='center',color='white' if v>max(1,cm.to_numpy().max()/2) else 'black')
    ax.tick_params(axis='x',labelrotation=15)
    fig.colorbar(im,ax=ax,shrink=.78);fig.tight_layout();fig.savefig(out/'03_confusion_EACLD.png',dpi=170);plt.close(fig)

    freq=results['probe_frequencies']
    active=['B2_exhaustive','B3_random','B4_entropy_greedy','B5_naive_independence','B6_EACLD']
    ff=freq[freq.policy.isin(active)].pivot(index='policy',columns='action',values='rate').reindex(active)
    fig,ax=plt.subplots(figsize=(8.5,5.0))
    x=np.arange(len(active));w=.20
    for j,action in enumerate(ACTIONS):
        ax.bar(x+(j-1.5)*w,ff[action].to_numpy(),width=w,label=action.replace('_',' '))
    ax.set(xticks=x,xticklabels=[chart_names[p] for p in active],ylim=(0,1),ylabel='Fraction of episodes',
           title='E0: frequency of each diagnostic probe')
    ax.legend(fontsize=8,ncol=2);ax.grid(axis='y',alpha=.22);fig.tight_layout();fig.savefig(out/'04_probe_usage.png',dpi=170);plt.close(fig)

    fig,ax=plt.subplots(figsize=(8.3,4.8))
    series=[results['df'][results['df'].policy==p].latency_ms.to_numpy() for p in active]
    ax.boxplot(series,tick_labels=[chart_names[p] for p in active],showfliers=False)
    ax.set(ylabel='Cumulative simulated probing latency (ms)',title='E0: probing-latency distribution')
    ax.grid(axis='y',alpha=.22);fig.tight_layout();fig.savefig(out/'05_latency_distribution.png',dpi=170);plt.close(fig)

    conditional=results['conditional']
    fig,ax=plt.subplots(figsize=(8.2,4.8))
    modes=['nominal','degraded']
    xx=np.arange(2);width=.17
    for j,p in enumerate(['B1_passive_P1','B4_entropy_greedy','B5_naive_independence','B6_EACLD']):
        ss=conditional[conditional.policy==p].set_index('mode').reindex(modes)
        ax.bar(xx+(j-1.5)*width,ss.mean_brier.to_numpy(),width=width,label=chart_names[p])
    ax.set(xticks=xx,xticklabels=['Nominal','Degraded'],ylabel='Multiclass Brier score (lower is better)',
           title='E0: posterior calibration under network degradation')
    ax.legend(fontsize=8);ax.grid(axis='y',alpha=.22);fig.tight_layout();fig.savefig(out/'06_brier_by_mode.png',dpi=170);plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='config/e0_config.json')
    parser.add_argument('--out',default='.')
    parser.add_argument('--bootstrap',type=int,default=None)
    args=parser.parse_args()
    root=Path(args.out); root.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    if args.bootstrap is not None:cfg['bootstrap_replicates']=args.bootstrap
    splits=build_dataset(cfg)
    save_dataset(splits,root/'data')
    model=fit_supervised_emission_model(cfg,splits['train'])
    write_json(root/'results'/'fitted_model.json',{'priors':model.priors,'emissions':model.emissions})
    write_json(root/'results'/'experiment_manifest.json',{
        'id':cfg['experiment_id'],'seed':cfg['seed'],'hypotheses':HYPOTHESES,
        'train_episodes':len(splits['train']), 'validation_episodes':len(splits['validation']),
        'test_episodes':len(splits['test']),'test_blocks':len(splits['test'])//4,
        'python_version':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
        'fitted_model':'TRAIN ONLY - supervised emissions using injected H and C labels',
        'validation_use':'untuned holdout diagnostic evaluation',
        'test_use':'primary E0 evaluation; causal labels available to evaluator only',
        'modes':cfg['modes'],'calibration':cfg['calibration'],'bootstrap_replicates':cfg['bootstrap_replicates']
    })
    for split in ('validation','test'):
        raw, traces=run_policies(splits[split],model,cfg)
        private={e.private['episode_id']:e.private for e in splits[split]}
        df=add_truth_metrics(raw,private,cfg)
        (root/'results').mkdir(parents=True,exist_ok=True)
        df.to_csv(root/'results'/f'{split}_per_episode.csv',index=False)
        pd.DataFrame(summarize(df)).to_csv(root/'results'/f'{split}_summary.csv',index=False)
        with (root/'results'/f'{split}_decision_traces.jsonl').open('w',encoding='utf-8') as file:
            for item in traces:file.write(json.dumps(item,ensure_ascii=False)+'\n')
        if split=='test':
            boot=stratified_paired_bootstrap(df,cfg)
            boot.to_csv(root/'results'/'test_paired_bootstrap_95ci.csv',index=False)
            conditional=conditional_summary(df)
            conditional.to_csv(root/'results'/'test_summary_by_mode.csv',index=False)
            cm=confusion_matrix(df)
            cm.to_csv(root/'results'/'test_confusion_B6.csv')
            freqs=probe_frequencies(df)
            freqs.to_csv(root/'results'/'test_probe_frequencies.csv',index=False)
            res={'summary':summarize(df),'df':df,'conditional':conditional,'probe_frequencies':freqs}
            create_figures(res,root/'figures')
    print('\nPRIMARY TEST RESULTS (160 episodes):')
    d=summarize(pd.read_csv(root/'results'/'test_per_episode.csv'))
    print(d[['policy','macro_f1','exact_coverage','mean_realized_loss','mean_loss_plus_probe_cost','mean_probes','mean_cost','latency_p95_ms','mean_brier']].to_string(index=False,float_format=lambda x:f'{x:.4f}'))
    print('\nSaved in:',root.resolve())

if __name__=='__main__':main()
