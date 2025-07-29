import os
import json
import asyncio
import aiohttp
import psycopg2
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TenantConfig:
    """Tenant configuration"""
    tenant_id: str
    name: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    model_name: str
    language: str

class PostgresOllamaAgent:
    """Enhanced PostgreSQL + Ollama Agent with AI-Generated SQL"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://192.168.11.97:12434')
        self.tenant_configs = self._load_tenant_configs()
        self.database_schemas = self._load_database_schemas()
        
    def _load_tenant_configs(self) -> Dict[str, TenantConfig]:
        """Load tenant configurations from environment variables"""
        configs = {}
        
        # Company A Configuration
        configs['company-a'] = TenantConfig(
            tenant_id='company-a',
            name='SiamTech Bangkok HQ',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_A', 'postgres-company-a'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_A', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_A', 'siamtech_company_a'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_A', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_A', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_A', 'llama3.1:8b'),
            language='th'
        )
        
        # Company B Configuration
        configs['company-b'] = TenantConfig(
            tenant_id='company-b',
            name='SiamTech Chiang Mai Regional',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_B', 'postgres-company-b'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_B', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_B', 'siamtech_company_b'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_B', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_B', 'password123'),
            model_name=os.getenv('MODEL_COMPANY_B', 'llama3.1:8b'),
            language='th'
        )
        
        # Company C Configuration
        configs['company-c'] = TenantConfig(
            tenant_id='company-c',
            name='SiamTech International',
            db_host=os.getenv('POSTGRES_HOST_COMPANY_C', 'postgres-company-c'),
            db_port=int(os.getenv('POSTGRES_PORT_COMPANY_C', '5432')),
            db_name=os.getenv('POSTGRES_DB_COMPANY_C', 'siamtech_company_c'),
            db_user=os.getenv('POSTGRES_USER_COMPANY_C', 'postgres'),
            db_password=os.getenv('POSTGRES_PASSWORD_COMPANY_C', 'password123'),
            model_name=os.getenv('', 'phi3:14b'),
            language='en'
        )
        
        return configs
    
    def _load_database_schemas(self) -> Dict[str, Dict]:
        """Load database schema information for each tenant"""
        return {
            'company-a': {
                'description': 'SiamTech Bangkok HQ Database - Enterprise solutions, Banking, E-commerce projects',
                'tables': {
                    'employees': {
                        'description': 'พนักงานของบริษัท',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - ชื่อพนักงาน',
                            'department (VARCHAR(50)) - แผนก เช่น IT, Sales, Management, HR',
                            'position (VARCHAR(100)) - ตำแหน่งงาน',
                            'salary (DECIMAL(10,2)) - เงินเดือน',
                            'hire_date (DATE) - วันที่เข้าทำงาน',
                            'email (VARCHAR(150)) - อีเมล'
                        ]
                    },
                    'projects': {
                        'description': 'โปรเจคของบริษัท',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - ชื่อโปรเจค',
                            'client (VARCHAR(100)) - ลูกค้า',
                            'budget (DECIMAL(12,2)) - งบประมาณ (หน่วยบาท)',
                            'status (VARCHAR(20)) - สถานะ (active, completed, cancelled)',
                            'start_date (DATE) - วันเริ่มโปรเจค',
                            'end_date (DATE) - วันจบโปรเจค',
                            'tech_stack (VARCHAR(500)) - เทคโนโลยีที่ใช้'
                        ]
                    },
                    'employee_projects': {
                        'description': 'ความสัมพันธ์ระหว่างพนักงานและโปรเจค',
                        'columns': [
                            'employee_id (INTEGER) - รหัสพนักงาน (FK to employees.id)',
                            'project_id (INTEGER) - รหัสโปรเจค (FK to projects.id)',
                            'role (VARCHAR(100)) - บทบาทในโปรเจค',
                            'allocation (DECIMAL(3,2)) - สัดส่วนเวลาทำงาน (0-1)'
                        ]
                    }
                },
                'business_context': 'บริษัทพัฒนาซอฟต์แวร์องค์กร ระบบธนาคาร และ E-commerce ลูกค้าส่วนใหญ่เป็นธนาคารและบริษัทขนาดใหญ่'
            },
            'company-b': {
                'description': 'SiamTech Chiang Mai Regional Database - Tourism, Hospitality, Regional projects',
                'tables': {
                    'employees': {
                        'description': 'พนักงานสาขาเชียงใหม่',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - ชื่อพนักงาน',
                            'department (VARCHAR(50)) - แผนก',
                            'position (VARCHAR(100)) - ตำแหน่งงาน',
                            'salary (DECIMAL(10,2)) - เงินเดือน',
                            'hire_date (DATE) - วันที่เข้าทำงาน',
                            'email (VARCHAR(150)) - อีเมล'
                        ]
                    },
                    'projects': {
                        'description': 'โปรเจคสาขาเชียงใหม่ เน้นการท่องเที่ยว',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - ชื่อโปรเจค',
                            'client (VARCHAR(100)) - ลูกค้า (โรงแรม, การท่องเที่ยว)',
                            'budget (DECIMAL(12,2)) - งบประมาณ (หน่วยบาท)',
                            'status (VARCHAR(20)) - สถานะ',
                            'start_date (DATE) - วันเริ่มโปรเจค',
                            'end_date (DATE) - วันจบโปรเจค',
                            'tech_stack (VARCHAR(500)) - เทคโนโลยีที่ใช้'
                        ]
                    },
                    'employee_projects': {
                        'description': 'ความสัมพันธ์ระหว่างพนักงานและโปรเจค',
                        'columns': [
                            'employee_id (INTEGER) - รหัสพนักงาน',
                            'project_id (INTEGER) - รหัสโปรเจค',
                            'role (VARCHAR(100)) - บทบาทในโปรเจค',
                            'allocation (DECIMAL(3,2)) - สัดส่วนเวลาทำงาน'
                        ]
                    }
                },
                'business_context': 'สาขาเชียงใหม่เน้นเทคโนโลยีการท่องเที่ยว ลูกค้าส่วนใหญ่เป็นโรงแรม รีสอร์ท และธุรกิจท่องเที่ยว'
            },
            'company-c': {
                'description': 'SiamTech International Database - Global operations, International clients',
                'tables': {
                    'employees': {
                        'description': 'International team members',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(100)) - Employee name',
                            'department (VARCHAR(50)) - Department',
                            'position (VARCHAR(100)) - Job position',
                            'salary (DECIMAL(10,2)) - Salary',
                            'hire_date (DATE) - Hire date',
                            'email (VARCHAR(150)) - Email'
                        ]
                    },
                    'projects': {
                        'description': 'International projects',
                        'columns': [
                            'id (SERIAL PRIMARY KEY)',
                            'name (VARCHAR(200)) - Project name',
                            'client (VARCHAR(100)) - International client',
                            'budget (DECIMAL(12,2)) - Budget',
                            'status (VARCHAR(20)) - Status',
                            'start_date (DATE) - Start date',
                            'end_date (DATE) - End date',
                            'tech_stack (VARCHAR(500)) - Technology stack'
                        ]
                    },
                    'employee_projects': {
                        'description': 'Employee-project relationships',
                        'columns': [
                            'employee_id (INTEGER) - Employee ID',
                            'project_id (INTEGER) - Project ID',
                            'role (VARCHAR(100)) - Role in project',
                            'allocation (DECIMAL(3,2)) - Time allocation'
                        ]
                    }
                },
                'business_context': 'International software solutions, global clients, cross-border technology projects'
            }
        }
    
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
        """Execute SQL query and return results"""
        conn = None
        try:
            conn = self.get_database_connection(tenant_id)
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
                
            logger.info(f"Query executed successfully for {tenant_id}: {len(results)} rows returned")
            return results
            
        except Exception as e:
            logger.error(f"SQL execution failed for {tenant_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def generate_sql_with_ai(self, question: str, tenant_id: str) -> str:
        """ให้ AI สร้าง SQL จากคำถาม - ฟีเจอร์หลักใหม่"""
        config = self.tenant_configs[tenant_id]
        schema_info = self.database_schemas[tenant_id]
        
        # สร้าง schema information สำหรับ AI
        schema_text = self._format_schema_for_ai(schema_info, config.language)
        
        # สร้าง prompt สำหรับ AI
        if config.language == 'en':
            system_prompt = f"""You are a SQL expert for {config.name}.

