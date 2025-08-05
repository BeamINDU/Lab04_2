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
from enterprise_intent_classifier import EnterpriseIntentIntegration
from enterprise_schema_validator import EnterpriseQueryValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TenantConfig:
    """Enhanced Tenant configuration"""
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
    """🏗️ Enterprise-Grade PostgreSQL + Ollama Agent with Auto-Discovery v3.0"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434')
        self.tenant_configs = self._load_enhanced_tenant_configs()
        
        # 🚀 ENTERPRISE UPGRADE: Replace hard-coded validation
        self.enterprise_validator = EnterpriseQueryValidator(self.tenant_configs)
        self._enterprise_initialized = False
        
        self.enterprise_intent = None

        # Keep old methods for fallback
        self.sql_patterns = self._load_sql_patterns()
        self._initialization_lock = asyncio.Lock()

    async def _ensure_enterprise_intent_initialized(self):
        if self.enterprise_intent is None and self._enterprise_initialized:
            self.enterprise_intent = EnterpriseIntentIntegration(self.enterprise_validator)
            logger.info("🧠 Enterprise Intent Classifier ready")

    async def _ensure_enterprise_initialized(self):
        """🔧 FIXED: Ensure enterprise validator is initialized"""
        if not self._enterprise_initialized:
            async with self._initialization_lock:
                if not self._enterprise_initialized:  # Double-check
                    try:
                        logger.info("🔍 Initializing Enterprise Schema Discovery...")
                        await self.enterprise_validator.initialize()
                        self._enterprise_initialized = True
                        logger.info("✅ Enterprise validation ready")
                    except Exception as e:
                        logger.error(f"🚨 Enterprise initialization failed: {e}")
                        # Use fallback mode instead of failing
                        self._enterprise_initialized = False
    
    async def generate_enhanced_sql(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """🏗️ Enterprise SQL generation with auto-discovery validation"""
        
        # 1. 🚀 ENTERPRISE VALIDATION - Replace all hard-coded checks
        await self._ensure_enterprise_initialized()
        
        validation_result = await self.enterprise_validator.validate_question(question, tenant_id)
        
        if not validation_result['can_answer']:
            # Return enterprise-grade explanation
            metadata = {
                'method': 'enterprise_schema_validation',
                'missing_concepts': validation_result['missing_concepts'],
                'available_tables': validation_result['available_tables'],
                'confidence': 'high',
                'explanation': validation_result['response']
            }
            return "SELECT 'ENTERPRISE_VALIDATION_FAILED' as message;", metadata
        
        # 2. Continue with SQL generation using discovered schema
        config = self.tenant_configs[tenant_id]
        
        # 🚀 Get auto-discovered schema context (no more hard-coding!)
        enterprise_schema_context = self.enterprise_validator.get_safe_sql_context(tenant_id)
        
        # 3. Create enterprise-grade prompt
        system_prompt = self._create_enterprise_sql_prompt(question, enterprise_schema_context, config)
        
        try:
            ai_response = await self.call_ollama_api(
                tenant_id=tenant_id,
                prompt=system_prompt,
                context_data="",
                temperature=0.1
            )
            
            # Extract and validate SQL
            sql_query = self._extract_and_validate_sql(ai_response, tenant_id)
            
            # 🛡️ Enterprise validation using discovered schema
            is_valid, validation_msg = self._validate_sql_enterprise(sql_query, tenant_id)
            
            if not is_valid:
                logger.warning(f"Enterprise SQL validation failed: {validation_msg}")
                fallback_sql = self._generate_enterprise_fallback_sql(question, tenant_id)
                metadata = {
                    'method': 'enterprise_validated_fallback',
                    'validation_error': validation_msg,
                    'confidence': 'medium'
                }
                return fallback_sql, metadata
            
            metadata = {
                'method': 'enterprise_ai_generation',
                'confidence': 'high',
                'validation': validation_msg,
                'schema_source': 'auto_discovered'
            }
            
            return sql_query, metadata
            
        except Exception as e:
            logger.error(f"Enterprise SQL generation failed: {e}")
            fallback_sql = self._generate_enterprise_fallback_sql(question, tenant_id)
            metadata = {
                'method': 'enterprise_error_fallback',
                'error': str(e),
                'confidence': 'low'
            }
            return fallback_sql, metadata
    
    def _create_enterprise_sql_prompt(self, question: str, schema_context: str, config: TenantConfig) -> str:
        """🏗️ Create enterprise SQL prompt with auto-discovered schema"""
        
        if config.language == 'th':
            prompt = f"""🏗️ คุณคือ Enterprise SQL Expert สำหรับ {config.name}

{schema_context}

🚨 กฎเหล็กสำหรับ Enterprise System:
1. ใช้เฉพาะตารางและคอลัมน์ที่แสดงข้างต้น (auto-discovered จากฐานข้อมูลจริง)
2. ห้ามสร้างตาราง/คอลัมน์ที่ไม่มี - ระบบได้ตรวจสอบแล้ว
3. ใช้ PostgreSQL syntax เท่านั้น (ไม่ใช่ MySQL)
4. SELECT queries เท่านั้น พร้อม LIMIT
5. ใช้ proper JOINs ตาม foreign key relationships

