"""NTM v6.2 bounded API gateway — DO NOT interpret endpoint presence as tool certification.
API is service-to-service only. No WordPress and no caller-supplied staff identity.
"""
from __future__ import annotations
import dataclasses
import hmac
import json
import os
import math
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from ntm_catalog import (SERVICES, UI_TOOLS, VERIFIED_ORIGINAL, RESTRICTED_SERVICES, NTM_DENY_ONLY_ORIGINAL,
                         ORIGINAL_TOOL_NAMES, AGENTS, WORKFLOWS, slug, tool_status)
from ntm_verified_runtime import run_public_tool, chat_public
from ntm_floor_plan_agent import TOOLS as FLOOR_TOOLS, assess_room
from ntm_master_1a_policy import plan_request

class ToolInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project: str = Field(default='Public draft', max_length=120)
    specs: dict[str, Any] = Field(default_factory=dict)

class WorkflowInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    specs: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False

class AgentInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    params: dict[str, Any] = Field(default_factory=dict)
    specs: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False

class EstimateInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    description: str = Field(default='Draft line item',max_length=200)
    quantity: float = Field(ge=0,le=1e12)
    unit_price: float = Field(ge=0,le=1e12)

class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=2400)
    service: str = Field(default='Dashboard & Projects', max_length=110)

app = FastAPI(title='NTM Agent API', version='1.0.0-rc1', description=(
    'Endpoint discovery is complete for Cell 228 UI. Original NTM tool execution is enabled only '
    'for previously independently verified, read-only handlers. Restricted and unverified endpoints fail closed.'))

@app.middleware('http')
async def internal_service_auth(request: Request, call_next):
    # A token authenticates the frontend SERVICE, not its anonymous visitor.
    # Never convert this token into an admin/staff role.
    if request.url.path.startswith('/api/v1/'):
        secret = os.getenv('NTM_API_SERVICE_TOKEN','')
        provided = request.headers.get('X-NTM-Service-Key','')
        if len(secret) < 32 or secret.startswith('REPLACE_') or not hmac.compare_digest(provided,secret):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={'status':'denied','code':'invalid_service_credential'})
    return await call_next(request)

def blocked(code: str, *, forbidden: bool=False):
    raise HTTPException(status_code=403 if forbidden else 503,
                        detail={'status':'denied' if forbidden else 'unavailable','code':code})

def original_execution(name: str, request: ToolInput):
    # The canonical NTM registry marks these originals ADMIN-only.
    # A service-to-service key authenticates the frontend SERVICE, never a staff person.
    # Until a production identity issuer and owner-scoped state are installed, deny.
    blocked('verified_staff_identity_required', forbidden=True)
    entry=VERIFIED_ORIGINAL.get(name)
    if entry is None:
        blocked('original_tool_not_independently_verified')
    if len(json.dumps(request.specs,default=str)) > 5000:
        raise HTTPException(status_code=422,detail={'code':'specifications_too_large'})
    service, tool = entry
    out=run_public_tool(service=service,tool=tool,project=request.project,
                        requirements=json.dumps(request.specs))
    status=out.get('status') if isinstance(out,dict) else None
    if status=='ok': return {'status':'ok','result':out,'original_tool':name,'draft_only':True}
    if status=='needs_details':raise HTTPException(422,detail={'status':status,'message':out.get('display_text','Invalid specs')})
    if status=='denied':blocked('original_tool_permission_denied',forbidden=True)
    blocked('original_tool_runtime_unavailable')

def floor_tool_execute(name: str, params: dict):
    fn=FLOOR_TOOLS.get(name)
    if not fn:blocked('floor_plan_tool_unknown')
    try: result=fn(**params)
    except (ValueError,TypeError,KeyError) as exc:
        raise HTTPException(422,detail={'status':'invalid','code':'floor_plan_parameter_error'}) from exc
    return {'status':'ok','tool':name,'result':result,'screening_only':True}

@app.get('/health/live',tags=['health'])
def health_live():
    return {'status':'alive','app':'ntm-api'}

