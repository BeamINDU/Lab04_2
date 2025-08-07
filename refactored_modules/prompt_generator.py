# prompt_generator.py
# 📝 AI Prompt Generation Service

from typing import Dict, Any, List, Tuple
import logging
from .tenant_config import TenantConfig
from .schema_discovery import SchemaDiscoveryService
from .business_logic_mapper import BusinessLogicMapper

logger = logging.getLogger(__name__)

class PromptGenerator:
    """📝 Generates enhanced prompts for AI interactions"""
    
    def __init__(self, schema_service: SchemaDiscoveryService, 
                 business_mapper: BusinessLogicMapper):
        self.schema_service = schema_service
        self.business_mapper = business_mapper
    
    def create_enhanced_sql_prompt(self, question: str, schema_info: Dict, 
                                  business_logic: Dict, config: TenantConfig) -> str:
        """Create enhanced SQL generation prompt with business intelligence"""
        
        # Format schema information with business context
        schema_text = self._format_enhanced_schema(schema_info, config.language)
        
        # Format business logic rules
        business_rules = self._format_business_logic(business_logic, config.language)
        
        if config.language == 'en':
            prompt = f"""You are an expert PostgreSQL business analyst for {config.name}.

COMPANY PROFILE:
- Business Type: {config.business_type}
- Key Focus: {schema_info.get('business_context', {}).get('primary_focus', 'Business operations')}
- Client Profile: {schema_info.get('business_context', {}).get('client_profile', 'Various clients')}
- Project Scale: {schema_info.get('business_context', {}).get('project_scale', 'Various scales')}

{schema_text}

{business_rules}

ADVANCED SQL GENERATION RULES:
1. ALWAYS use explicit column names (never SELECT *)
2. ALWAYS include LIMIT (max 20 rows) unless doing aggregation/counting
3. Use proper table aliases: employees e, projects p, employee_projects ep
4. Format money appropriately based on business context
5. Use ILIKE for case-insensitive text searches
6. Handle NULL values with COALESCE where appropriate
7. Use proper JOINs with clear relationships
8. Add meaningful ORDER BY clauses for better insights
9. Group related data logically for business analysis
10. Use subqueries when necessary for complex business logic

BUSINESS INTELLIGENCE PATTERNS:
- Employee analysis: Include department, position, salary context
- Project analysis: Include budget, client, team size, status
- Performance metrics: Use aggregations with business meaning
- Cross-table analysis: Join tables to provide comprehensive insights

SQL QUALITY STANDARDS:
- Readable formatting with proper indentation
- Business-meaningful column aliases
- Appropriate data type handling
- Optimized for PostgreSQL performance

USER QUESTION: {question}

Generate only the PostgreSQL query that provides comprehensive business insights:"""
        
        else:  # Thai
            prompt = f"""คุณคือนักวิเคราะห์ฐานข้อมูล PostgreSQL เชี่ยวชาญสำหรับ {config.name}

ข้อมูลบริษัท:
- ประเภทธุรกิจ: {config.business_type}
- จุดเน้นหลัก: {schema_info.get('business_context', {}).get('primary_focus', 'การดำเนินธุรกิจ')}
- กลุ่มลูกค้า: {schema_info.get('business_context', {}).get('client_profile', 'ลูกค้าหลากหลาย')}
- ขนาดโปรเจค: {schema_info.get('business_context', {}).get('project_scale', 'ขนาดหลากหลาย')}

{schema_text}

{business_rules}

กฎการสร้าง SQL ขั้นสูง:
1. ใช้ชื่อคอลัมน์ที่ชัดเจนเสมอ (ห้ามใช้ SELECT *)
2. ใส่ LIMIT เสมอ (ไม่เกิน 20 แถว) ยกเว้นการนับหรือสรุปข้อมูล
3. ใช้ table aliases: employees e, projects p, employee_projects ep
4. จัดรูปแบบเงินให้เหมาะสมตามบริบทธุรกิจ
5. ใช้ ILIKE สำหรับการค้นหาข้อความ (ไม่สนใจตัวใหญ่-เล็ก)
6. จัดการค่า NULL ด้วย COALESCE ที่เหมาะสม
7. ใช้ JOIN ที่ถูกต้องและชัดเจน
8. เพิ่ม ORDER BY ที่มีความหมายเพื่อให้ insight ที่ดี
9. จัดกลุ่มข้อมูลอย่างมีเหตุผลสำหรับการวิเคราะห์ธุรกิจ
10. ใช้ subquery เมื่อจำเป็นสำหรับ business logic ที่ซับซ้อน

รูปแบบ Business Intelligence:
- วิเคราะห์พนักงาน: รวมบริบทแผนก ตำแหน่ง เงินเดือน
- วิเคราะห์โปรเจค: รวมงบประมาณ ลูกค้า ขนาดทีม สถานะ
- วัดผลการปฏิบัติงาน: ใช้การสรุปข้อมูลที่มีความหมายทางธุรกิจ
- วิเคราะห์ข้ามตาราง: เชื่อมตารางเพื่อให้ insight ที่ครอบคลุม

มาตรฐานคุณภาพ SQL:
- จัดรูปแบบที่อ่านง่ายด้วยการเยื้องที่ถูกต้อง
- ตั้งชื่อ alias ที่มีความหมายทางธุรกิจ
- จัดการ data type อย่างเหมาะสม
- เพิ่มประสิทธิภาพสำหรับ PostgreSQL

คำถามผู้ใช้: {question}

สร้างเฉพาะ PostgreSQL query ที่ให้ business insights ที่ครอบคลุม:"""
        
        return prompt
    
    def create_enhanced_interpretation_prompt(self, question: str, sql_query: str, 
                                            results: List[Dict], tenant_config: TenantConfig,
                                            schema_info: Dict) -> str:
        """Create enhanced interpretation prompt with business intelligence"""
        
        # Format results with business context
        formatted_results = self._format_results_with_context(results, tenant_config.tenant_id)
        
        # Generate insights and patterns
        insights = self._generate_data_insights(results, tenant_config.tenant_id)
        
        if tenant_config.language == 'en':
            prompt = f"""You are a senior business analyst for {tenant_config.name} interpreting database results.

COMPANY CONTEXT:
- Business Type: {tenant_config.business_type}
- Focus Area: {schema_info.get('business_context', {}).get('primary_focus', 'Business operations')}
- Key Metrics: {', '.join(tenant_config.key_metrics)}

USER QUESTION: {question}
SQL EXECUTED: {sql_query}
RESULTS SUMMARY: {len(results)} records found

{formatted_results}

DATA INSIGHTS:
{insights}

RESPONSE GUIDELINES:
1. Start with direct answer addressing the specific question
2. Provide key business insights from the data
3. Highlight important trends, patterns, or anomalies
4. Add relevant business context and implications
5. Use professional yet accessible language
6. Include quantitative details with proper formatting
7. Suggest actionable next steps if appropriate
8. Keep response focused and valuable for business decision-making

FORMATTING STANDARDS:
- Use bullet points for multiple insights
- Bold important numbers and key findings
- Group related information logically
- Include percentage calculations where meaningful
- Provide context for numbers (comparisons, benchmarks)

Generate comprehensive business analysis response:"""
        
        else:  # Thai
            prompt = f"""คุณคือนักวิเคราะห์ธุรกิจอาวุโสสำหรับ {tenant_config.name} ที่ตีความผลลัพธ์จากฐานข้อมูล

บริบทบริษัท:
- ประเภทธุรกิจ: {tenant_config.business_type}
- จุดเน้น: {schema_info.get('business_context', {}).get('primary_focus', 'การดำเนินธุรกิจ')}
- ตัวชี้วัดหลัก: {', '.join(tenant_config.key_metrics)}

คำถามผู้ใช้: {question}
SQL ที่ใช้: {sql_query}
สรุปผลลัพธ์: พบข้อมูล {len(results)} รายการ

{formatted_results}

ข้อมูลเชิงลึก:
{insights}

แนวทางการตอบ:
1. เริ่มด้วยคำตอบที่ตรงประเด็นสำหรับคำถามที่ถาม
2. ให้ข้อมูลเชิงลึกทางธุรกิจที่สำคัญจากข้อมูล
3. เน้นแนวโน้ม รูปแบบ หรือความผิดปกติที่สำคัญ
4. เพิ่มบริบทธุรกิจที่เกี่ยวข้องและผลกระทบ
5. ใช้ภาษาที่เป็นมืออาชีพแต่เข้าใจง่าย
6. รวมรายละเอียดเชิงปริมาณด้วยการจัดรูปแบบที่เหมาะสม
7. แนะนำขั้นตอนต่อไปที่สามารถปฏิบัติได้หากเหมาะสม
8. รักษาการตอบให้มุ่งเน้นและมีคุณค่าสำหรับการตัดสินใจทางธุรกิจ

มาตรฐานการจัดรูปแบบ:
- ใช้ bullet points สำหรับข้อมูลเชิงลึกหลายๆ ข้อ
- ทำตัวหนาสำหรับตัวเลขสำคัญและการค้นพบหลัก
- จัดกลุ่มข้อมูลที่เกี่ยวข้องอย่างมีเหตุผล
- รวมการคำนวณเปอร์เซ็นต์ที่มีความหมาย
- ให้บริบทสำหรับตัวเลข (การเปรียบเทียบ มาตรฐาน)

สร้างการวิเคราะห์ธุรกิจที่ครอบคลุม:"""
        
        return prompt
    
    def _format_enhanced_schema(self, schema_info: Dict, language: str) -> str:
        """Format enhanced schema information with business context"""
        if language == 'en':
            formatted = f"DATABASE SCHEMA:\n"
            formatted += f"Business Context: {schema_info.get('business_context', {}).get('primary_focus', 'N/A')}\n\n"
        else:
            formatted = f"โครงสร้างฐานข้อมูล:\n"
            formatted += f"บริบทธุรกิจ: {schema_info.get('business_context', {}).get('primary_focus', 'ไม่ระบุ')}\n\n"
        
        tables = schema_info.get('tables', {})
        for table_name, table_info in tables.items():
            if language == 'en':
                formatted += f"📋 TABLE: {table_name}\n"
                formatted += f"   Description: {table_info.get('description', 'N/A')}\n"
                formatted += f"   Business Value: {table_info.get('business_significance', 'N/A')}\n"
                formatted += f"   Key Insights: {table_info.get('key_insights', 'N/A')}\n"
                formatted += f"   Columns:\n"
            else:
                formatted += f"📋 ตาราง: {table_name}\n"
                formatted += f"   คำอธิบาย: {table_info.get('description', 'ไม่ระบุ')}\n"
                formatted += f"   ความสำคัญทางธุรกิจ: {table_info.get('business_significance', 'ไม่ระบุ')}\n"
                formatted += f"   ข้อมูลเชิงลึก: {table_info.get('key_insights', 'ไม่ระบุ')}\n"
                formatted += f"   คอลัมน์:\n"
            
            for column in table_info.get('columns', []):
                formatted += f"      • {column}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_business_logic(self, business_logic: Dict, language: str) -> str:
        """Format business logic rules for AI understanding"""
        if not business_logic:
            return ""
        
        if language == 'en':
            formatted = "BUSINESS LOGIC MAPPINGS:\n"
        else:
            formatted = "การแปลความหมายทางธุรกิจ:\n"
        
        for category, rules in business_logic.items():
            if language == 'en':
                formatted += f"• {category.replace('_', ' ').title()}:\n"
            else:
                category_thai = {
                    'employee_levels': 'ระดับพนักงาน',
                    'project_sizes': 'ขนาดโปรเจค',
                    'departments': 'แผนกงาน',
                    'time_periods': 'ช่วงเวลา',
                    'performance_indicators': 'ตัวชี้วัดผลงาน',
                    'project_types': 'ประเภทโปรเจค',
                    'regional_focus': 'เน้นพื้นที่',
                    'market_tiers': 'ระดับตลาด',
                    'geographic_regions': 'ภูมิภาค'
                }
                formatted += f"• {category_thai.get(category, category)}:\n"
            
            for term, condition in rules.items():
                formatted += f"  - {term}: {condition}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_results_with_context(self, results: List[Dict], tenant_id: str) -> str:
        """Format database results with business context"""
        if not results:
            return "ไม่พบข้อมูลที่ตรงกับคำถาม"
        
        formatted = "ข้อมูลจากฐานข้อมูล:\n"
        
        # Show first 10 results with formatting
        for i, row in enumerate(results[:10], 1):
            formatted += f"{i}. "
            for key, value in row.items():
                # Format based on data type and business context
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    if tenant_id == 'company-c':
                        formatted += f"{key}: ${value:,.0f}, "
                    else:
                        formatted += f"{key}: {value:,.0f} บาท, "
                elif key in ['allocation'] and isinstance(value, float):
                    formatted += f"{key}: {value*100:.1f}%, "
                elif isinstance(value, (int, float)):
                    formatted += f"{key}: {value:,.0f}, "
                else:
                    formatted += f"{key}: {value}, "
            formatted = formatted.rstrip(", ") + "\n"
        
        if len(results) > 10:
            formatted += f"... และอีก {len(results) - 10} รายการ\n"
        
        return formatted
    
    def _generate_data_insights(self, results: List[Dict], tenant_id: str) -> str:
        """Generate business insights from query results"""
        if not results:
            return "ไม่สามารถวิเคราะห์ได้เนื่องจากไม่มีข้อมูล"
        
        insights = []
        
        # Analyze numerical patterns
        numerical_columns = []
        for key, value in results[0].items():
            if isinstance(value, (int, float)) and key not in ['id']:
                numerical_columns.append(key)
        
        for col in numerical_columns:
            values = [row.get(col, 0) for row in results if row.get(col) is not None]
            if values:
                avg_val = sum(values) / len(values)
                max_val = max(values)
                min_val = min(values)
                
                if col in ['salary', 'budget']:
                    currency = "USD" if tenant_id == 'company-c' else "บาท"
                    insights.append(f"- {col}: เฉลี่ย {avg_val:,.0f} {currency}, สูงสุด {max_val:,.0f} {currency}, ต่ำสุด {min_val:,.0f} {currency}")
                else:
                    insights.append(f"- {col}: เฉลี่ย {avg_val:.1f}, สูงสุด {max_val}, ต่ำสุด {min_val}")
        
        # Analyze categorical patterns
        categorical_columns = []
        for key, value in results[0].items():
            if isinstance(value, str) and key not in ['name', 'email', 'description']:
                categorical_columns.append(key)
        
        for col in categorical_columns:
            values = [row.get(col) for row in results if row.get(col)]
            if values:
                unique_count = len(set(values))
                most_common = max(set(values), key=values.count)
                insights.append(f"- {col}: {unique_count} ประเภท, พบ '{most_common}' มากที่สุด")
        
        return "\n".join(insights) if insights else "ไม่พบรูปแบบที่น่าสนใจในข้อมูล"