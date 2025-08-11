# refactored_modules/ai_service.py
# 🤖 Enhanced AI/Ollama Communication Service with Smart Prompt Engineering

import os
import json
import asyncio
import aiohttp
import re
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from .tenant_config import TenantConfig  # ✅ Only import TenantConfig, not AIService

logger = logging.getLogger(__name__)

class EnhancedAIService:
    """🤖 Enhanced AI Service with smart prompt engineering and response optimization"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434')
        self.request_timeout = int(os.getenv('AI_REQUEST_TIMEOUT', '90'))
        self.max_retries = int(os.getenv('AI_MAX_RETRIES', '3'))
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'cache_hits': 0,
            'tenant_breakdown': {}
        }
        
        # Response cache for identical prompts
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Model-specific configurations
        self.model_configs = {
            'llama3.1:8b': {
                'temperature': 0.1,
                'num_predict': 800,
                'top_k': 20,
                'top_p': 0.8,
                'repeat_penalty': 1.0,
                'num_ctx': 2048
            },
            'gemma2:9b': {
                'temperature': 0.2,
                'num_predict': 1000,
                'top_k': 25,
                'top_p': 0.85,
                'repeat_penalty': 1.05,
                'num_ctx': 2048
            },
            'phi3:14b': {
                'temperature': 0.15,
                'num_predict': 1200,
                'top_k': 30,
                'top_p': 0.9,
                'repeat_penalty': 1.02,
                'num_ctx': 4096
            }
        }
        
        logger.info("✅ Enhanced AI Service initialized")
        logger.info(f"🌐 Ollama URL: {self.ollama_base_url}")
        logger.info(f"⏱️ Timeout: {self.request_timeout}s")
    
    # ========================================================================
    # 🎯 ENHANCED PROMPT ENGINEERING
    # ========================================================================
    
    async def generate_enhanced_sql_prompt(self, question: str, tenant_config: TenantConfig, 
                                         schema_info: Dict, intent_result: Dict) -> str:
        """🎯 Generate SIMPLE and WORKING SQL prompt"""
        
        # Get business-specific context
        business_context = self._get_business_context(tenant_config)
        
        prompt = f"""คุณคือ PostgreSQL Expert สำหรับ {tenant_config.name}

{business_context}

📊 โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

📋 ตัวอย่างข้อมูลจริง:
• department: {', '.join(schema_info.get('sample_data', {}).get('employees', {}).get('department', ['IT', 'Sales']))}
• position: {', '.join(schema_info.get('sample_data', {}).get('employees', {}).get('position', ['Developer', 'Designer'])[:5])}

🔧 กฎ SQL สำคัญ (ห้ามผิด):
1. ใช้ ILIKE '%keyword%' สำหรับการค้นหา (ไม่สนใจตัวใหญ่เล็ก)
2. ห้ามใช้ COALESCE ที่ซับซ้อน
3. เขียน SQL ให้เรียบง่าย
4. ใช้ LIMIT 20 เสมอ
5. ใช้ ORDER BY ที่เรียบง่าย

🎯 คำถาม: {question}

📚 ตัวอย่าง SQL ที่ถูกต้อง:

ตัวอย่างที่ 1 - ค้นหาตำแหน่ง:
```sql
SELECT name, position, department 
FROM employees 
WHERE position ILIKE '%frontend%' 
ORDER BY name 
LIMIT 20;
```

ตัวอย่างที่ 2 - นับจำนวนตามแผนก:
```sql
SELECT department, COUNT(*) as employee_count 
FROM employees 
GROUP BY department 
ORDER BY employee_count DESC;
```

ตัวอย่างที่ 3 - แสดงรายชื่อทั้งหมด:
```sql
SELECT name, position, department 
FROM employees 
ORDER BY name 
LIMIT 20;
```

สร้าง PostgreSQL query ที่เรียบง่าย ถูกต้อง และทำงานได้:"""
        
        return prompt
    
    def _get_business_context(self, tenant_config: TenantConfig) -> str:
        """🏢 Get business-specific context for better AI understanding"""
        
        contexts = {
            'enterprise_software': """🏢 บริบทธุรกิจ: Enterprise Software Development
