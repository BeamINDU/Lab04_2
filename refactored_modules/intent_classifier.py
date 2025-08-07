import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class IntentClassifier:
    """🎯 Enhanced intent classifier with better SQL detection"""
    
    def __init__(self):
        # Pure conversational patterns (high confidence)
        self.pure_conversational_patterns = {
            'greeting': [
                r'^(สวัสดี|hello|hi|hey)(?!\s+.*(?:พนักงาน|โปรเจค|employee|project))',
                r'^(good morning|good afternoon|good evening)(?!\s+.*(?:พนักงาน|โปรเจค))'
            ],
            'thanks': [
                r'^(ขอบคุณ|thank you|thanks|thx)(?!\s+.*(?:พนักงาน|โปรเจค))',
                r'^(appreciate|grateful)(?!\s+.*(?:พนักงาน|โปรเจค))'
            ],
            'help_general': [
                r'^(ช่วย.*ได้.*อะไร|what can you do|how.*help)(?!\s+.*(?:พนักงาน|โปรเจค|แผนก))',
                r'^(ขอความช่วยเหลือ|need help)(?!\s+.*(?:พนักงาน|โปรเจค))'
            ]
        }
        
        # Strong SQL indicator patterns (should trigger SQL)
        self.strong_sql_patterns = {
            'employee_queries': [
                r'(พนักงาน.*(?:คน|ใคร|ไหน|รับผิดชอบ|ทำงาน|โปรเจค))',
                r'(employee.*(?:who|work|project|responsible))',
                r'(คนไหน.*(?:ทำ|รับผิดชอบ|จัดการ))',
                r'(ใคร.*(?:รับผิดชอบ|ทำงาน|จัดการ|ดูแล).*(?:โปรเจค|งาน|project))'
            ],
            'project_queries': [
                r'(โปรเจค.*(?:อะไร|ไหน|บ้าง|มี|งาน))',
                r'(project.*(?:what|which|list|work|responsible))',
                r'(งาน.*(?:อะไร|ไหน|บ้าง|รับผิดชอบ))',
                r'(รับผิดชอบ.*(?:โปรเจค|งาน|project))'
            ],
            'department_queries': [
                r'(แผนก.*(?:ไหน|อะไร|มี|กี่))',
                r'(department.*(?:what|which|how many))',
                r'(ฝ่าย.*(?:ไหน|อะไร|มี))'
            ],
            'counting_queries': [
                r'(กี่.*(?:คน|โปรเจค|แผนก))',
                r'(จำนวน.*(?:พนักงาน|โปรเจค|แผนก))',
                r'(how many.*(?:employee|project|department))',
                r'(count.*(?:employee|project))'
            ],
            'assignment_queries': [  # 🔥 NEW: รับผิดชอบ/assignment patterns
                r'(แต่ละคน.*(?:รับผิดชอบ|ทำงาน|จัดการ))',
                r'(each.*(?:responsible|work|manage))',
                r'(รับผิดชอบ.*(?:อะไร|ไหน|บ้าง))',
                r'(responsible.*(?:what|which|for))',
                r'(assignment|assigned|allocate)'
            ]
        }
        
        # Business entity indicators
        self.business_entities = [
            'พนักงาน', 'employee', 'staff', 'คน', 'people',
            'โปรเจค', 'project', 'งาน', 'work', 'task',
            'แผนก', 'department', 'ฝ่าย', 'division', 'team',
            'เงินเดือน', 'salary', 'pay', 'wage',
            'งบประมาณ', 'budget', 'cost', 'expense',
            'ลูกค้า', 'client', 'customer',
            'siamtech', 'สยามเทค'
        ]
    
    def classify_intent(self, question: str) -> Dict[str, Any]:
        """🎯 Enhanced intent classification with better SQL detection"""
        
        if not question or len(question.strip()) == 0:
            return self._create_response('conversation', 0.9, 'Empty question')
        
        question_lower = question.lower().strip()
        
        # 1. Check for PURE conversational patterns first (strict matching)
        pure_conv_result = self._check_pure_conversational_patterns(question_lower)
        if pure_conv_result['confidence'] > 0.8:
            return pure_conv_result
        
        # 2. Check for STRONG SQL patterns (should override conversational)
        strong_sql_result = self._check_strong_sql_patterns(question_lower)
        if strong_sql_result['confidence'] > 0.7:
            return strong_sql_result
        
        # 3. Check for business entities (moderate confidence SQL)
        entity_result = self._check_business_entities(question_lower)
        if entity_result['confidence'] > 0.5:
            return entity_result
        
        # 4. Default: if contains any work-related terms, try SQL
        if self._contains_work_terms(question_lower):
            return self._create_response(
                'business_query',
                0.6,
                'Contains work-related terms, trying SQL'
            )
        
        # 5. Final fallback to conversation
        return self._create_response(
            'conversation',
            0.5,
            'No clear business intent detected'
        )
    
    def _check_pure_conversational_patterns(self, question: str) -> Dict[str, Any]:
        """💬 Check for PURE conversational patterns (no business context)"""
        
        for category, patterns in self.pure_conversational_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return self._create_response(
                        'conversation',
                        0.95,
                        f'Pure conversational pattern: {category}'
                    )
        
        return self._create_response('unknown', 0.0, 'No pure conversational patterns')
    
    def _check_strong_sql_patterns(self, question: str) -> Dict[str, Any]:
        """🗄️ Check for STRONG SQL indicator patterns"""
        
        confidence = 0.0
        matched_categories = []
        
        for category, patterns in self.strong_sql_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    confidence += 0.3
                    matched_categories.append(category)
                    
                    # 🔥 Special boost for assignment queries
                    if category == 'assignment_queries':
                        confidence += 0.2
        
        if confidence > 0:
            unique_categories = list(dict.fromkeys(matched_categories))
            return self._create_response(
                'business_query',
                min(0.95, confidence),
                f'Strong SQL patterns: {unique_categories}'
            )
        
        return self._create_response('unknown', 0.0, 'No strong SQL patterns')
    
    def _check_business_entities(self, question: str) -> Dict[str, Any]:
        """🏢 Check for business entity mentions"""
        
        entity_count = 0
        found_entities = []
        
        for entity in self.business_entities:
            if entity.lower() in question:
                entity_count += 1
                found_entities.append(entity)
        
        if entity_count >= 2:  # At least 2 business entities
            return self._create_response(
                'business_query',
                0.8,
                f'Multiple business entities: {found_entities[:3]}'
            )
        elif entity_count >= 1:  # At least 1 business entity
            return self._create_response(
                'business_query',
                0.6,
                f'Business entity detected: {found_entities[0]}'
            )
        
        return self._create_response('unknown', 0.0, 'No business entities')
    
    def _contains_work_terms(self, question: str) -> bool:
        """🔍 Check if contains any work-related terms"""
        work_terms = [
            'รับผิดชอบ', 'responsible', 'assignment', 'assigned',
            'ทำงาน', 'work', 'working', 'job',
            'จัดการ', 'manage', 'management',
            'ดูแล', 'handle', 'take care',
            'siamtech', 'บริษัท', 'company'
        ]
        
        return any(term in question for term in work_terms)
    
    def _create_response(self, intent: str, confidence: float, reasoning: str) -> Dict[str, Any]:
        """📝 Create standardized response"""
        
        should_use_sql = intent in ['business_query', 'data_query']
        
        return {
            'intent': intent,
            'confidence': confidence,
            'should_use_sql': should_use_sql,
            'reasoning': reasoning,
            'classifier_version': 'enhanced_v2.0'
        }

