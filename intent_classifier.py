# 🏗️ Scalable Intent Classifier for 20+ Companies
# Designed to work with ANY company database schema

import re
import json
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@dataclass
class BusinessContext:
    """📊 Business context extracted from actual schema"""
    table_names: Set[str]
    column_names: Set[str]
    text_columns: Set[str]      # columns that likely contain names/descriptions
    numeric_columns: Set[str]   # columns that likely contain numbers
    date_columns: Set[str]      # columns that likely contain dates
    key_entities: Set[str]      # important business entities detected

class SchemaAnalyzer:
    """🔍 Analyzes any database schema to understand business context"""
    
    @staticmethod
    def analyze_schema(schema: Dict[str, List[str]]) -> BusinessContext:
        """📊 Extract business context from ANY schema"""
        
        table_names = set(schema.keys())
        column_names = set()
        text_columns = set()
        numeric_columns = set()
        date_columns = set()
        key_entities = set()
        
        for table, columns in schema.items():
            column_names.update(columns)
            
            # Add table name as key entity
            key_entities.add(table.lower())
            
            for column in columns:
                col_lower = column.lower()
                
                # Classify column types by patterns
                if any(pattern in col_lower for pattern in ['name', 'title', 'description', 'note']):
                    text_columns.add(column)
                    
                elif any(pattern in col_lower for pattern in ['amount', 'price', 'cost', 'salary', 'budget', 'count', 'number', 'quantity']):
                    numeric_columns.add(column)
                    
                elif any(pattern in col_lower for pattern in ['date', 'time', 'created', 'updated', 'start', 'end']):
                    date_columns.add(column)
                
                # Extract business entities from column names
                # Remove common suffixes to get base entity
                base_name = re.sub(r'(_id|_name|_date|_count|_amount)$', '', col_lower)
                if len(base_name) > 2:  # Avoid very short names
                    key_entities.add(base_name)
        
        return BusinessContext(
            table_names=table_names,
            column_names=column_names,
            text_columns=text_columns,
            numeric_columns=numeric_columns,
            date_columns=date_columns,
            key_entities=key_entities
        )

