"""Kaggle GPU run of targets/voynich/tfm: calibration on Latin, then 8 texts x 3 seeds (two jobs at a time, one per
GPU), then summarize.py and probe.py. Everything lands in /kaggle/working/voynich_tfm/tfm/{results,models,logs}."""
import glob, json, os, shutil, subprocess, sys, time, zipfile
import numpy as np
W = '/kaggle/working'
src = (glob.glob('/kaggle/input/**/voynich_tfm.zip', recursive=True) or [None])[0]
if src:
    zipfile.ZipFile(src).extractall(W)
else:
    tree = glob.glob('/kaggle/input/**/voynich_tfm', recursive=True)[0]; shutil.copytree(tree, W + '/voynich_tfm', dirs_exist_ok=True)
R = W + '/voynich_tfm'; os.chdir(R); os.makedirs('tfm/logs', exist_ok=True)
ARGS = '--steps 8000 --lr 3e-3 --drop 0.1 --batch 64 --d 128 --layers 4'
TEXTS = ['voynich', 'latin', 'voynich_shufpage', 'voynich_shufline', 'naibbe', 'italian', 'rugg', 'autocopist']
def run(cmd, gpu, log):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), PYTHONUTF8='1')
    return subprocess.Popen(f'{sys.executable} -W ignore {cmd} > {log} 2>&1', shell=True, env=env)
t0 = time.time()
run(f'tfm/train.py latin {ARGS} --tag calib_latin', 0, 'tfm/logs/calib_latin.log').wait()
c = json.load(open('tfm/results/calib_latin.json')); ng = json.load(open('tfm/results/ngram.json'))
m = float(np.mean(c['curve'])); print(f'CALIBRATION latin model {m:.3f} vs 5-gram {ng["latin"]["5"]:.3f} ->', 'OK' if m < ng['latin']['5'] else 'UNDERTRAINED', f'({time.time() - t0:.0f}s)', flush=True)
os.rename('tfm/results/calib_latin.json', 'tfm/logs/calib_latin.json'); os.remove('tfm/models/calib_latin.pt')
jobs = [(t, s) for s in (0, 1, 2) for t in TEXTS]; running = {}
while jobs or running:
    for g in (0, 1):
        if g not in running and jobs:
            t, s = jobs.pop(0); running[g] = (t, s, run(f'tfm/train.py {t} {ARGS} --seed {s} --tag {t}_s{s}', g, f'tfm/logs/{t}_s{s}.log'))
    for g in list(running):
        t, s, p = running[g]
        if p.poll() is not None:
            print(f'done {t}_s{s} rc {p.returncode} ({time.time() - t0:.0f}s):', open(f'tfm/logs/{t}_s{s}.log').read().strip().splitlines()[-1][:160], flush=True)
            del running[g]
    time.sleep(5)
subprocess.run(f'{sys.executable} tfm/summarize.py > tfm/results/summary.md 2>&1', shell=True)
print(open('tfm/results/summary.md').read(), flush=True)
subprocess.run(f'CUDA_VISIBLE_DEVICES=0 {sys.executable} -W ignore tfm/probe.py --model voynich_s0 > tfm/results/probe.txt 2>&1', shell=True)
print(open('tfm/results/probe.txt').read(), flush=True)
print(f'ALL DONE {time.time() - t0:.0f}s')
