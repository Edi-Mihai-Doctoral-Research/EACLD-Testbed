"""Unit and metamorphic tests for E0."""
import json
from pathlib import Path
import numpy as np
from eacld.core import *
from eacld.simulator import *

CFG=json.loads((Path(__file__).resolve().parents[1]/'config/e0_config.json').read_text())


def test_probabilities_normalize():
    for mode in CFG['modes']:
        for h in HYPOTHESES:
            for c in TRUST:
                for a in ACTIONS:
                    law=categorical_likelihood(CFG,a,h,c,mode)
                    assert abs(sum(law.values())-1)<1e-12
                    assert all(0<value<1 for value in law.values())


def test_p0_strictly_equal_within_block():
    sets=build_dataset(CFG)
    test=sets['test']
    assert len(test)==160
    assert len({e.public['block_id'] for e in test})==40
    for block in {e.public['block_id'] for e in test}:
        group=[e for e in test if e.public['block_id']==block]
        assert {e.private['cause'] for e in group}==set(HYPOTHESES)
        assert len({tuple(e.public['p0_temperature_trace_c']) for e in group})==1
        assert all(e.private['cause'] not in e.public['episode_id'] for e in group)


def test_fit_normalizes_and_does_not_use_test_truth():
    sets=build_dataset(CFG)
    model=fit_supervised_emission_model(CFG,sets['train'])
    for mode in CFG['modes']:
        assert 0<model.p_bad(mode)<1
        assert abs(model.state_prior(mode).sum()-1)<1e-10
        for h in HYPOTHESES:
            for c in TRUST:
                for a in ACTIONS:
                    assert np.isclose(model.emission(mode,a,h,c).sum(),1)


def test_bayes_expected_information_nonnegative():
    sets=build_dataset(CFG)
    model=fit_supervised_emission_model(CFG,sets['train'])
    for mode in CFG['modes']:
        b=model.state_prior(mode)
        for a in ACTIONS:
            v=action_value(b,model,loss_matrix(CFG),mode,a,False)
            assert v['risk_reduction']>=-1e-11
            assert v['information_bits']>=-1e-11


def test_policy_only_accesses_public_interface():
    sets=build_dataset(CFG)
    model=fit_supervised_emission_model(CFG,sets['train'])
    e=sets['test'][0]
    env=Environment(e)
    out=PolicyEngine(model,CFG).run('B6_EACLD',env,np.random.default_rng(123))
    assert out['episode_id']==e.public['episode_id']
    assert out['cost_nominal']<=CFG['decision']['max_cost']+1e-9
    assert out['probe_count']==len(out['actions'])==len(set(out['actions']))
    assert np.isclose(sum(out['probabilities_h']),1)
    assert 0<=out['probability_bad_verifier']<=1
    assert 'cause' not in out and 'verifier_trust' not in out


def test_common_trust_changes_joint_likelihood():
    sets=build_dataset(CFG)
    model=fit_supervised_emission_model(CFG,sets['train'])
    mode='degraded'
    full=model.state_prior(mode)
    naive=model.state_prior(mode)
    for a,z in [('message_verify','valid'),('sequence_check','fresh')]:
        full=model.posterior(full,mode,a,z,False)
        naive=model.posterior(naive,mode,a,z,True)
    # Naive model fails to update shared latent trust state.
    assert not np.allclose(full,naive)


def test_identifiability_for_equal_models():
    sets=build_dataset(CFG)
    model=fit_supervised_emission_model(CFG,sets['train'])
    # P0 equal by construction; ratio H1/H2 remains one before any probe.
    b=model.state_prior('nominal')
    assert np.isclose(b[0].sum()/b[1].sum(),1.)
    # Bayes update can only change odds when likelihood laws differ.
    mode='nominal'
    a='message_verify'; z='valid'
    assert abs(model.likelihood(mode,a,z)[0].mean()-model.likelihood(mode,a,z)[1].mean()) < .15


def test_reproducible_generation():
    a=build_dataset(CFG)
    b=build_dataset(CFG)
    assert a['test'][0].public==b['test'][0].public
    assert a['test'][0].private==b['test'][0].private
    assert a['test'][0].potential_outcomes==b['test'][0].potential_outcomes


def test_nonmyopic_complementarity():
    """Two crossed binary probes have no useful single-step attribution,
    but together identify all four causes. Bellman must not stop myopically.
    """
    from eacld.core import optimal_finite_horizon_action
    from copy import deepcopy
    cfg=deepcopy(CFG)
    sets=build_dataset(cfg)
    model=fit_supervised_emission_model(cfg,sets['train'])
    mode='nominal'
    # Replace two emissions with crossed, highly reliable partitions.
    for a, positive in [('reference_read',{'H1','H3'}),('node_challenge',{'H1','H4'})]:
        for h in HYPOTHESES:
            for c in TRUST:
                wanted='high' if h in positive else 'normal'
                other='normal' if wanted=='high' else 'high'
                model.emissions[mode][a][h][c]={wanted:.999,other:.0009,'unavailable':.0001}
    model.cfg['actions']['reference_read']['cost']=.015
    model.cfg['actions']['node_challenge']['cost']=.015
    belief=model.state_prior(mode)
    l=loss_matrix(cfg)
    # Single crossed probe is insufficient for individual or predefined class attribution.
    for a in ('reference_read','node_challenge'):
        v=action_value(belief,model,l,mode,a,False)
        assert v['net_value']<0.0
    choice,total,delta=optimal_finite_horizon_action(
        belief,model,l,mode,['reference_read','node_challenge'],False,.1,.07)
    assert choice in ('reference_read','node_challenge')
    assert delta>0
    assert total<bayes_decision(belief,l)[1]