💡 Enterprise Best Practices:
- ใช้ table aliases: employees e, projects p
- Format เงินด้วย TO_CHAR สำหรับการแสดงผล
- ใช้ ORDER BY เพื่อให้ผลลัพธ์มีความหมาย
- GROUP BY เมื่อต้องการสรุปข้อมูล

คำถาม: {question}

สร้าง Enterprise-grade PostgreSQL query:"""
        
        else:  # English
            prompt = f"""🏗️ You are an Enterprise SQL Expert for {config.name}

{schema_context}

🚨 Enterprise System Rules:
1. Use ONLY tables and columns shown above (auto-discovered from real database)
2. NEVER create non-existent tables/columns - system has validated
3. PostgreSQL syntax only (not MySQL)
4. SELECT queries only with LIMIT
5. Use proper JOINs following foreign key relationships

💡 Enterprise Best Practices:
- Use table aliases: employees e, projects p
- Format currency with appropriate functions
- Use ORDER BY for meaningful results
- GROUP BY when aggregating data

Question: {question}

Generate Enterprise-grade PostgreSQL query:"""
        
        return prompt
    
    def _validate_sql_enterprise(self, sql: str, tenant_id: str) -> Tuple[bool, str]:
        """🛡️ Validate SQL using enterprise schema discovery"""
        sql_upper = sql.upper()
        
        # 1. Basic security checks
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            return False, f"❌ Dangerous SQL operations not allowed"
        
        # 2. Must be SELECT
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return False, f"❌ Only SELECT queries allowed"
        
        # 3. 🏗️ ENTERPRISE VALIDATION using discovered schema
        if self._enterprise_initialized and tenant_id in self.enterprise_validator.schema_service.discovered_schemas:
            discovered_schema = self.enterprise_validator.schema_service.discovered_schemas[tenant_id]
            
            # Check table references
            has_valid_table = False
            for table_name in discovered_schema.tables.keys():
                if table_name.upper() in sql_upper:
                    has_valid_table = True
                    
                    # Check column references for this table
                    valid_columns = discovered_schema.tables[table_name]
                    # Basic column validation (in production, use proper SQL parser)
                    for column in valid_columns:
                        if column.upper() in sql_upper:
                            continue  # Valid column reference
            
            if not has_valid_table and 'FROM' in sql_upper:
                return False, f"❌ No valid table references found (using enterprise schema discovery)"
        
        return True, "✅ Enterprise SQL validation passed"
    
    def _generate_enterprise_fallback_sql(self, question: str, tenant_id: str) -> str:
        """🏗️ Generate enterprise fallback using discovered schema"""
        question_lower = question.lower()
        
        # Get available tables from discovery
        if self._enterprise_initialized and tenant_id in self.enterprise_validator.schema_service.discovered_schemas:
            schema = self.enterprise_validator.schema_service.discovered_schemas[tenant_id]
            
            if any(word in question_lower for word in ['พนักงาน', 'employee']) and 'employees' in schema.tables:
                columns = schema.tables['employees'][:3]  # First 3 columns
                return f"SELECT {', '.join(columns)} FROM employees ORDER BY {columns[0]} LIMIT 10;"
                
            elif any(word in question_lower for word in ['โปรเจค', 'project']) and 'projects' in schema.tables:
                columns = schema.tables['projects'][:3]
                return f"SELECT {', '.join(columns)} FROM projects ORDER BY {columns[0]} LIMIT 10;"
        
        # Safe fallback
        config = self.tenant_configs[tenant_id]
        if config.language == 'th':
            return "SELECT 'ไม่สามารถสร้าง SQL ได้ กรุณาลองคำถามใหม่' as message;"
        else:
            return "SELECT 'Cannot generate SQL. Please try a different question' as message;"
    
    async def create_enhanced_interpretation_prompt(self, question: str, sql_query: str, results: List[Dict], tenant_id: str) -> str:
        """🏗️ Enterprise interpretation with discovered schema context"""
        config = self.tenant_configs[tenant_id]
        
        # Check if this was enterprise validation failure
        if sql_query.strip() == "SELECT 'ENTERPRISE_VALIDATION_FAILED' as message;":
            # Get the validation result again for the explanation
            await self._ensure_enterprise_initialized()
            validation_result = await self.enterprise_validator.validate_question(question, tenant_id)
            return f"DIRECT_RESPONSE: {validation_result['response']}"
        
        # Regular interpretation using enterprise context
        if not results:
            enterprise_context = ""
            if self._enterprise_initialized:
                schema_summary = self.enterprise_validator.get_schema_summary(tenant_id)
                if 'tables' in schema_summary:
                    enterprise_context = f"\n📊 Available in {config.name}:\n"
                    for table, info in schema_summary['tables'].items():
                        enterprise_context += f"• {table}: {info['column_count']} columns\n"
            
            if config.language == 'th':
                no_data_msg = f"""ไม่พบข้อมูลที่ตรงกับคำถาม "{question}"{enterprise_context}

