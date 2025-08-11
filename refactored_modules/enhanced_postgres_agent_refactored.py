# refactored_modules/enhanced_postgres_agent_refactored.py
# 🔄 FIXED VERSION: Enhanced Intent Detection + Real-time Schema Discovery

import os
import time
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
from decimal import Decimal

# Import essential modules
from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .ai_service import AIService

# 🆕 Import PromptManager
try:
    from core_system.prompt_manager import WorkingPromptManager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False
    logging.warning("⚠️ PromptManager not available, using fallback prompts")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedIntentDetector:
    """🎯 Enhanced Intent Detection System"""
    
    def __init__(self):
        # คำที่บ่งบอกว่าต้องใช้ SQL อย่างชัดเจน
        self.sql_indicators = {
            'identification': ['ใครอยู่', 'ใครเป็น', 'ใครทำ', 'who is', 'who are', 'who works'],
            'listing': ['ใครบ้าง', 'รายชื่อ', 'list', 'แสดง', 'show me', 'display'],
            'counting': ['กี่คน', 'จำนวน', 'how many', 'count', 'เท่าไร', 'มีกี่'],
            'searching': ['หา', 'ค้นหา', 'find', 'search', 'ตำแหน่ง', 'position'],
            'filtering': ['แผนก', 'department', 'ฝ่าย', 'งาน', 'โปรเจค', 'project'],
            'analysis': ['เปรียบเทียบ', 'วิเคราะห์', 'สรุป', 'analyze', 'compare']
        }
        
        # คำที่บ่งบอกว่าเป็น Conversational อย่างชัดเจน
        self.conversational_indicators = {
            'greetings': ['สวัสดี', 'hello', 'hi', 'ช่วย', 'help'],
            'general_info': ['คุณคือใคร', 'เกี่ยวกับ', 'about', 'what are you'],
            'capabilities': ['ทำอะไรได้', 'ช่วยอะไร', 'what can you do']
        }
    
    def detect_intent(self, question: str) -> Dict[str, Any]:
        """🎯 Enhanced Intent Detection with confidence scoring"""
        
        question_lower = question.lower()
        
        # คำนวณคะแนน SQL indicators
        sql_score = 0
        sql_reasons = []
        
        for category, keywords in self.sql_indicators.items():
            matches = [word for word in keywords if word in question_lower]
            if matches:
                # ให้น้ำหนักต่างกันตามประเภท
                weight = 3 if category in ['identification', 'counting'] else 2
                sql_score += len(matches) * weight
                sql_reasons.append(f"{category}: {matches}")
        
        # คำนวณคะแนน Conversational indicators
        conv_score = 0
        conv_reasons = []
        
        for category, keywords in self.conversational_indicators.items():
            matches = [word for word in keywords if word in question_lower]
            if matches:
                conv_score += len(matches) * 3  # ให้น้ำหนักสูง
                conv_reasons.append(f"{category}: {matches}")
        
        # ตรวจสอบ Pattern เฉพาะ
        specific_patterns = self._check_specific_patterns(question_lower)
        if specific_patterns['sql_pattern']:
            sql_score += 5
            sql_reasons.append(f"pattern: {specific_patterns['sql_pattern']}")
        
        if specific_patterns['conv_pattern']:
            conv_score += 5
            conv_reasons.append(f"pattern: {specific_patterns['conv_pattern']}")
        
        # ตัดสินใจ Intent
        total_score = sql_score + conv_score
        
        if total_score == 0:
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'sql_score': sql_score,
                'conv_score': conv_score,
                'reasons': ['No clear indicators found']
            }
        
        if conv_score > sql_score:
            return {
                'intent': 'conversational',
                'confidence': conv_score / total_score,
                'sql_score': sql_score,
                'conv_score': conv_score,
                'reasons': conv_reasons
            }
        else:
            return {
                'intent': 'sql_query',
                'confidence': sql_score / total_score,
                'sql_score': sql_score,
                'conv_score': conv_score,
                'reasons': sql_reasons
            }
    
    def _check_specific_patterns(self, question_lower: str) -> Dict[str, str]:
        """ตรวจสอบ Pattern เฉพาะที่บ่งบอก Intent ชัดเจน"""
        
        # Patterns ที่บ่งบอก SQL อย่างชัดเจน
        sql_patterns = [
            r'ใครอยู่.*ตำแหน่ง',  # "ใครอยู่ตำแหน่ง frontend บ้าง"
            r'มี.*กี่คน.*แผนก',    # "มีพนักงานกี่คนในแผนก IT"
            r'รายชื่อ.*ที่',       # "รายชื่อพนักงานที่..."
            r'แสดง.*ข้อมูล',       # "แสดงข้อมูลพนักงาน"
            r'who.*in.*position',  # "who is in position"
            r'how many.*in'        # "how many people in"
        ]
        
        # Patterns ที่บ่งบอก Conversational อย่างชัดเจน
        conv_patterns = [
            r'สวัสดี.*ครับ',       # "สวัสดีครับ"
            r'คุณ.*คือ.*ใคร',      # "คุณคือใครครับ"
            r'ช่วย.*อะไร.*ได้',    # "ช่วยอะไรได้บ้าง"
            r'hello.*there',       # "hello there"
            r'what.*are.*you'      # "what are you"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, question_lower):
                return {'sql_pattern': pattern, 'conv_pattern': None}
        
        for pattern in conv_patterns:
            if re.search(pattern, question_lower):
                return {'conv_pattern': pattern, 'sql_pattern': None}
        
        return {'sql_pattern': None, 'conv_pattern': None}

class SchemaInspector:
    """🔍 Real-time Schema Discovery and Analysis"""
    
    def __init__(self, database_handler: DatabaseHandler):
        self.database_handler = database_handler
        self.schema_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def get_live_schema_info(self, tenant_id: str) -> Dict[str, Any]:
        """ดึงข้อมูล Schema แบบ Real-time พร้อม Cache"""
        
        cache_key = f"{tenant_id}_schema"
        
        # ตรวจสอบ Cache
        if self._is_cache_valid(cache_key):
            logger.info(f"📊 Using cached schema for {tenant_id}")
            return self.schema_cache[cache_key]['data']
        
        try:
            logger.info(f"🔍 Discovering live schema for {tenant_id}")
            schema_info = await self._discover_schema(tenant_id)
            
            # บันทึกลง Cache
            self.schema_cache[cache_key] = {
                'data': schema_info,
                'timestamp': time.time()
            }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"❌ Schema discovery failed for {tenant_id}: {e}")
            return self._get_fallback_schema()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """ตรวจสอบว่า Cache ยังใช้ได้หรือไม่"""
        if cache_key not in self.schema_cache:
            return False
        
        cache_age = time.time() - self.schema_cache[cache_key]['timestamp']
        return cache_age < self.cache_ttl
    
    async def _discover_schema(self, tenant_id: str) -> Dict[str, Any]:
        """ค้นพบโครงสร้างฐานข้อมูลจริง"""
        
        try:
            conn = self.database_handler.get_database_connection(tenant_id)
            cursor = conn.cursor()
            
            # ดึงข้อมูลโครงสร้างตาราง
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('employees', 'projects', 'employee_projects')
                ORDER BY table_name, ordinal_position
            """)
            
            schema_info = {
                'tables': {},
                'sample_data': {},
                'discovered_at': datetime.now().isoformat()
            }
            
            # จัดกลุ่มข้อมูลตามตาราง
            for row in cursor.fetchall():
                table_name, column_name, data_type, is_nullable = row
                
                if table_name not in schema_info['tables']:
                    schema_info['tables'][table_name] = {
                        'columns': [],
                        'primary_key': None
                    }
                
                schema_info['tables'][table_name]['columns'].append({
                    'name': column_name,
                    'type': data_type,
                    'nullable': is_nullable == 'YES'
                })
            
            # ดึงตัวอย่างข้อมูลสำหรับแต่ละตาราง
            for table_name in schema_info['tables'].keys():
                sample_data = await self._get_sample_data(cursor, table_name)
                schema_info['sample_data'][table_name] = sample_data
            
            conn.close()
            return schema_info
            
        except Exception as e:
            logger.error(f"Schema discovery error: {e}")
            raise
    
    async def _get_sample_data(self, cursor, table_name: str) -> Dict[str, List]:
        """ดึงตัวอย่างข้อมูลเพื่อให้ AI เข้าใจรูปแบบข้อมูล"""
        
        sample_data = {}
        
        try:
            # ดึงชื่อคอลัมน์ทั้งหมด
            cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            columns = [row[0] for row in cursor.fetchall()]
            
            # ดึงตัวอย่างข้อมูลสำหรับคอลัมน์สำคัญ
            important_columns = ['department', 'position', 'name', 'client', 'status']
            
            for column in columns:
                if column in important_columns:
                    cursor.execute(f"""
                        SELECT DISTINCT {column} 
                        FROM {table_name} 
                        WHERE {column} IS NOT NULL 
                        LIMIT 5
                    """)
                    
                    values = [str(row[0]) for row in cursor.fetchall()]
                    sample_data[column] = values
            
            return sample_data
            
        except Exception as e:
            logger.warning(f"Could not get sample data for {table_name}: {e}")
            return {}
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """Schema สำรองในกรณีที่ไม่สามารถดึงข้อมูลจริงได้"""
        return {
            'tables': {
                'employees': {
                    'columns': [
                        {'name': 'id', 'type': 'integer', 'nullable': False},
                        {'name': 'name', 'type': 'character varying', 'nullable': False},
                        {'name': 'department', 'type': 'character varying', 'nullable': False},
                        {'name': 'position', 'type': 'character varying', 'nullable': False},
                        {'name': 'salary', 'type': 'numeric', 'nullable': False}
                    ]
                }
            },
            'sample_data': {},
            'discovered_at': datetime.now().isoformat(),
            'fallback': True
        }

class EnhancedPostgresOllamaAgent:
    """🎯 Enhanced PostgreSQL Agent with Fixed Intent Detection and Real-time Schema Discovery"""
    
    def __init__(self):
        """🏗️ Initialize with enhanced components"""
        self.config_manager = TenantConfigManager()
        self.tenant_configs = self.config_manager.tenant_configs
        self.database_handler = DatabaseHandler(self.tenant_configs)
        self.ai_service = AIService()
        
        # 🆕 Enhanced components
        self.intent_detector = EnhancedIntentDetector()
        self.schema_inspector = SchemaInspector(self.database_handler)
        
        # 🆕 Initialize PromptManager
        self.prompt_manager = None
        self.use_prompt_manager = False
        self._init_prompt_manager()
        
        # Statistics tracking
        self.stats = {
            'total_queries': 0,
            'sql_queries': 0,
            'conversational_queries': 0,
            'intent_accuracy': []
        }
        
        logger.info(f"✅ Enhanced PostgreSQL Agent initialized with fixes")
        logger.info(f"🎯 Intent Detection: Enhanced multi-pattern system")
        logger.info(f"🔍 Schema Discovery: Real-time with caching")
        logger.info(f"🎯 PromptManager: {'✅ Active' if self.use_prompt_manager else '❌ Fallback mode'}")
    
    def _init_prompt_manager(self):
        """🔧 Initialize PromptManager with proper error handling"""
        
        if not PROMPT_MANAGER_AVAILABLE:
            logger.warning("⚠️ PromptManager module not available")
            return
        
        try:
            # 🔧 Convert TenantConfig objects to dictionaries
            tenant_config_dicts = {}
            for tenant_id, config in self.tenant_configs.items():
                tenant_config_dicts[tenant_id] = {
                    'company_id': tenant_id,
                    'name': config.name,
                    'model': config.model_name,
                    'language': config.language,
                    'business_type': config.business_type,
                    'db_host': config.db_host,
                    'db_port': config.db_port,
                    'db_name': config.db_name,
                    'db_user': config.db_user,
                    'db_password': config.db_password
                }
            
            self.prompt_manager = WorkingPromptManager(tenant_config_dicts)
            
            # Check if any prompts loaded successfully
            stats = self.prompt_manager.get_statistics()
            if stats['loaded_prompts'] > 0:
                self.use_prompt_manager = True
                self.supported_companies = list(self.prompt_manager.company_prompts.keys())
                logger.info(f"✅ PromptManager loaded: {stats['loaded_prompts']} company prompts")
            else:
                logger.warning("⚠️ PromptManager: No company prompts loaded")
                
        except Exception as e:
            logger.error(f"❌ PromptManager initialization failed: {e}")
    
    # ========================================================================
    # 🎯 MAIN PROCESSING METHOD - Enhanced Intent Detection
    # ========================================================================
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main processing method with enhanced intent detection"""
        
        if tenant_id not in self.tenant_configs:
            return self._create_error_response("Unknown tenant", tenant_id)
        
        start_time = datetime.now()
        self.stats['total_queries'] += 1
        
        try:
            # 🆕 Enhanced Intent Detection
            intent_result = self.intent_detector.detect_intent(question)
            
            logger.info(f"🎯 Intent Detection Result for '{question[:50]}...': "
                       f"{intent_result['intent']} (confidence: {intent_result['confidence']:.2f})")
            
            # Log intent decision for analysis
            self._log_intent_decision(question, intent_result, tenant_id)
            
            # Route based on intent
            if intent_result['intent'] == 'conversational' and intent_result['confidence'] >= 0.6:
                return await self._process_conversational_question(question, tenant_id, start_time, intent_result)
            
            elif intent_result['intent'] == 'sql_query' and intent_result['confidence'] >= 0.5:
                return await self._process_sql_question(question, tenant_id, start_time, intent_result)
            
            else:
                # Ambiguous case - use hybrid approach
                return await self._process_hybrid_question(question, tenant_id, start_time, intent_result)
                
        except Exception as e:
            logger.error(f"❌ Processing failed for {tenant_id}: {e}")
            return self._create_error_response(str(e), tenant_id)
    
    async def _process_conversational_question(self, question: str, tenant_id: str, 
                                            start_time: datetime, intent_result: Dict) -> Dict[str, Any]:
        """💬 Process conversational questions (greetings, general info)"""
        
        self.stats['conversational_queries'] += 1
        
        try:
            # Use PromptManager if available and supported
            if self.use_prompt_manager and tenant_id in self.supported_companies:
                logger.info(f"💬 Using PromptManager for conversational query: {tenant_id}")
                result = await self.prompt_manager.process_query(question, tenant_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                result.update({
                    'processing_time_seconds': processing_time,
                    'system_used': 'prompt_manager_conversational',
                    'intent_detection': intent_result,
                    'fixed_agent_version': 'v2.1_enhanced'
                })
                return result
            else:
                # Fallback conversational response
                return self._create_fallback_conversational_response(question, tenant_id, start_time, intent_result)
                
        except Exception as e:
            logger.error(f"❌ Conversational processing failed: {e}")
            return self._create_fallback_conversational_response(question, tenant_id, start_time, intent_result)
    
    async def _process_sql_question(self, question: str, tenant_id: str, 
                                  start_time: datetime, intent_result: Dict) -> Dict[str, Any]:
        """🎯 Process SQL questions with enhanced schema discovery"""
        
        self.stats['sql_queries'] += 1
        
        try:
            # 🔍 Get live schema information
            schema_info = await self.schema_inspector.get_live_schema_info(tenant_id)
            
            # 🎯 Generate enhanced SQL prompt
            sql_prompt = await self._generate_enhanced_sql_prompt(question, tenant_id, schema_info, intent_result)
            
            # 🤖 Call AI service to generate SQL
            config = self._get_config(tenant_id)
            ai_response = await self.ai_service.call_ollama_api(
                config, sql_prompt, temperature=0.1
            )
            
            # 🔍 Extract and validate SQL
            sql_query = self._extract_sql_with_validation(ai_response, question)
            
            if not self._is_valid_sql(sql_query):
                raise ValueError(f"Invalid or unsafe SQL generated: {sql_query}")
            
            # 🗄️ Execute SQL query
            results = await self._execute_sql_enhanced(sql_query, tenant_id)
            
            # 🎨 Format response with enhanced context
            formatted_answer = self._format_enhanced_response(
                results, question, tenant_id, schema_info, sql_query
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": formatted_answer,
                "success": True,
                "data_source_used": f"enhanced_sql_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(results) if results else 0,
                "tenant_id": tenant_id,
                "processing_time_seconds": processing_time,
                "system_used": "enhanced_sql_with_schema_discovery",
                "intent_detection": intent_result,
                "schema_discovery": {
                    "used_live_schema": not schema_info.get('fallback', False),
                    "cache_hit": schema_info.get('discovered_at') != datetime.now().isoformat()
                },
                "fixed_agent_version": "v2.1_enhanced"
            }
            
        except Exception as e:
            logger.error(f"❌ SQL processing failed: {e}")
            return self._create_sql_error_response(question, tenant_id, str(e), intent_result)
    
    async def _process_hybrid_question(self, question: str, tenant_id: str, 
                                     start_time: datetime, intent_result: Dict) -> Dict[str, Any]:
        """🔄 Process ambiguous questions using hybrid approach"""
        
        logger.info(f"🔄 Using hybrid approach for ambiguous question: {question[:50]}...")
        
        # Try SQL first, fallback to conversational
        try:
            sql_result = await self._process_sql_question(question, tenant_id, start_time, intent_result)
            
            # If SQL returns meaningful results, use it
            if sql_result.get('success') and sql_result.get('db_results_count', 0) > 0:
                sql_result['system_used'] = 'hybrid_sql_successful'
                return sql_result
            else:
                # Fallback to conversational
                conv_result = await self._process_conversational_question(question, tenant_id, start_time, intent_result)
                conv_result['system_used'] = 'hybrid_conversational_fallback'
                return conv_result
                
        except Exception as e:
            # If SQL fails, try conversational
            logger.warning(f"Hybrid SQL failed, trying conversational: {e}")
            conv_result = await self._process_conversational_question(question, tenant_id, start_time, intent_result)
            conv_result['system_used'] = 'hybrid_conversational_after_sql_error'
            return conv_result
    
    # ========================================================================
    # 🔧 ENHANCED SQL GENERATION AND PROCESSING
    # ========================================================================
    
    async def _generate_enhanced_sql_prompt(self, question: str, tenant_id: str, 
                                          schema_info: Dict, intent_result: Dict) -> str:
        """🎯 Generate enhanced SQL prompt using real schema data"""
        
        config = self._get_config(tenant_id)
        business_context = self._get_business_context_enhanced(tenant_id)
        
        # Extract relevant tables based on question
        relevant_tables = self._identify_relevant_tables(question, schema_info)
        
        prompt = f"""คุณคือ PostgreSQL Expert สำหรับ {config.name}

{business_context}

🔍 REAL DATABASE SCHEMA (ข้อมูลจริงจากฐานข้อมูล):
"""
        
        # Add schema information for relevant tables
        for table_name in relevant_tables:
            if table_name in schema_info['tables']:
                table_info = schema_info['tables'][table_name]
                prompt += f"\n📊 ตาราง {table_name}:\n"
                
                for column in table_info['columns']:
                    prompt += f"  • {column['name']} ({column['type']})"
                    if not column['nullable']:
                        prompt += " [NOT NULL]"
                    prompt += "\n"
                
                # Add sample data if available
                if table_name in schema_info['sample_data']:
                    sample_data = schema_info['sample_data'][table_name]
                    if sample_data:
                        prompt += "  📋 ตัวอย่างข้อมูลจริง:\n"
                        for col, values in sample_data.items():
                            if values and len(values) > 0:
                                prompt += f"    {col}: {', '.join(map(str, values[:3]))}\n"
        
        # Add specific search rules based on intent
        search_guidance = self._get_search_guidance(question, intent_result)
        
        prompt += f"""
🎯 กฎ SQL สำหรับคำถามนี้:
{search_guidance}

🔧 กฎทั่วไป:
1. ใช้ ILIKE '%keyword%' สำหรับการค้นหาข้อความ (ไม่สนใจตัวใหญ่เล็ก)
2. ใช้ COALESCE สำหรับจัดการ NULL values
3. แสดงผลไม่เกิน 20 รายการ: LIMIT 20
4. จัดเรียงตามความเกี่ยวข้องกับคำถาม

Intent Detection: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})
คำถาม: {question}

สร้าง PostgreSQL query ที่ถูกต้องและตรงกับคำถาม:"""
        
        return prompt
    
    def _identify_relevant_tables(self, question: str, schema_info: Dict) -> List[str]:
        """ระบุตารางที่เกี่ยวข้องกับคำถาม"""
        
        question_lower = question.lower()
        relevant_tables = set()
        
        # เพิ่มตารางหลักเสมอ
        relevant_tables.add('employees')
        
        # ตรวจสอบคำสำคัญที่เกี่ยวข้องกับโปรเจค
        project_keywords = ['โปรเจค', 'project', 'งาน', 'ลูกค้า', 'client']
        if any(keyword in question_lower for keyword in project_keywords):
            relevant_tables.add('projects')
            relevant_tables.add('employee_projects')
        
        # ตรวจสอบคำสำคัญที่เกี่ยวข้องกับการมอบหมายงาน
        assignment_keywords = ['ทำงาน', 'รับผิดชอบ', 'assigned', 'working on']
        if any(keyword in question_lower for keyword in assignment_keywords):
            relevant_tables.add('employee_projects')
        
        return list(relevant_tables)
    
    def _get_search_guidance(self, question: str, intent_result: Dict) -> str:
        """สร้างคำแนะนำการค้นหาตามประเภทคำถาม"""
        
        question_lower = question.lower()
        
        # สำหรับการค้นหาตำแหน่ง
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            position_keyword = self._extract_position_keyword(question)
            return f"""
1. สำหรับการค้นหาตำแหน่ง: position ILIKE '%{position_keyword}%'
2. พิจารณาคำที่คล้ายกัน: frontend = front-end = front end
3. จัดเรียงตามความแม่นยำ: exact match ก่อน, partial match ตาม"""
        
        # สำหรับการนับจำนวน
        elif any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many']):
            return """
1. ใช้ COUNT(*) สำหรับนับจำนวน
2. ใช้ GROUP BY เมื่อต้องการแบ่งกลุ่ม
3. เพิ่ม WHERE clause เมื่อมีเงื่อนไข"""
        
        # สำหรับการค้นหาแผนก
        elif 'แผนก' in question_lower or 'department' in question_lower:
            return """
1. ใช้ department ILIKE '%keyword%' สำหรับค้นหาแผนก
2. พิจารณาชื่อแผนกเต็ม: IT = Information Technology
3. แสดงทั้งชื่อและจำนวนคน"""
        
        # Default guidance
        else:
            return """
1. ใช้ ILIKE สำหรับการค้นหาข้อความ
2. ใช้ JOIN เมื่อต้องการข้อมูลจากหลายตาราง
3. เพิ่ม ORDER BY เพื่อจัดเรียงผล"""
    
    def _extract_position_keyword(self, question: str) -> str:
        """ดึงคำสำคัญเกี่ยวกับตำแหน่งจากคำถาม"""
        
        question_lower = question.lower()
        
        # Position patterns and their variations
        position_patterns = {
            'frontend': ['frontend', 'front-end', 'front end'],
            'backend': ['backend', 'back-end', 'back end'],
            'fullstack': ['fullstack', 'full-stack', 'full stack'],
            'developer': ['developer', 'dev', 'พัฒนา'],
            'designer': ['designer', 'design', 'ดีไซน์'],
            'manager': ['manager', 'จัดการ', 'หัวหน้า'],
            'qa': ['qa', 'quality', 'ทดสอบ'],
            'devops': ['devops', 'dev-ops', 'ops']
        }
        
        for position, patterns in position_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                return position
        
        # If no specific pattern found, try to extract the word after "ตำแหน่ง"
        import re
        match = re.search(r'ตำแหน่ง\s*(\w+)', question_lower)
        if match:
            return match.group(1)
        
        match = re.search(r'position\s*(\w+)', question_lower)
        if match:
            return match.group(1)
        
        return 'developer'  # default
    
    def _extract_sql_with_validation(self, ai_response: str, question: str) -> str:
        """🔍 Extract SQL with enhanced validation"""
        
        # Try multiple patterns to extract SQL
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?)\s*```',
            r'(SELECT.*?);?\s*(?:\n|$)',
            r'Query:\s*(SELECT.*?)(?:\n|$)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                
                # Clean up the SQL
                sql = self._clean_sql(sql)
                
                # Validate that it makes sense for the question
                if self._validate_sql_relevance(sql, question):
                    return sql
        
        # If no valid SQL found, create a fallback
        logger.warning(f"No valid SQL extracted from AI response for question: {question}")
        return self._create_fallback_sql(question)
    
    def _clean_sql(self, sql: str) -> str:
        """🧹 Clean and normalize SQL query"""
        
        # Remove trailing semicolon
        sql = sql.rstrip(';').strip()
        
        # Remove extra whitespace
        sql = re.sub(r'\s+', ' ', sql)
        
        # Ensure proper SELECT format
        if not sql.upper().startswith('SELECT'):
            sql = f"SELECT {sql}" if not sql.startswith('*') else f"SELECT {sql}"
        
        return sql
    
    def _validate_sql_relevance(self, sql: str, question: str) -> bool:
        """🔍 Validate that SQL is relevant to the question"""
        
        sql_lower = sql.lower()
        question_lower = question.lower()
        
        # Check for dangerous operations
        dangerous_ops = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate']
        if any(op in sql_lower for op in dangerous_ops):
            return False
        
        # Check if SQL addresses the question intent
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            return 'position' in sql_lower
        
        if 'แผนก' in question_lower or 'department' in question_lower:
            return 'department' in sql_lower
        
        if 'กี่คน' in question_lower or 'how many' in question_lower:
            return 'count' in sql_lower
        
        # Basic check - must be a SELECT statement
        return sql_lower.startswith('select')
    
    def _create_fallback_sql(self, question: str) -> str:
        """🔄 Create fallback SQL when extraction fails"""
        
        question_lower = question.lower()
        
        if 'ตำแหน่ง' in question_lower and 'frontend' in question_lower:
            return """
            SELECT name, position, department, salary 
            FROM employees 
            WHERE position ILIKE '%frontend%' 
            ORDER BY name 
            LIMIT 20
            """
        
        elif 'แผนก' in question_lower and 'กี่คน' in question_lower:
            return """
            SELECT department, COUNT(*) as employee_count 
            FROM employees 
            GROUP BY department 
            ORDER BY employee_count DESC
            """
        
        else:
            return """
            SELECT name, department, position 
            FROM employees 
            ORDER BY name 
            LIMIT 20
            """
    
    async def _execute_sql_enhanced(self, sql_query: str, tenant_id: str) -> List[Dict[str, Any]]:
        """🎯 Enhanced SQL execution with better error handling"""
        
        try:
            logger.info(f"🗄️ Executing SQL for {tenant_id}: {sql_query[:100]}...")
            
            results = self.database_handler.execute_sql_query(tenant_id, sql_query)
            
            # Convert Decimal to float for JSON serialization
            processed_results = []
            for row in results:
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        processed_row[key] = float(value)
                    else:
                        processed_row[key] = value
                processed_results.append(processed_row)
            
            logger.info(f"✅ SQL executed successfully: {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ SQL execution failed for {tenant_id}: {e}")
            logger.error(f"❌ Failed SQL: {sql_query}")
            return []
    
    def _format_enhanced_response(self, results: List[Dict], question: str, 
                                tenant_id: str, schema_info: Dict, sql_query: str) -> str:
        """🎨 Enhanced response formatting with business context"""
        
        if not results:
            return f"ไม่พบข้อมูลที่ตรงกับคำถาม: {question}"
        
        config = self._get_config(tenant_id)
        business_emoji = self._get_business_emoji(tenant_id)
        
        response = f"{business_emoji} ผลการค้นหา - {config.name}\n\n"
        response += f"🎯 คำถาม: {question}\n\n"
        
        # Format results based on data type
        if self._is_counting_query(sql_query):
            response += self._format_counting_results(results, tenant_id)
        elif self._is_listing_query(sql_query):
            response += self._format_listing_results(results, tenant_id)
        else:
            response += self._format_general_results(results, tenant_id)
        
        # Add summary
        response += f"\n💡 สรุป: พบข้อมูล {len(results)} รายการ"
        
        # Add schema info if using live data
        if not schema_info.get('fallback', False):
            response += " (ข้อมูลล่าสุดจากฐานข้อมูล)"
        
        return response
    
    def _is_counting_query(self, sql: str) -> bool:
        """ตรวจสอบว่าเป็น query ที่นับจำนวนหรือไม่"""
        return 'count(' in sql.lower() or 'group by' in sql.lower()
    
    def _is_listing_query(self, sql: str) -> bool:
        """ตรวจสอบว่าเป็น query ที่แสดงรายการหรือไม่"""
        return 'name' in sql.lower() and 'count(' not in sql.lower()
    
    def _format_counting_results(self, results: List[Dict], tenant_id: str) -> str:
        """จัดรูปแบบผลลัพธ์สำหรับการนับจำนวน"""
        
        response = "📊 สถิติและจำนวน:\n"
        
        for i, row in enumerate(results, 1):
            response += f"{i:2d}. "
            
            for key, value in row.items():
                if 'count' in key.lower():
                    response += f"{key}: {value:,} คน, "
                elif key.lower() == 'department':
                    response += f"แผนก{value}: "
                else:
                    response += f"{key}: {value}, "
            
            response = response.rstrip(', ') + "\n"
        
        return response
    
    def _format_listing_results(self, results: List[Dict], tenant_id: str) -> str:
        """จัดรูปแบบผลลัพธ์สำหรับการแสดงรายการ"""
        
        response = "👥 รายชื่อพนักงาน:\n"
        
        for i, row in enumerate(results[:15], 1):  # จำกัด 15 รายการ
            response += f"{i:2d}. "
            
            # แสดงชื่อก่อน
            if 'name' in row:
                response += f"👤 {row['name']}"
            
            # แสดงตำแหน่ง
            if 'position' in row:
                response += f" - {row['position']}"
            
            # แสดงแผนก
            if 'department' in row:
                response += f" (แผนก{row['department']})"
            
            # แสดงเงินเดือน
            if 'salary' in row and isinstance(row['salary'], (int, float)):
                currency = "USD" if tenant_id == 'company-c' else "บาท"
                response += f" | เงินเดือน: {row['salary']:,.0f} {currency}"
            
            response += "\n"
        
        if len(results) > 15:
            response += f"... และอีก {len(results) - 15} รายการ\n"
        
        return response
    
    def _format_general_results(self, results: List[Dict], tenant_id: str) -> str:
        """จัดรูปแบบผลลัพธ์ทั่วไป"""
        
        response = "📋 ข้อมูลที่พบ:\n"
        
        for i, row in enumerate(results[:10], 1):
            response += f"{i:2d}. "
            
            for key, value in row.items():
                if key.lower() in ['salary', 'budget'] and isinstance(value, (int, float)):
                    currency = "USD" if tenant_id == 'company-c' else "บาท"
                    response += f"{key}: {value:,.0f} {currency}, "
                else:
                    response += f"{key}: {value}, "
            
            response = response.rstrip(', ') + "\n"
        
        if len(results) > 10:
            response += f"... และอีก {len(results) - 10} รายการ\n"
        
        return response
    
    # ========================================================================
    # 🔧 ENHANCED HELPER METHODS
    # ========================================================================
    
    def _get_business_context_enhanced(self, tenant_id: str) -> str:
        """🏢 Enhanced business context with real data insights"""
        
        enhanced_contexts = {
            'company-a': """🏢 บริบท: สำนักงานใหญ่ กรุงเทพมฯ - Enterprise Banking & E-commerce
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบธนาคาร, CRM, โปรเจคขนาดใหญ่ (800K-3M บาท)
👥 ลูกค้าหลัก: ธนาคารกรุงเทพ, ธนาคารไทยพาณิชย์, Central Group""",

            'company-b': """🏨 บริบท: สาขาภาคเหนือ เชียงใหม่ - Tourism & Hospitality Technology
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบท่องเที่ยว, โรงแรม, วัฒนธรรมล้านนา (300K-800K บาท)
👥 ลูกค้าหลัก: โรงแรมดุสิต, การท่องเที่ยวแห่งประเทศไทย""",

            'company-c': """🌍 บริบท: International Office - Global Software Solutions
💰 สกุลเงิน: USD และ Multi-currency
🎯 เน้น: ระบบข้ามประเทศ, Global compliance (1M-4M USD)
👥 ลูกค้าหลัก: MegaCorp International (USA), Global Finance Corp (Singapore)"""
        }
        
        return enhanced_contexts.get(tenant_id, enhanced_contexts['company-a'])
    
    def _log_intent_decision(self, question: str, intent_result: Dict, tenant_id: str):
        """📊 Log intent decisions for analysis and improvement"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': question[:100],  # Truncate for privacy
            'intent': intent_result['intent'],
            'confidence': intent_result['confidence'],
            'sql_score': intent_result.get('sql_score', 0),
            'conv_score': intent_result.get('conv_score', 0),
            'tenant_id': tenant_id
        }
        
        try:
            # Append to intent log file
            import os
            os.makedirs('/app/logs', exist_ok=True)
            with open('/app/logs/intent_decisions.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.warning(f"Could not log intent decision: {e}")
    
    # ========================================================================
    # 🔄 FALLBACK AND ERROR HANDLING
    # ========================================================================
    
    def _create_fallback_conversational_response(self, question: str, tenant_id: str, 
                                               start_time: datetime, intent_result: Dict) -> Dict[str, Any]:
        """💬 Create fallback conversational response"""
        
        config = self._get_config(tenant_id)
        business_emoji = self._get_business_emoji(tenant_id)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if self._is_greeting(question):
            fallback_greetings = {
                'company-a': f"""สวัสดีครับ! ผมคือ AI Assistant สำหรับ {config.name} (Enhanced v2.1)

{business_emoji} ระบบธนาคารและองค์กร - พร้อมให้บริการ
💡 ตัวอย่างคำถาม: 
  • "ใครอยู่ตำแหน่ง frontend บ้าง"
  • "มีพนักงานกี่คนในแผนก IT"
  • "โปรเจคธนาคารมีงบประมาณเท่าไร" """,

                'company-b': f"""สวัสดีเจ้า! ผมคือ AI Assistant สำหรับ {config.name} (Enhanced v2.1)

{business_emoji} ระบบท่องเที่ยวและโรงแรม - พร้อมให้บริการ
💡 ตัวอย่างคำถาม: 
  • "ใครอยู่ตำแหน่ง designer บ้าง"
  • "มีโปรเจคท่องเที่ยวอะไรบ้าง"
  • "ลูกค้าโรงแรมในเชียงใหม่" """,

                'company-c': f"""Hello! I'm the AI Assistant for {config.name} (Enhanced v2.1)

{business_emoji} International Operations - Ready to help
💡 Example questions: 
  • "Who are the frontend developers?"
  • "How many employees in each department?"
  • "What's the USD budget breakdown?" """
            }
            
            answer = fallback_greetings.get(tenant_id, fallback_greetings['company-a'])
        else:
            answer = f"{business_emoji} Enhanced System สำหรับ {config.name}\n\nคำถาม: {question}\n\n💡 ลองถามคำถามที่เฉพาะเจาะจงมากขึ้น เช่น:\n• การค้นหาพนักงาน: \"ใครอยู่ตำแหน่ง [ตำแหน่ง] บ้าง\"\n• การนับจำนวน: \"มีพนักงานกี่คนในแผนก [แผนก]\""
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": f"enhanced_conversational_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "processing_time_seconds": processing_time,
            "system_used": "enhanced_conversational_fallback",
            "intent_detection": intent_result,
            "fixed_agent_version": "v2.1_enhanced"
        }
    
    def _create_sql_error_response(self, question: str, tenant_id: str, 
                                 error_message: str, intent_result: Dict) -> Dict[str, Any]:
        """❌ Create SQL error response with helpful guidance"""
        
        config = self._get_config(tenant_id)
        business_emoji = self._get_business_emoji(tenant_id)
        
        answer = f"""{business_emoji} ไม่สามารถประมวลผลคำถามได้

คำถาม: {question}

⚠️ ปัญหา: {error_message}

💡 คำแนะนำ:
• ลองถามใหม่ด้วยรูปแบบที่ชัดเจนขึ้น
• ตัวอย่าง: "ใครอยู่ตำแหน่ง frontend บ้าง" หรือ "มีพนักงานกี่คนในแผนก IT"

หรือลองถามเกี่ยวกับข้อมูลทั่วไปของบริษัท"""
        
        return {
            "answer": answer,
            "success": False,
            "data_source_used": f"enhanced_sql_error_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_used": "enhanced_sql_error_handling",
            "intent_detection": intent_result,
            "error_reason": error_message,
            "fixed_agent_version": "v2.1_enhanced"
        }
    
    def _create_error_response(self, error_message: str, tenant_id: str) -> Dict[str, Any]:
        """❌ Create general error response"""
        return {
            "answer": f"เกิดข้อผิดพลาดในระบบ: {error_message}",
            "success": False,
            "data_source_used": "enhanced_error",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_used": "error_handler",
            "error": error_message,
            "fixed_agent_version": "v2.1_enhanced"
        }
    
    # ========================================================================
    # 🔧 UTILITY METHODS (Enhanced versions)
    # ========================================================================
    
    def _is_greeting(self, question: str) -> bool:
        """ตรวจสอบว่าเป็นการทักทายหรือไม่"""
        greetings = ['สวัสดี', 'hello', 'hi', 'ช่วย', 'help', 'คุณคือใคร']
        return any(word in question.lower() for word in greetings)
    
    def _is_valid_sql(self, sql: str) -> bool:
        """🔒 Enhanced SQL validation for security"""
        if not sql or not sql.strip():
            return False
        
        sql_upper = sql.upper()
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"🚨 Dangerous SQL keyword detected: {keyword}")
                return False
        
        # Must start with SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        # Basic syntax check
        if sql_upper.count('SELECT') > 5:  # Prevent overly complex queries
            logger.warning("🚨 Query too complex")
            return False
        
        return True
    
    def _get_config(self, tenant_id: str) -> TenantConfig:
        """📝 Get tenant configuration"""
        return self.tenant_configs[tenant_id]
    
    def _get_business_emoji(self, tenant_id: str) -> str:
        """🎯 Get business emoji for each company"""
        emojis = {
            'company-a': '🏦',  # Banking
            'company-b': '🏨',  # Tourism  
            'company-c': '🌍'   # International
        }
        return emojis.get(tenant_id, '💼')
    
    # ========================================================================
    # 📊 SYSTEM MONITORING AND STATISTICS
    # ========================================================================
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """📊 Get comprehensive system statistics"""
        
        success_rate = 0
        if self.stats['total_queries'] > 0:
            success_rate = ((self.stats['sql_queries'] + self.stats['conversational_queries']) / 
                          self.stats['total_queries']) * 100
        
        return {
            'agent_version': 'enhanced_v2.1_with_intent_detection',
            'total_queries': self.stats['total_queries'],
            'sql_queries': self.stats['sql_queries'],
            'conversational_queries': self.stats['conversational_queries'],
            'success_rate': round(success_rate, 2),
            'intent_detection': {
                'enabled': True,
                'version': 'enhanced_multi_pattern_v2.1'
            },
            'schema_discovery': {
                'enabled': True,
                'cache_enabled': True,
                'cache_ttl': self.schema_inspector.cache_ttl
            },
            'prompt_manager': {
                'available': PROMPT_MANAGER_AVAILABLE,
                'active': self.use_prompt_manager,
                'supported_companies': getattr(self, 'supported_companies', [])
            },
            'tenant_configs': list(self.tenant_configs.keys()),
            'enhanced_features': [
                'real_time_schema_discovery',
                'enhanced_intent_detection',
                'adaptive_sql_generation',
                'business_context_awareness',
                'error_recovery_mechanisms'
            ]
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS
    # ========================================================================
    
    async def process_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Compatibility method"""
        return await self.process_enhanced_question(question, tenant_id)
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Enhanced streaming implementation"""
        
        # Send initial status
        yield {
            "type": "status", 
            "message": "🎯 Enhanced Intent Detection...", 
            "system": "enhanced_v2.1"
        }
        
        # Detect intent
        intent_result = self.intent_detector.detect_intent(question)
        yield {
            "type": "intent_detected",
            "intent": intent_result['intent'],
            "confidence": intent_result['confidence'],
            "message": f"Intent: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})"
        }
        
        # Process question
        result = await self.process_enhanced_question(question, tenant_id)
        
        # Stream answer in chunks
        answer = result["answer"]
        chunk_size = 100
        
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i+chunk_size]
            yield {"type": "answer_chunk", "content": chunk}
            
        # Send completion info
        yield {
            "type": "answer_complete",
            "sql_query": result.get("sql_query"),
            "db_results_count": result.get("db_results_count", 0),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
            "tenant_id": tenant_id,
            "system_used": result.get("system_used", "enhanced_v2.1"),
            "intent_detection": result.get("intent_detection", {}),
            "fixed_agent_version": "v2.1_enhanced"
        }