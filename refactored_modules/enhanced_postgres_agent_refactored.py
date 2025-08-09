# 🎯 Simple Enhanced PostgreSQL Agent - เวอร์ชั่นเรียบง่าย
# refactored_modules/simple_enhanced_postgres_agent.py

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from decimal import Decimal

# Import essential modules only
from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleEnhancedPostgresAgent:
    """🎯 Simple Enhanced PostgreSQL Agent - เฉพาะที่จำเป็น"""
    
    def __init__(self):
        """🏗️ Initialize เฉพาะที่จำเป็น"""
        self.config_manager = TenantConfigManager()
        self.tenant_configs = self.config_manager.tenant_configs
        self.database_handler = DatabaseHandler(self.tenant_configs)
        self.ai_service = AIService()
        
        logger.info("✅ Simple Enhanced PostgreSQL Agent initialized")
    
    # ========================================================================
    # 🎯 CORE METHODS (เฉพาะ 8 ตัวที่จำเป็น)
    # ========================================================================
    
    async def process_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 1. Main processing method - เรียบง่าย"""
        
        if tenant_id not in self.tenant_configs:
            return self._create_error_response("ไม่รู้จัก tenant", tenant_id)
        
        start_time = datetime.now()
        config = self._get_config(tenant_id)
        
        try:
            # Simple logic: check if question needs SQL
            if self._needs_sql(question):
                return await self._process_sql_question(question, tenant_id, config, start_time)
            else:
                return self._process_conversational_question(question, tenant_id, config)
                
        except Exception as e:
            logger.error(f"❌ Processing failed for {tenant_id}: {e}")
            return self._create_error_response(str(e), tenant_id)
    
    async def _process_sql_question(self, question: str, tenant_id: str, config: TenantConfig, start_time: datetime) -> Dict[str, Any]:
        """🎯 2. Process questions that need SQL"""
        
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
                    "data_source_used": f"simple_sql_{config.model_name}",
                    "sql_query": sql_query,
                    "db_results_count": len(results) if results else 0,
                    "tenant_id": tenant_id,
                    "processing_time_seconds": processing_time,
                    "system_type": "simple_enhanced_agent"
                }
            else:
                return self._create_fallback_response(question, tenant_id, "SQL ไม่ปลอดภัย")
                
        except Exception as e:
            return self._create_fallback_response(question, tenant_id, str(e))
    
    async def _generate_sql(self, question: str, tenant_id: str) -> str:
        """🎯 3. Simple SQL generation"""
        
        config = self._get_config(tenant_id)
        
        # Simple prompt template
        prompt = f"""คุณคือ PostgreSQL Expert สำหรับ {config.name}

โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack  
• employee_projects: employee_id, project_id, role, allocation

กฎ SQL:
1. ใช้ COALESCE สำหรับ NULL: COALESCE(p.name, 'ไม่มีโปรเจค')
2. แสดงเงิน: TO_CHAR(salary, 'FM999,999,999') || ' บาท'
3. ใช้ LEFT JOIN สำหรับ assignment
4. LIMIT 20 เสมอ

คำถาม: {question}

สร้าง PostgreSQL query เดียว:"""
        
        try:
            ai_response = await self.ai_service.call_ollama_api(
                config, prompt, temperature=0.1
            )
            
            # Extract SQL from response
            sql_query = self._extract_sql(ai_response)
            return sql_query
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return "SELECT 'SQL generation failed' as error"
    
    async def _execute_sql(self, sql_query: str, tenant_id: str) -> List[Dict[str, Any]]:
        """🎯 4. Simple SQL execution"""
        
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
        """🎯 5. Simple response formatting"""
        
        config = self._get_config(tenant_id)
        
        if not results:
            return f"ไม่พบข้อมูลที่ตรงกับคำถาม: {question}"
        
        # Simple formatting
        if config.language == 'th':
            response = f"📊 ผลการค้นหาสำหรับ {config.name}\n\n"
            response += f"คำถาม: {question}\n\n"
        else:
            response = f"📊 Search Results for {config.name}\n\n"
            response += f"Query: {question}\n\n"
        
        # Display results (simple table format)
        for i, row in enumerate(results[:15], 1):
            response += f"{i:2d}. "
            for key, value in row.items():
                if 'salary' in key.lower() or 'budget' in key.lower():
                    response += f"{key}: {value:,.0f} บาท, "
                else:
                    response += f"{key}: {value}, "
            response = response.rstrip(', ') + "\n"
        
        response += f"\n💡 พบข้อมูล {len(results)} รายการ"
        
        return response
    
    def _create_fallback_response(self, question: str, tenant_id: str, error_reason: str) -> Dict[str, Any]:
        """🎯 6. Simple fallback response"""
        
        config = self._get_config(tenant_id)
        
        # Simple fallback based on business type
        if config.business_type == 'tourism_hospitality':
            fallback_answer = f"""🏨 {config.name} - ระบบท่องเที่ยวและโรงแรม