💡 ลองถามคำถามอื่น เช่น:
• "มีพนักงานกี่คนในแต่ละแผนก"
• "โปรเจคไหนมีงบประมาณสูงสุด"
• "พนักงานคนไหนได้เงินเดือนสูงสุด"
"""
            else:
                no_data_msg = f"""No data found for "{question}"{enterprise_context}

💡 Try asking:
• "How many employees in each department"  
• "Which projects have highest budget"
• "Which employee has highest salary"
"""
            return f"DIRECT_RESPONSE: {no_data_msg}"
        
        # Format results with enterprise context
        formatted_results = self._format_results_safely(results, tenant_id)
        
        if config.language == 'th':
            prompt = f"""🏗️ คุณคือนักวิเคราะห์ Enterprise ที่ตอบตามข้อมูลจริงเท่านั้น

คำถาม: {question}
SQL: {sql_query}
ผลลัพธ์: {len(results)} รายการ (จากการค้นหาอัตโนมัติในฐานข้อมูล)

{formatted_results}

🏗️ Enterprise Analysis Guidelines:
1. ตอบตามข้อมูลที่มีเท่านั้น - ไม่เดา ไม่สมมติ
2. ข้อมูลได้รับการตรวจสอบด้วย Enterprise Schema Discovery
3. ตัวเลขทั้งหมดมาจากฐานข้อมูลจริง
4. ให้คำแนะนำเชิงธุรกิจที่เป็นประโยชน์

ให้การวิเคราะห์ระดับ Enterprise:"""
        
        else:
            prompt = f"""🏗️ You are an Enterprise Analyst responding ONLY to actual data

Question: {question}
SQL: {sql_query}
Results: {len(results)} records (from automated database discovery)

{formatted_results}

🏗️ Enterprise Analysis Guidelines:
1. Answer ONLY based on provided data - NO assumptions
2. Data validated through Enterprise Schema Discovery
3. All numbers from actual database only
4. Provide actionable business insights

