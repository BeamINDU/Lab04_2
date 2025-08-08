

# =============================================================================
# company_prompts/company_b/regional_rules.py
# 🌿 Northern Thailand Regional Business Rules
# =============================================================================

from typing import Dict, Any, List, Set
from datetime import datetime

class NorthernThailandRules:
    """🌿 Comprehensive Northern Thailand regional business rules"""
    
    def __init__(self):
        self.tourism_seasons = {
            'cool_season': {
                'months': [11, 12, 1, 2],
                'characteristics': 'High tourist season, cool weather, festivals',
                'sql_condition': 'EXTRACT(MONTH FROM start_date) IN (11, 12, 1, 2)'
            },
            'hot_season': {
                'months': [3, 4, 5],
                'characteristics': 'Hot weather, Songkran festival, fruit season',
                'sql_condition': 'EXTRACT(MONTH FROM start_date) IN (3, 4, 5)'
            },
            'rainy_season': {
                'months': [6, 7, 8, 9, 10],
                'characteristics': 'Green season, fewer tourists, local activities',
                'sql_condition': 'EXTRACT(MONTH FROM start_date) IN (6, 7, 8, 9, 10)'
            }
        }
        
        self.regional_clients = {
            'tier_1': [
                'โรงแรมดุสิต เชียงใหม่',
                'การท่องเที่ยวแห่งประเทศไทย',
                'มหาวิทยาลัยเชียงใหม่'
            ],
            'tier_2': [
                'สวนพฤกษศาสตร์เชียงใหม่',
                'กลุ่มร้านอาหารล้านนา',
                'สำนักงานท่องเที่ยวจังหวัด'
            ],
            'emerging': [
                'โรงแรมบูติค',
                'โฮมสเตย์กลุ่ม',
                'ร้านค้าท้องถิ่น'
            ]
        }
        
        self.technology_focus = {
            'mobile_apps': ['Vue.js + Cordova', 'Flutter', 'React Native'],
            'web_systems': ['Vue.js', 'Laravel', 'Firebase'],
            'integration': ['Payment gateways', 'Maps API', 'Booking systems']
        }
    
    def get_primary_tourism_clients(self) -> List[str]:
        """Get primary tourism clients for SQL generation"""
        return self.regional_clients['tier_1'] + self.regional_clients['tier_2']
    
    def get_seasonal_sql_condition(self, season: str) -> str:
        """Get SQL condition for tourism seasons"""
        return self.tourism_seasons.get(season, {}).get('sql_condition', '')
    
    def get_client_tier_condition(self, tier: str) -> str:
        """Get SQL condition for client tiers"""
        clients = self.regional_clients.get(tier, [])
        if not clients:
            return ''
        
        conditions = []
        for client in clients:
            conditions.append(f"client ILIKE '%{client}%'")
        
        return f"({' OR '.join(conditions)})"
    
    def analyze_regional_context(self, question: str) -> Dict[str, Any]:
        """Analyze question for regional context"""
        
        question_lower = question.lower()
        
        # Tourism type detection
        tourism_types = {
            'accommodation': ['โรงแรม', 'รีสอร์ท', 'hotel', 'resort', 'ที่พัก'],
            'cultural': ['วัฒนธรรม', 'ประเพณี', 'ล้านนา', 'cultural', 'tradition'],
            'nature': ['สวน', 'ธรรมชาติ', 'ป่า', 'ดอย', 'nature', 'garden'],
            'food': ['ร้านอาหาร', 'อาหาร', 'ครัว', 'restaurant', 'food'],
            'adventure': ['ผจญภัย', 'กิจกรรม', 'adventure', 'activity']
        }
        
        detected_types = []
        for tourism_type, keywords in tourism_types.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_types.append(tourism_type)
        
        # Regional keywords
        regional_indicators = [
            'เชียงใหม่', 'ภาคเหนือ', 'ล้านนา', 'northern',
            'chiang mai', 'lanna', 'ลำปาง', 'ลำพูน'
        ]
        
        has_regional_focus = any(indicator in question_lower for indicator in regional_indicators)
        
        return {
            'tourism_types': detected_types,
            'has_regional_focus': has_regional_focus,
            'primary_type': detected_types[0] if detected_types else 'general',
            'complexity_score': len(detected_types)
        }

# =============================================================================
# company_prompts/company_b/hospitality_schema.py  
# 🏨 Hospitality-specific schema mappings
# =============================================================================