คำถาม: {question}

เราเป็นผู้เชี่ยวชาญด้านเทคโนโลยีท่องเที่ยวในภาคเหนือ มีโปรเจคที่เกี่ยวข้องกับ:
• ระบบจองโรงแรม
• แอปพลิเคชันท่องเที่ยว  
• ระบบจัดการทัวร์
• เทคโนโลยีสำหรับธุรกิจบริการ

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น"""

        elif config.business_type == 'enterprise':
            fallback_answer = f"""🏦 {config.name} - ระบบองค์กรและธนาคาร

คำถาม: {question}

เราเป็นผู้เชี่ยวชาญด้านระบบองค์กรขนาดใหญ่ มีโปรเจคที่เกี่ยวข้องกับ:
• ระบบธนาคารและการเงิน
• E-commerce และ CRM
• ระบบ AI และ Chatbot
• Mobile Banking

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น"""

        else:
            fallback_answer = f"""🌍 {config.name} - ระบบซอฟต์แวร์นานาชาติ

คำถาม: {question}

เราเป็นผู้เชี่ยวชาญด้านระบบซอฟต์แวร์ระหว่างประเทศ มีโปรเจคที่เกี่ยวข้องกับ:
• Global platforms
• Multi-currency systems
• Cross-border solutions
• International compliance

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น"""
        
        return {
            "answer": fallback_answer,
            "success": True,
            "data_source_used": f"simple_fallback_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "simple_fallback",
            "fallback_reason": error_reason
        }
    
    def _is_valid_sql(self, sql: str) -> bool:
        """🎯 7. Simple SQL validation"""
        
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
        """🎯 8. Get tenant configuration"""
        return self.tenant_configs[tenant_id]
    
    # ========================================================================
    # 🔧 SIMPLE HELPER METHODS (ไม่นับเป็น core methods)
    # ========================================================================
    
    def _needs_sql(self, question: str) -> bool:
        """Check if question needs SQL query"""
        sql_keywords = [
            'พนักงาน', 'employee', 'โปรเจค', 'project', 'กี่คน', 'จำนวน', 
            'เท่าไร', 'มีอะไร', 'ธนาคาร', 'งบประมาณ', 'budget', 'salary',
            'เงินเดือน', 'แผนก', 'department', 'ลูกค้า', 'client'
        ]
        return any(keyword in question.lower() for keyword in sql_keywords)
    
    def _extract_sql(self, ai_response: str) -> str:
        """Extract SQL from AI response"""
        
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
                # Remove trailing semicolon if present
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
        """Process conversational questions"""
        
        greetings = ['สวัสดี', 'hello', 'hi', 'ช่วย', 'help', 'คุณคือใคร']
        if any(word in question.lower() for word in greetings):
            
            if config.language == 'th':
                answer = f"""สวัสดีครับ! ผมคือ AI Assistant สำหรับ {config.name}

✨ ความสามารถของผม:
• วิเคราะห์ข้อมูลพนักงานและโปรเจค
• ตอบคำถามเกี่ยวกับธุรกิจ
• สร้างรายงานและสถิติ

🎯 ตัวอย่างคำถาม:
• "มีพนักงานกี่คนในแต่ละแผนก"
• "โปรเจคไหนมีงบประมาณสูงสุด"
• "พนักงานคนไหนทำงานหลายโปรเจค"

มีอะไรให้ผมช่วยไหมครับ?"""
            else:
                answer = f"""Hello! I'm the AI Assistant for {config.name}

✨ My capabilities:
• Analyze employee and project data
• Answer business questions
• Generate reports and statistics

🎯 Example questions:
• "How many employees in each department"
• "Which projects have highest budget"
• "Which employees work on multiple projects"

How can I help you?"""
        else:
            answer = self._create_fallback_response(question, tenant_id, "conversational")["answer"]
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": f"simple_conversational_{config.model_name}",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "simple_conversational"
        }
    
    def _create_error_response(self, error_message: str, tenant_id: str) -> Dict[str, Any]:
        """Create error response"""
        
        return {
            "answer": f"เกิดข้อผิดพลาด: {error_message}",
            "success": False,
            "data_source_used": "simple_error",
            "sql_query": None,
            "tenant_id": tenant_id,
            "system_type": "simple_error",
            "error": error_message
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (เพื่อความเข้ากันได้กับระบบเดิม)
    # ========================================================================
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Compatibility method for existing code"""
        return await self.process_question(question, tenant_id)
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Simple streaming implementation"""
        
        yield {
            "type": "status", 
            "message": "🎯 กำลังประมวลผลคำถาม...",
            "step": "processing"
        }
        
        # Process question
        result = await self.process_question(question, tenant_id)
        
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
            "tenant_id": tenant_id
        }