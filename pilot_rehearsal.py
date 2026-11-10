"""Ensayo completo LOCAL con fixture de identidad, sin OAuth ni conexiones."""
import json
import secrets
import tempfile
import time
from pathlib import Path
from client_delivery import client_delivery,client_html
from decision_store import DecisionStore,Scope
from review_workflow import new_review
from session_store import SessionStore
from store_backup import backup_database,restore_database
from identity_boundary import AuthenticationDenied


def rehearse():
    fixture=json.loads((Path(__file__).parent/'examples/taller_rio_synthetic.json').read_text())
    now=int(time.time())
    with tempfile.TemporaryDirectory(prefix='puente-pilot-') as directory:
        root=Path(directory);database=root/'lab.sqlite'
        sessions=SessionStore(database,clock=lambda:now)
        binding=secrets.token_urlsafe(32);challenge=sessions.begin(binding)
        # Fixture de claims explícito. No constituye verificación de firma ni login Google.
        def verifier(token,audience):
            return {'iss':'https://accounts.google.com','sub':'123456789012345678901','aud':audience,
                    'iat':now-5,'exp':now+300,'nonce':challenge['nonce']}
        handle=sessions.finish(challenge['state'],binding,'TOKEN-FICTICIO','client-ficticio',verifier)
        actor=sessions.resolve(handle);scope=Scope('AGENCIA-FICTICIA',fixture['record']['submission_id'])
        policy=lambda who,target,action:who==actor and target==scope
        store=DecisionStore(database,policy)
        version=store.save_revision(actor,scope,fixture['record'],fixture['audit'],
                                    new_review(fixture['record'],fixture['audit']),fixture['dossier'],0)
        result=store.decide(actor,scope,version,'A','Decisión FICTICIA para demostrar una ruta fundamentada y viable. No es aprobación humana real.',
                            'request-ficticio-endtoend-001')
        contract={'submission_id':scope.project,'version':'CONTRATO-FICTICIO-V1','included_deliverables':['strategy','direction']}
        projected=client_delivery(result['package'],fixture['record'],fixture['audit'],contract)
        html=client_html(projected)
        backup=root/'backup.sqlite';restored=root/'restored.sqlite'
        manifest=backup_database(database,backup);restore_database(backup,restored)
        restored_store=DecisionStore(restored,policy)
        assert restored_store.latest_decision(actor,scope)==result
        assert restored_store.history(actor,scope)==store.history(actor,scope)
        try:SessionStore(restored,clock=lambda:now).resolve(handle)
        except AuthenticationDenied:pass
        else:raise AssertionError('La restauración no invalidó sesiones anteriores.')
        sessions.revoke(handle)
        report={'status':'LOCAL_APROBADO','identity':'SIMULADA — no OAuth real',
                'dossier_version':version,'decision_persisted':True,'production_approved':False,
                'client_sections':list(projected['sections']),'history_events':len(store.history(actor,scope)),
                'restore_matches':True,'restored_sessions_invalidated':True,'session_revoked':True,'backup_format':manifest['format'],
                'limitations':['Sin evaluación humana','Sin Google real','Sin cookies/PKCE','Solo un archivo SQLite local']}
        return report,html


if __name__=='__main__':
    report,_=rehearse();print(json.dumps(report,ensure_ascii=False,indent=2))
