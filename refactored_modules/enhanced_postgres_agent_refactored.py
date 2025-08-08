# 🔥 Enhanced PostgreSQL Agent - Universal Prompt System Integration
# refactored_modules/enhanced_postgres_agent_refactored.py

import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from decimal import Decimal

# Import our refactored modules
from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .schema_discovery import SchemaDiscoveryService
from .business_logic_mapper import BusinessLogicMapper
from .ai_service import AIService
from .prompt_generator import PromptGenerator
from .intent_classifier import IntentClassifier

# 🔥 CHANGED: Import Universal Prompt System instead of Few-Shot
# from .few_shot_sql_engine import EnhancedFewShotAgent  # ❌ เอาออก
from .universal_prompt_system import UniversalPromptGenerator  # ✅ เพิ่ม

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_decimal_to_float(obj: Any) -> Any:
    """🔧 Convert Decimal objects to float recursively"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimal_to_float(item) for item in obj)
    else:
        return obj  

class EnhancedPostgresOllamaAgent:
    """🚀 Enhanced PostgreSQL + Ollama Agent - Universal Prompt System Version"""
    
    def __init__(self):
        # Initialize all services
        self.config_manager = TenantConfigManager()
        self.tenant_configs = self.config_manager.tenant_configs
        
        self.database_handler = DatabaseHandler(self.tenant_configs)
        self.schema_service = SchemaDiscoveryService()
        self.business_mapper = BusinessLogicMapper()
        self.ai_service = AIService()
        self.prompt_generator = PromptGenerator(self.schema_service, self.business_mapper)
        self.intent_classifier = IntentClassifier()
        
        # 🔥 CHANGED: Use Universal Prompt System instead of Few-Shot
        self.universal_prompt_generator = UniversalPromptGenerator()
        
        logger.info("✅ Enhanced PostgreSQL Ollama Agent initialized with Universal Prompt System")

    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Enhanced question processing with Universal Prompt System"""
        if tenant_id not in self.tenant_configs:
            return {
                "answer": f"ไม่รู้จัก tenant: {tenant_id}",
                "success": False,
                "data_source_used": "error",
                "confidence": "none"
            }

        config = self.tenant_configs[tenant_id]
        start_time = datetime.now()
        
        # 🔥 ใช้ Intent Classifier ตรวจสอบก่อน
        intent_result = self.intent_classifier.classify_intent(question)
        logger.info(f"Intent classification for '{question}': {intent_result}")
        
        # 🎯 ถ้าไม่ใช่คำถามที่ต้องใช้ SQL
        if not intent_result['should_use_sql']:
            return await self._handle_non_sql_question(
                question, tenant_id, intent_result, config
            )
        
        # 🗄️ ถ้าเป็นคำถามที่ต้องใช้ SQL - ใช้ Universal Prompt System
        try:
            # 1. Enhanced SQL generation with Universal Prompt
            sql_query, sql_metadata = await self.generate_enhanced_sql(question, tenant_id)
            
            # 2. Execute SQL query
            db_results = self.database_handler.execute_sql_query(tenant_id, sql_query)
            
            # 3. Convert Decimal to float before JSON serialization
            processed_results = self.database_handler.process_decimal_data(db_results)
            
            # 4. Enhanced interpretation
            schema_info = self.schema_service.get_schema_info(tenant_id)
            interpretation_prompt = self.prompt_generator.create_enhanced_interpretation_prompt(
                question, sql_query, processed_results, config, schema_info
            )
            
            ai_response = await self.ai_service.call_ollama_api(
                config, interpretation_prompt, temperature=0.3
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": ai_response,
                "success": True,
                "data_source_used": f"universal_prompt_{config.model_name}",  # 🔥 CHANGED
                "sql_query": sql_query,
                "db_results_count": len(processed_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "sql_generation_method": sql_metadata["method"],  # 🔥 จะเป็น "universal_prompt_system"
                "confidence": sql_metadata["confidence"],
                "processing_time_seconds": processing_time,
                "intent_detected": intent_result['intent'],
                "enhancement_version": "3.0_universal_prompt"  # 🔥 CHANGED
            }
            
        except Exception as e:
            logger.error(f"Universal Prompt processing failed for {tenant_id}: {e}")
            
            # Enhanced fallback
            try:
                fallback_prompt = self._create_enhanced_fallback_prompt(question, tenant_id)
                ai_response = await self.ai_service.call_ollama_api(config, fallback_prompt)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "answer": ai_response,
                    "success": True,
                    "data_source_used": f"enhanced_fallback_{config.model_name}",
                    "error": str(e),
                    "fallback_mode": True,
                    "confidence": "low",
                    "processing_time_seconds": processing_time,
                    "intent_detected": intent_result['intent'],
                    "enhancement_version": "3.0_universal_prompt_fallback"
                }
            except Exception as ai_error:
                return {
                    "answer": f"เกิดข้อผิดพลาดในระบบ: {str(e)}",
                    "success": False,
                    "data_source_used": "error",
                    "error": str(ai_error),
                    "confidence": "none"
                }

    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """🔥 Fixed streaming version with Universal Prompt System"""
        if tenant_id not in self.tenant_configs:
            yield {
                "type": "error",
                "message": f"ไม่รู้จัก tenant: {tenant_id}"
            }
            return

        config = self.tenant_configs[tenant_id]
        start_time = datetime.now()

        try:
            # 📊 Step 1: Generate SQL with Universal Prompt
            yield {
                "type": "status",
                "message": "🎯 กำลังสร้าง SQL Query ด้วย Universal Prompt System...",
                "step": "universal_sql_generation"
            }
            
            sql_query, sql_metadata = await self.generate_enhanced_sql(question, tenant_id)
            
            yield {
                "type": "sql_generated",
                "sql_query": sql_query,
                "method": sql_metadata["method"],  # "universal_prompt_system"
                "confidence": sql_metadata["confidence"]
            }

            # 🗄️ Step 2: Execute SQL
            yield {
                "type": "status", 
                "message": "📊 กำลังดึงข้อมูลจากฐานข้อมูล...",
                "step": "database_query"
            }
            
            db_results = self.database_handler.execute_sql_query(tenant_id, sql_query)
            
            # 🔧 FIX: Process Decimal data BEFORE yielding
            processed_results = self.database_handler.process_decimal_data(db_results)
            
            # 🔧 FIX: Convert any remaining Decimals in preview
            safe_preview = []
            for item in processed_results[:3]:
                safe_item = convert_decimal_to_float(item)
                safe_preview.append(safe_item)
            
            yield {
                "type": "db_results",
                "count": len(processed_results),
                "preview": safe_preview
            }

            # 🤖 Step 3: Create interpretation prompt
            schema_info = self.schema_service.get_schema_info(tenant_id)
            interpretation_prompt = self.prompt_generator.create_enhanced_interpretation_prompt(
                question, sql_query, processed_results, config, schema_info
            )

            # 🔥 Step 4: Stream AI response
            yield {
                "type": "status",
                "message": "🤖 AI กำลังวิเคราะห์และตอบคำถาม...",
                "step": "ai_processing"
            }
            
            yield {"type": "answer_start"}

            # Stream the AI response token by token
            async for token in self.ai_service.call_ollama_api_streaming(
                config, interpretation_prompt, temperature=0.3
            ):
                yield {
                    "type": "answer_chunk",
                    "content": token
                }

            # ✅ Final metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            
            yield {
                "type": "answer_complete",
                "sql_query": sql_query,
                "db_results_count": len(processed_results),
                "sql_generation_method": sql_metadata["method"],  # "universal_prompt_system"
                "confidence": sql_metadata["confidence"],
                "processing_time_seconds": processing_time,
                "tenant_id": tenant_id,
                "model_used": config.model_name
            }

        except Exception as e:
            logger.error(f"Universal Prompt streaming processing failed for {tenant_id}: {e}")
            yield {
                "type": "error",
                "message": f"เกิดข้อผิดพลาดในระบบ Universal Prompt: {str(e)}"
            }

    async def generate_enhanced_sql(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """🎯 Enhanced SQL generation with Universal Prompt System"""
        
        try:
            logger.info(f"🎯 Using Universal Prompt System for: {question[:50]}...")
            
            # 🔥 CHANGED: Use Universal Prompt instead of Few-Shot
            sql_query, metadata = await self.universal_prompt_generator.generate_sql_with_universal_prompt(
                question, tenant_id, self
            )
            
            # เช็คว่า SQL ที่ได้มีคุณภาพดีไหม
            if self._is_high_quality_sql(sql_query, question):
                logger.info(f"✅ Universal Prompt Success! Method: {metadata['method']}")
                return sql_query, metadata
            else:
                logger.warning("🔄 Universal Prompt SQL quality insufficient, falling back...")
                
        except Exception as e:
            logger.warning(f"🔄 Universal Prompt failed: {e}, falling back to original method")
        
        # Fallback to original enhanced method
        return await self.original_generate_enhanced_sql(question, tenant_id)

    async def original_generate_enhanced_sql(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """Enhanced SQL generation with business intelligence and pattern matching (Original Method)"""
        
        config = self.tenant_configs[tenant_id]
        schema_info = self.schema_service.get_schema_info(tenant_id)
        business_logic = self.business_mapper.get_business_logic(tenant_id)
        
        # Analyze question for intent and patterns
        query_analysis = self._analyze_question_intent(question, tenant_id)
        
        # Check for pre-defined patterns
        if query_analysis['pattern_match']:
            sql_query = self._apply_sql_pattern(query_analysis, tenant_id)
            metadata = {
                'method': 'pattern_matching_original',
                'pattern_used': query_analysis['pattern_match'],
                'confidence': 'high'
            }
            return sql_query, metadata
        
        # Generate enhanced system prompt
        system_prompt = self.prompt_generator.create_enhanced_sql_prompt(
            question, schema_info, business_logic, config
        )
        
        try:
            # Call AI with enhanced prompt
            ai_response = await self.ai_service.call_ollama_api(
                tenant_config=config,
                prompt=system_prompt,
                context_data="",
                temperature=0.1
            )
            
            # Extract and validate SQL
            sql_query = self._extract_and_validate_sql(ai_response, tenant_id)
            
            metadata = {
                'method': 'ai_generation_original',
                'original_response': ai_response[:200],
                'confidence': 'medium' if len(sql_query) > 50 else 'low'
            }
            
            return sql_query, metadata
            
        except Exception as e:
            logger.error(f"Original enhanced SQL generation failed: {e}")
            fallback_sql = self._generate_fallback_sql(question, tenant_id)
            metadata = {
                'method': 'fallback_original', 
                'error': str(e),
                'confidence': 'low'
            }
            return fallback_sql, metadata

    def _is_high_quality_sql(self, sql: str, question: str) -> bool:
        """🔍 ตรวจสอบคุณภาพ SQL ที่ Universal Prompt สร้าง"""
        sql_upper = sql.upper()
        question_lower = question.lower()
        
        # Basic validation
        if not sql_upper.startswith('SELECT'):
            return False
        
        if 'แต่ละคน' in question_lower and 'รับผิดชอบ' in question_lower:
            if 'LEFT JOIN' not in sql_upper:
                logger.warning("❌ Assignment query without LEFT JOIN")
                return False
            
            if 'COALESCE' not in sql_upper:
                logger.warning("❌ Assignment query without COALESCE for NULL handling")
                return False
        
        dangerous_patterns = [
            'AND.*OR.*ORDER',
            'SELECT \\*',
            'WHERE.*ILIKE.*AND.*ILIKE.*OR'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"❌ Found dangerous pattern: {pattern}")
                return False
        
        return True

    def get_universal_prompt_stats(self) -> Dict[str, Any]:
        """📊 ดึงสถิติการใช้งาน Universal Prompt System"""
        if hasattr(self, 'universal_prompt_generator'):
            stats = self.universal_prompt_generator.get_statistics()
            
            return {
                "universal_prompt_enabled": True,
                "version": "3.0",
                "companies_supported": len(self.universal_prompt_generator.company_profiles),
                "business_types": [
                    profile.business_type 
                    for profile in self.universal_prompt_generator.company_profiles.values()
                ],
                "templates_available": len(self.universal_prompt_generator.prompt_templates),
                "pattern_matchers": len(self.universal_prompt_generator.pattern_matchers),
                "status": "active",
                **stats
            }
        else:
            return {
                "universal_prompt_enabled": False,
                "error": "Universal Prompt System not initialized"
            }

    # 🔧 Keep all existing methods (unchanged)
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
        sql_template = self.business_mapper.get_sql_pattern(pattern)
        
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
                if self.database_handler.validate_sql_query(sql, tenant_id):
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
            
            if self.database_handler.validate_sql_query(sql_query, tenant_id):
                return sql_query
        
        # Final fallback
        return self._generate_fallback_sql("Unable to generate SQL", tenant_id)

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

    async def _handle_non_sql_question(self, question: str, tenant_id: str, 
                                    intent_result: dict, config: TenantConfig) -> Dict[str, Any]:
        """🔥 Handle non-SQL questions with AI-generated responses"""
        
        intent = intent_result['intent']
        
        # สร้าง context-aware prompt ตาม intent
        if intent == 'greeting':
            context_prompt = self._create_greeting_prompt(config)
        elif intent == 'help':
            context_prompt = self._create_help_prompt(config)
        else:
            context_prompt = self._create_general_conversation_prompt(question, config)
        
        # 🔥 ให้ AI สร้างคำตอบ
        ai_response = await self.ai_service.call_ollama_api(
            tenant_config=config,
            prompt=context_prompt,
            context_data="",
            temperature=0.7  # ใช้ temperature สูงกว่าเพื่อความเป็นธรรมชาติ
        )
        
        return {
            "answer": ai_response,
            "success": True,
            "data_source_used": f"conversational_{config.model_name}",
            "intent_detected": intent,
            "intent_confidence": intent_result['confidence'],
            "sql_used": False,
            "processing_type": "ai_conversational",
            "tenant_id": tenant_id,
            "enhancement_version": "3.0_universal_prompt"
        }

    def _create_greeting_prompt(self, config: TenantConfig) -> str:
        """Create context-aware greeting prompt for AI"""
        
        if config.language == 'th':
            return f"""คุณเป็น AI Assistant ที่เป็นมิตรและมีประโยชน์ของ {config.name}

ข้อมูลบริษัท:
- ชื่อ: {config.name}
- ลักษณะงาน: {config.business_type}
- ความเชี่ยวชาญ: การพัฒนาซอฟต์แวร์และเทคโนโลยี

ความสามารถของคุณ:
- วิเคราะห์ข้อมูลพนักงานและโปรเจค
- ตอบคำถามเกี่ยวกับธุรกิจและการดำเนินงาน
- สร้างรายงานและสถิติต่างๆ

ตัวอย่างคำถามที่คุณตอบได้:
• มีพนักงานกี่คนในแต่ละแผนก
• โปรเจคไหนมีงบประมาณสูงสุด
• พนักงานคนไหนทำงานในโปรเจคหลายโปรเจค

ผู้ใช้ทักทายคุณ กรุณาตอบทักทายอย่างเป็นมิตร แนะนำตัวเอง และบอกว่าคุณสามารถช่วยอะไรได้บ้าง:"""
        
        else:  # English
            return f"""You are a friendly and helpful AI Assistant for {config.name}

Company Information:
- Name: {config.name}
- Business: {config.business_type}
- Expertise: Software development and technology solutions

Your Capabilities:
- Analyze employee and project data
- Answer questions about business operations
- Generate reports and statistics

Example questions you can answer:
• How many employees are in each department?
• Which projects have the highest budgets?
• Which employees work on multiple projects?

The user is greeting you. Please respond in a friendly manner, introduce yourself, and explain how you can help:"""

    def _create_help_prompt(self, config: TenantConfig) -> str:
        """Create help prompt for AI"""
        
        if config.language == 'th':
            return f"""คุณเป็น AI Assistant ของ {config.name} ผู้ใช้ถามว่าคุณสามารถช่วยอะไรได้บ้าง

บริบทบริษัท:
- ธุรกิจ: {config.business_type}
- ข้อมูลที่มี: พนักงาน, โปรเจค, งบประมาณ, ลูกค้า, แผนกต่างๆ

ประเภทการวิเคราะห์ที่คุณทำได้:
1. ข้อมูลพนักงาน (จำนวน, เงินเดือน, แผนก, ตำแหน่ง)
2. ข้อมูลโปรเจค (งบประมาณ, สถานะ, ทีมงาน, ลูกค้า)
3. การวิเคราะห์ประสิทธิภาพ (KPI, สถิติ, แนวโน้ม)
4. รายงานสำหรับผู้บริหาร

กรุณาอธิบายความสามารถของคุณอย่างชัดเจนและให้ตัวอย่างคำถามที่เป็นประโยชน์:"""
        
        else:
            return f"""You are an AI Assistant for {config.name}. The user is asking what you can help with.

Company Context:
- Business Type: {config.business_type}
- Available Data: employees, projects, budgets, clients, departments

Types of analysis you can perform:
1. Employee data (count, salaries, departments, positions)
2. Project information (budgets, status, teams, clients)
3. Performance analysis (KPIs, statistics, trends)
4. Executive reports

Please explain your capabilities clearly and provide useful example questions:"""

    def _create_general_conversation_prompt(self, question: str, config: TenantConfig) -> str:
        """Create prompt for general conversation"""
        
        if config.language == 'th':
            return f"""คุณเป็น AI Assistant ที่เป็นมิตรของ {config.name}

บริษัทของเรา:
- ชื่อ: {config.name}
- ประเภทธุรกิจ: {config.business_type}
- ความเชี่ยวชาญ: การพัฒนาซอฟต์แวร์และเทคโนโลยี

คำถามผู้ใช้: {question}

หากคำถามเกี่ยวข้องกับข้อมูลบริษัท ให้แนะนำว่าคุณสามารถช่วยวิเคราะห์ข้อมูลได้
หากเป็นคำถามทั่วไป ให้ตอบอย่างเป็นมิตรและเป็นประโยชน์
ไม่ต้องพยายามสร้าง SQL หรือเข้าถึงฐานข้อมูล:"""
        
        else:
            return f"""You are a friendly AI Assistant for {config.name}

Our Company:
- Name: {config.name}
- Business Type: {config.business_type}
- Expertise: Software development and technology solutions

User Question: {question}

If the question relates to company data, suggest that you can help analyze information
If it's a general question, respond in a friendly and helpful manner
Don't try to generate SQL or access databases:"""

    def _create_enhanced_fallback_prompt(self, question: str, tenant_id: str) -> str:
        """Create enhanced fallback prompt with business context"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.schema_service.get_schema_info(tenant_id)
        
        if config.language == 'en':
            return f"""As a business consultant for {config.name}, please answer this question using your knowledge about {config.business_type} operations.

Company Context:
- Business Focus: {schema_info.get('business_context', {}).get('primary_focus', 'N/A')}
- Client Type: {schema_info.get('business_context', {}).get('client_profile', 'N/A')}
- Project Scale: {schema_info.get('business_context', {}).get('project_scale', 'N/A')}

Question: {question}

Note: Direct database access is temporarily unavailable. Please provide helpful insights based on typical {config.business_type} operations and best practices.

Provide a professional, informative response:"""
        else:
            return f"""ในฐานะที่ปรึกษาธุรกิจสำหรับ {config.name} กรุณาตอบคำถามนี้โดยใช้ความรู้เกี่ยวกับการดำเนินงาน {config.business_type}

บริบทบริษัท:
- จุดเน้นธุรกิจ: {schema_info.get('business_context', {}).get('primary_focus', 'ไม่ระบุ')}
- ประเภทลูกค้า: {schema_info.get('business_context', {}).get('client_profile', 'ไม่ระบุ')}
- ขนาดโปรเจค: {schema_info.get('business_context', {}).get('project_scale', 'ไม่ระบุ')}

คำถาม: {question}

หมายเหตุ: ไม่สามารถเข้าถึงฐานข้อมูลโดยตรงได้ในขณะนี้ กรุณาให้ข้อมูลเชิงลึกที่เป็นประโยชน์โดยอิงจากการดำเนินงาน {config.business_type} ทั่วไปและแนวทางปฏิบัติที่ดี

ให้คำตอบที่เป็นมืออาชีพและให้ข้อมูล:"""


# 🧪 Test Function สำหรับ Universal Prompt Integration
async def test_universal_prompt_integration():
    """🧪 ทดสอบ Universal Prompt Integration กับ Enhanced Agent"""
    agent = EnhancedPostgresOllamaAgent()
    
    test_scenarios = [
        {
            "tenant": "company-a",
            "questions": [
                "สวัสดีครับ",  # Should be conversational
                "มีพนักงานกี่คนในแต่ละแผนก",  # Should use Universal Prompt
                "พนักงานคนไหนมีเงินเดือนสูงที่สุด"  # Should use Universal Prompt
            ]
        },
        {
            "tenant": "company-b", 
            "questions": [
                "มีโปรเจคท่องเที่ยวอะไรบ้าง",  # Should use Universal Prompt (Tourism)
                "โปรเจคโรงแรมมีกี่โปรเจค"  # Should use Universal Prompt (Tourism)
            ]
        },
        {
            "tenant": "company-c",
            "questions": [
                "Which projects have highest USD budget",  # Should use Universal Prompt (International)
                "How many international employees"  # Should use Universal Prompt (International)
            ]
        }
    ]
    
    print("🧪 Testing Universal Prompt System Integration")
    print("=" * 70)
    
    for scenario in test_scenarios:
        print(f"\n🏢 Testing {scenario['tenant'].upper()}")
        print("-" * 50)
        
        for question in scenario['questions'][:2]:  # Test only 2 questions per tenant
            print(f"\n❓ Question: {question}")
            
            result = await agent.process_enhanced_question(question, scenario['tenant'])
            
            # Extract key information
            success = result.get('success', False)
            sql_method = result.get('sql_generation_method', 'N/A')
            data_source = result.get('data_source_used', 'N/A')
            fallback_mode = result.get('fallback_mode', False)
            sql_query = result.get('sql_query')
            
            # Determine status
            if 'universal_prompt' in sql_method:
                status = "✅ UNIVERSAL PROMPT SUCCESS"
            elif sql_method == 'few_shot_learning':
                status = "⚠️ USING FEW-SHOT (Not Universal)"
            elif fallback_mode:
                status = "❌ FALLBACK MODE"
            elif 'conversational' in data_source:
                status = "💬 CONVERSATIONAL (Expected)"
            else:
                status = "❓ UNKNOWN METHOD"
            
            print(f"   {status}")
            print(f"   Success: {success}")
            print(f"   SQL Method: {sql_method}")
            print(f"   Data Source: {data_source}")
            print(f"   Has SQL: {'Yes' if sql_query else 'No'}")
            print(f"   Answer: {result['answer'][:100]}...")
    
    # Test Universal Prompt Statistics
    print(f"\n📊 Universal Prompt System Statistics:")
    print("-" * 50)
    
    try:
        stats = agent.get_universal_prompt_stats()
        print(f"   Enabled: {stats.get('universal_prompt_enabled', False)}")
        print(f"   Version: {stats.get('version', 'N/A')}")
        print(f"   Companies: {stats.get('companies_supported', 0)}")
        print(f"   Status: {stats.get('status', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error getting stats: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced PostgreSQL Ollama Agent - Universal Prompt Integration")
    print("🎯 Now using Universal Prompt System instead of Few-Shot Learning")
    asyncio.run(test_universal_prompt_integration())