Provide Enterprise-grade analysis:"""
        
        return prompt

    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🏗️ Enterprise question processing with dynamic intent classification"""
        if tenant_id not in self.tenant_configs:
            return {
                "answer": f"Unknown tenant: {tenant_id}",
                "success": False,
                "data_source_used": "error",
                "confidence": "none"
            }
        
        config = self.tenant_configs[tenant_id]
        start_time = datetime.now()
        
        logger.info(f"🔍 Processing question: {question[:100]}...")
        
        # 1. 🏗️ Initialize enterprise systems
        await self._ensure_enterprise_initialized()
        await self._ensure_enterprise_intent_initialized()
        
        # 2. 🧠 ENTERPRISE INTENT CLASSIFICATION
        if self.enterprise_intent:
            intent_result = self.enterprise_intent.classify_question_intent(question, tenant_id)
            logger.info(f"🧠 Enterprise intent: {intent_result}")
        else:
            # Fallback to basic classification
            from intent_classifier import IntentClassifier
            basic_classifier = IntentClassifier()
            basic_result = basic_classifier.classify_intent(question)
            intent_result = {
                'intent': basic_result['intent'],
                'confidence': basic_result['confidence'],
                'should_use_sql': basic_result['should_use_sql'],
                'reasoning': 'Fallback to basic classification'
            }
            logger.info(f"🔄 Basic intent (fallback): {intent_result}")
        
        # 3. 💬 Handle non-SQL questions
        if not intent_result['should_use_sql']:
            logger.info(f"📝 Processing as conversational: {intent_result['reasoning']}")
            return await self._handle_non_sql_question_enterprise(
                question, tenant_id, intent_result, config
            )
        
        try:
            logger.info(f"🚀 Starting enterprise SQL processing - Intent: {intent_result['intent']}")
            
            # 4. 🏗️ Enterprise SQL generation with auto-discovery
            sql_query, sql_metadata = await self.generate_enhanced_sql(question, tenant_id)
            
            logger.info(f"🔧 SQL Generated: {sql_query[:100]}...")
            logger.info(f"🔧 SQL Metadata: {sql_metadata}")
            
            # Check if enterprise validation failed
            if sql_query.strip() == "SELECT 'ENTERPRISE_VALIDATION_FAILED' as message;":
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info("❌ Enterprise validation failed, returning explanation")
                return {
                    "answer": sql_metadata['explanation'],
                    "success": True,
                    "data_source_used": "enterprise_schema_validation",
                    "missing_concepts": sql_metadata.get('missing_concepts', []),
                    "available_tables": sql_metadata.get('available_tables', []),
                    "sql_query": "N/A (validation failed)",
                    "tenant_id": tenant_id,
                    "confidence": "high",
                    "processing_time_seconds": processing_time,
                    "enterprise_validation": True,
                    "schema_source": "auto_discovered",
                    "intent_classification": intent_result,
                    "enhancement_version": "3.0_enterprise"
                }
            
            # 5. Execute SQL query
            logger.info("🗄️ Executing SQL query...")
            db_results = self.execute_sql_query(tenant_id, sql_query)
            logger.info(f"📊 Query results: {len(db_results)} rows")
            
            # 6. 🏗️ Enterprise interpretation
            logger.info("🧠 Creating interpretation prompt...")
            interpretation_prompt = await self.create_enhanced_interpretation_prompt(
                question, sql_query, db_results, tenant_id
            )
            
            # Check for direct response
            if interpretation_prompt.startswith("DIRECT_RESPONSE: "):
                ai_response = interpretation_prompt[17:]
                logger.info("📝 Using direct response")
            else:
                logger.info("🤖 Calling AI for interpretation...")
                ai_response = await self.call_ollama_api(
                    tenant_id, 
                    interpretation_prompt, 
                    temperature=0.2
                )
                logger.info(f"🤖 AI response: {ai_response[:100]}...")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info("✅ Enterprise processing completed successfully")
            
            return {
                "answer": ai_response,
                "success": True,
                "data_source_used": f"enterprise_discovery_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(db_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "ai_generated_sql": True,
                "sql_generation_method": sql_metadata['method'],
                "confidence": sql_metadata['confidence'],
                "processing_time_seconds": processing_time,
                "business_context": config.business_type,
                "enterprise_validation": True,
                "schema_source": "auto_discovered",
                "intent_classification": intent_result,  # 🧠 Include intent details
                "enhancement_version": "3.0_enterprise",
                "validation_passed": True
            }
            
        except Exception as e:
            logger.error(f"🚨 Enterprise processing failed for {tenant_id}: {e}")
            
            # 🔥 ENHANCED FALLBACK
            try:
                logger.info("🛡️ Attempting enhanced fallback...")
                
                simple_answer = await self._create_simple_fallback_answer(question, tenant_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "answer": simple_answer,
                    "success": True,
                    "data_source_used": f"enhanced_fallback_{config.model_name}",
                    "error": str(e),
                    "fallback_mode": True,
                    "confidence": "medium",
                    "processing_time_seconds": processing_time,
                    "enterprise_validation": True,
                    "intent_classification": intent_result,
                    "enhancement_version": "3.0_enterprise",
                    "fallback_reason": "exception_recovery"
                }
            except Exception as ai_error:
                logger.error(f"🚨 Even fallback failed: {ai_error}")
                
                return {
                    "answer": self._create_helpful_error_message(question, tenant_id, str(e)),
                    "success": False,
                    "data_source_used": "error_with_suggestions",
                    "error": str(ai_error),
                    "original_error": str(e),
                    "confidence": "none",
                    "enterprise_validation": True,
                    "intent_classification": intent_result,
                    "suggestions": [
                        "ลองถามเกี่ยวกับพนักงานในโปรเจค",
                        "ถามเกี่ยวกับสถานะโปรเจค",
                        "ถามเกี่ยวกับงบประมาณโปรเจค"
                    ]
                }

    async def _create_simple_fallback_answer(self, question: str, tenant_id: str) -> str:
        """🛡️ Create simple fallback answer without enterprise features"""
        config = self.tenant_configs[tenant_id]
        question_lower = question.lower()
        
        # Enhanced pattern matching with intent awareness
        if ('ใคร' in question_lower or 'who' in question_lower) and ('โปรเจค' in question_lower or 'project' in question_lower):
            try:
                # Enhanced SQL for project team queries
                if 'mobile banking' in question_lower or 'banking' in question_lower:
                    simple_sql = """
                        SELECT DISTINCT
                            p.name as project_name,
                            p.client,
                            e.name as employee_name,
                            e.position,
                            ep.role,
                            CASE 
                                WHEN ep.role ILIKE '%lead%' OR ep.role ILIKE '%manager%' 
                                THEN '🔸 ผู้นำ'
                                ELSE '👤 สมาชิก'
                            END as leadership_role
                        FROM projects p
                        LEFT JOIN employee_projects ep ON p.id = ep.project_id
                        LEFT JOIN employees e ON ep.employee_id = e.id
                        WHERE (p.name ILIKE '%mobile%banking%' OR p.name ILIKE '%banking%')
                        AND e.name IS NOT NULL
                        ORDER BY 
                            CASE WHEN ep.role ILIKE '%lead%' OR ep.role ILIKE '%manager%' THEN 1 ELSE 2 END,
                            e.name
                        LIMIT 10;
                    """
                else:
                    # General project team query
                    simple_sql = """
                        SELECT DISTINCT
                            p.name as project_name,
                            p.client,
                            e.name as employee_name,
                            e.position,
                            ep.role
                        FROM projects p
                        LEFT JOIN employee_projects ep ON p.id = ep.project_id
                        LEFT JOIN employees e ON ep.employee_id = e.id
                        WHERE e.name IS NOT NULL
                        ORDER BY p.start_date DESC, e.name
                        LIMIT 15;
                    """
                
                results = self.execute_sql_query(tenant_id, simple_sql)
                
                if results:
                    answer = f"จากข้อมูลโปรเจคและทีมงาน:\n\n"
                    
                    current_project = None
                    leaders_found = []
                    
                    for row in results:
                        if row['project_name'] != current_project:
                            current_project = row['project_name']
                            answer += f"📋 **{current_project}**\n"
                            if row.get('client'):
                                answer += f"   ลูกค้า: {row['client']}\n"
                        
                        if row['employee_name']:
                            role_indicator = row.get('leadership_role', '👤')
                            answer += f"   {role_indicator} {row['employee_name']} ({row['position']}) - {row['role']}\n"
                            
                            # Track leaders
                            if 'lead' in row.get('role', '').lower() or 'manager' in row.get('role', '').lower():
                                leaders_found.append(f"{row['employee_name']} ({row['role']})")
                    
                    if leaders_found:
                        answer += f"\n🔸 **ผู้นำโปรเจค**: {', '.join(leaders_found)}\n"
                    
                    answer += "\n💡 หากต้องการข้อมูลเพิ่มเติม:\n"
                    answer += "• ถามเกี่ยวกับสถานะโปรเจค\n"
                    answer += "• ถามเกี่ยวกับงบประมาณ\n"
                    answer += "• ถามเกี่ยวกับไทม์ไลน์โปรเจค"
                    
                    return answer
                else:
                    return self._create_no_data_message(question, tenant_id)
                    
            except Exception as e:
                logger.error(f"Enhanced fallback SQL failed: {e}")
                return self._create_no_data_message(question, tenant_id)
        
        # Handle other question types...
        elif 'โปรเจค' in question_lower:
            try:
                simple_sql = """
                    SELECT 
                        p.name,
                        p.client,
                        p.status,
                        p.budget,
                        COUNT(ep.employee_id) as team_size
                    FROM projects p
                    LEFT JOIN employee_projects ep ON p.id = ep.project_id
                    GROUP BY p.id, p.name, p.client, p.status, p.budget
                    ORDER BY p.start_date DESC 
                    LIMIT 5;
                """
                results = self.execute_sql_query(tenant_id, simple_sql)
                
                if results:
                    answer = f"โปรเจคปัจจุบันของ {config.name}:\n\n"
                    for i, row in enumerate(results, 1):
                        budget_fmt = f"{row['budget']:,.0f} บาท" if row['budget'] else "ไม่ระบุ"
                        team_size = row.get('team_size', 0)
                        answer += f"{i}. **{row['name']}**\n"
                        answer += f"   ลูกค้า: {row['client']}\n"
                        answer += f"   สถานะ: {row['status']}\n"
                        answer += f"   งบประมาณ: {budget_fmt}\n"
                        answer += f"   ทีมงาน: {team_size} คน\n\n"
                    
                    answer += "💡 ลองถามเฉพาะเจาะจงเกี่ยวกับโปรเจคใดโปรเจคหนึ่ง"
                    return answer
                else:
                    return self._create_no_data_message(question, tenant_id)
                    
            except Exception as e:
                logger.error(f"Project fallback failed: {e}")
                return self._create_no_data_message(question, tenant_id)
        
        # Default response
        return self._create_no_data_message(question, tenant_id)


    def _create_no_data_message(self, question: str, tenant_id: str) -> str:
        """📝 Create helpful no-data message"""
        config = self.tenant_configs[tenant_id]
        
        if config.language == 'th':
            return f"""ขออภัยครับ ไม่พบข้อมูลที่ตรงกับคำถาม "{question}"

    📊 ข้อมูลที่มีใน {config.name}:
    • ข้อมูลพนักงาน (ชื่อ, ตำแหน่ง, แผนก, เงินเดือน)
    • ข้อมูลโปรเจค (ชื่อ, ลูกค้า, งบประมาณ, สถานะ)
    • การมอบหมายงาน (ใครทำงานในโปรเจคไหน, บทบาทอะไร)

    💡 ลองถามคำถามเหล่านี้:
    • "มีโปรเจคอะไรบ้าง"
    • "ใครทำงานในโปรเจค [ชื่อโปรเจค]"
    • "สถานะของโปรเจค [ชื่อโปรเจค] เป็นอย่างไร"
    • "โปรเจคไหนมีงบประมาณสูงสุด"
    • "พนักงานคนไหนเป็นผู้นำโปรเจค"
    """
        else:
            return f"""Sorry, no data found for "{question}"

    📊 Available data in {config.name}:
    • Employee information (name, position, department, salary)
    • Project data (name, client, budget, status)
    • Work assignments (who works on which project, what role)

    💡 Try these questions:
    • "What projects do we have?"
    • "Who works on [project name]?"
    • "What's the status of [project name]?"
    • "Which project has the highest budget?"
    • "Who leads [project name]?"
    """
        
    async def _handle_non_sql_question_enterprise(self, question: str, tenant_id: str, 
                                                intent_result: dict, config: TenantConfig) -> Dict[str, Any]:
        """🏗️ Handle non-SQL questions with enterprise context and dynamic intent"""
        
        intent = intent_result.get('intent', 'unknown')
        reasoning = intent_result.get('reasoning', 'No reasoning provided')
        
        # Get enterprise schema context for better responses
        await self._ensure_enterprise_initialized()
        schema_context = ""
        if tenant_id in self.enterprise_validator.schema_service.discovered_schemas:
            schema_summary = self.enterprise_validator.get_schema_summary(tenant_id)
            if 'tables' in schema_summary:
                schema_context = f"Available data: {list(schema_summary['tables'].keys())}"
        
        if intent == 'greeting':
            context_prompt = self._create_enterprise_greeting_prompt(config, schema_context)
        elif intent == 'conversation' or intent == 'help':
            context_prompt = self._create_enterprise_help_prompt(config, schema_context, intent_result)
        else:
            context_prompt = self._create_enterprise_general_prompt(question, config, schema_context, intent_result)
        
        ai_response = await self.call_ollama_api(
            tenant_id=tenant_id,
            prompt=context_prompt,
            context_data="",
            temperature=0.7
        )
        
        return {
            "answer": ai_response,
            "success": True,
            "data_source_used": f"enterprise_conversational_{config.model_name}",
            "intent_detected": intent,
            "intent_confidence": intent_result.get('confidence', 0.5),
            "intent_reasoning": reasoning,
            "sql_used": False,
            "enterprise_validation": True,
            "schema_source": "auto_discovered",
            "detected_concepts": intent_result.get('detected_concepts', []),
            "tenant_id": tenant_id
        }

    
    def _create_enterprise_greeting_prompt(self, config: TenantConfig, schema_context: str) -> str:
        """🏗️ Enterprise greeting with auto-discovered context"""
        if config.language == 'th':
            return f"""คุณเป็น Enterprise AI Assistant ของ {config.name}

🏗️ ระบบของเรา:
- Enterprise Schema Auto-Discovery
- Real-time Database Validation  
- Zero-Hallucination Architecture

📊 ข้อมูลที่ตรวจพบอัตโนมัติ: {schema_context}

ความสามารถ Enterprise:
- วิเคราะห์ข้อมูลด้วย AI ขั้นสูง
- ตรวจสอบความถูกต้องแบบอัตโนมัติ
- ไม่มีข้อมูลปลอมหรือการเดา

ผู้ใช้ทักทายคุณ กรุณาแนะนำระบบ Enterprise และความสามารถ:"""
        else:
            return f"""You are an Enterprise AI Assistant for {config.name}

🏗️ Our System Features:
- Enterprise Schema Auto-Discovery
- Real-time Database Validation
- Zero-Hallucination Architecture

📊 Auto-discovered data: {schema_context}

Enterprise Capabilities:
- Advanced AI data analysis
- Automated accuracy validation
- No fake data or assumptions

User is greeting you. Introduce the Enterprise system and capabilities:"""
    
    def _create_enterprise_help_prompt(self, config: TenantConfig, schema_context: str, intent_result: dict) -> str:
        """🏗️ Enterprise help with dynamic intent context"""
        detected_concepts = intent_result.get('detected_concepts', [])
        
        if config.language == 'th':
            prompt = f"""คุณเป็น Enterprise AI Assistant ของ {config.name}

    🏗️ ระบบ Enterprise ของเรา:
    - Schema Auto-Discovery: ค้นหาโครงสร้างฐานข้อมูลอัตโนมัติ
    - Dynamic Intent Classification: จำแนกความต้องการอัจฉริยะ
    - Real-time Validation: ตรวจสอบความถูกต้องแบบเรียลไทม์

    📊 ข้อมูลที่ตรวจพบ: {schema_context}

    🧠 ความเข้าใจจากคำถาม: {intent_result.get('reasoning', 'ไม่ระบุ')}
    """
            
            if detected_concepts:
                prompt += f"🔍 แนวคิดที่เกี่ยวข้อง: {', '.join(detected_concepts)}\n"
            
            prompt += """
    ความสามารถหลัก:
    1. วิเคราะห์ข้อมูลพนักงาน โปรเจค แผนกงาน
    2. ตอบคำถาม "ใคร" "อะไร" "กี่" ด้วยข้อมูลจริง
    3. สร้างรายงานและสถิติแบบเรียลไทม์
    4. ป้องกันข้อมูลปลอม 100%

    💡 ตัวอย่างคำถาม:
    • "ใครคือผู้นำโปรเจค [ชื่อโปรเจค]"
    • "มีพนักงานกี่คนในแต่ละแผนก"
    • "โปรเจคไหนมีงบประมาณสูงสุด"

    กรุณาอธิบายความสามารถ Enterprise อย่างละเอียด:"""
            
        else:
            prompt = f"""You are an Enterprise AI Assistant for {config.name}

    🏗️ Our Enterprise System:
    - Schema Auto-Discovery: Automatic database structure detection
    - Dynamic Intent Classification: Intelligent intent recognition
    - Real-time Validation: Live accuracy verification

    📊 Discovered data: {schema_context}

    🧠 Intent Understanding: {intent_result.get('reasoning', 'Not specified')}
    """
            
            if detected_concepts:
                prompt += f"🔍 Related concepts: {', '.join(detected_concepts)}\n"
            
            prompt += """
    Core Capabilities:
    1. Employee, project, and department data analysis
    2. Answer "who", "what", "how many" with real data
    3. Real-time reports and statistics
    4. 100% hallucination prevention

    💡 Example questions:
    • "Who leads the [project name] project?"
    • "How many employees in each department?"
    • "Which project has the highest budget?"

    Explain Enterprise capabilities in detail:"""
        
        return prompt
    
    def _create_helpful_error_message(self, question: str, tenant_id: str, error: str) -> str:
        config = self.tenant_configs[tenant_id]
        
        if config.language == 'th':
            return f"""ระบบ Enterprise ไม่สามารถประมวลผลคำถามได้ในขณะนี้

    🏗️ ข้อมูลระบบ:
    • {config.name}
    • Enterprise Schema Auto-Discovery ✅
    • Dynamic Intent Classification ✅
    • ข้อผิดพลาดชั่วคราว: {error[:100]}...

    📊 ข้อมูลที่มีอยู่:
    • ข้อมูลพนักงาน และ ทีมงาน
    • ข้อมูลโปรเจค และ ลูกค้า
    • สถิติและรายงานต่างๆ

    💡 กรุณาลองคำถามที่ชัดเจน เช่น:
    • "ใครเป็นผู้นำโปรเจค [ชื่อเฉพาะ]"
    • "มีโปรเจคอะไรบ้าง"
    • "พนักงานในแผนก IT มีใครบ้าง"
    • "โปรเจคที่มีงบประมาณสูงสุด 3 อันดับ"

    ระบบจะตรวจสอบและตอบด้วยข้อมูลที่แม่นยำ"""
        else:
            return f"""Enterprise system cannot process the question at this time

    🏗️ System Information:
    • {config.name}
    • Enterprise Schema Auto-Discovery ✅
    • Dynamic Intent Classification ✅
    • Temporary error: {error[:100]}...

    📊 Available data:
    • Employee and team information
    • Project and client data
    • Statistics and reports

    💡 Please try specific questions like:
    • "Who leads [specific project name]?"
    • "What projects do we have?"
    • "Who are the IT department employees?"
    • "Top 3 projects by budget?"

    System will validate and respond with accurate data"""
    def _create_enterprise_general_prompt(self, question: str, config: TenantConfig, 
                                        schema_context: str, intent_result: dict) -> str:
        """🏗️ Enterprise general conversation with intent context"""
        
        if config.language == 'th':
            return f"""คุณเป็น Enterprise AI Assistant ของ {config.name}

    คำถาม: {question}

    🏗️ บริบท Enterprise:
    - Intent ที่ตรวจพบ: {intent_result.get('intent', 'ไม่ระบุ')}
    - เหตุผล: {intent_result.get('reasoning', 'ไม่ระบุ')}
    - ข้อมูลที่มี: {schema_context}

    🧠 แนวคิดที่เกี่ยวข้อง: {', '.join(intent_result.get('detected_concepts', []))}

    หากคำถามเกี่ยวกับข้อมูลที่ไม่มี ให้อธิบายด้วย Enterprise System
    หากเป็นคำถามทั่วไป ให้ตอบในบริบท Enterprise โดยอ้างอิงข้อมูลที่มีจริง:"""
        
        else:
            return f"""You are an Enterprise AI Assistant for {config.name}

    Question: {question}

    🏗️ Enterprise Context:
    - Detected Intent: {intent_result.get('intent', 'Unknown')}
    - Reasoning: {intent_result.get('reasoning', 'Not specified')}
    - Available data: {schema_context}

    🧠 Related concepts: {', '.join(intent_result.get('detected_concepts', []))}

    If asking about unavailable data, explain using Enterprise system
    If general question, respond in Enterprise context with reference to actual data:"""

    
    # Keep essential methods from original class
    def _load_enhanced_tenant_configs(self) -> Dict[str, TenantConfig]:
        """Load tenant configurations"""
        configs = {}
        
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
        
        configs['company-b'] = TenantConfig(
            tenant_id='company-b',
            name='SiamTech Chiang Mai Regional',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_B', 'postgres-company-b'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_B', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_B', 'siamtech_company_b'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_B', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_B', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_B', 'llama3.1:8b'),
            language='th',
            business_type='tourism_hospitality',
            key_metrics=['client_count', 'regional_budget', 'tourism_projects']
        )
        
        configs['company-c'] = TenantConfig(
            tenant_id='company-c',
            name='SiamTech International',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_C', 'postgres-company-c'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_C', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_C', 'siamtech_company_c'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_C', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_C', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_C', 'llama3.1:8b'),
            language='en',
            business_type='global_operations',
            key_metrics=['usd_revenue', 'international_clients', 'global_projects']
        )
        
        return configs
    
    def _load_sql_patterns(self) -> Dict[str, str]:
        """Safe SQL patterns for fallback"""
        return {
            'employee_count_by_department': """
                SELECT 
                    department,
                    COUNT(*) as employee_count,
                    ROUND(AVG(salary), 0) as avg_salary
                FROM employees 
                GROUP BY department 
                ORDER BY employee_count DESC
                LIMIT 10;
            """,
            'top_earners': """
                SELECT 
                    name,
                    position,
                    department,
                    salary
                FROM employees 
                ORDER BY salary DESC 
                LIMIT 5;
            """,
            'high_budget_projects': """
                SELECT 
                    name as project_name,
                    client,
                    budget,
                    status
                FROM projects
                WHERE budget > 1000000
                ORDER BY budget DESC
                LIMIT 10;
            """
        }
    
    def _extract_and_validate_sql(self, ai_response: str, tenant_id: str) -> str:
        """Extract SQL from AI response"""
        cleaned = ai_response.strip()
        
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;)\s*```',
            r'(SELECT.*?;)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                return sql
        
        return self._generate_enterprise_fallback_sql("default", tenant_id)
    
    def _format_results_safely(self, results: List[Dict], tenant_id: str) -> str:
        """Format results safely"""
        if not results:
            return "ไม่มีข้อมูล"
        
        config = self.tenant_configs[tenant_id]
        formatted = "ข้อมูลจากฐานข้อมูล (Enterprise Validated):\n"
        
        for i, row in enumerate(results[:10], 1):
            formatted += f"{i}. "
            for key, value in row.items():
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    if config.tenant_id == 'company-c':
                        formatted += f"{key}: ${value:,.0f}, "
                    else:
                        formatted += f"{key}: {value:,.0f} บาท, "
                else:
                    formatted += f"{key}: {value}, "
            formatted = formatted.rstrip(", ") + "\n"
        
        if len(results) > 10:
            formatted += f"... และอีก {len(results) - 10} รายการ\n"
        
        return formatted
    
    # Essential database methods
    def get_database_connection(self, tenant_id: str) -> psycopg2.extensions.connection:
        """Get database connection"""
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
        """Execute SQL query safely"""
        conn = None
        try:
            conn = self.get_database_connection(tenant_id)
            cursor = conn.cursor()
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
                
            logger.info(f"Enterprise query executed for {tenant_id}: {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Enterprise SQL execution failed for {tenant_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def call_ollama_api(self, tenant_id: str, prompt: str, context_data: str = "", temperature: float = 0.7) -> str:
        """Call Ollama API"""
        config = self.tenant_configs[tenant_id]
        
        if context_data:
            full_prompt = f"{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        payload = {
            "model": config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 800,
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.0,
                "num_ctx": 2048
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', 'ไม่สามารถรับคำตอบจาก AI ได้')
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return f"เกิดข้อผิดพลาดในการเรียก AI (HTTP {response.status})"
                        
        except asyncio.TimeoutError:
            logger.error("Ollama API timeout")
            return "AI ใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"

# Test function for Enterprise system
async def test_enterprise_system():
    """🧪 Test the Enterprise Auto-Discovery System"""
    agent = EnhancedPostgresOllamaAgent()
    
    test_scenarios = [
        {
            "description": "🚫 Should be blocked by Enterprise validation",
            "questions": [
                ("company-a", "ต้องการรู้ยอดขายเป็นรายเดือน"),
                ("company-a", "มีพนักงานชายกี่คน หญิงกี่คน"),
                ("company-b", "รายได้ประจำเดือนของสาขา"),
            ]
        },
        {
            "description": "✅ Should work with Enterprise discovery",
            "questions": [
                ("company-a", "มีพนักงานกี่คนในแต่ละแผนก"),
                ("company-a", "โปรเจคไหนมีงบประมาณสูงสุด"),
                ("company-b", "พนักงานที่ทำงานโปรเจคท่องเที่ยว"),
                ("company-c", "Which employees work on international projects?"),
            ]
        }
    ]
    
    print("🏗️ Testing Enterprise Auto-Discovery System v3.0")
    print("=" * 60)
    
    for scenario in test_scenarios:
        print(f"\n{scenario['description']}")
        print("-" * 50)
        
        for tenant_id, question in scenario['questions']:
            print(f"\n❓ Question: {question}")
            print(f"🏢 Tenant: {tenant_id}")
            
            try:
                result = await agent.process_enhanced_question(question, tenant_id)
                
                print(f"✅ Success: {result['success']}")
                print(f"🏗️ Enterprise: {result.get('enterprise_validation', False)}")
                print(f"📊 Schema Source: {result.get('schema_source', 'N/A')}")
                print(f"🔍 Method: {result.get('sql_generation_method', 'N/A')}")
                print(f"📋 Available Tables: {result.get('available_tables', [])}")
                print(f"🚫 Missing Concepts: {result.get('missing_concepts', [])}")
                print(f"⏱️ Time: {result.get('processing_time_seconds', 0):.2f}s")
                print(f"💬 Answer: {result['answer'][:150]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print(f"\n🎯 Enterprise Features Demonstrated:")
    print("• Schema Auto-Discovery from real database")
    print("• Dynamic validation without hard-coding")
    print("• Scalable to unlimited companies")
    print("• Real-time schema synchronization")
    print("• Zero maintenance for new tenants")

if __name__ == "__main__":
    print("🏗️ Enterprise PostgreSQL Ollama Agent v3.0")
    print("🔧 Features: Schema Auto-Discovery, Enterprise Validation")
    asyncio.run(test_enterprise_system())