class UniversalIntentClassifier:
    """🌍 Universal Intent Classifier that works with ANY company/schema"""
    
    def __init__(self):
        # Universal conversational patterns (language-agnostic)
        self.conversational_patterns = {
            'greeting': [
                r'^(สวัสดี|hello|hi|hey|good morning|good afternoon|good evening)',
                r'^(greetings|hola|bonjour|guten tag|konnichiwa|namaste)'
            ],
            'thanks': [
                r'^(ขอบคุณ|thank you|thanks|thx|merci|grazie|danke|arigato)',
                r'(appreciate|grateful)'
            ],
            'identity': [
                r'(คุณคือใคร|คุณเป็นใคร|who are you|what are you)',
                r'(tell me about yourself|introduce yourself)',
                r'(คุณชื่ออะไร|what.*your name)'
            ],
            'help': [
                r'(ช่วย.*ได้.*อะไร|help.*me|can you help)',
                r'(สามารถ.*ช่วย|what can you do|how.*help)',
                r'(ขอความช่วยเหลือ|need help|assistance)'
            ],
            'capability': [
                r'(ทำอะไรได้|what.*can.*do|capabilities)',
                r'(functions|features|abilities)'
            ],
            'goodbye': [
                r'^(ลาก่อน|bye|goodbye|see you|good night|farewell)',
                r'(talk.*later|until.*next|adios|au revoir)'
            ],
            'status': [
                r'(เป็นยังไง|สบายดีไหม|how are you|how.*going)',
                r'(what.*up|how.*things|comment.*va)'
            ]
        }
        
        # Universal SQL indicator patterns (schema-agnostic)
        self.sql_patterns = {
            'counting': [
                r'(กี่|จำนวน|รวม|how many|count|total|number of)',
                r'(มี.*กี่|กี่.*มี|how much|quantity)'
            ],
            'identification': [
                r'(ใคร|ใครคือ|ใครเป็น|who|which person|what person)',
                r'(คนไหน|บุคคลใด|individual|person)'
            ],
            'comparison': [
                r'(สูงสุด|ต่ำสุด|มากที่สุด|น้อยที่สุด)',
                r'(highest|lowest|maximum|minimum|most|least)',
                r'(ดีที่สุด|แย่ที่สุด|best|worst|top|bottom)',
                r'(เปรียบเทียบ|compare|versus|vs|against)'
            ],
            'filtering': [
                r'(ที่มี|ที่เป็น|ซึ่ง|where|with|having)',
                r'(เฉพาะ|แค่|only|just|specific)'
            ],
            'sorting': [
                r'(เรียง|จัด|sort|order|arrange)',
                r'(ascending|descending|asc|desc|เรียงตาม)'
            ],
            'aggregation': [
                r'(เฉลี่ย|รวม|สรุป|average|sum|total|aggregate)',
                r'(mean|median|standard|deviation)'
            ],
            'temporal': [
                r'(วันนี้|เมื่อไหร่|เมื่อใด|today|yesterday|when)',
                r'(ล่าสุด|ใหม่สุด|เก่าสุด|latest|newest|oldest|recent)'
            ]
        }
    
    def classify_intent(self, question: str, business_context: Optional[BusinessContext] = None) -> Dict[str, Any]:
        """🎯 Universal intent classification that works with any company"""
        
        if not question or len(question.strip()) == 0:
            return self._create_response('conversation', 0.9, 'Empty question')
        
        question_lower = question.lower().strip()
        
        # 1. Check conversational patterns (highest priority)
        conv_result = self._check_conversational_patterns(question_lower)
        if conv_result['confidence'] > 0.8:
            return conv_result
        
        # 2. Check for SQL indicators
        sql_result = self._check_sql_patterns(question_lower)
        
        # 3. If we have business context, use it to boost confidence
        if business_context:
            business_boost = self._analyze_business_context_match(question_lower, business_context)
            if business_boost > 0:
                sql_result['confidence'] = min(0.95, sql_result['confidence'] + business_boost)
                sql_result['reasoning'] += f" + business context match ({business_boost:.1f})"
        
        # 4. Final decision
        if sql_result['confidence'] > 0.3:
            return sql_result
        
        # 5. Default to conversation
        return self._create_response(
            'conversation',
            0.7,
            'No clear SQL indicators, defaulting to conversation'
        )
    
    def _check_conversational_patterns(self, question: str) -> Dict[str, Any]:
        """💬 Check for conversational patterns"""
        
        for category, patterns in self.conversational_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return self._create_response(
                        'conversation',
                        0.95,
                        f'Matched conversational pattern: {category}'
                    )
        
        return self._create_response('unknown', 0.0, 'No conversational patterns')
    
    def _check_sql_patterns(self, question: str) -> Dict[str, Any]:
        """🗄️ Check for SQL indicator patterns"""
        
        confidence = 0.0
        matched_patterns = []
        
        for category, patterns in self.sql_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    confidence += 0.15
                    matched_patterns.append(category)
        
        if confidence > 0:
            # Remove duplicates but preserve order
            unique_patterns = list(dict.fromkeys(matched_patterns))
            return self._create_response(
                'business_query',
                min(0.9, confidence),
                f'SQL patterns detected: {unique_patterns}'
            )
        
        return self._create_response('unknown', 0.0, 'No SQL patterns')
    
    def _analyze_business_context_match(self, question: str, context: BusinessContext) -> float:
        """🏢 Analyze how well question matches business context"""
        
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        
        # Check matches with business entities
        entity_matches = len(question_words & context.key_entities)
        table_matches = len(question_words & {t.lower() for t in context.table_names})
        column_matches = len(question_words & {c.lower() for c in context.column_names})
        
        # Calculate boost based on matches
        total_matches = entity_matches + table_matches + column_matches
        
        if total_matches >= 3:
            return 0.3  # Strong business context
        elif total_matches >= 2:
            return 0.2  # Medium business context
        elif total_matches >= 1:
            return 0.1  # Weak business context
        
        return 0.0  # No business context
    
    def _create_response(self, intent: str, confidence: float, reasoning: str) -> Dict[str, Any]:
        """📝 Create standardized response"""
        
        should_use_sql = intent in ['business_query', 'data_query']
        
        return {
            'intent': intent,
            'confidence': confidence,
            'should_use_sql': should_use_sql,
            'reasoning': reasoning,
            'classifier_version': 'universal_1.0'
        }