@app.get('/health/ready',tags=['health'])
def health_ready():
    # NOT a full production readiness claim. Bounded public functionality only.
    secret=os.getenv('NTM_API_SERVICE_TOKEN','')
    ready=len(secret)>=32 and not secret.startswith('REPLACE_')
    return {'status':'limited_public_ready' if ready else 'service_credential_missing',
            'public_api_configured':ready,'full_backend_ready':False,
            'wordpress_enabled':False,'privileged_tools_enabled':False,
            'verified_original_tool_count':len(VERIFIED_ORIGINAL),
            'original_tool_catalog_count':len(ORIGINAL_TOOL_NAMES),
            'staff_identity_issuer_configured':False,'original_tool_execution_enabled':False}

@app.get('/api/v1/catalog/services',tags=['catalog'])
def catalog_services():
    return {'status':'ok','services':[{'name':s,'slug':slug(s),'tools':[
        {'name':tool,'slug':slug(tool), 'status':tool_status(s,tool),
         'endpoint':f'/api/v1/ui/{slug(s)}/tools/{slug(tool)}/execute'}
        for tool in UI_TOOLS.get(s,[])]} for s in SERVICES]}

@app.get('/api/v1/catalog/agents',tags=['catalog'])
def catalog_agents():
    return {'status':'ok','agents':[{'name':a,'endpoint':f'/api/v1/agents/{slug(a)}/invoke',
        'status':'PUBLIC_PLANNING_ONLY' if a in ('master_1a','floor_plan') else 'FUNCTIONAL_UNVERIFIED'}
        for a in AGENTS]}

@app.get('/api/v1/catalog/original-tools',tags=['catalog'])
def catalog_original():
    return {'status':'ok','source_registry_tool_count':40,'standalone_executable_count':2,
            'tools':[{'name':t,'status':'STAFF_AUTH_REQUIRED' if t in VERIFIED_ORIGINAL else ('POLICY_DENIED' if t in NTM_DENY_ONLY_ORIGINAL else 'FUNCTIONAL_UNVERIFIED_OR_RESTRICTED'),
                      'endpoint':f'/api/v1/original-tools/{slug(t)}/execute'} for t in ORIGINAL_TOOL_NAMES]}

@app.get('/api/v1/routes',tags=['catalog'])
def route_map():
    return {'status':'ok','ui_tool_endpoint_count':sum(len(t) for t in UI_TOOLS.values()),
            'original_tool_endpoint_count':len(ORIGINAL_TOOL_NAMES),
            'agent_endpoint_count':len(AGENTS),'workflow_endpoint_count':len(WORKFLOWS),
            'openapi':'/openapi.json','api_docs':'/docs'}

@app.post('/api/v1/chat',tags=['chat'])
def chat(req:ChatInput):
    if req.service not in SERVICES:raise HTTPException(422,detail={'code':'unknown_service'})
    result=chat_public(prompt=req.message,service=req.service)
    if result.get('status')=='ok':return result
    if result.get('status')=='denied':blocked(result.get('reason','chat_denied'),forbidden=True)
    blocked('chat_model_or_runtime_unavailable')

@app.post('/api/v1/workspace/estimates/line-item',tags=['workspace'])
def draft_line_item(req: EstimateInput):
    if not all(math.isfinite(x) for x in (req.quantity,req.unit_price)):
        raise HTTPException(422,detail={'code':'non_finite_amount'})
    total=round(req.quantity*req.unit_price,2)
    if not math.isfinite(total) or total>1e18:
        raise HTTPException(422,detail={'code':'draft_amount_out_of_bounds'})
    return {'status':'ok','description':req.description,'quantity':req.quantity,
            'unit_price_xaf':req.unit_price,'draft_total_xaf':total,'price_verified':False,
            'formal_quotation_approved':False,'disclaimer':'User-supplied rate; engineer/PM approval required.'}

@app.post('/api/v1/artifacts/create',tags=['artifacts'])
def artifact_create(_:ToolInput):
    blocked('owner_scoped_artifact_store_not_configured',forbidden=True)

@app.get('/api/v1/artifacts/{artifact_id}',tags=['artifacts'])
def artifact_get(artifact_id:str):
    blocked('owner_scoped_artifact_store_not_configured',forbidden=True)

