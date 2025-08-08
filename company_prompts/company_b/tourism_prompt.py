from ..base_prompt import BaseCompanyPrompt
from .regional_rules import NorthernThailandRules
from .hospitality_schema import HospitalitySchemaMapper
from .cultural_context import LocalCulturalContext
import logger
import datetime
from typing import Dict, Any, List, Set
class TourismPrompt(BaseCompanyPrompt):
    """🏨 Tourism & Hospitality Prompt System (Northern Thailand)"""
    
    def __init__(self, company_config: Dict[str, Any]):
        super().__init__(company_config)
        
        # Tourism-specific components
        self.regional_rules = NorthernThailandRules()
        self.schema_mapper = HospitalitySchemaMapper()
        self.cultural_context = LocalCulturalContext()
        
        logger.info("🏨 Tourism & Hospitality Prompt System ready")
    
    def generate_sql_prompt(self, question: str, schema_info: Dict[str, Any]) -> str:
        """🎯 Generate Tourism-specific SQL prompt"""
        
        self.usage_stats['queries_processed'] += 1
        self.usage_stats['last_used'] = datetime.now().isoformat()
        
        tourism_context = self._analyze_tourism_context(question)
        
        prompt = f"""คุณคือนักวิเคราะห์ระบบท่องเที่ยวสำหรับ {self.company_name}

🏨 บริบทธุรกิจ: เทคโนโลยีท่องเที่ยวและการต้อนรับ ภาคเหนือ
🌿 เน้นพื้นที่: เชียงใหม่ และภาคเหนือของประเทศไทย
💰 งบประมาณโปรเจค: 300,000 - 800,000 บาท
🎯 ลูกค้าเป้าหมาย: {', '.join(self.regional_rules.get_tourism_clients())}

📊 โครงสร้างฐานข้อมูลท่องเที่ยว:
{self._format_tourism_schema(schema_info)}

🔧 กฎการสร้าง SQL สำหรับธุรกิจท่องเที่ยว:
{self._get_tourism_sql_rules()}

🌟 ความรู้เฉพาะด้านท่องเที่ยวภาคเหนือ:
{self._get_regional_tourism_logic(tourism_context)}

🎭 บริบทวัฒนธรรมท้องถิ่น:
{self.cultural_context.get_cultural_considerations()}

คำถาม: {question}

สร้าง PostgreSQL query ที่เน้นธุรกิจท่องเที่ยวและวัฒนธรรมท้องถิ่น:"""

        self.usage_stats['successful_generations'] += 1
        return prompt
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """📋 Tourism business rules"""
        return {
            'tourism_seasons': {
                'high_season': 'EXTRACT(MONTH FROM start_date) IN (11, 12, 1, 2)',
                'low_season': 'EXTRACT(MONTH FROM start_date) IN (6, 7, 8, 9)',
                'festival_season': 'EXTRACT(MONTH FROM start_date) IN (4, 11)'  # Songkran, Loy Krathong
            },
            'project_scales': {
                'local': 'budget < 400000',
                'regional': 'budget BETWEEN 400000 AND 600000',
                'provincial': 'budget > 600000'
            },
            'tourism_expertise': {
                'cultural_guide': 'skills ILIKE \'%cultural%\' OR skills ILIKE \'%local%\'',
                'hospitality_specialist': 'skills ILIKE \'%hospitality%\' OR position ILIKE \'%hotel%\'',
                'tourism_tech': 'skills ILIKE \'%tourism%\' AND skills ILIKE \'%technical%\''
            }
        }