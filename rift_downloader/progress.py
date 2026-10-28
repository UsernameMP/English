"""Crash-tolerant, compact live status for the Colab 200-file pilot.

A Google Colab runtime may disappear without running Python finally blocks.
Write small, recoverable progress JSON regularly during the actual pilot.
Neither OAuth tokens nor downloaded document bodies appear in the report.
"""
import time
from pathlib import Path

from .db import summary
from .backup import last_backup_count
from .mounted_drive import atomic_json

def progress_snapshot(db,*,state="running",target=200):
    if target<1:
        raise ValueError("target must be a positive integer")
    data=summary(db)
    verified=data["uploaded_files"]
    return {
        "schema":"rift-pilot-progress/v1",
        "updated_at_unix":time.time(),
        "state":state,
        "target_unique_files":target,
        "verified_unique_files":verified,
        "remaining_unique_files":max(0,target-verified),
        "latest_index_checkpoint_verified_files":last_backup_count(db),
        "queue_and_http":data,
        "note":"This is an intermediate, local-SQLite-backed snapshot. "
               "If Colab terminates abruptly, newer verified originals may "
               "exist in RIFT/raw and RIFT/receipts. The next run reconciles them."
    }

def write_progress(db,path,*,state="running",target=200):
    report=progress_snapshot(db,state=state,target=target)
    atomic_json(Path(path),report)
    return report