class AdaptiveConversationalGenerator:
    """💬 Adaptive conversational response generator that works with any company"""
    
    def __init__(self):
        self.response_templates = {
            'greeting': {
                'th': """สวัสดีครับ! 😊

ผมคือ AI Assistant ของ {company_name} 

🤖 **สิ่งที่ผมช่วยได้:**
• วิเคราะห์ข้อมูลและตอบคำถามเกี่ยวกับธุรกิจ
• ค้นหาข้อมูลจากฐานข้อมูลของบริษัท
• สร้างรายงานและสถิติต่างๆ

📊 **ข้อมูลที่มีในระบบ:**
{available_data}

💡 **ตัวอย่างคำถาม:**
{example_questions}

มีอะไรให้ผมช่วยไหมครับ? 🚀""",

                'en': """Hello! 😊

I'm the AI Assistant for {company_name}

🤖 **How I can help:**
• Analyze data and answer business questions
• Search information from company databases
• Generate reports and statistics

📊 **Available data in the system:**
{available_data}

💡 **Example questions:**
{example_questions}

How can I help you today? 🚀"""
            },
            
            'help': {
                'th': """แน่นอนครับ! ผมยินดีช่วยเหลือ 😊

**📊 ประเภทคำถามที่ถามได้:**

🔢 **คำถามเชิงปริมาณ:**
{count_examples}

👥 **คำถามเกี่ยวกับบุคคล/หน่วยงาน:**
{people_examples}

💰 **คำถามเกี่ยวกับตัวเลข:**
{numeric_examples}

📋 **คำถามเกี่ยวกับสถานะ:**
{status_examples}

**เริ่มถามได้เลยครับ! 🚀**""",

                'en': """Of course! I'm happy to help 😊

**📊 Types of questions you can ask:**

🔢 **Quantitative questions:**
{count_examples}

👥 **People/Organization questions:**
{people_examples}

💰 **Numerical questions:**
{numeric_examples}

📋 **Status questions:**
{status_examples}

**Feel free to start asking! 🚀**"""
            }
        }
    
    def generate_response(self, question: str, company_name: str, 
                         business_context: Optional[BusinessContext] = None,
                         language: str = 'th') -> Dict[str, Any]:
        """💬 Generate adaptive conversational response"""
        
        question_lower = question.lower()
        
        # Determine response type
        if any(word in question_lower for word in ['สวัสดี', 'hello', 'hi']):
            response_type = 'greeting'
        elif any(word in question_lower for word in ['ช่วย', 'help']):
            response_type = 'help'
        elif any(word in question_lower for word in ['ขอบคุณ', 'thank']):
            return self._generate_thanks_response(language)
        elif any(word in question_lower for word in ['คุณคือใคร', 'who are you']):
            return self._generate_identity_response(company_name, language)
        else:
            return self._generate_default_response(company_name, business_context, language)
        
        # Generate contextual response
        template = self.response_templates[response_type][language]
        
        # Fill in dynamic content based on business context
        if business_context:
            available_data = self._format_available_data(business_context, language)
            example_questions = self._generate_example_questions(business_context, language)
        else:
            available_data = "• ข้อมูลธุรกิจทั่วไป" if language == 'th' else "• General business data"
            example_questions = "• มีข้อมูลอะไรบ้าง?" if language == 'th' else "• What data is available?"
        
        if response_type == 'greeting':
            answer = template.format(
                company_name=company_name,
                available_data=available_data,
                example_questions=example_questions
            )
        elif response_type == 'help':
            examples = self._generate_help_examples(business_context, language)
            answer = template.format(**examples)
        else:
            answer = template
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": "adaptive_conversational",
            "company_name": company_name,
            "language": language,
            "response_type": response_type,
            "sql_used": False
        }
    
    def _format_available_data(self, context: BusinessContext, language: str) -> str:
        """📊 Format available data description"""
        
        if language == 'th':
            items = []
            for table in sorted(context.table_names):
                items.append(f"• ข้อมูล{table}")
            return "\n".join(items[:5])  # Limit to 5 items
        else:
            items = []
            for table in sorted(context.table_names):
                items.append(f"• {table.title()} data")
            return "\n".join(items[:5])
    
    def _generate_example_questions(self, context: BusinessContext, language: str) -> str:
        """💡 Generate relevant example questions"""
        
        examples = []
        
        if language == 'th':
            # Generate based on available tables
            if 'employees' in context.table_names or 'staff' in context.table_names:
                examples.append("• มีพนักงานกี่คน?")
            if 'projects' in context.table_names:
                examples.append("• โปรเจคไหนสำคัญที่สุด?")
            if 'customers' in context.table_names or 'clients' in context.table_names:
                examples.append("• ลูกค้าใหม่มีกี่ราย?")
            if not examples:
                examples = ["• มีข้อมูลอะไรบ้าง?", "• สามารถวิเคราะห์อะไรได้บ้าง?"]
        else:
            if 'employees' in context.table_names or 'staff' in context.table_names:
                examples.append("• How many employees do we have?")
            if 'projects' in context.table_names:
                examples.append("• Which project is most important?")
            if 'customers' in context.table_names or 'clients' in context.table_names:
                examples.append("• How many new customers?")
            if not examples:
                examples = ["• What data is available?", "• What can you analyze?"]
        
        return "\n".join(examples[:3])
    
    def _generate_help_examples(self, context: BusinessContext, language: str) -> Dict[str, str]:
        """🔧 Generate help examples based on context"""
        
        if language == 'th':
            return {
                'count_examples': "• มีข้อมูลกี่รายการ?\n• จำนวนทั้งหมดเท่าไหร่?",
                'people_examples': "• ใครเป็นผู้รับผิดชอบ?\n• ทีมไหนดูแลเรื่องนี้?",
                'numeric_examples': "• มูลค่าสูงสุดคือเท่าไหร่?\n• เฉลี่ยอยู่ที่เท่าไหร่?",
                'status_examples': "• สถานะปัจจุบันเป็นอย่างไร?\n• ความคืบหน้าถึงไหนแล้ว?"
            }
        else:
            return {
                'count_examples': "• How many records are there?\n• What's the total count?",
                'people_examples': "• Who is responsible?\n• Which team handles this?",
                'numeric_examples': "• What's the highest value?\n• What's the average?",
                'status_examples': "• What's the current status?\n• What's the progress?"
            }
    
    def _generate_thanks_response(self, language: str) -> Dict[str, Any]:
        """🙏 Generate thanks response"""
        
        if language == 'th':
            answer = "ยินดีครับ! 😊 หากมีคำถามอื่นๆ เกี่ยวกับข้อมูลบริษัท สามารถถามผมได้ตลอดเวลานะครับ 🚀"
        else:
            answer = "You're welcome! 😊 If you have any other questions about company data, feel free to ask anytime! 🚀"
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": "conversational_thanks",
            "sql_used": False,
            "language": language
        }
    
    def _generate_identity_response(self, company_name: str, language: str) -> Dict[str, Any]:
        """🤖 Generate identity response"""
        
        if language == 'th':
            answer = f"""ผมคือ AI Assistant ที่ออกแบบมาเฉพาะสำหรับ {company_name} ครับ 🤖

**ความสามารถหลักของผม:**
• 📊 วิเคราะห์ข้อมูลจากฐานข้อมูลบริษัท
• 🔍 ค้นหาข้อมูลและตอบคำถามทางธุรกิจ
• 📈 สร้างรายงานและข้อมูลเชิงลึก
• 💡 ให้คำแนะนำสำหรับการตัดสินใจ

ผมใช้เทคโนโลยี AI ขั้นสูงในการเข้าใจคำถามและดึงข้อมูลที่เกี่ยวข้องมาตอบครับ ✨"""
        else:
            answer = f"""I'm an AI Assistant specifically designed for {company_name} 🤖

**My main capabilities:**
• 📊 Analyze data from company databases
• 🔍 Search information and answer business questions
• 📈 Generate reports and insights
• 💡 Provide recommendations for decision making

I use advanced AI technology to understand questions and retrieve relevant data to provide answers ✨"""
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": "conversational_identity",
            "company_name": company_name,
            "sql_used": False,
            "language": language
        }
    
    def _generate_default_response(self, company_name: str, 
                                  context: Optional[BusinessContext], 
                                  language: str) -> Dict[str, Any]:
        """🔄 Generate default conversational response"""
        
        if language == 'th':
            answer = f"""ขอบคุณสำหรับคำถามครับ! 😊

ผมเป็น AI Assistant ที่เชี่ยวชาญในการวิเคราะห์ข้อมูลของ {company_name}

หากคุณต้องการทราบข้อมูลเกี่ยวกับธุรกิจ กรุณาถามคำถามที่เฉพาะเจาะจงหน่อยครับ แล้วผมจะช่วยวิเคราะห์ข้อมูลให้ทันที! 🚀

ตัวอย่าง: "มีข้อมูลอะไりบ้าง?" หรือ "สรุปสถานการณ์ปัจจุบัน"
"""
        else:
            answer = f"""Thank you for your question! 😊

I'm an AI Assistant specialized in analyzing data for {company_name}

If you need information about the business, please ask more specific questions, and I'll analyze the data for you immediately! 🚀

Examples: "What data is available?" or "Current situation summary"
"""
        
        return {
            "answer": answer,
            "success": True,
            "data_source_used": "conversational_default",
            "company_name": company_name,
            "sql_used": False,
            "language": language
        }

