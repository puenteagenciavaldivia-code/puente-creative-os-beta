"""Compatibilidad del PR DCP-02 con el único adaptador vigente.

Revisión local: el responsable de texto NO autentica a una persona. Operaciones
persistentes protegidas deben usar DecisionStore y política del servidor.
"""
from dossier_adapter import bind_dossier, approve_bound
from dossier_engine import handoff


def prepare_for_brief(record, dossier, audit=None):
    if not isinstance(audit, dict):
        raise ValueError('El adaptador reconciliado requiere la auditoría del briefing.')
    return bind_dossier(dossier, record, audit)


def finalize_from_review(package, record, audit, review):
    selection = str(review.get('direccion_seleccionada') or '').strip().casefold()
    matches = [d for d in package['dossier']['directions'] if d['name'].strip().casefold() == selection]
    if len(matches) != 1:
        raise ValueError('La selección no coincide con el dossier.')
    return approve_bound(package, record, audit, review, review.get('responsable'),
                         matches[0]['id'], review.get('observaciones'))


def deliver_creative(package, route='undecided'):
    return handoff(package, route)
