"""Skills package — SAP technology and domain knowledge registries."""

from skills.sap.bw4hana import get_knowledge as _bw4hana_knowledge
from skills.sap.bw_on_hana import get_knowledge as _bw_on_hana_knowledge
from skills.sap.sac_analytics import get_knowledge as _sac_analytics_knowledge
from skills.sap.sac_planning import get_knowledge as _sac_planning_knowledge
from skills.sap.bpc import get_knowledge as _bpc_knowledge
from skills.sap.group_reporting import get_knowledge as _group_reporting_knowledge
from skills.sap.papm import get_knowledge as _papm_knowledge
from skills.sap.bdc import get_knowledge as _bdc_knowledge
from skills.sap.embedded_analytics import get_knowledge as _embedded_analytics_knowledge
from skills.sap.abap import get_knowledge as _abap_knowledge
from skills.domain.finance import get_knowledge as _finance_knowledge
from skills.domain.sales import get_knowledge as _sales_knowledge
from skills.domain.procurement import get_knowledge as _procurement_knowledge
from skills.domain.operations import get_knowledge as _operations_knowledge
from skills.domain.hr import get_knowledge as _hr_knowledge

# Maps technology dropdown values to their skill get_knowledge functions.
# Keys must exactly match SAP_TECHNOLOGIES in utils/session_state.py.
# Each technology maps to its OWN dedicated skill file — no sharing (CLAUDE.md §3.5).
SAP_SKILL_REGISTRY: dict = {
    "SAP Analytics Cloud – Analytics": _sac_analytics_knowledge,
    "SAP Analytics Cloud – Planning (FP&A)": _sac_planning_knowledge,
    "SAP BW/4HANA": _bw4hana_knowledge,
    "SAP BW on HANA (7.5)": _bw_on_hana_knowledge,
    "SAP BPC (Standard or Embedded)": _bpc_knowledge,
    "SAP Group Reporting": _group_reporting_knowledge,
    "SAP PaPM": _papm_knowledge,
    "SAP Business Data Cloud (BDC)": _bdc_knowledge,
    "SAP Embedded Analytics (CDS / Fiori)": _embedded_analytics_knowledge,
    "SAP ABAP Custom Development": _abap_knowledge,
}

DOMAIN_SKILL_REGISTRY: dict = {
    "finance": _finance_knowledge,
    "sales": _sales_knowledge,
    "procurement": _procurement_knowledge,
    "operations": _operations_knowledge,
    "hr": _hr_knowledge,
}


_EMPTY_SAP_SKILL: dict = {"summary": "", "key_concepts": [], "kpis": [], "sap_objects": [], "common_patterns": []}
_MERGED_LIST_KEYS = ("key_concepts", "kpis", "sap_objects", "common_patterns")


def _normalise_technologies(technology) -> list:
    """Accept a single technology name, a '+'-joined string of several, or a list.

    Returns a clean, order-preserving, duplicate-free list of individual technology names.
    """
    if isinstance(technology, str):
        names = [name.strip() for name in technology.split("+") if name.strip()]
    else:
        names = [name.strip() for name in (technology or []) if name and name.strip()]
    return list(dict.fromkeys(names))


def load_sap_skill(technology) -> dict:
    """Return the knowledge dict for one or more selected SAP technologies.

    Accepts a single technology name, a '+'-joined string of multiple technology
    names (used internally when several technologies are selected), or a list of
    technology names. Knowledge from every matched technology is merged: list-valued
    keys are concatenated (duplicates removed), never overwritten.
    """
    names = _normalise_technologies(technology)
    knowledge_dicts = [SAP_SKILL_REGISTRY[name]() for name in names if name in SAP_SKILL_REGISTRY]

    if not knowledge_dicts:
        return dict(_EMPTY_SAP_SKILL)
    if len(knowledge_dicts) == 1:
        return knowledge_dicts[0]

    merged = {"summary": " ".join(k["summary"] for k in knowledge_dicts if k.get("summary"))}
    for list_key in _MERGED_LIST_KEYS:
        merged[list_key] = list(dict.fromkeys(
            item for k in knowledge_dicts for item in k.get(list_key, [])
        ))
    return merged


def load_all_domain_skills() -> list:
    """Return a list of knowledge dicts for all functional domains (fallback when domain is unknown)."""
    return [{"domain": name, **getter()} for name, getter in DOMAIN_SKILL_REGISTRY.items()]


def load_domain_skills(domains: list) -> list:
    """Return knowledge dicts for only the given detected domains.

    Falls back to all domain skills when `domains` is empty or contains no
    recognised domain name (FR-08).
    """
    recognised = [d for d in (domains or []) if d in DOMAIN_SKILL_REGISTRY]
    if not recognised:
        return load_all_domain_skills()
    return [{"domain": name, **DOMAIN_SKILL_REGISTRY[name]()} for name in recognised]
