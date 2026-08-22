# Experiments

Code and results for the paper. Run from this directory.

## Layout
- `packetdo/` - the PacketDO intervention operator (contribution C1): field registry,
  operator (packet_do + zero_mask baseline), validity predicates, pooled sampler, unit tests.
- `e1_operator_validity/` - E1: zero-mask vs PacketDO protocol-validity study.
- `poc/` - the original proof of concept (Phase 0), kept for provenance.

## Reproduce
    pip install -r requirements.txt
    python -m pytest packetdo/tests -q            # operator unit tests
    python e1_operator_validity/run_e1.py --n 2000 --seed 0

Results land in each experiment's `results/`. All runs are seeded.
