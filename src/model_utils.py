import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

def hgb(X, y, w=None, seed=0, **kw):
    p = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=20,
             l2_regularization=1.0, categorical_features="from_dtype", random_state=seed)
    p.update(kw)
    return HistGradientBoostingClassifier(**p).fit(X, y, sample_weight=w)
