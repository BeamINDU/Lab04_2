import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SQLExample:
    """ตัวอย่าง SQL พร้อมคำอธิบาย"""
    question: str
    sql: str
    explanation: str
    category: str
    difficulty: str = "medium"
    confidence: float = 0.9

class FewShotSQLEngine:
    """🧠 ระบบ Few-Shot Learning สำหรับ SQL Generation"""
    
    def __init__(self):
        self.sql_examples = self._load_curated_examples()
        self.question_patterns = self._load_question_patterns()
        logger.info("✅ Few-Shot SQL Engine initialized")
    
    def _load_curated_examples(self) -> Dict[str, List[SQLExample]]:
        """โหลดตัวอย่าง SQL ที่คัดสรรมาแล้ว"""
        return {
            # 🎯 Assignment Queries - คำถามเกี่ยวกับการมอบหมายงาน
            'assignment_queries': [
                SQLExample(
                    question="พนักงาน siamtech แต่ละคนรับผิดชอบโปรเจคอะไรบ้าง",
                    sql="""SELECT 
    e.name as employee_name,
    e.position,
    e.department,
    COALESCE(p.name, 'ไม่มีโปรเจค') as project_name,
    COALESCE(p.client, '-') as client,
    COALESCE(ep.role, 'ไม่มีบทบาท') as project_role,
    CASE 
        WHEN ep.allocation IS NOT NULL 
        THEN ROUND(ep.allocation * 100, 1) || '%'
        ELSE '0%' 
    END as time_allocation
FROM employees e
LEFT JOIN employee_projects ep ON e.id = ep.employee_id
LEFT JOIN projects p ON ep.project_id = p.id
ORDER BY e.name, p.name
LIMIT 20;""",
                    explanation="ใช้ LEFT JOIN เพื่อแสดงพนักงานทุกคน รวมคนที่ไม่มีโปรเจค, ใช้ COALESCE สำหรับจัดการ NULL",
                    category="assignment_queries",
                    confidence=0.95
                ),
                
                SQLExample(
                    question="ใครบ้างที่ทำงานในโปรเจค Mobile Banking App",
                    sql="""SELECT 
    p.name as project_name,
    p.client,
    e.name as employee_name,
    e.position,
    ep.role as project_role,
    ROUND(ep.allocation * 100, 1) || '%' as time_allocation,
    p.status as project_status
FROM projects p
JOIN employee_projects ep ON p.id = ep.project_id
JOIN employees e ON ep.employee_id = e.id
WHERE p.name ILIKE '%Mobile Banking%'
ORDER BY ep.allocation DESC;""",
                    explanation="ใช้ INNER JOIN เพื่อแสดงเฉพาะคนที่มีงาน, ใช้ ILIKE สำหรับค้นหาแบบไม่สนใจตัวใหญ่เล็ก",
                    category="assignment_queries",
                    confidence=0.90
                )
            ],
            
            # 📊 Department Analysis - วิเคราะห์แผนก
            'department_analysis': [
                SQLExample(
                    question="มีพนักงานกี่คนในแต่ละแผนก",
                    sql="""SELECT 
    department,
    COUNT(*) as employee_count,
    ROUND(AVG(salary), 0) as avg_salary,
    MIN(salary) as min_salary,
    MAX(salary) as max_salary,
    TO_CHAR(AVG(salary), 'FM999,999,999') || ' บาท' as formatted_avg_salary
FROM employees 
GROUP BY department 
ORDER BY employee_count DESC;""",
                    explanation="ใช้ GROUP BY สำหรับจัดกลุ่มตามแผนก, ใช้ COUNT, AVG, MIN, MAX สำหรับสถิติ",
                    category="department_analysis",
                    confidence=0.95
                )
            ],
            
            # 💰 Project & Budget Analysis - วิเคราะห์โปรเจคและงบประมาณ
            'project_analysis': [
                SQLExample(
                    question="โปรเจคไหนมีงบประมาณสูงสุด",
                    sql="""SELECT 
    p.name as project_name,
    p.client,
    TO_CHAR(p.budget, 'FM999,999,999') || ' บาท' as formatted_budget,
    p.status,
    p.start_date,
    p.end_date,
    COUNT(ep.employee_id) as team_size
FROM projects p
LEFT JOIN employee_projects ep ON p.id = ep.project_id
GROUP BY p.id, p.name, p.client, p.budget, p.status, p.start_date, p.end_date
ORDER BY p.budget DESC NULLS LAST
LIMIT 10;""",
                    explanation="ใช้ LEFT JOIN เพื่อรวมข้อมูลทีม, จัดรูปแบบเงิน, เรียงตามงบประมาณ",
                    category="project_analysis",
                    confidence=0.90
                )
            ]
        }
    
    def _load_question_patterns(self) -> Dict[str, List[str]]:
        """โหลด patterns สำหรับจับประเภทคำถาม"""
        return {
            'assignment_queries': [
                r'(พนักงาน.*แต่ละคน.*(?:รับผิดชอบ|ทำงาน|จัดการ))',
                r'(siamtech.*แต่ละคน.*(?:รับผิดชอบ|โปรเจค))',
                r'(ใคร.*(?:ทำงาน|รับผิดชอบ).*(?:โปรเจค|งาน))',
                r'(รับผิดชอบ.*(?:อะไร|ไหน|บ้าง))',
                r'(แต่ละคน.*(?:รับผิดชอบ|ทำ|งาน))'
            ],
            'department_analysis': [
                r'((?:กี่คน|จำนวน).*แผนก)',
                r'(แผนก.*(?:กี่คน|จำนวน|มี))',
                r'(แผนกไหน.*(?:เงินเดือน|พนักงาน))'
            ],
            'project_analysis': [
                r'(โปรเจค.*(?:งบประมาณ|สูงสุด|ใหญ่))',
                r'(งบประมาณ.*(?:โปรเจค|สูงสุด|มาก))',
                r'(ลูกค้า.*(?:โปรเจค|กี่))'
            ]
        }
    
    def find_relevant_examples(self, question: str, max_examples: int = 2) -> List[SQLExample]:
        """🎯 หาตัวอย่างที่เกี่ยวข้องกับคำถาม"""
        question_lower = question.lower()
        scored_examples = []
        
        # คำนวณคะแนนสำหรับแต่ละตัวอย่าง
        for category, examples in self.sql_examples.items():
            category_patterns = self.question_patterns.get(category, [])
            
            # เช็คว่าคำถามตรงกับ category นี้ไหม
            category_score = 0
            for pattern in category_patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    category_score += 1
            
            # ถ้าตรงกับ category ให้คิดคะแนนตัวอย่าง
            if category_score > 0:
                for example in examples:
                    # คำนวณความคล้าย
                    similarity_score = self._calculate_similarity(question, example.question)
                    total_score = (category_score * 0.4) + (similarity_score * 0.4) + (example.confidence * 0.2)
                    
                    scored_examples.append((total_score, example))
        
        # เรียงตามคะแนนและเอาที่ดีที่สุด
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in scored_examples[:max_examples]]
    
    def _calculate_similarity(self, question1: str, question2: str) -> float:
        """คำนวณความคล้ายระหว่างคำถาม"""
        words1 = set(question1.lower().split())
        words2 = set(question2.lower().split())
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def generate_few_shot_prompt(self, question: str, schema_info: Dict, config) -> str:
        """🎯 สร้าง Few-Shot Prompt ที่มีประสิทธิภาพ"""
        
        # หาตัวอย่างที่เกี่ยวข้อง
        relevant_examples = self.find_relevant_examples(question, max_examples=2)
        
        # สร้าง examples section
        examples_section = self._format_examples_section(relevant_examples)
        
        # สร้าง schema section แบบกระชับ
        schema_section = self._format_schema_section(schema_info)
        
        if config.language == 'th':
            prompt = f"""คุณคือ PostgreSQL Expert ที่เขียน SQL ได้อย่างแม่นยำสำหรับ {config.name}

📋 โครงสร้างฐานข้อมูล:
{schema_section}

🎯 เรียนรู้จากตัวอย่างที่ถูกต้อง:
{examples_section}

🔧 หลักการสำคัญ:
1. ใช้ LEFT JOIN เมื่อต้องการแสดงข้อมูลทั้งหมด (รวมที่ไม่มีความสัมพันธ์)
2. ใช้ INNER JOIN เมื่อต้องการเฉพาะข้อมูลที่มีความสัมพันธ์
3. ใช้ COALESCE สำหรับแทนที่ NULL ด้วยข้อความที่เหมาะสม
4. ใช้ TO_CHAR หรือ ROUND สำหรับจัดรูปแบบตัวเลข
5. ใส่ ORDER BY เพื่อเรียงข้อมูลให้เป็นระเบียบ
6. ใส่ LIMIT เมื่อต้องการจำกัดจำนวนผลลัพธ์
7. ใช้ ILIKE แทน LIKE สำหรับการค้นหาใน PostgreSQL

⚠️ สำคัญมาก:
- ตอบเฉพาะ SQL query ที่สมบูรณ์
- ไม่ต้องมีคำอธิบายเพิ่มเติม
- ใช้ชื่อคอลัมน์ที่มีความหมาย (employee_name, project_name)

คำถาม: {question}

PostgreSQL Query:
```sql"""
        
        else:  # English
            prompt = f"""You are a PostgreSQL Expert for {config.name}

📋 Database Schema:
{schema_section}

🎯 Learn from these examples:
{examples_section}

🔧 Key Principles:
1. Use LEFT JOIN to show all records
2. Use INNER JOIN for required relationships
3. Use COALESCE for NULL handling
4. Use meaningful column names
5. Include ORDER BY and LIMIT

Question: {question}

PostgreSQL Query:
```sql"""
        
        return prompt
    
    def _format_examples_section(self, examples: List[SQLExample]) -> str:
        """จัดรูปแบบ section ตัวอย่าง"""
        if not examples:
            return "ไม่มีตัวอย่างที่เกี่ยวข้องโดยตรง"
        
        formatted = ""
        for i, example in enumerate(examples, 1):
            formatted += f"""
ตัวอย่างที่ {i}:
คำถาม: {example.question}
```sql
{example.sql.strip()}
```
หลักการ: {example.explanation}
"""
        return formatted
    
    def _format_schema_section(self, schema_info: Dict) -> str:
        """จัดรูปแบบ schema แบบกระชับ"""
        tables = schema_info.get('tables', {})
        formatted = ""
        
        # เอาเฉพาะตารางหลักและคอลัมน์สำคัญ
        essential_tables = ['employees', 'projects', 'employee_projects']
        
        for table_name in essential_tables:
            if table_name in tables:
                table_info = tables[table_name]
                columns = table_info.get('columns', [])
                
                # เอาเฉพาะคอลัมน์สำคัญ
                main_columns = []
                for col in columns[:8]:  # จำกัด 8 คอลัมน์
                    col_name = col.split(' ')[0]  # เอาเฉพาะชื่อ
                    main_columns.append(col_name)
                
                formatted += f"• {table_name}: {', '.join(main_columns)}\n"
        
        # เพิ่มความสัมพันธ์
        formatted += "\n🔗 ความสัมพันธ์:\n"
        formatted += "• employees ← employee_projects → projects\n"
        formatted += "• employee_projects มี role และ allocation\n"
        
        return formatted

