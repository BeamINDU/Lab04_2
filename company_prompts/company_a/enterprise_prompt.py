import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from company_prompts.base_prompt import BaseCompanyPrompt
from typing import Dict, Any, List
from datetime import datetime

# Import existing components instead of creating new ones
try:
    from refactored_modules.business_logic_mapper import BusinessLogicMapper
    from refactored_modules.schema_discovery import SchemaDiscoveryService
    EXISTING_COMPONENTS_AVAILABLE = True
except ImportError:
    EXISTING_COMPONENTS_AVAILABLE = False

# Import shared logger
from shared_components.logging_config import logger

class EnterprisePrompt(BaseCompanyPrompt):
    """🏦 Enterprise Banking Prompt - ใช้ existing components แทนการสร้างใหม่"""
    
    def __init__(self, company_config: Dict[str, Any]):
        super().__init__(company_config)
        
        # ใช้ existing business logic instead of custom files
        if EXISTING_COMPONENTS_AVAILABLE:
            self.business_mapper = BusinessLogicMapper()
            self.schema_service = SchemaDiscoveryService()
            self.business_rules = self.business_mapper.get_business_logic('company-a')
        else:
            # Fallback to hardcoded rules
            self.business_rules = self._get_fallback_business_rules()
        
        logger.info(f"✅ EnterprisePrompt initialized for {self.company_name}")
    
    def generate_sql_prompt(self, question: str, schema_info: Dict[str, Any]) -> str:
        """🎯 Generate Enterprise SQL prompt using existing logic"""
        
        self.usage_stats['queries_processed'] += 1
        self.usage_stats['last_used'] = datetime.now().isoformat()
        
        # Format schema using existing service if available
        if EXISTING_COMPONENTS_AVAILABLE and hasattr(self, 'schema_service'):
            schema_text = self._format_schema_with_existing_service()
        else:
            schema_text = self._format_schema_fallback(schema_info)
        
        prompt = f"""คุณคือนักวิเคราะห์ระบบ Enterprise Banking สำหรับ {self.company_name}

🏢 บริบทธุรกิจ: ระบบธนาคารและองค์กรขนาดใหญ่  
💰 งบประมาณโปรเจค: 800,000 - 3,000,000+ บาท
🎯 ลูกค้าเป้าหมาย: ธนาคาร, บริษัทใหญ่, E-commerce

{schema_text}

🔧 กฎการสร้าง SQL สำหรับ Enterprise Banking:
{self._get_enterprise_sql_rules()}

💡 Business Rules สำหรับ Enterprise:
{self._format_business_rules()}

คำถาม: {question}

สร้าง PostgreSQL query ที่เน้นการวิเคราะห์ระบบ enterprise:"""

        self.usage_stats['successful_generations'] += 1
        return prompt
    
    def format_response(self, question: str, results: List[Dict], metadata: Dict) -> str:
        """🎨 Format Enterprise response"""
        
        if not results:
            return f"ไม่พบข้อมูลที่ตรงกับคำถาม: {question}"
        
        response = f"📊 การวิเคราะห์ระบบ Enterprise Banking สำหรับ {self.company_name}\n\n"
        
        # แสดงผลลัพธ์
        for i, row in enumerate(results[:15], 1):
            response += f"{i:2d}. "
            for key, value in row.items():
                if 'salary' in key or 'budget' in key:
                    response += f"{key}: {value:,.0f} บาท, "
                else:
                    response += f"{key}: {value}, "
            response = response.rstrip(', ') + "\n"
        
        response += f"\n💡 Enterprise Insights:\n"
        response += f"• จำนวนรายการ: {len(results)} รายการ\n"
        response += f"• ระบบ: Banking & Enterprise Solutions\n"
        response += f"• ข้อมูลจาก: PostgreSQL Database\n"
        
        return response
    
    def _format_schema_with_existing_service(self) -> str:
        """ใช้ existing schema discovery service"""
        try:
            company_schema = self.schema_service.get_enhanced_schema_info('company-a')
            
            formatted = "📊 โครงสร้างฐานข้อมูล Enterprise:\n"
            
            for table_name, table_info in company_schema.get('tables', {}).items():
                formatted += f"• {table_name}: {table_info.get('description', '')}\n"
                for column in table_info.get('columns', [])[:5]:  # แสดง 5 คอลัมน์แรก
                    formatted += f"  - {column}\n"
            
            return formatted
        except Exception as e:
            logger.warning(f"Schema service failed: {e}, using fallback")
            return self._format_schema_fallback({})
    
    def _format_schema_fallback(self, schema_info: Dict) -> str:
        """Fallback schema formatting"""
        return """📊 โครงสร้างฐานข้อมูล Enterprise:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation
• departments: id, name, description, manager_id, budget, location
• clients: id, name, industry, contact_person, contract_value
• skills: id, name, category, description
• employee_skills: employee_id, skill_id, proficiency_level, certified"""
    
    def _format_business_rules(self) -> str:
        """Format business rules from existing mapper or fallback"""
        
        rules_text = ""
        for category, rules in self.business_rules.items():
            rules_text += f"• {category}:\n"
            if isinstance(rules, dict):
                for rule_name, condition in rules.items():
                    rules_text += f"  - {rule_name}: {condition}\n"
            else:
                rules_text += f"  - {rules}\n"
        
        return rules_text
    
    def _get_enterprise_sql_rules(self) -> str:
        """Enterprise-specific SQL rules"""
        return """1. เน้นความปลอดภัยและ compliance
2. ใช้ COALESCE สำหรับ NULL handling  
3. เงินเดือน: แสดงเป็น "xxx,xxx บาท"
4. โปรเจค enterprise: budget > 1,000,000
5. พนักงาน senior: salary > 60,000 OR position ILIKE '%senior%'
6. แผนกหลัก: IT, Management, Sales
7. การวิเคราะห์ performance: เน้น ROI และ efficiency"""
    
    def _get_fallback_business_rules(self) -> Dict[str, Any]:
        """Fallback business rules if existing mapper not available"""
        return {
            'employee_levels': {
                'junior': 'salary < 40000',
                'mid_level': 'salary BETWEEN 40000 AND 60000',
                'senior': 'salary > 60000 OR position ILIKE \'%senior%\'',
                'executive': 'salary > 100000 OR position ILIKE \'%manager%\' OR position ILIKE \'%director%\''
            },
            'project_categories': {
                'small': 'budget < 500000',
                'medium': 'budget BETWEEN 500000 AND 2000000', 
                'large': 'budget > 2000000',
                'enterprise': 'budget > 3000000'
            },
            'critical_departments': ['IT', 'Management', 'Risk Management', 'Compliance']
        }
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """Required by base class"""
        return self.business_rules
    
    def _load_schema_mappings(self) -> Dict[str, Any]:
        """Required by base class"""
        return {
            'core_tables': ['employees', 'projects', 'employee_projects', 'departments'],
            'extended_tables': ['clients', 'skills', 'employee_skills', 'training'],
            'business_views': ['high_value_projects', 'senior_staff', 'critical_allocations']
        }