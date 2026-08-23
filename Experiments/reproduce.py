"""
Cross-platform reproduction driver (Windows/Linux/Mac). Regenerates every synthetic-benchmark
number in the paper from a clean checkout. Real-data (CIC-IDS2017) steps are separate and need the
dataset staged (see realdata/DATASET.md).

  python reproduce.py            # full synthetic pipeline
  python reproduce.py --quick    # tests + E1 + 1-seed audit only (fast smoke)

Each step prints [OK]/[FAIL]; exits nonzero on any failure.
"""
import subprocess, sys, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(desc, args, cwd=HERE):
    print(f"\n=== {desc} ===", flush=True)
    r = subprocess.run([PY] + args, cwd=cwd)
    tag = "[OK]" if r.returncode == 0 else "[FAIL]"
    print(f"{tag} {desc} (exit {r.returncode})", flush=True)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    run("PacketDO unit tests", ["-m", "pytest", "packetdo/tests", "-q"])
    run("E1 operator-validity", ["e1_operator_validity/run_e1.py", "--n", "2000", "--seed", "0"])

    os.makedirs(os.path.join(HERE, "benchmark", "data"), exist_ok=True)
    for p, tag in [("0.5", "p05"), ("0.7", "p07"), ("0.9", "p09"), ("1.0", "p10")]:
        run(f"generate benchmark p={p}",
            ["benchmark/generate.py", "--p", p, "--n", "6000", "--seed", "0",
             "--out", f"benchmark/data/{tag}.npz"])

    seeds = ["0"] if args.quick else ["0", "1", "2", "3", "4"]
    for s in seeds:
        run(f"audit seed {s}", ["benchmark/run_audit.py", "--seed", s])
    if not args.quick and os.path.exists(os.path.join(HERE, "benchmark", "aggregate_seeds.py")):
        run("aggregate seeds", ["benchmark/aggregate_seeds.py"])
    if os.path.exists(os.path.join(HERE, "benchmark", "run_e5.py")):
        run("E5 operator sensitivity", ["benchmark/run_e5.py"])
    if os.path.exists(os.path.join(HERE, "benchmark", "validate_rm.py")):
        run("R(M) validation (legacy vs corrected)", ["benchmark/validate_rm.py"])
    # real-data threshold sensitivity (reads a committed a2_port_results.json)
    if os.path.exists(os.path.join(HERE, "realdata", "results", "a2_port_results.json")):
        run("real-data FC threshold sensitivity", ["realdata/fc_sensitivity.py"])
    # byte-level PCAP study runs only if the ISCX subset is staged (see realdata/PCAP_DATASET.md)
    if os.path.exists(os.path.join(HERE, "realdata", "pcap")) and \
       any(f.endswith(".pcap") for f in os.listdir(os.path.join(HERE, "realdata", "pcap"))):
        run("byte-level PCAP study", ["realdata/pcap_bytelevel.py"], cwd=os.path.join(HERE, "realdata"))
    run("figures", ["figures/make_figures.py"])

    print("\n=== reproduction complete ===")


if __name__ == "__main__":
    main()
