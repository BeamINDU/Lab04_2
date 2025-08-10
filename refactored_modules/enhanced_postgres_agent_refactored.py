# refactored_modules/enhanced_postgres_agent_refactored.py
# 🔄 REFACTORED: Now uses PromptManager for scalability

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
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

class EnhancedPostgresOllamaAgent:
    """🎯 Enhanced PostgreSQL Agent - Now uses PromptManager for scalability"""
    
    def __init__(self):
        """🏗️ Initialize with PromptManager support"""
        self.config_manager = TenantConfigManager()
        self.tenant_configs = self.config_manager.tenant_configs
        self.database_handler = DatabaseHandler(self.tenant_configs)
        self.ai_service = AIService()
        
        # 🆕 Initialize PromptManager
        self.prompt_manager = None
        self.use_prompt_manager = False
        self._init_prompt_manager()
        
        logger.info(f"✅ Enhanced PostgreSQL Agent initialized")
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
                # Convert TenantConfig to dict format expected by PromptManager
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
                logger.info(f"🏢 Supported companies: {self.supported_companies}")
            else:
                logger.warning("⚠️ PromptManager: No company prompts loaded")
                
        except Exception as e:
            logger.error(f"❌ PromptManager initialization failed: {e}")
            logger.info("🔄 Will use fallback prompt system")
    
    # ========================================================================
    # 🎯 MAIN PROCESSING METHOD - Routes to PromptManager or Fallback
    # ========================================================================
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main processing method - Routes to appropriate system"""
        
        if tenant_id not in self.tenant_configs:
            return self._create_error_response("Unknown tenant", tenant_id)
        
        start_time = datetime.now()
        
        try:
            # 🆕 Try PromptManager first (if available and supported)
            if self.use_prompt_manager and tenant_id in self.supported_companies:
                logger.info(f"🎯 Using PromptManager for {tenant_id}")
                return await self._process_with_prompt_manager(question, tenant_id, start_time)
            else:
                logger.info(f"🔄 Using fallback system for {tenant_id}")
                return await self._process_with_fallback(question, tenant_id, start_time)
                
        except Exception as e:
            logger.error(f"❌ Processing failed for {tenant_id}: {e}")
            return self._create_error_response(str(e), tenant_id)
    
    async def _process_with_prompt_manager(self, question: str, tenant_id: str, start_time: datetime) -> Dict[str, Any]:
        """🎯 Hybrid: SQL from Enhanced Agent, Conversation from PromptManager"""
        
        try:
            # 🔧 Check if question needs SQL generation
            if self._needs_sql(question):
                logger.info(f"🎯 SQL query detected for {tenant_id}, using Enhanced Agent")
                # Use Enhanced Agent's SQL generation
                result = await self._process_sql_question_fallback(question, tenant_id, self._get_config(tenant_id), start_time)
                result.update({
                    'system_used': 'enhanced_agent_sql',
                    'company_prompt_active': False,
                    'sql_source': 'enhanced_agent'
                })
                return result
            else:
                logger.info(f"🎯 Conversational query, using PromptManager for {tenant_id}")
                # Use PromptManager for greetings and conversational
                result = await self.prompt_manager.process_query(question, tenant_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                result.update({
                    'processing_time_seconds': processing_time,
                    'system_used': 'prompt_manager',
                    'company_prompt_active': True,
                    'sql_generation': False
                })
                return result
                
        except Exception as e:
            logger.error(f"❌ Hybrid processing failed for {tenant_id}: {e}")
            return await self._process_with_fallback(question, tenant_id, start_time)
    
    async def _process_with_fallback(self, question: str, tenant_id: str, start_time: datetime) -> Dict[str, Any]:
        """🔄 Fallback processing using built-in prompts"""
        
        config = self._get_config(tenant_id)
        
        try:
            # Simple intent detection
            if self._needs_sql(question):
                return await self._process_sql_question_fallback(question, tenant_id, config, start_time)
            else:
                return self._process_conversational_question_fallback(question, tenant_id, config)
                
        except Exception as e:
            return self._create_fallback_response(question, tenant_id, str(e))
    
    async def _process_sql_question_fallback(self, question: str, tenant_id: str, config: TenantConfig, start_time: datetime) -> Dict[str, Any]:
        """🎯 Process SQL questions using fallback system"""
        
        try:
            # Generate SQL using built-in prompts
            sql_query = await self._generate_sql_fallback(question, tenant_id)
            
            # Execute SQL
            if self._is_valid_sql(sql_query):
                results = await self._execute_sql(sql_query, tenant_id)
                formatted_answer = self._format_response_fallback(results, question, tenant_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "answer": formatted_answer,
                    "success": True,
                    "data_source_used": f"fallback_sql_{config.model_name}",
                    "sql_query": sql_query,
                    "db_results_count": len(results) if results else 0,
                    "tenant_id": tenant_id,
                    "processing_time_seconds": processing_time,
                    "system_used": "fallback_built_in",
                    "company_prompt_active": False,
                    "agent_version": "enhanced_v2.0_fallback"
                }
            else:
                return self._create_fallback_response(question, tenant_id, "Invalid SQL generated")
                
        except Exception as e:
            return self._create_fallback_response(question, tenant_id, str(e))
    
    # ========================================================================
    # 🔧 FALLBACK PROMPT SYSTEM (for companies not supported by PromptManager)
    # ========================================================================
    
    async def _generate_sql_fallback(self, question: str, tenant_id: str) -> str:
        """🔄 Fallback SQL generation"""
        
        config = self._get_config(tenant_id)
        business_context = self._get_business_context_fallback(tenant_id)
        
        prompt = f"""คุณคือ PostgreSQL Expert สำหรับ {config.name}

