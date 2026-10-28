"""Read-only local readiness checks before a 200-file VPS pilot."""
import json
import shutil
import stat
from pathlib import Path

EXPECTED_SCOPE='https://www.googleapis.com/auth/drive.file'

def preflight(db,token_path=None,spool='state/spool',check_drive=False):
    """Return a redacted report. Never prints OAuth client IDs or tokens."""
    checks={}
    total=db.execute('SELECT COUNT(*) FROM resources').fetchone()[0]
    candidates=db.execute('SELECT COUNT(*) FROM resources WHERE file_candidate=1').fetchone()[0]
    checks['queue_imported']={'ok':total>0,'resources':total,'file_candidates':candidates}
    spool_path=Path(spool).expanduser().resolve()
    existing=spool_path
    while not existing.exists() and existing.parent!=existing:
        existing=existing.parent
    disk=shutil.disk_usage(existing)
    checks['disk_space']={'ok':disk.free>=1024**3,
        'free_bytes':disk.free,'recommended_min_bytes':1024**3}
    path=Path(token_path).expanduser().resolve() if token_path else None
    token_ok=False
    if path is None or not path.is_file():
        checks['drive_oauth']={'ok':False,'reason':'OAuth refresh token not available on VPS'}
    else:
        perms=stat.S_IMODE(path.stat().st_mode)
        private=not bool(perms & (stat.S_IRWXG|stat.S_IRWXO))
        try:
            credentials=json.loads(path.read_text(encoding='utf-8'))
            refresh=bool(credentials.get('refresh_token'))
            scopes=credentials.get('scopes') or []
            scope_ok=EXPECTED_SCOPE in scopes
            token_ok=private and refresh and scope_ok
            checks['drive_oauth']={'ok':token_ok,'private_file':private,
                'has_refresh_token':refresh,'drive_file_scope':scope_ok}
        except (OSError,ValueError,UnicodeError):
            checks['drive_oauth']={'ok':False,'reason':'invalid OAuth JSON (or inaccessible file)'}
    if check_drive:
        if not token_ok:
            checks['drive_api']={'ok':False,'reason':'missing or unsafe OAuth credentials'}
        else:
            try:
                from .drive import build_service
                svc=build_service(path)
                obj=svc.files().list(page_size=1,fields='files(id),nextPageToken').execute()
                checks['drive_api']={'ok':isinstance(obj.get('files'),list),
                                     'mode':'read-only metadata request'}
            except Exception as exc:
                # Never expose exception contents: an OAuth SDK error may include
                # token, client metadata or a URL with account-specific details.
                checks['drive_api']={'ok':False,'reason':type(exc).__name__}
    return {'ready':all(value['ok'] for value in checks.values()),'checks':checks,
            'note':'No website documents or Drive files downloaded or uploaded by doctor.'}