class HospitalitySchemaMapper:
    """🏨 Maps hospitality business concepts to database schema"""
    
    def __init__(self):
        self.hospitality_concepts = {
            'accommodation_systems': {
                'description': 'Hotel and resort management systems',
                'typical_features': ['booking', 'check-in', 'room management', 'guest services'],
                'sql_indicators': [
                    "client ILIKE '%โรงแรม%'",
                    "client ILIKE '%รีสอร์ท%'", 
                    "client ILIKE '%hotel%'",
                    "project_name ILIKE '%booking%'",
                    "tech_stack ILIKE '%booking%'"
                ]
            },
            'restaurant_systems': {
                'description': 'Restaurant and food service systems',
                'typical_features': ['POS', 'ordering', 'inventory', 'delivery'],
                'sql_indicators': [
                    "client ILIKE '%ร้านอาหาร%'",
                    "client ILIKE '%restaurant%'",
                    "project_name ILIKE '%POS%'",
                    "tech_stack ILIKE '%POS%'"
                ]
            },
            'tourism_platforms': {
                'description': 'Tourism information and booking platforms',
                'typical_features': ['destination info', 'activity booking', 'guides', 'reviews'],
                'sql_indicators': [
                    "client ILIKE '%ท่องเที่ยว%'",
                    "client ILIKE '%tourism%'",
                    "client ILIKE '%TAT%'",
                    "project_name ILIKE '%tourism%'"
                ]
            },
            'cultural_heritage': {
                'description': 'Cultural and heritage preservation systems',
                'typical_features': ['digital archives', 'virtual tours', 'educational content'],
                'sql_indicators': [
                    "client ILIKE '%วัฒนธรรม%'",
                    "client ILIKE '%พิพิธภัณฑ์%'",
                    "client ILIKE '%สวน%'",
                    "project_name ILIKE '%culture%'"
                ]
            }
        }
    
    def map_question_to_hospitality_domain(self, question: str) -> Dict[str, Any]:
        """Map question to specific hospitality domain"""
        
        question_lower = question.lower()
        matched_domains = []
        
        for domain, config in self.hospitality_concepts.items():
            # Check if question contains domain-specific terms
            domain_keywords = self._extract_keywords_from_sql_indicators(config['sql_indicators'])
            
            if any(keyword in question_lower for keyword in domain_keywords):
                matched_domains.append({
                    'domain': domain,
                    'description': config['description'],
                    'features': config['typical_features'],
                    'sql_conditions': config['sql_indicators']
                })
        
        return {
            'matched_domains': matched_domains,
            'primary_domain': matched_domains[0]['domain'] if matched_domains else 'general_hospitality',
            'suggested_sql_conditions': self._combine_sql_conditions(matched_domains)
        }
    
    def _extract_keywords_from_sql_indicators(self, sql_indicators: List[str]) -> List[str]:
        """Extract searchable keywords from SQL ILIKE conditions"""
        
        keywords = []
        for indicator in sql_indicators:
            # Extract text between % symbols in ILIKE conditions
            import re
            matches = re.findall(r"'%([^%]+)%'", indicator)
            keywords.extend(matches)
        
        return keywords
    
    def _combine_sql_conditions(self, matched_domains: List[Dict]) -> str:
        """Combine SQL conditions from multiple domains"""
        
        if not matched_domains:
            return ''
        
        all_conditions = []
        for domain in matched_domains:
            all_conditions.extend(domain['sql_conditions'])
        
        return f"({' OR '.join(all_conditions)})"

# =============================================================================
# company_prompts/company_b/cultural_context.py
# 🎭 Local cultural context for better responses
# =============================================================================

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

# =============================================================================
# Integration with existing system
# =============================================================================

def integrate_tourism_prompt_with_existing_system():
    """🔧 Integration helper function"""
    
    integration_guide = """
    🔧 Tourism Prompt Integration Steps:
    
    1. Add to prompt_manager.py:
    ```python
    elif tenant_id == 'company-b':
        from company_prompts.company_b.tourism_prompt import TourismPrompt
        company_config = {**config, 'company_id': tenant_id}
        self.company_prompts[tenant_id] = TourismPrompt(company_config)
    ```
    
    2. Update integration_bridge.py:
    ```python
    if tenant_id in ['company-a', 'company-b'] and self.modular_available:
        return await self.prompt_manager.process_query(question, tenant_id)
    ```
    
    3. Test tourism-specific queries:
    - "มีโปรเจคท่องเที่ยวอะไรบ้าง"
    - "ลูกค้าโรงแรมในเชียงใหม่"
    - "ระบบร้านอาหารล้านนา"
    """
    
    return integration_guide

# =============================================================================
# Testing Framework for Tourism Prompts
# =============================================================================

async def test_tourism_prompt_system():
    """🧪 Test tourism prompt system"""
    
    test_cases = [
        {
            'question': 'มีโปรเจคท่องเที่ยวอะไรบ้าง',
            'expected_focus': 'tourism_projects',
            'expected_keywords': ['ท่องเที่ยว', 'tourism', 'TAT']
        },
        {
            'question': 'ลูกค้าโรงแรมมีใครบ้าง',
            'expected_focus': 'accommodation',
            'expected_keywords': ['โรงแรม', 'hotel', 'ดุสิต']
        },
        {
            'question': 'ระบบร้านอาหารล้านนา',
            'expected_focus': 'food_service',
            'expected_keywords': ['ร้านอาหาร', 'restaurant', 'ล้านนา']
        },
        {
            'question': 'พนักงานที่มีความเชี่ยวชาญด้านวัฒนธรรม',
            'expected_focus': 'cultural_expertise',
            'expected_keywords': ['วัฒนธรรม', 'cultural', 'expertise']
        }
    ]
    
    return test_cases