# refactored_modules/enhanced_postgres_agent_refactored.py
# 🎯 Enhanced PostgreSQL Agent - แทนที่ IntentClassifier ด้วย Simple Logic

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from decimal import Decimal

# Import essential modules only (ลบ IntentClassifier)
from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPostgresOllamaAgent:
    """🎯 Enhanced PostgreSQL Agent - Simple Intent Logic (ไม่ใช้ IntentClassifier)"""
    
    def __init__(self):
        """🏗️ Initialize without IntentClassifier"""
        self.config_manager = TenantConfigManager()
        self.tenant_configs = self.config_manager.tenant_configs
        self.database_handler = DatabaseHandler(self.tenant_configs)
        self.ai_service = AIService()
        
        # ❌ ลบบรรทัดนี้: self.intent_classifier = IntentClassifier()
        
        logger.info("✅ Enhanced PostgreSQL Agent initialized (Simple Intent Logic)")
    
    # ========================================================================
    # 🎯 CORE METHODS - แทนที่ IntentClassifier ด้วย Simple Logic
    # ========================================================================
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main processing method - ใช้ Simple Intent Logic"""
        
        if tenant_id not in self.tenant_configs:
            return self._create_error_response("ไม่รู้จัก tenant", tenant_id)
        
        start_time = datetime.now()
        config = self._get_config(tenant_id)
        
        try:
            # ✅ แทนที่ IntentClassifier ด้วย Simple Logic
            if self._needs_sql(question):
                return await self._process_sql_question(question, tenant_id, config, start_time)
            else:
                return self._process_conversational_question(question, tenant_id, config)
                
        except Exception as e:
            logger.error(f"❌ Processing failed for {tenant_id}: {e}")
            return self._create_error_response(str(e), tenant_id)
    
    def _needs_sql(self, question: str) -> bool:
        """🎯 Simple Intent Logic - แทนที่ IntentClassifier (400+ บรรทัด → 5 บรรทัด)"""
        sql_keywords = [
            # Thai keywords
            'พนักงาน', 'โปรเจค', 'กี่คน', 'จำนวน', 'เท่าไร', 'มีอะไร', 
            'งบประมาณ', 'เงินเดือน', 'แผนก', 'ลูกค้า', 'บริษัท',
            'ใคร', 'ไหน', 'เมื่อไร', 'ทำงาน', 'รับผิดชอบ',
            
            # English keywords  
            'employee', 'project', 'how many', 'budget', 'salary', 
            'department', 'client', 'company', 'who', 'what', 'when',
            'work', 'assign', 'responsible',
            
            # Business keywords
            'ธนาคาร', 'banking', 'ท่องเที่ยว', 'tourism', 'โรงแรม', 'hotel',
            'ระบบ', 'system', 'แอป', 'app', 'เว็บ', 'website'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in sql_keywords)
    
    async def _process_sql_question(self, question: str, tenant_id: str, config: TenantConfig, start_time: datetime) -> Dict[str, Any]:
        """🎯 Process questions that need SQL"""
        
        try:
            # Generate SQL
            sql_query = await self._generate_sql(question, tenant_id)
            
            # Execute SQL
            if self._is_valid_sql(sql_query):
                results = await self._execute_sql(sql_query, tenant_id)
                
                # Format response
                formatted_answer = self._format_response(results, question, tenant_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "answer": formatted_answer,
                    "success": True,
                    "data_source_used": f"enhanced_sql_{config.model_name}",
                    "sql_query": sql_query,
                    "db_results_count": len(results) if results else 0,
                    "tenant_id": tenant_id,
                    "processing_time_seconds": processing_time,
                    "system_type": "enhanced_agent_simple_intent",
                    "intent_method": "simple_keyword_matching"  # แทนที่ complex classification
                }
            else:
                return self._create_fallback_response(question, tenant_id, "SQL ไม่ปลอดภัย")
                
        except Exception as e:
            return self._create_fallback_response(question, tenant_id, str(e))
    
    async def _generate_sql(self, question: str, tenant_id: str) -> str:
        """🎯 SQL generation with business context"""
        
        config = self._get_config(tenant_id)
        
        # Enhanced prompt based on business type
        business_context = self._get_business_context(tenant_id)
        
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
            logger.error(f"SQL generation failed: {e}")
            return "SELECT 'SQL generation failed' as error"
    
    def _get_business_context(self, tenant_id: str) -> str:
        """🏢 Get business context for each company"""
        
        business_contexts = {
            'company-a': """🏢 บริบท: สำนักงานใหญ่ กรุงเทพมฯ - Enterprise Banking & E-commerce
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบธนาคาร, E-commerce, โปรเจคขนาดใหญ่ (1M-3M บาท)
🏦 ลูกค้าหลัก: ธนาคารกรุงเทพ, ธนาคารไทยพาณิชย์, Central Group""",

            'company-b': """🏨 บริบท: สาขาภาคเหนือ เชียงใหม่ - Tourism & Hospitality  
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: ระบบท่องเที่ยว, โรงแรม, โปรเจคระดับภูมิภาค (300k-800k บาท)
🌿 ลูกค้าหลัก: โรงแรมดุสิต, TAT, สวนพฤกษศาสตร์, ร้านอาหารล้านนา""",

            'company-c': """🌍 บริบท: International Office - Global Operations
