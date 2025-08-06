# 🧠 Smart Prompt System - Complete Implementation
# smart_prompt_system.py

import os
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from functools import lru_cache
import re

logger = logging.getLogger(__name__)

@dataclass
class CompanyProfile:
    """Profile ของแต่ละ Company ที่ดึงจาก Schema จริง"""
    company_id: str
    name: str
    business_type: str
    tables: Dict[str, List[str]]  # table_name -> columns
    table_relationships: Dict[str, List[str]]  # table -> related_tables
    business_concepts: Dict[str, str]  # concept -> table.column
    common_questions: List[str]
    leadership_patterns: List[str]  # role patterns that indicate leadership
    key_metrics: List[str]  # important business metrics
    language: str = 'th'
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class BusinessTypeDetector:
    """🔍 ตรวจจับประเภทธุรกิจจาก Database Schema"""
    
    @staticmethod
    def detect_business_type(schema: Dict[str, List[str]], sample_data: Dict = None) -> str:
        """🔍 ตรวจจับประเภทธุรกิจอัจฉริยะ"""
        
        tables = set(t.lower() for t in schema.keys())
        all_columns = set()
        for columns in schema.values():
            all_columns.update(col.lower() for col in columns)
        
        # Healthcare indicators (โรงพยาบาล/คลินิก)
        healthcare_indicators = {
            'tables': {'patients', 'doctors', 'appointments', 'medical_records', 'prescriptions', 'diagnoses'},
            'columns': {'patient', 'doctor', 'diagnosis', 'prescription', 'medical', 'treatment', 'appointment', 'symptom', 'medicine'}
        }
        if (tables & healthcare_indicators['tables'] or 
            len(all_columns & healthcare_indicators['columns']) >= 3):
            return 'healthcare'
        
        # Tourism/Hospitality indicators (ท่องเที่ยว/โรงแรม)
        tourism_indicators = {
            'tables': {'bookings', 'reservations', 'hotels', 'rooms', 'guests', 'tours', 'packages'},
            'columns': {'booking', 'reservation', 'hotel', 'room', 'guest', 'tourist', 'tour', 'package', 'check_in', 'check_out'}
        }
        if (tables & tourism_indicators['tables'] or 
            len(all_columns & tourism_indicators['columns']) >= 3):
            return 'tourism_hospitality'
        
        # E-commerce indicators (ร้านค้าออนไลน์)
        ecommerce_indicators = {
            'tables': {'products', 'orders', 'carts', 'payments', 'inventory', 'categories', 'reviews'},
            'columns': {'product', 'order', 'cart', 'payment', 'shipping', 'inventory', 'category', 'review', 'rating', 'stock'}
        }
        if (tables & ecommerce_indicators['tables'] or 
            len(all_columns & ecommerce_indicators['columns']) >= 3):
            return 'ecommerce'
        
        # Restaurant/Food Service indicators (ร้านอาหาร)
        restaurant_indicators = {
            'tables': {'menu', 'orders', 'tables', 'reservations', 'ingredients', 'recipes'},
            'columns': {'menu', 'dish', 'ingredient', 'recipe', 'table', 'reservation', 'order', 'kitchen', 'waiter', 'chef'}
        }
        if (tables & restaurant_indicators['tables'] or 
            len(all_columns & restaurant_indicators['columns']) >= 3):
            return 'restaurant_food'
        
        # Banking/Finance indicators (ธนาคาร/การเงิน)
        finance_indicators = {
            'tables': {'accounts', 'transactions', 'loans', 'deposits', 'cards', 'branches'},
            'columns': {'account', 'transaction', 'loan', 'credit', 'debit', 'balance', 'interest', 'branch', 'atm'}
        }
        if (tables & finance_indicators['tables'] or 
            len(all_columns & finance_indicators['columns']) >= 3):
            return 'banking_finance'
        
        # Manufacturing indicators (การผลิต)
        manufacturing_indicators = {
            'tables': {'production', 'warehouses', 'suppliers', 'materials', 'quality_control'},
            'columns': {'production', 'warehouse', 'supplier', 'material', 'quality', 'assembly', 'batch', 'factory'}
        }
        if (tables & manufacturing_indicators['tables'] or 
            len(all_columns & manufacturing_indicators['columns']) >= 3):
            return 'manufacturing'
        
        # Education indicators (การศึกษา)
        education_indicators = {
            'tables': {'students', 'courses', 'enrollments', 'teachers', 'classes', 'grades'},
            'columns': {'student', 'course', 'grade', 'enrollment', 'teacher', 'class', 'semester', 'subject', 'exam'}
        }
        if (tables & education_indicators['tables'] or 
            len(all_columns & education_indicators['columns']) >= 3):
            return 'education'
        
        # Real Estate indicators (อสังหาริมทรัพย์)
        realestate_indicators = {
            'tables': {'properties', 'listings', 'agents', 'viewings', 'contracts'},
            'columns': {'property', 'listing', 'agent', 'viewing', 'rent', 'sale', 'apartment', 'house', 'land'}
        }
        if (tables & realestate_indicators['tables'] or 
            len(all_columns & realestate_indicators['columns']) >= 3):
            return 'real_estate'
        
        # International/Multi-currency indicators (ธุรกิจระหว่างประเทศ)
        international_indicators = {
            'columns': {'currency', 'exchange', 'country', 'timezone', 'international', 'global', 'usd', 'eur', 'gbp'}
        }
        if len(all_columns & international_indicators['columns']) >= 2:
            return 'international_business'
        
        # Software/IT Service indicators (บริการ IT)
        software_indicators = {
            'tables': {'projects', 'developers', 'sprints', 'issues', 'repositories'},
            'columns': {'sprint', 'scrum', 'repository', 'commit', 'issue', 'bug', 'feature', 'deployment'}
        }
        if (tables & software_indicators['tables'] or 
            len(all_columns & software_indicators['columns']) >= 3):
            return 'software_development'
        
        # Default: General business
        return 'general_business'

