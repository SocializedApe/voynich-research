"""Build the Kaggle kernel that runs tier 5 (nomenclator layer) or tier 6 (the tier-5 calibration cipher with copying
noise) of the verbose sweep on Kaggle's GPUs. (11 Nov 2026)

The kernel is one script with this package's code embedded as a base64 zip; the data (kaggle_pkg/data/, written by
verbose/prepare.py and verbose/nomen.py, git-ignored) comes from a Kaggle dataset attached to the kernel. The kernel
runs gpu_sweep.py --tier 5 with one shard per GPU, then analyze5.py, and leaves gpu_shard*.jsonl, log*.txt and
analysis.md in /kaggle/working/pkg/results.

Run from targets/voynich:
  python verbose/prepare.py; python verbose/nomen.py                    (once: writes kaggle_pkg/data/)
  kaggle datasets create -p verbose/kaggle_pkg/data ...                 (once: upload it as a private dataset)
  python verbose/kaggle_pkg/build_kernel5.py <out dir> <kaggle user> <dataset slug, e.g. user/voynich-archive> [tier, default 5]
      (tier 6 packs verbose/kaggle_results/tier5/*.jsonl too: analyze6.py takes its threshold from the clean calibration)
  kaggle kernels push -p <out dir>
  kaggle kernels status <user>/voynich-verbose-tier5
  kaggle kernels output <user>/voynich-verbose-tier5 -p <dir>           (copy gpu_shard*.jsonl, analysis.md to
                                                                         verbose/kaggle_results/tier5/)
Without Kaggle: python verbose/kaggle_pkg/gpu_sweep.py --tier 5 --out <dir>; python verbose/kaggle_pkg/analyze5.py <dir>
(384 jobs; about 2.5 h on 2 x T4).
"""
import base64, io, json, os, sys, zipfile
PKG = os.path.dirname(os.path.abspath(__file__))

SCRIPT = '''# Voynich verbose attack, tier TIER (see targets/voynich/verbose/README.md)
import base64, glob, io, os, subprocess, sys, time, zipfile
W = '/kaggle/working/pkg'; os.makedirs(W, exist_ok=True)
zipfile.ZipFile(io.BytesIO(base64.b64decode(PKG_B64))).extractall(W)
cands = glob.glob('/kaggle/input/**/kaggle_pkg/data', recursive=True)
print('data dirs:', cands, flush=True)
if not cands:
    print(subprocess.run('find /kaggle/input -maxdepth 4 | head -50', shell=True, capture_output=True, text=True).stdout, flush=True)
    raise SystemExit('archive data not found')
os.symlink(cands[0], W + '/data')
subprocess.run(f'{sys.executable} -m pip install -q sentencepiece', shell=True)
import torch
n = max(torch.cuda.device_count(), 1); print('gpus', torch.cuda.device_count(), flush=True)
os.makedirs(W + '/results', exist_ok=True); t0 = time.time(); procs = []
for g in range(n):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(g), PYTHONUTF8='1')
    procs.append(subprocess.Popen(f'{sys.executable} -W ignore {W}/gpu_sweep.py --tier TIER --shard {g} --nshards {n} --out {W}/results --deadline 36000 > {W}/results/log{g}.txt 2>&1', shell=True, env=env))
while any(p.poll() is None for p in procs):
    time.sleep(120)
    for g in range(n):
        tail = open(f'{W}/results/log{g}.txt').read().strip().splitlines()[-1:]
        print(f'[{time.time() - t0:.0f}s] shard {g}:', tail, flush=True)
for g in range(n):
    print(open(f'{W}/results/log{g}.txt').read()[-3000:], flush=True)
r = subprocess.run(f'{sys.executable} {W}/analyzeTIER.py {W}/results {W}/tier5', shell=True, capture_output=True, text=True, cwd=W)
open(W + '/results/analysis.md', 'w').write(r.stdout + r.stderr); print(r.stdout, r.stderr, flush=True)
os.remove(W + '/data')
print(f'ALL DONE {time.time() - t0:.0f}s')
'''


def main():
    out, user, dataset = sys.argv[1:4]; tier = sys.argv[4] if len(sys.argv) > 4 else '5'; os.makedirs(out, exist_ok=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in ('solver.py', 'sweep.py', 'gpu_sweep.py', 'analyze.py', 'analyze5.py', 'analyze6.py'):
            z.write(os.path.join(PKG, f), f)
        if tier == '6':
            for f in ('gpu_shard0.jsonl', 'gpu_shard1.jsonl'):
                z.write(os.path.join(PKG, '..', 'kaggle_results', 'tier5', f), 'tier5/' + f)
    b64 = base64.b64encode(buf.getvalue()).decode()
    open(os.path.join(out, f'tier{tier}.py'), 'w', encoding='utf-8').write('PKG_B64 = "' + b64 + '"\n' + SCRIPT.replace('TIER', tier))
    json.dump({"id": f"{user}/voynich-verbose-tier{tier}", "title": f"voynich-verbose-tier{tier}", "code_file": f"tier{tier}.py", "language": "python", "kernel_type": "script",
               "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": [dataset], "competition_sources": [], "kernel_sources": []},
              open(os.path.join(out, 'kernel-metadata.json'), 'w'), indent=1)
    print('wrote', out, len(b64), 'base64 chars')


if __name__ == '__main__':
    main()
