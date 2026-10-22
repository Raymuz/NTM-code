"""NTM Floor Plan Agent — public deterministic assistance, not BIM/code certification.
The four tools and allowed handoffs match the supplied HF guide.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import math
import os

FLOOR_PLAN_SYSTEM_PROMPT = (
    'Assist with preliminary architectural floor-plan calculations and feasibility screening. '
    'Use metric units. Never assert code compliance, structural adequacy or valid geometry '
    'based solely on these checks. Do not fabricate drawings, window measurements or permits. '
    'Handoffs are planning proposals only until the protected backend approves routing.'
)
MAX_AGENT_STEPS = max(1, min(16, int(os.getenv('MAX_AGENT_STEPS', '8'))))
MAX_HANDOFFS = max(0, min(5, int(os.getenv('MAX_HANDOFFS', '3'))))

@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    instructions: str
    tools: list[str]
    allowed_handoffs: list[str]

AGENTS: dict[str, AgentDefinition] = {}
TOOLS: dict[str, Callable] = {}

def register_agent(agent: AgentDefinition) -> None:
    if agent.name in AGENTS:
        raise ValueError('agent_already_registered')
    AGENTS[agent.name] = agent

def _positive(value, label):
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(label + '_invalid') from None
    if not math.isfinite(val) or val <= 0 or val > 10000:
        raise ValueError(label + '_out_of_bounds')
    return val

def calculate_room_area(width_m: float, length_m: float):
    w = _positive(width_m, 'width_m')
    l = _positive(length_m, 'length_m')
    return {'ok': True, 'area_sqm': round(w*l, 3), 'width_m':w, 'length_m':l}

def validate_room_dimensions(width_m: float, length_m: float, building_width_m: float, building_length_m:float):
    w = _positive(width_m, 'width_m'); l = _positive(length_m, 'length_m')
    bw = _positive(building_width_m, 'building_width_m'); bl = _positive(building_length_m, 'building_length_m')
    return {'ok':True, 'fits_individual_envelope': w<=bw and l<=bl,
            'limitations':'Does not verify room placement, overlaps, circulation or local building-code minimums.'}

def check_daylight(window_glazed_area_sqm: float, room_area_sqm: float):
    w = float(window_glazed_area_sqm)
    r = _positive(room_area_sqm, 'room_area_sqm')
    if not math.isfinite(w) or w < 0: raise ValueError('glazed_area_invalid')
    ratio = w/r
    return {'ok':True, 'glazed_to_floor_ratio':round(ratio,4),
            'screening_only': True,
            'note':'Informational ratio, not a daylight-factor calculation or code-compliance assessment.'}

def check_ventilation(openable_window_area_sqm:float, room_area_sqm:float):
    w = float(openable_window_area_sqm); r=_positive(room_area_sqm,'room_area_sqm')
    if not math.isfinite(w) or w<0: raise ValueError('opening_area_invalid')
    return {'ok':True, 'openable_to_floor_ratio':round(w/r,4),
            'screening_only':True,
            'note':'Ratio alone cannot establish air changes, airflow or ventilation-code compliance.'}

TOOLS.update({
    'calculate_room_area':calculate_room_area,
    'validate_room_dimensions':validate_room_dimensions,
    'check_daylight':check_daylight,
    'check_ventilation':check_ventilation,
})
register_agent(AgentDefinition(
    name='floor_plan',
    description='Generates preliminary floor-plan metrics and validates input dimensions; does not produce permit drawings.',
    instructions=FLOOR_PLAN_SYSTEM_PROMPT,
    tools=['calculate_room_area', 'validate_room_dimensions','check_daylight','check_ventilation'],
    allowed_handoffs=['construction','pricing','documents'],
))

def assess_room(room_width, room_length, building_width, building_length, glazing, openable):
    area=calculate_room_area(room_width,room_length)
    geom=validate_room_dimensions(room_width,room_length,building_width,building_length)
    daylight=check_daylight(glazing,area['area_sqm'])
    ventilation=check_ventilation(openable,area['area_sqm'])
    return ('### Floor Plan Agent — Preliminary Room Review\n\n'
            f"**Room area:** {area['area_sqm']:,.2f} m²\n\n"
            f"**Fits the building's individual width/length envelope:** {'Yes' if geom['fits_individual_envelope'] else 'No'}\n\n"
            f"**Glazed opening / floor ratio:** {daylight['glazed_to_floor_ratio']*100:.1f}%\n\n"
            f"**Openable area / floor ratio:** {ventilation['openable_to_floor_ratio']*100:.1f}%\n\n"
            '**Limitations:** Does not establish daylight quality, cross-ventilation, room clearances, structural safety, or regulatory compliance. '\
            'All handoffs to pricing, construction and documents require separate backend authorization.')
