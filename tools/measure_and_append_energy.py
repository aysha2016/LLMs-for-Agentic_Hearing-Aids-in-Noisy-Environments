#!/usr/bin/env python3
"""Measure power while running a command, compute energy, and append to evaluation CSV.

Supported sampling backends:
- nvidia: uses `nvidia-smi --query-gpu=power.draw`
- rapl: reads cumulative energy_uj from /sys/class/powercap and differentiates

Usage example:
  python3 tools/measure_and_append_energy.py \
    --method nvidia \
    --scenario voice_female \
    --run-cmd "python3 enhanced_speech_demo.py --scenario voice_female" \
    --interval 0.5

The script updates `output_enhanced_speech/evaluation_matrix.csv`, adding
`energy_J_total` and `energy_J_per_s` columns for the matching scenario row.
"""
import argparse
import csv
import os
import shlex
import shutil
import subprocess
import sys
import time
from glob import glob


def read_nvidia_power_w():
    smi = shutil.which("nvidia-smi")
    if not smi:
        raise RuntimeError("nvidia-smi not found")
    # query power.draw (watts)
    p = subprocess.run([smi, "--query-gpu=power.draw", "--format=csv,noheader,nounits"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("nvidia-smi failed: %s" % p.stderr.strip())
    out = p.stdout.strip().splitlines()[0]
    return float(out)


def find_energy_uj_file():
    candidates = glob("/sys/class/powercap/**/energy_uj", recursive=True)
    if candidates:
        return candidates[0]
    return None


def read_rapl_energy_uj(path):
    with open(path, "r") as f:
        return int(f.read().strip())


def sample_power(method, prev_rapl=None, rapl_path=None):
    if method == "nvidia":
        return read_nvidia_power_w(), None
    if method == "rapl":
        if not rapl_path:
            rapl_path = find_energy_uj_file()
            if not rapl_path:
                raise RuntimeError("No RAPL energy_uj file found")
        cur = read_rapl_energy_uj(rapl_path)
        if prev_rapl is None:
            return None, (cur, rapl_path)
        # delta microJ -> J
        delta_uj = cur - prev_rapl[0]
        return (delta_uj / 1e6), (cur, rapl_path)
    raise RuntimeError("Unsupported method %s" % method)


def integrate_energy(samples):
    # samples: list of (t, power_W) where power_W may be None for first rapl sample
    # Integrate using trapezoid rule, skipping None entries
    energy = 0.0
    prev_t = None
    prev_p = None
    for t, p in samples:
        if p is None:
            prev_t, prev_p = t, p
            continue
        if prev_t is None or prev_p is None:
            prev_t, prev_p = t, p
            continue
        dt = t - prev_t
        energy += 0.5 * (p + prev_p) * dt
        prev_t, prev_p = t, p
    return energy


def update_csv(csv_path, scenario, energy_j):
    # read CSV
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        header = reader[0]
        rows = reader[1:]

    # ensure columns
    if "energy_J_total" not in header:
        header.append("energy_J_total")
    if "energy_J_per_s" not in header:
        header.append("energy_J_per_s")

    # map header indices
    hidx = {h: i for i, h in enumerate(header)}

    # convert rows to dicts
    updated = False
    new_rows = []
    for r in rows:
        # pad row to header length
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        row_map = {header[i]: r[i] for i in range(len(header))}
        if row_map.get("scenario", "") == scenario:
            try:
                duration = float(row_map.get("duration_s", "0") or "0")
            except (ValueError, TypeError) as exc:
                print(f"Warning: could not parse duration for {scenario}: {exc}", file=sys.stderr)
                duration = 0.0
            row_map["energy_J_total"] = "%.6f" % energy_j
            per_s = energy_j / duration if duration > 0 else 0.0
            row_map["energy_J_per_s"] = "%.6f" % per_s
            updated = True
        new_rows.append([row_map.get(h, "") for h in header])

    if not updated:
        # add new row
        duration = ""
        new_row = [""] * len(header)
        if "scenario" in hidx:
            new_row[hidx["scenario"]] = scenario
        if "duration_s" in hidx:
            new_row[hidx["duration_s"]] = duration
        if "energy_J_total" in hidx:
            new_row[hidx["energy_J_total"]] = "%.6f" % energy_j
        if "energy_J_per_s" in hidx:
            new_row[hidx["energy_J_per_s"]] = ""
        new_rows.append(new_row)

    # write back
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(new_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", choices=["nvidia", "rapl"], default="nvidia")
    ap.add_argument("--interval", type=float, default=0.5, help="sampling interval seconds")
    ap.add_argument("--scenario", required=True, help="scenario name to update in CSV")
    ap.add_argument("--run-cmd", required=True, help="command to run (quoted) while measuring")
    ap.add_argument("--csv", default="output_enhanced_speech/evaluation_matrix.csv", help="evaluation CSV to update")
    args = ap.parse_args()

    method = args.method
    interval = max(0.05, args.interval)
    scenario = args.scenario
    run_cmd = args.run_cmd
    csv_path = args.csv

    rapl_prev = None
    rapl_path = None

    popen = subprocess.Popen(shlex.split(run_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    samples = []
    start = time.time()
    last = start
    try:
        while True:
            now = time.time()
            try:
                if method == "nvidia":
                    p_w = read_nvidia_power_w()
                elif method == "rapl":
                    val, rapl_prev = sample_power("rapl", rapl_prev, rapl_path)
                    # sample_power returns instantaneous energy_J since prev sample for rapl
                    if val is None:
                        p_w = None
                    else:
                        # convert energy over interval to W estimate
                        dt = now - last if last is not None else interval
                        p_w = val / dt if dt > 0 else 0.0
                        rapl_path = rapl_prev[1]
                else:
                    raise RuntimeError("unsupported method")
            except Exception as e:
                print("Power read error:", e, file=sys.stderr)
                p_w = None

            samples.append((now - start, p_w))
            last = now

            # check process status
            ret = popen.poll()
            if ret is not None:
                break
            time.sleep(interval)

        # capture final power sample if possible
        try:
            if method == "nvidia":
                p_w = read_nvidia_power_w()
                samples.append((time.time() - start, p_w))
        except Exception as exc:
            print(f"Final power sample failed: {exc}", file=sys.stderr)

        total_energy = integrate_energy(samples)
        print(f"Measured energy (J): {total_energy:.6f}")

        # update CSV
        update_csv(csv_path, scenario, total_energy)
        print(f"Updated {csv_path} for scenario {scenario}")

    finally:
        try:
            out, err = popen.communicate(timeout=1)
        except Exception as exc:
            print(f"Process cleanup failed ({exc}), killing.", file=sys.stderr)
            popen.kill()


if __name__ == "__main__":
    main()