# 🧪 Testing Framework
def test_universal_classifier():
    """🧪 Test with various company schemas"""
    
    # Test schemas from different industries
    test_schemas = {
        'tech_company': {
            'employees': ['id', 'name', 'position', 'department', 'salary'],
            'projects': ['id', 'name', 'budget', 'status', 'manager_id'],
            'clients': ['id', 'company_name', 'industry', 'contact_person']
        },
        'hospital': {
            'patients': ['id', 'name', 'age', 'diagnosis', 'doctor_id'],
            'doctors': ['id', 'name', 'specialization', 'department'],
            'appointments': ['id', 'patient_id', 'doctor_id', 'appointment_date'],
            'wards': ['id', 'name', 'capacity', 'head_nurse_id']
        },
        'restaurant': {
            'menu_items': ['id', 'name', 'category', 'price', 'chef_id'],
            'orders': ['id', 'table_number', 'customer_name', 'total_amount'],
            'staff': ['id', 'name', 'role', 'shift', 'hourly_rate'],
            'tables': ['id', 'number', 'capacity', 'status']
        },
        'school': {
            'students': ['id', 'name', 'grade', 'class_id', 'guardian_contact'],
            'teachers': ['id', 'name', 'subject', 'experience_years'],
            'classes': ['id', 'name', 'grade_level', 'teacher_id'],
            'subjects': ['id', 'name', 'department', 'credits']
        }
    }
    
    test_questions = [
        # Conversational (should work for all)
        "สวัสดีครับ",
        "Hello there",
        "คุณคือใคร",
        "What can you help with?",
        "ขอบคุณมากครับ",
        
        # Business queries (should work for all with context)
        "มีข้อมูลกี่รายการ",  # counting
        "ใครเป็นผู้รับผิดชอบ",  # identification
        "อะไรสำคัญที่สุด",      # comparison
        "สถานการณ์ปัจจุบัน",   # status
        
        # Industry-specific (should work with context)
        "How many patients today?",      # hospital
        "กี่คนในครัว",                   # restaurant  
        "นักเรียนชั้น 3 มีกี่คน",        # school
        "โปรเจคไหนกำลังทำ"               # tech
    ]
    
    classifier = UniversalIntentClassifier()
    analyzer = SchemaAnalyzer()
    
    print("🧪 Testing Universal Intent Classifier")
    print("=" * 70)
    
    for schema_name, schema in test_schemas.items():
        print(f"\n🏢 Testing with {schema_name.upper()} schema:")
        print("-" * 50)
        
        # Analyze business context
        business_context = analyzer.analyze_schema(schema)
        print(f"📊 Entities detected: {list(business_context.key_entities)[:5]}")
        
        for question in test_questions[:8]:  # Test subset
            result = classifier.classify_intent(question, business_context)
            
            intent = result['intent']
            confidence = result['confidence']
            use_sql = result['should_use_sql']
            
            status = "💬" if intent == 'conversation' else "🗄️"
            print(f"{status} {question:<25} | {intent:<15} | SQL:{str(use_sql):<5} | {confidence:.2f}")

if __name__ == "__main__":
    test_universal_classifier()