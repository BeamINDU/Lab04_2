class IntentClassifier:
    def __init__(self):
        self.sql_intents = [
            'data_query', 'count_query', 'search_query', 
            'analysis_query', 'report_query'
        ]
        
        self.general_intents = [
            'greeting', 'help', 'casual_conversation', 
            'system_status', 'about_company'
        ]
    
    def classify_intent(self, question: str) -> dict:
        question_lower = question.lower().strip()
        
        # กรองคำทักทาย
        greeting_patterns = [
            'สวัสดี', 'hello', 'hi', 'hey', 'good morning',
            'good afternoon', 'good evening', 'ขอบคุณ', 'thank you'
        ]
        
        if any(pattern in question_lower for pattern in greeting_patterns):
            return {
                'intent': 'greeting',
                'confidence': 0.9,
                'should_use_sql': False
            }
        
        # กรองคำถามทั่วไป
        casual_patterns = [
            'อย่างไร', 'เป็นยังไง', 'ช่วยได้อะไร', 'what can you do',
            'help me', 'ขอความช่วยเหลือ', 'คุณคือใคร', 'who are you'

        ]
        
        if any(pattern in question_lower for pattern in casual_patterns):
            return {
                'intent': 'help',
                'confidence': 0.8,
                'should_use_sql': False
            }
        
        # ตรวจสอบคำถามที่เกี่ยวข้องกับข้อมูล
        sql_keywords = [
            'กี่คน', 'จำนวน', 'รายชื่อ', 'ข้อมูล', 'พนักงาน', 'โปรเจค',
            'เงินเดือน', 'งบประมาณ', 'แผนก', 'ลูกค้า', 'สถานะ',
            'how many', 'count', 'list', 'show', 'find', 'search',
            'employee', 'project', 'salary', 'budget', 'department'
        ]
        
        if any(keyword in question_lower for keyword in sql_keywords):
            return {
                'intent': 'data_query',
                'confidence': 0.9,
                'should_use_sql': True
            }
        
        # Default: คำถามทั่วไป
        return {
            'intent': 'general',
            'confidence': 0.6,
            'should_use_sql': False
        }