💰 สกุลเงิน: USD และ Multi-currency
🎯 เน้น: ระบบข้ามประเทศ, Global platforms (1M-4M USD)
🌎 ลูกค้าหลัก: MegaCorp International, Global Finance Corp, Education Global"""
        }
        
        return business_contexts.get(tenant_id, business_contexts['company-a'])
    
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
    
    def _format_response(self, results: List[Dict], question: str, tenant_id: str) -> str:
        """🎨 Enhanced response formatting based on business context"""
        
        config = self._get_config(tenant_id)
        
        if not results:
            return f"ไม่พบข้อมูลที่ตรงกับคำถาม: {question}"
        
        # Business-specific formatting
        business_emoji = self._get_business_emoji(tenant_id)
        currency = "USD" if tenant_id == 'company-c' else "บาท"
        
        if config.language == 'th':
            response = f"{business_emoji} ผลการค้นหาสำหรับ {config.name}\n\n"
            response += f"คำถาม: {question}\n\n"
        else:
            response = f"{business_emoji} Search Results for {config.name}\n\n"
            response += f"Query: {question}\n\n"
        
        # Display results with business context
        for i, row in enumerate(results[:15], 1):
            response += f"{i:2d}. "
            for key, value in row.items():
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    response += f"{key}: {value:,.0f} {currency}, "
                elif key == 'allocation' and isinstance(value, float):
                    response += f"{key}: {value*100:.1f}%, "
                else:
                    response += f"{key}: {value}, "
            response = response.rstrip(', ') + "\n"
        
        # Add business insights
        insights = self._generate_business_insights(results, tenant_id)
        response += f"\n💡 {insights}"
        
        return response
    
    def _get_business_emoji(self, tenant_id: str) -> str:
        """🎯 Get business emoji for each company"""
        emojis = {
            'company-a': '🏦',  # Banking
            'company-b': '🏨',  # Tourism  
            'company-c': '🌍'   # International
        }
        return emojis.get(tenant_id, '💼')
    
    def _generate_business_insights(self, results: List[Dict], tenant_id: str) -> str:
        """💡 Generate business insights based on data"""
        
        if not results:
            return "ไม่มีข้อมูลสำหรับวิเคราะห์"
        
        insights = []
        
        # Count and analyze
        total_count = len(results)
        insights.append(f"พบข้อมูล {total_count} รายการ")
        
        # Analyze salary/budget if present
        financial_values = []
        for row in results:
            for key, value in row.items():
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    financial_values.append(value)
        
        if financial_values:
            avg_value = sum(financial_values) / len(financial_values)
            max_value = max(financial_values)
            currency = "USD" if tenant_id == 'company-c' else "บาท"
            insights.append(f"เฉลี่ย: {avg_value:,.0f} {currency}, สูงสุด: {max_value:,.0f} {currency}")
        
        # Business-specific insights
        business_insights = {
            'company-a': "ระดับ Enterprise - โปรเจคขนาดใหญ่",
            'company-b': "ระดับภูมิภาค - เน้นท่องเที่ยวและวัฒนธรรม", 
            'company-c': "ระดับนานาชาติ - Global operations"
        }
        
        insights.append(business_insights.get(tenant_id, "ข้อมูลธุรกิจ"))
        
        return " | ".join(insights)
    
    def _create_fallback_response(self, question: str, tenant_id: str, error_reason: str) -> Dict[str, Any]:
        """🔄 Business-specific fallback response"""
        
        config = self._get_config(tenant_id)
        business_emoji = self._get_business_emoji(tenant_id)
        
        fallback_responses = {
            'company-a': f"""{business_emoji} {config.name} - ระบบธนาคารและองค์กร

คำถาม: {question}

เราเชี่ยวชาญด้าน:
• ระบบธนาคารและการเงิน (CRM, Mobile Banking)
• E-commerce และ AI Chatbot
• ระบบองค์กรขนาดใหญ่
• โปรเจคงบประมาณหลายล้านบาท

💡 ลองถามเกี่ยวกับ: พนักงาน, โปรเจคธนาคาร, งบประมาณ""",

            'company-b': f"""{business_emoji} {config.name} - ระบบท่องเที่ยวและโรงแรม

คำถาม: {question}

เราเชี่ยวชาญด้าน:
• ระบบโรงแรมและการจอง
• แอปพลิเคชันท่องเที่ยว
• ระบบร้านอาหารและ POS
• เทคโนโลยีสำหรับวัฒนธรรมล้านนา

💡 ลองถามเกี่ยวกับ: โปรเจคท่องเที่ยว, ลูกค้าโรงแรม, ระบบภาคเหนือ""",

            'company-c': f"""{business_emoji} {config.name} - International Operations

Question: {question}

We specialize in:
• Global software platforms
• Multi-currency systems  
• Cross-border solutions
• International compliance

