import sys
import os
sys.path.append(os.path.dirname(__file__))

from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Import existing enhanced agent
from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent

# Import new modular components
from core_system.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ModularEnhancedAgent:
    """🔥 Bridge ระหว่าง existing system และ modular prompts"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.tenant_configs = tenant_configs
        
        # Original enhanced agent (fallback)
        self.original_agent = EnhancedPostgresOllamaAgent()
        
        # New modular prompt manager
        try:
            self.prompt_manager = PromptManager(tenant_configs)
            self.modular_available = True
            logger.info("✅ Modular prompt system loaded")
        except Exception as e:
            logger.warning(f"⚠️ Modular prompts failed: {e}")
            self.prompt_manager = None
            self.modular_available = False
        
        # Statistics
        self.usage_stats = {
            'total_queries': 0,
            'modular_queries': 0,
            'fallback_queries': 0
        }
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main processing method - ใช้ modular หรือ fallback"""
        
        start_time = datetime.now()
        self.usage_stats['total_queries'] += 1
        
        try:
            # ลองใช้ modular prompt ก่อน (สำหรับ company-a)
            if self.modular_available and tenant_id == 'company-a':
                try:
                    result = await self.prompt_manager.process_query(question, tenant_id)
                    self.usage_stats['modular_queries'] += 1
                    
                    # เพิ่ม metadata
                    result.update({
                        'system_type': 'modular_prompts',
                        'architecture': 'company_specific_prompts',
                        'modular_system_used': True
                    })
                    
                    logger.info(f"✅ Modular system used for {tenant_id}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"🔄 Modular failed for {tenant_id}: {e}, using fallback")
            
            # Fallback ไปใช้ original system
            result = await self.original_agent.process_enhanced_question(question, tenant_id)
            self.usage_stats['fallback_queries'] += 1
            
            # เพิ่ม metadata
            result.update({
                'system_type': 'original_enhanced_agent',
                'architecture': 'universal_prompt_system',
                'modular_system_used': False,
                'fallback_reason': 'modular_not_available' if not self.modular_available else 'company_not_supported'
            })
            
            logger.info(f"🔄 Original system used for {tenant_id}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Both systems failed for {tenant_id}: {e}")
            
            return {
                'success': False,
                'answer': f"เกิดข้อผิดพลาด: {str(e)}",
                'error': str(e),
                'processing_time': processing_time,
                'tenant_id': tenant_id,
                'system_type': 'error_handler'
            }
    
    # เพิ่ม methods อื่นๆ ที่ original agent มี
    def get_database_connection(self, tenant_id: str):
        """Delegate to original agent"""
        return self.original_agent.get_database_connection(tenant_id)
    
    async def generate_enhanced_sql(self, question: str, tenant_id: str):
        """Delegate to original agent"""
        return await self.original_agent.generate_enhanced_sql(question, tenant_id)
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Delegate to original agent for streaming"""
        async for chunk in self.original_agent.process_enhanced_question_streaming(question, tenant_id):
            yield chunk
    
    def get_modular_statistics(self) -> Dict[str, Any]:
        """📊 ดึงสถิติการใช้งาน modular system"""
        
        modular_rate = 0
        if self.usage_stats['total_queries'] > 0:
            modular_rate = (self.usage_stats['modular_queries'] / 
                          self.usage_stats['total_queries']) * 100
        
        return {
            'modular_system_available': self.modular_available,
            'total_queries': self.usage_stats['total_queries'],
            'modular_queries': self.usage_stats['modular_queries'],
            'fallback_queries': self.usage_stats['fallback_queries'],
            'modular_usage_rate': round(modular_rate, 2),
            'companies_supported': ['company-a'] if self.modular_available else [],
            'fallback_companies': ['company-b', 'company-c']
        }