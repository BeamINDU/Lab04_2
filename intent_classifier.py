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
        

        greeting_patterns = [
            'สวัสดี', 'hello', 'hi', 'hey', 'good morning',
            'good afternoon', 'good evening', 'ขอบคุณ', 'thank you',
            'ไง', 'หวัดดี', 'ครับ', 'ค่ะ', 'สบายดี', 'เป็นไงบ้าง'
        ]
        
        # 🎯 ตรวจสอบคำทักทายอย่างเข้มข้น
        for pattern in greeting_patterns:
            if pattern in question_lower and len(question_lower) < 20:  # 🔥 เพิ่มเงื่อนไข length
                return {
                    'intent': 'greeting',
                    'confidence': 0.95,
                    'should_use_sql': False,
                    'use_ai_response': True
                }
        
        # 🔥 แก้ไข: คำถามทั่วไปให้ AI ตอบแทน hard-code
        help_patterns = [
            'ช่วย', 'help', 'ทำอะไรได้', 'what can you do',
            'คุณคือใคร', 'who are you', 'สามารถ', 'ความสามารถ',
            'ใช้งานยังไง', 'how to use'
        ]
        
        for pattern in help_patterns:
            if pattern in question_lower:
                return {
                    'intent': 'help',
                    'confidence': 0.9,
                    'should_use_sql': False,
                    'use_ai_response': True
                }
        
        # 🔍 ตรวจสอบคำถามที่เกี่ยวข้องกับข้อมูล (เข้มข้นขึ้น)
        sql_keywords = [
            'กี่คน', 'จำนวน', 'รายชื่อ', 'ข้อมูล', 'พนักงาน', 'โปรเจค',
            'เงินเดือน', 'งบประมาณ', 'แผนก', 'ลูกค้า', 'สถานะ', 'รายงาน',
            'how many', 'count', 'list', 'show', 'find', 'search',
            'employee', 'project', 'salary', 'budget', 'department', 'client',
            'มาก', 'น้อย', 'สูง', 'ต่ำ', 'เปรียบเทียบ', 'วิเคราะห์',
            'ใครบ้าง', 'อะไรบ้าง', 'เท่าไหร่', 'เมื่อไหร่'
        ]
        
        # 🎯 ต้องมีคำหลักเกี่ยวกับข้อมูล AND คำถาม
        has_data_keyword = any(keyword in question_lower for keyword in sql_keywords)
        has_question_word = any(word in question_lower for word in ['ใคร', 'อะไร', 'เท่าไหร่', 'กี่', 'มี', 'who', 'what', 'how', 'which'])
        
        if has_data_keyword and (has_question_word or len(question_lower) > 10):
            return {
                'intent': 'data_query',
                'confidence': 0.9,
                'should_use_sql': True,
                'use_ai_response': False
            }
        
        # 🔥 Default: ให้ AI ตอบคำถามทั่วไป (แทนการ reject)
        return {
            'intent': 'general_conversation',
            'confidence': 0.7,
            'should_use_sql': False,
            'use_ai_response': True
        }