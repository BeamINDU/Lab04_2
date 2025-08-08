from ..base_prompt import BaseCompanyPrompt
from .global_rules import InternationalBusinessRules
from .multi_currency import MultiCurrencyHandler
from .compliance_global import GlobalComplianceRules
import logger
import datetime
from typing import Dict, Any, List, Set

class InternationalPrompt(BaseCompanyPrompt):
    """🌍 International Operations Prompt System"""
    
    def __init__(self, company_config: Dict[str, Any]):
        super().__init__(company_config)
        
        # International-specific components
        self.global_rules = InternationalBusinessRules()
        self.currency_handler = MultiCurrencyHandler()
        self.global_compliance = GlobalComplianceRules()
        
        logger.info("🌍 International Operations Prompt System ready")
    
    def generate_sql_prompt(self, question: str, schema_info: Dict[str, Any]) -> str:
        """🎯 Generate International-specific SQL prompt"""
        
        self.usage_stats['queries_processed'] += 1
        self.usage_stats['last_used'] = datetime.now().isoformat()
        
        global_context = self._analyze_global_context(question)
        
        prompt = f"""You are a PostgreSQL expert for {self.company_name} (International Operations)

🌍 Business Context: Global software solutions and cross-border operations
💱 Multi-Currency Operations: USD (primary), EUR, GBP, SGD, AUD
💰 Project Scale: $1M - $4M USD for international projects
🎯 Target Clients: {', '.join(self.global_rules.get_international_clients())}

📊 International Database Schema:
{self._format_international_schema(schema_info)}

🔧 SQL Rules for International Business:
{self._get_international_sql_rules()}

💼 Global Business Intelligence:
{self._get_international_business_logic(global_context)}

🌐 Cross-Border Compliance:
{self.global_compliance.get_international_compliance_rules()}

Question: {question}

Generate PostgreSQL query focusing on international business operations:"""

        self.usage_stats['successful_generations'] += 1
        return prompt
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """📋 International business rules"""
        return {
            'market_tiers': {
                'tier_1': 'contract_value_usd > 3000000',
                'tier_2': 'contract_value_usd BETWEEN 1000000 AND 3000000',
                'emerging': 'contract_value_usd < 1000000'
            },
            'geographic_regions': {
                'apac': 'country IN (\'Singapore\', \'Australia\', \'Japan\', \'South Korea\')',
                'emea': 'country IN (\'United Kingdom\', \'Germany\', \'France\', \'Netherlands\')',
                'americas': 'country IN (\'United States\', \'Canada\', \'Brazil\')'
            },
            'project_complexity': {
                'global_enterprise': 'budget > 2000000 AND market_type = \'global\'',
                'regional_expansion': 'budget BETWEEN 1000000 AND 2000000',
                'market_entry': 'budget < 1000000 AND market_type = \'international\''
            }
        }