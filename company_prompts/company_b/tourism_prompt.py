# company_prompts/company_b/tourism_prompt.py
# 🏨 Complete Tourism & Hospitality Prompt System

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from company_prompts.base_prompt import BaseCompanyPrompt
from typing import Dict, Any, List, Set
from datetime import datetime
import re

# Import shared logger
from shared_components.logging_config import logger

# Import existing components if available
try:
    from refactored_modules.business_logic_mapper import BusinessLogicMapper
    from refactored_modules.schema_discovery import SchemaDiscoveryService
    EXISTING_COMPONENTS_AVAILABLE = True
except ImportError:
    EXISTING_COMPONENTS_AVAILABLE = False

class TourismPrompt(BaseCompanyPrompt):
    """🏨 Tourism & Hospitality Prompt System for Northern Thailand"""
    
    def __init__(self, company_config: Dict[str, Any]):
        super().__init__(company_config)
        
        # Tourism-specific components
        self.regional_rules = NorthernThailandRules()
        self.hospitality_mapper = HospitalitySchemaMapper()
        self.cultural_context = LocalCulturalContext()
        
        # Use existing business logic if available
        if EXISTING_COMPONENTS_AVAILABLE:
            try:
                self.business_mapper = BusinessLogicMapper()
                self.tourism_business_rules = self.business_mapper.get_business_logic('company-b')
            except Exception as e:
                logger.warning(f"Failed to load existing business mapper: {e}")
                self.tourism_business_rules = self._get_fallback_tourism_rules()
        else:
            self.tourism_business_rules = self._get_fallback_tourism_rules()
        
        logger.info(f"🏨 Tourism Prompt System initialized for {self.company_name}")
    
    def generate_sql_prompt(self, question: str, schema_info: Dict[str, Any]) -> str:
        """🎯 Generate Tourism-specific SQL prompt"""
        
        self.usage_stats['queries_processed'] += 1
        self.usage_stats['last_used'] = datetime.now().isoformat()
        
        # Analyze tourism context in question
        tourism_context = self._analyze_tourism_context(question)
        
        # Get regional insights
        regional_insights = self.regional_rules.get_contextual_insights(question)
        
        prompt = f"""คุณคือนักวิเคราะห์ระบบท่องเที่ยวเชี่ยวชาญสำหรับ {self.company_name}

🏨 บริบทธุรกิจ: เทคโนโลยีท่องเที่ยวและการต้อนรับ สาขาภาคเหนือ
🌿 พื้นที่เป้าหมาย: เชียงใหม่ ลำปาง ลำพูน และจังหวัดภาคเหนือ
💰 งบประมาณโปรเจค: 300,000 - 800,000 บาท (โปรเจคระดับภูมิภาค)
🎯 ลูกค้าหลัก: {', '.join(self.regional_rules.get_primary_tourism_clients())}

📊 โครงสร้างฐานข้อมูลท่องเที่ยว:
{self._format_tourism_schema(schema_info)}

🔧 กฎการสร้าง SQL เฉพาะธุรกิจท่องเที่ยว:
{self._get_tourism_sql_rules()}

🌟 ความรู้เฉพาะด้านท่องเที่ยวภาคเหนือ:
{self._format_regional_tourism_logic(tourism_context)}

🎭 บริบทวัฒนธรรมและท้องถิ่น:
{self.cultural_context.get_cultural_considerations(question)}

💡 Tourism Business Intelligence:
{self._get_tourism_business_insights(regional_insights)}

คำถาม: {question}

สร้าง PostgreSQL query ที่เน้นธุรกิจท่องเที่ยวและวัฒนธรรมท้องถิ่นภาคเหนือ:"""

        self.usage_stats['successful_generations'] += 1
        return prompt
    
    def format_response(self, question: str, results: List[Dict], metadata: Dict) -> str:
        """🎨 Format Tourism response with cultural context"""
        
        if not results:
            return f"ไม่พบข้อมูลท่องเที่ยวที่เกี่ยวข้องกับ: {question}"
        
        response = f"🏨 การวิเคราะห์ระบบท่องเที่ยวภาคเหนือ - {self.company_name}\n\n"
        
        # Analyze if this is tourism-specific data
        is_tourism_data = self._is_tourism_related_data(results)
        
        if is_tourism_data:
            response += "🌿 ข้อมูลโปรเจคท่องเที่ยวและการต้อนรับ:\n"
        else:
            response += "👥 ข้อมูลทีมงานและโครงสร้างองค์กร:\n"
        
        # Display results with tourism context
        for i, row in enumerate(results[:12], 1):
            response += f"{i:2d}. "
            
            # Format each field appropriately
            for key, value in row.items():
                if 'budget' in key.lower() and isinstance(value, (int, float)):
                    response += f"{key}: {value:,.0f} บาท, "
                elif 'client' in key.lower() and value:
                    # Add tourism context to client names
                    tourism_context = self._get_client_tourism_context(value)
                    response += f"{key}: {value}{tourism_context}, "
                elif 'project_name' in key.lower() and value:
                    # Highlight tourism projects
                    tourism_indicator = self._get_project_tourism_indicator(value)
                    response += f"{key}: {value}{tourism_indicator}, "
                else:
                    response += f"{key}: {value}, "
            
            response = response.rstrip(', ') + "\n"
        
        # Add tourism insights
        response += f"\n🎯 Tourism Intelligence:\n"
        response += f"• จำนวนรายการ: {len(results)} รายการ\n"
        response += f"• ประเภทธุรกิจ: ท่องเที่ยวและการต้อนรับ ภาคเหนือ\n"
        response += f"• เทคโนโลジี: Vue.js, Firebase, Mobile Apps สำหรับการท่องเที่ยว\n"
        
        # Add regional insights
        regional_insights = self._analyze_regional_context(results)
        if regional_insights:
            response += f"• ข้อมูลเชิงลึกภูมิภาค: {regional_insights}\n"
        
        return response
    
    def _analyze_tourism_context(self, question: str) -> Dict[str, Any]:
        """🔍 Analyze tourism context in question"""
        
        question_lower = question.lower()
        
        tourism_keywords = {
            'accommodation': ['โรงแรม', 'รีสอร์ท', 'hotel', 'resort', 'ที่พัก'],
            'attractions': ['ท่องเที่ยว', 'tourism', 'สถานที่ท่องเที่ยว', 'แหล่งท่องเที่ยว'],
            'cultural': ['วัฒนธรรม', 'culture', 'ล้านนา', 'lanna', 'ประเพณี', 'tradition'],
            'regional': ['เชียงใหม่', 'chiang mai', 'ภาคเหนือ', 'northern', 'ลำปาง', 'ลำพูน'],
            'food': ['ร้านอาหาร', 'restaurant', 'อาหาร', 'food', 'ครัว', 'kitchen'],
            'nature': ['สวน', 'garden', 'ธรรมชาติ', 'nature', 'ป่า', 'forest', 'ดอย', 'mountain']
        }
        
        detected_categories = []
        for category, keywords in tourism_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_categories.append(category)
        
        return {
            'categories': detected_categories,
            'is_tourism_focused': len(detected_categories) > 0,
            'primary_focus': detected_categories[0] if detected_categories else 'general',
            'complexity': len(detected_categories)
        }
    
    def _format_tourism_schema(self, schema_info: Dict[str, Any]) -> str:
        """📊 Format schema with tourism context"""
        
        base_schema = """• employees: id, name, department, position, salary, hire_date, email
  - เน้น: ทีมงานท่องเที่ยว, ความเชี่ยวชาญภูมิภาค, ทักษะวัฒนธรรมท้องถิ่น
• projects: id, name, client, budget, status, start_date, end_date, tech_stack  
  - เน้น: โปรเจคท่องเที่ยว, ระบบโรงแรม, แอพท่องเที่ยว, งบประมาณ 300k-800k
• employee_projects: employee_id, project_id, role, allocation
  - เน้น: การจัดทีมงานท่องเที่ยว, ความเชี่ยวชาญเฉพาะด้าน"""
        
        return base_schema
    
    def _get_tourism_sql_rules(self) -> str:
        """🔧 Tourism-specific SQL generation rules"""
        
        return """1. ค้นหาโปรเจคท่องเที่ยว: 
   - client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%โรงแรม%' OR client ILIKE '%tourism%'
   - client ILIKE '%ดุสิต%' OR client ILIKE '%TAT%' OR client ILIKE '%สวน%'

2. เน้นลูกค้าภาคเหนือ:
   - client ILIKE '%เชียงใหม่%' OR client ILIKE '%ภาคเหนือ%'
   - client ILIKE '%ล้านนา%' OR client ILIKE '%lanna%'

3. งบประมาณระดับภูมิภาค:
   - budget BETWEEN 300000 AND 800000 (โปรเจคขนาดกลาง)
   - budget > 600000 (โปรเจคใหญ่ระดับจังหวัด)

4. เทคโนโลยีท่องเที่ยว:
   - tech_stack ILIKE '%Vue.js%' OR tech_stack ILIKE '%Firebase%'
   - tech_stack ILIKE '%Mobile%' OR tech_stack ILIKE '%App%'

5. ทีมงานเฉพาะทาง:
   - position ILIKE '%tourism%' OR position ILIKE '%regional%'
   - department = 'IT' AND salary BETWEEN 32000 AND 70000"""
    
    def _format_regional_tourism_logic(self, tourism_context: Dict[str, Any]) -> str:
        """🌟 Format regional tourism business logic"""
        
        logic_lines = []
        
        if tourism_context['is_tourism_focused']:
            focus = tourism_context['primary_focus']
            
            if focus == 'accommodation':
                logic_lines.append("• มุ่งเน้นโรงแรมและรีสอร์ท: ระบบจอง, ระบบจัดการ, Mobile check-in")
                logic_lines.append("• ลูกค้าหลัก: โรงแรมดุสิต, รีสอร์ทบูติค, โฮมสเตย์")
                
            elif focus == 'attractions':
                logic_lines.append("• เน้นสถานที่ท่องเที่ยว: แอพนำทาง, ข้อมูลสถานที่, ระบบจองตั๋ว")
                logic_lines.append("• ลูกค้าหลัก: TAT, สวนพฤกษศาสตร์, พิพิธภัณฑ์")
                
            elif focus == 'cultural':
                logic_lines.append("• เน้นวัฒนธรรมล้านนา: ระบบแนะนำวัฒนธรรม, เส้นทางท่องเที่ยววัฒนธรรม")
                logic_lines.append("• องค์ความรู้: ประเพณีท้องถิ่น, ศิลปะ, อาหาร, ภาษาถิ่น")
                
            elif focus == 'food':
                logic_lines.append("• เน้นร้านอาหาร: ระบบ POS, ระบบสั่งอาหาร, แอพรีวิว")
                logic_lines.append("• อาหารพื้นเมือง: ข้าวซอย, แกงฮังเล, ไส้อั่ว, น้ำพริกน้ำปู")
        else:
            # General tourism logic
            logic_lines.append("• โปรเจคท่องเที่ยวทั่วไป: ระบบจัดการลูกค้า, แอพท่องเที่ยว")
            logic_lines.append("• เทคโนโลยีสำหรับท่องเที่ยว: Vue.js, Firebase, Mobile development")
        
        logic_lines.append("• การตลาดภูมิภาค: SEO ท้องถิ่น, Social Media, ภาษาถิ่น")
        logic_lines.append("• มาตรฐานการบริการ: ความปลอดภัย, คุณภาพ, ความเป็นมิตรกับสิ่งแวดล้อม")
        
        return '\n'.join(logic_lines)
    
    def _get_tourism_business_insights(self, regional_insights: Dict[str, Any]) -> str:
        """💡 Get tourism business intelligence insights"""
        
        insights = []
        
        insights.append("• การแบ่งแยกตลาด: นักท่องเที่ยวไทย vs ต่างชาติ")
        insights.append("• ช่วงเวลาท่องเที่ยว: High season (Nov-Feb), Low season (Jun-Sep)")
        insights.append("• ประเภทท่องเที่ยว: วัฒนธรรม, ธรรมชาติ, อาหาร, ผจญภัย")
        insights.append("• เทคโนโลยีที่นิยม: Mobile apps, QR codes, Contactless payment")
        insights.append("• ความท้าทาย: ภาษาท้องถิ่น, การเข้าถึงเทคโนโลยี, มาตรฐานบริการ")
        
        return '\n'.join(insights)
    
    def _is_tourism_related_data(self, results: List[Dict]) -> bool:
        """🔍 Check if results contain tourism-related data"""
        
        if not results:
            return False
        
        tourism_indicators = [
            'ท่องเที่ยว', 'tourism', 'โรงแรม', 'hotel', 'ดุสิต', 'TAT',
            'สวน', 'garden', 'ร้านอาหาร', 'restaurant', 'เชียงใหม่'
        ]
        
        # Check in client names and project names
        for row in results:
            for key, value in row.items():
                if isinstance(value, str):
                    if any(indicator in value.lower() for indicator in tourism_indicators):
                        return True
        
        return False
    
    def _get_client_tourism_context(self, client_name: str) -> str:
        """🏨 Add tourism context to client names"""
        
        context_map = {
            'ดุสิต': ' 🏨',
            'โรงแรม': ' 🏨',
            'hotel': ' 🏨',
            'ท่องเที่ยว': ' ✈️',
            'tourism': ' ✈️',
            'TAT': ' 🌟',
            'สวน': ' 🌿',
            'garden': ' 🌿',
            'ร้านอาหาร': ' 🍜',
            'restaurant': ' 🍜',
            'ล้านนา': ' 🎭',
            'lanna': ' 🎭'
        }
        
        client_lower = client_name.lower()
        for keyword, icon in context_map.items():
            if keyword in client_lower:
                return icon
        
        return ''
    
    def _get_project_tourism_indicator(self, project_name: str) -> str:
        """🎯 Add tourism indicator to project names"""
        
        project_lower = project_name.lower()
        
        if any(word in project_lower for word in ['โรงแรม', 'hotel']):
            return ' [ระบบโรงแรม]'
        elif any(word in project_lower for word in ['ท่องเที่ยว', 'tourism']):
            return ' [ระบบท่องเที่ยว]'
        elif any(word in project_lower for word in ['mobile', 'app']):
            return ' [แอพมือถือ]'
        elif any(word in project_lower for word in ['pos', 'ร้านอาหาร']):
            return ' [ระบบร้านอาหาร]'
        
        return ''
    
    def _analyze_regional_context(self, results: List[Dict]) -> str:
        """🌿 Analyze regional context from results"""
        
        insights = []
        
        # Count tourism vs non-tourism projects
        tourism_count = 0
        total_budget = 0
        
        for row in results:
            if 'budget' in row and isinstance(row['budget'], (int, float)):
                total_budget += row['budget']
            
            # Check if this is tourism-related
            is_tourism = False
            for key, value in row.items():
                if isinstance(value, str) and any(word in value.lower() for word in ['ท่องเที่ยว', 'โรงแรม', 'tourism']):
                    is_tourism = True
                    break
            
            if is_tourism:
                tourism_count += 1
        
        if tourism_count > 0:
            tourism_percentage = (tourism_count / len(results)) * 100
            insights.append(f"โปรเจคท่องเที่ยว {tourism_percentage:.0f}% จากทั้งหมด")
        
        if total_budget > 0:
            avg_budget = total_budget / len(results)
            insights.append(f"งบประมาณเฉลี่ย {avg_budget:,.0f} บาท")
        
        return ', '.join(insights) if insights else "โปรเจคระดับภูมิภาค"
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """📋 Tourism business rules"""
        return {
            'tourism_seasons': {
                'high_season': 'EXTRACT(MONTH FROM start_date) IN (11, 12, 1, 2)',
                'cool_season': 'EXTRACT(MONTH FROM start_date) IN (11, 12, 1, 2)',
                'hot_season': 'EXTRACT(MONTH FROM start_date) IN (3, 4, 5)',
                'rainy_season': 'EXTRACT(MONTH FROM start_date) IN (6, 7, 8, 9, 10)',
                'festival_season': 'EXTRACT(MONTH FROM start_date) IN (4, 11)'  # Songkran, Loy Krathong
            },
            'project_scales': {
                'local': 'budget < 400000',
                'regional': 'budget BETWEEN 400000 AND 600000',
                'provincial': 'budget > 600000'
            },
            'tourism_types': {
                'accommodation': "client ILIKE '%โรงแรม%' OR client ILIKE '%รีสอร์ท%'",
                'attractions': "client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%สวน%'",
                'food_beverage': "client ILIKE '%ร้านอาหาร%' OR client ILIKE '%ครัว%'",
                'cultural': "client ILIKE '%วัฒนธรรม%' OR client ILIKE '%ล้านนา%'"
            }
        }
    
    def _load_schema_mappings(self) -> Dict[str, Any]:
        """🗄️ Tourism schema mappings"""
        return {
            'core_tables': ['employees', 'projects', 'employee_projects'],
            'tourism_focus_fields': {
                'projects': ['client', 'budget', 'tech_stack'],
                'employees': ['position', 'department', 'salary']
            },
            'regional_keywords': ['เชียงใหม่', 'ภาคเหนือ', 'ล้านนา', 'ท่องเที่ยว', 'โรงแรม']
        }
    
    def _get_fallback_tourism_rules(self) -> Dict[str, Any]:
        """Fallback tourism rules if existing mapper not available"""
        return {
            'tourism_projects': {
                'hotel_systems': "client ILIKE '%โรงแรม%' OR client ILIKE '%ดุสิต%'",
                'tourism_apps': "client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%TAT%'",
                'restaurant_pos': "client ILIKE '%ร้านอาหาร%' OR client ILIKE '%อาหาร%'",
                'regional_projects': "client ILIKE '%เชียงใหม่%' OR client ILIKE '%ภาคเหนือ%'"
            },
            'budget_ranges': {
                'small_regional': 'budget < 400000',
                'medium_regional': 'budget BETWEEN 400000 AND 600000',
                'large_regional': 'budget > 600000'
            }
        }


