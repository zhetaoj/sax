""" Patched Datastructures for SAX """

from __future__ import annotations

import re
from textwrap import dedent

from fastcore.basics import patch_to
from .typing_ import is_complex_float, is_float

try:
    import jax.numpy as jnp
    from flax.core import FrozenDict
    from jaxlib.xla_extension import DeviceArray  # type: ignore

    JAX_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    import numpy as jnp

    DeviceArray = jnp.ndarray
    FrozenDict = dict
    JAX_AVAILABLE = False


if JAX_AVAILABLE:

    @patch_to(FrozenDict)
    def __repr__(self):  # type: ignore
        _dict = lambda d: dict(
            {
                k: (v if not isinstance(v, self.__class__) else dict(v))
                for k, v in d.items()
            }
        )
        return f"{self.__class__.__name__}({dict.__repr__(_dict(self))})"


if JAX_AVAILABLE:

    @patch_to(DeviceArray)
    def __repr__(self):  # type: ignore
        if self.ndim == 0 and is_float(self):
            v = float(self)
            return repr(round(v, 5)) if abs(v) > 1e-4 else repr(v)
        elif self.ndim == 0 and is_complex_float(self):
            r, i = float(self.real), float(self.imag)
            r = round(r, 5) if abs(r) > 1e-4 else r
            i = round(i, 5) if abs(i) > 1e-4 else i
            s = repr(r + 1j * i)
            if s[0] == "(" and s[-1] == ")":
                s = s[1:-1]
            return s
        else:
            s = super(self.__class__, self).__repr__()
            s = s.replace("DeviceArray(", "      array(")
            s = re.sub(r", dtype=.*[,)]", "", s)
            s = re.sub(r" weak_type=.*[,)]", "", s)
            return dedent(s) + ")"
