from typing import Dict, Any, List, Set
class LocalCulturalContext:
    """🎭 Provides Northern Thai cultural context for tourism responses"""
    
    def __init__(self):
        self.cultural_knowledge = {
            'lanna_heritage': {
                'language': {
                    'formal_terms': ['คำเมือง', 'ภาษาล้านนา', 'อักษรล้านนา'],
                    'common_words': ['เจ้า', 'ลาว', 'ฮัก', 'แซ่บ', 'ลืม']
                },
                'architecture': {
                    'temple_style': ['วัดล้านนา', 'ช่อฟ้า', 'ประติมากรรม'],
                    'house_style': ['เรือนเหนือ', 'เรือนไม้', 'หลังคาจั่ว']
                }
            },
            'festivals_events': {
                'major_festivals': [
                    {'name': 'สงกรานต์', 'month': 4, 'description': 'Thai New Year, water festival'},
                    {'name': 'ลอยกระทง', 'month': 11, 'description': 'Light festival, krathong floating'},
                    {'name': 'ยี่เป็ง', 'month': 11, 'description': 'Lantern festival, sky lanterns'},
                    {'name': 'บุญบั้งไฟ', 'month': 5, 'description': 'Rocket festival, rain calling'}
                ],
                'seasonal_activities': {
                    'cool_season': ['trekking', 'temple visits', 'cultural tours'],
                    'hot_season': ['water activities', 'fruit picking', 'indoor attractions'],
                    'rainy_season': ['cooking classes', 'handicraft workshops', 'spa treatments']
                }
            },
            'local_cuisine': {
                'signature_dishes': [
                    {'name': 'ข้าวซอย', 'type': 'noodle', 'description': 'Coconut curry noodles'},
                    {'name': 'แกงฮังเล', 'type': 'curry', 'description': 'Northern pork curry'},
                    {'name': 'ไส้อั่ว', 'type': 'sausage', 'description': 'Northern style sausage'},
                    {'name': 'น้ำพริกน้ำปู', 'type': 'dip', 'description': 'Crab chili dip'}
                ],
                'dining_culture': ['khan tok', 'communal dining', 'sticky rice traditions']
            },
            'hospitality_principles': {
                'service_values': [
                    'น้ำใจเหนือ (Northern hospitality)',
                    'ความเป็นมิตรแบบคนเหนือ',
                    'การให้ความสำคัญกับแขก',
                    'ความจริงใจและเรียบง่าย'
                ],
                'communication_style': [
                    'ใช้ภาษาที่อ่อนโยน',
                    'เน้นความเคารพ',
                    'หลีกเลี่ยงการเผชิญหน้า',
                    'แสดงความใส่ใจ'
                ]
            }
        }
    
    def get_cultural_considerations(self, question: str) -> str:
        """Get relevant cultural considerations for the question"""
        
        question_lower = question.lower()
        considerations = []
        
        # Cultural context detection
        if any(term in question_lower for term in ['วัฒนธรรม', 'ประเพณี', 'ล้านนา', 'cultural']):
            considerations.extend([
                "• เน้นเอกลักษณ์ล้านนา: ภาษา, สถาปัตยกรรม, ประเพณี",
                "• รักษาองค์ความรู้ท้องถิ่น: นิทาน, ตำนาน, ภูมิปัญญา",
                "• การถ่ายทอดวัฒนธรรมผ่านเทคโนโลยี"
            ])
        
        # Service context detection  
        if any(term in question_lower for term in ['บริการ', 'service', 'ลูกค้า', 'guest']):
            considerations.extend([
                "• น้ำใจเหนือ: ความเป็นมิตร, ความจริงใจ, การดูแลเอาใจใส่",
                "• การสื่อสารแบบคนเหนือ: นุ่มนวล, สุภาพ, เคารพ",
                "• เน้นประสบการณ์ที่แท้จริงของท้องถิ่น"
            ])
        
        # Food context detection
        if any(term in question_lower for term in ['อาหาร', 'ร้านอาหาร', 'food', 'restaurant']):
            considerations.extend([
                "• อาหารพื้นเมืองเหนือ: ข้าวซอย, แกงฮังเล, ไส้อั่ว",
                "• วัฒนธรรมการกิน: ข้าวเหนียว, การกินแบบข่านโต๊ก",
                "• ส่วนผสมและรสชาติท้องถิ่น"
            ])
        
        # Default considerations if none detected
        if not considerations:
            considerations = [
                "• รักษาเอกลักษณ์ภาคเหนือในการพัฒนาระบบ",
                "• เน้นความเรียบง่ายและใช้งานง่าย",
                "• คำนึงถึงความหลากหลายทางวัฒนธรรม"
            ]
        
        return '\n'.join(considerations[:3])  # Return max 3 considerations
    
    def get_seasonal_recommendations(self, month: int) -> Dict[str, Any]:
        """Get seasonal tourism recommendations"""
        
        if month in [11, 12, 1, 2]:
            season = 'cool_season'
            activities = self.cultural_knowledge['festivals_events']['seasonal_activities']['cool_season']
            festivals = [f for f in self.cultural_knowledge['festivals_events']['major_festivals'] if f['month'] == month]
        elif month in [3, 4, 5]:
            season = 'hot_season'
            activities = self.cultural_knowledge['festivals_events']['seasonal_activities']['hot_season']
            festivals = [f for f in self.cultural_knowledge['festivals_events']['major_festivals'] if f['month'] == month]
        else:
            season = 'rainy_season'
            activities = self.cultural_knowledge['festivals_events']['seasonal_activities']['rainy_season']
            festivals = [f for f in self.cultural_knowledge['festivals_events']['major_festivals'] if f['month'] == month]
        
        return {
            'season': season,
            'recommended_activities': activities,
            'festivals': festivals,
            'cultural_tips': self.cultural_knowledge['hospitality_principles']['service_values']
        }