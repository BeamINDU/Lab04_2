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
from decimal import Decimal

from intent_classifier import UniversalIntentClassifier, SchemaAnalyzer, AdaptiveConversationalGenerator, BusinessContext


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
    """🚀 Enhanced PostgreSQL + Ollama Agent with Universal Intent Classification v3.0"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434')
        self.tenant_configs = self._load_enhanced_tenant_configs()
        self.database_schemas = self._load_enhanced_database_schemas()
        self.business_logic_mappings = self._load_business_logic_mappings()
        self.sql_patterns = self._load_sql_patterns()
        
        # 🌍 NEW: Universal Intent Classification Components
        self.intent_classifier = UniversalIntentClassifier()
        self.schema_analyzer = SchemaAnalyzer()
        self.conversational_generator = AdaptiveConversationalGenerator()
        
        # 📊 NEW: Business context cache for performance
        self.business_contexts = {}
        self.schema_cache = {}
        
        logger.info("🌍 Enhanced Agent v3.0 with Universal Intent Classification initialized")
        
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
            model_name=os.getenv('MODEL_COMPANY_B', 'llama3.1:8b'),
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
            model_name=os.getenv('MODEL_COMPANY_C', 'llama3.1:8b'),
            language='en',
            business_type='global_operations',
            key_metrics=['usd_revenue', 'international_clients', 'global_projects', 'multi_currency']
        )
        
        return configs
    
    # 🌍 NEW: Universal Schema Discovery Methods
    async def get_business_context(self, tenant_id: str) -> BusinessContext:
        """📊 Get or create business context for tenant"""
        
        if tenant_id not in self.business_contexts:
            try:
                # Get actual schema from database
                schema = await self.discover_actual_schema(tenant_id)
                
                if not schema:
                    # Fallback to cached schema info
                    schema = self.database_schemas.get(tenant_id, {}).get('tables', {})
                
                # Analyze business context
                business_context = self.schema_analyzer.analyze_schema(schema)
                
                # Cache it
                self.business_contexts[tenant_id] = business_context
                
                logger.info(f"📊 Business context created for {tenant_id}: {len(business_context.key_entities)} entities, {len(business_context.table_names)} tables")
                
            except Exception as e:
                logger.error(f"Failed to create business context for {tenant_id}: {e}")
                # Create minimal fallback context
                self.business_contexts[tenant_id] = BusinessContext(
                    table_names=set(),
                    column_names=set(),
                    text_columns=set(),
                    numeric_columns=set(),
                    date_columns=set(),
                    key_entities=set()
                )
        
        return self.business_contexts[tenant_id]
    
    async def discover_actual_schema(self, tenant_id: str) -> Dict[str, List[str]]:
        """🔍 Discover actual database schema dynamically"""
        
        # Check cache first
        if tenant_id in self.schema_cache:
            return self.schema_cache[tenant_id]
        
        schema = {}
        
        try:
            conn = self.get_database_connection(tenant_id)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            table_results = cursor.fetchall()
            tables = [row[0] for row in table_results] if table_results else []
            
            # Get columns for each table
            for table in tables:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                column_results = cursor.fetchall()
                columns = [row[0] for row in column_results] if column_results else []
                schema[table] = columns
            
            conn.close()
            
            # Cache the schema
            self.schema_cache[tenant_id] = schema
            
            logger.info(f"🔍 Schema discovered for {tenant_id}: {len(schema)} tables")
            return schema
            
        except Exception as e:
            logger.error(f"Schema discovery failed for {tenant_id}: {e}")
            # Return fallback from static config
            return self.database_schemas.get(tenant_id, {}).get('tables', {})
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Enhanced question processing with Universal Intent Classification v3.0"""
        
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
            # 📊 Get business context for this tenant
            business_context = await self.get_business_context(tenant_id)
            
            # 🧠 Universal intent classification
            intent_result = self.intent_classifier.classify_intent(question, business_context)
            
            logger.info(f"🎯 Universal Intent for '{question[:50]}...': {intent_result['intent']}")
            logger.info(f"🔍 Confidence: {intent_result['confidence']:.2f}, Use SQL: {intent_result['should_use_sql']}")
            logger.info(f"💭 Reasoning: {intent_result['reasoning']}")
            
            # 💬 If conversational -> generate adaptive response
            if not intent_result['should_use_sql']:
                logger.info("💬 Processing as conversational question")
                
                response = self.conversational_generator.generate_response(
                    question=question,
                    company_name=config.name,
                    business_context=business_context,
                    language=config.language
                )
                
                # Add intent metadata
                response.update({
                    "intent_detected": intent_result['intent'],
                    "intent_confidence": intent_result['confidence'],
                    "intent_reasoning": intent_result['reasoning'],
                    "business_entities_available": len(business_context.key_entities),
                    "enhancement_version": "3.0_universal"
                })
                
                return response
            
            # 🗄️ If needs SQL -> continue with existing logic
            logger.info("🗄️ Processing as SQL business query")
            return await self._process_sql_question(question, tenant_id, intent_result, business_context, start_time)
            
        except Exception as e:
            logger.error(f"Universal processing failed for {tenant_id}: {e}")
            return await self._universal_fallback(question, tenant_id, str(e))
    
    async def _process_sql_question(self, question: str, tenant_id: str, 
                                   intent_result: Dict, business_context: BusinessContext,
                                   start_time: datetime) -> Dict[str, Any]:
        """🗄️ Process SQL questions with business context"""
        
        config = self.tenant_configs[tenant_id]
        
        try:
            # 1. Enhanced SQL generation
            sql_query, sql_metadata = await self.generate_enhanced_sql(question, tenant_id)
            
            # 2. Execute SQL query
            db_results = self.execute_sql_query(tenant_id, sql_query)
            processed_results = self._process_decimal_data(db_results)
            
            # 3. Check if we have results
            if not processed_results:
                return self._generate_universal_no_data_response(
                    question, tenant_id, sql_query, business_context
                )
            
            # 4. Enhanced interpretation
            interpretation_prompt = await self.create_enhanced_interpretation_prompt(
                question, sql_query, processed_results, tenant_id
            )
            
            ai_response = await self.call_ollama_api(
                tenant_id, interpretation_prompt, temperature=0.3
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": ai_response,
                "success": True,
                "data_source_used": f"universal_sql_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(processed_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "sql_generation_method": sql_metadata["method"],
                "confidence": sql_metadata["confidence"],
                "processing_time_seconds": processing_time,
                "intent_detected": intent_result['intent'],
                "intent_confidence": intent_result['confidence'],
                "intent_reasoning": intent_result['reasoning'],
                "business_entities_detected": len(business_context.key_entities),
                "tables_available": len(business_context.table_names),
                "enhancement_version": "3.0_universal"
            }
            
        except Exception as e:
            logger.error(f"SQL processing failed: {e}")
            return await self._universal_fallback(question, tenant_id, str(e))
    
    def _generate_universal_no_data_response(self, question: str, tenant_id: str, 
                                           sql_query: str, business_context: BusinessContext) -> Dict[str, Any]:
        """🤔 Generate helpful no-data response for any company"""
        
        config = self.tenant_configs[tenant_id]
        language = config.language
        
        # Generate suggestions based on available business entities
        suggestions = []
        entities = list(business_context.key_entities)[:5]
        
        if language == 'th':
            for entity in entities:
                suggestions.append(f"• มีข้อมูล{entity}กี่รายการ?")
                suggestions.append(f"• {entity}ไหนสำคัญที่สุด?")
            
            if not suggestions:
                suggestions = [
                    "• มีข้อมูลอะไรบ้างในระบบ?",
                    "• สรุปสถานการณ์ปัจจุบัน",
                    "• ข้อมูลล่าสุดคืออะไร?"
                ]
            
            answer = f"""ไม่พบข้อมูลที่ตรงกับคำถาม "{question}"

🔍 **SQL ที่ใช้ค้นหา:**
```sql
{sql_query}
```

📊 **ข้อมูลที่มีในระบบ:**
{chr(10).join(f'• ตาราง {table}' for table in sorted(business_context.table_names))}

💡 **ลองถามคำถามเหล่านี้แทน:**
{chr(10).join(suggestions[:6])}

🚀 **หรือสอบถามข้อมูลทั่วไป:**
• มีข้อมูลอะไรบ้างในระบบ?
• สามารถวิเคราะห์อะไรได้บ้าง?"""
        
        else:  # English
            for entity in entities:
                suggestions.append(f"• How many {entity} records?")
                suggestions.append(f"• Which {entity} is most important?")
            
            if not suggestions:
                suggestions = [
                    "• What data is available in the system?",
                    "• Current situation summary",
                    "• What's the latest information?"
                ]
            
            answer = f"""No data found for the question "{question}"

🔍 **SQL query used:**
```sql
{sql_query}
```

📊 **Available data in system:**
{chr(10).join(f'• {table.title()} table' for table in sorted(business_context.table_names))}

💡 **Try asking these questions instead:**
{chr(10).join(suggestions[:6])}

🚀 **Or ask about general information:**
• What data is available in the system?
• What can you analyze?"""
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": "universal_no_data_guidance",
            "sql_query": sql_query,
            "db_results_count": 0,
            "tenant_id": tenant_id,
            "model_used": config.model_name,
            "suggestions_generated": len(suggestions),
            "business_entities_used": len(entities),
            "tables_available": len(business_context.table_names),
            "enhancement_version": "3.0_universal"
        }
    
    async def _universal_fallback(self, question: str, tenant_id: str, error: str) -> Dict[str, Any]:
        """🛡️ Universal fallback for any company"""
        
        config = self.tenant_configs[tenant_id]
        
        try:
            # Try to get business context for better fallback
            business_context = await self.get_business_context(tenant_id)
            
            # Generate contextual fallback response
            response = self.conversational_generator.generate_response(
                question=f"ขออภัย เกิดข้อผิดพลาดในการประมวลผล: {question}",
                company_name=config.name,
                business_context=business_context,
                language=config.language
            )
            
            # Add error information
            response.update({
                "error": error,
                "fallback_mode": True,
                "enhancement_version": "3.0_universal"
            })
            
            return response
            
        except Exception as fallback_error:
            logger.error(f"Universal fallback failed: {fallback_error}")
            
            if config.language == 'th':
                answer = f"""ขออภัย ระบบไม่สามารถประมวลผลคำถามได้ในขณะนี้

❌ **ข้อผิดพลาด:** {error}

💡 **ข้อเสนอแนะ:**
• ลองถามคำถามที่ง่ายกว่า เช่น "สวัสดีครับ" หรือ "มีข้อมูลอะไรบ้าง"
• ตรวจสอบการสะกดคำและไวยากรณ์
• ลองใหม่อีกครั้งในอีกสักครู่

🚀 ระบบจะพร้อมให้บริการอีกครั้งเร็วๆ นี้"""
            else:
                answer = f"""Sorry, the system cannot process the question at this time

❌ **Error:** {error}

💡 **Suggestions:**
• Try asking simpler questions like "Hello" or "What data is available"
• Check spelling and grammar
• Try again in a moment

🚀 The system will be ready to serve again soon"""
            
            return {
                "answer": answer,
                "success": False,
                "data_source_used": "universal_error_fallback",
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "error": error,
                "fallback_mode": True,
                "enhancement_version": "3.0_universal"
            }

    # 🔄 Keep existing methods but add universal support
    async def generate_enhanced_sql(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """Enhanced SQL generation with business intelligence and pattern matching"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.database_schemas[tenant_id]
        business_logic = self.business_logic_mappings.get(tenant_id, {})
        
        # Check for pre-defined patterns first
        query_analysis = self._analyze_question_intent(question, tenant_id)
        
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
                temperature=0.1
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

    def _process_decimal_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """🔧 Convert Decimal objects to float for JSON serialization"""
        processed_data = []
        
        for row in data:
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, Decimal):
                    processed_row[key] = float(value)
                else:
                    processed_row[key] = value
            processed_data.append(processed_row)
        
        return processed_data

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
            
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
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
                        logger.error(f"Enhanced Ollama API error: {response.status}")
                        return f"เกิดข้อผิดพลาดในการเรียก AI (HTTP {response.status})"
                        
        except asyncio.TimeoutError:
            logger.error("Enhanced Ollama API timeout")
            return "AI ใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Enhanced Ollama API call failed: {e}")
            return f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"


if __name__ == "__main__":
    print("🌟 Universal Enhanced PostgreSQL Ollama Agent v3.0")
    print("🔧 Features: Universal Intent Classification, Advanced prompts, Business intelligence")
    print("🎯 Multi-tenant support with intelligent question routing")