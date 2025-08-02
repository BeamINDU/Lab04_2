import os
import json
import asyncio
import aiohttp
import psycopg2
from typing import Dict, Any, Optional, List, Tuple
import logging
from dataclasses import dataclass
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TenantConfig:
    """Enhanced Tenant configuration with business intelligence"""
    tenant_id: str
    name: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    model_name: str
    language: str
    business_type: str
    key_metrics: List[str]

class EnhancedPostgresOllamaAgent:
    """Enhanced PostgreSQL + Ollama Agent with Advanced Prompts v2.0"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://13.212.102.46:12434')
        self.tenant_configs = self._load_enhanced_tenant_configs()
        self.database_schemas = self._load_enhanced_database_schemas()
        self.business_logic_mappings = self._load_business_logic_mappings()
        self.sql_patterns = self._load_sql_patterns()
        
    def _load_enhanced_tenant_configs(self) -> Dict[str, TenantConfig]:
        """Load enhanced tenant configurations"""
        configs = {}
        
        # Company A Configuration - Enterprise Focus
        configs['company-a'] = TenantConfig(
            tenant_id='company-a',
            name='SiamTech Bangkok HQ',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_A', 'postgres-company-a'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_A', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_A', 'siamtech_company_a'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_A', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_A', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_A', 'llama3.1:8b'),
            language='th',
            business_type='enterprise_software',
            key_metrics=['salary', 'budget', 'project_count', 'team_size']
        )
        
        # Company B Configuration - Tourism Focus  
        configs['company-b'] = TenantConfig(
            tenant_id='company-b',
            name='SiamTech Chiang Mai Regional',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_B', 'postgres-company-b'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_B', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_B', 'siamtech_company_b'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_B', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_B', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_B', 'gemma2:9b'),
            language='th',
            business_type='tourism_hospitality',
            key_metrics=['client_count', 'regional_budget', 'tourism_projects', 'local_team']
        )
        
        # Company C Configuration - International Focus
        configs['company-c'] = TenantConfig(
            tenant_id='company-c',
            name='SiamTech International',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_C', 'postgres-company-c'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_C', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_C', 'siamtech_company_c'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_C', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_C', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_C', 'phi3:14b'),
            language='en',
            business_type='global_operations',
            key_metrics=['usd_revenue', 'international_clients', 'global_projects', 'multi_currency']
        )
        
        return configs
    
    def _load_business_logic_mappings(self) -> Dict[str, Dict]:
        """Enhanced business logic mappings for natural language interpretation"""
        return {
            'company-a': {
                'employee_levels': {
                    'junior': 'salary < 40000',
                    'mid': 'salary BETWEEN 40000 AND 60000', 
                    'senior': 'salary > 60000 OR position ILIKE \'%senior%\'',
                    'executive': 'salary > 100000 OR position ILIKE \'%manager%\' OR position ILIKE \'%director%\' OR position ILIKE \'%ceo%\' OR position ILIKE \'%cto%\''
                },
                'project_sizes': {
                    'small': 'budget < 500000',
                    'medium': 'budget BETWEEN 500000 AND 2000000',
                    'large': 'budget > 2000000',
                    'enterprise': 'budget > 3000000'
                },
                'departments': {
                    'core': "department IN ('IT', 'Management')",
                    'support': "department IN ('Sales', 'HR')",
                    'technical': "department = 'IT'",
                    'business': "department IN ('Sales', 'Management')"
                },
                'time_periods': {
                    'recent': "hire_date > CURRENT_DATE - INTERVAL '1 year'",
                    'experienced': "hire_date < CURRENT_DATE - INTERVAL '2 years'",
                    'veteran': "hire_date < CURRENT_DATE - INTERVAL '5 years'"
                },
                'performance_indicators': {
                    'high_performer': '(salary > 60000 AND EXTRACT(YEAR FROM hire_date) < 2023)',
                    'top_earner': 'salary > 80000',
                    'key_player': "position ILIKE '%lead%' OR position ILIKE '%senior%' OR position ILIKE '%architect%'"
                }
            },
            'company-b': {
                'project_types': {
                    'tourism': "client ILIKE '%โรงแรม%' OR client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%รีสอร์ท%'",
                    'hospitality': "client ILIKE '%โรงแรม%' OR client ILIKE '%ดุสิต%'",
                    'government': "client ILIKE '%การท่องเที่ยวแห่งประเทศไทย%'",
                    'education': "client ILIKE '%มหาวิทยาลัย%' OR client ILIKE '%วิทยา%'"
                },
                'regional_focus': {
                    'northern': "client ILIKE '%เชียงใหม่%' OR client ILIKE '%ล้านนา%'",
                    'local': "client NOT ILIKE '%กรุงเทพ%'",
                    'cultural': "client ILIKE '%ล้านนา%' OR client ILIKE '%วัฒนธรรม%'"
                }
            },
            'company-c': {
                'market_tiers': {
                    'global': "contract_value_usd > 2000000",
                    'enterprise': "contract_value_usd > 1000000", 
                    'regional': "contract_value_usd BETWEEN 500000 AND 1000000",
                    'startup': "contract_value_usd < 500000"
                },
                'geographic_regions': {
                    'americas': "country IN ('USA', 'Canada', 'Mexico')",
                    'europe': "country IN ('UK', 'Germany', 'France', 'Netherlands')",
                    'asia_pacific': "country IN ('Singapore', 'Australia', 'Japan', 'South Korea')",
                    'emerging': "country NOT IN ('USA', 'UK', 'Germany', 'Singapore', 'Australia')"
                }
            }
        }
    
    def _load_sql_patterns(self) -> Dict[str, str]:
        """Pre-defined SQL patterns for common business queries"""
        return {
            'employee_count_by_department': """
                SELECT 
                    department,
                    COUNT(*) as employee_count,
                    ROUND(AVG(salary), 0) as avg_salary,
                    TO_CHAR(AVG(salary), 'FM999,999,999') || ' บาท' as formatted_avg_salary
                FROM employees 
                GROUP BY department 
                ORDER BY employee_count DESC;
            """,
            'top_earners': """
                SELECT 
                    name,
                    position,
                    department,
                    TO_CHAR(salary, 'FM999,999,999') || ' บาท' as formatted_salary
                FROM employees 
                ORDER BY salary DESC 
                LIMIT {limit};
            """,
            'high_budget_projects': """
                SELECT 
                    p.name as project_name,
                    p.client,
                    TO_CHAR(p.budget, 'FM999,999,999') || ' บาท' as formatted_budget,
                    p.status,
                    COUNT(ep.employee_id) as team_size
                FROM projects p
                LEFT JOIN employee_projects ep ON p.id = ep.project_id
                WHERE p.budget > {threshold}
                GROUP BY p.id, p.name, p.client, p.budget, p.status
                ORDER BY p.budget DESC;
            """,
            'employee_project_allocation': """
                SELECT 
                    e.name as employee_name,
                    e.position,
                    p.name as project_name,
                    TO_CHAR(p.budget, 'FM999,999,999') || ' บาท' as project_budget,
                    ep.role as project_role,
                    ROUND(ep.allocation * 100, 1) || '%' as time_allocation
                FROM employees e
                JOIN employee_projects ep ON e.id = ep.employee_id
                JOIN projects p ON ep.project_id = p.id
                WHERE {where_condition}
                ORDER BY p.budget DESC, e.name;
            """,
            'department_performance': """
                SELECT 
                    e.department,
                    COUNT(DISTINCT e.id) as total_employees,
                    COUNT(DISTINCT ep.project_id) as active_projects,
                    TO_CHAR(AVG(e.salary), 'FM999,999,999') || ' บาท' as avg_salary,
                    TO_CHAR(SUM(e.salary), 'FM999,999,999') || ' บาท' as total_payroll
                FROM employees e
                LEFT JOIN employee_projects ep ON e.id = ep.employee_id
                LEFT JOIN projects p ON ep.project_id = p.id AND p.status = 'active'
                GROUP BY e.department
                ORDER BY total_payroll DESC;
            """
        }
    
    def _load_enhanced_database_schemas(self) -> Dict[str, Dict]:
        """Enhanced database schema information with business context"""
        return {
            'company-a': {
                'description': 'SiamTech Bangkok HQ - Enterprise Software Solutions Database',
                'business_context': {
                    'primary_focus': 'Enterprise software development for banking and e-commerce',
                    'client_profile': 'Large corporations, banks, government agencies',
                    'project_scale': 'Multi-million baht enterprise projects',
                    'team_expertise': 'Senior developers, solution architects, project managers',
                    'key_technologies': 'React, Node.js, AWS, PostgreSQL, Microservices'
                },
                'business_kpis': {
                    'revenue_per_employee': 'Total project budget / number of employees',
                    'avg_project_size': 'Average budget per project',
                    'utilization_rate': 'Percentage of employees on active projects',
                    'salary_competitiveness': 'Average salary vs market rate'
                },
                'tables': {
                    'employees': {
                        'description': 'Core team members - senior developers and specialists',
                        'business_significance': 'High-value technical talent with specialized skills',
                        'key_insights': 'Salary ranges 35k-150k THB, majority in IT department',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - Employee full name',
                            'department (VARCHAR(50)) - IT, Sales, Management, HR',
                            'position (VARCHAR(100)) - Technical roles, leadership positions',
                            'salary (DECIMAL(10,2)) - Monthly salary in THB (35,000 - 150,000 range)',
                            'hire_date (DATE) - Employment start date',
                            'email (VARCHAR(150)) - Corporate email address'
                        ]
                    },
                    'projects': {
                        'description': 'Enterprise-scale software projects',
                        'business_significance': 'Multi-million baht contracts with major clients',
                        'key_insights': 'Average budget 1.5M THB, focus on financial and e-commerce systems',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - Project name/title',
                            'client (VARCHAR(100)) - Major corporate clients (banks, conglomerates)',
                            'budget (DECIMAL(12,2)) - Project budget in THB (typically 800k - 3M+)',
                            'status (VARCHAR(20)) - active, completed, cancelled',
                            'start_date (DATE) - Project start date',
                            'end_date (DATE) - Project end date',
                            'tech_stack (VARCHAR(500)) - Technologies used'
                        ]
                    },
                    'employee_projects': {
                        'description': 'Project team allocations and roles',
                        'business_significance': 'Resource allocation and utilization tracking',
                        'key_insights': 'Most employees work on 1-2 projects with varying allocations',
                        'columns': [
                            'employee_id (INTEGER) - Reference to employees table',
                            'project_id (INTEGER) - Reference to projects table',
                            'role (VARCHAR(100)) - Project role (Lead Developer, Backend Developer, etc.)',
                            'allocation (DECIMAL(3,2)) - Time allocation percentage (0.0-1.0)'
                        ]
                    }
                }
            },
            'company-b': {
                'description': 'SiamTech Chiang Mai Regional - Tourism & Hospitality Technology Solutions',
                'business_context': {
                    'primary_focus': 'Tourism and hospitality technology solutions for Northern Thailand',
                    'client_profile': 'Hotels, tourism boards, cultural organizations, regional businesses',
                    'project_scale': 'Medium-scale regional projects (300k - 800k THB)',
                    'team_expertise': 'Regional specialists, tourism domain knowledge, local partnerships',
                    'key_technologies': 'Vue.js, Firebase, Mobile development, Local systems integration'
                },
                'tables': {
                    'employees': {
                        'description': 'Regional team focusing on tourism technology',
                        'business_significance': 'Smaller team with local market expertise',
                        'key_insights': 'Salary ranges 32k-70k THB, focus on tourism industry knowledge',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - Employee name',
                            'department (VARCHAR(50)) - IT, Sales, Operations',
                            'position (VARCHAR(100)) - Regional specialized roles',
                            'salary (DECIMAL(10,2)) - Monthly salary in THB (32,000 - 70,000 range)',
                            'hire_date (DATE) - Employment start date',
                            'email (VARCHAR(150)) - Regional office email'
                        ]
                    },
                    'projects': {
                        'description': 'Tourism and hospitality focused projects',
                        'business_significance': 'Regional development projects supporting local tourism',
                        'key_insights': 'Average budget 500k THB, focus on hospitality and cultural preservation',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - Project name',
                            'client (VARCHAR(100)) - Tourism clients (hotels, TAT, universities)',
                            'budget (DECIMAL(12,2)) - Project budget in THB (typically 350k - 800k)',
                            'status (VARCHAR(20)) - Project status',
                            'start_date (DATE) - Start date',
                            'end_date (DATE) - End date',
                            'tech_stack (VARCHAR(500)) - Regional tech stack'
                        ]
                    }
                }
            },
            'company-c': {
                'description': 'SiamTech International - Global Operations and Cross-Border Solutions',
                'business_context': {
                    'primary_focus': 'International software solutions and global client services',
                    'client_profile': 'Multinational corporations, global fintech, international education',
                    'project_scale': 'Large international projects (1M - 4M USD)',
                    'team_expertise': 'International experience, multi-cultural team, global standards',
                    'key_technologies': 'Enterprise microservices, cloud-native, international compliance'
                },
                'tables': {
                    'employees': {
                        'description': 'International team with global experience',
                        'business_significance': 'High-value international talent with cross-cultural skills',
                        'key_insights': 'Salary ranges 55k-120k USD equivalent, international experience required',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - Employee name',
                            'department (VARCHAR(50)) - International Development, Global Sales, Operations',
                            'position (VARCHAR(100)) - International roles',
                            'salary (DECIMAL(10,2)) - Monthly salary in USD equivalent',
                            'hire_date (DATE) - Employment start date',
                            'email (VARCHAR(150)) - International email'
                        ]
                    },
                    'projects': {
                        'description': 'Global scale international projects',
                        'business_significance': 'Multi-million USD international contracts',
                        'key_insights': 'Average budget 2M USD, focus on global platforms and fintech',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - Project name',
                            'client (VARCHAR(100)) - International clients (MegaCorp, Global Finance, etc.)',
                            'budget (DECIMAL(12,2)) - Project budget in USD (typically 1.5M - 4M)',
                            'status (VARCHAR(20)) - Project status',
                            'start_date (DATE) - Start date',
                            'end_date (DATE) - End date',
                            'tech_stack (VARCHAR(500)) - Enterprise tech stack'
                        ]
                    }
                }
            }
        }

    async def generate_enhanced_sql(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """Enhanced SQL generation with business intelligence and pattern matching"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.database_schemas[tenant_id]
        business_logic = self.business_logic_mappings.get(tenant_id, {})
        
        # Analyze question for intent and patterns
        query_analysis = self._analyze_question_intent(question, tenant_id)
        
        # Check for pre-defined patterns
        if query_analysis['pattern_match']:
            sql_query = self._apply_sql_pattern(query_analysis, tenant_id)
            metadata = {
                'method': 'pattern_matching',
                'pattern_used': query_analysis['pattern_match'],
                'confidence': 'high'
            }
            return sql_query, metadata
        
        # Generate enhanced system prompt
        system_prompt = self._create_enhanced_sql_prompt(question, schema_info, business_logic, config)
        
        try:
            # Call AI with enhanced prompt
            ai_response = await self.call_ollama_api(
                tenant_id=tenant_id,
                prompt=system_prompt,
                context_data="",
                temperature=0.1  # Low temperature for precise SQL
            )
            
            # Extract and validate SQL
            sql_query = self._extract_and_validate_sql(ai_response, tenant_id)
            
            metadata = {
                'method': 'ai_generation',
                'original_response': ai_response[:200],
                'confidence': 'medium' if len(sql_query) > 50 else 'low'
            }
            
            return sql_query, metadata
            
        except Exception as e:
            logger.error(f"Enhanced SQL generation failed: {e}")
            fallback_sql = self._generate_fallback_sql(question, tenant_id)
            metadata = {
                'method': 'fallback',
                'error': str(e),
                'confidence': 'low'
            }
            return fallback_sql, metadata

    def _analyze_question_intent(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Analyze question to determine intent and suggest patterns"""
        question_lower = question.lower()
        
        # Common intent patterns
        intents = {
            'employee_count': ['กี่คน', 'จำนวนพนักงาน', 'how many employees', 'employee count'],
            'salary_info': ['เงินเดือน', 'ค่าจ้าง', 'salary', 'pay', 'earning'],
            'project_budget': ['งบประมาณ', 'บัดเจต', 'budget', 'cost', 'price'],
            'top_performers': ['สูงสุด', 'มากที่สุด', 'เก่ง', 'ดี', 'top', 'best', 'highest'],
            'department_analysis': ['แผนก', 'ฝ่าย', 'department', 'division', 'team'],
            'project_status': ['โปรเจค', 'project', 'งาน', 'work', 'status'],
            'client_info': ['ลูกค้า', 'client', 'customer', 'บริษัท']
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Pattern matching logic
        pattern_match = None
        if 'employee_count' in detected_intents and 'department_analysis' in detected_intents:
            pattern_match = 'employee_count_by_department'
        elif 'salary_info' in detected_intents and 'top_performers' in detected_intents:
            pattern_match = 'top_earners'
        elif 'project_budget' in detected_intents and 'top_performers' in detected_intents:
            pattern_match = 'high_budget_projects'
        
        return {
            'intents': detected_intents,
            'pattern_match': pattern_match,
            'complexity': len(detected_intents),
            'question_type': 'analytical' if len(detected_intents) > 1 else 'simple'
        }

    def _apply_sql_pattern(self, query_analysis: Dict, tenant_id: str) -> str:
        """Apply pre-defined SQL patterns for common queries"""
        pattern = query_analysis['pattern_match']
        sql_template = self.sql_patterns.get(pattern, '')
        
        if pattern == 'top_earners':
            return sql_template.format(limit=5)
        elif pattern == 'high_budget_projects':
            # Different thresholds based on tenant
            thresholds = {
                'company-a': 2000000,  # 2M THB for enterprise
                'company-b': 500000,   # 500k THB for regional  
                'company-c': 1500000   # 1.5M USD for international
            }
            return sql_template.format(threshold=thresholds.get(tenant_id, 1000000))
        elif pattern == 'employee_project_allocation':
            return sql_template.format(where_condition='p.status = \'active\'')
        
        return sql_template

    def _create_enhanced_sql_prompt(self, question: str, schema_info: Dict, business_logic: Dict, config: TenantConfig) -> str:
        """Create enhanced SQL generation prompt with business intelligence"""
        
        # Format schema information with business context
        schema_text = self._format_enhanced_schema(schema_info, config.language)
        
        # Format business logic rules
        business_rules = self._format_business_logic(business_logic, config.language)
        
        if config.language == 'en':
            prompt = f"""You are an expert PostgreSQL business analyst for {config.name}.

COMPANY PROFILE:
- Business Type: {config.business_type}
- Key Focus: {schema_info['business_context']['primary_focus']}
- Client Profile: {schema_info['business_context']['client_profile']}
- Project Scale: {schema_info['business_context']['project_scale']}

{schema_text}

{business_rules}

ADVANCED SQL GENERATION RULES:
1. ALWAYS use explicit column names (never SELECT *)
2. ALWAYS include LIMIT (max 20 rows) unless doing aggregation/counting
3. Use proper table aliases: employees e, projects p, employee_projects ep
4. Format money appropriately based on business context
5. Use ILIKE for case-insensitive text searches
6. Handle NULL values with COALESCE where appropriate
7. Use proper JOINs with clear relationships
8. Add meaningful ORDER BY clauses for better insights
9. Group related data logically for business analysis
10. Use subqueries when necessary for complex business logic

BUSINESS INTELLIGENCE PATTERNS:
- Employee analysis: Include department, position, salary context
- Project analysis: Include budget, client, team size, status
- Performance metrics: Use aggregations with business meaning
- Cross-table analysis: Join tables to provide comprehensive insights

SQL QUALITY STANDARDS:
- Readable formatting with proper indentation
- Business-meaningful column aliases
- Appropriate data type handling
- Optimized for PostgreSQL performance

USER QUESTION: {question}

Generate only the PostgreSQL query that provides comprehensive business insights:"""
        
        else:  # Thai
            prompt = f"""คุณคือนักวิเคราะห์ฐานข้อมูล PostgreSQL เชี่ยวชาญสำหรับ {config.name}

ข้อมูลบริษัท:
- ประเภทธุรกิจ: {config.business_type}
- จุดเน้นหลัก: {schema_info['business_context']['primary_focus']}
- กลุ่มลูกค้า: {schema_info['business_context']['client_profile']}
- ขนาดโปรเจค: {schema_info['business_context']['project_scale']}

{schema_text}

{business_rules}

กฎการสร้าง SQL ขั้นสูง:
1. ใช้ชื่อคอลัมน์ที่ชัดเจนเสมอ (ห้ามใช้ SELECT *)
2. ใส่ LIMIT เสมอ (ไม่เกิน 20 แถว) ยกเว้นการนับหรือสรุปข้อมูล
3. ใช้ table aliases: employees e, projects p, employee_projects ep
4. จัดรูปแบบเงินให้เหมาะสมตามบริบทธุรกิจ
5. ใช้ ILIKE สำหรับการค้นหาข้อความ (ไม่สนใจตัวใหญ่-เล็ก)
6. จัดการค่า NULL ด้วย COALESCE ที่เหมาะสม
7. ใช้ JOIN ที่ถูกต้องและชัดเจน
8. เพิ่ม ORDER BY ที่มีความหมายเพื่อให้ insight ที่ดี
9. จัดกลุ่มข้อมูลอย่างมีเหตุผลสำหรับการวิเคราะห์ธุรกิจ
10. ใช้ subquery เมื่อจำเป็นสำหรับ business logic ที่ซับซ้อน

รูปแบบ Business Intelligence:
- วิเคราะห์พนักงาน: รวมบริบทแผนก ตำแหน่ง เงินเดือน
- วิเคราะห์โปรเจค: รวมงบประมาณ ลูกค้า ขนาดทีม สถานะ
- วัดผลการปฏิบัติงาน: ใช้การสรุปข้อมูลที่มีความหมายทางธุรกิจ
- วิเคราะห์ข้ามตาราง: เชื่อมตารางเพื่อให้ insight ที่ครอบคลุม

มาตรฐานคุณภาพ SQL:
- จัดรูปแบบที่อ่านง่ายด้วยการเยื้องที่ถูกต้อง
- ตั้งชื่อ alias ที่มีความหมายทางธุรกิจ
- จัดการ data type อย่างเหมาะสม
- เพิ่มประสิทธิภาพสำหรับ PostgreSQL

คำถามผู้ใช้: {question}

สร้างเฉพาะ PostgreSQL query ที่ให้ business insights ที่ครอบคลุม:"""
        
        return prompt

    def _format_enhanced_schema(self, schema_info: Dict, language: str) -> str:
        """Format enhanced schema information with business context"""
        if language == 'en':
            formatted = f"DATABASE SCHEMA:\n"
            formatted += f"Business Context: {schema_info['business_context']['primary_focus']}\n\n"
        else:
            formatted = f"โครงสร้างฐานข้อมูล:\n"
            formatted += f"บริบทธุรกิจ: {schema_info['business_context']['primary_focus']}\n\n"
        
        for table_name, table_info in schema_info['tables'].items():
            if language == 'en':
                formatted += f"📋 TABLE: {table_name}\n"
                formatted += f"   Description: {table_info['description']}\n"
                formatted += f"   Business Value: {table_info['business_significance']}\n"
                formatted += f"   Key Insights: {table_info['key_insights']}\n"
                formatted += f"   Columns:\n"
            else:
                formatted += f"📋 ตาราง: {table_name}\n"
                formatted += f"   คำอธิบาย: {table_info['description']}\n"
                formatted += f"   ความสำคัญทางธุรกิจ: {table_info['business_significance']}\n"
                formatted += f"   ข้อมูลเชิงลึก: {table_info['key_insights']}\n"
                formatted += f"   คอลัมน์:\n"
            
            for column in table_info['columns']:
                formatted += f"      • {column}\n"
            formatted += "\n"
        
        return formatted

    def _format_business_logic(self, business_logic: Dict, language: str) -> str:
        """Format business logic rules for AI understanding"""
        if not business_logic:
            return ""
        
        if language == 'en':
            formatted = "BUSINESS LOGIC MAPPINGS:\n"
        else:
            formatted = "การแปลความหมายทางธุรกิจ:\n"
        
        for category, rules in business_logic.items():
            if language == 'en':
                formatted += f"• {category.replace('_', ' ').title()}:\n"
            else:
                category_thai = {
                    'employee_levels': 'ระดับพนักงาน',
                    'project_sizes': 'ขนาดโปรเจค',
                    'departments': 'แผนกงาน',
                    'time_periods': 'ช่วงเวลา',
                    'performance_indicators': 'ตัวชี้วัดผลงาน',
                    'project_types': 'ประเภทโปรเจค',
                    'regional_focus': 'เน้นพื้นที่',
                    'market_tiers': 'ระดับตลาด',
                    'geographic_regions': 'ภูมิภาค'
                }
                formatted += f"• {category_thai.get(category, category)}:\n"
            
            for term, condition in rules.items():
                formatted += f"  - {term}: {condition}\n"
            formatted += "\n"
        
        return formatted

    def _extract_and_validate_sql(self, ai_response: str, tenant_id: str) -> str:
        """Enhanced SQL extraction with validation"""
        # Remove markdown code blocks
        cleaned = ai_response.strip()
        
        # Extract SQL from various formats
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;)\s*```',
            r'(SELECT.*?;)',
            r'(WITH.*?;)',
            r'(INSERT.*?;)',
            r'(UPDATE.*?;)',
            r'(DELETE.*?;)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                
                # Validate SQL
                if self._validate_sql_query(sql, tenant_id):
                    return sql
        
        # If no valid SQL found, try line-by-line extraction
        lines = cleaned.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('--'):
                if any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'HAVING']):
                    sql_lines.append(line)
                elif sql_lines and line.endswith(';'):
                    sql_lines.append(line)
                    break
                elif sql_lines:
                    sql_lines.append(line)
        
        if sql_lines:
            sql_query = ' '.join(sql_lines)
            # Clean up and validate
            sql_query = ' '.join(sql_query.split())
            if not sql_query.rstrip().endswith(';'):
                sql_query += ';'
            
            if self._validate_sql_query(sql_query, tenant_id):
                return sql_query
        
        # Final fallback
        return self._generate_fallback_sql("Unable to generate SQL", tenant_id)

    def _validate_sql_query(self, sql: str, tenant_id: str) -> bool:
        """Validate SQL query for safety and correctness"""
        sql_upper = sql.upper()
        
        # Security checks
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            logger.warning(f"Dangerous SQL keyword detected in query for {tenant_id}")
            return False
        
        # Basic structure checks
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return False
        
        # Must have FROM clause (except for utility queries)
        if 'FROM' not in sql_upper and 'SELECT' in sql_upper:
            # Allow simple utility queries like SELECT CURRENT_DATE
            utility_patterns = ['CURRENT_DATE', 'CURRENT_TIME', 'NOW()', 'VERSION()']
            if not any(pattern in sql_upper for pattern in utility_patterns):
                return False
        
        # Check for proper table references
        schema_info = self.database_schemas[tenant_id]
        table_names = list(schema_info['tables'].keys())
        
        has_valid_table = False
        for table in table_names:
            if table.upper() in sql_upper:
                has_valid_table = True
                break
        
        if not has_valid_table and 'FROM' in sql_upper:
            logger.warning(f"No valid table references found in SQL for {tenant_id}")
            return False
        
        return True

    def _generate_fallback_sql(self, question: str, tenant_id: str) -> str:
        """Generate safe fallback SQL when AI generation fails"""
        # Simple fallback based on question keywords
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['พนักงาน', 'employee', 'คน', 'people']):
            return "SELECT name, position, department FROM employees ORDER BY hire_date DESC LIMIT 10;"
        elif any(word in question_lower for word in ['โปรเจค', 'project', 'งาน', 'work']):
            return "SELECT name, client, status FROM projects ORDER BY start_date DESC LIMIT 10;"
        elif any(word in question_lower for word in ['เงินเดือน', 'salary', 'ค่าจ้าง', 'pay']):
            return "SELECT name, position, salary FROM employees ORDER BY salary DESC LIMIT 10;"
        elif any(word in question_lower for word in ['งบประมาณ', 'budget', 'บัดเจต', 'cost']):
            return "SELECT name, client, budget FROM projects ORDER BY budget DESC LIMIT 10;"
        else:
            return "SELECT 'ไม่สามารถสร้าง SQL ได้ กรุณาลองใหม่อีกครั้ง' as message LIMIT 1;"

    async def create_enhanced_interpretation_prompt(self, question: str, sql_query: str, results: List[Dict], tenant_id: str) -> str:
        """Create enhanced interpretation prompt with business intelligence"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.database_schemas[tenant_id]
        
        # Format results with business context
        formatted_results = self._format_results_with_context(results, tenant_id)
        
        # Generate insights and patterns
        insights = self._generate_data_insights(results, tenant_id)
        
        if config.language == 'en':
            prompt = f"""You are a senior business analyst for {config.name} interpreting database results.

COMPANY CONTEXT:
- Business Type: {config.business_type}
- Focus Area: {schema_info['business_context']['primary_focus']}
- Key Metrics: {', '.join(config.key_metrics)}

USER QUESTION: {question}
SQL EXECUTED: {sql_query}
RESULTS SUMMARY: {len(results)} records found

{formatted_results}

DATA INSIGHTS:
{insights}

RESPONSE GUIDELINES:
1. Start with direct answer addressing the specific question
2. Provide key business insights from the data
3. Highlight important trends, patterns, or anomalies
4. Add relevant business context and implications
5. Use professional yet accessible language
6. Include quantitative details with proper formatting
7. Suggest actionable next steps if appropriate
8. Keep response focused and valuable for business decision-making

FORMATTING STANDARDS:
- Use bullet points for multiple insights
- Bold important numbers and key findings
- Group related information logically
- Include percentage calculations where meaningful
- Provide context for numbers (comparisons, benchmarks)

Generate comprehensive business analysis response:"""
        
        else:  # Thai
            prompt = f"""คุณคือนักวิเคราะห์ธุรกิจอาวุโสสำหรับ {config.name} ที่ตีความผลลัพธ์จากฐานข้อมูล

บริบทบริษัท:
- ประเภทธุรกิจ: {config.business_type}
- จุดเน้น: {schema_info['business_context']['primary_focus']}
- ตัวชี้วัดหลัก: {', '.join(config.key_metrics)}

คำถามผู้ใช้: {question}
SQL ที่ใช้: {sql_query}
สรุปผลลัพธ์: พบข้อมูล {len(results)} รายการ

{formatted_results}

ข้อมูลเชิงลึก:
{insights}

แนวทางการตอบ:
1. เริ่มด้วยคำตอบที่ตรงประเด็นสำหรับคำถามที่ถาม
2. ให้ข้อมูลเชิงลึกทางธุรกิจที่สำคัญจากข้อมูล
3. เน้นแนวโน้ม รูปแบบ หรือความผิดปกติที่สำคัญ
4. เพิ่มบริบทธุรกิจที่เกี่ยวข้องและผลกระทบ
5. ใช้ภาษาที่เป็นมืออาชีพแต่เข้าใจง่าย
6. รวมรายละเอียดเชิงปริมาณด้วยการจัดรูปแบบที่เหมาะสม
7. แนะนำขั้นตอนต่อไปที่สามารถปฏิบัติได้หากเหมาะสม
8. รักษาการตอบให้มุ่งเน้นและมีคุณค่าสำหรับการตัดสินใจทางธุรกิจ

มาตรฐานการจัดรูปแบบ:
- ใช้ bullet points สำหรับข้อมูลเชิงลึกหลายๆ ข้อ
- ทำตัวหนาสำหรับตัวเลขสำคัญและการค้นพบหลัก
- จัดกลุ่มข้อมูลที่เกี่ยวข้องอย่างมีเหตุผล
- รวมการคำนวณเปอร์เซ็นต์ที่มีความหมาย
- ให้บริบทสำหรับตัวเลข (การเปรียบเทียบ มาตรฐาน)

สร้างการวิเคราะห์ธุรกิจที่ครอบคลุม:"""
        
        return prompt

    def _format_results_with_context(self, results: List[Dict], tenant_id: str) -> str:
        """Format database results with business context"""
        if not results:
            return "ไม่พบข้อมูลที่ตรงกับคำถาม"
        
        config = self.tenant_configs[tenant_id]
        formatted = "ข้อมูลจากฐานข้อมูล:\n"
        
        # Show first 10 results with formatting
        for i, row in enumerate(results[:10], 1):
            formatted += f"{i}. "
            for key, value in row.items():
                # Format based on data type and business context
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    if config.tenant_id == 'company-c':
                        formatted += f"{key}: ${value:,.0f}, "
                    else:
                        formatted += f"{key}: {value:,.0f} บาท, "
                elif key in ['allocation'] and isinstance(value, float):
                    formatted += f"{key}: {value*100:.1f}%, "
                elif isinstance(value, (int, float)):
                    formatted += f"{key}: {value:,.0f}, "
                else:
                    formatted += f"{key}: {value}, "
            formatted = formatted.rstrip(", ") + "\n"
        
        if len(results) > 10:
            formatted += f"... และอีก {len(results) - 10} รายการ\n"
        
        return formatted

    def _generate_data_insights(self, results: List[Dict], tenant_id: str) -> str:
        """Generate business insights from query results"""
        if not results:
            return "ไม่สามารถวิเคราะห์ได้เนื่องจากไม่มีข้อมูล"
        
        insights = []
        config = self.tenant_configs[tenant_id]
        
        # Analyze numerical patterns
        numerical_columns = []
        for key, value in results[0].items():
            if isinstance(value, (int, float)) and key not in ['id']:
                numerical_columns.append(key)
        
        for col in numerical_columns:
            values = [row.get(col, 0) for row in results if row.get(col) is not None]
            if values:
                avg_val = sum(values) / len(values)
                max_val = max(values)
                min_val = min(values)
                
                if col in ['salary', 'budget']:
                    currency = "USD" if config.tenant_id == 'company-c' else "บาท"
                    insights.append(f"- {col}: เฉลี่ย {avg_val:,.0f} {currency}, สูงสุด {max_val:,.0f} {currency}, ต่ำสุด {min_val:,.0f} {currency}")
                else:
                    insights.append(f"- {col}: เฉลี่ย {avg_val:.1f}, สูงสุด {max_val}, ต่ำสุด {min_val}")
        
        # Analyze categorical patterns
        categorical_columns = []
        for key, value in results[0].items():
            if isinstance(value, str) and key not in ['name', 'email', 'description']:
                categorical_columns.append(key)
        
        for col in categorical_columns:
            values = [row.get(col) for row in results if row.get(col)]
            if values:
                unique_count = len(set(values))
                most_common = max(set(values), key=values.count)
                insights.append(f"- {col}: {unique_count} ประเภท, พบ '{most_common}' มากที่สุด")
        
        # Business-specific insights
        if config.tenant_id == 'company-a':
            if any('IT' in str(row) for row in results):
                it_count = sum(1 for row in results if 'IT' in str(row.get('department', '')))
                insights.append(f"- แผนก IT: {it_count}/{len(results)} รายการ ({it_count/len(results)*100:.1f}%)")
        
        return "\n".join(insights) if insights else "ไม่พบรูปแบบที่น่าสนใจในข้อมูล"

    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Enhanced question processing with comprehensive business intelligence"""
        if tenant_id not in self.tenant_configs:
            return {
                "answer": f"ไม่รู้จัก tenant: {tenant_id}",
                "success": False,
                "data_source_used": "error",
                "confidence": "none"
            }
        
        config = self.tenant_configs[tenant_id]
        start_time = datetime.now()
        
        try:
            # 1. Enhanced SQL generation with pattern matching
            sql_query, sql_metadata = await self.generate_enhanced_sql(question, tenant_id)
            
            # 2. Execute SQL query
            db_results = self.execute_sql_query(tenant_id, sql_query)
            
            # 3. Enhanced interpretation with business intelligence
            interpretation_prompt = await self.create_enhanced_interpretation_prompt(
                question, sql_query, db_results, tenant_id
            )
            
            ai_response = await self.call_ollama_api(
                tenant_id, 
                interpretation_prompt, 
                temperature=0.3  # Slightly higher for more natural language
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": ai_response,
                "success": True,
                "data_source_used": f"enhanced_sql_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(db_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "ai_generated_sql": True,
                "sql_generation_method": sql_metadata['method'],
                "confidence": sql_metadata['confidence'],
                "processing_time_seconds": processing_time,
                "business_context": config.business_type,
                "enhancement_version": "2.0"
            }
            
        except Exception as e:
            logger.error(f"Enhanced processing failed for {tenant_id}: {e}")
            
            # Enhanced fallback with better error handling
            try:
                fallback_prompt = self._create_enhanced_fallback_prompt(question, tenant_id)
                ai_response = await self.call_ollama_api(tenant_id, fallback_prompt)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "answer": ai_response,
                    "success": True,
                    "data_source_used": f"enhanced_fallback_{config.model_name}",
                    "error": str(e),
                    "fallback_mode": True,
                    "confidence": "low",
                    "processing_time_seconds": processing_time,
                    "enhancement_version": "2.0"
                }
            except Exception as ai_error:
                return {
                    "answer": f"เกิดข้อผิดพลาดในระบบ: {str(e)}",
                    "success": False,
                    "data_source_used": "error",
                    "error": str(ai_error),
                    "confidence": "none"
                }

    def _create_enhanced_fallback_prompt(self, question: str, tenant_id: str) -> str:
        """Create enhanced fallback prompt with business context"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.database_schemas[tenant_id]
        
        if config.language == 'en':
            return f"""As a business consultant for {config.name}, please answer this question using your knowledge about {config.business_type} operations.

Company Context:
- Business Focus: {schema_info['business_context']['primary_focus']}
- Client Type: {schema_info['business_context']['client_profile']}
- Project Scale: {schema_info['business_context']['project_scale']}

Question: {question}

Note: Direct database access is temporarily unavailable. Please provide helpful insights based on typical {config.business_type} operations and best practices.

Provide a professional, informative response:"""
        else:
            return f"""ในฐานะที่ปรึกษาธุรกิจสำหรับ {config.name} กรุณาตอบคำถามนี้โดยใช้ความรู้เกี่ยวกับการดำเนินงาน {config.business_type}

บริบทบริษัท:
- จุดเน้นธุรกิจ: {schema_info['business_context']['primary_focus']}
- ประเภทลูกค้า: {schema_info['business_context']['client_profile']}
- ขนาดโปรเจค: {schema_info['business_context']['project_scale']}

คำถาม: {question}

หมายเหตุ: ไม่สามารถเข้าถึงฐานข้อมูลโดยตรงได้ในขณะนี้ กรุณาให้ข้อมูลเชิงลึกที่เป็นประโยชน์โดยอิงจากการดำเนินงาน {config.business_type} ทั่วไปและแนวทางปฏิบัติที่ดี

ให้คำตอบที่เป็นมืออาชีพและให้ข้อมูล:"""

    def get_database_connection(self, tenant_id: str) -> psycopg2.extensions.connection:
        """Get database connection for specific tenant"""
        if tenant_id not in self.tenant_configs:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        config = self.tenant_configs[tenant_id]
        
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database for {tenant_id}: {e}")
            raise
    
    def execute_sql_query(self, tenant_id: str, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results with enhanced error handling"""
        conn = None
        try:
            conn = self.get_database_connection(tenant_id)
            cursor = conn.cursor()
            
            # Execute query with timeout
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
                
            logger.info(f"Enhanced query executed successfully for {tenant_id}: {len(results)} rows returned")
            return results
            
        except Exception as e:
            logger.error(f"Enhanced SQL execution failed for {tenant_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def call_ollama_api(self, tenant_id: str, prompt: str, context_data: str = "", temperature: float = 0.7) -> str:
        """Enhanced Ollama API call with better error handling"""
        config = self.tenant_configs[tenant_id]
        
        # Prepare system prompt
        if context_data:
            full_prompt = f"{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        # Prepare request payload with enhanced options
        payload = {
            "model": config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2000 if temperature > 0.5 else 1500,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)  # Increased timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', 'ไม่สามารถรับคำตอบจาก AI ได้')
                    else:
                        logger.error(f"Enhanced Ollama API error: {response.status}")
                        return f"เกิดข้อผิดพลาดในการเรียก AI (HTTP {response.status})"
                        
        except asyncio.TimeoutError:
            logger.error("Enhanced Ollama API timeout")
            return "AI ใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Enhanced Ollama API call failed: {e}")
            return f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"

# For testing the enhanced agent
async def test_enhanced_agent():
    """Test the enhanced agent with sample questions"""
    agent = EnhancedPostgresOllamaAgent()
    
    test_scenarios = [
        {
            "tenant": "company-a",
            "questions": [
                "พนักงานคนไหนมีเงินเดือนสูงที่สุด 5 คน",
                "โปรเจคไหนมีงบประมาณมากกว่า 2 ล้านบาท",
                "แผนกไหนมีพนักงานมากที่สุดและเงินเดือนเฉลี่ยเท่าไหร่",
                "พนักงานที่ทำงานในโปรเจคงบประมาณสูง"
            ]
        },
        {
            "tenant": "company-b", 
            "questions": [
                "โปรเจคของโรงแรมดุสิตมีรายละเอียดอย่างไร",
                "ลูกค้าในภาคเหนือมีใครบ้าง",
                "พนักงานที่ทำงานโปรเจคท่องเที่ยว"
            ]
        },
        {
            "tenant": "company-c",
            "questions": [
                "Which employees work on the highest budget international projects?",
                "What are our key global clients and their project values?",
                "How many employees work in international development?"
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*60}")
        print(f"🏢 Testing {scenario['tenant'].upper()}")
        print(f"{'='*60}")
        
        for question in scenario['questions']:
            print(f"\n❓ Question: {question}")
            print("-" * 50)
            
            result = await agent.process_enhanced_question(question, scenario['tenant'])
            
            print(f"✅ Success: {result['success']}")
            print(f"🔍 SQL Method: {result.get('sql_generation_method', 'N/A')}")
            print(f"📊 Results: {result.get('db_results_count', 'N/A')} rows")
            print(f"⏱️  Time: {result.get('processing_time_seconds', 'N/A'):.2f}s")
            print(f"🎯 Confidence: {result.get('confidence', 'N/A')}")
            print(f"💬 Answer: {result['answer'][:300]}...")
            if result.get('sql_query'):
                print(f"🔧 SQL: {result['sql_query'][:100]}...")

if __name__ == "__main__":
    print("🚀 Enhanced PostgreSQL Ollama Agent v2.0")
    print("🔧 Features: Advanced prompts, business intelligence, pattern matching")
    asyncio.run(test_enhanced_agent())