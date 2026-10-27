"""Generate a one-shot *user* systemd service; never start it automatically.

Designed not to modify existing VPS system units or other services.
"""
import argparse
import os
import stat
from pathlib import Path

UNIT_NAME='rift-downloader-pilot.service'

def quote(text):
    return '"'+str(text).replace('\\','\\\\').replace('"','\\"')+'"'

def render_unit(*,repo,python,token,state_dir):
    repo=Path(repo).resolve();python=Path(python).resolve()
    token=Path(token).resolve();state_dir=Path(state_dir).resolve()
    db=state_dir/'rift.sqlite3';spool=state_dir/'spool';report=state_dir/'pilot_report.json'
    return f"""# RIFT pilot: 200 verified Drive objects; NO automatic restart or scheduling.
[Unit]
Description=RIFT 200-file archive pilot
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory={quote(repo)}
Environment=PYTHONUNBUFFERED=1
ExecStart={quote(python)} -m rift_downloader.cli --db {quote(db)} run --token {quote(token)} --spool {quote(spool)} --limit-success 200 --max-checks 3000 --min-delay 10 --max-file-mb 100 --spool-max-gb 10 --backup-every 25
ExecStartPost={quote(python)} -m rift_downloader.cli --db {quote(db)} export-report --output {quote(report)}
TimeoutStartSec=infinity
TimeoutStopSec=60
Restart=no
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=default.target
"""

def install(args):
    root=Path(__file__).resolve().parents[1]
    python=root/'.venv/bin/python'
    token=Path(args.token).expanduser().resolve()
    if not token.is_file():
        raise SystemExit('OAuth token not found. First authorize on a trusted computer and transfer token securely.')
    if token.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SystemExit('Refusing insecure OAuth token. Run: chmod 600 '+str(token))
    if not python.is_file():
        raise SystemExit('Virtualenv missing: create .venv and install requirements first')
    state_dir=Path(args.state_dir).expanduser().resolve()
    state_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    (state_dir/'spool').mkdir(exist_ok=True,mode=0o700)
    db=state_dir/'rift.sqlite3'
    if not db.is_file():
        raise SystemExit('Import the RIFT resource shards before installing the service: '+str(db))
    unit_dir=Path.home()/'.config/systemd/user'
    unit_dir.mkdir(parents=True,exist_ok=True)
    unit_path=unit_dir/UNIT_NAME
    if unit_path.exists() and not args.overwrite:
        raise SystemExit(f'{unit_path} already exists; use --overwrite only if intentional')
    unit_path.write_text(render_unit(repo=root,python=python,token=token,state_dir=state_dir),
                         encoding='utf-8')
    print('Created:',unit_path)
    print('No service started or enabled.')
    print('Next: systemctl --user daemon-reload')
    print('Then: systemctl --user start '+UNIT_NAME)
    print('Monitor: journalctl --user -u '+UNIT_NAME+' -f')
    print('Status: systemctl --user status '+UNIT_NAME)
    print('Pilot report:',state_dir/'pilot_report.json')

def main():
    parser=argparse.ArgumentParser(description='Prepare isolated user-systemd pilot service; never auto-start')
    parser.add_argument('--token',required=True,help='Existing chmod 600 Drive OAuth token')
    parser.add_argument('--state-dir',default='~/.local/share/rift-downloader')
    parser.add_argument('--overwrite',action='store_true')
    install(parser.parse_args())
if __name__=='__main__':
    main()
