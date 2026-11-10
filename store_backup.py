"""Copias LOCALES verificables de SQLite. Sin almacenamiento cloud ni secretos."""
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path


def _check(path):
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('La base no supera integrity_check.')


def backup_database(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if source==destination or not source.is_file():raise ValueError('Origen de copia no válido.')
    _check(source)
    # Reserva exclusiva; nunca sobrescribir una copia anterior.
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    manifest=destination.with_suffix(destination.suffix+'.json')
    if manifest.exists():destination.unlink();raise FileExistsError('El manifiesto ya existe.')
    try:
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(destination) as dst:
            src.backup(dst)
        _check(destination)
        result={'format':'puente.sqlite.backup.v1','bytes':destination.stat().st_size,
                'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}
        with manifest.open('x',encoding='utf-8') as stream:json.dump(result,stream,sort_keys=True)
        return result
    except Exception:
        destination.unlink(missing_ok=True);raise


def restore_database(backup,destination):
    backup=Path(backup).resolve();destination=Path(destination).resolve()
    manifest=json.loads(backup.with_suffix(backup.suffix+'.json').read_text())
    if manifest.get('format')!='puente.sqlite.backup.v1' or manifest.get('sha256')!=hashlib.sha256(backup.read_bytes()).hexdigest():
        raise ValueError('La copia no coincide con el manifiesto.')
    # Crea una base nueva y su manifiesto; nunca reemplaza una base existente.
    result=backup_database(backup,destination)
    try:
        # Una restauración no debe resucitar sesiones o callbacks anteriores.
        with sqlite3.connect(destination) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'identity_sessions' in tables:db.execute('UPDATE identity_sessions SET revoked=1')
            if 'login_challenges' in tables:db.execute('UPDATE login_challenges SET used=1')
            # La cookie OIDC nativa vive fuera de SQLite. El gate del piloto exige
            # un ID token emitido después de esta recuperación, en cada operación.
            if 'pilot_access_meta' in tables:
                db.execute('UPDATE pilot_access_meta SET not_before=? WHERE id=1',(time.time(),))
        _check(destination)
        result['sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
        result['bytes']=destination.stat().st_size
        result['sessions_invalidated']=True
        destination.with_suffix(destination.suffix+'.json').write_text(json.dumps(result,sort_keys=True))
        return result
    except Exception:
        destination.unlink(missing_ok=True)
        destination.with_suffix(destination.suffix+'.json').unlink(missing_ok=True)
        raise