💡 Try asking about: international projects, USD budgets, global clients"""
        }
        
        answer = fallback_responses.get(tenant_id, fallback_responses['company-a'])
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": f"enhanced_fallback_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "enhanced_fallback_simple_intent",
            "fallback_reason": error_reason,
            "intent_method": "simple_keyword_matching"
        }
    
    def _is_valid_sql(self, sql: str) -> bool:
        """🔒 SQL validation for security"""
        
        if not sql or not sql.strip():
            return False
        
        sql_upper = sql.upper()
        
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"🚨 Dangerous SQL keyword detected: {keyword}")
                return False
        
        # Must be a SELECT statement
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        return True
    
    def _get_config(self, tenant_id: str) -> TenantConfig:
        """📝 Get tenant configuration"""
        return self.tenant_configs[tenant_id]
    
    def _extract_sql(self, ai_response: str) -> str:
        """🔍 Extract SQL from AI response"""
        
        # Look for SQL in code blocks
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
        
        # If no pattern found, look for SELECT statement
        lines = ai_response.split('\n')
        for line in lines:
            if line.strip().upper().startswith('SELECT'):
                return line.strip()
        
        return "SELECT 'No valid SQL found' as message"
    
    def _process_conversational_question(self, question: str, tenant_id: str, config: TenantConfig) -> Dict[str, Any]:
        """💬 Process conversational questions"""
        
        business_emoji = self._get_business_emoji(tenant_id)
        
        greetings = ['สวัสดี', 'hello', 'hi', 'ช่วย', 'help', 'คุณคือใคร']
        if any(word in question.lower() for word in greetings):
            
            greeting_responses = {
                'company-a': f"""สวัสดีครับ! ผมคือ AI Assistant สำหรับ {config.name}

{business_emoji} ความสามารถของผม:
• วิเคราะห์ข้อมูลระบบธนาคารและองค์กร
• ตอบคำถามเกี่ยวกับโปรเจค E-commerce  
• สร้างรายงานและสถิติธุรกิจ
• ข้อมูลพนักงานและงบประมาณ

🎯 ตัวอย่างคำถาม:
• "มีพนักงานกี่คนในแต่ละแผนก"
• "โปรเจคธนาคารมีงบประมาณเท่าไร"
• "ใครทำงานโปรเจค CRM"

มีอะไรให้ผมช่วยไหมครับ?""",

                'company-b': f"""สวัสดีเจ้า! ผมคือ AI Assistant สำหรับ {config.name}

{business_emoji} ความสามารถของผม:
• วิเคราะห์ข้อมูลระบบท่องเที่ยวและโรงแรม
• ตอบคำถามเกี่ยวกับโปรเจคภาคเหนือ
• ข้อมูลวัฒนธรรมล้านนาและการต้อนรับ
• สถิติธุรกิจท่องเที่ยว

🎯 ตัวอย่างคำถาม:
• "มีโปรเจคท่องเที่ยวอะไรบ้าง"
• "ลูกค้าโรงแรมในเชียงใหม่"
• "ระบบร้านอาหารล้านนา"

น้ำใจเหนือ - มีอะไรให้ช่วยไหมครับ?""",

                'company-c': f"""Hello! I'm the AI Assistant for {config.name}

{business_emoji} My capabilities:
• Analyze international software projects
• Answer questions about global operations
• Multi-currency financial analysis
• Cross-border business intelligence

🎯 Example questions:
• "Which international projects exist"
• "What's the USD budget breakdown"
• "How many global clients do we have"

How can I help you today?"""
            }
            
            answer = greeting_responses.get(tenant_id, greeting_responses['company-a'])
        else:
            answer = self._create_fallback_response(question, tenant_id, "conversational")["answer"]
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": f"enhanced_conversational_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "enhanced_conversational_simple_intent",
            "intent_method": "simple_keyword_matching"
        }
    
    def _create_error_response(self, error_message: str, tenant_id: str) -> Dict[str, Any]:
        """❌ Create error response"""
        
        return {
            "answer": f"เกิดข้อผิดพลาด: {error_message}",
            "success": False,
            "data_source_used": "enhanced_error",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "enhanced_error",
            "error": error_message,
            "intent_method": "simple_keyword_matching"
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (เพื่อความเข้ากันได้กับระบบเดิม)
    # ========================================================================
    
    async def process_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Compatibility method"""
        return await self.process_enhanced_question(question, tenant_id)
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Simple streaming implementation"""
        
        yield {
            "type": "status", 
            "message": "🎯 กำลังประมวลผลคำถาม (Simple Intent Logic)...",
            "step": "processing"
        }
        
        # Process question
        result = await self.process_enhanced_question(question, tenant_id)
        
        # Yield result in chunks
        answer = result["answer"]
        chunk_size = 100
        
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i+chunk_size]
            yield {
                "type": "answer_chunk",
                "content": chunk
            }
            
        yield {
            "type": "answer_complete",
            "sql_query": result.get("sql_query"),
            "db_results_count": result.get("db_results_count", 0),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
            "tenant_id": tenant_id,
            "intent_method": "simple_keyword_matching"
        }