{business_context}

โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack  
• employee_projects: employee_id, project_id, role, allocation

กฎ SQL สำคัญ:
1. ใช้ COALESCE สำหรับ NULL: COALESCE(p.name, 'ไม่มีโปรเจค')
2. แสดงเงิน: TO_CHAR(salary, 'FM999,999,999') || ' บาท'
3. ใช้ LEFT JOIN สำหรับ assignment analysis
4. ใช้ ILIKE สำหรับ text search
5. LIMIT 20 เสมอ

คำถาม: {question}

สร้าง PostgreSQL query เดียว:"""
        
        try:
            ai_response = await self.ai_service.call_ollama_api(
                config, prompt, temperature=0.1
            )
            sql_query = self._extract_sql(ai_response)
            return sql_query
            
        except Exception as e:
            logger.error(f"Fallback SQL generation failed: {e}")
            return "SELECT 'Fallback SQL generation failed' as error"
    
    def _get_business_context_fallback(self, tenant_id: str) -> str:
        """🏢 Fallback business context (สำหรับ companies ที่ PromptManager ไม่รองรับ)"""
        
        fallback_contexts = {
            'company-a': """🏢 บริบท: สำนักงานใหญ่ กรุงเทพมฯ - Enterprise Banking & E-commerce
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบธนาคาร, E-commerce, โปรเจคขนาดใหญ่ (1M-3M บาท)""",

            'company-b': """🏨 บริบท: สาขาภาคเหนือ เชียงใหม่ - Tourism & Hospitality  
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบท่องเที่ยว, โรงแรม, โปรเจคระดับภูมิภาค (300k-800k บาท)""",

            'company-c': """🌍 บริบท: International Office - Global Operations