💰 งบประมาณ: 800,000 - 3,000,000+ บาท
🎯 ลูกค้า: ธนาคาร, บริษัทใหญ่, E-commerce
📊 โฟกัส: ระบบธนาคาร, CRM, การจัดการองค์กร""",

            'tourism_hospitality': """🏨 บริบทธุรกิจ: Tourism & Hospitality Technology
💰 งบประมาณ: 300,000 - 800,000 บาท
🎯 ลูกค้า: โรงแรม, รีสอร์ท, หน่วยงานท่องเที่ยว
📊 โฟกัส: ระบบจองห้อง, แอปท่องเที่ยว, ระบบร้านอาหาร""",

            'global_operations': """🌍 บริบทธุรกิจ: Global Software Solutions
💰 งบประมาณ: 1,000,000 - 4,000,000+ USD
🎯 ลูกค้า: บริษัทข้ามชาติ, องค์กรระหว่างประเทศ
📊 โฟกัส: ระบบข้ามประเทศ, Multi-currency, Global compliance"""
        }
        
        return contexts.get(tenant_config.business_type, contexts['enterprise_software'])
    
    def _extract_query_hints(self, question: str, intent_result: Dict, schema_info: Dict) -> str:
        """🔍 Extract specific hints for the query type"""
        
        question_lower = question.lower()
        hints = ["🔧 กฎ SQL เฉพาะสำหรับคำถามนี้:"]
        
        # Position search hints
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            position_keyword = self._extract_keyword(question, ['frontend', 'backend', 'developer', 'designer'])
            hints.extend([
                f"1. ใช้ position ILIKE '%{position_keyword}%' สำหรับค้นหาตำแหน่ง",
                "2. พิจารณาคำที่คล้ายกัน: frontend = front-end = front end",
                "3. จัดเรียงตามความแม่นยำ: exact match ก่อน"
            ])
        
        # Department counting hints
        elif any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many']):
            if 'แผนก' in question_lower:
                hints.extend([
                    "1. ใช้ COUNT(*) กับ GROUP BY department",
                    "2. พิจารณาชื่อแผนกเต็ม: IT = Information Technology",
                    "3. จัดเรียงตามจำนวนคน: ORDER BY COUNT(*) DESC"
                ])
            else:
                hints.extend([
                    "1. ใช้ COUNT(*) สำหรับนับจำนวนรวม",
                    "2. เพิ่ม WHERE clause ตามเงื่อนไขที่กำหนด",
                    "3. ใช้ DISTINCT หากต้องการนับค่าที่ไม่ซ้ำ"
                ])
        
        # Listing hints
        elif any(word in question_lower for word in ['ใครบ้าง', 'รายชื่อ', 'who are']):
            hints.extend([
                "1. SELECT name, position, department สำหรับข้อมูลพื้นฐาน",
                "2. เพิ่ม salary หากเกี่ยวข้องกับการเปรียบเทียบ",
                "3. ใช้ ORDER BY name สำหรับเรียงลำดับ"
            ])
        
        # Add sample data hints if available
        if 'sample_data' in schema_info and schema_info['sample_data']:
            hints.append("\n📋 ตัวอย่างข้อมูลจริง:")
            for table, data in schema_info['sample_data'].items():
                if data and table == 'employees':  # Focus on employees table
                    for column, values in data.items():
                        if values and len(values) > 0:
                            hints.append(f"   {column}: {', '.join(map(str, values[:3]))}")
        
        return '\n'.join(hints)
    
    def _build_schema_section(self, schema_info: Dict, question: str) -> str:
        """🗄️ Build comprehensive schema section based on question relevance"""
        
        if not schema_info or 'tables' not in schema_info:
            return "📊 โครงสร้างฐานข้อมูล: ใช้โครงสร้างมาตรฐาน"
        
        # Determine relevant tables based on question
        relevant_tables = self._identify_relevant_tables(question, schema_info)
        
        schema_section = "📊 โครงสร้างฐานข้อมูล (ข้อมูลจริง):\n"
        
        for table_name in relevant_tables:
            if table_name in schema_info['tables']:
                table_info = schema_info['tables'][table_name]
                schema_section += f"\n🔹 ตาราง {table_name}:\n"
                
                # Add columns with enhanced info
                for column in table_info['columns'][:10]:  # Limit to prevent prompt overflow
                    nullable_info = "" if column.get('nullable', True) else " [NOT NULL]"
                    type_info = column.get('type', 'unknown')
                    schema_section += f"   • {column['name']} ({type_info}){nullable_info}\n"
                
                # Add foreign key relationships
                if 'foreign_keys' in table_info and table_info['foreign_keys']:
                    schema_section += "   🔗 ความสัมพันธ์:\n"
                    for fk in table_info['foreign_keys'][:3]:  # Limit to 3
                        schema_section += f"     - {fk['column']} → {fk['references_table']}.{fk['references_column']}\n"
        
        # Add business insights if available
        if 'business_insights' in schema_info and schema_info['business_insights']:
            insights = schema_info['business_insights']
            if 'department_info' in insights and insights['department_info']:
                dept_info = insights['department_info']
                schema_section += f"\n💡 ข้อมูลเชิงลึก: มี {dept_info.get('total_departments', 0)} แผนก"
                if 'largest_department' in dept_info:
                    schema_section += f", แผนกใหญ่สุด: {dept_info['largest_department']}"
        
        return schema_section
    
    def _identify_relevant_tables(self, question: str, schema_info: Dict) -> List[str]:
        """ระบุตารางที่เกี่ยวข้องกับคำถาม"""
        
        question_lower = question.lower()
        relevant_tables = ['employees']  # Always include employees as primary table
        
        # Check for project-related keywords
        project_keywords = ['โปรเจค', 'project', 'งาน', 'ลูกค้า', 'client']
        if any(keyword in question_lower for keyword in project_keywords):
            relevant_tables.extend(['projects', 'employee_projects'])
        
        # Check for department-related keywords (if departments table exists)
        if 'departments' in schema_info.get('tables', {}):
            dept_keywords = ['แผนก', 'department', 'ฝ่าย']
            if any(keyword in question_lower for keyword in dept_keywords):
                relevant_tables.append('departments')
        
        # Check for client-related keywords
        if 'clients' in schema_info.get('tables', {}):
            client_keywords = ['ลูกค้า', 'client', 'customer']
            if any(keyword in question_lower for keyword in client_keywords):
                relevant_tables.append('clients')
        
        return list(set(relevant_tables))  # Remove duplicates
    
    def _generate_relevant_examples(self, question: str, tenant_config: TenantConfig, intent_result: Dict) -> str:
        """📚 Generate relevant SQL examples based on query type"""
        
        question_lower = question.lower()
        examples = ["📚 ตัวอย่าง SQL ที่เกี่ยวข้อง:"]
        
        # Position search examples
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            examples.extend([
                "",
                "ตัวอย่างที่ 1 - ค้นหาตำแหน่งเฉพาะ:",
                "```sql",
                "SELECT name, position, department, salary",
                "FROM employees",
                "WHERE position ILIKE '%frontend%'",
                "ORDER BY name",
                "LIMIT 20;",
                "```"
            ])
        
        # Counting examples
        elif any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many']):
            examples.extend([
                "",
                "ตัวอย่างที่ 1 - นับจำนวนตามแผนก:",
                "```sql",
                "SELECT department, COUNT(*) as employee_count",
                "FROM employees",
                "GROUP BY department",
                "ORDER BY employee_count DESC;",
                "```"
            ])
        
        # Listing examples
        elif any(word in question_lower for word in ['ใครบ้าง', 'รายชื่อ', 'who are']):
            examples.extend([
                "",
                "ตัวอย่างที่ 1 - แสดงรายชื่อพนักงาน:",
                "```sql",
                "SELECT name, position, department",
                "FROM employees",
                "WHERE department ILIKE '%IT%'",
                "ORDER BY name",
                "LIMIT 20;",
                "```"
            ])
        
        return '\n'.join(examples)
    
    def _extract_keyword(self, text: str, keywords: List[str]) -> str:
        """Extract specific keyword from text"""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                return keyword
        return keywords[0] if keywords else 'developer'
    
    # ========================================================================
    # 🤖 ENHANCED OLLAMA API CALLS
    # ========================================================================
    
    async def call_ollama_api(self, tenant_config: TenantConfig, prompt: str, 
                             context_data: str = "", temperature: float = None) -> str:
        """Enhanced Ollama API call with intelligent model configuration"""
        
        start_time = time.time()
        
        try:
            # Get model-specific configuration
            model_config = self.model_configs.get(tenant_config.model_name, self.model_configs['llama3.1:8b'])
            
            # Override temperature if provided
            if temperature is not None:
                model_config = model_config.copy()
                model_config['temperature'] = temperature
            
            # Prepare full prompt
            full_prompt = self._prepare_full_prompt(prompt, context_data, tenant_config)
            
            # Check cache first
            cache_key = self._generate_cache_key(full_prompt, tenant_config.model_name)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self._update_performance_stats(tenant_config.tenant_id, time.time() - start_time, True, True)
                return cached_response
            
            # Prepare request payload
            payload = {
                "model": tenant_config.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": model_config
            }
            
            # Make API call with retry logic
            response_text = await self._make_api_call_with_retry(payload, tenant_config)
            
            # Cache successful response
            self._cache_response(cache_key, response_text)
            
            # Update performance stats
            execution_time = time.time() - start_time
            self._update_performance_stats(tenant_config.tenant_id, execution_time, True, False)
            
            return response_text
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_stats(tenant_config.tenant_id, execution_time, False, False)
            logger.error(f"❌ Enhanced Ollama API call failed for {tenant_config.tenant_id}: {e}")
            return f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"
    
    def _prepare_full_prompt(self, prompt: str, context_data: str, tenant_config: TenantConfig) -> str:
        """Prepare optimized full prompt"""
        
        # Add system context based on tenant
        system_context = f"System: You are an expert AI assistant for {tenant_config.name} ({tenant_config.business_type})"
        
        if context_data:
            full_prompt = f"{system_context}\n\n{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{system_context}\n\n{prompt}\n\nAssistant:"
        
        return full_prompt
    
    async def _make_api_call_with_retry(self, payload: Dict, tenant_config: TenantConfig) -> str:
        """Make API call with intelligent retry logic"""
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🤖 AI API call attempt {attempt + 1} for {tenant_config.tenant_id}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get('response', '')
                            
                            if response_text.strip():
                                logger.info(f"✅ AI API call successful for {tenant_config.tenant_id}")
                                return response_text
                            else:
                                raise ValueError("Empty response from AI")
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=f"HTTP {response.status}"
                            )
                            
            except asyncio.TimeoutError as e:
                last_error = f"Timeout after {self.request_timeout}s (attempt {attempt + 1})"
                logger.warning(f"⏰ {last_error}")
                
                # Increase timeout for next attempt
                if attempt < self.max_retries - 1:
                    self.request_timeout = min(self.request_timeout + 30, 120)
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                last_error = f"API call error: {str(e)} (attempt {attempt + 1})"
                logger.warning(f"🔄 {last_error}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"All {self.max_retries} attempts failed. Last error: {last_error}")
    
    # ========================================================================
    # 🔄 STREAMING SUPPORT
    # ========================================================================
    
    async def call_ollama_api_streaming(self, tenant_config: TenantConfig, prompt: str, 
                                       context_data: str = "", temperature: float = None) -> AsyncGenerator:
        """Enhanced streaming version with better chunk processing"""
        
        try:
            # Get model configuration
            model_config = self.model_configs.get(tenant_config.model_name, self.model_configs['llama3.1:8b'])
            if temperature is not None:
                model_config = model_config.copy()
                model_config['temperature'] = temperature
            
            # Prepare full prompt
            full_prompt = self._prepare_full_prompt(prompt, context_data, tenant_config)
            
            # Prepare streaming payload
            payload = {
                "model": tenant_config.model_name,
                "prompt": full_prompt,
                "stream": True,
                "options": model_config
            }
            
            logger.info(f"🌊 Starting streaming AI call for {tenant_config.tenant_id}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout * 2)  # Longer timeout for streaming
                ) as response:
                    
                    if response.status == 200:
                        accumulated_response = ""
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if line_text:
                                        data = json.loads(line_text)
                                        
                                        if 'response' in data and data['response']:
                                            chunk = data['response']
                                            accumulated_response += chunk
                                            yield chunk
                                        
                                        # Check if streaming is complete
                                        if data.get('done', False):
                                            logger.info(f"✅ Streaming completed for {tenant_config.tenant_id}")
                                            break
                                            
                                except json.JSONDecodeError:
                                    continue  # Skip invalid JSON lines
                    else:
                        error_msg = f"HTTP {response.status} error from AI service"
                        logger.error(f"❌ {error_msg}")
                        yield error_msg
                        
        except asyncio.TimeoutError:
            error_msg = f"AI streaming timeout after {self.request_timeout * 2}s"
            logger.error(f"⏰ {error_msg}")
            yield error_msg
        except Exception as e:
            error_msg = f"Streaming error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            yield error_msg
    
    # ========================================================================
    # 🧠 INTELLIGENT RESPONSE PROCESSING
    # ========================================================================
    
    def extract_sql_with_validation(self, ai_response: str, question: str, 
                                   tenant_config: TenantConfig) -> Dict[str, Any]:
        """Enhanced SQL extraction with validation and confidence scoring"""
        
        extraction_result = {
            'sql': None,
            'confidence': 0.0,
            'extraction_method': None,
            'validation_issues': [],
            'suggestions': []
        }
        
        # Try multiple extraction methods
        extraction_methods = [
            ('code_block_sql', self._extract_from_sql_code_block),
            ('code_block_generic', self._extract_from_code_block),
            ('select_pattern', self._extract_from_select_pattern),
            ('fallback_generation', self._generate_fallback_sql)
        ]
        
        for method_name, method_func in extraction_methods:
            try:
                sql = method_func(ai_response, question)
                if sql and self._basic_sql_validation(sql):
                    
                    # Calculate confidence based on method and SQL quality
                    confidence = self._calculate_sql_confidence(sql, question, method_name)
                    
                    if confidence > extraction_result['confidence']:
                        extraction_result.update({
                            'sql': sql,
                            'confidence': confidence,
                            'extraction_method': method_name
                        })
                        
                        # Stop if we have high confidence
                        if confidence >= 0.8:
                            break
                            
            except Exception as e:
                logger.warning(f"SQL extraction method {method_name} failed: {e}")
                continue
        
        # Validate final SQL
        if extraction_result['sql']:
            validation_issues = self._validate_sql_relevance(extraction_result['sql'], question)
            extraction_result['validation_issues'] = validation_issues
            
            # Adjust confidence based on validation issues
            if validation_issues:
                extraction_result['confidence'] *= 0.7  # Reduce confidence if issues found
        
        return extraction_result
    
    def _extract_from_sql_code_block(self, response: str, question: str) -> Optional[str]:
        """Extract SQL from ```sql code blocks"""
        pattern = r'```sql\s*(.*?)\s*```'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        return self._clean_sql(match.group(1)) if match else None
    
    def _extract_from_code_block(self, response: str, question: str) -> Optional[str]:
        """Extract SQL from generic ``` code blocks"""
        pattern = r'```\s*(SELECT.*?)\s*```'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        return self._clean_sql(match.group(1)) if match else None
    
    def _extract_from_select_pattern(self, response: str, question: str) -> Optional[str]:
        """Extract SQL using SELECT pattern matching"""
        pattern = r'(SELECT\s+.+?)(?:\n\s*\n|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        return self._clean_sql(match.group(1)) if match else None
    
    def _generate_fallback_sql(self, response: str, question: str) -> Optional[str]:
        """Generate SIMPLE fallback SQL when extraction fails"""
        
        question_lower = question.lower()
        
        # Position search fallback - SIMPLIFIED
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            if 'frontend' in question_lower:
                return "SELECT name, position, department FROM employees WHERE position ILIKE '%frontend%' ORDER BY name LIMIT 20"
            elif 'backend' in question_lower:
                return "SELECT name, position, department FROM employees WHERE position ILIKE '%backend%' ORDER BY name LIMIT 20"
            elif 'designer' in question_lower:
                return "SELECT name, position, department FROM employees WHERE position ILIKE '%designer%' ORDER BY name LIMIT 20"
            elif 'developer' in question_lower:
                return "SELECT name, position, department FROM employees WHERE position ILIKE '%developer%' ORDER BY name LIMIT 20"
            else:
                return "SELECT name, position, department FROM employees WHERE position ILIKE '%developer%' ORDER BY name LIMIT 20"
        
        # Department counting fallback - SIMPLIFIED
        elif 'แผนก' in question_lower and any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many']):
            if 'it' in question_lower:
                return "SELECT COUNT(*) as employee_count FROM employees WHERE department ILIKE '%IT%'"
            else:
                return "SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department ORDER BY employee_count DESC"
        
        # General employee listing - SIMPLIFIED
        elif any(word in question_lower for word in ['พนักงาน', 'employee', 'ใครบ้าง']):
            return "SELECT name, position, department FROM employees ORDER BY name LIMIT 20"
        
        # Project listing
        elif any(word in question_lower for word in ['โปรเจค', 'project']):
            return "SELECT name, client, budget, status FROM projects ORDER BY name LIMIT 20"
        
        return None
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL query"""
        if not sql:
            return ""
        
        # Remove trailing semicolon and whitespace
        sql = sql.rstrip(';').strip()
        
        # Replace multiple whitespace with single space
        sql = re.sub(r'\s+', ' ', sql)
        
        # Ensure proper capitalization for keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT']
        for keyword in keywords:
            sql = re.sub(rf'\b{keyword.lower()}\b', keyword, sql, flags=re.IGNORECASE)
        
        return sql
    
    def _basic_sql_validation(self, sql: str) -> bool:
        """Basic SQL validation"""
        if not sql or not sql.strip():
            return False
        
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False
        
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        return not any(keyword in sql_upper for keyword in dangerous_keywords)
    
    def _calculate_sql_confidence(self, sql: str, question: str, method: str) -> float:
        """Calculate confidence score for extracted SQL"""
        
        confidence = 0.0
        
        # Base confidence by extraction method
        method_confidence = {
            'code_block_sql': 0.9,
            'code_block_generic': 0.8,
            'select_pattern': 0.7,
            'fallback_generation': 0.5
        }
        confidence += method_confidence.get(method, 0.3)
        
        # Boost confidence if SQL contains relevant keywords from question
        question_lower = question.lower()
        sql_lower = sql.lower()
        
        keyword_matches = 0
        total_keywords = 0
        
        # Check for position keywords
        if 'ตำแหน่ง' in question_lower or 'position' in question_lower:
            total_keywords += 1
            if 'position' in sql_lower:
                keyword_matches += 1
        
        # Check for department keywords
        if 'แผนก' in question_lower or 'department' in question_lower:
            total_keywords += 1
            if 'department' in sql_lower:
                keyword_matches += 1
        
        # Check for counting keywords
        if any(word in question_lower for word in ['กี่คน', 'จำนวน', 'how many']):
            total_keywords += 1
            if 'count' in sql_lower:
                keyword_matches += 1
        
        # Adjust confidence based on keyword matching
        if total_keywords > 0:
            keyword_ratio = keyword_matches / total_keywords
            confidence *= (0.5 + 0.5 * keyword_ratio)  # Scale between 0.5 and 1.0
        
        # Check SQL complexity appropriateness
        if 'LIMIT' in sql.upper():
            confidence += 0.1  # Good practice
        
        if len(sql) > 20 and len(sql) < 200:
            confidence += 0.05  # Reasonable length
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _validate_sql_relevance(self, sql: str, question: str) -> List[str]:
        """Validate SQL relevance to question and return issues"""
        
        issues = []
        sql_lower = sql.lower()
        question_lower = question.lower()
        
        # Check if SQL addresses question intent
        if 'ตำแหน่ง' in question_lower and 'position' not in sql_lower:
            issues.append("SQL doesn't search by position as requested")
        
        if 'แผนก' in question_lower and 'department' not in sql_lower:
            issues.append("SQL doesn't filter by department as requested")
        
        if any(word in question_lower for word in ['กี่คน', 'จำนวน']) and 'count' not in sql_lower:
            issues.append("SQL doesn't count records as requested")
        
        # Check for missing LIMIT in potentially large result sets
        if 'limit' not in sql_lower and 'count(' not in sql_lower:
            issues.append("SQL may return too many results (missing LIMIT)")
        
        return issues
    
    # ========================================================================
    # 📊 CACHING SYSTEM
    # ========================================================================
    
    def _generate_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt and model combination"""
        import hashlib
        
        # Create hash from prompt + model
        content = f"{prompt}|{model}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and valid"""
        
        if cache_key not in self.response_cache:
            return None
        
        cache_entry = self.response_cache[cache_key]
        
        # Check if cache is still valid
        cache_age = time.time() - cache_entry['timestamp']
        if cache_age > self.cache_ttl:
            del self.response_cache[cache_key]
            return None
        
        logger.info(f"🚀 Using cached AI response (age: {cache_age:.1f}s)")
        return cache_entry['response']
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache AI response"""
        
        # Limit cache size
        if len(self.response_cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]['timestamp']
            )[:20]
            
            for key in oldest_keys:
                del self.response_cache[key]
        
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def clear_cache(self):
        """Clear all cached responses"""
        self.response_cache.clear()
        logger.info("🧹 AI response cache cleared")
    
    # ========================================================================
    # 📊 PERFORMANCE MONITORING
    # ========================================================================
    
    def _update_performance_stats(self, tenant_id: str, execution_time: float, 
                                 success: bool, cache_hit: bool):
        """Update performance statistics"""
        
        # Update global stats
        self.performance_stats['total_requests'] += 1
        
        if success:
            self.performance_stats['successful_requests'] += 1
        else:
            self.performance_stats['failed_requests'] += 1
        
        if cache_hit:
            self.performance_stats['cache_hits'] += 1
        
        # Update average response time
        total_requests = self.performance_stats['total_requests']
        current_avg = self.performance_stats['avg_response_time']
        new_avg = ((current_avg * (total_requests - 1)) + execution_time) / total_requests
        self.performance_stats['avg_response_time'] = new_avg
        
        # Update tenant-specific stats
        if tenant_id not in self.performance_stats['tenant_breakdown']:
            self.performance_stats['tenant_breakdown'][tenant_id] = {
                'requests': 0,
                'successes': 0,
                'failures': 0,
                'cache_hits': 0,
                'avg_response_time': 0
            }
        
        tenant_stats = self.performance_stats['tenant_breakdown'][tenant_id]
        tenant_stats['requests'] += 1
        
        if success:
            tenant_stats['successes'] += 1
        else:
            tenant_stats['failures'] += 1
        
        if cache_hit:
            tenant_stats['cache_hits'] += 1
        
        # Update tenant average response time
        tenant_requests = tenant_stats['requests']
        tenant_current_avg = tenant_stats['avg_response_time']
        tenant_new_avg = ((tenant_current_avg * (tenant_requests - 1)) + execution_time) / tenant_requests
        tenant_stats['avg_response_time'] = tenant_new_avg
    
    def get_performance_stats(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get performance statistics"""
        
        if tenant_id and tenant_id in self.performance_stats['tenant_breakdown']:
            tenant_stats = self.performance_stats['tenant_breakdown'][tenant_id]
            success_rate = (tenant_stats['successes'] / tenant_stats['requests'] * 100) if tenant_stats['requests'] > 0 else 0
            cache_hit_rate = (tenant_stats['cache_hits'] / tenant_stats['requests'] * 100) if tenant_stats['requests'] > 0 else 0
            
            return {
                'tenant_id': tenant_id,
                'requests': tenant_stats['requests'],
                'success_rate': round(success_rate, 2),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'avg_response_time': round(tenant_stats['avg_response_time'], 3)
            }
        else:
            total_requests = self.performance_stats['total_requests']
            success_rate = (self.performance_stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
            cache_hit_rate = (self.performance_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'success_rate': round(success_rate, 2),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'avg_response_time': round(self.performance_stats['avg_response_time'], 3),
                'tenant_breakdown': self.performance_stats['tenant_breakdown']
            }
    
    # ========================================================================
    # 🔧 HEALTH CHECK AND DIAGNOSTICS
    # ========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for AI service"""
        
        health_status = {
            'status': 'unknown',
            'ollama_server': {},
            'model_availability': {},
            'performance_metrics': {},
            'cache_status': {},
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Test basic connectivity
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        models_data = await response.json()
                        available_models = [model['name'] for model in models_data.get('models', [])]
                        
                        health_status['ollama_server'] = {
                            'status': 'healthy',
                            'url': self.ollama_base_url,
                            'response_time': '< 10s'
                        }
                        
                        health_status['model_availability'] = {
                            'available_models': available_models,
                            'configured_models': list(self.model_configs.keys()),
                            'missing_models': [
                                model for model in self.model_configs.keys() 
                                if model not in available_models
                            ]
                        }
                        
                        # Test a simple query
                        test_result = await self._test_model_functionality()
                        health_status['model_test'] = test_result
                        
                        # Overall status determination
                        if not health_status['model_availability']['missing_models'] and test_result['success']:
                            health_status['status'] = 'healthy'
                        else:
                            health_status['status'] = 'degraded'
                    else:
                        health_status['ollama_server'] = {
                            'status': 'unhealthy',
                            'error': f"HTTP {response.status}"
                        }
                        health_status['status'] = 'unhealthy'
                        
        except asyncio.TimeoutError:
            health_status['ollama_server'] = {
                'status': 'unhealthy',
                'error': 'Connection timeout'
            }
            health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['ollama_server'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Add performance metrics
        health_status['performance_metrics'] = self.get_performance_stats()
        
        # Add cache status
        health_status['cache_status'] = {
            'cached_responses': len(self.response_cache),
            'cache_ttl': self.cache_ttl
        }
        
        return health_status
    
    async def _test_model_functionality(self) -> Dict[str, Any]:
        """Test basic model functionality"""
        
        try:
            # Create a simple test config
            from .tenant_config import TenantConfig
            test_config = TenantConfig(
                tenant_id='test',
                name='Test',
                db_host='test',
                db_port=5432,
                db_name='test',
                db_user='test',
                db_password='test',
                model_name='llama3.1:8b',
                language='th',
                business_type='test',
                key_metrics=[]
            )
            
            test_prompt = "Generate a simple SELECT SQL query to get employee names."
            response = await self.call_ollama_api(test_config, test_prompt, temperature=0.1)
            
            # Check if response contains SQL
            has_sql = 'SELECT' in response.upper()
            
            return {
                'success': True,
                'response_length': len(response),
                'contains_sql': has_sql,
                'model_responsive': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model_responsive': False
            }
    
    # ========================================================================
    # 🔧 UTILITY METHODS
    # ========================================================================
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific model"""
        return self.model_configs.get(model_name, self.model_configs['llama3.1:8b'])
    
    def add_model_config(self, model_name: str, config: Dict[str, Any]):
        """Add new model configuration"""
        self.model_configs[model_name] = config
        logger.info(f"✅ Added model configuration for {model_name}")
    
    def optimize_for_tenant(self, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Get optimized settings for specific tenant"""
        
        # Business type specific optimizations
        optimizations = {
            'enterprise_software': {
                'temperature': 0.1,  # More precise for technical queries
                'top_p': 0.8,
                'emphasis': 'accuracy'
            },
            'tourism_hospitality': {
                'temperature': 0.2,  # Slightly more creative for tourism
                'top_p': 0.85,
                'emphasis': 'cultural_awareness'
            },
            'global_operations': {
                'temperature': 0.15,  # Balanced for international context
                'top_p': 0.9,
                'emphasis': 'multilingual_accuracy'
            }
        }
        
        return optimizations.get(tenant_config.business_type, optimizations['enterprise_software'])

# Create alias for backward compatibility
AIService = EnhancedAIService

# Also export both names
__all__ = ['EnhancedAIService', 'AIService']# refactored_modules/ai_service.py
# 🤖 Enhanced AI/Ollama Communication Service with Smart Prompt Engineering

