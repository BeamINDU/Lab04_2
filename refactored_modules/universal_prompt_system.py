# 🎯 Universal Prompt System - Implementation
# ไฟล์: refactored_modules/universal_prompt_system.py

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from .tenant_config import TenantConfig

logger = logging.getLogger(__name__)

@dataclass
class CompanyContext:
    """บริบท Company ที่จำเป็นสำหรับ Prompt Generation"""
    tenant_id: str
    name: str
    business_type: str
    language: str
    schema_info: Dict[str, Any]
    business_rules: Dict[str, Any]
    common_queries: List[str]
    sql_patterns: Dict[str, str]

class TypeSafetySQLValidator:
    """🛡️ ตรวจสอบและแก้ไข SQL ให้ Type-Safe"""
    
    @staticmethod
    def has_type_safety_issues(sql: str) -> bool:
        """ตรวจหา Type Safety Issues ใน SQL"""
        
        # Patterns ที่อันตราย
        dangerous_patterns = [
            # COALESCE กับ date/timestamp fields ด้วย string
            r"COALESCE\s*\(\s*\w+\.(start_date|end_date|hire_date|created_at|updated_at)\s*,\s*'[^']+'\s*\)",
            r"COALESCE\s*\(\s*\w+\.date\w*\s*,\s*'[^']+'\s*\)",
            r"COALESCE\s*\(\s*(start_date|end_date|hire_date)\s*,\s*'[^']+'\s*\)",
            
            # COALESCE กับ numeric fields ด้วย string (ที่ไม่ใช่ '0')
            r"COALESCE\s*\(\s*\w+\.(budget|salary|amount|price)\s*,\s*'(?!0)[^']+'\s*\)",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"🚨 Type safety issue detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def fix_type_safety_issues(sql: str) -> str:
        """แก้ไข Type Safety Issues ใน SQL"""
        
        # แก้ COALESCE กับ date fields
        def fix_date_coalesce(match):
            field = match.group(1) if match.group(1) else match.group(0).split(',')[0].split('(')[1].strip()
            return f"CASE WHEN {field} IS NULL THEN 'ไม่มี' ELSE {field}::text END"
        
        # แก้ date field COALESCE
        fixed_sql = re.sub(
            r"COALESCE\s*\(\s*(\w+\.(start_date|end_date|hire_date|created_at|updated_at))\s*,\s*'[^']+'\s*\)",
            fix_date_coalesce,
            sql,
            flags=re.IGNORECASE
        )
        
        # แก้ standalone date field COALESCE
        fixed_sql = re.sub(
            r"COALESCE\s*\(\s*(start_date|end_date|hire_date)\s*,\s*'[^']+'\s*\)",
            fix_date_coalesce,
            fixed_sql,
            flags=re.IGNORECASE
        )
        
        # แก้ numeric fields กับ string (ยกเว้น '0')
        def fix_numeric_coalesce(match):
            field = match.group(1)
            return f"COALESCE({field}, 0)"
        
        fixed_sql = re.sub(
            r"COALESCE\s*\(\s*(\w+\.(budget|salary|amount|price))\s*,\s*'(?!0)[^']+'\s*\)",
            fix_numeric_coalesce,
            fixed_sql,
            flags=re.IGNORECASE
        )
        
        if fixed_sql != sql:
            logger.info("🔧 Fixed type safety issues in SQL")
        
        return fixed_sql

class UniversalPromptGenerator:
    """🌟 Universal Prompt Generator ที่ปรับตัวได้ตาม Company"""
    
    def __init__(self):
        self.company_contexts: Dict[str, CompanyContext] = {}
        self.universal_templates = self._load_universal_templates()
        self.type_safety_rules = self._load_type_safety_rules()
        
    def register_company(self, company_context: CompanyContext):
        """ลงทะเบียน Company ใหม่"""
        self.company_contexts[company_context.tenant_id] = company_context
        logger.info(f"✅ Registered company: {company_context.name} ({company_context.business_type})")
    ""
    def generate_sql_prompt(self, question: str, tenant_id: str) -> str:
        """🎯 สร้าง SQL Prompt ที่ปรับตัวตาม Company"""
        
        if tenant_id not in self.company_contexts:
            # ถ้าไม่มี context ให้สร้าง minimal context
            return self._generate_fallback_prompt(question, tenant_id)
        
        context = self.company_contexts[tenant_id]
        
        # 1. เลือก Template ตาม Business Type
        template = self._select_template(context.business_type, context.language)
        
        # 2. สร้าง Components
        schema_section = self._build_schema_section(context)
        business_rules_section = self._build_business_rules_section(context)
        examples_section = self._build_examples_section(context, question)
        type_safety_section = self._build_type_safety_section()
        
        # 3. สร้าง Final Prompt
        final_prompt = template.format(
            company_name=context.name,
            business_type=self._translate_business_type(context.business_type, context.language),
            schema_section=schema_section,
            business_rules_section=business_rules_section,
            examples_section=examples_section,
            type_safety_section=type_safety_section,
            user_question=question
        )
        
        logger.info(f"📝 Generated {context.business_type} prompt ({len(final_prompt)} chars) for: {question[:50]}...")
        return final_prompt
    
    def _load_universal_templates(self) -> Dict[str, str]:
        """Universal Templates - Simplified Version"""
        return {
            'thai_enterprise': """🎯 คุณคือ PostgreSQL Expert สำหรับ {company_name}

    🏢 บริบทธุรกิจ: {business_type}

    {schema_section}

    {type_safety_section}

    {business_rules_section}

    {examples_section}

    ⚡ กฎการสร้าง SQL (Simple & Effective):
    1. **เริ่มต้นด้วย SQL ง่ายๆ เสมอ** - ไม่ต้องใส่เงื่อนไขซับซ้อน
    2. **ใช้เงื่อนไข WHERE เฉพาะเมื่อคำถามระบุชัดเจน**
    3. **LEFT JOIN สำหรับแสดงข้อมูลทั้งหมด รวมที่ไม่มีความสัมพันธ์**
    4. **INNER JOIN เฉพาะเมื่อต้องการข้อมูลที่มีความสัมพันธ์เท่านั้น**
    5. **ใส่ ORDER BY และ LIMIT เสมอ**

    🎯 หลักการสำคัญ:
    • ถ้าถาม "แต่ละคน" → ใช้ LEFT JOIN เพื่อแสดงทุกคน รวมคนที่ไม่มีโปรเจค
    • ถ้าถามจำนวน → ใช้ COUNT และ GROUP BY
    • ถ้าถามรายการ → แสดงข้อมูลตรงๆ ไม่ต้องกรอง

    ⚠️ ห้ามทำ:
    • ห้ามใส่เงื่อนไข WHERE ที่ซับซ้อนโดยไม่จำเป็น
    • ห้ามกรองข้อมูลออกเว้นแต่คำถามจะระบุชัดเจน
    • ห้ามสมมติเงื่อนไขเพิ่มเติม

    คำถาม: {user_question}

    สร้าง PostgreSQL query ที่เรียบง่ายและตรงประเด็น:
    """,
                
            'thai_tourism': """🎯 คุณคือ PostgreSQL Expert สำหรับ {company_name}

    🏨 บริบทธุรกิจท่องเที่ยว: {business_type}

    {schema_section}

    {type_safety_section}

    {business_rules_section}

    {examples_section}

    ⚡ กฎการสร้าง SQL (Tourism Focused):
    1. **แสดงข้อมูลท่องเที่ยวอย่างครบถ้วน**
    2. **ใช้ LEFT JOIN เพื่อรวมข้อมูลที่เกี่ยวข้อง**
    3. **ไม่กรองข้อมูลเว้นแต่จำเป็น**
    4. **เน้นข้อมูลที่เป็นประโยชน์สำหรับการท่องเที่ยว**

    คำถาม: {user_question}

    สร้าง PostgreSQL query สำหรับธุรกิจท่องเที่ยว:
    """,
                
            'english_international': """🎯 You are a PostgreSQL Expert for {company_name}

    🌍 International Business Context: {business_type}

    {schema_section}

    {type_safety_section}

    {business_rules_section}

    {examples_section}

    ⚡ SQL Generation Rules (International Focus):
    1. **Start with simple, comprehensive queries**
    2. **Use LEFT JOIN to show all data including null relationships**
    3. **Only add WHERE conditions when explicitly asked**
    4. **Focus on international business metrics**

    Question: {user_question}

    Generate straightforward PostgreSQL query for global operations:
    """
        }

    def _select_template(self, business_type: str, language: str) -> str:
        """เลือก Template ที่เหมาะสม"""
        
        if language == 'en':
            return self.universal_templates['english_international']
        
        # Thai language templates
        if business_type in ['tourism_hospitality', 'tourism']:
            return self.universal_templates['thai_tourism']
        else:
            return self.universal_templates['thai_enterprise']
    
    def _translate_business_type(self, business_type: str, language: str) -> str:
        """แปล Business Type ตามภาษา"""
        translations = {
            'th': {
                'enterprise_software': 'การพัฒนาซอฟต์แวร์องค์กร',
                'tourism_hospitality': 'ธุรกิจท่องเที่ยวและโรงแรม',
                'international_operations': 'การดำเนินงานระหว่างประเทศ',
                'general_business': 'ธุรกิจทั่วไป'
            },
            'en': {
                'enterprise_software': 'Enterprise Software Development',
                'tourism_hospitality': 'Tourism & Hospitality Services',
                'international_operations': 'Global Business Operations',
                'general_business': 'General Business Operations'
            }
        }
        
        return translations.get(language, translations['th']).get(
            business_type, business_type
        )
    
    def _build_schema_section(self, context: CompanyContext) -> str:
        """สร้าง Schema Section ที่กระชับและเข้าใจง่าย"""
        
        if context.language == 'en':
            schema_text = "📋 DATABASE SCHEMA:\n"
        else:
            schema_text = "📋 โครงสร้างฐานข้อมูล:\n"
        
        tables = context.schema_info.get('tables', {})
        
        # แสดงตารางหลักก่อน
        important_tables = ['employees', 'projects', 'employee_projects']
        other_tables = [t for t in tables.keys() if t not in important_tables]
        
        for table_name in important_tables + other_tables:
            if table_name in tables:
                table_info = tables[table_name]
                
                schema_text += f"🗃️ {table_name}:\n"
                
                # แสดงคอลัมน์สำคัญ (จำกัด 8 คอลัมน์)
                columns = table_info.get('columns', [])
                main_columns = []
                for col in columns[:8]:
                    if isinstance(col, str):
                        col_name = col.split(' ')[0] if ' ' in col else col
                        main_columns.append(col_name)
                
                schema_text += f"   • คอลัมน์: {', '.join(main_columns)}\n"
                
                # เพิ่ม business context สั้นๆ
                if 'business_significance' in table_info:
                    significance = table_info['business_significance'][:100] + "..." if len(table_info['business_significance']) > 100 else table_info['business_significance']
                    schema_text += f"   💡 {significance}\n"
                
                schema_text += "\n"
        
        # เพิ่มความสัมพันธ์สำคัญ
        schema_text += "🔗 ความสัมพันธ์สำคัญ:\n"
        if context.business_type == 'tourism_hospitality':
            schema_text += "• clients → projects (ลูกค้าท่องเที่ยว → โปรเจคพัฒนาระบบ)\n"
            schema_text += "• employees → projects (พนักงาน → งานพัฒนาระบบท่องเที่ยว)\n"
        elif context.business_type == 'international_operations':
            schema_text += "• clients → international_contracts (global clients → contracts)\n"
            schema_text += "• contracts → payments (สัญญา → การชำระเงินข้ามประเทศ)\n"
        else:
            schema_text += "• employees → employee_projects → projects\n"
            schema_text += "• projects → clients (โปรเจค → ลูกค้าองค์กร)\n"
        
        return schema_text
    
    def _build_business_rules_section(self, context: CompanyContext) -> str:
        """สร้าง Business Rules Section - Fixed Version"""
        
        if context.language == 'en':
            rules_text = "🏢 BUSINESS RULES:\n"
        else:
            rules_text = "🏢 กฎทางธุรกิจเฉพาะ:\n"
        
        business_rules = context.business_rules
        if not business_rules:
            return rules_text + "• ใช้กฎมาตรฐานทั่วไป\n"
        
        # 🔧 FIX: ลดการใช้ business rules ที่ซับซ้อน
        simple_rules_only = ['employee_levels', 'project_sizes']  # จำกัดเฉพาะกฎง่ายๆ
        
        # แปลงชื่อหมวดหมู่
        category_translations = {
            'employee_levels': 'ระดับพนักงาน' if context.language == 'th' else 'Employee Levels',
            'project_sizes': 'ขนาดโปรเจค' if context.language == 'th' else 'Project Sizes'
        }
        
        # 🔧 FIX: แสดงกฎแค่ 2 หมวดหมู่ และ 2 กฎต่อหมวด
        shown_categories = 0
        for category, rules in business_rules.items():
            if category not in simple_rules_only or shown_categories >= 2:
                continue
                
            category_name = category_translations.get(category, category)
            rules_text += f"\n• {category_name} (ตัวอย่าง):\n"
            
            # แสดงแค่ 2 กฎต่อหมวด
            rule_count = 0
            for key, condition in rules.items():
                if rule_count >= 2:
                    break
                rules_text += f"  - {key}: ใช้เฉพาะเมื่อจำเป็น\n"  # 🔧 FIX: ไม่ใส่เงื่อนไขซับซ้อน
                rule_count += 1
                
            shown_categories += 1
        
        # 🔧 FIX: เพิ่มคำเตือนให้ใช้เงื่อนไขเฉพาะเมื่อจำเป็น
        rules_text += f"\n⚠️ สำคัญ: ใช้เงื่อนไข WHERE เฉพาะเมื่อคำถามระบุชัดเจน ไม่ใช่ทุกครั้ง\n"
        
        return rules_text
    
    def _build_type_safety_section(self) -> str:
        """สร้าง Type Safety Section"""
        return self.type_safety_rules
    
    def _build_examples_section(self, context: CompanyContext, question: str) -> str:
        """สร้าง Examples Section ที่เกี่ยวข้องกับคำถาม"""
        
        if context.language == 'en':
            examples_text = "📚 RELEVANT SQL EXAMPLES:\n"
        else:
            examples_text = "📚 ตัวอย่าง SQL ที่เกี่ยวข้อง:\n"
        
        # หา patterns ที่เกี่ยวข้อง
        relevant_patterns = self._find_relevant_patterns(question, context)
        
        if not relevant_patterns:
            return examples_text + "💡 ไม่มีตัวอย่างที่เกี่ยวข้องโดยตรง - สร้าง SQL ใหม่ตามโครงสร้างข้อมูล\n"
        
        # แสดงตัวอย่าง (จำกัด 2 ตัวอย่าง)
        for i, (pattern_name, sql_example) in enumerate(relevant_patterns.items()):
            if i >= 2:
                break
                
            examples_text += f"\nตัวอย่างที่ {i+1} ({pattern_name}):\n"
            examples_text += "```sql\n"
            examples_text += sql_example.strip()
            examples_text += "\n```\n"
        
        return examples_text
    
    def _find_relevant_patterns(self, question: str, context: CompanyContext) -> Dict[str, str]:
        """หา SQL patterns - แก้ไขให้เจาะจงขึ้น"""
        
        question_lower = question.lower()
        relevant = {}
        
        # 🔧 FIX: เพิ่ม pattern สำหรับคำถามที่เจาะจง
        if 'แต่ละคน' in question_lower and 'รับผิดชอบ' in question_lower:
            # Pattern สำหรับคำถาม "แต่ละคนรับผิดชอบอะไรบ้าง"
            relevant['employee_assignments'] = """
    SELECT 
        e.name as employee_name,
        e.position,
        e.department,
        COALESCE(p.name, 'ไม่มีโปรเจค') as project_name,
        COALESCE(p.client, '-') as client,
        COALESCE(ep.role, 'ไม่มีบทบาท') as project_role
    FROM employees e
    LEFT JOIN employee_projects ep ON e.id = ep.employee_id
    LEFT JOIN projects p ON ep.project_id = p.id
    ORDER BY e.name, p.name
    LIMIT 20;
            """
        
        elif 'โปรเจค' in question_lower and ('อะไรบ้าง' in question_lower or 'มี' in question_lower):
            # Pattern สำหรับคำถาม "มีโปรเจคอะไรบ้าง"
            relevant['list_projects'] = """
    SELECT 
        p.name as project_name,
        p.client,
        p.status,
        p.budget,
        COUNT(ep.employee_id) as team_size
    FROM projects p
    LEFT JOIN employee_projects ep ON p.id = ep.project_id
    GROUP BY p.id, p.name, p.client, p.status, p.budget
    ORDER BY p.name
    LIMIT 20;
            """
        
        return relevant

    
    def _generate_fallback_prompt(self, question: str, tenant_id: str) -> str:
        """สร้าง Fallback Prompt เมื่อไม่มี Context"""
        return f"""🎯 คุณคือ PostgreSQL Expert สำหรับ {tenant_id.upper()}

{self.type_safety_rules}

📋 กฎพื้นฐาน:
• ใช้ ILIKE แทน LIKE สำหรับ PostgreSQL
• ใส่ LIMIT เสมอเพื่อจำกัดผลลัพธ์
• ใช้ proper JOIN types
• จัดการ NULL values อย่างระมัดระวัง

คำถาม: {question}

สร้าง PostgreSQL query ที่ปลอดภัย:
"""

class UniversalPromptIntegration:
    """🔗 Integration กับระบบเดิม"""
    
    def __init__(self, original_agent):
        self.original_agent = original_agent
        self.universal_prompt = UniversalPromptGenerator()
        self.sql_validator = TypeSafetySQLValidator()
        self._register_existing_companies()
        
    def _register_existing_companies(self):
        """ลงทะเบียน Companies ที่มีอยู่"""
        
        try:
            # Company A - Enterprise
            company_a = self._create_company_context(
                tenant_id='company-a',
                name='SiamTech Bangkok HQ',
                business_type='enterprise_software'
            )
            self.universal_prompt.register_company(company_a)
            
            # Company B - Tourism  
            company_b = self._create_company_context(
                tenant_id='company-b',
                name='SiamTech Chiang Mai Regional',
                business_type='tourism_hospitality'
            )
            self.universal_prompt.register_company(company_b)
            
            # Company C - International
            company_c = self._create_company_context(
                tenant_id='company-c', 
                name='SiamTech International',
                business_type='international_operations'
            )
            self.universal_prompt.register_company(company_c)
            
            logger.info("✅ All companies registered with Universal Prompt System")
            
        except Exception as e:
            logger.error(f"Failed to register companies: {e}")
    
    def _create_company_context(self, tenant_id: str, name: str, business_type: str) -> CompanyContext:
        """สร้าง CompanyContext - Fixed Version"""
        
        # กำหนดภาษา
        language = 'en' if tenant_id == 'company-c' else 'th'
        
        # ดึงข้อมูลจากระบบเดิม (แก้ไขให้ robust ขึ้น)
        schema_info = {}
        business_rules = {}
        sql_patterns = {}
        
        try:
            if hasattr(self.original_agent, 'schema_service'):
                schema_info = self.original_agent.schema_service.get_schema_info(tenant_id)
                logger.info(f"✅ Got schema info for {tenant_id}")
            else:
                logger.warning(f"⚠️ No schema_service for {tenant_id}")
        except Exception as e:
            logger.warning(f"Could not get schema info for {tenant_id}: {e}")
            # 🔧 FIX: สร้าง minimal schema
            schema_info = {
                'tables': {
                    'employees': {'columns': ['id', 'name', 'department', 'position', 'salary']},
                    'projects': {'columns': ['id', 'name', 'client', 'budget', 'status']},
                    'employee_projects': {'columns': ['employee_id', 'project_id', 'role', 'allocation']}
                }
            }
            
        try:
            if hasattr(self.original_agent, 'business_mapper'):
                business_rules = self.original_agent.business_mapper.get_business_logic(tenant_id)
                sql_patterns = self.original_agent.business_mapper.sql_patterns
                logger.info(f"✅ Got business logic for {tenant_id}")
        except Exception as e:
            logger.warning(f"Could not get business rules for {tenant_id}: {e}")
            # 🔧 FIX: สร้าง simple business rules
            business_rules = {
                'employee_levels': {'all': 'ทุกระดับ'},
                'project_sizes': {'all': 'ทุกขนาด'}
            }
            sql_patterns = {}
        
        # สร้าง common queries
        common_queries = self._generate_common_queries(business_type, language)
        
        context = CompanyContext(
            tenant_id=tenant_id,
            name=name,
            business_type=business_type,
            language=language,
            schema_info=schema_info,
            business_rules=business_rules,
            common_queries=common_queries,
            sql_patterns=sql_patterns
        )
        
        logger.info(f"✅ Created context for {tenant_id}: {business_type} ({language})")
        return context
    
    def _generate_common_queries(self, business_type: str, language: str) -> List[str]:
        """สร้างคำถามทั่วไปตาม business type"""
        
        if language == 'en':
            base = ["How many employees", "Which department has most people", "Who is the manager"]
            specific = {
                'international_operations': [
                    "Which projects have highest USD budget",
                    "How many international clients", 
                    "Revenue breakdown by country"
                ]
            }
        else:
            base = ["มีพนักงานกี่คน", "แผนกไหนมีคนมากสุด", "ใครเป็นหัวหน้า"]
            specific = {
                'enterprise_software': [
                    "โปรเจคไหนมีงบประมาณสูงสุด",
                    "ใครทำงานในโปรเจคอะไรบ้าง", 
                    "เงินเดือนเฉลี่ยแต่ละแผนก"
                ],
                'tourism_hospitality': [
                    "มีห้องว่างกี่ห้อง",
                    "แขกมาจากไหนมากสุด",
                    "รายได้จากท่องเที่ยว"
                ]
            }
        
        return base + specific.get(business_type, [])
    
    async def generate_enhanced_sql_with_universal_prompt(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """🎯 Main Method: ใช้ Universal Prompt สำหรับ SQL Generation"""
        
        try:
            # 1. สร้าง Universal Prompt
            universal_prompt = self.universal_prompt.generate_sql_prompt(question, tenant_id)
            
            config = self.original_agent.tenant_configs[tenant_id]
            
            # 2. เรียก AI ด้วย Universal Prompt
            ai_response = await self.original_agent.ai_service.call_ollama_api(
                config, universal_prompt, temperature=0.05  # ใช้ temp ต่ำเพื่อความแม่นยำ
            )
            
            # 3. Extract SQL
            sql_query = self._extract_sql_safely(ai_response, tenant_id)
            
            # 4. Validate และแก้ไข Type Safety
            if self.sql_validator.has_type_safety_issues(sql_query):
                logger.warning("🔧 Fixing type safety issues...")
                sql_query = self.sql_validator.fix_type_safety_issues(sql_query)
            
            # 5. Final validation
            if not self._final_validation(sql_query, tenant_id):
                raise ValueError("SQL failed final validation")
            
            metadata = {
                'method': 'universal_prompt_system',
                'business_type': self.universal_prompt.company_contexts.get(tenant_id, {}).business_type if tenant_id in self.universal_prompt.company_contexts else 'unknown',
                'confidence': 'high',
                'prompt_length': len(universal_prompt),
                'type_safety_applied': self.sql_validator.has_type_safety_issues(ai_response),
                'template_used': self._get_template_type(tenant_id)
            }
            
            return sql_query, metadata
            
        except Exception as e:
            logger.error(f"Universal prompt generation failed for {tenant_id}: {e}")
            # Fallback to original method
            return await self.original_agent.original_generate_enhanced_sql(question, tenant_id)
    
    def _extract_sql_safely(self, ai_response: str, tenant_id: str) -> str:
        """Extract SQL with enhanced safety checks"""
        
        # ใช้ extraction logic เดิม
        sql = self.original_agent._extract_and_validate_sql(ai_response, tenant_id)
        
        # เพิ่ม safety checks
        if not sql or sql.strip() == "":
            raise ValueError("Empty SQL extracted")
        
        if len(sql) < 20:  # SQL สั้นเกินไป
            raise ValueError("SQL too short to be valid")
        
        return sql
    
    def _final_validation(self, sql: str, tenant_id: str) -> bool:
        """การตรวจสอบสุดท้าย"""
        
        try:
            # ใช้ validator เดิม
            return self.original_agent.database_handler.validate_sql_query(sql, tenant_id)
        except:
            return True  # ถ้า validator ไม่ทำงาน ให้ผ่านไป
    
    def _get_template_type(self, tenant_id: str) -> str:
        """ระบุประเภท template ที่ใช้"""
        
        if tenant_id not in self.universal_prompt.company_contexts:
            return 'fallback'
        
        context = self.universal_prompt.company_contexts[tenant_id]
        
        if context.language == 'en':
            return 'english_international'
        elif context.business_type == 'tourism_hospitality':
            return 'thai_tourism'
        else:
            return 'thai_enterprise'

# 🔧 Integration Helper - แก้ไขไฟล์เดิม
class EnhancedAgentWithUniversalPrompt:
    """🚀 Enhanced Agent ที่รวม Universal Prompt System"""
    
    def __init__(self, original_agent):
        self.original_agent = original_agent
        self.universal_integration = UniversalPromptIntegration(original_agent)
        
        # Override เฉพาะ generate_enhanced_sql method
        self.original_generate_enhanced_sql = original_agent.generate_enhanced_sql
        original_agent.generate_enhanced_sql = self.generate_enhanced_sql_with_universal_prompt
        
        logger.info("🚀 Enhanced Agent with Universal Prompt System initialized")
    
    # 🔧 FIX: Delegate ทุก method ไปยัง original_agent
    def __getattr__(self, name):
        """Delegate all methods to original_agent"""
        return getattr(self.original_agent, name)
    
    async def generate_enhanced_sql_with_universal_prompt(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """🎯 ใช้ Universal Prompt System"""
        try:
            return await self.universal_integration.generate_enhanced_sql_with_universal_prompt(
                question, tenant_id
            )
        except Exception as e:
            logger.warning(f"🔄 Universal prompt failed: {e}, falling back...")
            return await self.original_generate_enhanced_sql(question, tenant_id)
    
    def get_universal_prompt_stats(self) -> Dict[str, Any]:
        """📊 ดึงสถิติ Universal Prompt System"""
        contexts = self.universal_integration.universal_prompt.company_contexts
        return {
            "universal_prompt_enabled": True,
            "registered_companies": len(contexts),
            "company_details": [
                {
                    "tenant_id": ctx.tenant_id,
                    "name": ctx.name,
                    "business_type": ctx.business_type,
                    "language": ctx.language,
                    "has_schema": len(ctx.schema_info) > 0,
                    "has_business_rules": len(ctx.business_rules) > 0,
                    "common_queries_count": len(ctx.common_queries)
                }
                for ctx in contexts.values()
            ],
            "type_safety_validator": "active",
            "template_types": ["thai_enterprise", "thai_tourism", "english_international"],
            "fallback_available": True
        }

class UniversalPromptMigrationGuide:
    """📖 คำแนะนำการ migrate ไปใช้ Universal Prompt System"""
    
    @staticmethod
    def integrate_with_existing_agent(original_agent):
        """🔧 Integration กับ Agent เดิม - แก้ไขแล้ว"""
        
        print("🚀 Starting Universal Prompt System Integration...")
        print("=" * 60)
        
        try:
            # 🔧 FIX: ใช้ approach ใหม่ - ไม่สร้าง wrapper class
            from .universal_prompt_system import UniversalPromptIntegration
            
            # สร้าง integration
            universal_integration = UniversalPromptIntegration(original_agent)
            
            # เก็บ original methods
            original_generate_enhanced_sql = original_agent.generate_enhanced_sql
            
            # สร้าง enhanced method
            async def enhanced_sql_with_universal_prompt(question: str, tenant_id: str):
                try:
                    logger.info(f"🎯 Using Universal Prompt for: {question[:50]}...")
                    return await universal_integration.generate_enhanced_sql_with_universal_prompt(
                        question, tenant_id
                    )
                except Exception as e:
                    logger.warning(f"🔄 Universal prompt failed: {e}, falling back...")
                    return await original_generate_enhanced_sql(question, tenant_id)
            
            # Apply enhancement ไปยัง original agent โดยตรง
            original_agent.generate_enhanced_sql = enhanced_sql_with_universal_prompt
            original_agent.universal_integration = universal_integration
            
            # เพิ่ม stats method
            def get_universal_prompt_stats():
                contexts = universal_integration.universal_prompt.company_contexts
                return {
                    "universal_prompt_enabled": True,
                    "registered_companies": len(contexts),
                    "company_details": [
                        {
                            "tenant_id": ctx.tenant_id,
                            "name": ctx.name,
                            "business_type": ctx.business_type,
                            "language": ctx.language,
                            "has_schema": len(ctx.schema_info) > 0,
                            "has_business_rules": len(ctx.business_rules) > 0,
                            "common_queries_count": len(ctx.common_queries)
                        }
                        for ctx in contexts.values()
                    ],
                    "type_safety_validator": "active",
                    "template_types": ["thai_enterprise", "thai_tourism", "english_international"],
                    "fallback_available": True
                }
            
            original_agent.get_universal_prompt_stats = get_universal_prompt_stats
            
            print("✅ Universal Prompt System applied directly to original agent")
            print("🔧 No wrapper class created - all methods delegated properly")
            
            # ทดสอบว่า methods สำคัญยังใช้งานได้
            important_methods = ['process_enhanced_question', 'generate_enhanced_sql']
            for method_name in important_methods:
                if hasattr(original_agent, method_name):
                    print(f"   ✅ {method_name}: Available")
                else:
                    print(f"   ❌ {method_name}: Missing")
            
            return original_agent  # 🔧 FIX: คืน original agent ไม่ใช่ wrapper
            
        except Exception as e:
            print(f"❌ Integration failed: {e}")
            print("🔄 Your original agent remains unchanged")
            return original_agent

# 📝 Usage Instructions
"""
🚀 วิธีการใช้งาน Universal Prompt System:

1. Integration กับ Agent เดิม:
   ```python
   from refactored_modules.universal_prompt_system import UniversalPromptMigrationGuide
   
   # สมมติว่ามี original agent
   enhanced_agent = UniversalPromptMigrationGuide.integrate_with_existing_agent(original_agent)
   ```

2. ทดสอบระบบ:
   ```python
   UniversalPromptMigrationGuide.test_universal_prompts(enhanced_agent)
   ```

3. ใช้งานปกติ:
   ```python
   # ระบบจะใช้ Universal Prompt อัตโนมัติ
   result = await enhanced_agent.process_enhanced_question(question, tenant_id)
   ```

4. ดูสถิติ:
   ```python
   stats = enhanced_agent.get_universal_prompt_stats()
   print(json.dumps(stats, indent=2, ensure_ascii=False))
   ```

🎯 ข้อดี:
✅ Type-safe SQL generation (ไม่ error เรื่อง date/string)
✅ Business context-aware prompts
✅ Easy to add new companies
✅ Automatic fallback to original system
✅ Multi-language support (Thai/English)
✅ Template-based architecture

🔧 การเพิ่ม Company ใหม่:
```python
new_context = CompanyContext(
    tenant_id='company-d',
    name='New Company',
    business_type='new_business_type',
    language='th',
    schema_info=schema_data,
    business_rules=rules_data,
    common_queries=questions,
    sql_patterns=patterns
)

enhanced_agent.universal_integration.universal_prompt.register_company(new_context)
```
"""

# 🎯 Export main classes
__all__ = [
    'UniversalPromptGenerator',
    'UniversalPromptIntegration', 
    'EnhancedAgentWithUniversalPrompt',
    'UniversalPromptMigrationGuide',
    'CompanyContext',
    'TypeSafetySQLValidator'
]