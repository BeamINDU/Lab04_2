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
        """🔥 FIXED: Create enhanced interpretation prompt with data awareness"""
        
        # วิเคราะห์ข้อมูลก่อนส่งให้ AI
        data_analysis = self._analyze_results_structure(results, sql_query, question)
        
        # Format results with business context awareness
        formatted_results = self._format_results_with_data_awareness(results, data_analysis, tenant_config.tenant_id)
        
        # Generate insights and patterns
        insights = self._generate_enhanced_data_insights(results, data_analysis, tenant_config.tenant_id)
        
        if tenant_config.language == 'en':
            prompt = f"""You are a senior business analyst for {tenant_config.name} interpreting database results.

COMPANY CONTEXT:
- Business Type: {tenant_config.business_type}
- Focus Area: {schema_info.get('business_context', {}).get('primary_focus', 'Business operations')}
- Key Metrics: {', '.join(tenant_config.key_metrics)}

USER QUESTION: {question}
SQL EXECUTED: {sql_query}
RESULTS SUMMARY: {len(results)} records found

🔍 CRITICAL DATA INTERPRETATION RULES:
{self._create_data_interpretation_rules_en(data_analysis)}

{formatted_results}

ENHANCED DATA INSIGHTS:
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

🔍 กฎสำคัญในการตีความข้อมูล:
{self._create_data_interpretation_rules_th(data_analysis)}

{formatted_results}

ข้อมูลเชิงลึกขั้นสูง:
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
    
    def _create_data_interpretation_rules_en(self, data_analysis: Dict) -> str:
        """สร้างกฎการตีความข้อมูลภาษาอังกฤษ"""
        rules = []
        
        rules.append("1. Read data as it is, without misinterpretation")
        rules.append("2. Calculate percentages and numbers from actual data only")
        
        if data_analysis.get('has_null_substitutes'):
            rules.append("3. ⚠️ 'ไม่มีโปรเจค' = employees without project assignments (not a project name)")
            rules.append("4. ⚠️ 'ไม่มีบทบาท' = no defined role in system (not a job position)")
        
        if data_analysis.get('business_context', {}).get('query_type') == 'employee_assignment_analysis':
            rules.append("5. 🎯 This is assignment analysis focusing on resource allocation")
            rules.append("6. 🎯 Business impact: human resource utilization and workload balance")
        
        rules.append("7. ❌ Never create conclusions without data evidence")
        rules.append("8. ❌ Never guess or assume missing data")
        
        return '\n'.join(rules)
    
    def _generate_enhanced_data_insights(self, results: List[Dict], data_analysis: Dict, tenant_id: str) -> str:
        """สร้าง insights ที่เข้าใจข้อมูลลึกซึ้ง"""
        if not results:
            return "ไม่สามารถวิเคราะห์ได้เนื่องจากไม่มีข้อมูล"
        
        insights = []
        
        # Insights สำหรับ assignment analysis
        if data_analysis.get('business_context', {}).get('query_type') == 'employee_assignment_analysis':
            assignment_stats = data_analysis.get('employee_assignments', {})
            
            if assignment_stats:
                utilization = assignment_stats.get('utilization_rate', 0)
                without_projects = assignment_stats.get('without_projects', 0)
                
                if utilization < 80:
                    insights.append(f"⚠️ อัตราการใช้ทรัพยากรอยู่ที่ {utilization}% ซึ่งต่ำกว่าเกณฑ์มาตรฐาน")
                
                if without_projects > 0:
                    insights.append(f"💡 มีพนักงาน {without_projects} คนที่พร้อมรับงานใหม่")
                    insights.append("💼 ควรพิจารณาหาโปรเจคใหม่หรือถ่ายโอนงานจากคนที่งานเยอะ")
                
                if utilization > 90:
                    insights.append("✅ อัตราการใช้ทรัพยากรอยู่ในเกณฑ์ดี")
        
        # Insights ทั่วไป
        else:
            # วิเคราะห์ numerical patterns
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
                        insights.append(f"💰 {col}: เฉลี่ย {avg_val:,.0f} {currency}, สูงสุด {max_val:,.0f} {currency}")
                    else:
                        insights.append(f"📊 {col}: เฉลี่ย {avg_val:.1f}, ช่วง {min_val}-{max_val}")
        
        return '\n'.join(insights) if insights else "ข้อมูลมีความสมดุลและไม่พบประเด็นที่ต้องให้ความสนใจเป็นพิเศษ"
    
    def _format_general_results(self, results: List[Dict], tenant_id: str) -> str:
        """จัดรูปแบบผลลัพธ์ทั่วไป"""
        formatted = ""
        
        # แสดงผล 5 รายการแรก
        display_results = results[:5]
        
        for i, row in enumerate(display_results, 1):
            formatted += f"{i}. "
            
            for key, value in row.items():
                # จัดรูปแบบตามประเภทข้อมูล
                if key in ['salary', 'budget'] and isinstance(value, (int, float)):
                    currency = "USD" if tenant_id == 'company-c' else "บาท"
                    formatted += f"{key}: {value:,.0f} {currency}, "
                elif key in ['allocation'] and isinstance(value, float):
                    formatted += f"{key}: {value*100:.1f}%, "
                elif isinstance(value, (int, float)):
                    formatted += f"{key}: {value:,.0f}, "
                else:
                    formatted += f"{key}: {value}, "
            
            formatted = formatted.rstrip(", ") + "\n"
        
        if len(results) > 5:
            formatted += f"... และอีก {len(results) - 5} รายการ\n"
        
        return formatted
    
    def _format_results_with_data_awareness(self, results: List[Dict], data_analysis: Dict, tenant_id: str) -> str:
        """จัดรูปแบบผลลัพธ์พร้อมความเข้าใจข้อมูล"""
        if not results:
            return "ไม่มีข้อมูลที่ตรงกับคำถาม"
        
        formatted = "📊 ข้อมูลจากฐานข้อมูล:\n"
        
        # แยกข้อมูลตามประเภท
        if data_analysis.get('business_context', {}).get('query_type') == 'employee_assignment_analysis':
            formatted += self._format_assignment_analysis_results(results, data_analysis)
        else:
            formatted += self._format_general_results(results, tenant_id)
        
        return formatted
    
    def _format_assignment_analysis_results(self, results: List[Dict], data_analysis: Dict) -> str:
        """จัดรูปแบบผลลัพธ์สำหรับ assignment analysis"""
        formatted = ""
        
        # แยกพนักงานที่มีงาน vs ไม่มีงาน
        employees_with_projects = []
        employees_without_projects = []
        
        for row in results:
            project_name = str(row.get('project_name', ''))
            if 'ไม่มี' in project_name:
                employees_without_projects.append(row)
            else:
                employees_with_projects.append(row)
        
        # แสดงสถิติสรุป
        assignment_stats = data_analysis.get('employee_assignments', {})
        if assignment_stats:
            formatted += f"""