{schema_text}

IMPORTANT RULES:
1. Generate ONLY valid PostgreSQL SQL query
2. Always use LIMIT to prevent large results (max 20 rows)
3. Use proper JOINs when accessing multiple tables
4. Handle potential NULL values safely
5. For budget/money questions: budget is in Thai Baht (฿), 1 million = 1,000,000
6. Use appropriate WHERE clauses to filter data
7. Return only the SQL query, no explanations

User Question: {question}

Generate SQL query:"""
        else:
            system_prompt = f"""คุณคือ SQL Expert สำหรับ {config.name}

{schema_text}

กฎสำคัญ:
1. สร้างเฉพาะ SQL query ที่ถูกต้องสำหรับ PostgreSQL
2. ใช้ LIMIT เสมอเพื่อจำกัดผลลัพธ์ (ไม่เกิน 20 แถว)
3. ใช้ JOIN เมื่อต้องการข้อมูลจากหลายตาราง
4. จัดการกับค่า NULL อย่างปลอดภัย
5. สำหรับคำถามเรื่องงบประมาณ: budget เป็นหน่วยบาท 1 ล้าน = 1,000,000
6. ใช้ WHERE clause ที่เหมาะสมในการกรองข้อมูล
7. ตอบเฉพาะ SQL query เท่านั้น ไม่ต้องอธิบาย