class EnhancedFewShotAgent:
    """🚀 Agent ที่ใช้ Few-Shot Learning"""
    
    def __init__(self, original_agent):
        self.original_agent = original_agent
        self.few_shot_engine = FewShotSQLEngine()
        logger.info("✅ Enhanced Few-Shot Agent initialized")
    
    async def generate_sql_with_few_shot(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """สร้าง SQL ด้วย Few-Shot Learning"""
        
        config = self.original_agent.tenant_configs[tenant_id]
        schema_info = self.original_agent.schema_service.get_schema_info(tenant_id)
        
        try:
            # 1. สร้าง Few-Shot Prompt
            few_shot_prompt = self.few_shot_engine.generate_few_shot_prompt(
                question, schema_info, config
            )
            
            logger.info(f"🎯 Generated few-shot prompt with {len(self.few_shot_engine.find_relevant_examples(question))} examples")
            
            # 2. เรียก AI
            ai_response = await self.original_agent.ai_service.call_ollama_api(
                config, few_shot_prompt, temperature=0.1  # ใช้ temp ต่ำเพื่อความแม่นยำ
            )
            
            # 3. แยก SQL
            sql_query = self._extract_sql_from_response(ai_response)
            
            # 4. Validate
            if self._validate_sql_basic(sql_query):
                return sql_query, {
                    'method': 'few_shot_learning',
                    'confidence': 'high',
                    'examples_used': len(self.few_shot_engine.find_relevant_examples(question)),
                    'temperature': 0.1
                }
            else:
                # Fallback
                return await self._fallback_to_original(question, tenant_id)
                
        except Exception as e:
            logger.error(f"Few-shot generation failed: {e}")
            return await self._fallback_to_original(question, tenant_id)
    
    def _extract_sql_from_response(self, ai_response: str) -> str:
        """แยก SQL จาก AI response"""
        # ลบ markdown และข้อความเพิ่มเติม
        cleaned = ai_response.strip()
        
        # หา SQL ใน code block
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;?)\s*```',
            r'(SELECT.*?;)',
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                
                # ทำความสะอาด
                sql = ' '.join(sql.split())  # ลบ whitespace เกิน
                if not sql.endswith(';'):
                    sql += ';'
                
                return sql
        
        # ถ้าไม่เจอ ลองหาจากบรรทัดแรกที่ขึ้นต้นด้วย SELECT
        lines = cleaned.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('SELECT') or sql_lines:
                sql_lines.append(line)
                if line.endswith(';'):
                    break
        
        if sql_lines:
            sql = ' '.join(sql_lines)
            return sql if sql.endswith(';') else sql + ';'
        
        return "SELECT 'Few-shot SQL extraction failed' as error;"
    
    def _validate_sql_basic(self, sql: str) -> bool:
        """ตรวจสอบ SQL พื้นฐาน"""
        sql_upper = sql.upper().strip()
        
        # เช็คพื้นฐาน
        if not sql_upper.startswith('SELECT'):
            return False
        
        # เช็คว่าไม่มีคำสั่งอันตราย
        dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous):
            return False
        
        # เช็คว่ามี FROM
        if 'FROM' not in sql_upper:
            return False
        
        return True
    
    async def _fallback_to_original(self, question: str, tenant_id: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback ไปยังวิธีเดิม"""
        logger.info("🔄 Falling back to original SQL generation")
        return await self.original_agent.original_generate_enhanced_sql(question, tenant_id)

# Test function สำหรับทดสอบ
async def test_few_shot_engine():
    """ทดสอบระบบ Few-Shot"""
    
    # สร้าง mock objects
    class MockConfig:
        language = 'th'
        name = 'SiamTech Bangkok HQ'
    
    mock_schema = {
        'tables': {
            'employees': {'columns': ['id', 'name', 'position', 'department', 'salary']},
            'projects': {'columns': ['id', 'name', 'client', 'budget', 'status']},
            'employee_projects': {'columns': ['employee_id', 'project_id', 'role', 'allocation']}
        }
    }
    
    # ทดสอบ
    engine = FewShotSQLEngine()
    config = MockConfig()
    
    test_question = "พนักงาน siamtech แต่ละคนรับผิดชอบโปรเจคอะไรบ้าง"
    
    print("🧪 Testing Few-Shot SQL Engine")
    print("=" * 50)
    print(f"Question: {test_question}")
    
    # หาตัวอย่างที่เกี่ยวข้อง
    examples = engine.find_relevant_examples(test_question)
    print(f"🎯 Found {len(examples)} relevant examples")
    
    # สร้าง prompt
    prompt = engine.generate_few_shot_prompt(test_question, mock_schema, config)
    print(f"📝 Prompt generated successfully: {len(prompt)} characters")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_few_shot_engine())