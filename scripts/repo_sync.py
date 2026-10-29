#!/usr/bin/env python3
"""Explicit, fast-forward-only repository sync for a Git-managed skill directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def git(*args, check=True):
    result = subprocess.run(['git','-C',str(ROOT)]+list(args), capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Git command failed')
    return result.stdout.strip()


def clean():
    if git('status','--porcelain'):
        raise RuntimeError('Public files have uncommitted changes. Test and commit them first; local ignored preferences are not pushed.')


def status(fetch=True):
    if fetch: git('fetch','origin')
    upstream = git('rev-parse','--abbrev-ref','@{upstream}')
    head = git('rev-parse','HEAD');remote = git('rev-parse','@{upstream}')
    changes = git('status','--porcelain')
    result = {'branch':git('branch','--show-current'),'upstream':upstream,
              'local_commit':head,'remote_commit':remote,'public_worktree_clean':not changes,
              'in_sync':head==remote and not changes,'local_preferences_intentionally_ignored':True}
    print(json.dumps(result,indent=2))
    return result['in_sync']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('status','pull','push'))
    parser.add_argument('--offline',action='store_true',help='Compare the last fetched state only')
    args = parser.parse_args()
    try:
        if args.action == 'pull':
            clean();git('pull','--ff-only');status()
        elif args.action == 'push':
            clean();git('fetch','origin')
            subprocess.run([sys.executable,'-I',str(ROOT/'scripts/check_release.py')],check=True)
            upstream=git('rev-parse','--abbrev-ref','@{upstream}')
            ancestor=subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',upstream,'HEAD'])
            if ancestor.returncode: raise RuntimeError('Remote is ahead or diverged. Pull and reconcile normally; force pushing is not supported.')
            git('push');status()
        else:
            raise SystemExit(0 if status(not args.offline) else 1)
    except (RuntimeError,subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