คำถามผู้ใช้: {question}

สร้าง SQL query:"""
        
        try:
            # เรียก AI สร้าง SQL
            ai_response = await self.call_ollama_api(
                tenant_id=tenant_id,
                prompt=system_prompt,
                context_data="",
                temperature=0.1  # ใช้ temperature ต่ำสำหรับ SQL generation
            )
            
            # Extract SQL from AI response
            sql_query = self._extract_sql_from_response(ai_response)
            
            logger.info(f"AI Generated SQL for {tenant_id}: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Failed to generate SQL with AI: {e}")
            # Fallback to simple query
            return "SELECT 'ไม่สามารถสร้าง SQL ได้' as message LIMIT 1;"
    
    def _format_schema_for_ai(self, schema_info: Dict, language: str) -> str:
        """Format database schema information for AI prompt"""
        formatted = ""
        
        if language == 'en':
            formatted += f"Database: {schema_info['description']}\n"
            formatted += f"Business Context: {schema_info['business_context']}\n\n"
            formatted += "Tables and Columns:\n"
        else:
            formatted += f"ฐานข้อมูล: {schema_info['description']}\n"
            formatted += f"บริบทธุรกิจ: {schema_info['business_context']}\n\n"
            formatted += "ตารางและคอลัมน์:\n"
        
        for table_name, table_info in schema_info['tables'].items():
            formatted += f"\n📋 {table_name}: {table_info['description']}\n"
            for column in table_info['columns']:
                formatted += f"   • {column}\n"
        
        # เพิ่มตัวอย่าง SQL patterns
        if language == 'en':
            formatted += f"\nCommon SQL Patterns:\n"
            formatted += f"• Employee count by department: SELECT department, COUNT(*) FROM employees GROUP BY department;\n"
            formatted += f"• High budget projects: SELECT * FROM projects WHERE budget > 2000000 ORDER BY budget DESC;\n"
            formatted += f"• Employee in projects: SELECT e.name, p.name FROM employees e JOIN employee_projects ep ON e.id = ep.employee_id JOIN projects p ON ep.project_id = p.id;\n"
        else:
            formatted += f"\nรูปแบบ SQL ทั่วไป:\n"
            formatted += f"• นับพนักงานตามแผนก: SELECT department, COUNT(*) FROM employees GROUP BY department;\n"
            formatted += f"• โปรเจคงบสูง: SELECT * FROM projects WHERE budget > 2000000 ORDER BY budget DESC;\n"
            formatted += f"• พนักงานในโปรเจค: SELECT e.name, p.name FROM employees e JOIN employee_projects ep ON e.id = ep.employee_id JOIN projects p ON ep.project_id = p.id;\n"
        
        return formatted
    
    def _extract_sql_from_response(self, ai_response: str) -> str:
        """Extract SQL query from AI response"""
        # Remove common prefixes/suffixes
        cleaned = ai_response.strip()
        
        # Remove markdown code blocks
        if '```sql' in cleaned:
            start = cleaned.find('```sql') + 6
            end = cleaned.find('```', start)
            if end != -1:
                cleaned = cleaned[start:end].strip()
        elif '```' in cleaned:
            start = cleaned.find('```') + 3
            end = cleaned.find('```', start)
            if end != -1:
                cleaned = cleaned[start:end].strip()
        
        # Extract just the SQL part
        lines = cleaned.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('--') and not line.startswith('/*'):
                # Check if line looks like SQL
                if any(keyword in line.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER']):
                    sql_lines.append(line)
                elif sql_lines:  # Continue adding if we've started collecting SQL
                    sql_lines.append(line)
        
        if sql_lines:
            sql_query = ' '.join(sql_lines)
            # Ensure query ends with semicolon
            if not sql_query.rstrip().endswith(';'):
                sql_query += ';'
            
            # Clean up extra spaces
            sql_query = ' '.join(sql_query.split())
            
            return sql_query
        
        # Fallback if no SQL detected
        return "SELECT 'ไม่สามารถสร้าง SQL ได้' as message LIMIT 1;"
    
    async def call_ollama_api(self, tenant_id: str, prompt: str, context_data: str = "", temperature: float = 0.7) -> str:
        """Call Ollama API with tenant-specific model"""
        config = self.tenant_configs[tenant_id]
        
        # Prepare system prompt
        if context_data:
            full_prompt = f"{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        # Prepare request payload
        payload = {
            "model": config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1000 if temperature < 0.3 else 2000
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
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
    
    async def process_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Main processing function ที่ให้ AI สร้าง SQL เอง"""
        if tenant_id not in self.tenant_configs:
            return {
                "answer": f"ไม่รู้จัก tenant: {tenant_id}",
                "success": False,
                "data_source_used": "error"
            }
        
        config = self.tenant_configs[tenant_id]
        
        try:
            # 1. ให้ AI สร้าง SQL จากคำถาม (ฟีเจอร์หลักใหม่)
            sql_query = await self.generate_sql_with_ai(question, tenant_id)
            
            # 2. Execute SQL query
            db_results = self.execute_sql_query(tenant_id, sql_query)
            
            # 3. Format database results
            if db_results:
                context_data = f"ข้อมูลจากฐานข้อมูล {config.name}:\n"
                for i, row in enumerate(db_results[:15]):  # Limit to 15 rows for context
                    context_data += f"{i+1}. "
                    for key, value in row.items():
                        # Format values nicely
                        if isinstance(value, (int, float)) and key == 'budget':
                            context_data += f"{key}: {value:,.0f} บาท, "
                        else:
                            context_data += f"{key}: {value}, "
                    context_data = context_data.rstrip(", ") + "\n"
            else:
                context_data = "ไม่พบข้อมูลที่ตรงกับคำถาม"
            
            # 4. ให้ AI ตีความผลลัพธ์และตอบคำถาม
            if config.language == 'en':
                interpretation_prompt = f"""Based on the database query results, please answer the user's question clearly and professionally.

User Question: {question}
SQL Query Used: {sql_query}
Database Results: {context_data}

Please provide a comprehensive and helpful answer based on this data:"""
            else:
                interpretation_prompt = f"""จากข้อมูลที่ได้จากฐานข้อมูล กรุณาตอบคำถามของผู้ใช้อย่างชัดเจนและเป็นประโยชน์

คำถามผู้ใช้: {question}
SQL ที่ใช้: {sql_query}
ผลลัพธ์จากฐานข้อมูล: {context_data}

กรุณาให้คำตอบที่ครบถ้วนและเป็นประโยชน์จากข้อมูลนี้:"""
            
            ai_response = await self.call_ollama_api(tenant_id, interpretation_prompt)
            
            return {
                "answer": ai_response,
                "success": True,
                "data_source_used": f"ai_generated_sql_{config.model_name}",
                "sql_query": sql_query,
                "db_results_count": len(db_results),
                "tenant_id": tenant_id,
                "model_used": config.model_name,
                "ai_generated_sql": True
            }
            
        except Exception as e:
            logger.error(f"Error processing question for {tenant_id}: {e}")
            
            # Fallback to AI-only response
            try:
                fallback_prompt = f"คำถาม: {question}\n\nเนื่องจากไม่สามารถเข้าถึงข้อมูลฐานข้อมูลได้ กรุณาตอบคำถามด้วยความรู้ทั่วไปเกี่ยวกับ {config.name}"
                ai_response = await self.call_ollama_api(tenant_id, fallback_prompt)
                return {
                    "answer": ai_response,
                    "success": True,
                    "data_source_used": f"ai_only_{config.model_name}",
                    "error": str(e),
                    "fallback_mode": True
                }
            except Exception as ai_error:
                return {
                    "answer": f"เกิดข้อผิดพลาด: {str(e)}",
                    "success": False,
                    "data_source_used": "error",
                    "error": str(ai_error)
                }

# For testing
async def main():
    agent = PostgresOllamaAgent()
    
    test_questions = [
        ("company-a", "พนักงานคนไหนทำงานในโปรเจคที่มีงบประมาณสูงกว่า 2 ล้านบาท"),
        ("company-a", "มีพนักงานกี่คนในแต่ละแผนก"),
        ("company-a", "โปรเจคไหนมีงบประมาณสูงสุด 3 อันดับแรก"),
        ("company-b", "โปรเจคของโรงแรมดุสิตมีงบประมาณเท่าไหร่"),
        ("company-c", "What are the highest budget international projects?"),
    ]
    
    for tenant_id, question in test_questions:
        print(f"\n{'='*50}")
        print(f"🏢 Tenant: {tenant_id}")
        print(f"❓ Question: {question}")
        print(f"{'='*50}")
        
        result = await agent.process_question(question, tenant_id)
        
        print(f"✅ Success: {result['success']}")
        print(f"🔍 SQL: {result.get('sql_query', 'N/A')}")
        print(f"📊 Results: {result.get('db_results_count', 'N/A')} rows")
        print(f"💬 Answer: {result['answer'][:200]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())