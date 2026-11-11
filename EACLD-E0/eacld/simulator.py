"""Paired intervention blocks and synthetic, reproducible probe responses.

Each episode has four pre-sampled potential outcomes. PolicyEngine only sees an
outcome if it calls Environment.execute(action). The paired P0 measurement trace
is IDENTICAL for H1-H4 in each block; hidden physical truth is different.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from collections import Counter
from typing import Dict
import numpy as np

from .core import HYPOTHESES, TRUST, ACTIONS, OUTCOMES, categorical_likelihood, FittedModel


@dataclass
class Episode:
    public: dict
    private: dict
    potential_outcomes: dict


class Environment:
    """A narrow probe-execution interface, with no access to causal labels."""
    def __init__(self, episode: Episode):
        self.public = episode.public
        self.__potential = episode.potential_outcomes
        self.__observed_actions = set()

    def execute(self, action: str) -> tuple[str, dict]:
        if action not in ACTIONS:
            raise ValueError(f'Unsupported probe: {action}')
        if action in self.__observed_actions:
            raise ValueError(f'Duplicate probe: {action}')
        self.__observed_actions.add(action)
        item = self.__potential[action]
        return item['outcome'], {k: item[k] for k in ('cost','latency_ms','bytes')}


def sample_discrete(distribution: dict, rng: np.random.Generator) -> str:
    vals = tuple(distribution.keys())
    return str(rng.choice(vals, p=[distribution[v] for v in vals]))


def build_dataset(cfg: dict) -> dict[str,list[Episode]]:
    rng = np.random.default_rng(cfg['seed'])
    output = {}
    for split, nblocks in cfg['blocks_per_mode'].items():
        episodes = []
        for mode in cfg['modes']:
            for block_idx in range(nblocks):
                block_id = f'{split}_{mode}_B{block_idx:03d}'
                # Matched P0 process trace is sampled once per block, then reused for all causes.
                p0_waveform = np.round(29 + rng.normal(0, 0.13, size=12), 3).tolist()
                mac_covered = bool(rng.random() < cfg['simulation']['passive_coverage_mac'][mode])
                seq_covered = bool(rng.random() < cfg['simulation']['passive_coverage_seq'][mode])
                order = rng.permutation(HYPOTHESES)
                for slot, h in enumerate(order):
                    compromised = bool(rng.random() < cfg['simulation']['prior_bad_verifier'][mode])
                    trust = TRUST[1] if compromised else TRUST[0]
                    episode_id = f'{block_id}_E{slot:02d}'
                    passive = {}
                    for a, field, covered in [('message_verify', 'passive_mac', mac_covered),
                                               ('sequence_check', 'passive_sequence', seq_covered)]:
                        law = categorical_likelihood(cfg, a, h, trust, mode)
                        passive[field] = sample_discrete(law, rng) if covered else None
                    potential = {}
                    for a in ACTIONS:
                        law = categorical_likelihood(cfg, a, h, trust, mode)
                        outcome = sample_discrete(law, rng)
                        latency_base = cfg['actions'][a]['latency_ms'][mode]
                        latency = float(latency_base * rng.lognormal(-.5 * .24**2, .24))
                        cost = float(cfg['actions'][a]['cost'] * rng.lognormal(-.5 * .11**2, .11))
                        actual_temp = None
                        if a in ('reference_read', 'node_challenge') and outcome != 'unavailable':
                            target = 29 if outcome == 'high' else 22
                            actual_temp = float(round(rng.normal(target, 0.28 if a == 'reference_read' else 0.36),3))
                        potential[a] = {
                            'outcome': outcome, 'cost': cost, 'latency_ms': latency,
                            'bytes': int(cfg['actions'][a]['bytes']), 'numeric_temperature_c': actual_temp
                        }
                    public = {
                        'episode_id':episode_id, 'block_id':block_id, 'mode':mode,
                        'p0_temperature_trace_c':p0_waveform,
                        'passive':passive
                    }
                    private = {
                        'episode_id':episode_id, 'block_id':block_id, 'split':split,
                        'cause':h, 'verifier_trust':trust, 'mode':mode,
                        'physical_temp_c':29 if h == 'H1' else 22,
                        'current_node_temp_c':29 if h in ('H1','H2') else 22,
                        'platform_temp_c':29,
                        'intervention':{'H1':'physical_heating','H2':'sensor_bias',
                                        'H3':'post_authentication_tampering','H4':'replay_of_old_valid_message'}[h]
                    }
                    episodes.append(Episode(public, private, potential))
        output[split] = episodes
    return output


def fit_supervised_emission_model(cfg: dict, training: list[Episode]) -> FittedModel:
    """Calibration uses TRAIN labels and injected verifier-state labels only.

    The test-set generator and latent truth are never passed to the policy engine.
    Dirichlet smoothing prevents the impossible zero-likelihood artefact.
    """
    alpha = cfg['calibration']['dirichlet_alpha']
    priors = {}
    emissions = {}
    for mode in cfg['modes']:
        subset = [e for e in training if e.private['mode'] == mode]
        n_bad = sum(e.private['verifier_trust'] == 'unhealthy' for e in subset)
        a, b = cfg['calibration']['prior_beta_alpha'], cfg['calibration']['prior_beta_beta']
        priors[mode] = float((n_bad+a) / (len(subset)+a+b))
        emissions[mode] = {}
        for action in ACTIONS:
            emissions[mode][action] = {}
            for h in HYPOTHESES:
                emissions[mode][action][h] = {}
                for trust in TRUST:
                    selected = [e.potential_outcomes[action]['outcome'] for e in subset
                                if e.private['cause'] == h and e.private['verifier_trust'] == trust]
                    counts = Counter(selected)
                    den = len(selected) + alpha*len(OUTCOMES[action])
                    emissions[mode][action][h][trust] = {
                        z: float((counts[z]+alpha)/den) for z in OUTCOMES[action]
                    }
    return FittedModel(priors=priors, emissions=emissions, cfg=cfg)


def save_dataset(splits:dict, directory):
    """Data segregation for reproducibility and leakage tests."""
    from pathlib import Path
    import pandas as pd
    directory = Path(directory)
    (directory/'public').mkdir(parents=True, exist_ok=True)
    (directory/'private').mkdir(parents=True, exist_ok=True)
    for split, episodes in splits.items():
        rows_public = []
        rows_private = []
        probe_rows = []
        for e in episodes:
            rows_public.append({
                'episode_id': e.public['episode_id'], 'block_id': e.public['block_id'],
                'mode':e.public['mode'], 'passive_mac':e.public['passive']['passive_mac'],
                'passive_sequence':e.public['passive']['passive_sequence'],
                'p0_trace_json':json.dumps(e.public['p0_temperature_trace_c'])
            })
            rows_private.append(e.private)
            for a, values in e.potential_outcomes.items():
                probe_rows.append({'episode_id':e.public['episode_id'], 'action':a, **values})
        pd.DataFrame(rows_public).to_csv(directory/'public'/f'{split}_public.csv',index=False)
        pd.DataFrame(rows_private).to_csv(directory/'private'/f'{split}_ground_truth.csv',index=False)
        pd.DataFrame(probe_rows).to_csv(directory/'private'/f'{split}_potential_outcomes.csv',index=False)
