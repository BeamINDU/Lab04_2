# business_logic_mapper.py
# 🏢 Business Logic Mapping and SQL Pattern Management

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BusinessLogicMapper:
    """🏢 Maps business concepts to database logic"""
    
    def __init__(self):
        self.business_logic_mappings = self._load_business_logic_mappings()
        self.sql_patterns = self._load_sql_patterns()
    
    def _load_business_logic_mappings(self) -> Dict[str, Dict]:
        """Enhanced business logic mappings for natural language interpretation"""
        return {
            'company-a': {
                'employee_levels': {
                    'junior': 'salary < 40000',
                    'mid': 'salary BETWEEN 40000 AND 60000', 
                    'senior': 'salary > 60000 OR position ILIKE \'%senior%\'',
                    'executive': 'salary > 100000 OR position ILIKE \'%manager%\' OR position ILIKE \'%director%\' OR position ILIKE \'%ceo%\' OR position ILIKE \'%cto%\''
                },
                'project_sizes': {
                    'small': 'budget < 500000',
                    'medium': 'budget BETWEEN 500000 AND 2000000',
                    'large': 'budget > 2000000',
                    'enterprise': 'budget > 3000000'
                },
                'departments': {
                    'core': "department IN ('IT', 'Management')",
                    'support': "department IN ('Sales', 'HR')",
                    'technical': "department = 'IT'",
                    'business': "department IN ('Sales', 'Management')"
                },
                'time_periods': {
                    'recent': "hire_date > CURRENT_DATE - INTERVAL '1 year'",
                    'experienced': "hire_date < CURRENT_DATE - INTERVAL '2 years'",
                    'veteran': "hire_date < CURRENT_DATE - INTERVAL '5 years'"
                },
                'performance_indicators': {
                    'high_performer': '(salary > 60000 AND EXTRACT(YEAR FROM hire_date) < 2023)',
                    'top_earner': 'salary > 80000',
                    'key_player': "position ILIKE '%lead%' OR position ILIKE '%senior%' OR position ILIKE '%architect%'"
                }
            },
            'company-b': {
                'project_types': {
                    'tourism': "client ILIKE '%โรงแรม%' OR client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%รีสอร์ท%'",
                    'hospitality': "client ILIKE '%โรงแรม%' OR client ILIKE '%ดุสิต%'",
                    'government': "client ILIKE '%การท่องเที่ยวแห่งประเทศไทย%'",
                    'education': "client ILIKE '%มหาวิทยาลัย%' OR client ILIKE '%วิทยา%'"
                },
                'regional_focus': {
                    'northern': "client ILIKE '%เชียงใหม่%' OR client ILIKE '%ล้านนา%'",
                    'local': "client NOT ILIKE '%กรุงเทพ%'",
                    'cultural': "client ILIKE '%ล้านนา%' OR client ILIKE '%วัฒนธรรม%'"
                }
            },
            'company-c': {
                'market_tiers': {
                    'global': "contract_value_usd > 2000000",
                    'enterprise': "contract_value_usd > 1000000", 
                    'regional': "contract_value_usd BETWEEN 500000 AND 1000000",
                    'startup': "contract_value_usd < 500000"
                },
                'geographic_regions': {
                    'americas': "country IN ('USA', 'Canada', 'Mexico')",
                    'europe': "country IN ('UK', 'Germany', 'France', 'Netherlands')",
                    'asia_pacific': "country IN ('Singapore', 'Australia', 'Japan', 'South Korea')",
                    'emerging': "country NOT IN ('USA', 'UK', 'Germany', 'Singapore', 'Australia')"
                }
            }
        }
    
    def _load_sql_patterns(self) -> Dict[str, str]:
        """Pre-defined SQL patterns for common business queries"""
        return {
            'employee_count_by_department': """
                SELECT 
                    department,
                    COUNT(*) as employee_count,
                    ROUND(AVG(salary), 0) as avg_salary,
                    TO_CHAR(AVG(salary), 'FM999,999,999') || ' บาท' as formatted_avg_salary
                FROM employees 
                GROUP BY department 
                ORDER BY employee_count DESC;
            """,
            'top_earners': """
                SELECT 
                    name,
                    position,
                    department,
                    TO_CHAR(salary, 'FM999,999,999') || ' บาท' as formatted_salary
                FROM employees 
                ORDER BY salary DESC 
                LIMIT {limit};
            """,
            'high_budget_projects': """
                SELECT 
                    p.name as project_name,
                    p.client,
                    TO_CHAR(p.budget, 'FM999,999,999') || ' บาท' as formatted_budget,
                    p.status,
                    COUNT(ep.employee_id) as team_size
                FROM projects p
                LEFT JOIN employee_projects ep ON p.id = ep.project_id
                WHERE p.budget > {threshold}
                GROUP BY p.id, p.name, p.client, p.budget, p.status
                ORDER BY p.budget DESC;
            """,
            'employee_project_allocation': """
                SELECT 
                    e.name as employee_name,
                    e.position,
                    p.name as project_name,
                    TO_CHAR(p.budget, 'FM999,999,999') || ' บาท' as project_budget,
                    ep.role as project_role,
                    ROUND(ep.allocation * 100, 1) || '%' as time_allocation
                FROM employees e
                JOIN employee_projects ep ON e.id = ep.employee_id
                JOIN projects p ON ep.project_id = p.id
                WHERE {where_condition}
                ORDER BY p.budget DESC, e.name;
            """,
            'department_performance': """
                SELECT 
                    e.department,
                    COUNT(DISTINCT e.id) as total_employees,
                    COUNT(DISTINCT ep.project_id) as active_projects,
                    TO_CHAR(AVG(e.salary), 'FM999,999,999') || ' บาท' as avg_salary,
                    TO_CHAR(SUM(e.salary), 'FM999,999,999') || ' บาท' as total_payroll
                FROM employees e
                LEFT JOIN employee_projects ep ON e.id = ep.employee_id
                LEFT JOIN projects p ON ep.project_id = p.id AND p.status = 'active'
                GROUP BY e.department
                ORDER BY total_payroll DESC;
            """
        }
    
    def get_business_logic(self, tenant_id: str) -> Dict[str, Any]:
        """Get business logic mappings for specific tenant"""
        return self.business_logic_mappings.get(tenant_id, {})
    
    def get_sql_pattern(self, pattern_name: str) -> str:
        """Get SQL pattern by name"""
        return self.sql_patterns.get(pattern_name, '')
    
    def apply_business_mapping(self, concept: str, tenant_id: str) -> str:
        """Apply business concept mapping to SQL condition"""
        logic_mappings = self.business_logic_mappings.get(tenant_id, {})
        
        for category, mappings in logic_mappings.items():
            if concept in mappings:
                return mappings[concept]
        
        return concept  # Return original if no mapping found