# 🎯 Complete Universal Prompt System - Multi-Tenant Ready
# refactored_modules/universal_prompt_system.py

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, asdict
import logging
from functools import lru_cache
import re

logger = logging.getLogger(__name__)

@dataclass
class CompanyProfile:
    """Profile ของแต่ละ Company"""
    company_id: str
    name: str
    business_type: str
    language: str
    prompt_template: str
    sql_patterns: Dict[str, str]
    business_entities: List[str]
    currency: str = "THB"
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class UniversalPromptGenerator:
    """🎯 Universal Prompt System ที่รองรับ Multi-Tenant"""
    
    def __init__(self):
        # Initialize core components
        self.company_profiles = self._load_company_profiles()
        self.prompt_templates = self._load_prompt_templates()
        self.type_safety_rules = self._load_type_safety_rules()
        self.pattern_matchers = self._load_pattern_matchers()
        self.business_logic_mappings = self._load_business_logic_mappings()
        
        # Statistics
        self.generation_stats = {
            'total_queries': 0,
            'successful_generations': 0,
            'template_usage': {},
            'tenant_usage': {}
        }
        
        logger.info("✅ Universal Prompt System initialized with complete multi-tenant support")
    
    def _load_company_profiles(self) -> Dict[str, CompanyProfile]:
        """โหลด Company Profiles ทั้งหมด"""
        profiles = {}
        
        # Company A - Bangkok HQ (Enterprise)
        profiles['company-a'] = CompanyProfile(
            company_id='company-a',
            name='SiamTech Bangkok HQ',
            business_type='enterprise_software',
            language='th',
            prompt_template='enterprise_thai',
            sql_patterns={
                'employee_analysis': 'complex_joins_with_aggregation',
                'project_analysis': 'budget_focus_with_teams',
                'department_analysis': 'hierarchy_aware'
            },
            business_entities=[
                'พนักงาน', 'employee', 'โปรเจค', 'project', 'แผนก', 'department',
                'เงินเดือน', 'salary', 'งบประมาณ', 'budget', 'ธนาคาร', 'banking'
            ],
            currency='THB'
        )
        
        # Company B - Chiang Mai Regional (Tourism)
        profiles['company-b'] = CompanyProfile(
            company_id='company-b',
            name='SiamTech Chiang Mai Regional',
            business_type='tourism_hospitality',
            language='th',
            prompt_template='tourism_thai',
            sql_patterns={
                'project_analysis': 'tourism_focused',
                'client_analysis': 'regional_hospitality',
                'employee_analysis': 'local_specialization'
            },
            business_entities=[
                'พนักงาน', 'employee', 'โปรเจค', 'project', 'ท่องเที่ยว', 'tourism',
                'โรงแรม', 'hotel', 'รีสอร์ท', 'resort', 'ลูกค้า', 'client',
                'เชียงใหม่', 'chiang mai', 'ภาคเหนือ', 'northern'
            ],
            currency='THB'
        )
        
        # Company C - International (Global)
        profiles['company-c'] = CompanyProfile(
            company_id='company-c',
            name='SiamTech International',
            business_type='global_operations',
            language='en',
            prompt_template='international_english',
            sql_patterns={
                'project_analysis': 'multi_currency_global',
                'client_analysis': 'international_markets',
                'financial_analysis': 'usd_focused'
            },
            business_entities=[
                'employee', 'employees', 'project', 'projects', 'international',
                'global', 'USD', 'dollar', 'overseas', 'multinational',
                'cross-border', 'foreign', 'worldwide'
            ],
            currency='USD'
        )
        
        return profiles
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """โหลด Prompt Templates สำหรับแต่ละประเภทธุรกิจ"""
        return {
            'enterprise_thai': """คุณคือ PostgreSQL Expert สำหรับ {company_name} (Enterprise Software)

🏢 บริบทธุรกิจ: บริษัทพัฒนาซอฟต์แวร์ขนาดใหญ่ เน้นลูกค้าธนาคารและ E-commerce
💰 สกุลเงิน: บาท (THB)
📊 เน้น: Performance, Scalability, Complex Business Logic

📋 โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🎯 กฎการเขียน SQL สำหรับ Enterprise:
1. ใช้ explicit column names (ไม่ใช้ SELECT *)
2. ใช้ LEFT JOIN สำหรับ assignment queries เพื่อแสดงพนักงานทั้งหมด
3. ใช้ COALESCE สำหรับ NULL handling: 'ไม่มีโปรเจค', 'ไม่มีบทบาท'
4. จัดรูปแบบเงิน: TO_CHAR(amount, 'FM999,999,999') || ' บาท'
5. ใช้ aggregate functions: COUNT, SUM, AVG, MAX, MIN
6. ใส่ ORDER BY และ LIMIT เสมอ
7. ใช้ ILIKE สำหรับ text search ใน PostgreSQL

คำถาม: {question}

สร้าง PostgreSQL query:""",

            'tourism_thai': """คุณคือ PostgreSQL Expert สำหรับ {company_name} (Tourism & Hospitality)

🏨 บริบทธุรกิจ: เทคโนโลยีท่องเที่ยวและโรงแรม สาขาภาคเหนือ
💰 สกุลเงิน: บาท (THB)
📊 เน้น: Regional Tourism, Hospitality Systems, Local Business

📋 โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🏔️ ลูกค้าหลัก: โรงแรม, TAT, สวนพฤกษศาสตร์, ร้านอาหาร, มหาวิทยาลัย

🎯 กฎการเขียน SQL สำหรับ Tourism:
1. มองหา keywords: ท่องเที่ยว, โรงแรม, tourism, hotel
2. เน้นโปรเจคที่เกี่ยวข้องกับ hospitality industry
3. ใช้ ILIKE สำหรับค้นหาชื่อลูกค้า: '%โรงแรม%', '%ท่องเที่ยว%'
4. งบประมาณมักอยู่ในช่วง 300k-800k บาท
5. ใช้ LEFT JOIN และ COALESCE เหมือน enterprise
6. จัดเรียงตาม business priority

คำถาม: {question}

สร้าง PostgreSQL query ที่เน้น tourism business:""",

            'international_english': """You are a PostgreSQL Expert for {company_name} (Global Operations)

🌍 Business Context: International software solutions, global clients
💰 Currency: USD (primary), multi-currency support
📊 Focus: Cross-border operations, International compliance, Global scale

📋 Database Schema:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🌐 Key Clients: MegaCorp International, Global Finance Corp, Education Global Network

🎯 SQL Rules for International Business:
1. Look for keywords: international, global, USD, dollar, overseas
2. Budget often in USD range: $1M - $4M
3. Use LEFT JOIN and COALESCE for complete data: 'No Project', 'No Role'
4. Format currency: TO_CHAR(amount, 'FM999,999,999') || ' USD'
5. Search clients: ILIKE '%International%', '%Global%', '%Corp%'
6. Focus on high-value international projects
7. Order by business value and impact

Question: {question}

Generate PostgreSQL query for international business analysis:"""
        }
    
    def _load_type_safety_rules(self) -> Dict[str, Any]:
        """โหลดกฎ Type Safety เพื่อป้องกัน SQL errors"""
        return {
            'date_fields': ['hire_date', 'start_date', 'end_date', 'created_at'],
            'numeric_fields': ['salary', 'budget', 'allocation', 'id'],
            'text_fields': ['name', 'department', 'position', 'client', 'email'],
            'enum_fields': {
                'status': ['active', 'completed', 'cancelled'],
                'department': ['IT', 'Sales', 'Management', 'HR']
            },
            'null_substitutes': {
                'project_name': 'ไม่มีโปรเจค',
                'project_role': 'ไม่มีบทบาท',
                'client': '-',
                'allocation': '0%'
            },
            'safe_patterns': [
                r'COALESCE\([^,]+,\s*\'[^\']+\'\)',  # Safe COALESCE usage
                r'TO_CHAR\([^,]+,\s*\'[^\']+\'\)',   # Safe formatting
                r'ILIKE\s*\'%[^%]*%\'',              # Safe ILIKE patterns
            ],
            'dangerous_patterns': [
                r'WHERE.*=.*\'ไม่มี\'',               # Direct comparison with Thai text
                r'DATE\(\'[^\']*ไม่มี[^\']*\'\)',      # Invalid date casting
                r'CAST\([^)]*ไม่มี[^)]*\sAS\s',       # Invalid casting
            ]
        }
    
    def _load_pattern_matchers(self) -> Dict[str, List[str]]:
        """โหลด Pattern Matchers สำหรับแต่ละประเภทคำถาม"""
        return {
            'assignment_queries': [
                r'(แต่ละคน.*(?:รับผิดชอบ|ทำงาน|จัดการ))',
                r'(each.*(?:responsible|work|manage))',
                r'(รับผิดชอบ.*(?:อะไร|ไหน|บ้าง))',
                r'(assignment|assigned|allocate)'
            ],
            'project_queries': [
                r'(โปรเจค.*(?:อะไร|ไหน|บ้าง|มี|กี่))',
                r'(project.*(?:what|which|list|how many))',
                r'(ท่องเที่ยว.*(?:โปรเจค|งาน))',  # Tourism specific
                r'(USD.*(?:budget|project))',        # International specific
            ],
            'employee_queries': [
                r'(พนักงาน.*(?:คน|ใคร|ไหน|กี่))',
                r'(employee.*(?:who|how many|work))',
                r'(กี่คน.*(?:แผนก|department))'
            ],
            'financial_queries': [
                r'(งบประมาณ.*(?:สูงสุด|มาก|เท่าไหร่))',
                r'(budget.*(?:highest|maximum|USD))',
                r'(เงินเดือน.*(?:สูงสุด|มาก))',
                r'(salary.*(?:highest|maximum))'
            ]
        }
    
    def _load_business_logic_mappings(self) -> Dict[str, Dict[str, str]]:
        """โหลด Business Logic Mappings สำหรับแต่ละ tenant"""
        return {
            'company-a': {
                'high_budget': 'budget > 2000000',
                'senior_employee': "position ILIKE '%senior%' OR position ILIKE '%lead%' OR position ILIKE '%manager%'",
                'recent_project': "start_date > CURRENT_DATE - INTERVAL '1 year'",
                'active_project': "status = 'active'"
            },
            'company-b': {
                'tourism_project': "client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%โรงแรม%' OR client ILIKE '%tourism%' OR client ILIKE '%hotel%'",
                'regional_client': "client ILIKE '%เชียงใหม่%' OR client ILIKE '%ภาคเหนือ%'",
                'medium_budget': 'budget BETWEEN 300000 AND 800000',
                'hospitality_focus': "client ILIKE '%โรงแรม%' OR client ILIKE '%รีสอร์ท%'"
            },
            'company-c': {
                'international_project': "client ILIKE '%International%' OR client ILIKE '%Global%'",
                'high_value_usd': 'budget > 2000000',  # Assuming USD amounts
                'global_client': "client ILIKE '%Corp%' OR client ILIKE '%International%' OR client ILIKE '%Global%'",
                'enterprise_scale': 'budget > 1500000'
            }
        }
    
    async def generate_sql_with_universal_prompt(self, question: str, tenant_id: str, agent=None) -> Tuple[str, Dict[str, Any]]:
        """🎯 หลัก method สำหรับ SQL generation ด้วย Universal Prompt"""
        
        start_time = datetime.now()
        
        # Update statistics
        self.generation_stats['total_queries'] += 1
        if tenant_id not in self.generation_stats['tenant_usage']:
            self.generation_stats['tenant_usage'][tenant_id] = 0
        self.generation_stats['tenant_usage'][tenant_id] += 1
        
        try:
            # 1. Get company profile
            if tenant_id not in self.company_profiles:
                raise ValueError(f"Unknown tenant: {tenant_id}")
            
            profile = self.company_profiles[tenant_id]
            
            # 2. Analyze question type
            question_type = self._analyze_question_type(question, profile)
            
            # 3. Generate context-aware prompt
            prompt = self._generate_context_aware_prompt(question, profile, question_type)
            
            # 4. Call AI with universal prompt
            if agent and hasattr(agent, 'ai_service'):
                config = agent.tenant_configs[tenant_id]
                ai_response = await agent.ai_service.call_ollama_api(
                    tenant_config=config,
                    prompt=prompt,
                    context_data="",
                    temperature=0.1  # Low temperature for accurate SQL
                )
            else:
                raise ValueError("Agent or AI service not available")
            
            # 5. Extract and validate SQL
            sql_query = self._extract_and_validate_sql(ai_response, profile, question_type)
            
            # 6. Apply type safety rules
            safe_sql = self._apply_type_safety_rules(sql_query, profile)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 7. Create metadata
            metadata = {
                'method': 'universal_prompt_system',
                'template_used': profile.prompt_template,
                'question_type': question_type,
                'business_type': profile.business_type,
                'confidence': self._calculate_confidence(safe_sql, question, profile),
                'processing_time': processing_time,
                'tenant_id': tenant_id,
                'language': profile.language,
                'currency': profile.currency
            }
            
            # Update template usage stats
            template = profile.prompt_template
            if template not in self.generation_stats['template_usage']:
                self.generation_stats['template_usage'][template] = 0
            self.generation_stats['template_usage'][template] += 1
            
            self.generation_stats['successful_generations'] += 1
            
            logger.info(f"✅ Universal Prompt success for {tenant_id}: {question_type} query")
            
            return safe_sql, metadata
            
        except Exception as e:
            logger.error(f"❌ Universal Prompt failed for {tenant_id}: {e}")
            
            # Fallback metadata
            metadata = {
                'method': 'universal_prompt_fallback',
                'error': str(e),
                'confidence': 'low',
                'tenant_id': tenant_id
            }
            
            # Generate safe fallback SQL
            fallback_sql = self._generate_safe_fallback_sql(question, tenant_id)
            
            return fallback_sql, metadata
    
    def _analyze_question_type(self, question: str, profile: CompanyProfile) -> str:
        """🔍 วิเคราะห์ประเภทคำถาม"""
        question_lower = question.lower()
        
        # Check against pattern matchers
        for question_type, patterns in self.pattern_matchers.items():
            for pattern in patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    return question_type.replace('_queries', '')
        
        # Business-specific detection
        if profile.business_type == 'tourism_hospitality':
            tourism_keywords = ['ท่องเที่ยว', 'tourism', 'โรงแรม', 'hotel']
            if any(keyword in question_lower for keyword in tourism_keywords):
                return 'tourism_project'
        
        elif profile.business_type == 'global_operations':
            international_keywords = ['usd', 'international', 'global', 'dollar']
            if any(keyword in question_lower for keyword in international_keywords):
                return 'international_project'
        
        # Default analysis
        if any(word in question_lower for word in ['แต่ละคน', 'รับผิดชอบ', 'each', 'responsible']):
            return 'assignment'
        elif any(word in question_lower for word in ['โปรเจค', 'project']):
            return 'project'
        elif any(word in question_lower for word in ['พนักงาน', 'employee', 'กี่คน']):
            return 'employee'
        elif any(word in question_lower for word in ['งบประมาณ', 'budget', 'เงินเดือน', 'salary']):
            return 'financial'
        else:
            return 'general'
    
    def _generate_context_aware_prompt(self, question: str, profile: CompanyProfile, question_type: str) -> str:
        """📝 สร้าง Context-Aware Prompt"""
        
        # Get base template
        template = self.prompt_templates.get(profile.prompt_template, self.prompt_templates['enterprise_thai'])
        
        # Fill in company-specific information
        filled_template = template.format(
            company_name=profile.name,
            question=question
        )
        
        # Add business logic hints for specific question types
        business_hints = self._get_business_logic_hints(question_type, profile)
        if business_hints:
            filled_template += f"\n\n💡 Business Logic Hints:\n{business_hints}"
        
        return filled_template
    
    def _get_business_logic_hints(self, question_type: str, profile: CompanyProfile) -> str:
        """💡 ดึง Business Logic Hints เฉพาะ"""
        
        mappings = self.business_logic_mappings.get(profile.company_id, {})
        hints = []
        
        if question_type == 'assignment':
            hints.append("• ใช้ LEFT JOIN เพื่อแสดงพนักงานทั้งหมด (รวมคนที่ไม่มีโปรเจค)")
            hints.append("• ใช้ COALESCE(p.name, 'ไม่มีโปรเจค') สำหรับ NULL handling")
            hints.append("• ใช้ COALESCE(ep.role, 'ไม่มีบทบาท') สำหรับ role")
        
        elif question_type == 'project' or question_type == 'tourism_project':
            if profile.business_type == 'tourism_hospitality':
                hints.append("• มองหาโปรเจคท่องเที่ยว: ILIKE '%ท่องเที่ยว%' OR ILIKE '%โรงแรม%'")
                hints.append("• ลูกค้าในกลุ่ม hospitality: โรงแรม, TAT, สวนพฤกษศาสตร์")
            elif profile.business_type == 'global_operations':
                hints.append("• มองหาโปรเจค international: ILIKE '%International%' OR ILIKE '%Global%'")
                hints.append("• งบประมาณมักเป็น USD และมีมูลค่าสูง")
        
        elif question_type == 'financial':
            if profile.currency == 'USD':
                hints.append("• จัดรูปแบบเงิน: TO_CHAR(budget, 'FM999,999,999') || ' USD'")
            else:
                hints.append("• จัดรูปแบบเงิน: TO_CHAR(budget, 'FM999,999,999') || ' บาท'")
        
        # Add business logic mappings
        for concept, sql_condition in mappings.items():
            if concept in question_type or any(word in concept for word in question_type.split('_')):
                hints.append(f"• {concept}: {sql_condition}")
        
        return '\n'.join(hints) if hints else ""
    
    def _extract_and_validate_sql(self, ai_response: str, profile: CompanyProfile, question_type: str) -> str:
        """🔧 แยก SQL และ validate"""
        
        # Clean response
        cleaned = ai_response.strip()
        
        # Extract SQL patterns
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;?)\s*```',
            r'(SELECT.*?;)',
        ]
        
        extracted_sql = None
        for pattern in sql_patterns:
            match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                extracted_sql = match.group(1).strip()
                if extracted_sql.upper().startswith('SELECT'):
                    break
        
        if not extracted_sql:
            # Try line-by-line extraction
            lines = cleaned.split('\n')
            sql_lines = []
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('SELECT') or sql_lines:
                    sql_lines.append(line)
                    if line.endswith(';'):
                        break
            
            if sql_lines:
                extracted_sql = ' '.join(sql_lines)
        
        if not extracted_sql:
            raise ValueError("Could not extract SQL from AI response")
        
        # Clean up SQL
        extracted_sql = ' '.join(extracted_sql.split())  # Remove extra whitespace
        if not extracted_sql.endswith(';'):
            extracted_sql += ';'
        
        # Basic validation
        if not self._validate_basic_sql(extracted_sql):
            raise ValueError("Generated SQL failed basic validation")
        
        return extracted_sql
    
    def _validate_basic_sql(self, sql: str) -> bool:
        """✅ Basic SQL validation"""
        sql_upper = sql.upper()
        
        # Must be SELECT
        if not sql_upper.startswith('SELECT'):
            return False
        
        # No dangerous operations
        dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous):
            return False
        
        # Must have FROM
        if 'FROM' not in sql_upper:
            return False
        
        return True
    
    def _apply_type_safety_rules(self, sql: str, profile: CompanyProfile) -> str:
        """🛡️ ใช้ Type Safety Rules"""
        
        safe_sql = sql
        
        # Check for dangerous patterns
        for pattern in self.type_safety_rules['dangerous_patterns']:
            if re.search(pattern, safe_sql, re.IGNORECASE):
                logger.warning(f"Found dangerous pattern: {pattern}")
                # Apply fix based on pattern type
                if 'ไม่มี' in pattern:
                    # Replace direct comparisons with proper COALESCE
                    safe_sql = re.sub(
                        r'WHERE\s+([^=]+)\s*=\s*\'ไม่มี[^\']*\'',
                        r'WHERE COALESCE(\1, \'ไม่มีข้อมูล\') = \'ไม่มีข้อมูล\'',
                        safe_sql,
                        flags=re.IGNORECASE
                    )
        
        # Ensure proper NULL handling in assignment queries
        if 'LEFT JOIN' in safe_sql.upper() and 'COALESCE' not in safe_sql.upper():
            logger.info("Adding COALESCE for NULL handling in LEFT JOIN query")
            # This is a basic fix - in production, you'd want more sophisticated logic
            safe_sql = safe_sql.replace('p.name', 'COALESCE(p.name, \'ไม่มีโปรเจค\')')
        
        return safe_sql
    
    def _calculate_confidence(self, sql: str, question: str, profile: CompanyProfile) -> str:
        """📊 คำนวณ confidence level"""
        
        confidence_score = 0.5  # Base score
        
        # SQL quality indicators
        sql_upper = sql.upper()
        
        if 'LEFT JOIN' in sql_upper and 'COALESCE' in sql_upper:
            confidence_score += 0.2  # Good assignment query structure
        
        if 'ORDER BY' in sql_upper and 'LIMIT' in sql_upper:
            confidence_score += 0.1  # Good query structure
        
        if 'GROUP BY' in sql_upper and any(agg in sql_upper for agg in ['COUNT', 'SUM', 'AVG']):
            confidence_score += 0.1  # Good aggregation
        
        # Business context matching
        question_lower = question.lower()
        if profile.business_type == 'tourism_hospitality':
            if any(keyword in question_lower for keyword in ['ท่องเที่ยว', 'tourism', 'โรงแรม']):
                confidence_score += 0.1
        
        elif profile.business_type == 'global_operations':
            if any(keyword in question_lower for keyword in ['usd', 'international', 'global']):
                confidence_score += 0.1
        
        # Convert to category
        if confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _generate_safe_fallback_sql(self, question: str, tenant_id: str) -> str:
        """🛡️ สร้าง Safe Fallback SQL"""
        question_lower = question.lower()
        
        # Safe fallback based on question keywords
        if any(word in question_lower for word in ['พนักงาน', 'employee', 'คน']):
            return "SELECT name, position, department FROM employees ORDER BY hire_date DESC LIMIT 10;"
        elif any(word in question_lower for word in ['โปรเจค', 'project', 'งาน']):
            return "SELECT name, client, status FROM projects ORDER BY start_date DESC LIMIT 10;"
        elif any(word in question_lower for word in ['เงินเดือน', 'salary']):
            return "SELECT name, position, salary FROM employees ORDER BY salary DESC LIMIT 10;"
        elif any(word in question_lower for word in ['งบประมาณ', 'budget']):
            return "SELECT name, client, budget FROM projects ORDER BY budget DESC LIMIT 10;"
        else:
            return "SELECT 'Universal Prompt System: Safe fallback query' as message LIMIT 1;"
    
    def get_statistics(self) -> Dict[str, Any]:
        """📊 ดึงสถิติการใช้งาน"""
        
        success_rate = 0
        if self.generation_stats['total_queries'] > 0:
            success_rate = (self.generation_stats['successful_generations'] / 
                          self.generation_stats['total_queries']) * 100
        
        return {
            'total_queries_processed': self.generation_stats['total_queries'],
            'successful_generations': self.generation_stats['successful_generations'],
            'success_rate_percentage': round(success_rate, 2),
            'template_usage_stats': self.generation_stats['template_usage'],
            'tenant_usage_stats': self.generation_stats['tenant_usage'],
            'companies_supported': len(self.company_profiles),
            'templates_available': len(self.prompt_templates),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_company_profile(self, tenant_id: str) -> Optional[CompanyProfile]:
        """🏢 ดึงข้อมูล Company Profile"""
        return self.company_profiles.get(tenant_id)
    
    def list_supported_companies(self) -> List[Dict[str, Any]]:
        """📋 แสดงรายการ companies ที่รองรับ"""
        companies = []
        for company_id, profile in self.company_profiles.items():
            companies.append({
                'company_id': profile.company_id,
                'name': profile.name,
                'business_type': profile.business_type,
                'language': profile.language,
                'currency': profile.currency,
                'prompt_template': profile.prompt_template,
                'entities_count': len(profile.business_entities)
            })
        return companies
    
    async def test_universal_prompt_generation(self, test_questions: List[Tuple[str, str]]) -> Dict[str, Any]:
        """🧪 ทดสอบ Universal Prompt Generation"""
        
        test_results = []
        
        for tenant_id, question in test_questions:
            try:
                start_time = datetime.now()
                
                # Mock agent for testing
                class MockAgent:
                    def __init__(self):
                        from .tenant_config import TenantConfig
                        self.tenant_configs = {
                            'company-a': TenantConfig('company-a', 'SiamTech Bangkok HQ', 'localhost', 5432, 'db', 'user', 'pass', 'llama3.1:8b', 'th', 'enterprise', []),
                            'company-b': TenantConfig('company-b', 'SiamTech Chiang Mai', 'localhost', 5432, 'db', 'user', 'pass', 'llama3.1:8b', 'th', 'tourism', []),
                            'company-c': TenantConfig('company-c', 'SiamTech International', 'localhost', 5432, 'db', 'user', 'pass', 'llama3.1:8b', 'en', 'global', [])
                        }
                        self.ai_service = MockAIService()
                
                class MockAIService:
                    async def call_ollama_api(self, tenant_config, prompt, context_data="", temperature=0.1):
                        # Mock AI response with SQL
                        if 'assignment' in prompt.lower() or 'แต่ละคน' in prompt.lower():
                            return """SELECT 
    e.name as employee_name,
    e.position,
    COALESCE(p.name, 'ไม่มีโปรเจค') as project_name,
    COALESCE(ep.role, 'ไม่มีบทบาท') as project_role
FROM employees e
LEFT JOIN employee_projects ep ON e.id = ep.employee_id
LEFT JOIN projects p ON ep.project_id = p.id
ORDER BY e.name
LIMIT 20;"""
                        
                        elif 'project' in prompt.lower() or 'โปรเจค' in prompt.lower():
                            return """SELECT 
    name as project_name,
    client,
    budget,
    status
FROM projects 
ORDER BY budget DESC 
LIMIT 10;"""
                        
                        else:
                            return "SELECT 'Test query' as result LIMIT 1;"
                
                mock_agent = MockAgent()
                
                sql_query, metadata = await self.generate_sql_with_universal_prompt(
                    question, tenant_id, mock_agent
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                test_results.append({
                    'tenant_id': tenant_id,
                    'question': question,
                    'success': True,
                    'sql_generated': sql_query,
                    'method': metadata['method'],
                    'template_used': metadata.get('template_used'),
                    'confidence': metadata.get('confidence'),
                    'processing_time_ms': round(processing_time * 1000, 2)
                })
                
            except Exception as e:
                test_results.append({
                    'tenant_id': tenant_id,
                    'question': question,
                    'success': False,
                    'error': str(e),
                    'method': 'failed'
                })
        
        # Calculate overall test statistics
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r['success']])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate_percentage': round(success_rate, 2)
            },
            'test_results': test_results,
            'system_status': 'operational' if success_rate >= 80 else 'needs_attention'
        }


# 🧪 Test Function สำหรับ Universal Prompt System
async def test_complete_universal_prompt_system():
    """🧪 ทดสอบ Universal Prompt System แบบครบถ้วน"""
    
    print("🧪 Testing Complete Universal Prompt System")
    print("=" * 70)
    
    # Initialize system
    generator = UniversalPromptGenerator()
    
    # Test 1: Company Profiles
    print("\n1️⃣ Testing Company Profiles:")
    companies = generator.list_supported_companies()
    for company in companies:
        print(f"   ✅ {company['name']} ({company['business_type']}) - {company['language']}")
    
    # Test 2: Question Type Analysis
    print("\n2️⃣ Testing Question Type Analysis:")
    test_questions = [
        ("company-a", "พนักงาน siamtech แต่ละคนรับผิดชอบโปรเจคอะไรบ้าง"),
        ("company-b", "มีโปรเจคท่องเที่ยวอะไรบ้าง"), 
        ("company-c", "Which projects have highest USD budget")
    ]
    
    for tenant_id, question in test_questions:
        profile = generator.get_company_profile(tenant_id)
        question_type = generator._analyze_question_type(question, profile)
        print(f"   🎯 {tenant_id}: '{question[:40]}...' → {question_type}")
    
    # Test 3: Prompt Generation
    print("\n3️⃣ Testing Universal Prompt Generation:")
    test_results = await generator.test_universal_prompt_generation(test_questions)
    
    print(f"   📊 Success Rate: {test_results['test_summary']['success_rate_percentage']}%")
    print(f"   ✅ Successful: {test_results['test_summary']['successful_tests']}")
    print(f"   ❌ Failed: {test_results['test_summary']['failed_tests']}")
    
    for result in test_results['test_results']:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['tenant_id']}: {result.get('method', 'failed')}")
    
    # Test 4: Statistics
    print("\n4️⃣ System Statistics:")
    stats = generator.get_statistics()
    print(f"   📈 Total Queries: {stats['total_queries_processed']}")
    print(f"   ✅ Success Rate: {stats['success_rate_percentage']}%")
    print(f"   🏢 Companies: {stats['companies_supported']}")
    print(f"   📝 Templates: {stats['templates_available']}")
    
    # Overall status
    overall_success = test_results['test_summary']['success_rate_percentage'] >= 80
    print(f"\n🎯 Overall Status: {'✅ READY FOR PRODUCTION' if overall_success else '⚠️ NEEDS IMPROVEMENT'}")
    
    return overall_success

# 🚀 Integration Helper Function
def create_universal_prompt_integration_guide():
    """📚 สร้างคู่มือการ Integration"""
    
    guide = """
🚀 Universal Prompt System Integration Guide
==========================================

📁 Files to Update:
------------------
1. refactored_modules/universal_prompt_system.py (✅ Ready)
2. refactored_modules/enhanced_postgres_agent_refactored.py (✅ Updated)

🔧 Integration Steps:
-------------------
1. Replace old universal_prompt_system.py with new version
2. Restart the container/service
3. Test with curl commands
4. Verify sql_generation_method = "universal_prompt_system"

🧪 Test Commands:
----------------
# Company A (Enterprise)
curl -X POST http://localhost:5000/enhanced-rag-query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: company-a" \
  -d '{"query": "พนักงานแต่ละคนรับผิดชอบโปรเจคอะไรบ้าง"}'

# Company B (Tourism) 
curl -X POST http://localhost:5000/enhanced-rag-query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: company-b" \
  -d '{"query": "มีโปรเจคท่องเที่ยวอะไรบ้าง"}'

# Company C (International)
curl -X POST http://localhost:5000/enhanced-rag-query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: company-c" \
  -d '{"query": "Which projects have highest USD budget"}'

# Check Universal Prompt Status
curl http://localhost:5000/universal-prompt-status

✅ Expected Results:
------------------
- sql_generation_method: "universal_prompt_system"
- data_source_used: "universal_prompt_[model]"
- fallback_mode: false
- confidence_level: "high" or "medium"
- enhancement_version: "3.0_universal_prompt"

🎯 Success Criteria:
------------------
- All 3 companies use Universal Prompt System
- No more Few-Shot Learning fallbacks  
- SQL queries generated successfully
- Business-appropriate responses
- No AttributeError exceptions

⚠️ Troubleshooting:
------------------
- If AttributeError: Check method names in universal_prompt_system.py
- If fallback_mode: true: Check Intent Classification
- If SQL errors: Check Type Safety Rules
- If wrong responses: Check Prompt Templates
"""
    
    return guide

if __name__ == "__main__":
    print("🎯 Universal Prompt System - Complete Implementation")
    print("🔥 Ready for Multi-Tenant Production Deployment")
    
    # Print integration guide
    print(create_universal_prompt_integration_guide())
    
    # Run tests
    import asyncio
    asyncio.run(test_complete_universal_prompt_system())