# Supporting Classes for Tourism System

class NorthernThailandRules:
    """🌿 Northern Thailand regional business rules"""
    
    def __init__(self):
        self.primary_clients = [
            'โรงแรมดุสิต เชียงใหม่',
            'การท่องเที่ยวแห่งประเทศไทย',
            'สวนพฤกษศาสตร์เชียงใหม่',
            'กลุ่มร้านอาหารล้านนา',
            'มหาวิทยาลัยเชียงใหม่'
        ]
        
        self.regional_keywords = {
            'locations': ['เชียงใหม่', 'ลำปาง', 'ลำพูน', 'เชียงราย', 'ภาคเหนือ'],
            'culture': ['ล้านนา', 'lanna', 'วัฒนธรรม', 'ประเพณี', 'ผ้าไทย'],
            'food': ['ข้าวซอย', 'แกงฮังเล', 'ไส้อั่ว', 'น้ำพริกน้ำปู', 'อาหารเหนือ'],
            'attractions': ['ดอยสุเทพ', 'วัดพระธาตุ', 'ตลาดวโรรส', 'ถนนคนเดิน']
        }
    
    def get_primary_tourism_clients(self) -> List[str]:
        """Get primary tourism clients"""
        return self.primary_clients
    
    def get_contextual_insights(self, question: str) -> Dict[str, Any]:
        """Get contextual insights based on question"""
        
        question_lower = question.lower()
        
        relevant_keywords = []
        for category, keywords in self.regional_keywords.items():
            matches = [kw for kw in keywords if kw in question_lower]
            if matches:
                relevant_keywords.extend([(category, kw) for kw in matches])
        
        return {
            'relevant_keywords': relevant_keywords,
            'regional_focus': len(relevant_keywords) > 0,
            'cultural_context': any(cat == 'culture' for cat, _ in relevant_keywords),
            'food_context': any(cat == 'food' for cat, _ in relevant_keywords)
        }


