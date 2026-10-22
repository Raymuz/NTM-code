"""NTM Master 1A: pure, fail-closed planning layer. Not a tool executor.
Place after Cell 226 in the running Colab. Keeps original dispatch unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional
import json, subprocess, sys, tempfile, textwrap, pathlib, hashlib

class Workflow(str, Enum):
    CONSTRUCTION='construction'; CLEANING='cleaning'; PROPERTY_MANAGEMENT='property_management'
    REAL_ESTATE='real_estate'; TRAINING='training'; CONSULTING='consulting'
    LOGISTICS='logistics'; SMART_CONSTRUCTION='smart_construction'
    ARCHITECTURAL_DESIGN='architectural_design'; PROJECT_OWNERSHIP='project_ownership'
    FINAL_QUOTE='final_quote'; GENERAL='general'

HARD_REQUIRED_SPECS={
    Workflow.CONSTRUCTION:('project_type','area_sqm','location'),
    Workflow.CLEANING:('property_type','area_sqm','location'),
    Workflow.PROPERTY_MANAGEMENT:('property_type','location','monthly_rent_xaf'),
    Workflow.REAL_ESTATE:('transaction_type','property_type','location'),
    Workflow.TRAINING:('module',),
    Workflow.CONSULTING:('advisory_topic','location'),
    Workflow.LOGISTICS:('logistics_type','location'),
    Workflow.SMART_CONSTRUCTION:('project_type','location','technology_scope'),
    Workflow.ARCHITECTURAL_DESIGN:('plan_type','area_sqm','location'),
    Workflow.PROJECT_OWNERSHIP:('project_type','location'),
    Workflow.FINAL_QUOTE:('project_type','area_sqm','location','finish_level'),
    Workflow.GENERAL:(),
}
AUTOFILLABLE_SPECS={
    Workflow.CONSTRUCTION:('finish_level','floors','bedrooms','timeline_months','budget_xaf'),
    Workflow.CLEANING:('cleaning_type','frequency','team_size'),
    Workflow.PROPERTY_MANAGEMENT:('units','management_scope','fee_percent'),
    Workflow.REAL_ESTATE:('budget_xaf','timeline_months','agreement_type'),
    Workflow.TRAINING:('participant_count','delivery_mode','start_date'),
    Workflow.CONSULTING:('engagement_length_days','delivery_mode'),
    Workflow.LOGISTICS:('load_type','distance_km','frequency'),
    Workflow.SMART_CONSTRUCTION:('finish_level','timeline_months','integration_level'),
    Workflow.ARCHITECTURAL_DESIGN:('floors','bedrooms','style','revision_rounds'),
    Workflow.PROJECT_OWNERSHIP:('ownership_stake_percent','oversight_frequency'),
    Workflow.FINAL_QUOTE:('floors','bedrooms','timeline_months','payment_schedule'),
    Workflow.GENERAL:(),
}
QUOTE_TOOL={
    Workflow.CONSTRUCTION:'generate_construction_quote',
    Workflow.FINAL_QUOTE:'generate_final_construction_quote',
    Workflow.CLEANING:'calculate_cleaning_quote',
    Workflow.PROPERTY_MANAGEMENT:'generate_property_management_quote',
    Workflow.REAL_ESTATE:'generate_real_estate_agreement',
    Workflow.TRAINING:'generate_training_enrollment',
    Workflow.CONSULTING:'generate_consulting_proposal',
    Workflow.LOGISTICS:'generate_logistics_quote',
    Workflow.SMART_CONSTRUCTION:'generate_smart_construction_quote',
    Workflow.ARCHITECTURAL_DESIGN:'generate_design_package_quote',
    Workflow.PROJECT_OWNERSHIP:'generate_ownership_model_proposal',
}
QUESTIONS={
    'project_type':'What type of project is this?', 'area_sqm':'What is the approximate area in square meters?',
    'location':'Which town or quarter is the project in?', 'plan_type':'Do you need a new design, modification or full architectural package?',
    'advisory_topic':'What would you like advice on?',
    'logistics_type':'What materials, equipment or site support do you need?',
    'technology_scope':'Which smart systems are you considering?',
    'property_type':'What kind of property is it?',
    'monthly_rent_xaf':'What is the current or expected monthly rent in XAF?',
    'transaction_type':'Are you buying, selling, renting or listing?',
    'module':'Which training module are you interested in?',
    'finish_level':'What finish level do you require?',
}

@dataclass(frozen=True)
class Plan:
    action: str
    workflow: str
    question: Optional[str]=None
    missing: tuple[str,...]=()
    proposed_tool: Optional[str]=None
    reason: str=''
    metadata: dict[str,Any]=field(default_factory=dict)

def _workflow(v):
    try: return Workflow(v)
    except (ValueError,TypeError): return None

def plan_request(state: Mapping[str,Any], *, verified_gateway: bool=False, approval_attested: bool=False) -> Plan:
    """Pure decision policy. User state/claimed role never grants authority.
    No I/O, dispatch, quote, lead logging, or approval happens here.
    """
    if not isinstance(state, Mapping): raise TypeError('state_must_be_mapping')
    wf=_workflow(state.get('active_workflow'))
    if wf is None: return Plan('clarify_service','',question='Which NTM service do you need?',reason='no_valid_workflow')
    if wf==Workflow.GENERAL: return Plan('knowledge',wf.value,reason='general_information_only')
    p=state.get('project_data') or {}
    if not isinstance(p, Mapping): return Plan('reject',wf.value,reason='invalid_project_data')
    specs=p.get('extracted_specs') or {}
    if not isinstance(specs, Mapping): return Plan('reject',wf.value,reason='invalid_specs')
    missing=tuple(k for k in HARD_REQUIRED_SPECS[wf] if specs.get(k) in (None,'',[]))
    if missing: return Plan('ask_spec',wf.value,question=QUESTIONS.get(missing[0],f'Please provide {missing[0]}.'),missing=missing,reason='hard_required_fields_missing')
    assumptions=p.get('auto_filled_assumptions') or {}
    if not isinstance(assumptions,Mapping): return Plan('reject',wf.value,reason='invalid_assumptions')
    unsupported=set(assumptions)-set(AUTOFILLABLE_SPECS[wf])
    if unsupported: return Plan('reject',wf.value,reason='unapproved_autofill_fields',metadata={'fields':sorted(unsupported)})
    if not p.get('is_confirmed_by_user'):
        return Plan('confirm_details',wf.value,reason='explicit_project_confirmation_required',metadata={'assumption_fields':sorted(assumptions)})
    # Customer confirmation of project specs is NOT approval of an NTM formal quote.
    if wf==Workflow.FINAL_QUOTE and not (verified_gateway and approval_attested):
        return Plan('engineer_review',wf.value,reason='final_quote_requires_server_verified_engineer_pm_approval')
    proposed=QUOTE_TOOL.get(wf)
    if not proposed: return Plan('reject',wf.value,reason='no_workflow_tool_mapping')
    # Tool availability and authorization must be verified by protected backend.
    if not verified_gateway: return Plan('handoff_required',wf.value,proposed_tool=proposed,reason='server_verified_gateway_required')
    return Plan('request_authorized_tool_resolution',wf.value,proposed_tool=proposed,reason='tool_registry_and_policy_must_verify_before_execution')

# The source module is never an identity provider or public endpoint.
if __name__ == '__main__':
    def s(wf,specs=None,confirm=False,assume=None,role=None):
        return {'active_workflow':wf, 'role':role, 'project_data':{'extracted_specs':specs or {}, 'auto_filled_assumptions':assume or {},'is_confirmed_by_user':confirm}}
    assert len(Workflow)==12 and len(HARD_REQUIRED_SPECS)==12
    assert plan_request(s('architectural_design')).action=='ask_spec'
    assert plan_request(s('architectural_design',{'plan_type':'new','area_sqm':140,'location':'Douala'})).action=='confirm_details'
    assert plan_request(s('architectural_design',{'plan_type':'new','area_sqm':140,'location':'Douala'},True)).action=='handoff_required'
    assert plan_request(s('architectural_design',{'plan_type':'new','area_sqm':140,'location':'Douala'},True),verified_gateway=True).proposed_tool=='generate_design_package_quote'
    assert plan_request(s('final_quote',{'project_type':'build','area_sqm':140,'location':'Douala','finish_level':'high-end'},True,role='admin'),verified_gateway=True).action=='engineer_review'
    assert plan_request(s('final_quote',{'project_type':'build','area_sqm':140,'location':'Douala','finish_level':'high-end'},True),verified_gateway=True,approval_attested=True).action=='request_authorized_tool_resolution'
    assert plan_request(s('consulting',{'advisory_topic':'planning','location':'Yaounde'},True,{'unapproved_price':5})).action=='reject'
    assert plan_request(s('general')).action=='knowledge'
    for wf in Workflow:
        if wf==Workflow.GENERAL: continue
        assert plan_request(s(wf.value)).action=='ask_spec'
    print('MASTER_1A_SELF_TEST_PASS: service coverage 12/12; hard-spec, consent, role spoof, authorization and approval checks passed')