class SchemaAnalyzer:
    """🔗 วิเคราะห์ความสัมพันธ์ในฐานข้อมูล"""
    
    @staticmethod
    def discover_table_relationships(schema: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """🔗 ค้นหาความสัมพันธ์ระหว่างตารางจาก Column names"""
        relationships = {}
        
        for table, columns in schema.items():
            related_tables = []
            
            for column in columns:
                col_lower = column.lower()
                
                # Foreign key patterns: table_id, tableId, table_name_id
                fk_patterns = [
                    r'(.+)_id$',  # employee_id -> employee
                    r'(.+)id$',   # employeeid -> employee  
                    r'id_(.+)$'   # id_employee -> employee
                ]
                
                for pattern in fk_patterns:
                    match = re.match(pattern, col_lower)
                    if match:
                        potential_table = match.group(1)
                        
                        # หาตารางที่ชื่อใกล้เคียง
                        for other_table in schema.keys():
                            other_lower = other_table.lower()
                            
                            # Exact match or plural/singular variations
                            if (potential_table == other_lower or 
                                potential_table + 's' == other_lower or
                                potential_table == other_lower + 's' or
                                potential_table in other_lower or
                                other_lower in potential_table):
                                
                                if other_table != table and other_table not in related_tables:
                                    related_tables.append(other_table)
            
            relationships[table] = related_tables
        
        return relationships
    
    @staticmethod
    def map_business_concepts(schema: Dict[str, List[str]], business_type: str) -> Dict[str, str]:
        """🏢 แมป Business Concepts กับ Database Fields"""
        concepts = {}
        
        # Universal concepts
        for table, columns in schema.items():
            for column in columns:
                col_lower = column.lower()
                
                # Names
                if any(word in col_lower for word in ['name', 'title', 'label']):
                    concepts['ชื่อ'] = f"{table}.{column}"
                    concepts['name'] = f"{table}.{column}"
                
                # Money/Financial
                if any(word in col_lower for word in ['salary', 'wage', 'income', 'pay']):
                    concepts['เงินเดือน'] = f"{table}.{column}"
                    concepts['salary'] = f"{table}.{column}"
                
                if any(word in col_lower for word in ['budget', 'cost', 'price', 'amount', 'value', 'fee']):
                    concepts['งบประมาณ'] = f"{table}.{column}"
                    concepts['budget'] = f"{table}.{column}"
                
                # Organization
                if any(word in col_lower for word in ['department', 'division', 'team', 'unit']):
                    concepts['แผนก'] = f"{table}.{column}"
                    concepts['department'] = f"{table}.{column}"
                
                if any(word in col_lower for word in ['position', 'title', 'role', 'job']):
                    concepts['ตำแหน่ง'] = f"{table}.{column}"
                    concepts['position'] = f"{table}.{column}"
                
                # Status/State
                if any(word in col_lower for word in ['status', 'state', 'condition']):
                    concepts['สถานะ'] = f"{table}.{column}"
                    concepts['status'] = f"{table}.{column}"
        
        # Business-specific concepts
        business_specific_mappings = {
            'healthcare': {
                'patterns': [
                    (['patient', 'client'], ['ผู้ป่วย', 'patient']),
                    (['doctor', 'physician'], ['แพทย์', 'doctor']),
                    (['diagnosis', 'disease'], ['การวินิจฉัย', 'diagnosis']),
                    (['appointment', 'visit'], ['นัดหมาย', 'appointment']),
                ]
            },
            'tourism_hospitality': {
                'patterns': [
                    (['guest', 'customer', 'visitor'], ['แขก', 'guest']),
                    (['room', 'accommodation'], ['ห้องพัก', 'room']),
                    (['booking', 'reservation'], ['การจอง', 'booking']),
                    (['tour', 'trip'], ['ทัวร์', 'tour']),
                ]
            },
            'ecommerce': {
                'patterns': [
                    (['product', 'item'], ['สินค้า', 'product']),
                    (['order', 'purchase'], ['คำสั่งซื้อ', 'order']),
                    (['customer', 'buyer'], ['ลูกค้า', 'customer']),
                    (['inventory', 'stock'], ['สต็อก', 'inventory']),
                ]
            },
            'restaurant_food': {
                'patterns': [
                    (['menu', 'dish'], ['เมนู', 'menu']),
                    (['table', 'seat'], ['โต๊ะ', 'table']),
                    (['order', 'request'], ['ออเดอร์', 'order']),
                    (['ingredient', 'material'], ['วัตถุดิบ', 'ingredient']),
                ]
            }
        }
        
        if business_type in business_specific_mappings:
            for table, columns in schema.items():
                for column in columns:
                    col_lower = column.lower()
                    
                    for patterns, concepts_list in business_specific_mappings[business_type]['patterns']:
                        if any(pattern in col_lower for pattern in patterns):
                            for concept in concepts_list:
                                concepts[concept] = f"{table}.{column}"
        
        return concepts
    
    @staticmethod
    def detect_leadership_patterns(schema: Dict[str, List[str]], business_type: str) -> List[str]:
        """👥 ตรวจจับ patterns ที่บ่งบอกถึงผู้นำ"""
        
        base_patterns = [
            'lead', 'leader', 'head', 'chief', 'manager', 'director', 
            'supervisor', 'coordinator', 'admin', 'principal'
        ]
        
        business_patterns = {
            'healthcare': ['doctor', 'physician', 'surgeon', 'specialist', 'consultant'],
            'tourism_hospitality': ['concierge', 'guide', 'host', 'captain'],
            'ecommerce': ['merchant', 'vendor', 'seller'],
            'restaurant_food': ['chef', 'cook', 'waiter_lead', 'host'],
            'education': ['teacher', 'professor', 'instructor', 'principal'],
            'software_development': ['architect', 'senior', 'tech_lead', 'scrum_master']
        }
        
        patterns = base_patterns.copy()
        if business_type in business_patterns:
            patterns.extend(business_patterns[business_type])
        
        return patterns

class QuestionGenerator:
    """❓ สร้างคำถามตัวอย่างที่เหมาะสมกับธุรกิจ"""
    
    @staticmethod
    def generate_relevant_questions(schema: Dict[str, List[str]], business_type: str) -> List[str]:
        """❓ สร้างคำถามตัวอย่างที่เหมาะสมกับธุรกิจ"""
        
        questions = []
        tables = [t.lower() for t in schema.keys()]
        
        # Universal questions
        if any('employee' in t for t in tables):
            questions.extend([
                "มีพนักงานกี่คนในแต่ละแผนก",
                "พนักงานคนไหนได้เงินเดือนสูงสุด",
                "ใครเป็นหัวหน้าแผนก"
            ])
        
        if any('project' in t for t in tables):
            questions.extend([
                "มีโปรเจคอะไรบ้าง",
                "โปรเจคไหนมีงบประมาณสูงสุด",
                "ใครเป็นผู้นำโปรเจค"
            ])
        
        # Business-specific questions
        business_questions = {
            'healthcare': [
                "มีผู้ป่วยกี่คนวันนี้",
                "แพทย์คนไหนมีผู้ป่วยมากที่สุด",
                "การวินิจฉัยที่พบบ่อยที่สุดคืออะไร",
                "ใครเป็นหัวหน้าแผนกแพทย์"
            ],
            'tourism_hospitality': [
                "มีห้องว่างกี่ห้อง",
                "แขกที่เข้าพักมาจากไหนบ้าง",
                "รายได้จากการท่องเที่ยวเดือนนี้",
                "ทัวร์ไหนได้รับความนิยมมากที่สุด"
            ],
            'ecommerce': [
                "สินค้าไหนขายดีที่สุด",
                "ยอดขายรวมเดือนนี้",
                "ลูกค้าใหม่มีกี่คน",
                "สินค้าไหนมีสต็อกน้อย"
            ],
            'restaurant_food': [
                "เมนูไหนสั่งบ่อยที่สุด",
                "โต๊ะไหนว่างบ้าง",
                "วัตถุดิบไหนหมดแล้ว",
                "ใครเป็นเชฟหัวหน้า"
            ],
            'education': [
                "มีนักเรียนกี่คนในแต่ละชั้น",
                "อาจารย์คนไหนสอนมากที่สุด",
                "วิชาไหนมีนักเรียนลงทะเบียนมากที่สุด",
                "ใครเป็นหัวหน้าแผนก"
            ],
            'software_development': [
                "โปรเจคไหนใกล้ deadline",
                "ใครเป็น tech lead",
                "bug ใหม่มีกี่อัน",
                "feature ไหนกำลัง develop"
            ]
        }
        
        if business_type in business_questions:
            questions.extend(business_questions[business_type])
        
        return questions[:8]  # จำกัด 8 คำถาม

class SmartPromptGenerator:
    """🧠 สร้าง Prompt อัจฉริยะตาม Schema จริงของแต่ละ Company"""
    
    def __init__(self):
        self.company_profiles: Dict[str, CompanyProfile] = {}
        self.schema_cache = {}
        self.prompt_cache = {}
    
    async def build_company_profile(self, company_id: str, discovered_schema: Dict[str, List[str]], 
                                   sample_data: Dict[str, Any] = None) -> CompanyProfile:
        """🔍 สร้าง Company Profile จาก Schema ที่ Discovery มา"""
        
        try:
            # 1. วิเคราะห์ Business Type
            business_type = BusinessTypeDetector.detect_business_type(discovered_schema, sample_data)
            
            # 2. หาความสัมพันธ์ระหว่างตาราง
            relationships = SchemaAnalyzer.discover_table_relationships(discovered_schema)
            
            # 3. แมป Business Concepts
            business_concepts = SchemaAnalyzer.map_business_concepts(discovered_schema, business_type)
            
            # 4. สร้างคำถามตัวอย่าง
            common_questions = QuestionGenerator.generate_relevant_questions(discovered_schema, business_type)
            
            # 5. ตรวจจับ Leadership patterns
            leadership_patterns = SchemaAnalyzer.detect_leadership_patterns(discovered_schema, business_type)
            
            # 6. กำหนด Key metrics
            key_metrics = self._identify_key_metrics(discovered_schema, business_type)
            
            # 7. ดึงชื่อ Company
            company_name = self._extract_company_name(company_id, sample_data)
            
            profile = CompanyProfile(
                company_id=company_id,
                name=company_name,
                business_type=business_type,
                tables=discovered_schema,
                table_relationships=relationships,
                business_concepts=business_concepts,
                common_questions=common_questions,
                leadership_patterns=leadership_patterns,
                key_metrics=key_metrics
            )
            
            self.company_profiles[company_id] = profile
            logger.info(f"✅ Built profile for {company_name}: {business_type} with {len(discovered_schema)} tables")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to build company profile for {company_id}: {e}")
            
            # Fallback profile
            fallback_profile = CompanyProfile(
                company_id=company_id,
                name=f"Company {company_id.upper()}",
                business_type='general_business',
                tables=discovered_schema,
                table_relationships={},
                business_concepts={},
                common_questions=["มีข้อมูลอะไรบ้าง", "ข้อมูลใหม่สุดคืออะไร"],
                leadership_patterns=['lead', 'manager', 'head'],
                key_metrics=['count', 'total', 'average']
            )
            
            self.company_profiles[company_id] = fallback_profile
            return fallback_profile
    
    def _identify_key_metrics(self, schema: Dict[str, List[str]], business_type: str) -> List[str]:
        """📊 ระบุ metrics สำคัญตามประเภทธุรกิจ"""
        
        base_metrics = ['จำนวน', 'รวม', 'เฉลี่ย', 'สูงสุด', 'ต่ำสุด']
        
        business_metrics = {
            'healthcare': ['ผู้ป่วยรายใหม่', 'อัตราการรักษา', 'ระยะเวลารอคิว'],
            'tourism_hospitality': ['อัตราเข้าพัก', 'รายได้ต่อห้อง', 'ความพึงพอใจ'],
            'ecommerce': ['ยอดขาย', 'จำนวนออเดอร์', 'มูลค่าเฉลี่ยต่อออเดอร์'],
            'restaurant_food': ['ยอดขายต่อวัน', 'เมนูยอดนิยม', 'เวลาเสิร์ฟเฉลี่ย'],
            'education': ['จำนวนนักเรียน', 'อัตราผ่าน', 'ความพึงพอใจการเรียน']
        }
        
        metrics = base_metrics.copy()
        if business_type in business_metrics:
            metrics.extend(business_metrics[business_type])
        
        return metrics
    
    def _extract_company_name(self, company_id: str, sample_data: Dict = None) -> str:
        """🏢 ดึงชื่อ Company จริง"""
        
        # Try to get from sample data first
        if sample_data and 'company_info' in sample_data:
            name = sample_data['company_info'].get('name')
            if name:
                return name
        
        # Fallback to default mapping
        name_mapping = {
            'company-a': 'SiamTech Bangkok HQ',
            'company-b': 'SiamTech Chiang Mai Regional',
            'company-c': 'SiamTech International',
            'company-demo': 'Demo Company',
            'company-hospital': 'Demo Hospital',
            'company-restaurant': 'Demo Restaurant'
        }
        
        return name_mapping.get(company_id, f'Company {company_id.upper()}')
    
    @lru_cache(maxsize=100)
    def generate_smart_prompt(self, question: str, company_id: str, 
                             question_type: str = None) -> str:
        """🧠 สร้าง Smart Prompt ตาม Company Profile"""
        
        if company_id not in self.company_profiles:
            return self._generate_fallback_prompt(question, company_id)
        
        profile = self.company_profiles[company_id]
        
        # Cache key for prompt
        cache_key = f"{company_id}_{question_type}_{len(question)}"
        if cache_key in self.prompt_cache:
            base_prompt = self.prompt_cache[cache_key]
        else:
            base_prompt = self._create_base_prompt(profile)
            self.prompt_cache[cache_key] = base_prompt
        
        # Add question-specific guidance
        specific_guidance = self._get_question_specific_guidance(question, profile)
        
        # Final prompt
        final_prompt = f"""{base_prompt}

{specific_guidance}

คำถาม: {question}

สร้าง SQL query ที่เหมาะสมกับธุรกิจ {profile.business_type}:
"""
        
        return final_prompt
    
    def _create_base_prompt(self, profile: CompanyProfile) -> str:
        """📋 สร้าง Base prompt ตาม Company profile"""
        
        prompt = f"""🎯 คุณคือ Business Intelligence Expert ของ {profile.name}

📊 ข้อมูลที่มีในระบบ (ประเภท: {profile.business_type}):
"""
        
        # Schema information
        for table, columns in profile.tables.items():
            prompt += f"🗃️ ตาราง {table}: {', '.join(columns[:6])}"
            if len(columns) > 6:
                prompt += f" และอีก {len(columns)-6} คอลัมน์"
            prompt += "\n"
        
        # Business context
        business_context = self._get_business_context(profile.business_type)
        prompt += f"\n💡 Business Context ({profile.business_type}):\n{business_context}"
        
        # Table relationships
        if profile.table_relationships:
            prompt += "\n🔗 ความสัมพันธ์ระหว่างตาราง:\n"
            for table, related in profile.table_relationships.items():
                if related:
                    prompt += f"• {table} เชื่อมโยงกับ {', '.join(related)}\n"
        
        # Business concepts
        if profile.business_concepts:
            prompt += "\n🏢 แนวคิดทางธุรกิจที่สำคัญ:\n"
            concept_items = list(profile.business_concepts.items())[:8]
            for concept, location in concept_items:
                prompt += f"• {concept} → {location}\n"
        
        # Leadership guidance
        if profile.leadership_patterns:
            prompt += f"\n👥 Patterns ที่บ่งบอกผู้นำ: {', '.join(profile.leadership_patterns[:5])}\n"
        
        # Example questions
        prompt += f"\n📝 คำถามตัวอย่างที่ระบบตอบได้:\n"
        for i, q in enumerate(profile.common_questions[:6], 1):
            prompt += f"{i}. {q}\n"
        
        # Rules
        prompt += f"""
⚠️ กฎสำคัญ:
1. ใช้เฉพาะตารางและคอลัมน์ที่แสดงข้างต้น
2. เข้าใจ Business Logic ของ {profile.business_type}
3. สร้าง PostgreSQL query ที่ถูกต้อง (ใช้ ILIKE แทน LIKE)
4. ใช้ LIMIT เพื่อจำกัดผลลัพธ์
5. เมื่อถามเกี่ยวกับ "ผู้นำ" ให้มองหา role ที่มี patterns: {', '.join(profile.leadership_patterns[:3])}
"""
        
        return prompt
    
    def _get_question_specific_guidance(self, question: str, profile: CompanyProfile) -> str:
        """🎯 คำแนะนำเฉพาะตามประเภทคำถาม"""
        
        question_lower = question.lower()
        guidance = ""
        
        # Leadership questions
        if any(word in question_lower for word in ['ใครคือ', 'ผู้นำ', 'หัวหน้า', 'who is', 'leader']):
            guidance += f"""
🔸 เนื่องจากถามเกี่ยวกับ "ผู้นำ":
• มองหา role ที่มี: {', '.join(profile.leadership_patterns[:5])}
• ใช้ JOIN ระหว่างตารางที่เกี่ยวข้อง
• เรียงลำดับผู้นำก่อน (ORDER BY role patterns)
• ตัวอย่าง: WHERE role ILIKE '%lead%' OR role ILIKE '%manager%'
"""
        
        # Counting questions
        elif any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many', 'count']):
            guidance += """
🔸 เนื่องจากถามเกี่ยวกับ "จำนวน":
• ใช้ COUNT(*) หรือ COUNT(DISTINCT column)
• ใช้ GROUP BY เพื่อแยกกลุ่ม
• เรียงลำดับด้วย ORDER BY COUNT(*) DESC
"""
        
        # Financial questions
        elif any(word in question_lower for word in ['งบประมาณ', 'เงิน', 'ราคา', 'budget', 'money']):
            guidance += f"""
🔸 เนื่องจากถามเกี่ยวกับ "การเงิน":
• คอลัมน์ที่เกี่ยวข้อง: {', '.join([v for k, v in profile.business_concepts.items() if any(word in k for word in ['งบประมาณ', 'เงินเดือน', 'budget', 'salary'])][:3])}
• ใช้ SUM(), AVG(), MAX(), MIN() สำหรับการคำนวณ
• เรียงลำดับด้วย ORDER BY amount DESC
"""
        
        # Project-specific questions
        elif any(word in question_lower for word in ['โปรเจค', 'project']):
            guidance += """
🔸 เนื่องจากถามเกี่ยวกับ "โปรเจค":
• หาโปรเจคที่เกี่ยวข้องจากชื่อที่กล่าวถึง
• ใช้ JOIN กับตารางพนักงานเพื่อหาทีมงาน
• แสดงสถานะ, งบประมาณ, และสมาชิกทีม
"""
        
        # Business-specific guidance
        business_guidance = {
            'healthcare': """
🏥 Healthcare-specific:
• ผู้ป่วย (patients) เชื่อมกับ แพทย์ (doctors)
• นัดหมาย (appointments) เชื่อมกับทั้งคู่
• การวินิจฉัย (diagnosis) เป็นข้อมูลสำคัญ
""",
            'tourism_hospitality': """
🏨 Tourism-specific:
• แขก (guests) เชื่อมกับ การจอง (bookings)
• ห้องพัก (rooms) มีสถานะ available/occupied
• ทัวร์ (tours) เชื่อมกับ แพ็คเกจ (packages)
""",
            'ecommerce': """
🛒 E-commerce-specific:
• สินค้า (products) เชื่อมกับ หมวดหมู่ (categories)
• คำสั่งซื้อ (orders) เชื่อมกับ ลูกค้า (customers)
• สต็อก (inventory) เป็นข้อมูลสำคัญ
""",
            'restaurant_food': """
🍽️ Restaurant-specific:
• เมนู (menu) เชื่อมกับ ประเภทอาหาร (categories)
• ออเดอร์ (orders) เชื่อมกับ โต๊ะ (tables)
• วัตถุดิบ (ingredients) เชื่อมกับ สูตรอาหาร (recipes)
"""
        }
        
        if profile.business_type in business_guidance:
            guidance += business_guidance[profile.business_type]
        
        return guidance
    
    def _get_business_context(self, business_type: str) -> str:
        """🏢 Business Context เฉพาะแต่ละประเภทธุรกิจ"""
        
        contexts = {
            'healthcare': """
• เน้นผู้ป่วย (patients), แพทย์ (doctors), การวินิจฉัย (diagnosis)
• การวิเคราะห์ต้องคำนึงถึงความปลอดภัยและความเป็นส่วนตัว
• ผู้นำมักเป็น หัวหน้าแพทย์, ผู้อำนวยการโรงพยาบาล
• เมตริกสำคัญ: จำนวนผู้ป่วย, อัตราการรักษา, ระยะเวลารอคิว
""",
            'tourism_hospitality': """
• เน้นแขก (guests), การจอง (bookings), ห้องพัก (rooms)
• การวิเคราะห์ต้องคำนึงถึงฤดูกาล, เทศกาล, สถานที่ท่องเที่ยว
• ผู้นำมักเป็น ผู้จัดการโรงแรม, หัวหน้าแผนกต้อนรับ
• เมตริกสำคัญ: อัตราเข้าพัก, รายได้ต่อห้อง, ความพึงพอใจ
""",
            'ecommerce': """
• เน้นสินค้า (products), คำสั่งซื้อ (orders), ลูกค้า (customers)
• การวิเคราะห์ยอดขาย, สต็อก, พฤติกรรมลูกค้า
• ผู้นำมักเป็น Product Manager, Sales Manager
• เมตริกสำคัญ: ยอดขาย, จำนวนออเดอร์, มูลค่าเฉลี่ย
""",
            'restaurant_food': """
• เน้นเมนู (menu), ออเดอร์ (orders), โต๊ะ (tables)
• การวิเคราะห์ยอดขาย, ความนิยมของเมนู, ประสิทธิภาพครัว
• ผู้นำมักเป็น เชฟหัวหน้า, ผู้จัดการร้าน
• เมตริกสำคัญ: ยอดขายต่อวัน, เมนูยอดนิยม, เวลาเสิร์ฟ
""",
            'banking_finance': """
• เน้นบัญชี (accounts), ธุรกรรม (transactions), สินเชื่อ (loans)
• ข้อมูลต้องแม่นยำและปลอดภัยสูง
• ผู้นำมักเป็น ผู้จัดการสาขา, หัวหน้าสินเชื่อ
• เมตริกสำคัญ: ยอดเงินฝาก, จำนวนธุรกรรม, อัตราผิดนัดชำระ
""",
            'education': """
• เน้นนักเรียน (students), หลักสูตร (courses), การลงทะเบียน
• การวิเคราะห์ผลการเรียน, อัตราผ่าน, ความพึงพอใจ
• ผู้นำมักเป็น หัวหน้าแผนก, อาจารย์ประจำ
• เมตริกสำคัญ: จำนวนนักเรียน, อัตราผ่าน, คะแนนเฉลี่ย
""",
            'software_development': """
• เน้นโปรเจค (projects), พัฒนา (developers), งาน (tasks)
• การวิเคราะห์ progress, bug tracking, performance
• ผู้นำมักเป็น Tech Lead, Scrum Master, Architect
• เมตริกสำคัญ: velocity, burn rate, code quality
""",
            'general_business': """
• ธุรกิจทั่วไป: พนักงาน (employees), โปรเจค (projects), ลูกค้า (clients)
• การวิเคราะห์พื้นฐานเรื่องทีมงาน, งบประมาณ, ประสิทธิภาพ
• ผู้นำมักเป็น Project Manager, Department Head
• เมตริกสำคัญ: จำนวนพนักงาน, งบประมาณ, ความสำเร็จโปรเจค
"""
        }
        
        return contexts.get(business_type, contexts['general_business'])
    
    def _generate_fallback_prompt(self, question: str, company_id: str) -> str:
        """🛡️ Fallback prompt เมื่อไม่มี Company Profile"""
        return f"""🎯 คุณคือ Business Intelligence Expert

⚠️ ไม่มีข้อมูล Company Profile สำหรับ {company_id}
กรุณาสร้าง SQL query ทั่วไปที่ปลอดภัย

กฎพื้นฐาน:
• ใช้ PostgreSQL syntax (ILIKE แทน LIKE)
• SELECT เท่านั้น ห้าม INSERT/UPDATE/DELETE
• ใช้ LIMIT เพื่อจำกัดผลลัพธ์
• เมื่อถามเกี่ยวกับ "ผู้นำ" ให้มองหา role ที่มี lead, manager, head

คำถาม: {question}

สร้าง SQL query พื้นฐาน:
"""

    def get_company_profile_summary(self, company_id: str) -> Dict[str, Any]:
        """📊 ดึงสรุปข้อมูล Company Profile"""
        if company_id not in self.company_profiles:
            return {"error": "Company profile not found"}
        
        profile = self.company_profiles[company_id]
        return {
            "company_id": profile.company_id,
            "name": profile.name,
            "business_type": profile.business_type,
            "tables_count": len(profile.tables),
            "table_names": list(profile.tables.keys()),
            "business_concepts_count": len(profile.business_concepts),
            "common_questions": profile.common_questions,
            "leadership_patterns": profile.leadership_patterns,
            "key_metrics": profile.key_metrics,
            "created_at": profile.created_at
        }

# 🚀 Integration class for existing agent
class EnhancedPromptAgent:
    """🔗 รวม Smart Prompt เข้ากับ Agent เดิม"""
    
    def __init__(self, existing_agent):
        self.agent = existing_agent
        self.prompt_generator = SmartPromptGenerator()
        self._profiles_built = set()
        self._initialization_lock = asyncio.Lock()
    
    async def _ensure_profile_built(self, tenant_id: str):
        """🔧 สร้าง Company Profile ถ้ายังไม่มี"""
        if tenant_id not in self._profiles_built:
            async with self._initialization_lock:
                if tenant_id not in self._profiles_built:  # Double-check
                    try:
                        schema = await self.agent.get_actual_schema(tenant_id)
                        sample_data = await self._get_sample_data(tenant_id)
                        
                        await self.prompt_generator.build_company_profile(
                            tenant_id, schema, sample_data
                        )
                        self._profiles_built.add(tenant_id)
                        
                        logger.info(f"✅ Company profile built for {tenant_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to build profile for {tenant_id}: {e}")
                        # Continue with fallback
    
    async def _get_sample_data(self, tenant_id: str) -> Dict[str, Any]:
        """📊 ดึงข้อมูลตัวอย่างเพื่อช่วยในการวิเคราะห์"""
        try:
            # Try to get company info from database
            sample_query = "SELECT * FROM company_info LIMIT 1;"
            result = self.agent.execute_sql_query(tenant_id, sample_query)
            
            if result:
                return {"company_info": result[0]}
                
        except Exception as e:
            logger.debug(f"No company_info table found for {tenant_id}: {e}")
        
        return {}
    
    async def process_question_with_smart_prompt(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 ใช้ Smart Prompt ในการประมวลผล"""
        
        start_time = datetime.now()
        
        try:
            # 1. Ensure company profile is built
            await self._ensure_profile_built(tenant_id)
            
            # 2. Get enhanced question analysis
            question_analysis = self._analyze_question_advanced(question)
            
            # 3. Generate smart prompt
            smart_prompt = self.prompt_generator.generate_smart_prompt(
                question, tenant_id, question_analysis['type']
            )
            
            # 4. Process with enhanced prompt
            result = await self._process_with_smart_prompt(
                question, tenant_id, smart_prompt, question_analysis
            )
            
            # 5. Add smart prompt metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result.update({
                'smart_prompt_used': True,
                'company_profile': self.prompt_generator.company_profiles[tenant_id].business_type if tenant_id in self.prompt_generator.company_profiles else 'unknown',
                'question_analysis': question_analysis,
                'enhancement_version': '3.2_smart_prompt',
                'smart_processing_time': processing_time,
                'profile_built': tenant_id in self._profiles_built
            })
            
            return result
            
        except Exception as e:
            logger.error(f"🚨 Smart prompt processing failed for {tenant_id}: {e}")
            
            # Fallback to original processing
            logger.info(f"🔄 Falling back to original processing for {tenant_id}")
            result = await self.agent.process_enhanced_question(question, tenant_id)
            
            result.update({
                'smart_prompt_used': False,
                'fallback_reason': str(e),
                'enhancement_version': '3.2_smart_prompt_fallback'
            })
            
            return result
    
    def _analyze_question_advanced(self, question: str) -> Dict[str, Any]:
        """🧠 วิเคราะห์คำถามขั้นสูง"""
        
        question_lower = question.lower()
        
        # Advanced pattern matching
        patterns = {
            'project_leader': [
                'ใครคือผู้นำโปรเจค', 'ใครเป็นหัวหน้าโปรเจค', 'ผู้นำโปรเจค',
                'who leads', 'project leader', 'project manager'
            ],
            'team_members': [
                'ใครทำงานใน', 'ทีมงาน', 'สมาชิกทีม',
                'who works on', 'team members', 'project team'
            ],
            'department_analysis': [
                'แผนกไหน', 'กี่คนในแต่ละแผนก', 'แผนกมี',
                'department', 'division'
            ],
            'financial_analysis': [
                'งบประมาณ', 'เงินเดือน', 'ราคา', 'ค่าใช้จ่าย',
                'budget', 'salary', 'cost', 'expense'
            ],
            'performance_metrics': [
                'สูงสุด', 'ต่ำสุด', 'มากที่สุด', 'น้อยที่สุด',
                'highest', 'lowest', 'maximum', 'minimum'
            ],
            'status_inquiry': [
                'สถานะ', 'อย่างไร', 'เป็นยังไง',
                'status', 'how is', 'what is the state'
            ]
        }
        
        detected_type = 'general'
        confidence = 0.5
        
        for pattern_type, keywords in patterns.items():
            matches = sum(1 for keyword in keywords if keyword in question_lower)
            if matches > 0:
                detected_type = pattern_type
                confidence = min(0.9, 0.5 + (matches * 0.2))
                break
        
        return {
            'type': detected_type,
            'confidence': confidence,
            'keywords_found': [kw for kw in patterns.get(detected_type, []) if kw in question_lower],
            'requires_join': detected_type in ['project_leader', 'team_members'],
            'analysis_method': 'advanced_pattern_matching'
        }
    
    async def _process_with_smart_prompt(self, question: str, tenant_id: str, 
                                        smart_prompt: str, question_analysis: Dict) -> Dict[str, Any]:
        """🎯 ประมวลผลด้วย Smart Prompt"""
        
        # Get configuration
        config = self.agent.tenant_configs[tenant_id]
        
        try:
            # 1. Generate SQL with smart prompt
            ai_response = await self.agent.call_ollama_api(
                tenant_id=tenant_id,
                prompt=smart_prompt,
                context_data="",
                temperature=0.1
            )
            
            # 2. Extract and validate SQL
            schema = await self.agent.get_actual_schema(tenant_id)
            sql_query = self._extract_and_validate_sql_smart(ai_response, schema, question_analysis)
            
            # 3. Execute SQL
            db_results = self.agent.execute_sql_query(tenant_id, sql_query)
            
            # 4. Create interpretation with business context
            if db_results:
                interpretation_prompt = await self._create_business_aware_interpretation(
                    question, sql_query, db_results, tenant_id, question_analysis
                )
                
                ai_interpretation = await self.agent.call_ollama_api(
                    tenant_id, 
                    interpretation_prompt, 
                    temperature=0.2
                )
            else:
                ai_interpretation = self._create_no_data_response(question, tenant_id)
            
            return {
                "answer": ai_interpretation,
                "success": True,
                "data_source_used": f"smart_prompt_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(db_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "sql_generation_method": "smart_prompt_enhanced",
                "confidence_level": "high"
            }
            
        except Exception as e:
            logger.error(f"🚨 Smart prompt processing failed: {e}")
            
            # Enhanced fallback
            fallback_response = await self._smart_fallback(question, tenant_id, question_analysis)
            return fallback_response
    
    def _extract_and_validate_sql_smart(self, ai_response: str, schema: Dict[str, List[str]], 
                                       question_analysis: Dict) -> str:
        """🔧 แยก SQL และตรวจสอบด้วย Smart validation"""
        
        # Extract SQL patterns (same as before)
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;?)\s*```',
            r'(SELECT.*?;?)'
        ]
        
        extracted_sql = None
        for pattern in sql_patterns:
            match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            if match:
                extracted_sql = match.group(1).strip()
                if extracted_sql.upper().startswith('SELECT'):
                    break
        
        if not extracted_sql:
            return self._generate_smart_fallback_sql(question_analysis, schema)
        
        # Clean up SQL
        if not extracted_sql.endswith(';'):
            extracted_sql += ';'
        
        # Validate against schema
        if self._validate_sql_against_schema_smart(extracted_sql, schema, question_analysis):
            return extracted_sql
        else:
            return self._generate_smart_fallback_sql(question_analysis, schema)
    
    def _validate_sql_against_schema_smart(self, sql: str, schema: Dict[str, List[str]], 
                                          question_analysis: Dict) -> bool:
        """✅ ตรวจสอบ SQL ด้วย Smart validation"""
        
        sql_upper = sql.upper()
        
        # Basic safety checks
        dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous):
            return False
        
        # Must be SELECT
        if not sql_upper.startswith('SELECT'):
            return False
        
        # Check table references
        valid_tables = set(table.upper() for table in schema.keys())
        found_tables = set()
        
        for table in valid_tables:
            if table in sql_upper:
                found_tables.add(table)
        
        if not found_tables:
            return False
        
        # Smart validation based on question type
        if question_analysis['type'] == 'project_leader' and question_analysis['requires_join']:
            # Should have JOIN for leadership questions
            if 'JOIN' not in sql_upper:
                logger.warning("Leadership question without JOIN detected")
                return False
        
        return True
    
    def _generate_smart_fallback_sql(self, question_analysis: Dict, schema: Dict[str, List[str]]) -> str:
        """🛡️ สร้าง Fallback SQL อัจฉริยะ"""
        
        question_type = question_analysis['type']
        
        if question_type == 'project_leader':
            # Generate leadership query
            if all(table in schema for table in ['projects', 'employee_projects', 'employees']):
                return """
                    SELECT DISTINCT
                        p.name as project_name,
                        e.name as employee_name,
                        e.position,
                        ep.role as project_role
                    FROM projects p
                    JOIN employee_projects ep ON p.id = ep.project_id
                    JOIN employees e ON ep.employee_id = e.id
                    WHERE ep.role ILIKE '%lead%' OR ep.role ILIKE '%manager%' OR ep.role ILIKE '%head%'
                    ORDER BY p.name, e.name
                    LIMIT 10;
                """
        
        elif question_type == 'department_analysis':
            if 'employees' in schema:
                return """
                    SELECT 
                        department,
                        COUNT(*) as employee_count,
                        ROUND(AVG(salary), 0) as avg_salary
                    FROM employees 
                    GROUP BY department 
                    ORDER BY employee_count DESC
                    LIMIT 10;
                """
        
        elif question_type == 'financial_analysis':
            if 'projects' in schema:
                return """
                    SELECT 
                        name as project_name,
                        budget,
                        client,
                        status
                    FROM projects 
                    ORDER BY budget DESC NULLS LAST
                    LIMIT 10;
                """
        
        # Generic fallback
        first_table = list(schema.keys())[0] if schema else 'employees'
        first_columns = schema.get(first_table, ['id', 'name'])[:3]
        
        return f"SELECT {', '.join(first_columns)} FROM {first_table} LIMIT 5;"
    
    async def _create_business_aware_interpretation(self, question: str, sql_query: str, 
                                                   results: List[Dict], tenant_id: str,
                                                   question_analysis: Dict) -> str:
        """🎯 สร้างการตีความที่เข้าใจธุรกิจ"""
        
        config = self.agent.tenant_configs[tenant_id]
        business_type = self.prompt_generator.company_profiles[tenant_id].business_type if tenant_id in self.prompt_generator.company_profiles else 'general_business'
        
        formatted_results = self._format_results_business_aware(results, business_type)
        
        prompt = f"""🎯 คุณคือนักวิเคราะห์ธุรกิจ {business_type} ที่ตีความข้อมูลอย่างเข้าใจบริบท

คำถาม: {question}
ประเภทคำถาม: {question_analysis['type']}
SQL ที่ใช้: {sql_query}
ผลลัพธ์: {len(results)} รายการ

{formatted_results}

💡 คำแนะนำการตีความ:
• ตอบตรงประเด็นที่ถาม
• อธิบายความหมายทางธุรกิจ
• ให้ insight ที่เป็นประโยชน์
• ใช้ภาษาที่เข้าใจง่าย

วิเคราะห์และตอบคำถามอย่างเป็นมืออาชีพ:
"""
        
        return prompt
    
    def _format_results_business_aware(self, results: List[Dict], business_type: str) -> str:
        """📊 จัดรูปแบบผลลัพธ์ตามประเภทธุรกิจ"""
        
        if not results:
            return "ไม่มีข้อมูล"
        
        formatted = "ข้อมูลจากฐานข้อมูล:\n"
        
        # Limit results for readability
        display_results = results[:10]
        
        for i, row in enumerate(display_results, 1):
            formatted += f"{i}. "
            
            # Format based on business type
            for key, value in row.items():
                if business_type == 'healthcare' and 'patient' in key.lower():
                    formatted += f"ผู้ป่วย: {value}, "
                elif business_type == 'tourism_hospitality' and 'guest' in key.lower():
                    formatted += f"แขก: {value}, "
                elif business_type == 'ecommerce' and 'product' in key.lower():
                    formatted += f"สินค้า: {value}, "
                elif key.lower() in ['salary', 'budget', 'amount', 'price'] and isinstance(value, (int, float)):
                    formatted += f"{key}: {value:,.0f} บาท, "
                else:
                    formatted += f"{key}: {value}, "
            
            formatted = formatted.rstrip(", ") + "\n"
        
        if len(results) > 10:
            formatted += f"... และอีก {len(results) - 10} รายการ\n"
        
        return formatted
    
    def _create_no_data_response(self, question: str, tenant_id: str) -> str:
        """📝 สร้างคำตอบเมื่อไม่มีข้อมูล"""
        
        if tenant_id in self.prompt_generator.company_profiles:
            profile = self.prompt_generator.company_profiles[tenant_id]
            
            response = f"""ไม่พบข้อมูลสำหรับคำถาม: "{question}"

📊 ข้อมูลที่มีใน {profile.name} ({profile.business_type}):
"""
            
            for i, table in enumerate(list(profile.tables.keys())[:5], 1):
                columns = profile.tables[table]
                response += f"{i}. ตาราง {table}: {len(columns)} คอลัมน์\n"
            
            if profile.common_questions:
                response += f"\n💡 ลองถามคำถามเหล่านี้:\n"
                for i, q in enumerate(profile.common_questions[:5], 1):
                    response += f"{i}. {q}\n"
        
        else:
            response = f"""ไม่พบข้อมูลสำหรับคำถาม: "{question}"

💡 ลองถามคำถามทั่วไป เช่น:
• มีข้อมูลอะไรบ้าง
• จำนวนรายการในแต่ละตาราง
• ข้อมูลล่าสุดคืออะไร
"""
        
        return response
    
    async def _smart_fallback(self, question: str, tenant_id: str, question_analysis: Dict) -> Dict[str, Any]:
        """🛡️ Smart fallback เมื่อ processing หลักล้มเหลว"""
        
        try:
            # Try basic processing with enhanced error handling
            basic_response = await self.agent.process_enhanced_question(question, tenant_id)
            
            basic_response.update({
                'smart_prompt_used': False,
                'fallback_mode': True,
                'fallback_reason': 'smart_processing_failed',
                'question_analysis': question_analysis
            })
            
            return basic_response
            
        except Exception as e:
            logger.error(f"🚨 Even smart fallback failed: {e}")
            
            config = self.agent.tenant_configs[tenant_id]
            
            return {
                "answer": f"ขออภัย ระบบไม่สามารถประมวลผลคำถามได้ในขณะนี้\n\nกรุณาลองคำถามที่ง่ายกว่า เช่น:\n• มีข้อมูลอะไรบ้าง\n• จำนวนรายการทั้งหมด",
                "success": False,
                "data_source_used": "smart_fallback_error",
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "smart_prompt_used": False,
                "fallback_mode": True,
                "error": str(e),
                "enhancement_version": "3.2_smart_prompt_error"
            }
    
    def get_company_profile_info(self, tenant_id: str) -> Dict[str, Any]:
        """📊 ดึงข้อมูล Company Profile สำหรับ debugging"""
        return self.prompt_generator.get_company_profile_summary(tenant_id)

# 🧪 Testing and Demo Functions
class SmartPromptTester:
    """🧪 ทดสอบระบบ Smart Prompt"""
    
    def __init__(self, enhanced_agent: EnhancedPromptAgent):
        self.agent = enhanced_agent
    
    async def test_business_type_detection(self):
        """🔍 ทดสอบการตรวจจับประเภทธุรกิจ"""
        
        test_schemas = {
            'healthcare_demo': {
                'patients': ['id', 'name', 'age', 'diagnosis', 'doctor_id'],
                'doctors': ['id', 'name', 'specialization', 'department'],
                'appointments': ['id', 'patient_id', 'doctor_id', 'appointment_date']
            },
            'restaurant_demo': {
                'menu': ['id', 'dish_name', 'price', 'category'],
                'orders': ['id', 'table_id', 'menu_id', 'quantity'],
                'tables': ['id', 'table_number', 'capacity', 'status']
            },
            'ecommerce_demo': {
                'products': ['id', 'name', 'price', 'category_id', 'stock'],
                'orders': ['id', 'customer_id', 'total_amount', 'status'],
                'customers': ['id', 'name', 'email', 'address']
            }
        }
        
        print("🔍 Testing Business Type Detection:")
        print("=" * 50)
        
        for schema_name, schema in test_schemas.items():
            detected_type = BusinessTypeDetector.detect_business_type(schema)
            print(f"📋 {schema_name}")
            print(f"   Tables: {list(schema.keys())}")
            print(f"   🎯 Detected: {detected_type}")
            print()
    
    async def test_smart_prompts(self, test_questions: List[Tuple[str, str]]):
        """🧪 ทดสอบ Smart Prompts"""
        
        print("🧪 Testing Smart Prompts:")
        print("=" * 50)
        
        for tenant_id, question in test_questions:
            print(f"\n❓ Question: {question}")
            print(f"🏢 Tenant: {tenant_id}")
            print("-" * 40)
            
            try:
                result = await self.agent.process_question_with_smart_prompt(question, tenant_id)
                
                print(f"✅ Success: {result['success']}")
                print(f"🧠 Smart Prompt: {result.get('smart_prompt_used', False)}")
                print(f"🏢 Business Type: {result.get('company_profile', 'unknown')}")
                print(f"🔍 Question Type: {result.get('question_analysis', {}).get('type', 'unknown')}")
                print(f"📊 DB Results: {result.get('db_results_count', 0)}")
                print(f"⏱️ Response Time: {result.get('response_time_ms', 0)}ms")
                print(f"💬 Answer: {result['answer'][:200]}...")
                
                if result.get('sql_query'):
                    print(f"🔧 SQL: {result['sql_query'][:100]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def run_comprehensive_test(self):
        """🎯 รัน comprehensive test"""
        
        # Test business type detection
        await self.test_business_type_detection()
        
        # Test smart prompts
        test_questions = [
            ("company-a", "ใครคือผู้นำโปรเจค Mobile Banking App"),
            ("company-a", "มีพนักงานกี่คนในแต่ละแผนก"),
            ("company-a", "โปรเจคไหนมีงบประมาณสูงสุด"),
            ("company-b", "มีโปรเจคอะไรบ้าง"),
            ("company-c", "Who works on international projects"),
        ]
        
        await self.test_smart_prompts(test_questions)

# 🚀 Demo Company Creation Helper
class DemoCompanyCreator:
    """🏗️ สร้าง Demo Company เพื่อทดสอบ"""
    
    @staticmethod
    def create_healthcare_demo() -> Dict[str, Any]:
        """🏥 สร้าง Healthcare Demo"""
        return {
            'sql_init': """
-- Healthcare Demo Database
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    diagnosis VARCHAR(200),
    doctor_id INTEGER,
    admission_date DATE,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    department VARCHAR(100),
    years_experience INTEGER
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER REFERENCES doctors(id),
    appointment_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT
);

-- Sample data
INSERT INTO doctors VALUES 
(1, 'หมอสมหญิง ใจดี', 'อายุรกรรม', 'Internal Medicine', 10),
(2, 'หมอสมชาย รักษา', 'ศัลยกรรม', 'Surgery', 15),
(3, 'หมอมาลี ดูแล', 'กุมารเวชกรรม', 'Pediatrics', 8);

INSERT INTO patients VALUES 
(1, 'คนไข้หนึ่ง', 35, 'ไข้หวัด', 1, '2024-08-01', 'active'),
(2, 'คนไข้สอง', 45, 'เบาหวาน', 1, '2024-08-02', 'active'),
(3, 'คนไข้สาม', 8, 'ไข้', 3, '2024-08-03', 'discharged');

INSERT INTO appointments VALUES 
(1, 1, 1, '2024-08-05 09:00:00', 'scheduled', 'ตรวจทั่วไป'),
(2, 2, 1, '2024-08-05 10:00:00', 'completed', 'ตรวจน้ำตาล'),
(3, 3, 3, '2024-08-05 14:00:00', 'scheduled', 'ตรวจเด็ก');
""",
            'config': {
                'tenant_id': 'company-hospital',
                'name': 'Demo Hospital',
                'business_type': 'healthcare',
                'expected_questions': [
                    "มีผู้ป่วยกี่คนวันนี้",
                    "หมอคนไหนมีผู้ป่วยมากที่สุด",
                    "ใครเป็นหัวหน้าแผนกอายุรกรรม"
                ]
            }
        }
    
    @staticmethod
    def create_restaurant_demo() -> Dict[str, Any]:
        """🍽️ สร้าง Restaurant Demo"""
        return {
            'sql_init': """
-- Restaurant Demo Database
CREATE TABLE menu (
    id SERIAL PRIMARY KEY,
    dish_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(8,2),
    ingredients TEXT,
    chef_id INTEGER
);

CREATE TABLE tables (
    id SERIAL PRIMARY KEY,
    table_number INTEGER UNIQUE,
    capacity INTEGER,
    status VARCHAR(20) DEFAULT 'available'
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES tables(id),
    menu_id INTEGER REFERENCES menu(id),
    quantity INTEGER DEFAULT 1,
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE chefs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    role VARCHAR(50),
    experience_years INTEGER
);

-- Sample data
INSERT INTO chefs VALUES 
(1, 'เชฟสมชาย', 'อาหารไทย', 'Head Chef', 15),
(2, 'เชฟสมหญิง', 'ขนมหวาน', 'Pastry Chef', 8),
(3, 'เชฟมาลี', 'อาหารนานาชาติ', 'Sous Chef', 12);

INSERT INTO menu VALUES 
(1, 'ผัดไทย', 'อาหารหลัก', 80.00, 'เส้นจันทน์, กุ้ง, ไข่', 1),
(2, 'ส้มตำ', 'ยำ', 60.00, 'มะละกอ, มะเขือเทศ, ถั่วฝักยาว', 1),
(3, 'ไอศครีมกะทิ', 'ของหวาน', 45.00, 'กะทิ, น้ำตาล, วนิลา', 2);

INSERT INTO tables VALUES 
(1, 1, 4, 'occupied'),
(2, 2, 2, 'available'),
(3, 3, 6, 'reserved');

INSERT INTO orders VALUES 
(1, 1, 1, 2, '2024-08-05 12:30:00', 'cooking'),
(2, 1, 2, 1, '2024-08-05 12:32:00', 'pending'),
(3, 3, 3, 3, '2024-08-05 13:00:00', 'completed');
""",
            'config': {
                'tenant_id': 'company-restaurant',
                'name': 'Demo Restaurant',
                'business_type': 'restaurant_food',
                'expected_questions': [
                    "เมนูไหนสั่งบ่อยที่สุด",
                    "โต๊ะไหนว่างบ้าง",
                    "ใครเป็นเชฟหัวหน้า"
                ]
            }
        }

# 🎯 Usage Examples and Integration
async def demo_smart_prompt_system():
    """🎮 Demo การใช้งาน Smart Prompt System"""
    
    print("🎮 Smart Prompt System Demo")
    print("=" * 60)
    
    # This would be integrated with your existing agent
    # from enhanced_postgres_agent import FixedPostgresOllamaAgent
    # agent = FixedPostgresOllamaAgent()
    # smart_agent = EnhancedPromptAgent(agent)
    
    # Demo business type detection
    demo_schemas = {
        'หจก.โรงพยาบาลใจดี': {
            'patients': ['id', 'name', 'diagnosis', 'doctor_id'],
            'doctors': ['id', 'name', 'specialization']
        },
        'ร้านอาหารอร่อยดี': {
            'menu': ['id', 'dish_name', 'price', 'chef_id'],
            'orders': ['id', 'table_id', 'menu_id']
        },
        'บริษัทเทคโนโลยี': {
            'employees': ['id', 'name', 'position', 'department'],
            'projects': ['id', 'name', 'budget', 'manager_id']
        }
    }
    
    print("🔍 Business Type Detection Results:")
    for company, schema in demo_schemas.items():
        business_type = BusinessTypeDetector.detect_business_type(schema)
        print(f"• {company} → {business_type}")
    
    print("\n🧠 Smart Prompt Generation Example:")
    prompt_gen = SmartPromptGenerator()
    
    # Build sample profile
    sample_profile = await prompt_gen.build_company_profile(
        "demo-company",
        demo_schemas['บริษัทเทคโนโลยี']
    )
    
    print(f"Company Profile Created:")
    print(f"• Name: {sample_profile.name}")
    print(f"• Business Type: {sample_profile.business_type}")
    print(f"• Tables: {list(sample_profile.tables.keys())}")
    print(f"• Sample Questions: {sample_profile.common_questions[:3]}")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_smart_prompt_system())