class HospitalitySchemaMapper:
    """🏨 Maps hospitality concepts to database schema"""
    
    def __init__(self):
        self.hospitality_mappings = {
            'accommodation': {
                'keywords': ['โรงแรม', 'รีสอร์ท', 'hotel', 'resort', 'ที่พัก'],
                'sql_conditions': "client ILIKE '%โรงแรม%' OR client ILIKE '%รีสอร์ท%'"
            },
            'restaurant': {
                'keywords': ['ร้านอาหาร', 'restaurant', 'อาหาร', 'ครัว'],
                'sql_conditions': "client ILIKE '%ร้านอาหาร%' OR client ILIKE '%อาหาร%'"
            },
            'tourism_service': {
                'keywords': ['ท่องเที่ยว', 'tourism', 'นำเที่ยว', 'guide'],
                'sql_conditions': "client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%tourism%'"
            }
        }
    
    def map_tourism_concepts(self, question: str) -> Dict[str, str]:
        """Map tourism concepts to SQL conditions"""
        
        question_lower = question.lower()
        mapped_conditions = {}
        
        for concept, mapping in self.hospitality_mappings.items():
            if any(keyword in question_lower for keyword in mapping['keywords']):
                mapped_conditions[concept] = mapping['sql_conditions']
        
        return mapped_conditions


