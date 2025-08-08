import re
from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)

class IntentClassifier:
    """🎯 Intent Classifier - Main interface class"""
    
    def __init__(self):
        self.smart_classifier = SmartIntentClassifier()
        logger.info("✅ IntentClassifier initialized")
    
    def classify_intent(self, question: str) -> Dict[str, Any]:
        """Main method to classify user intent"""
        return self.smart_classifier.classify_intent(question)
    
    def get_debug_analysis(self, question: str) -> Dict[str, Any]:
        """Get detailed analysis for debugging"""
        return self.smart_classifier.get_debug_analysis(question)

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
                'บริษัท', 'company', 'องค์กร', 'organization'
            ],
            'technical_roles': [
                'frontend', 'backend', 'fullstack', 'devops', 'senior', 'junior',
                'lead', 'architect', 'designer', 'tester', 'analyst'
            ],
            'data_metrics': [
                'กี่คน', 'จำนวน', 'ราคา', 'เงินเดือน', 'งบประมาณ', 'budget',
                'cost', 'salary', 'count', 'total', 'sum'
            ]
        }
    
    def _load_question_structures(self) -> Dict[str, List[str]]:
        """❓ Question structure patterns"""
        return {
            'who_questions': ['ใคร', 'who', 'คนไหน', 'ใครบ้าง'],
            'what_questions': ['อะไร', 'what', 'สิ่งไหน', 'อะไรบ้าง'],
            'how_many_questions': ['กี่', 'how many', 'จำนวน', 'มีกี่'],
            'where_questions': ['ที่ไหน', 'where', 'ตรงไหน'],
            'when_questions': ['เมื่อไร', 'when', 'เวลาไหน'],
            'analysis_questions': ['วิเคราะห์', 'analyze', 'เปรียบเทียบ', 'compare']
        }
    
    def _load_context_indicators(self) -> Dict[str, List[str]]:
        """🎯 Context indicators"""
        return {
            'business_context': [
                'รายงาน', 'report', 'สถิติ', 'statistics', 'ผลงาน', 'performance',
                'กำไร', 'profit', 'ขาดทุน', 'loss', 'เปอร์เซ็นต์', 'percentage'
            ],
            'conversational_context': [
                'สวัสดี', 'hello', 'hi', 'ขอบคุณ', 'thank you', 'thanks',
                'ลาก่อน', 'bye', 'goodbye', 'สบายดี', 'how are you'
            ],
            'system_context': [
                'คุณคือใคร', 'who are you', 'ช่วยอะไร', 'what can you do',
                'ระบบ', 'system', 'โปรแกรม', 'program'
            ]
        }
    
    def classify_intent(self, question: str) -> Dict[str, Any]:
        """🎯 Main classification method with dynamic scoring"""
        
        question_lower = question.strip().lower()
        
        # 💬 Quick check for pure conversational
        if self._is_pure_conversational(question_lower):
            return {
                'intent': 'conversational',
                'should_use_sql': False,
                'confidence': 0.95,
                'reasoning': 'Pure conversational greeting/polite expression',
                'classification_method': 'pattern_based_conversational'
            }
        
        # 📊 Calculate dynamic scores
        scores = self._calculate_dynamic_scores(question_lower)
        total_business_score = sum(scores.values())
        
        # 🎯 Smart decision making
        if total_business_score >= 0.6:
            intent = 'business_query'
            should_use_sql = True
            confidence = min(0.95, 0.6 + (total_business_score - 0.6) * 0.5)
            reasoning = f"High business content (score: {total_business_score:.2f})"
        elif total_business_score >= 0.3:
            # 🤖 Mixed content - check context
            mixed_analysis = self._analyze_mixed_content(question_lower)
            if mixed_analysis['business_dominant']:
                intent = 'business_query'
                should_use_sql = True
                confidence = 0.75
                reasoning = f"Mixed content but business dominant (score: {total_business_score:.2f})"
            else:
                intent = 'conversational'
                should_use_sql = False
                confidence = 0.65
                reasoning = f"Mixed content but conversational dominant (score: {total_business_score:.2f})"
        else:
            intent = 'conversational'
            should_use_sql = False
            confidence = 0.85
            reasoning = f"Low business content (score: {total_business_score:.2f})"
        
        return {
            'intent': intent,
            'should_use_sql': should_use_sql,
            'confidence': confidence,
            'reasoning': reasoning,
            'business_score': total_business_score,
            'detailed_scores': scores,
            'classification_method': 'dynamic_scoring'
        }
    
    def _is_pure_conversational(self, question_lower: str) -> bool:
        """💬 Check for pure conversational patterns"""
        
        pure_conversational_patterns = [
            # Thai greetings
            r'^สวัสดี(ครับ|ค่ะ|คะ)*$',
            r'^สวัสดี\s+(ครับ|ค่ะ|คะ)$',
            r'^ขอบคุณ(ครับ|ค่ะ|คะ|มาก)*$',
            r'^ลาก่อน(ครับ|ค่ะ|คะ)*$',
            
            # English greetings
            r'^hi+$', r'^hello+$', r'^hey+$',
            r'^thank\s*you$', r'^thanks$', r'^bye$', r'^goodbye$',
            
            # System questions
            r'^คุณคือใคร$', r'^who\s+are\s+you$',
            r'^คุณช่วยอะไรได้บ้าง$', r'^what\s+can\s+you\s+do$'
        ]
        
        for pattern in pure_conversational_patterns:
            if re.match(pattern, question_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_dynamic_scores(self, question_lower: str) -> Dict[str, float]:
        """📊 Calculate dynamic scores for different aspects"""
        
        scores = {}
        
        # 1. Business Entity Score
        business_entity_matches = 0
        total_business_entities = 0
        for category, entities in self.business_entities.items():
            total_business_entities += len(entities)
            for entity in entities:
                if entity.lower() in question_lower:
                    business_entity_matches += 1
        
        scores['business_entity_score'] = (business_entity_matches / max(total_business_entities, 1)) * self.scoring_weights['business_entity_score']
        
        # 2. Question Structure Score
        question_structure_matches = 0
        total_structures = 0
        for category, structures in self.question_structures.items():
            total_structures += len(structures)
            for structure in structures:
                if structure.lower() in question_lower:
                    question_structure_matches += 1
        
        scores['question_structure_score'] = (question_structure_matches / max(total_structures, 1)) * self.scoring_weights['question_structure_score']
        
        # 3. Context Score
        business_context_matches = 0
        conversational_context_matches = 0
        
        for indicator in self.context_indicators['business_context']:
            if indicator.lower() in question_lower:
                business_context_matches += 1
        
        for indicator in self.context_indicators['conversational_context']:
            if indicator.lower() in question_lower:
                conversational_context_matches += 1
        
        # Context score favors business context
        context_score = max(0, business_context_matches - conversational_context_matches) * 0.1
        scores['context_score'] = min(context_score, self.scoring_weights['context_score'])
        
        # 4. Verb Action Score
        action_verbs = ['ดู', 'show', 'หา', 'find', 'ต้องการ', 'want', 'วิเคราะห์', 'analyze']
        verb_action_matches = sum(1 for verb in action_verbs if verb.lower() in question_lower)
        scores['verb_action_score'] = min(verb_action_matches * 0.05, self.scoring_weights['verb_action_score'])
        
        return scores
    
    def _analyze_mixed_content(self, question_lower: str) -> Dict[str, Any]:
        """🤖 Analyze mixed content to determine dominance"""
        
        business_indicators = 0
        conversational_indicators = 0
        
        # Count business vs conversational indicators
        for category, entities in self.business_entities.items():
            for entity in entities:
                if entity.lower() in question_lower:
                    business_indicators += 1
        
        for indicator in self.context_indicators['conversational_context']:
            if indicator.lower() in question_lower:
                conversational_indicators += 1
        
        return {
            'business_indicators': business_indicators,
            'conversational_indicators': conversational_indicators,
            'business_dominant': business_indicators > conversational_indicators,
            'analysis': f"Business: {business_indicators}, Conversational: {conversational_indicators}"
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