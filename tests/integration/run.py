"""Run joint, Channel Box and weight-paint integration checks in isolated Blender processes.

python tests/integration/run.py --blender PATH [--no-build] [-k PATTERN] [--headless-only]
GUI checks open a temporary factory window and close it on completion.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run as headless

GUI_RESULTS = {
    'blender_channel_box_wheel': 'allset-channel-wheel-result.txt',
    'blender_joint_viewport': 'allset-viewport-result.txt',
    'blender_weight_paint_keys': 'allset-paint-key-result.txt',
    'blender_weight_workspace_ui': 'allset-weight-ui-result.txt',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--blender', default=os.environ.get('BLENDER', headless.build.DEFAULT_BLENDER))
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--headless-only', action='store_true')
    ap.add_argument('-k', default='', help='comma-separated filename patterns')
    args = ap.parse_args()
    files = [p for p in sorted(HERE.glob('blender_*.py'))
             if any(k in p.stem for k in args.k.split(','))
             and not (args.headless_only and p.stem in GUI_RESULTS)]
    if not files:
        raise SystemExit('No matching integration checks')
    headless.SANDBOX = headless.ROOT / 'tmp' / 'integration_env'
    package = (headless.build.ext_zip() if args.no_build else
               headless.build.main(['--blender', args.blender, '--no-legacy']))
    env = headless.make_sandbox()
    env['ALLSET_NO_WELCOME'] = '1'
    env['ALLSET_INTEGRATION_OUTPUT'] = str(headless.SANDBOX / 'results')
    headless.install(args.blender, package, env)
    results = []
    for path in files:
        gui = path.stem in GUI_RESULTS
        cmd = [args.blender, '--factory-startup', '--python-exit-code', '1']
        geometry = os.environ.get('ALLSET_GUI_GEOMETRY', '0 0 1600 900').split()   # '2048 0 1600 900' = 2nd monitor
        cmd += (['--enable-event-simulate', '--window-geometry', *geometry]
                if gui else ['--background'])
        cmd += ['--python', str(path)]
        log = headless.SANDBOX / 'logs' / (path.stem + '.log')
        with headless.blender_slots.slot(f'integration {path.stem}'), log.open('w', encoding='utf-8') as stream:
            try:
                result = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=120)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 'timeout'
        output = log.read_text(encoding='utf-8', errors='replace')
        if gui:
            report = headless.SANDBOX / 'results' / GUI_RESULTS[path.stem]
            output = report.read_text(encoding='utf-8') if report.exists() else 'Missing GUI result'
            ok = code == 0 and output.startswith('PASS:')
        else:
            ok = code == 0 and 'PASS:' in output
        results.append({'name': path.stem, 'ok': ok, 'exit_code': code, 'log': str(log)})
        print(('PASS' if ok else 'FAIL') + '  ' + path.stem, flush=True)
        if not ok:
            print(output[-6000:], flush=True)
    (headless.SANDBOX / 'results' / 'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    failed = sum(not r['ok'] for r in results)
    print(f'{len(results) - failed} passed, {failed} failed', flush=True)
    return bool(failed)


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    import hidden_desktop  # noqa: E402  (test Blenders never show on screen)
    hidden_desktop.ensure_hidden()
    sys.exit(main())