# Workflows: 12 individually discoverable, strictly policy-only.
def make_workflow_handler(wf):
    def route(req:WorkflowInput):
        state={'active_workflow':wf,'project_data':{'extracted_specs':req.specs,
            'auto_filled_assumptions':{},'is_confirmed_by_user':req.confirmed}}
        # Never accept gateway or approval attestation from UI.
        outcome=plan_request(state,verified_gateway=False,approval_attested=False)
        return {'status':'ok','workflow':wf,'execution':False,'plan':dataclasses.asdict(outcome)}
    route.__name__='plan_'+wf
    return route
for wf in WORKFLOWS:
    app.add_api_route(f'/api/v1/workflows/{slug(wf)}/plan', make_workflow_handler(wf),
                      methods=['POST'],tags=['workflows'],response_model=None)

# Every UI tab tool has a DISTINCT service-scoped route.
def make_ui_handler(service, tool):
    def route(req:ToolInput):
        status=tool_status(service,tool)
        if status in {'SECURITY_BLOCKED','STAFF_AUTH_REQUIRED'}: blocked('public_operation_restricted',forbidden=True)
        if status!='FUNCTIONAL_PASS': blocked('ui_tool_backend_not_independently_verified')
        orig=next(n for n,entry in VERIFIED_ORIGINAL.items() if entry==(service,tool))
        return original_execution(orig,req)
    route.__name__='ui_'+slug(service).replace('-','_')+'_'+slug(tool).replace('-','_')
    return route
seen=set()
for s,tools in UI_TOOLS.items():
    for t in tools:
        path=f'/api/v1/ui/{slug(s)}/tools/{slug(t)}/execute'
        if path in seen:raise RuntimeError('UI endpoint slug collision: '+path)
        seen.add(path)
        app.add_api_route(path,make_ui_handler(s,t),methods=['POST'],tags=['ui-tools'])

# Actual historic original registry has a dedicated endpoint per name.
def make_original_handler(name):
    def route(req:ToolInput):
        if name in NTM_DENY_ONLY_ORIGINAL or name in VERIFIED_ORIGINAL:
            blocked('original_tool_requires_staff_identity',forbidden=True)
        if name not in VERIFIED_ORIGINAL: blocked('original_tool_not_independently_verified')
        return original_execution(name,req)
    route.__name__='original_'+slug(name).replace('-','_')
    return route
for name in ORIGINAL_TOOL_NAMES:
    app.add_api_route(f'/api/v1/original-tools/{slug(name)}/execute',make_original_handler(name),
                      methods=['POST'],tags=['original-tools'])

# Floor Plan Agent: distinct execute endpoint for each of its four real tools.
def make_floor_tool_handler(name):
    def route(req:AgentInput):return floor_tool_execute(name,req.params)
    route.__name__='floor_'+name
    return route
for name in FLOOR_TOOLS:
    app.add_api_route(f'/api/v1/floor-plan/tools/{slug(name)}/execute',make_floor_tool_handler(name),
                      methods=['POST'],tags=['floor-plan'])

# A distinct invocation endpoint exists for every named agent.
def make_agent_handler(name):
    def route(req:AgentInput):
        if name=='master_1a':
            wf=req.params.get('workflow')
            if wf not in WORKFLOWS:raise HTTPException(422,detail={'code':'unknown_workflow'})
            return make_workflow_handler(wf)(WorkflowInput(specs=req.specs,confirmed=req.confirmed))
        if name=='floor_plan':
            try:
                p=req.params
                report=assess_room(p['room_width'],p['room_length'],p['building_width'],
                                   p['building_length'],p['glazing'],p['openable'])
                return {'status':'ok','agent':'floor_plan','text':report,'certified':False}
            except (ValueError,KeyError,TypeError) as exc:
                raise HTTPException(422,detail={'code':'invalid_floor_plan_parameters'}) from exc
        blocked('agent_runtime_or_tool_closures_not_verified')
    route.__name__='agent_'+slug(name).replace('-','_')
    return route
for agent in AGENTS:
    app.add_api_route(f'/api/v1/agents/{slug(agent)}/invoke',make_agent_handler(agent),
                      methods=['POST'],tags=['agents'])
