import re
from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)

class SmartIntentClassifier:
    """🧠 Smart Intent Classifier ที่เรียนรู้ patterns แบบ dynamic"""
    
    def __init__(self):
        # 🎯 Core business entities (แทน hard code patterns)
        self.business_entities = self._load_business_entities()
        self.question_structures = self._load_question_structures()
        self.context_indicators = self._load_context_indicators()
        
        # 📊 Dynamic scoring weights
        self.scoring_weights = {
            'business_entity_score': 0.4,
            'question_structure_score': 0.3,
            'context_score': 0.2,
            'verb_action_score': 0.1
        }
        
        logger.info("✅ Smart Intent Classifier initialized with dynamic learning")
    
    def _load_business_entities(self) -> Dict[str, List[str]]:
        """🏢 Core business entities แทน hard code patterns"""
        return {
            'people': [
                'พนักงาน', 'employee', 'staff', 'คน', 'people', 'ใคร', 'who',
                'นักพัฒนา', 'developer', 'โปรแกรมเมอร์', 'programmer',
                'ทีม', 'team', 'สมาชิก', 'member'
            ],
            'work_items': [
                'โปรเจค', 'project', 'งาน', 'work', 'task', 'งานที่ทำ',
                'ภารกิจ', 'responsibility', 'หน้าที่', 'duty'
            ],
            'organizational': [
                'แผนก', 'department', 'ฝ่าย', 'division', 'ตำแหน่ง', 'position',
                'บทบาท', 'role', 'หน้าที่', 'function', 'ระดับ', 'level'
            ],
            'financial': [
                'เงินเดือน', 'salary', 'ค่าจ้าง', 'wage', 'งบประมาณ', 'budget',
                'ราคา', 'price', 'ค่าใช้จ่าย', 'cost', 'รายได้', 'income'
            ],
            'technical_positions': [
                'frontend', 'backend', 'fullstack', 'devops', 'qa', 'tester',
                'designer', 'architect', 'lead', 'senior', 'junior',
                'เฟรนท์เอนด์', 'แบ็กเอนด์', 'ดีไซน์เนอร์'
            ]
        }
    
    def _load_question_structures(self) -> Dict[str, List[str]]:
        """❓ Question structure patterns (more flexible)"""
        return {
            'who_what_questions': [
                'ใคร', 'who', 'คนไหน', 'which person', 'ใครบ้าง', 'who are',
                'ใครคือ', 'who is', 'ใครเป็น', 'who acts as'
            ],
            'what_where_questions': [
                'อะไร', 'what', 'ไหน', 'which', 'อะไรบ้าง', 'what are',
                'อย่างไร', 'how', 'เป็นอย่างไร', 'like what'
            ],
            'counting_questions': [
                'กี่', 'how many', 'จำนวน', 'count', 'เท่าไหร่', 'how much',
                'มากน้อย', 'amount', 'ปริมาณ', 'quantity'
            ],
            'listing_questions': [
                'บ้าง', 'some', 'ทั้งหมด', 'all', 'รายการ', 'list',
                'แต่ละ', 'each', 'ทุก', 'every'
            ]
        }
    
    def _load_context_indicators(self) -> Dict[str, List[str]]:
        """🎯 Context indicators for business vs conversation"""
        return {
            'business_actions': [
                'รับผิดชอบ', 'responsible', 'ทำงาน', 'work', 'จัดการ', 'manage',
                'พัฒนา', 'develop', 'ออกแบบ', 'design', 'ทดสอบ', 'test',
                'อยู่', 'is in', 'ประจำ', 'assigned to', 'สังกัด', 'belongs to'
            ],
            'business_contexts': [
                'บริษัท', 'company', 'siamtech', 'สยามเทค', 'องค์กร', 'organization',
                'ออฟฟิศ', 'office', 'สำนักงาน', 'workplace'
            ],
            'conversational_only': [
                'สวัสดี', 'hello', 'hi', 'ขอบคุณ', 'thank you', 'thanks',
                'คุณคือใคร', 'who are you', 'ช่วยได้อะไร', 'what can you do'
            ]
        }
    
    def classify_intent(self, question: str) -> Dict[str, Any]:
        """🧠 Smart intent classification with dynamic scoring"""
        
        if not question or len(question.strip()) == 0:
            return self._create_response('conversation', 0.9, 'Empty question')
        
        question_lower = question.strip().lower()
        
        # 🚫 Quick check for pure conversational patterns
        if self._is_pure_conversational(question_lower):
            return self._create_response('conversation', 0.95, 'Pure conversational pattern')
        
        # 🧠 Dynamic scoring
        scores = self._calculate_dynamic_scores(question_lower)
        
        # 🎯 Decision logic
        business_score = sum(scores.values())
        
        if business_score >= 0.6:
            confidence = min(0.95, 0.6 + (business_score - 0.6) * 0.7)
            return self._create_response(
                'business_query',
                confidence,
                f'Smart scoring: {scores}, total: {business_score:.2f}'
            )
        elif business_score >= 0.3:
            confidence = min(0.8, 0.4 + (business_score - 0.3) * 0.8)
            return self._create_response(
                'business_query',
                confidence,
                f'Moderate business indicators: {scores}'
            )
        else:
            return self._create_response(
                'conversation',
                0.7,
                f'Low business score: {business_score:.2f}'
            )
    
    def _is_pure_conversational(self, question: str) -> bool:
        """💬 Check for pure conversational patterns"""
        pure_patterns = [
            r'^(สวัสดี|สวัสดีครับ|สวัสดีค่ะ)$',
            r'^(hello|hi|hey)$',
            r'^(ขอบคุณ|ขอบคุณครับ|ขอบคุณค่ะ|thank you|thanks)$',
            r'^(คุณคือใคร|who are you)$',
            r'^(ช่วยได้อะไร|what can you do)$'
        ]
        
        for pattern in pure_patterns:
            if re.match(pattern, question, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_dynamic_scores(self, question: str) -> Dict[str, float]:
        """🧠 Calculate dynamic scores for different aspects"""
        
        scores = {}
        
        # 1. Business Entity Score
        scores['business_entities'] = self._score_business_entities(question)
        
        # 2. Question Structure Score
        scores['question_structure'] = self._score_question_structure(question)
        
        # 3. Context Score
        scores['context'] = self._score_context(question)
        
        # 4. Technical Position Score (ใหม่! สำหรับจับ "frontend", "backend")
        scores['technical_positions'] = self._score_technical_positions(question)
        
        # 5. Business Action Score
        scores['business_actions'] = self._score_business_actions(question)
        
        return scores
    
    def _score_business_entities(self, question: str) -> float:
        """🏢 Score based on business entities found"""
        score = 0.0
        entities_found = []
        
        for category, entities in self.business_entities.items():
            for entity in entities:
                if entity.lower() in question:
                    if category == 'people':
                        score += 0.2  # People entities are strong indicators
                    elif category == 'technical_positions':
                        score += 0.25  # Technical positions are very strong
                    elif category == 'work_items':
                        score += 0.15
                    elif category == 'organizational':
                        score += 0.15
                    elif category == 'financial':
                        score += 0.1
                    
                    entities_found.append(f"{category}:{entity}")
        
        # Bonus for multiple entity categories
        unique_categories = len(set(e.split(':')[0] for e in entities_found))
        if unique_categories >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_question_structure(self, question: str) -> float:
        """❓ Score based on question structure"""
        score = 0.0
        
        for structure_type, patterns in self.question_structures.items():
            for pattern in patterns:
                if pattern.lower() in question:
                    if structure_type == 'who_what_questions':
                        score += 0.2  # Strong indicator for business queries
                    elif structure_type == 'listing_questions':
                        score += 0.15
                    elif structure_type == 'counting_questions':
                        score += 0.1
                    elif structure_type == 'what_where_questions':
                        score += 0.1
        
        return min(score, 1.0)
    
    def _score_context(self, question: str) -> float:
        """🎯 Score based on context indicators"""
        score = 0.0
        
        # Check for business context
        for action in self.context_indicators['business_actions']:
            if action.lower() in question:
                score += 0.15
        
        for context in self.context_indicators['business_contexts']:
            if context.lower() in question:
                score += 0.1
        
        # Penalize conversational indicators
        for conv in self.context_indicators['conversational_only']:
            if conv.lower() in question:
                score -= 0.2
        
        return max(0.0, min(score, 1.0))
    
    def _score_technical_positions(self, question: str) -> float:
        """💻 Score technical position references (ใหม่!)"""
        score = 0.0
        
        technical_terms = self.business_entities['technical_positions']
        for term in technical_terms:
            if term.lower() in question:
                score += 0.3  # Technical positions are strong business indicators
        
        # Special handling for position-related questions
        position_indicators = ['ตำแหน่ง', 'position', 'role', 'อยู่', 'is in']
        for indicator in position_indicators:
            if indicator.lower() in question:
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_business_actions(self, question: str) -> float:
        """⚡ Score business action verbs"""
        score = 0.0
        
        action_verbs = [
            'ทำ', 'do', 'รับผิดชอบ', 'responsible', 'จัดการ', 'manage',
            'พัฒนา', 'develop', 'ออกแบบ', 'design', 'ประจำ', 'assigned'
        ]
        
        for verb in action_verbs:
            if verb.lower() in question:
                score += 0.1
        
        return min(score, 1.0)
    
    def _create_response(self, intent: str, confidence: float, reasoning: str) -> Dict[str, Any]:
        """📝 Create standardized response"""
        
        should_use_sql = intent in ['business_query', 'data_query']
        
        return {
            'intent': intent,
            'confidence': confidence,
            'should_use_sql': should_use_sql,
            'reasoning': reasoning,
            'classifier_version': 'smart_dynamic_v1.0',
            'features': [
                'dynamic_scoring',
                'technical_position_detection',
                'multi_entity_analysis',
                'context_aware_classification'
            ]
        }
    
    def get_debug_analysis(self, question: str) -> Dict[str, Any]:
        """🔍 Get detailed analysis for debugging"""
        question_lower = question.strip().lower()
        
        scores = self._calculate_dynamic_scores(question_lower)
        total_score = sum(scores.values())
        
        # Find matching entities
        matching_entities = {}
        for category, entities in self.business_entities.items():
            matches = [entity for entity in entities if entity.lower() in question_lower]
            if matches:
                matching_entities[category] = matches
        
        return {
            'question': question,
            'question_lower': question_lower,
            'individual_scores': scores,
            'total_business_score': total_score,
            'matching_entities': matching_entities,
            'decision': 'business_query' if total_score >= 0.6 else ('moderate' if total_score >= 0.3 else 'conversation'),
            'is_pure_conversational': self._is_pure_conversational(question_lower)
        }

# 🧪 Test the Smart Intent Classifier
def test_smart_intent_classifier():
    """🧪 ทดสอบ Smart Intent Classifier"""
    
    classifier = SmartIntentClassifier()
    
    test_cases = [
        # Should be business_query
        ("พนักงาน siamtech แต่ละคนรับผิดชอบโปรเจคอะไรบ้าง", True),
        ("ใครอยู่ตำแหน่งfrontendบ้าง", True),  # 🎯 ปัญหาเดิม
        ("มีใครทำงาน backend บ้าง", True),
        ("พนักงาน frontend คือใคร", True),
        ("ใครเป็น senior developer", True),
        ("มีโปรเจคอะไรบ้าง", True),
        ("พนักงานแผนก IT กี่คน", True),
        
        # Should be conversation
        ("สวัสดีครับ", False),
        ("ขอบคุณมากครับ", False),
        ("คุณคือใคร", False),
        ("hello", False),
        
        # Edge cases
        ("สวัสดี มี frontend developer กี่คน", True),  # Mixed but business wins
    ]
    
    print("🧪 Testing Smart Intent Classifier")
    print("=" * 70)
    print("🎯 Focus: Fix 'ใครอยู่ตำแหน่งfrontendบ้าง' classification")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    
    for question, expected_sql in test_cases:
        result = classifier.classify_intent(question)
        actual_sql = result['should_use_sql']
        status = "✅" if actual_sql == expected_sql else "❌"
        
        print(f"{status} {question}")
        print(f"   Expected: {expected_sql}, Got: {actual_sql}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reasoning: {result['reasoning']}")
        
        if actual_sql == expected_sql:
            correct += 1
        
        # Show debug for failed cases
        if actual_sql != expected_sql:
            debug = classifier.get_debug_analysis(question)
            print(f"   🔍 Scores: {debug['individual_scores']}")
            print(f"   🔍 Total: {debug['total_business_score']:.2f}")
            print(f"   🔍 Entities: {debug['matching_entities']}")
        
        print()
    
    accuracy = (correct / total) * 100
    print("=" * 70)
    print(f"📊 Results: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    
    if accuracy >= 90:
        print("🎉 EXCELLENT! Smart Intent Classifier is working!")
    elif accuracy >= 80:
        print("✅ GOOD! Minor improvements needed")
    else:
        print("⚠️ NEEDS WORK! Significant fixes required")
    
    return accuracy >= 85

if __name__ == "__main__":
    test_smart_intent_classifier()