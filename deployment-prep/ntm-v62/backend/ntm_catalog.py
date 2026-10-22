"""Public endpoint inventory sourced from approved Cell 228 UI (names only).
No Colab secrets, private source archives, or tool implementations.
"""
import ast
import re
from pathlib import Path

# Exact UI catalog is extracted and pinned from the approved Cell 228 app.py.
# The generated JSON is committed to this package; no runtime AST execution.
import json
DATA = json.loads((Path(__file__).parent/'ui_contract.json').read_text(encoding='utf-8'))
SERVICES = DATA['services']
UI_TOOLS = DATA['tools']
# The independently executed original sources are the ONLY original handlers enabled.
VERIFIED_ORIGINAL = {
    'Generate_Scope_of_Work': ('Construction & Services', 'Construction Scope Builder'),
    'Generate_Construction_Assumptions_Exclusions': ('Construction & Services', 'Construction Assumptions & Exclusions'),
}
RESTRICTED_SERVICES = {'Staff Administration (Restricted)', 'My Documents & Downloads', 'NTM Project Ownership'}
NTM_DENY_ONLY_ORIGINAL = frozenset({'NTM_Business_Assistant', 'NTM_Email_Automation', 'Search_Company_Documents'})
RESTRICTED_PHRASES = ('approval','access management','certificate','audit trail','price list','live price','securely','register','delivery','email','whatsapp')
WORKFLOWS = ('construction','cleaning','property_management','real_estate','training','consulting','logistics',
             'smart_construction','architectural_design','project_ownership','final_quote','general')
AGENTS = ('floor_plan','master_1a','general','construction','pricing','documents','research','cleaning',
          'property_management','real_estate','training','consulting','logistics','smart_construction',
          'architectural_design','project_ownership')

def slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]+','-', value.casefold()).strip('-')

def tool_status(service: str, tool: str) -> str:
    if (service, tool) in VERIFIED_ORIGINAL.values():
        return 'STAFF_AUTH_REQUIRED'
    if service in RESTRICTED_SERVICES or any(word in tool.casefold() for word in RESTRICTED_PHRASES):
        return 'SECURITY_BLOCKED'
    if (service,tool) in VERIFIED_ORIGINAL.values():
        return 'FUNCTIONAL_PASS'
    return 'FUNCTIONAL_UNVERIFIED'

# Exact source-registry names were derived from the historic registry and the
# Cell 227B report. The public application only advertises names, not handlers.
ORIGINAL_TOOL_NAMES = (
    'Auto_Lead_Sender', 'Cameroon_Real_Estate_Support_Assistant',
    'Collect_Detailed_Project_Information', 'Delete_from_Memory',
    'Generate_Comprehensive_NTM_Construction_Quote', 'Generate_Construction_Assumptions_Exclusions',
    'Generate_Final_NTM_Construction_Quote', 'Generate_NTM_Professional_Training_and_Certificate',
    'Generate_NTM_Project_Schedule_and_Progress_Report', 'Generate_NTM_Property_Management_Quote',
    'Generate_NTM_Real_Estate_Agreement_Template', 'Generate_Scope_of_Work',
    'Get_NTM_Location_Information', 'Google_Search', 'Google_Sheets_Add_Single_Row',
    'Load_from_Memory', 'Manage_Customer_Chat_Privacy', 'NTM_Business_Assistant',
    'NTM_Cleaning_Service_Tool', 'NTM_Email_Automation', 'NTM_Property_Construction_Tool',
    'Save_to_Memory', 'Search_Company_Documents', 'Search_NTM_Knowledge_Base',
    'Search_cleaning_and_property_management_quote_template_docx',
    'Search_cleaning_services_docx', 'Search_comprehensive_construction_docx',
    'Search_general_scope_of_work_docx', 'Search_ntm_ai_agent_knowledge_base_docx',
    'Search_ntm_building_options_and_finishes_docx',
    'Search_ntm_services_and_other_docx', 'Search_real_estate_practices_in_cameroon_docx',
    'Send_Cleaning_Service_Quote_to_Customer', 'Send_Property_Management_Quote_to_Customer',
    'Send_Quote_to_Customers', 'Send_Real_Estate_Agreement_to_Customer',
    'Send_WhatsApp_Message', 'Gemini_knowledge_search', 'Gemini_Context_Manager',
    'OpenAI_deep_researcher',
)
assert len(ORIGINAL_TOOL_NAMES) == 40 and len(set(ORIGINAL_TOOL_NAMES))==40
