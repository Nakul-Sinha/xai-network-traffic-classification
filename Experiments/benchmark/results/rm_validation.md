# R(M) validation: legacy (removal) vs corrected (sufficiency)

p=1.0, n_test=800, sufficiency fraction=0.5 (a set must recover >= 50% of above-chance skill).

| model | true R | legacy R | corrected R | corrected sets |
|---|---|---|---|---|
| commit_oracle(window only) | 1 | 1 | 1 | [['tcp.window']] |
| ttl_oracle(ttl only) | 1 | 1 | 1 | [['ip.ttl']] |
| redundant_oracle(ttl OR window) | 2 | 1 | 1 | [['ip.ttl', 'tcp.window']] |
| trained_ByteCNN | ? | 1 | 1 | [['tcp.window']] |
| trained_RandomForest | ? | 1 | 1 | [['tcp.window']] |
