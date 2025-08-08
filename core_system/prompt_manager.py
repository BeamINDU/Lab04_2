import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, Any, Optional , List
from shared_components.logging_config import logger

# Import existing components
try:
    from refactored_modules.database_handler import DatabaseHandler
    from refactored_modules.ai_service import AIService
    from refactored_modules.schema_discovery import SchemaDiscoveryService
    from refactored_modules.tenant_config import TenantConfigManager
    EXISTING_COMPONENTS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Existing components not found, using minimal implementation")
    EXISTING_COMPONENTS_AVAILABLE = False

# Import company prompts
from company_prompts.company_a.enterprise_prompt import EnterprisePrompt
from company_prompts.company_b.tourism_prompt import TourismPrompt  # 🆕 Added

class PromptManager:
    """🎯 Enhanced Prompt Manager with Tourism Support"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.tenant_configs = tenant_configs
        
        # ใช้ existing services if available
        if EXISTING_COMPONENTS_AVAILABLE:
            try:
                self.database_handler = DatabaseHandler(tenant_configs)
                self.ai_service = AIService()
                self.schema_service = SchemaDiscoveryService()
                logger.info("✅ Using existing refactored components")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load existing components: {e}")
                self.database_handler = None
                self.ai_service = None
                self.schema_service = None
        else:
            self.database_handler = None
            self.ai_service = None
            self.schema_service = None
        
        # Initialize company prompts
        self.company_prompts = {}
        self._initialize_company_prompts()
        
        logger.info(f"✅ Enhanced PromptManager initialized with {len(self.company_prompts)} company prompts")
    
    def _initialize_company_prompts(self):
        """Initialize company prompts with Tourism support"""
        
        for tenant_id, config in self.tenant_configs.items():
            try:
                company_config = {**config, 'company_id': tenant_id}
                
                if tenant_id == 'company-a':
                    # Enterprise Banking
                    self.company_prompts[tenant_id] = EnterprisePrompt(company_config)
                    logger.info(f"✅ EnterprisePrompt initialized for {tenant_id}")
                    pass
                elif tenant_id == 'company-b':
                    # 🆕 Tourism & Hospitality
                    self.company_prompts[tenant_id] = TourismPrompt(company_config)
                    logger.info(f"🏨 TourismPrompt initialized for {tenant_id}")
                    
                else:
                    # Company C - ยังไม่ implement
                    logger.info(f"⚠️ Using fallback for {tenant_id} (not implemented yet)")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize prompt for {tenant_id}: {e}")
    
    async def process_query(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Enhanced query processing with Tourism support"""
        
        try:
            if tenant_id in self.company_prompts:
                # ใช้ company-specific prompt (A หรือ B)
                return await self._process_with_company_prompt(question, tenant_id)
            else:
                # Fallback สำหรับ Company C
                return await self._process_with_existing_system(question, tenant_id)
                
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return {
                'success': False,
                'answer': f"เกิดข้อผิดพลาด: {str(e)}",
                'error': str(e),
                'tenant_id': tenant_id
            }
    
    async def _process_with_company_prompt(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """ใช้ company-specific prompt (Enterprise หรือ Tourism)"""
        
        prompt_instance = self.company_prompts[tenant_id]
        
        try:
            # 1. Get schema info
            if self.schema_service:
                schema_info = self.schema_service.get_schema_info(tenant_id)
            else:
                schema_info = self._get_fallback_schema_info(tenant_id)
            
            # 2. Generate company-specific prompt
            sql_prompt = prompt_instance.generate_sql_prompt(question, schema_info)
            
            # 3. Call AI service
            if self.ai_service and EXISTING_COMPONENTS_AVAILABLE:
                config = self._create_tenant_config_object(tenant_id)
                ai_response = await self.ai_service.call_ollama_api(
                    tenant_config=config,
                    prompt=sql_prompt,
                    context_data="",
                    temperature=0.1
                )
            else:
                # Simple fallback SQL based on company type
                ai_response = self._generate_fallback_sql(question, tenant_id)
            
            # 4. Extract SQL and execute
            sql_query = self._extract_sql_from_response(ai_response)
            
            if self.database_handler:
                results = self.database_handler.execute_sql_query(tenant_id, sql_query)
            else:
                # Mock results based on company
                results = self._generate_mock_results(tenant_id, question)
            
            # 5. Format company-specific response
            formatted_response = prompt_instance.format_response(question, results, {
                'sql_query': sql_query,
                'results_count': len(results)
            })
            
            return {
                'success': True,
                'answer': formatted_response,
                'sql_query': sql_query,
                'results_count': len(results),
                'tenant_id': tenant_id,
                'prompt_type': prompt_instance.__class__.__name__,
                'system_version': 'modular_with_tourism_support_v2.0'
            }
            
        except Exception as e:
            logger.error(f"❌ Company prompt processing failed: {e}")
            raise e
    
    def _get_fallback_schema_info(self, tenant_id: str) -> Dict[str, Any]:
        """Get fallback schema info based on company type"""
        
        if tenant_id == 'company-a':
            return {
                'description': 'Enterprise Banking Database',
                'focus': 'Banking systems, large projects, enterprise clients'
            }
        elif tenant_id == 'company-b':
            return {
                'description': 'Tourism & Hospitality Database',
                'focus': 'Tourism projects, hotels, regional clients, cultural sites'
            }
        else:
            return {
                'description': 'General Business Database',
                'focus': 'Standard business operations'
            }
    
    def _generate_fallback_sql(self, question: str, tenant_id: str) -> str:
        """Generate fallback SQL based on company and question"""
        
        question_lower = question.lower()
        
        if tenant_id == 'company-b':
            # Tourism-specific fallback SQL
            if any(word in question_lower for word in ['ท่องเที่ยว', 'tourism', 'โรงแรม', 'hotel']):
                return """SELECT name as project_name, client, budget, status 
                         FROM projects 
                         WHERE client ILIKE '%ท่องเที่ยว%' OR client ILIKE '%โรงแรม%' 
                         ORDER BY budget DESC LIMIT 10;"""
            elif any(word in question_lower for word in ['ร้านอาหาร', 'restaurant', 'อาหาร']):
                return """SELECT name as project_name, client, budget 
                         FROM projects 
                         WHERE client ILIKE '%ร้านอาหาร%' OR client ILIKE '%อาหาร%' 
                         ORDER BY start_date DESC LIMIT 10;"""
            else:
                return """SELECT name, position, department FROM employees 
                         WHERE department = 'IT' 
                         ORDER BY hire_date DESC LIMIT 10;"""
        
        elif tenant_id == 'company-a':
            # Enterprise-specific fallback SQL
            if any(word in question_lower for word in ['ธนาคาร', 'bank', 'enterprise']):
                return """SELECT name as project_name, client, budget 
                         FROM projects 
                         WHERE client ILIKE '%ธนาคาร%' OR budget > 2000000 
                         ORDER BY budget DESC LIMIT 10;"""
        
        # General fallback
        return "SELECT name, position, department FROM employees LIMIT 10;"
    
    def _generate_mock_results(self, tenant_id: str, question: str) -> List[Dict[str, Any]]:
        """Generate mock results for testing"""
        
        if tenant_id == 'company-b':
            # Tourism mock data
            return [
                {'project_name': 'ระบบจัดการโรงแรม', 'client': 'โรงแรมดุสิต เชียงใหม่', 'budget': 800000, 'status': 'active'},
                {'project_name': 'เว็บไซต์ท่องเที่ยว', 'client': 'การท่องเที่ยวแห่งประเทศไทย', 'budget': 600000, 'status': 'active'},
                {'project_name': 'Mobile App สวนสวยงาม', 'client': 'สวนพฤกษศาสตร์เชียงใหม่', 'budget': 450000, 'status': 'completed'}
            ]
        elif tenant_id == 'company-a':
            # Enterprise mock data
            return [
                {'project_name': 'ระบบ CRM สำหรับธนาคาร', 'client': 'ธนาคารกรุงเทพ', 'budget': 3000000, 'status': 'active'},
                {'project_name': 'AI Chatbot E-commerce', 'client': 'Central Group', 'budget': 1200000, 'status': 'active'}
            ]
        
        return [{'message': 'No mock data available'}]
    
    def _create_tenant_config_object(self, tenant_id: str):
        """Create tenant config object for AI service"""
        
        # Mock tenant config for AI service
        class MockTenantConfig:
            def __init__(self, tenant_id, config):
                self.tenant_id = tenant_id
                self.model_name = config.get('model', 'llama3.1:8b')
                self.language = config.get('language', 'th')
                self.name = config.get('name', f'Company {tenant_id.upper()}')
        
        return MockTenantConfig(tenant_id, self.tenant_configs[tenant_id])
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all company prompts"""
        
        stats = {
            'total_companies': len(self.company_prompts),
            'active_prompts': list(self.company_prompts.keys()),
            'company_statistics': {}
        }
        
        for tenant_id, prompt_instance in self.company_prompts.items():
            stats['company_statistics'][tenant_id] = prompt_instance.get_statistics()
        
        return stats