# Reproduce every number in the paper from a clean checkout.
#   make all         - full pipeline (tests -> E1 -> benchmark -> audit(5 seeds) -> E5 -> figures)
#   make test        - PacketDO unit tests
#   make e1          - operator-validity study
#   make data        - regenerate synthetic benchmark datasets
#   make audit       - 5-seed audit sweep (slow; needs GPU for the CNN)
#   make figures     - regenerate paper figures
# Real-data (CIC-IDS2017) targets need the dataset staged; see realdata/DATASET.md.
PY = python

.PHONY: all test e1 data audit e5 figures clean
all: test e1 data audit e5 figures
	@echo "=== full pipeline complete ==="

test:
	$(PY) -m pytest packetdo/tests -q

e1:
	$(PY) e1_operator_validity/run_e1.py --n 2000 --seed 0

data:
	mkdir -p benchmark/data
	$(PY) benchmark/generate.py --p 0.5 --n 6000 --seed 0 --out benchmark/data/p05.npz
	$(PY) benchmark/generate.py --p 0.7 --n 6000 --seed 0 --out benchmark/data/p07.npz
	$(PY) benchmark/generate.py --p 0.9 --n 6000 --seed 0 --out benchmark/data/p09.npz
	$(PY) benchmark/generate.py --p 1.0 --n 6000 --seed 0 --out benchmark/data/p10.npz

audit: data
	$(PY) benchmark/run_audit.py --seed 0
	$(PY) benchmark/run_audit.py --seed 1
	$(PY) benchmark/run_audit.py --seed 2
	$(PY) benchmark/run_audit.py --seed 3
	$(PY) benchmark/run_audit.py --seed 4
	$(PY) benchmark/aggregate_seeds.py

e5: data
	$(PY) benchmark/run_e5.py

figures:
	$(PY) figures/make_figures.py

clean:
	rm -f benchmark/data/*.npz benchmark/data/*.pkl
	rm -f benchmark/results/audit_*.json benchmark/results/*.md
