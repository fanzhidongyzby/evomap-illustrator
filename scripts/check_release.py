#!/usr/bin/env python3
"""Check the public package only; never read ignored local profiles or credentials."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = {
    'personal filesystem path': re.compile(r'/Users/[A-Za-z0-9_.-]+/'),
    'private document locator': re.compile(r'https?://[A-Za-z0-9.-]+\.feishu\.cn/(?:wiki|docx)/[A-Za-z0-9]{12,}'),
    'message identifier': re.compile(r'\bom_[A-Za-z0-9]{20,}\b'),
    'credential-like literal': re.compile(r'\b(?:sk-ant-api\d+-|ghp_|gho_)[A-Za-z0-9_-]{25,}'),
    'signed resource URL': re.compile(r'(?:Signature|Policy|X-Amz-Signature)=[A-Za-z0-9_~%-]{30,}'),
}


def public_files():
    result = subprocess.run(['git','-C',str(ROOT),'ls-files','-z'], capture_output=True, check=False)
    names = result.stdout.decode().split('\0') if result.returncode == 0 else []
    names = [name for name in names if name]
    if not names:
        names = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()
                 and not any(part in ('.git','.local','__pycache__') for part in p.relative_to(ROOT).parts)
                 and p.name != '.DS_Store']
    return names


def check():
    errors = []
    names = public_files()
    for needed in ('SKILL.md','README.md','LICENSE'):
        if not (ROOT/needed).is_file(): errors.append('Missing '+needed)
    for name in names:
        if name.startswith('.local/') or '.DS_Store' in name or '__pycache__' in name:
            errors.append('Private/cache path is tracked: '+name)
            continue
        path = ROOT/name
        if not path.is_file(): continue
        if path.suffix not in ('.md','.py','.json','.yml','.yaml','.sh') and name not in ('AGENTS.md',): continue
        text = path.read_text(encoding='utf-8')
        for kind,pattern in PATTERNS.items():
            if pattern.search(text): errors.append(name+': '+kind)
        if path.suffix == '.md':
            stripped = re.sub(r'```.*?```|`[^`\n]*`','',text,flags=re.S)
            for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)',stripped):
                if '://' in target or target.startswith('#'): continue
                target = target.split('#',1)[0]
                if not (path.parent/target).is_file(): errors.append(name+': missing documentation link '+target)
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    if not skill.startswith('---\n') or '\nname:' not in skill or '\ndescription:' not in skill:
        errors.append('Missing skill frontmatter')
    if errors:
        print(json.dumps({'passed':False,'errors':errors},ensure_ascii=False,indent=2))
        return 1
    print(json.dumps({'passed':True,'public_files_checked':len(names),'ignored_local_profiles_not_scanned':True},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
