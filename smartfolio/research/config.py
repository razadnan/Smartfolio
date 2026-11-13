import random
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path=None):
    path = path or ROOT / "configs" / "config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def set_seed(seed=None):
    if seed is None:
        seed = load_config()["seed"]
    random.seed(seed)
    np.random.seed(seed)
    return seed
