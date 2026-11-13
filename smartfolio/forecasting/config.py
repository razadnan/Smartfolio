import os, random
from pathlib import Path
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]

def load_config(path="configs/config.yaml"):
    with open(ROOT / path) as f:
        return yaml.safe_load(f)

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass
