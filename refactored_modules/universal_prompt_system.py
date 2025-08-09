import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SimpleUniversalPromptGenerator:
    """🎯 Simple Universal Prompt System - เฉพาะที่จำเป็น"""
    
    def __init__(self):
        """🏗️ Initialize เฉพาะที่จำเป็น"""
        self.company_templates = self._load_simple_templates()
        self.generation_stats = {'total': 0, 'success': 0}
        logger.info("✅ Simple Universal Prompt System initialized")
    
    # ========================================================================
    # 🎯 CORE METHODS (เฉพาะ 5 ตัวที่จำเป็น)
    # ========================================================================
    
    async def generate_prompt(self, question: str, tenant_id: str, agent=None) -> Tuple[str, Dict[str, Any]]:
        """🎯 1. Main prompt generation method"""
        
        self.generation_stats['total'] += 1
        
        try:
            # Get company template
            template = self._get_company_template(tenant_id)
            
            # Detect question type
            question_type = self._detect_question_type(question)
            
            # Format prompt
            prompt = self._format_prompt(template, question, question_type)
            
            # Create metadata
            metadata = {
                'method': 'simple_universal_prompt',
                'template_used': f'{tenant_id}_template',
                'question_type': question_type,
                'confidence': 'high',
                'processing_time': datetime.now().isoformat()
            }
            
            self.generation_stats['success'] += 1
            
            return prompt, metadata
            
        except Exception as e:
            logger.error(f"Prompt generation failed: {e}")
            
            # Fallback prompt
            fallback_prompt = f"Generate PostgreSQL query for: {question}"
            fallback_metadata = {
                'method': 'simple_fallback',
                'error': str(e),
                'confidence': 'low'
            }
            
            return fallback_prompt, fallback_metadata
    
    def _get_company_template(self, tenant_id: str) -> str:
        """🎯 2. Get company-specific template"""
        
        return self.company_templates.get(tenant_id, self.company_templates['default'])
    
    def _detect_question_type(self, question: str) -> str:
        """🎯 3. Simple question type detection"""
        
        question_lower = question.lower()
        
        # Assignment analysis
        if any(word in question_lower for word in ['รับผิดชอบ', 'ทำงาน', 'assign', 'work on']):
            return 'assignment'
        
        # Project queries
        elif any(word in question_lower for word in ['โปรเจค', 'project']):
            return 'project'
        
        # Employee queries
        elif any(word in question_lower for word in ['พนักงาน', 'employee', 'กี่คน']):
            return 'employee'
        
        # Budget/Financial
        elif any(word in question_lower for word in ['งบประมาณ', 'budget', 'เงินเดือน', 'salary']):
            return 'financial'
        
        # Tourism specific (for company-b)
        elif any(word in question_lower for word in ['ท่องเที่ยว', 'tourism', 'โรงแรม', 'hotel']):
            return 'tourism'
        
        else:
            return 'general'
    
    def _format_prompt(self, template: str, question: str, question_type: str) -> str:
        """🎯 4. Format prompt with question and type"""
        
        # Add question type specific hints
        type_hints = {
            'assignment': "\n💡 Hints: ใช้ LEFT JOIN เพื่อแสดงพนักงานทั้งหมด, ใช้ COALESCE สำหรับ NULL",
            'project': "\n💡 Hints: เน้นข้อมูล budget, status, client",
            'employee': "\n💡 Hints: GROUP BY department, COUNT(*) สำหรับจำนวน",
            'financial': "\n💡 Hints: แสดงตัวเลขเป็น 'XXX,XXX บาท', SUM/AVG สำหรับสถิติ",
            'tourism': "\n💡 Hints: มองหาโปรเจคที่เกี่ยวข้องกับ tourism, hospitality, travel",
            'general': "\n💡 Hints: ใช้ LIMIT 20, ORDER BY สำหรับเรียงลำดับ"
        }
        
        hint = type_hints.get(question_type, type_hints['general'])
        
        return template.format(
            question=question,
            question_type=question_type,
            type_hints=hint
        )
    
    def _load_simple_templates(self) -> Dict[str, str]:
        """🎯 5. Load simple company templates"""
        
        return {
            'company-a': """คุณคือ PostgreSQL Expert สำหรับ SiamTech Main Office (Enterprise Banking)

🏢 บริบท: ระบบธนาคารและองค์กรขนาดใหญ่
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: Performance, Banking Systems, E-commerce

📊 โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🔧 กฎ SQL สำหรับ Enterprise:
1. ใช้ LEFT JOIN สำหรับ assignment queries
2. ใช้ COALESCE(p.name, 'ไม่มีโปรเจค') สำหรับ NULL
3. แสดงเงิน: TO_CHAR(amount, 'FM999,999,999') || ' บาท'
4. ใช้ ILIKE สำหรับ text search
5. ใส่ LIMIT 20 เสมอ

ประเภทคำถาม: {question_type}
{type_hints}

คำถาม: {question}

สร้าง PostgreSQL query:""",

            'company-b': """คุณคือ PostgreSQL Expert สำหรับ SiamTech Chiang Mai Regional (Tourism & Hospitality)

🏨 บริบท: เทคโนโลยีท่องเที่ยวและโรงแรม ภาคเหนือ
💰 สกุลเงิน: บาท (THB)
🎯 เน้น: Tourism Systems, Local Business, Cultural Integration

📊 โครงสร้างฐานข้อมูล:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🏔️ ลูกค้าหลัก: โรงแรม, TAT, สวนพฤกษศาสตร์, ร้านอาหาร, มหาวิทยาลัย

🔧 กฎ SQL สำหรับ Tourism:
1. มองหา keywords: ท่องเที่ยว, โรงแรม, tourism, hotel
2. ใช้ ILIKE '%ท่องเที่ยว%', '%โรงแรม%' สำหรับค้นหา
3. งบประมาณ: 300k-800k บาท (โปรเจคระดับภูมิภาค)
4. ใช้ LEFT JOIN และ COALESCE เหมือน enterprise
5. ใส่ LIMIT 20 เสมอ

ประเภทคำถาม: {question_type}
{type_hints}

คำถาม: {question}

สร้าง PostgreSQL query:""",

            'company-c': """You are a PostgreSQL Expert for SiamTech International (Global Operations)

🌍 Context: International software solutions, cross-border projects
💰 Currency: USD and multi-currency support
🎯 Focus: Global Platforms, International Compliance, Multi-region

📊 Database Schema:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🌎 Key Clients: International corporations, global banks, multinational companies

🔧 SQL Rules for International:
1. Look for keywords: international, global, USD, overseas
2. Use ILIKE '%international%', '%global%' for search
3. Budget: Multi-million USD projects (large scale)
4. Use LEFT JOIN and COALESCE like other companies
5. Always include LIMIT 20

Question Type: {question_type}
{type_hints}

Question: {question}

Generate PostgreSQL query:""",

            'default': """คุณคือ PostgreSQL Expert

📊 Database Schema:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation

🔧 SQL Rules:
1. ใช้ LEFT JOIN สำหรับ assignment queries
2. ใช้ COALESCE สำหรับ NULL handling
3. ใส่ LIMIT 20 เสมอ

ประเภทคำถาม: {question_type}
{type_hints}

คำถาม: {question}

สร้าง PostgreSQL query:"""
        }
    
    # ========================================================================
    # 🔧 SIMPLE HELPER METHODS (ไม่นับเป็น core methods)
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simple statistics"""
        
        success_rate = 0
        if self.generation_stats['total'] > 0:
            success_rate = (self.generation_stats['success'] / self.generation_stats['total']) * 100
        
        return {
            'total_queries_processed': self.generation_stats['total'],
            'successful_generations': self.generation_stats['success'],
            'success_rate_percentage': round(success_rate, 2),
            'companies_supported': 3,
            'templates_available': len(self.company_templates),
            'system_version': 'simple_v1.0'
        }
    
    def list_supported_companies(self) -> List[Dict[str, str]]:
        """List supported companies"""
        
        return [
            {'id': 'company-a', 'name': 'SiamTech Main Office', 'business_type': 'enterprise', 'language': 'th'},
            {'id': 'company-b', 'name': 'SiamTech Chiang Mai Regional', 'business_type': 'tourism_hospitality', 'language': 'th'},
            {'id': 'company-c', 'name': 'SiamTech International', 'business_type': 'global_operations', 'language': 'en'}
        ]
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (เพื่อความเข้ากันได้กับระบบเดิม)
    # ========================================================================
    
    async def generate_sql_with_universal_prompt(self, question: str, tenant_id: str, agent=None) -> Tuple[str, Dict[str, Any]]:
        """Compatibility method for existing code"""
        
        # Generate prompt
        prompt, metadata = await self.generate_prompt(question, tenant_id, agent)
        
        # If agent is provided, use it to generate SQL
        if agent and hasattr(agent, 'ai_service'):
            try:
                config = agent.tenant_configs[tenant_id]
                ai_response = await agent.ai_service.call_ollama_api(
                    config, prompt, temperature=0.1
                )
                
                # Extract SQL from response
                sql_query = self._extract_sql_from_response(ai_response)
                
                return sql_query, metadata
                
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                return "SELECT 'AI generation failed' as error", metadata
        
        # If no agent, return the prompt as SQL (for testing)
        return f"-- Generated from prompt --\nSELECT '{question}' as query_intent", metadata
    
    def _extract_sql_from_response(self, ai_response: str) -> str:
        """Extract SQL from AI response"""
        
        import re
        
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

