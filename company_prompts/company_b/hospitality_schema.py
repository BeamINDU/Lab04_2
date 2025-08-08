from typing import Dict, Any, List, Set

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