💰 สกุลเงิน: USD และ Multi-currency
🎯 เน้น: ระบบข้ามประเทศ, Global platforms (1M-4M USD)"""
        }
        
        return fallback_contexts.get(tenant_id, fallback_contexts['company-a'])
    
    def _format_response_fallback(self, results: List[Dict], question: str, tenant_id: str) -> str:
        """🎨 Fallback response formatting"""
        
        config = self._get_config(tenant_id)
        
        if not results:
            return f"ไม่พบข้อมูลที่ตรงกับคำถาม: {question}"
        
        business_emoji = self._get_business_emoji(tenant_id)
        currency = "USD" if tenant_id == 'company-c' else "บาท"
        
        response = f"{business_emoji} ผลการค้นหา (Fallback System)\n\n"
        response += f"คำถาม: {question}\n\n"
        
        for i, row in enumerate(results[:10], 1):
            response += f"{i:2d}. "
            for key, value in row.items():
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    response += f"{key}: {value:,.0f} {currency}, "
                else:
                    response += f"{key}: {value}, "
            response = response.rstrip(', ') + "\n"
        
        response += f"\n💡 ระบบ Fallback | พบข้อมูล {len(results)} รายการ"
        
        return response
    
    def _process_conversational_question_fallback(self, question: str, tenant_id: str, config: TenantConfig) -> Dict[str, Any]:
        """💬 Fallback conversational responses"""
        
        business_emoji = self._get_business_emoji(tenant_id)
        
        if self._is_greeting(question):
            fallback_greetings = {
                'company-a': f"""สวัสดีครับ! ผมคือ AI Assistant สำหรับ {config.name} (Fallback System)

{business_emoji} ระบบธนาคารและองค์กร - พร้อมให้บริการ
💡 ตัวอย่างคำถาม: "มีพนักงานกี่คนในแต่ละแผนก", "โปรเจคธนาคารมีงบประมาณเท่าไร" """,

                'company-b': f"""สวัสดีเจ้า! ผมคือ AI Assistant สำหรับ {config.name} (Fallback System)

{business_emoji} ระบบท่องเที่ยวและโรงแรม - พร้อมให้บริการ
💡 ตัวอย่างคำถาม: "มีโปรเจคท่องเที่ยวอะไรบ้าง", "ลูกค้าโรงแรมในเชียงใหม่" """,

                'company-c': f"""Hello! I'm the AI Assistant for {config.name} (Fallback System)

{business_emoji} International Operations - Ready to help
💡 Example questions: "Which international projects exist?", "What's the USD budget breakdown?" """
            }
            
            answer = fallback_greetings.get(tenant_id, fallback_greetings['company-a'])
        else:
            answer = f"{business_emoji} Fallback System สำหรับ {config.name}\n\nคำถาม: {question}\n\nกรุณาลองถามคำถามที่เฉพาะเจาะจงมากขึ้น"
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": f"fallback_conversational_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_used": "fallback_conversational",
            "company_prompt_active": False
        }
    
    # ========================================================================
    # 🔧 UTILITY METHODS (รักษาไว้เหมือนเดิม)
    # ========================================================================
    
    def _needs_sql(self, question: str) -> bool:
        """🎯 Simple Intent Logic"""
        sql_keywords = [
            'พนักงาน', 'โปรเจค', 'กี่คน', 'จำนวน', 'เท่าไร', 'มีอะไร', 
            'งบประมาณ', 'เงินเดือน', 'แผนก', 'ลูกค้า', 'บริษัท',
            'employee', 'project', 'how many', 'budget', 'salary', 
            'department', 'client', 'company'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in sql_keywords)
    
    def _is_greeting(self, question: str) -> bool:
        """Check if greeting"""
        greetings = ['สวัสดี', 'hello', 'hi', 'ช่วย', 'help', 'คุณคือใคร']
        return any(word in question.lower() for word in greetings)
    
    async def _execute_sql(self, sql_query: str, tenant_id: str) -> List[Dict[str, Any]]:
        """🎯 SQL execution with Decimal handling"""
        try:
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
            
            return processed_results
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return []
    
    def _is_valid_sql(self, sql: str) -> bool:
        """🔒 SQL validation for security"""
        if not sql or not sql.strip():
            return False
        
        sql_upper = sql.upper()
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"🚨 Dangerous SQL keyword detected: {keyword}")
                return False
        
        return sql_upper.strip().startswith('SELECT')
    
    def _get_config(self, tenant_id: str) -> TenantConfig:
        """📝 Get tenant configuration"""
        return self.tenant_configs[tenant_id]
    
    def _extract_sql(self, ai_response: str) -> str:
        """🔍 Extract SQL from AI response"""
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?)\s*```',
            r'(SELECT.*?);?\s*$'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if sql.endswith(';'):
                    sql = sql[:-1]
                return sql
        
        return "SELECT 'No valid SQL found' as message"
    
    def _get_business_emoji(self, tenant_id: str) -> str:
        """🎯 Get business emoji for each company"""
        emojis = {
            'company-a': '🏦',  # Banking
            'company-b': '🏨',  # Tourism  
            'company-c': '🌍'   # International
        }
        return emojis.get(tenant_id, '💼')
    
    def _create_fallback_response(self, question: str, tenant_id: str, error_reason: str) -> Dict[str, Any]:
        """🔄 Create fallback response"""
        config = self._get_config(tenant_id)
        business_emoji = self._get_business_emoji(tenant_id)
        
        answer = f"""{business_emoji} {config.name} - Fallback System

