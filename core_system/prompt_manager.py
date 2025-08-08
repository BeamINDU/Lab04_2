import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, Any, Optional
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

class PromptManager:
    """🎯 Manages company prompts - ใช้ existing components"""
    
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
        
        logger.info(f"✅ PromptManager initialized")
    
    def _initialize_company_prompts(self):
        """Initialize company prompts"""
        
        for tenant_id, config in self.tenant_configs.items():
            try:
                if tenant_id == 'company-a':
                    # สำหรับตอนนี้ทำแค่ company-a ก่อน
                    company_config = {**config, 'company_id': tenant_id}
                    self.company_prompts[tenant_id] = EnterprisePrompt(company_config)
                    logger.info(f"✅ EnterprisePrompt initialized for {tenant_id}")
                else:
                    # ใช้ fallback (existing prompt generator)
                    logger.info(f"⚠️ Using fallback for {tenant_id} (not implemented yet)")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize prompt for {tenant_id}: {e}")
    
    async def process_query(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Process query ด้วย company-specific prompt"""
        
        try:
            if tenant_id in self.company_prompts:
                # ใช้ company-specific prompt
                return await self._process_with_company_prompt(question, tenant_id)
            else:
                # Fallback ไปใช้ existing system
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
        """ใช้ company-specific prompt"""
        
        prompt_instance = self.company_prompts[tenant_id]
        
        try:
            # 1. Get schema info (ใช้ existing service หรือ fallback)
            if self.schema_service:
                schema_info = self.schema_service.get_enhanced_schema_info(tenant_id)
            else:
                schema_info = {}
            
            # 2. Generate company-specific prompt
            sql_prompt = prompt_instance.generate_sql_prompt(question, schema_info)
            
            # 3. Call AI (ใช้ existing AI service หรือ simple fallback)
            if self.ai_service and EXISTING_COMPONENTS_AVAILABLE:
                config = self.tenant_configs[tenant_id]
                ai_response = await self.ai_service.call_ollama_api(
                    tenant_config=config,
                    prompt=sql_prompt,
                    context_data="",
                    temperature=0.1
                )
            else:
                # Simple fallback SQL
                ai_response = "SELECT name, position, department FROM employees WHERE department = 'IT' LIMIT 10;"
            
            # 4. Extract SQL and execute (ใช้ existing database handler หรือ mock)
            sql_query = self._extract_sql_from_response(ai_response)
            
            if self.database_handler:
                results = self.database_handler.execute_sql_query(tenant_id, sql_query)
            else:
                # Mock results for testing
                results = [
                    {'name': 'สมชาย ใจดี', 'position': 'Senior Developer', 'department': 'IT'},
                    {'name': 'สมหญิง รักงาน', 'position': 'Frontend Developer', 'department': 'IT'}
                ]
            
            # 5. Format response (ใช้ company-specific formatter)
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
                'system_version': 'modular_with_existing_components'
            }
            
        except Exception as e:
            logger.error(f"❌ Company prompt processing failed: {e}")
            raise e
    
    async def _process_with_existing_system(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Fallback ไปใช้ existing enhanced agent"""
        
        # Import existing agent
        try:
            from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent
            
            existing_agent = EnhancedPostgresOllamaAgent()
            result = await existing_agent.process_enhanced_question(question, tenant_id)
            
            # เพิ่ม flag ว่าใช้ fallback
            result.update({
                'fallback_mode': True,
                'prompt_type': 'existing_system',
                'system_version': 'fallback_to_existing'
            })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Existing system also failed: {e}")
            return {
                'success': False,
                'answer': f"ระบบทั้งหมดมีปัญหา: {str(e)}",
                'error': str(e),
                'tenant_id': tenant_id,
                'system_version': 'all_systems_failed'
            }
    
    def _extract_sql_from_response(self, ai_response: str) -> str:
        """Extract SQL from AI response"""
        
        import re
        
        # SQL extraction patterns
        patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;)\s*```',
            r'(SELECT.*?;)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if sql.upper().startswith('SELECT'):
                    return sql
        
        # Fallback
        return "SELECT name, position FROM employees LIMIT 10;"