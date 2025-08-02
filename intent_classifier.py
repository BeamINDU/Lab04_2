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
        
        # 🔧 แก้ไข: ให้คำทักทายผ่านไปใช้ AI แทนการ hard-code
        greeting_patterns = [
            'สวัสดี', 'hello', 'hi', 'hey', 'good morning',
            'good afternoon', 'good evening', 'ขอบคุณ', 'thank you',
            'ไง', 'หวัดดี', 'ครับ', 'ค่ะ'
        ]
        
        if any(pattern in question_lower for pattern in greeting_patterns):
            return {
                'intent': 'greeting',
                'confidence': 0.9,
                'should_use_sql': False,  # ไม่ใช้ SQL แต่ให้ AI ตอบ
                'use_ai_response': True   # 🆕 ให้ AI ตอบคำทักทาย
            }
        
        # 🔧 แก้ไข: คำถามทั่วไปให้ AI ตอบแทน hard-code
        help_patterns = [
            'ช่วย', 'help', 'ทำอะไรได้', 'what can you do',
            'คุณคือใคร', 'who are you', 'สามารถ', 'ความสามารถ'
        ]
        
        if any(pattern in question_lower for pattern in help_patterns):
            return {
                'intent': 'help',
                'confidence': 0.8,
                'should_use_sql': False,
                'use_ai_response': True
            }
        
        # ตรวจสอบคำถามที่เกี่ยวข้องกับข้อมูล
        sql_keywords = [
            'กี่คน', 'จำนวน', 'รายชื่อ', 'ข้อมูล', 'พนักงาน', 'โปรเจค',
            'เงินเดือน', 'งบประมาณ', 'แผนก', 'ลูกค้า', 'สถานะ', 'รายงาน',
            'how many', 'count', 'list', 'show', 'find', 'search',
            'employee', 'project', 'salary', 'budget', 'department', 'client',
            'มาก', 'น้อย', 'สูง', 'ต่ำ', 'เปรียบเทียบ', 'วิเคราะห์'
        ]
        
        if any(keyword in question_lower for keyword in sql_keywords):
            return {
                'intent': 'data_query',
                'confidence': 0.9,
                'should_use_sql': True,
                'use_ai_response': False
            }
        
        # 🔧 Default: ให้ AI ตอบคำถามทั่วไป (แทนการ reject)
        return {
            'intent': 'general_conversation',
            'confidence': 0.7,
            'should_use_sql': False,
            'use_ai_response': True   # 🆕 ให้ AI ตอบทุกคำถามที่ไม่ใช่ data query
        }