"""
PooledSampler: draws donor values for a field from the pooled (class-agnostic)
empirical marginal of a packet set.

This is what makes an intervention a do() rather than a deletion: the field's marginal
distribution over the dataset is preserved, only its mutual information with the label
is destroyed. Sampling class-agnostically (over all packets regardless of label) is the
null-model that removes the field's discriminative signal while keeping every value
realistic.
"""
import numpy as np
from . import fields as F


class PooledSampler:
    def __init__(self, packets, seed=0):
        self.rng = np.random.default_rng(seed)
        self.pool = {}
        for name in F.INTERVENABLE:
            vals = []
            for p in packets:
                if F.field_present(p, name):
                    v = F.REGISTRY[name].get(p)
                    if v is not None:
                        vals.append(v)
            self.pool[name] = vals

    def draw(self, field_name):
        vals = self.pool.get(field_name) or []
        if not vals:
            return None
        return vals[self.rng.integers(0, len(vals))]

    def has(self, field_name):
        return bool(self.pool.get(field_name))
