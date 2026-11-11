"""Finite-state exact inference, Bayesian decision theory, and adaptive policies.

Ground truth never appears in any decision/inference API. A PolicyEngine can
interrogate a supplied Environment only through the action-specific .execute().
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Mapping, Optional
import numpy as np

HYPOTHESES = ('H1', 'H2', 'H3', 'H4')
TRUST = ('healthy', 'unhealthy')
ACTIONS = ('reference_read', 'node_challenge', 'message_verify', 'sequence_check')
OUTCOMES = {
    'reference_read': ('normal', 'high', 'unavailable'),
    'node_challenge': ('normal', 'high', 'unavailable'),
    'message_verify': ('valid', 'invalid', 'unavailable'),
    'sequence_check': ('fresh', 'stale', 'unavailable'),
}
SECURITY_TO_PASSIVE = {'message_verify': 'passive_mac', 'sequence_check': 'passive_sequence'}
DECISIONS = HYPOTHESES + ('H1_or_H2', 'H3_or_H4', 'unresolved')


def true_status(action: str, h: str) -> str:
    if action == 'reference_read':
        return 'high' if h == 'H1' else 'normal'
    if action == 'node_challenge':
        return 'high' if h in ('H1', 'H2') else 'normal'
    if action == 'message_verify':
        return 'invalid' if h == 'H3' else 'valid'
    if action == 'sequence_check':
        return 'stale' if h == 'H4' else 'fresh'
    raise KeyError(action)


def opposite_status(action: str, status: str) -> str:
    vals = OUTCOMES[action][:2]
    return vals[1] if status == vals[0] else vals[0]


def categorical_likelihood(cfg: dict, action: str, h: str, trust: str, mode: str) -> Dict[str, float]:
    """Simulation-only data-generating laws, not fitted diagnostic parameters."""
    c = cfg['simulation']
    correct = true_status(action, h)
    if action == 'reference_read':
        success = c['reference_correct'][mode]
        unavailable = c['reference_unavailable'][mode]
    elif action == 'node_challenge':
        success = c['node_correct'][mode]
        unavailable = c['node_unavailable'][mode]
    else:
        unavailable = c['security_unavailable_good'][mode] if trust == 'healthy' else c['security_unavailable_bad'][mode]
        if trust == 'healthy':
            success = c['security_good_correct'][mode]
        elif correct in ('valid', 'fresh'):
            success = c['security_bad_true_positive_detection'][mode]
        else:
            success = c['security_bad_true_negative_detection'][mode]
    result = {key: 0.0 for key in OUTCOMES[action]}
    result['unavailable'] = unavailable
    result[correct] = (1 - unavailable) * success
    result[opposite_status(action, correct)] = (1 - unavailable) * (1 - success)
    assert abs(sum(result.values()) - 1) < 1e-12
    return result


def loss_matrix(cfg: dict) -> np.ndarray:
    p = cfg['decision']
    mat = np.zeros((len(DECISIONS), len(HYPOTHESES)), dtype=float)
    for j, h in enumerate(HYPOTHESES):
        for i, d in enumerate(DECISIONS):
            if d == 'unresolved':
                mat[i, j] = p['unresolved_loss']
            elif d == h:
                mat[i, j] = 0.0
            elif d in ('H1_or_H2', 'H3_or_H4'):
                allowed = ('H1','H2') if d == 'H1_or_H2' else ('H3','H4')
                mat[i, j] = p['class_correct_loss'] if h in allowed else p['class_incorrect_loss']
            elif h in ('H3','H4') and d in ('H1','H2'):
                mat[i, j] = p['missed_attack_loss']
            elif h in ('H1','H2') and d in ('H3','H4'):
                mat[i, j] = p['false_attack_loss']
            else:
                mat[i, j] = p['wrong_label_loss']
    return mat


@dataclass
class FittedModel:
    priors: dict
    emissions: dict
    cfg: dict

    def p_bad(self, mode: str) -> float:
        return float(self.priors[mode])

    def emission(self, mode: str, a: str, h: str, trust: str) -> np.ndarray:
        d = self.emissions[mode][a][h][trust]
        return np.array([d[z] for z in OUTCOMES[a]], dtype=float)

    def state_prior(self, mode: str) -> np.ndarray:
        cp = self.p_bad(mode)
        return np.array([[0.25 * (1 - cp), 0.25 * cp] for _ in HYPOTHESES])

    def likelihood(self, mode: str, a: str, z: str, naive_independent: bool = False) -> np.ndarray:
        """Matrix 4 x 2, or one marginal likelihood replicated along trust axis."""
        idx = OUTCOMES[a].index(z)
        arr = np.array([[self.emission(mode, a, h, c)[idx] for c in TRUST] for h in HYPOTHESES])
        if naive_independent:
            cp = self.p_bad(mode)
            marginal = arr[:, 0] * (1 - cp) + arr[:, 1] * cp
            arr = np.column_stack([marginal, marginal])
        return arr

    def posterior(self, belief: np.ndarray, mode: str, action: str, outcome: str, naive: bool = False) -> np.ndarray:
        like = self.likelihood(mode, action, outcome, naive_independent=naive)
        unnorm = belief * like
        den = unnorm.sum()
        if den <= 0:
            raise ArithmeticError('Zero posterior normalization constant')
        return unnorm / den

    def initial_posterior(self, mode: str, passive: Mapping[str, Optional[str]], naive: bool = False) -> np.ndarray:
        b = self.state_prior(mode)
        for a, field in SECURITY_TO_PASSIVE.items():
            if passive.get(field) is not None:
                b = self.posterior(b, mode, a, passive[field], naive)
        return b

    def predictive(self, belief: np.ndarray, mode: str, action: str, naive: bool = False) -> np.ndarray:
        p = np.array([(belief * self.likelihood(mode, action, z, naive)).sum() for z in OUTCOMES[action]])
        return p / p.sum()


def marginal_h(b: np.ndarray) -> np.ndarray:
    return b.sum(axis=1)


def bayes_decision(b: np.ndarray, losses: np.ndarray) -> tuple[str, float]:
    risk = losses @ marginal_h(b)
    idx = int(np.argmin(risk))
    return DECISIONS[idx], float(risk[idx])


def information_bits(b: np.ndarray, m: FittedModel, mode: str, a: str, naive: bool) -> float:
    def entropy(vec):
        vec = vec[vec > 0]
        return float(-(vec * np.log2(vec)).sum())
    prior = entropy(marginal_h(b))
    pred = m.predictive(b, mode, a, naive)
    after = 0.0
    for z, pz in zip(OUTCOMES[a], pred):
        if pz > 0:
            post = m.posterior(b, mode, a, z, naive)
            after += float(pz) * entropy(marginal_h(post))
    return max(0., prior - after)


def action_value(b: np.ndarray, m: FittedModel, losses: np.ndarray, mode: str, a: str, naive: bool) -> dict:
    _, risk = bayes_decision(b, losses)
    probabilities = m.predictive(b, mode, a, naive)
    expected = 0.0
    for z, prob in zip(OUTCOMES[a], probabilities):
        if prob > 0:
            post = m.posterior(b, mode, a, z, naive)
            _, r = bayes_decision(post, losses)
            expected += prob * r
    information = information_bits(b, m, mode, a, naive)
    cost = m.cfg['actions'][a]['cost']
    return {
        'expected_risk': float(expected),
        'risk_reduction': float(risk - expected),
        'information_bits': float(information),
        'nominal_cost': float(cost),
        'net_value': float(risk - expected - cost),
    }


def optimal_finite_horizon_action(belief: np.ndarray, model: FittedModel,
                                  losses: np.ndarray, mode: str,
                                  candidates: list[str], naive: bool,
                                  remaining_cost: float,
                                  risk_target: float) -> tuple[Optional[str], float, float]:
    """Exact Bellman optimization of expected terminal diagnostic loss + probe costs.

    For E0 there are at most four non-repeating probes. Full joint beliefs have
    eight states (four causes x two verifier states); conditional independence
    given (H,C) makes each observed-outcome set sufficient, allowing memoization.

    V(b,S) = min{R(b), min_a [c(a) + sum_z P(z|b,a) V(b_az,S minus {a})]}.
    Finite-horizon decision is non-myopic; future complementary probe value can
    justify a first action that has negligible immediate risk reduction.
    """
    options = tuple(candidates)
    current_risk = bayes_decision(belief, losses)[1]
    @lru_cache(None)
    def evaluate(observed: tuple[tuple[str, str], ...]):
        b = belief
        spent = 0.0
        seen = set()
        for action, result in observed:
            b = model.posterior(b, mode, action, result, naive)
            spent += model.cfg['actions'][action]['cost']
            seen.add(action)
        decision, risk = bayes_decision(b, losses)
        if risk <= risk_target:
            return risk, None
        best_value, best_action = risk, None
        for a in options:
            if a in seen:
                continue
            cost = float(model.cfg['actions'][a]['cost'])
            if spent + cost > remaining_cost + 1e-10:
                continue
            pz = model.predictive(b, mode, a, naive)
            future = 0.0
            for z, probability in zip(OUTCOMES[a], pz):
                if probability <= 0:
                    continue
                new_observed = tuple(sorted(observed + ((a, z),)))
                cost_to_go, _ = evaluate(new_observed)
                future += probability * cost_to_go
            value = cost + future
            if value < best_value - 1e-10:
                best_value, best_action = value, a
        return best_value, best_action
    best_total, action = evaluate(())
    return action, float(best_total), float(current_risk - best_total)


class PolicyEngine:
    def __init__(self, model: FittedModel, cfg: dict):
        self.model = model
        self.cfg = cfg
        self.loss = loss_matrix(cfg)

    def run(self, name: str, environment, rng: np.random.Generator) -> dict:
        """Only environment.public contains public observations, never H/C truth."""
        public = environment.public
        mode = public['mode']
        naive = name == 'B5_naive_independence'
        if name == 'B0_passive_P0':
            belief = self.model.state_prior(mode)
        else:
            belief = self.model.initial_posterior(mode, public['passive'], naive)

        selected = []
        trace = []
        cost_observed, cost_nominal, latency_ms, bytes_used = 0., 0., 0., 0
        can_act = name not in ('B0_passive_P0', 'B1_passive_P1')
        stop_reason = 'passive_only'
        max_steps = len(ACTIONS) + 1
        for step in range(max_steps):
            decision, risk = bayes_decision(belief, self.loss)
            candidates = [a for a in ACTIONS if a not in selected and
                          public['passive'].get(SECURITY_TO_PASSIVE.get(a,'')) in (None, 'unavailable')]
            remaining = self.cfg['decision']['max_cost'] - cost_nominal
            candidates = [a for a in candidates if self.cfg['actions'][a]['cost'] <= remaining + 1e-10]
            if not can_act:
                break
            if name != 'B2_exhaustive' and risk <= self.cfg['decision']['risk_target']:
                stop_reason = 'risk_target'
                break
            if not candidates:
                stop_reason = 'no_actions_or_budget'
                break
            values = {a: action_value(belief, self.model, self.loss, mode, a, naive) for a in candidates}
            if name in ('B6_EACLD', 'B5_naive_independence'):
                chosen, planned_total, planned_improvement = optimal_finite_horizon_action(
                    belief, self.model, self.loss, mode, candidates, naive,
                    remaining, self.cfg['decision']['risk_target'])
                if chosen is None:
                    stop_reason = 'nonpositive_dynamic_value'
                    break
                values['_bellman_planner'] = {'optimal_expected_loss_plus_cost': planned_total,
                                               'expected_improvement': planned_improvement}
            elif name == 'B4_entropy_greedy':
                chosen = max(candidates, key=lambda a: values[a]['information_bits'] / max(values[a]['nominal_cost'], 1e-10))
                if values[chosen]['information_bits'] <= 1e-8:
                    stop_reason = 'noninformative'
                    break
            elif name == 'B3_random':
                chosen = str(rng.choice(candidates))
            elif name == 'B2_exhaustive':
                chosen = candidates[0]
            else:
                raise ValueError(f'Unknown policy: {name}')
            z, metadata = environment.execute(chosen)
            next_belief = self.model.posterior(belief, mode, chosen, z, naive)
            selected.append(chosen)
            cost_nominal += float(self.cfg['actions'][chosen]['cost'])
            cost_observed += float(metadata['cost'])
            latency_ms += float(metadata['latency_ms'])
            bytes_used += int(metadata['bytes'])
            trace.append({
                'step': step + 1, 'action': chosen, 'observation': z,
                'risk_before': risk, 'risk_after': bayes_decision(next_belief, self.loss)[1],
                'action_values': values,
                'prior_h': marginal_h(belief).tolist(), 'posterior_h': marginal_h(next_belief).tolist(),
                'prior_unhealthy': float(belief[:, 1].sum()),
                'posterior_unhealthy': float(next_belief[:, 1].sum()),
                'nominal_cost': float(self.cfg['actions'][chosen]['cost']),
                'observed_cost': float(metadata['cost']),
                'latency_ms': float(metadata['latency_ms']), 'bytes': int(metadata['bytes'])
            })
            belief = next_belief
        else:
            stop_reason = 'step_limit'

        decision, risk = bayes_decision(belief, self.loss)
        if name == 'B2_exhaustive':
            stop_reason = 'exhaustive_complete' if len(selected) > 0 else 'no_actions'
        return {
            'policy': name, 'episode_id': public['episode_id'], 'block_id': public['block_id'],
            'mode': mode, 'decision': decision, 'risk_posterior': risk,
            'probabilities_h': marginal_h(belief).tolist(), 'probability_bad_verifier': float(belief[:,1].sum()),
            'cost_observed': cost_observed, 'cost_nominal': cost_nominal, 'latency_ms': latency_ms,
            'bytes': bytes_used, 'probe_count': len(selected), 'actions': selected,
            'stop_reason': stop_reason, 'trace': trace
        }
