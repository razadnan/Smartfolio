from smartfolio.research.config import load_config, set_seed


def test_seed_and_retraining():
    cfg = load_config()
    assert cfg["seed"] == 42
    assert cfg["retraining"]["every_days"] == 21
    assert cfg["retraining"]["min_feedback_obs"] == 50


def test_set_seed_returns_seed():
    assert set_seed() == 42
    