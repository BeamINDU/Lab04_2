import re
from typing import Dict, Any, List, Tuple, Set, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IntentContext:
    """Context for intent classification"""
    available_tables: Set[str]
    available_columns: Set[str]
    business_concepts: Set[str]
    tenant_language: str
    business_type: str

class EnterpriseIntentClassifier:
    """🧠 Schema-aware dynamic intent classifier"""
    
    def __init__(self, enterprise_validator=None):
        self.enterprise_validator = enterprise_validator
        self._intent_cache = {}  # Cache for performance
        
    def classify_intent(self, question: str, tenant_id: str = None, context: IntentContext = None) -> Dict[str, Any]:
        """🎯 Dynamic intent classification using actual schema"""
        
        question_lower = question.lower().strip()
        
        # 1. 🏗️ Get dynamic context from enterprise validator
        if not context and self.enterprise_validator and tenant_id:
            context = self._get_dynamic_context(tenant_id)
        
        if not context:
            # Fallback to basic classification
            return self._basic_intent_classification(question_lower)
        
        # 2. 🔍 Schema-aware classification
        return self._schema_aware_classification(question_lower, context)
    
    def _get_dynamic_context(self, tenant_id: str) -> Optional[IntentContext]:
        """🔍 Get dynamic context from enterprise schema discovery"""
        try:
            if not self.enterprise_validator._initialized:
                return None
                
            if tenant_id not in self.enterprise_validator.schema_service.discovered_schemas:
                return None
            
            schema = self.enterprise_validator.schema_service.discovered_schemas[tenant_id]
            tenant_config = self.enterprise_validator.schema_service.tenant_configs[tenant_id]
            
            # Extract available tables and columns
            available_tables = set(schema.tables.keys())
            available_columns = set()
            
            for table_name, columns in schema.tables.items():
                available_columns.update(columns)
            
            # Generate business concepts from schema
            business_concepts = self._generate_business_concepts_from_schema(schema)
            
            return IntentContext(
                available_tables=available_tables,
                available_columns=available_columns,
                business_concepts=business_concepts,
                tenant_language=tenant_config.language,
                business_type=tenant_config.business_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to get dynamic context: {e}")
            return None
    
    def _generate_business_concepts_from_schema(self, schema) -> Set[str]:
        """🏢 Generate business concepts from actual database schema"""
        concepts = set()
        
        for table_name, columns in schema.tables.items():
            # Add table concepts
            concepts.add(table_name)
            
            # Add column concepts
            for column in columns:
                concepts.add(column)
                
                # Map columns to business concepts
                column_lower = column.lower()
                
                if 'salary' in column_lower or 'pay' in column_lower:
                    concepts.update(['เงินเดือน', 'ค่าจ้าง', 'ค่าตอบแทน', 'salary', 'pay', 'compensation'])
                
                elif 'budget' in column_lower or 'cost' in column_lower:
                    concepts.update(['งบประมาณ', 'บัดเจต', 'ค่าใช้จ่าย', 'budget', 'cost', 'expense'])
                
                elif 'name' in column_lower:
                    concepts.update(['ชื่อ', 'รายชื่อ', 'name', 'title'])
                
                elif 'department' in column_lower:
                    concepts.update(['แผนก', 'ฝ่าย', 'หน่วยงาน', 'department', 'division', 'unit'])
                
                elif 'position' in column_lower or 'role' in column_lower:
                    concepts.update(['ตำแหน่ง', 'หน้าที่', 'บทบาท', 'position', 'role', 'job'])
                
                elif 'project' in column_lower:
                    concepts.update(['โปรเจค', 'โครงการ', 'งาน', 'project', 'work', 'task'])
                
                elif 'client' in column_lower or 'customer' in column_lower:
                    concepts.update(['ลูกค้า', 'คลื่น', 'client', 'customer'])
                
                elif 'status' in column_lower:
                    concepts.update(['สถานะ', 'สถานการณ์', 'status', 'state', 'condition'])
        
        return concepts
    
    def _schema_aware_classification(self, question: str, context: IntentContext) -> Dict[str, Any]:
        """🎯 Classify intent using actual schema awareness"""
        
        # 1. 🚨 High Priority: Employee/Person Queries (who questions)
        who_patterns = self._get_dynamic_who_patterns(context.tenant_language)
        if any(pattern in question for pattern in who_patterns):
            # Check if it's asking about people in context of business data
            if self._has_business_context(question, context.business_concepts):
                return {
                    'intent': 'employee_who_query',
                    'confidence': 0.95,
                    'should_use_sql': True,
                    'reasoning': 'Who question with business context detected',
                    'detected_concepts': self._extract_matching_concepts(question, context.business_concepts)
                }
        
        # 2. 🔢 Count/Quantity Queries
        count_patterns = self._get_dynamic_count_patterns(context.tenant_language)
        if any(pattern in question for pattern in count_patterns):
            if self._has_business_context(question, context.business_concepts):
                return {
                    'intent': 'count_query',
                    'confidence': 0.9,
                    'should_use_sql': True,
                    'reasoning': 'Count question with business context',
                    'detected_concepts': self._extract_matching_concepts(question, context.business_concepts)
                }
        
        # 3. 🔍 Data Lookup Queries
        lookup_patterns = self._get_dynamic_lookup_patterns(context.tenant_language)
        if any(pattern in question for pattern in lookup_patterns):
            if self._has_business_context(question, context.business_concepts):
                return {
                    'intent': 'data_lookup_query',
                    'confidence': 0.85,
                    'should_use_sql': True,
                    'reasoning': 'Data lookup with business context',
                    'detected_concepts': self._extract_matching_concepts(question, context.business_concepts)
                }
        
        # 4. 📊 Analysis/Comparison Queries
        analysis_patterns = self._get_dynamic_analysis_patterns(context.tenant_language)
        if any(pattern in question for pattern in analysis_patterns):
            if self._has_business_context(question, context.business_concepts):
                return {
                    'intent': 'analysis_query',
                    'confidence': 0.8,
                    'should_use_sql': True,
                    'reasoning': 'Analysis question with business context',
                    'detected_concepts': self._extract_matching_concepts(question, context.business_concepts)
                }
        
        # 5. 💬 Check if it's genuinely conversational
        if self._is_genuine_conversation(question, context):
            return {
                'intent': 'conversation',
                'confidence': 0.9,
                'should_use_sql': False,
                'reasoning': 'Genuine conversational intent detected'
            }
        
        # 6. 🏗️ Default: If it mentions business concepts, try SQL
        if self._has_business_context(question, context.business_concepts):
            return {
                'intent': 'general_business_query',
                'confidence': 0.7,
                'should_use_sql': True,
                'reasoning': 'Contains business concepts from schema',
                'detected_concepts': self._extract_matching_concepts(question, context.business_concepts)
            }
        
        # 7. ❓ Unknown intent
        return {
            'intent': 'unknown',
            'confidence': 0.5,
            'should_use_sql': False,
            'reasoning': 'No clear intent or business context detected'
        }
    
    def _get_dynamic_who_patterns(self, language: str) -> List[str]:
        """🔍 Dynamic who patterns based on language"""
        if language == 'th':
            return [
                'ใครคือ', 'ใครเป็น', 'ใครทำงาน', 'ใครรับผิดชอบ', 'ใครดูแล',
                'พนักงานคนไหน', 'คนไหน', 'ผู้ใด', 'บุคคลใด',
                'ผู้นำ', 'หัวหน้า', 'ผู้จัดการ', 'ผู้รับผิดชอบ',
                'ทีม', 'กลุ่ม', 'สมาชิก'
            ]
        else:  # English
            return [
                'who is', 'who are', 'who works', 'who manages', 'who leads',
                'which employee', 'which person', 'what person',
                'team member', 'staff member', 'leader', 'manager', 'head'
            ]
    
    def _get_dynamic_count_patterns(self, language: str) -> List[str]:
        """🔢 Dynamic count patterns"""
        if language == 'th':
            return [
                'กี่คน', 'จำนวน', 'เท่าไหร่', 'มากน้อย', 'เป็นจำนวน',
                'ทั้งหมด', 'รวม', 'นับ'
            ]
        else:
            return [
                'how many', 'how much', 'count', 'total', 'number of',
                'quantity', 'amount'
            ]
    
    def _get_dynamic_lookup_patterns(self, language: str) -> List[str]:
        """🔍 Dynamic lookup patterns"""
        if language == 'th':
            return [
                'ไหน', 'อะไร', 'ใด', 'รายการ', 'รายชื่อ', 'ข้อมูล',
                'แสดง', 'ดู', 'ค้นหา', 'หา'
            ]
        else:
            return [
                'what', 'which', 'show', 'list', 'find', 'search',
                'get', 'retrieve', 'display'
            ]
    
    def _get_dynamic_analysis_patterns(self, language: str) -> List[str]:
        """📊 Dynamic analysis patterns"""
        if language == 'th':
            return [
                'สูงสุด', 'ต่ำสุด', 'มากที่สุด', 'น้อยที่สุด',
                'เปรียบเทียบ', 'แตกต่าง', 'เหมือน', 'ความแตกต่าง',
                'วิเคราะห์', 'สถิติ', 'เฉลี่ย'
            ]
        else:
            return [
                'highest', 'lowest', 'maximum', 'minimum', 'most', 'least',
                'compare', 'comparison', 'difference', 'similar',
                'analyze', 'analysis', 'statistics', 'average'
            ]
    
    def _has_business_context(self, question: str, business_concepts: Set[str]) -> bool:
        """🏢 Check if question has business context using schema concepts"""
        question_lower = question.lower()
        
        # Check for direct concept matches
        for concept in business_concepts:
            if concept.lower() in question_lower:
                return True
        
        # Check for partial matches (for compound words)
        for concept in business_concepts:
            if len(concept) > 3:  # Only check longer concepts
                concept_lower = concept.lower()
                if concept_lower in question_lower or question_lower in concept_lower:
                    return True
        
        return False
    
    def _extract_matching_concepts(self, question: str, business_concepts: Set[str]) -> List[str]:
        """🔍 Extract matching business concepts from question"""
        question_lower = question.lower()
        matches = []
        
        for concept in business_concepts:
            if concept.lower() in question_lower:
                matches.append(concept)
        
        return matches
    
    def _is_genuine_conversation(self, question: str, context: IntentContext) -> bool:
        """💬 Check if it's genuine conversation (not business query)"""
        question_lower = question.lower()
        
        # Genuine conversational patterns
        if context.tenant_language == 'th':
            conversation_patterns = [
                'สวัสดี', 'ขอบคุณ', 'คุณคือใคร', 'คุณทำอะไรได้',
                'ช่วยได้อะไร', 'สบายดีไหม', 'เป็นยังไง',
                'ขอความช่วยเหลือ'
            ]
        else:
            conversation_patterns = [
                'hello', 'hi', 'thank you', 'thanks', 'who are you',
                'what can you do', 'how are you', 'help me',
                'good morning', 'good afternoon'
            ]
        
        # If it's purely conversational without business context
        has_conversation_pattern = any(pattern in question_lower for pattern in conversation_patterns)
        has_business_context = self._has_business_context(question, context.business_concepts)
        
        return has_conversation_pattern and not has_business_context
    
    def _basic_intent_classification(self, question: str) -> Dict[str, Any]:
        """🔄 Fallback to basic classification when no schema context available"""
        question_lower = question.lower()
        
        # Basic business keywords (fallback)
        business_keywords = [
            'พนักงาน', 'โปรเจค', 'แผนก', 'เงินเดือน', 'งบประมาณ',
            'employee', 'project', 'department', 'salary', 'budget',
            'ลูกค้า', 'client', 'customer', 'ข้อมูล', 'data'
        ]
        
        if any(keyword in question_lower for keyword in business_keywords):
            return {
                'intent': 'basic_business_query',
                'confidence': 0.6,
                'should_use_sql': True,
                'reasoning': 'Basic business keywords detected (no schema context)'
            }
        
        # Greeting patterns
        greeting_patterns = ['สวัสดี', 'hello', 'hi', 'good morning']
        if any(pattern in question_lower for pattern in greeting_patterns):
            return {
                'intent': 'greeting',
                'confidence': 0.9,
                'should_use_sql': False,
                'reasoning': 'Greeting pattern detected'
            }
        
        return {
            'intent': 'unknown',
            'confidence': 0.3,
            'should_use_sql': False,
            'reasoning': 'No clear intent detected (basic classification)'
        }

# Integration helper for existing enhanced_postgres_agent.py
class IntentClassifier:
    """🔄 Wrapper for backward compatibility"""
    
    def __init__(self):
        self.enterprise_classifier = EnterpriseIntentClassifier()
        
    def classify_intent(self, question: str) -> dict:
        """Backward compatible method"""
        result = self.enterprise_classifier._basic_intent_classification(question.lower())
        
        # Convert to old format
        return {
            'intent': result['intent'],
            'confidence': result['confidence'],
            'should_use_sql': result['should_use_sql']
        }

# Enhanced Integration for enhanced_postgres_agent.py
class EnterpriseIntentIntegration:
    """🏗️ Enterprise integration for enhanced postgres agent"""
    
    def __init__(self, enterprise_validator):
        self.enterprise_classifier = EnterpriseIntentClassifier(enterprise_validator)
    
    def classify_question_intent(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Enhanced intent classification with schema awareness"""
        return self.enterprise_classifier.classify_intent(question, tenant_id)

# Demo/Test
async def test_enterprise_intent_classifier():
    """🧪 Test enterprise intent classifier"""
    print("🧠 Testing Enterprise Intent Classifier")
    print("=" * 50)
    
    # Mock context for testing
    mock_context = IntentContext(
        available_tables={'employees', 'projects', 'employee_projects'},
        available_columns={'id', 'name', 'position', 'department', 'salary', 'budget', 'client', 'role'},
        business_concepts={'พนักงาน', 'โปรเจค', 'แผนก', 'เงินเดือน', 'งบประมาณ', 'ลูกค้า', 'ตำแหน่ง'},
        tenant_language='th',
        business_type='enterprise_software'
    )
    
    classifier = EnterpriseIntentClassifier()
    
    test_questions = [
        "มีใครคือผู้นำโปรเจค Mobile Banking App?",
        "พนักงานคนไหนทำงานในโปรเจค CRM?",
        "มีพนักงานกี่คนในแต่ละแผนก?",
        "โปรเจคไหนมีงบประมาณสูงสุด?",
        "สวัสดีครับ",
        "คุณคือใคร",
        "ขอความช่วยเหลือ"
    ]
    
    for question in test_questions:
        result = classifier._schema_aware_classification(question.lower(), mock_context)
        
        print(f"❓ Question: {question}")
        print(f"🎯 Intent: {result['intent']}")
        print(f"🔧 Use SQL: {result['should_use_sql']}")
        print(f"📊 Confidence: {result['confidence']}")
        print(f"💭 Reasoning: {result['reasoning']}")
        if 'detected_concepts' in result:
            print(f"🏢 Concepts: {result['detected_concepts']}")
        print("-" * 50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enterprise_intent_classifier())