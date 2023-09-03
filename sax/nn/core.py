""" SAX Neural Network Core Utils """

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple, Union

import jax
import jax.numpy as jnp
from .utils import denormalize, normalize
from ..typing_ import Array, ComplexFloat


def preprocess(*params: ComplexFloat) -> ComplexFloat:
    """preprocess parameters

    > Note: (1) all arguments are first casted into the same shape. (2) then pairs
      of arguments are divided into each other to create relative arguments. (3) all
      arguments are then stacked into one big tensor
    """
    x = jnp.stack(jnp.broadcast_arrays(*params), -1)
    assert isinstance(x, jnp.ndarray)
    to_concatenate = [x]
    for i in range(1, x.shape[-1]):
        _x = jnp.roll(x, shift=i, axis=-1)
        to_concatenate.append(x / _x)
        to_concatenate.append(_x / x)
    x = jnp.concatenate(to_concatenate, -1)
    assert isinstance(x, jnp.ndarray)
    return x


def dense(
    weights: Dict[str, Array],
    *params: ComplexFloat,
    x_norm: Tuple[float, float] = (0.0, 1.0),
    y_norm: Tuple[float, float] = (0.0, 1.0),
    preprocess: Callable = preprocess,
    activation: Callable = jax.nn.leaky_relu,
) -> ComplexFloat:
    """simple dense neural network"""
    x_mean, x_std = x_norm
    y_mean, y_std = y_norm
    x = preprocess(*params)
    x = normalize(x, mean=x_mean, std=x_std)
    for i in range(len([w for w in weights if w.startswith("w")])):
        x = activation(x @ weights[f"w{i}"] + weights.get(f"b{i}", 0.0))
    y = denormalize(x, mean=y_mean, std=y_std)
    return y


def generate_dense_weights(
    key: Union[int, Array],
    sizes: Tuple[int, ...],
    input_names: Optional[Tuple[str, ...]] = None,
    output_names: Optional[Tuple[str, ...]] = None,
    preprocess=preprocess,
) -> Dict[str, ComplexFloat]:
    """Generate the weights for a dense neural network"""

    if isinstance(key, int):
        key = jax.random.PRNGKey(key)
    assert isinstance(key, jnp.ndarray)

    sizes = tuple(s for s in sizes)
    if input_names:
        arr = preprocess(*jnp.ones(len(input_names)))
        assert isinstance(arr, jnp.ndarray)
        sizes = (arr.shape[-1],) + sizes
    if output_names:
        sizes = sizes + (len(output_names),)

    keys = jax.random.split(key, 2 * len(sizes))
    rand = jax.nn.initializers.lecun_normal()
    weights = {}
    for i, (m, n) in enumerate(zip(sizes[:-1], sizes[1:])):
        weights[f"w{i}"] = rand(keys[2 * i], (m, n))
        weights[f"b{i}"] = rand(keys[2 * i + 1], (1, n)).ravel()

    return weights
