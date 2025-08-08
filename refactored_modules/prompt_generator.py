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
        """🧠 Smart interpretation prompt ที่ประมวลผลข้อมูลก่อนส่งให้ AI"""
        
        # 🔍 วิเคราะห์ประเภทคำถามและข้อมูล
        question_context = self._analyze_question_context(question, sql_query, results)
        
        # 📊 ประมวลผลข้อมูลให้เป็น structured format
        processed_data = self._process_results_intelligently(results, question_context)
        
        # 🎯 สร้าง context-aware prompt แบบ dynamic
        return self._create_dynamic_interpretation_prompt(
            question, processed_data, question_context, tenant_config, schema_info
        )

    def _analyze_question_context(self, question: str, sql_query: str, results: List[Dict]) -> Dict[str, Any]:
        """🔍 วิเคราะห์ context ของคำถามและผลลัพธ์"""
        
        question_lower = question.lower()
        sql_upper = sql_query.upper()
        
        context = {
            'query_type': 'general',
            'data_structure': 'simple',
            'response_style': 'analytical',
            'focus_area': 'summary'
        }
        
        # 🎯 ตรวจจับ assignment queries
        if ('แต่ละคน' in question_lower or 'each' in question_lower) and 'LEFT JOIN' in sql_upper:
            context.update({
                'query_type': 'assignment',
                'data_structure': 'relational', 
                'response_style': 'listing',
                'focus_area': 'individual_items'
            })
        
        # 🎯 ตรวจจับ project queries
        elif 'โปรเจค' in question_lower or 'project' in question_lower:
            context.update({
                'query_type': 'project',
                'response_style': 'listing',
                'focus_area': 'items_with_details'
            })
        
        # 🎯 ตรวจจับ counting/aggregation queries
        elif any(word in question_lower for word in ['กี่', 'จำนวน', 'how many', 'count']):
            context.update({
                'query_type': 'counting',
                'response_style': 'statistical',
                'focus_area': 'numbers_and_trends'
            })
        
        # 🎯 ตรวจจับ financial queries
        elif any(word in question_lower for word in ['งบประมาณ', 'เงินเดือน', 'budget', 'salary']):
            context.update({
                'query_type': 'financial',
                'response_style': 'analytical',
                'focus_area': 'numbers_with_context'
            })
        
        return context

    def _process_results_intelligently(self, results: List[Dict], context: Dict[str, Any]) -> Dict[str, Any]:
        """📊 ประมวลผลข้อมูลอย่างชาญฉลาดตาม context"""
        
        if not results:
            return {'type': 'empty', 'message': 'ไม่มีข้อมูล'}
        
        processed = {
            'raw_count': len(results),
            'summary': {},
            'highlights': [],
            'formatted_display': ''
        }
        
        # 🎯 Assignment query processing
        if context['query_type'] == 'assignment':
            return self._process_assignment_data(results)
        
        # 🎯 Project query processing
        elif context['query_type'] == 'project':
            return self._process_project_data(results)
        
        # 🎯 Financial query processing
        elif context['query_type'] == 'financial':
            return self._process_financial_data(results)
        
        # 🎯 Counting query processing
        elif context['query_type'] == 'counting':
            return self._process_counting_data(results)
        
        # 🎯 General processing
        else:
            return self._process_general_data(results)

    def _process_assignment_data(self, results: List[Dict]) -> Dict[str, Any]:
        """👥 ประมวลผลข้อมูล assignment แบบ smart"""
        
        employees_with_projects = []
        employees_without_projects = []
        
        # Group by employee
        employee_data = {}
        for row in results:
            emp_name = row.get('name', 'Unknown')
            project = row.get('project_name', '')
            role = row.get('role', '')
            
            if emp_name not in employee_data:
                employee_data[emp_name] = {
                    'name': emp_name,
                    'projects': [],
                    'position': row.get('position', ''),
                    'department': row.get('department', '')
                }
            
            # Handle project assignment
            if project and 'ไม่มี' not in str(project):
                role_display = role if role and 'ไม่มี' not in str(role) else 'ไม่ระบุบทบาท'
                employee_data[emp_name]['projects'].append({
                    'name': project,
                    'role': role_display
                })
        
        # Categorize employees
        for emp_name, emp_info in employee_data.items():
            if emp_info['projects']:
                for project in emp_info['projects']:
                    employees_with_projects.append({
                        'employee': emp_name,
                        'project': project['name'],
                        'role': project['role']
                    })
            else:
                employees_without_projects.append({
                    'employee': emp_name,
                    'position': emp_info['position'],
                    'department': emp_info['department']
                })
        
        # Create structured display
        display_lines = []
        
        if employees_with_projects:
            display_lines.append("พนักงานที่มีโปรเจค:")
            for item in employees_with_projects[:10]:  # Limit display
                display_lines.append(f"• {item['employee']} → {item['project']} ({item['role']})")
        
        if employees_without_projects:
            display_lines.append("\nพนักงานที่ยังไม่มีโปรเจค:")
            for item in employees_without_projects[:5]:  # Limit display
                display_lines.append(f"• {item['employee']} ({item['position']} - {item['department']})")
        
        return {
            'type': 'assignment',
            'employees_with_projects': len(employees_with_projects),
            'employees_without_projects': len(employees_without_projects),
            'total_employees': len(employee_data),
            'display_data': employees_with_projects + employees_without_projects,
            'formatted_display': '\n'.join(display_lines),
            'summary': {
                'with_projects': len(employees_with_projects),
                'without_projects': len(employees_without_projects),
                'utilization_rate': round(len(employees_with_projects) / len(employee_data) * 100, 1) if employee_data else 0
            }
        }

    def _process_project_data(self, results: List[Dict]) -> Dict[str, Any]:
        """🚀 ประมวลผลข้อมูล project แบบ smart"""
        
        projects = []
        total_budget = 0
        
        for row in results:
            project_info = {
                'name': row.get('name', 'Unknown'),
                'client': row.get('client', 'Unknown'),
                'budget': row.get('budget', 0),
                'status': row.get('status', 'Unknown')
            }
            projects.append(project_info)
            
            if isinstance(project_info['budget'], (int, float)):
                total_budget += project_info['budget']
        
        # Sort by budget (descending)
        projects.sort(key=lambda x: x['budget'] if isinstance(x['budget'], (int, float)) else 0, reverse=True)
        
        # Create display
        display_lines = []
        active_projects = [p for p in projects if p['status'] == 'active']
        completed_projects = [p for p in projects if p['status'] == 'completed']
        
        if active_projects:
            display_lines.append("โปรเจคที่กำลังดำเนินการ:")
            for proj in active_projects[:5]:
                budget_display = f"{proj['budget']:,.0f} บาท" if isinstance(proj['budget'], (int, float)) else "ไม่ระบุ"
                display_lines.append(f"• {proj['name']} - {proj['client']} ({budget_display})")
        
        if completed_projects:
            display_lines.append("\nโปรเจคที่เสร็จแล้ว:")
            for proj in completed_projects[:3]:
                budget_display = f"{proj['budget']:,.0f} บาท" if isinstance(proj['budget'], (int, float)) else "ไม่ระบุ"
                display_lines.append(f"• {proj['name']} - {proj['client']} ({budget_display})")
        
        return {
            'type': 'project',
            'total_projects': len(projects),
            'active_projects': len(active_projects),
            'completed_projects': len(completed_projects),
            'total_budget': total_budget,
            'avg_budget': total_budget / len(projects) if projects else 0,
            'display_data': projects,
            'formatted_display': '\n'.join(display_lines),
            'highlights': [
                f"โปรเจคทั้งหมด: {len(projects)} โปรเจค",
                f"งบประมาณรวม: {total_budget:,.0f} บาท",
                f"งบประมาณเฉลี่ย: {total_budget / len(projects):,.0f} บาท" if projects else "ไม่มีข้อมูลงบประมาณ"
            ]
        }

    def _process_financial_data(self, results: List[Dict]) -> Dict[str, Any]:
        """💰 ประมวลผลข้อมูลทางการเงิน"""
        
        amounts = []
        for row in results:
            for key, value in row.items():
                if key in ['salary', 'budget', 'amount', 'price'] and isinstance(value, (int, float)):
                    amounts.append(value)
        
        if not amounts:
            return {'type': 'financial', 'message': 'ไม่พบข้อมูลทางการเงิน'}
        
        return {
            'type': 'financial',
            'total_amount': sum(amounts),
            'avg_amount': sum(amounts) / len(amounts),
            'max_amount': max(amounts),
            'min_amount': min(amounts),
            'count': len(amounts),
            'formatted_display': f"ยอดรวม: {sum(amounts):,.0f} บาท, เฉลี่ย: {sum(amounts)/len(amounts):,.0f} บาท, สูงสุด: {max(amounts):,.0f} บาท"
        }

    def _process_counting_data(self, results: List[Dict]) -> Dict[str, Any]:
        """🔢 ประมวลผลข้อมูลการนับ"""
        
        return {
            'type': 'counting',
            'total_count': len(results),
            'formatted_display': f"จำนวนทั้งหมด: {len(results)} รายการ"
        }

    def _process_general_data(self, results: List[Dict]) -> Dict[str, Any]:
        """📊 ประมวลผลข้อมูลทั่วไป"""
        
        return {
            'type': 'general',
            'total_records': len(results),
            'sample_data': results[:5],
            'formatted_display': f"พบข้อมูล {len(results)} รายการ"
        }

    def _create_dynamic_interpretation_prompt(self, question: str, processed_data: Dict[str, Any], 
                                            context: Dict[str, Any], tenant_config: TenantConfig,
                                            schema_info: Dict) -> str:
        """🎯 สร้าง dynamic prompt ตาม context และข้อมูลที่ประมวลผลแล้ว"""
        
        if tenant_config.language == 'th':
            base_prompt = f"""คุณเป็นผู้ช่วยที่ตอบคำถามตรงประเด็นสำหรับ {tenant_config.name}

    🎯 คำถาม: {question}
    📊 ประเภทข้อมูล: {processed_data.get('type', 'ทั่วไป')}
    📈 จำนวนข้อมูล: {processed_data.get('raw_count', 0)} รายการ

    """
        else:
            base_prompt = f"""You are a direct answer assistant for {tenant_config.name}

    🎯 Question: {question}
    📊 Data Type: {processed_data.get('type', 'general')}
    📈 Record Count: {processed_data.get('raw_count', 0)} records

    """
        
        # 🎯 เพิ่ม context-specific guidance
        if context['response_style'] == 'listing':
            if tenant_config.language == 'th':
                base_prompt += """⚠️ สำคัญ: ตอบแบบแสดงรายการ
    • แสดงรายชื่อและรายละเอียดที่เป็นประโยชน์
    • จัดกลุ่มข้อมูลอย่างเป็นระเบียบ
    • หลีกเลี่ยงการวิเคราะห์สถิติยาวๆ

    """
            else:
                base_prompt += """⚠️ Important: List-style response
    • Show names and useful details
    • Organize data systematically  
    • Avoid lengthy statistical analysis

    """
        
        elif context['response_style'] == 'statistical':
            if tenant_config.language == 'th':
                base_prompt += """⚠️ สำคัญ: ตอบแบบวิเคราะห์สถิติ
    • เน้นตัวเลขและเปอร์เซ็นต์
    • แสดงแนวโน้มและการเปรียบเทียบ
    • ให้ insights ทางธุรกิจ

    """
        
        # 🎯 เพิ่มข้อมูลที่ประมวลผลแล้ว
        base_prompt += f"""📋 ข้อมูลที่ประมวลผลแล้ว:
    {processed_data.get('formatted_display', 'ไม่มีข้อมูลเฉพาะ')}

    """
        
        # 🎯 เพิ่ม summary หาก context เหมาะสม
        if 'summary' in processed_data:
            summary = processed_data['summary']
            if tenant_config.language == 'th':
                base_prompt += f"""💡 สรุปสำคัญ: {summary}

    """
        
        if tenant_config.language == 'th':
            base_prompt += """กรุณาตอบคำถามโดยใช้ข้อมูลที่ประมวลผลแล้วข้างต้น เน้นความชัดเจนและตรงประเด็น:"""
        else:
            base_prompt += """Please answer the question using the processed data above, focusing on clarity and directness:"""
        
        return base_prompt

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