📈 สถิติการมอบหมายงาน:
• พนักงานที่มีโปรเจค: {assignment_stats.get('with_projects', 0)} คน
• พนักงานที่ไม่มีโปรเจค: {assignment_stats.get('without_projects', 0)} คน
• อัตราการใช้ทรัพยากร: {assignment_stats.get('utilization_rate', 0)}%

"""
        
        # แสดงรายละเอียดพนักงานที่มีงาน
        if employees_with_projects:
            formatted += f"👥 พนักงานที่มีโปรเจค ({len(employees_with_projects)} รายการ):\n"
            for i, row in enumerate(employees_with_projects[:5], 1):
                formatted += f"  {i}. {row.get('employee_name', 'N/A')} → {row.get('project_name', 'N/A')} ({row.get('time_allocation', '0%')})\n"
            
            if len(employees_with_projects) > 5:
                formatted += f"  ... และอีก {len(employees_with_projects) - 5} รายการ\n"
        
        # แสดงรายละเอียดพนักงานที่ไม่มีงาน
        if employees_without_projects:
            formatted += f"\n🚫 พนักงานที่ไม่มีโปรเจค ({len(employees_without_projects)} คน):\n"
            for i, row in enumerate(employees_without_projects[:5], 1):
                formatted += f"  {i}. {row.get('employee_name', 'N/A')} - {row.get('position', 'N/A')} ({row.get('department', 'N/A')})\n"
        
        return formatted
    def _analyze_results_structure(self, results: List[Dict], sql_query: str, question: str) -> Dict[str, Any]:
        """🔥 NEW: วิเคราะห์โครงสร้างข้อมูลเพื่อการตีความที่ถูกต้อง"""
        analysis = {
            'total_records': len(results),
            'has_null_substitutes': False,
            'null_substitute_patterns': [],
            'employee_assignments': {},
            'data_categories': {},
            'business_context': {}
        }
        
        if not results:
            return analysis
        
        # ตรวจหา COALESCE results (ไม่มีโปรเจค, ไม่มีบทบาท, etc.)
        for key in results[0].keys():
            values = [str(row.get(key, '')) for row in results]
            
            # หา pattern ของข้อมูลที่ถูก COALESCE
            null_substitutes = [v for v in values if 'ไม่มี' in v or v == '-' or v == '0%']
            if null_substitutes:
                analysis['has_null_substitutes'] = True
                analysis['null_substitute_patterns'].append({
                    'field': key,
                    'substitute_count': len(null_substitutes),
                    'total_count': len(values),
                    'percentage': round(len(null_substitutes) / len(values) * 100, 1),
                    'substitute_values': list(set(null_substitutes)),
                    'meaning': self._interpret_null_substitute(key, null_substitutes[0] if null_substitutes else '')
                })
        
        # วิเคราะห์ assignment patterns สำหรับคำถามเกี่ยวกับการมอบหมายงาน
        if 'แต่ละคน' in question and 'รับผิดชอบ' in question:
            analysis['business_context'] = {
                'query_type': 'employee_assignment_analysis',
                'focus': 'resource_allocation_and_workload_distribution'
            }
            
            # นับจำนวนคนที่มีงาน vs ไม่มีงาน
            employees_with_projects = []
            employees_without_projects = []
            
            for row in results:
                project_name = str(row.get('project_name', ''))
                employee_name = row.get('employee_name', '')
                
                if 'ไม่มี' in project_name:
                    employees_without_projects.append(employee_name)
                else:
                    employees_with_projects.append(employee_name)
            
            analysis['employee_assignments'] = {
                'with_projects': len(set(employees_with_projects)),
                'without_projects': len(set(employees_without_projects)),
                'total_employees': len(set([row.get('employee_name', '') for row in results])),
                'utilization_rate': round(len(set(employees_with_projects)) / len(set([row.get('employee_name', '') for row in results])) * 100, 1) if results else 0
            }
        
        return analysis
    
    def _interpret_null_substitute(self, field_name: str, substitute_value: str) -> str:
        """แปลความหมายของค่าที่ถูก substitute"""
        interpretations = {
            'project_name': {
                'ไม่มีโปรเจค': 'พนักงานที่ยังไม่ได้รับมอบหมายงาน',
                'ไม่มีงาน': 'พนักงานที่ยังไม่ได้รับมอบหมายงาน'
            },
            'project_role': {
                'ไม่มีบทบาท': 'ไม่ได้กำหนดบทบาทในโปรเจค',
                '-': 'ไม่มีข้อมูลบทบาท'
            },
            'time_allocation': {
                '0%': 'ไม่ได้จัดสรรเวลาทำงาน',
                '-': 'ไม่มีการจัดสรรเวลา'
            }
        }
        
        return interpretations.get(field_name, {}).get(substitute_value, 'ข้อมูลที่ไม่มีค่า')
    
    def _create_data_interpretation_rules_th(self, data_analysis: Dict) -> str:
        """สร้างกฎการตีความข้อมูลภาษาไทย"""
        rules = []
        
        # กฎพื้นฐาน
        rules.append("1. อ่านข้อมูลตามที่เป็น ไม่ใส่ความเข้าใจผิด")
        rules.append("2. ตัวเลขและเปอร์เซ็นต์ต้องคำนวณจากข้อมูลจริงเท่านั้น")
        
        # กฎเฉพาะสำหรับ COALESCE data
        if data_analysis.get('has_null_substitutes'):
            rules.append("3. ⚠️ 'ไม่มีโปรเจค' = พนักงานที่ไม่ได้รับมอบหมายงาน (ไม่ใช่ชื่อโปรเจค)")
            rules.append("4. ⚠️ 'ไม่มีบทบาท' = ไม่ได้กำหนดบทบาทในระบบ (ไม่ใช่ตำแหน่งงาน)")
            rules.append("5. ⚠️ '0%' = ไม่ได้จัดสรรเวลาทำงาน (ไม่ใช่ทำงาน 0 เปอร์เซ็นต์)")
        
        # กฎสำหรับ assignment analysis
        if data_analysis.get('business_context', {}).get('query_type') == 'employee_assignment_analysis':
            rules.append("6. 🎯 นี่คือการวิเคราะห์การมอบหมายงาน มุ่งเน้น resource allocation")
            rules.append("7. 🎯 ผลกระทบทางธุรกิจ: การใช้ทรัพยากรบุคคลและความสมดุลของงาน")
        
        rules.append("8. ❌ ห้ามสร้างข้อสรุปที่ไม่มีหลักฐานจากข้อมูล")
        rules.append("9. ❌ ห้ามคาดเดาหรือสมมติข้อมูลที่ไม่มี")
        
        return '\n'.join(rules)
    
    def _create_data_interpretation_rules_en(self, data_analysis: Dict) -> str:
        """สร้างกฎการตีความข้อมูลภาษาอังกฤษ"""
        rules = []
        
        rules.append("1. Read data as it is, without misinterpretation")
        rules.append("2. Calculate percentages and numbers from actual data only")
        
        if data_analysis.get('has_null_substitutes'):
            rules.append("3. ⚠️ 'ไม่มีโปรเจค' = employees without project assignments (not a project name)")
            rules.append("4. ⚠️ 'ไม่มีบทบาท' = no defined role in system (not a job position)")
        
        if data_analysis.get('business_context', {}).get('query_type') == 'employee_assignment_analysis':
            rules.append("5. 🎯 This is assignment analysis focusing on resource allocation")
            rules.append("6. 🎯 Business impact: human resource utilization and workload balance")
        
        rules.append("7. ❌ Never create conclusions without data evidence")
        rules.append("8. ❌ Never guess or assume missing data")
        
        return '\n'.join(rules)
    
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