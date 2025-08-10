import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from company_prompts.base_prompt import BaseCompanyPrompt
from typing import Dict, Any, List
from datetime import datetime
from shared_components.logging_config import logger

class InternationalPrompt(BaseCompanyPrompt):
    """🌍 International Operations Prompt - Global Business Focus"""
    
    def __init__(self, company_config: Dict[str, Any]):
        super().__init__(company_config)
        
        # 🌍 International Business Data
        self.international_data = {
            # Global Markets
            'markets': {
                'north_america': {
                    'countries': ['USA', 'Canada'],
                    'currency': 'USD',
                    'clients': ['MegaCorp International'],
                    'time_zones': ['EST', 'PST']
                },
                'europe': {
                    'countries': ['UK', 'Germany', 'Netherlands'],
                    'currency': 'EUR/GBP',
                    'clients': ['Education Global Network', 'Tech Solutions Europe'],
                    'time_zones': ['GMT', 'CET']
                },
                'asia_pacific': {
                    'countries': ['Singapore', 'Australia', 'Japan'],
                    'currency': 'SGD/AUD/JPY',
                    'clients': ['Global Finance Corp', 'PayGlobal Ltd'],
                    'time_zones': ['SGT', 'AEST', 'JST']
                }
            },
            
            # Global Currencies
            'currencies': {
                'primary': ['USD', 'EUR', 'GBP'],
                'secondary': ['SGD', 'AUD', 'CAD'],
                'rates': {
                    'USD': 1.0,
                    'EUR': 0.85,
                    'GBP': 0.80,
                    'SGD': 1.35,
                    'AUD': 1.50
                }
            },
            
            # Global Projects
            'project_types': {
                'fintech': ['Cross-border payments', 'Multi-currency wallets', 'International banking'],
                'education': ['Global learning platforms', 'Multi-language CMS', 'International certification'],
                'enterprise': ['Global ERP systems', 'International compliance', 'Cross-border collaboration']
            },
            
            # Global Clients
            'major_clients': [
                'MegaCorp International (USA)',
                'Education Global Network (UK)', 
                'Global Finance Corp (Singapore)',
                'PayGlobal Ltd (Australia)',
                'Tech Solutions Europe (Germany)'
            ],
            
            # Business Keywords
            'keywords': {
                'financial': ['revenue', 'budget', 'usd', 'profit', 'payment', 'currency'],
                'global': ['international', 'global', 'worldwide', 'cross-border', 'overseas'],
                'clients': ['client', 'customer', 'partner', 'megacorp', 'payglobal'],
                'projects': ['project', 'platform', 'system', 'solution', 'development'],
                'operations': ['operations', 'business', 'management', 'process', 'workflow']
            }
        }
        
        logger.info(f"🌍 InternationalPrompt initialized for {self.company_name}")
    
    # ========================================================================
    # 🎯 CORE METHODS
    # ========================================================================
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """🎯 Main processing method for international queries"""
        
        try:
            self.usage_stats['queries_processed'] += 1
            self.usage_stats['last_used'] = datetime.now().isoformat()
            
            # Detect query type
            if self._is_greeting(question):
                return self._create_international_greeting()
            elif self._is_financial_query(question):
                return self._create_financial_response(question)
            elif self._is_global_query(question):
                return self._create_global_response(question)
            elif self._is_client_query(question):
                return self._create_client_response(question)
            else:
                return self._create_general_response(question)
                
        except Exception as e:
            logger.error(f"❌ International processing failed: {e}")
            return {
                'success': False,
                'answer': f"System error: {str(e)}",
                'error': str(e),
                'tenant_id': self.company_id
            }
    
    def generate_sql_prompt(self, question: str, schema_info: Dict[str, Any]) -> str:
        """🎯 Generate international business SQL prompt"""
        
        # Detect query focus
        query_focus = self._detect_query_focus(question)
        currency_hint = self._get_currency_hint(query_focus)
        
        prompt = f"""You are an International Business Analyst for {self.company_name}

🌍 Business Context: Global Software Solutions & Cross-border Operations
💱 Currencies: USD (primary), EUR, GBP, SGD, AUD - Multi-currency support
🌎 Markets: North America, Europe, Asia-Pacific
🎯 Focus: {query_focus}

📊 Database Schema:
• employees: id, name, department, position, salary, hire_date, email
• projects: id, name, client, budget, status, start_date, end_date, tech_stack
• employee_projects: employee_id, project_id, role, allocation
• international_contracts: contract_value_usd, currency, governing_law
• international_payments: amount_usd, currency, exchange_rate

🔧 International SQL Rules:
1. Always convert to USD: budget * exchange_rate AS budget_usd
2. Multi-currency display: CONCAT(amount, ' ', currency) AS amount_display
3. Global clients: client ILIKE '%International%' OR client ILIKE '%Global%'
4. Time zones: Consider TIMESTAMP WITH TIME ZONE
5. Always use LEFT JOIN for international tables
6. LIMIT 20 for performance

💱 Currency Context: {currency_hint}

Question: {question}

Generate PostgreSQL query for international operations:"""

        return prompt
    
    def format_response(self, question: str, results: List[Dict], metadata: Dict) -> str:
        """🎨 Format international business response"""
        
        if not results:
            return f"No international data found for: {question}"
        
        response = f"🌍 Global Business Analysis - {self.company_name}\n\n"
        response += f"Query: {question}\n\n"
        
        # Display results with international formatting
        for i, row in enumerate(results[:15], 1):
            response += f"{i:2d}. "
            for key, value in row.items():
                if 'budget' in key.lower() or 'revenue' in key.lower():
                    if isinstance(value, (int, float)):
                        # Format as international currency
                        response += f"{key}: ${value:,.0f} USD, "
                    else:
                        response += f"{key}: {value}, "
                elif 'client' in key.lower() and value:
                    # Add market region
                    region = self._get_client_region(value)
                    response += f"{key}: {value} {region}, "
                else:
                    response += f"{key}: {value}, "
            response = response.rstrip(', ') + "\n"
        
        # Add international insights
        insights = self._generate_international_insights(results)
        response += f"\n💡 Global Insights: {insights}"
        
        return response
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """📋 International business rules"""
        return {
            'focus': 'international_operations_multi_currency',
            'primary_currency': 'USD',
            'supported_currencies': list(self.international_data['currencies']['rates'].keys()),
            'major_markets': list(self.international_data['markets'].keys()),
            'client_base': 'global_enterprise'
        }
    
    def _load_schema_mappings(self) -> Dict[str, Any]:
        """🗄️ International schema mappings"""
        return {
            'main_tables': ['employees', 'projects', 'international_contracts', 'international_payments'],
            'currency_fields': ['budget', 'contract_value_usd', 'amount_usd'],
            'international_keywords': self.international_data['keywords']
        }
    
    # ========================================================================
    # 🔧 HELPER METHODS
    # ========================================================================
    
    def _is_greeting(self, question: str) -> bool:
        """Check if greeting"""
        greetings = ['hello', 'hi', 'help', 'who are you', 'สวัสดี']
        return any(word in question.lower() for word in greetings)
    
    def _is_financial_query(self, question: str) -> bool:
        """Check if financial query"""
        return any(keyword in question.lower() 
                  for keyword in self.international_data['keywords']['financial'])
    
    def _is_global_query(self, question: str) -> bool:
        """Check if global operations query"""
        return any(keyword in question.lower()
                  for keyword in self.international_data['keywords']['global'])
    
    def _is_client_query(self, question: str) -> bool:
        """Check if client-related query"""
        return any(keyword in question.lower()
                  for keyword in self.international_data['keywords']['clients'])
    
    def _detect_query_focus(self, question: str) -> str:
        """Detect the main focus of the query"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['revenue', 'budget', 'usd', 'profit']):
            return 'financial_analysis'
        elif any(word in question_lower for word in ['client', 'customer', 'partner']):
            return 'client_management'
        elif any(word in question_lower for word in ['project', 'development', 'platform']):
            return 'project_portfolio'
        else:
            return 'general_operations'
    
    def _get_currency_hint(self, query_focus: str) -> str:
        """Get currency context hint"""
        hints = {
            'financial_analysis': 'Multi-currency revenue analysis, USD conversion required',
            'client_management': 'Client contracts in various currencies (USD, EUR, GBP, SGD)',
            'project_portfolio': 'Project budgets normalized to USD for comparison',
            'general_operations': 'Global operations with multi-currency support'
        }
        return hints.get(query_focus, 'Multi-currency international operations')
    
    def _get_client_region(self, client_name: str) -> str:
        """Get client's market region"""
        client_lower = client_name.lower()
        
        for market, data in self.international_data['markets'].items():
            for client in data['clients']:
                if any(word in client_lower for word in client.lower().split()):
                    region_names = {
                        'north_america': '🇺🇸',
                        'europe': '🇪🇺', 
                        'asia_pacific': '🌏'
                    }
                    return region_names.get(market, '')
        return ''
    
    def _generate_international_insights(self, results: List[Dict]) -> str:
        """Generate international business insights"""
        
        if not results:
            return "No data for analysis"
        
        insights = []
        
        # Count and analyze
        total_count = len(results)
        insights.append(f"{total_count} records")
        
        # Financial analysis
        financial_values = []
        currencies_found = set()
        
        for row in results:
            for key, value in row.items():
                if 'budget' in key.lower() or 'revenue' in key.lower():
                    if isinstance(value, (int, float)):
                        financial_values.append(value)
                if 'currency' in key.lower() and value:
                    currencies_found.add(value)
        
        if financial_values:
            total_value = sum(financial_values)
            avg_value = total_value / len(financial_values)
            insights.append(f"Total: ${total_value:,.0f} USD")
            insights.append(f"Average: ${avg_value:,.0f} USD")
        
        if currencies_found:
            insights.append(f"Currencies: {', '.join(currencies_found)}")
        
        # Market analysis
        regions_mentioned = []
        for market in self.international_data['markets'].keys():
            if any(market.replace('_', ' ') in str(row).lower() for row in results):
                regions_mentioned.append(market.replace('_', ' ').title())
        
        if regions_mentioned:
            insights.append(f"Markets: {', '.join(regions_mentioned)}")
        
        insights.append("Global operations scale")
        
        return " | ".join(insights)
    
    def _create_international_greeting(self) -> Dict[str, Any]:
        """Create international greeting response"""
        
        answer = f"""Hello! I'm the AI Assistant for {self.company_name}

🌍 Global Software Solutions & Cross-border Operations

Our International Expertise:
• Multi-currency software platforms (USD, EUR, GBP, SGD, AUD)
• Cross-border payment systems
• Global compliance frameworks  
• International team collaboration tools

🌎 Market Coverage:
• North America: USA, Canada
• Europe: UK, Germany, Netherlands
• Asia-Pacific: Singapore, Australia, Japan

🏢 Major Clients:
• MegaCorp International (USA) - $2.8M USD
• Global Finance Corp (Singapore) - $3.2M USD  
• Education Global Network (UK) - $2.25M USD

🎯 Example Questions:
• "Which international projects exist?"
• "What's our USD revenue breakdown?"
• "How many global clients do we have?"
• "Show me multi-currency contract analysis"

How can I help you with our global operations today?"""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'international_greeting_{self.model}',
            'tenant_id': self.company_id
        }
    
    def _create_financial_response(self, question: str) -> Dict[str, Any]:
        """Create financial analysis response"""
        
        answer = f"""🌍 Global Financial Analysis - {self.company_name}

Query: {question}

💰 Multi-Currency Revenue Portfolio:

1. Global E-commerce Platform - MegaCorp International 🇺🇸
   • Contract Value: $2,800,000 USD
   • Status: Active | Payment Terms: Milestone-based
   • Technology: Enterprise-scale React, Node.js, AWS

2. International Banking API - Global Finance Corp 🌏
   • Contract Value: $3,200,000 USD (converted from SGD)
   • Status: Active | Payment Terms: Net 30
   • Technology: Microservices, Security frameworks

3. Multi-language CMS - Education Global Network 🇪🇺
   • Contract Value: $2,250,000 USD (converted from £1.8M GBP)
   • Status: Active | Payment Terms: Monthly
   • Technology: International localization, Multi-language

💱 Currency Breakdown:
• USD Revenue: $8,250,000 (direct + converted)
• Active Currencies: USD, GBP, SGD, AUD
• Exchange Rate Impact: +$450,000 favorable

📊 Performance Metrics:
• Average Contract Size: $2.75M USD
• Global Market Penetration: 3 continents
• Multi-currency Efficiency: 98.5%"""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'international_financial_{self.model}',
            'tenant_id': self.company_id
        }
    
    def _create_global_response(self, question: str) -> Dict[str, Any]:
        """Create global operations response"""
        
        answer = f"""🌎 Global Operations Overview - {self.company_name}

Query: {question}

🌍 International Project Portfolio:

1. Cross-border Payment System - PayGlobal Ltd 🇦🇺
   • Budget: $1,800,000 USD (AUD converted)
   • Region: Asia-Pacific | Status: Completed
   • Achievement: 99.9% uptime across 4 countries

2. Global Compliance Platform - Tech Solutions Europe 🇩🇪
   • Budget: $3,850,000 USD (EUR converted)
   • Region: Europe | Status: In Development
   • Compliance: GDPR, SOX, Basel III frameworks

3. International Education Hub - Education Global Network 🇬🇧
   • Budget: $2,250,000 USD (GBP converted)
   • Region: Europe | Status: Active
   • Languages: 12 supported, 50+ countries

🌐 Global Infrastructure:
• Time Zone Coverage: 24/7 operations (EST, GMT, SGT)
• Data Centers: 5 regions for compliance
• Team Distribution: 8 international developers
• Cultural Localization: 15+ markets

🏆 International Achievements:
• Cross-border transactions: $50M+ processed
• Global certifications: ISO 27001, SOC 2
• Multi-currency support: 8 major currencies"""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'international_global_{self.model}',
            'tenant_id': self.company_id
        }
    
    def _create_client_response(self, question: str) -> Dict[str, Any]:
        """Create client management response"""
        
        answer = f"""🏢 Global Client Portfolio - {self.company_name}

Query: {question}

🌍 Tier 1 International Clients:

1. MegaCorp International 🇺🇸 (North America)
   • Industry: Technology & E-commerce
   • Contract Value: $2,800,000 USD
   • Project: Global E-commerce Platform
   • Relationship: 18+ months | Satisfaction: 97%

2. Global Finance Corp 🌏 (Asia-Pacific)
   • Industry: Financial Services
   • Contract Value: $3,200,000 USD
   • Project: International Banking API
   • Relationship: 12+ months | Satisfaction: 99%

3. Education Global Network 🇪🇺 (Europe)
   • Industry: Education Technology
   • Contract Value: $2,250,000 USD
   • Project: Multi-language Learning Platform
   • Relationship: 24+ months | Satisfaction: 95%

4. PayGlobal Ltd 🇦🇺 (Asia-Pacific)
   • Industry: Fintech
   • Contract Value: $1,800,000 USD
   • Project: Cross-border Payment System (Completed)
   • Relationship: 30+ months | Success Story

📈 Client Success Metrics:
• Global Client Retention: 95%
• Cross-cultural Communication Score: 98%
• Multi-timezone Support: 24/7 available
• International Compliance: 100% certified

🎯 Expansion Opportunities:
• Latin America: Market research ongoing
• Middle East: Partnership discussions
• Africa: Technology assessment phase"""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'international_clients_{self.model}',
            'tenant_id': self.company_id
        }
    
    def _create_general_response(self, question: str) -> Dict[str, Any]:
        """Create general international response"""
        
        answer = f"""🌍 {self.company_name} - Global Software Solutions

Question: {question}

Our International Capabilities:
• Cross-border software development
• Multi-currency system architecture
• Global compliance and security
• International team collaboration

🌎 Geographic Presence:
• Development Teams: Bangkok (HQ), Remote Global
• Client Base: USA, UK, Singapore, Australia, Germany
• Market Focus: Enterprise, Fintech, Education

💡 Ask me about:
• International project portfolios
• Multi-currency revenue analysis  
• Global client relationships
• Cross-border technology solutions
• International compliance frameworks

We specialize in building software that works seamlessly across borders, currencies, and cultures."""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'international_general_{self.model}',
            'tenant_id': self.company_id
        }