คำถาม: {question}

⚠️ ไม่สามารถประมวลผลได้: {error_reason}

กรุณาลองถามคำถามใหม่ หรือติดต่อผู้ดูแลระบบ"""
        
        return {
            "answer": answer,
            "success": False,
            "data_source_used": f"fallback_error_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_used": "fallback_error",
            "error_reason": error_reason,
            "company_prompt_active": False
        }
    
    def _create_error_response(self, error_message: str, tenant_id: str) -> Dict[str, Any]:
        """❌ Create error response"""
        return {
            "answer": f"เกิดข้อผิดพลาด: {error_message}",
            "success": False,
            "data_source_used": "enhanced_error",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_used": "error",
            "error": error_message
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (เพื่อความเข้ากันได้กับระบบเดิม)
    # ========================================================================
    
    async def process_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Compatibility method"""
        return await self.process_enhanced_question(question, tenant_id)
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Simple streaming implementation with PromptManager support"""
        
        if self.use_prompt_manager and tenant_id in self.supported_companies:
            yield {"type": "status", "message": "🎯 Using Company-Specific Prompts...", "system": "prompt_manager"}
        else:
            yield {"type": "status", "message": "🔄 Using Fallback System...", "system": "fallback"}
        
        # Process question
        result = await self.process_enhanced_question(question, tenant_id)
        
        # Yield result in chunks
        answer = result["answer"]
        chunk_size = 100
        
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i+chunk_size]
            yield {"type": "answer_chunk", "content": chunk}
            
        yield {
            "type": "answer_complete",
            "sql_query": result.get("sql_query"),
            "db_results_count": result.get("db_results_count", 0),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
            "tenant_id": tenant_id,
            "system_used": result.get("system_used", "unknown"),
            "company_prompt_active": result.get("company_prompt_active", False)
        }
    
    # ========================================================================
    # 📊 SYSTEM INFORMATION METHODS
    # ========================================================================
    
    def get_system_info(self) -> Dict[str, Any]:
        """📊 Get comprehensive system information"""
        
        info = {
            'agent_version': 'enhanced_v2.0_with_prompt_manager',
            'prompt_manager': {
                'available': PROMPT_MANAGER_AVAILABLE,
                'active': self.use_prompt_manager,
                'supported_companies': getattr(self, 'supported_companies', [])
            },
            'fallback_system': {
                'active': True,
                'coverage': 'all_tenants'
            },
            'tenant_configs': list(self.tenant_configs.keys()),
            'scalability': 'ready_for_new_companies'
        }
        
        if self.prompt_manager:
            try:
                prompt_stats = self.prompt_manager.get_statistics()
                info['prompt_manager']['statistics'] = prompt_stats
            except:
                pass
        
        return info
    
    def add_new_company_support(self, tenant_id: str, config: Dict[str, Any]) -> bool:
        """🆕 Add support for new company (future-ready)"""
        
        try:
            # Add to tenant configs
            from .tenant_config import TenantConfig
            new_config = TenantConfig(**config)
            self.tenant_configs[tenant_id] = new_config
            
            # Refresh PromptManager if available
            if self.use_prompt_manager and hasattr(self.prompt_manager, 'add_company'):
                self.prompt_manager.add_company(tenant_id, config)
                self.supported_companies.append(tenant_id)
            
            logger.info(f"✅ Added support for new company: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add new company {tenant_id}: {e}")
            return False