# 🧪 Test the improved classifier
def test_improved_classifier():
    """Test the improved intent classifier"""
    classifier = IntentClassifier()
    
    test_cases = [
        # Should be SQL (business queries)
        ("พนักงาน siamtech แต่ละคนรับผิดชอบโปรเจคอะไรบ้าง", True),
        ("มีพนักงานกี่คนในแต่ละแผนก", True),
        ("ใครรับผิดชอบโปรเจค Mobile App", True),
        ("โปรเจคไหนมีงบประมาณสูงสุด", True),
        
        # Should be conversational
        ("สวัสดีครับ", False),
        ("ขอบคุณมากครับ", False),
        ("คุณคือใคร", False),
        ("ช่วยได้อะไรบ้าง", False),
        
        # Edge cases - should be SQL
        ("สวัสดี มีพนักงานกี่คน", True),  # Mixed but has business context
        ("ขอบคุณ แล้วโปรเจคไหนสำคัญ", True)  # Mixed but has business context
    ]
    
    print("🧪 Testing Improved Intent Classifier")
    print("=" * 50)
    
    for question, expected_sql in test_cases:
        result = classifier.classify_intent(question)
        actual_sql = result['should_use_sql']
        status = "✅" if actual_sql == expected_sql else "❌"
        
        print(f"{status} {question}")
        print(f"   Expected SQL: {expected_sql}, Got: {actual_sql}")
        print(f"   Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
        print(f"   Reasoning: {result['reasoning']}")
        print()

if __name__ == "__main__":
    test_improved_classifier()