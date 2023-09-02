""" SAX Loss Functions """

from typing import Dict

import jax.numpy as jnp
from ..typing_ import ComplexFloat


def mse(x: ComplexFloat, y: ComplexFloat) -> float:
    """mean squared error"""
    return ((x - y) ** 2).mean()


def huber_loss(x: ComplexFloat, y: ComplexFloat, delta: float = 0.5) -> float:
    """huber loss"""
    return ((delta**2) * ((1.0 + ((x - y) / delta) ** 2) ** 0.5 - 1.0)).mean()


def l2_reg(weights: Dict[str, ComplexFloat]) -> float:
    """L2 regularization loss"""
    numel = 0
    loss = 0.0
    for w in (v for k, v in weights.items() if k[0] in ("w", "b")):
        numel = numel + w.size
        loss = loss + (jnp.abs(w) ** 2).sum()
    return loss / numel