class LocalCulturalContext:
    """🎭 Provides local cultural context for better responses"""
    
    def __init__(self):
        self.cultural_elements = {
            'language': {
                'lanna_terms': ['ล้านนา', 'คำเมือง', 'ภาษาถิ่น'],
                'respect_terms': ['ครับ', 'ค่ะ', 'น้อง', 'พี่', 'ลุง', 'ป้า']
            },
            'traditions': {
                'festivals': ['สงกรานต์', 'ลอยกระทง', 'ยี่เป็ง', 'ประเพณีไทยใหญ่'],
                'crafts': ['ผ้าไทย', 'เครื่องเงิน', 'ร่มบ่อสร้าง', 'เครื่องปั้นดินเผา']
            },
            'hospitality': {
                'service_style': ['น้ำใจเหนือ', 'การต้อนรับแบบล้านนา', 'ความเป็นมิตร'],
                'local_wisdom': ['ปรัชญาเศรษฐกิจพอเพียง', 'วิถีชีวิตล้านนา']
            }
        }
    
    def get_cultural_considerations(self, question: str) -> str:
        """Get cultural considerations for the question"""
        
        considerations = []
        question_lower = question.lower()
        
        # Check for cultural keywords in question
        if any(term in question_lower for term in ['วัฒนธรรม', 'ประเพณี', 'ล้านนา']):
            considerations.extend([
                "• คำนึงถึงวัฒนธรรมล้านนา: ภาษาถิ่น, ประเพณี, วิถีชีวิต",
                "• เน้นความเป็นมิตรและน้ำใจของคนเหนือ",
                "• รักษาอัตลักษณ์ท้องถิ่นในการให้บริการ"
            ])
        
        if any(term in question_lower for term in ['บริการ', 'service', 'ลูกค้า']):
            considerations.extend([
                "• บริการแบบล้านนา: อบอุ่น, เป็นมิตร, ใส่ใจ",
                "• การสื่อสารด้วยภาษาที่เข้าใจง่าย",
                "• เน้นประสบการณ์ที่แท้จริงของท้องถิ่น"
            ])
        
        # Default considerations
        if not considerations:
            considerations = [
                "• รักษาเอกลักษณ์ภาคเหนือในการพัฒนาระบบ",
                "• เน้นความเรียบง่ายและใช้งานง่าย", 
                "• คำนึงถึงความหลากหลายทางวัฒนธรรม"
            ]
        
        return '\n'.join(considerations[:3])  # Return max 3 considerations