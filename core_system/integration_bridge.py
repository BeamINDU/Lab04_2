import sys
import os
sys.path.append(os.path.dirname(__file__))

from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Import existing enhanced agent
from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent

# Import enhanced modular components
from core_system.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ModularEnhancedAgent:
    """🔥 Fixed Bridge with Tourism Support (Company A + B)"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.tenant_configs = tenant_configs
        
        # Original enhanced agent (fallback)
        self.original_agent = EnhancedPostgresOllamaAgent()
        
        # Enhanced modular prompt manager
        try:
            self.prompt_manager = PromptManager(tenant_configs)
            self.modular_available = True
            # 🔥 FIXED: Add supported_companies attribute
            self.supported_companies = ['company-a', 'company-b']
            logger.info("✅ Enhanced modular prompt system loaded (Enterprise + Tourism)")
        except Exception as e:
            logger.warning(f"⚠️ Modular prompts failed: {e}")
            self.prompt_manager = None
            self.modular_available = False
            self.supported_companies = []
        
        # Enhanced statistics
        self.usage_stats = {
            'total_queries': 0,
            'modular_queries': 0,
            'fallback_queries': 0,
            'company_breakdown': {
                'company-a': {'modular': 0, 'fallback': 0},
                'company-b': {'modular': 0, 'fallback': 0},
                'company-c': {'modular': 0, 'fallback': 0}
            }
        }
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Enhanced processing with Tourism support"""
        
        start_time = datetime.now()
        self.usage_stats['total_queries'] += 1
        
        try:
            # 🆕 ใช้ modular prompt สำหรับ Company A และ B
            if self.modular_available and tenant_id in self.supported_companies:
                try:
                    result = await self.prompt_manager.process_query(question, tenant_id)
                    self.usage_stats['modular_queries'] += 1
                    self.usage_stats['company_breakdown'][tenant_id]['modular'] += 1
                    
                    # เพิ่ม enhanced metadata
                    result.update({
                        'system_type': 'modular_prompts',
                        'architecture': f'{tenant_id}_specific_prompts',
                        'modular_system_used': True,
                        'company_specialization': self._get_company_specialization(tenant_id)
                    })
                    
                    logger.info(f"✅ Enhanced modular system used for {tenant_id}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"🔄 Modular failed for {tenant_id}: {e}, using fallback")
            
            # Fallback ไปใช้ original system
            result = await self.original_agent.process_enhanced_question(question, tenant_id)
            self.usage_stats['fallback_queries'] += 1
            self.usage_stats['company_breakdown'][tenant_id]['fallback'] += 1
            
            # เพิ่ม enhanced metadata
            result.update({
                'system_type': 'original_enhanced_agent',
                'architecture': 'universal_prompt_system',
                'modular_system_used': False,
                'fallback_reason': self._get_fallback_reason(tenant_id)
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
    
    def _get_company_specialization(self, tenant_id: str) -> str:
        """Get company specialization description"""
        
        specializations = {
            'company-a': 'Enterprise Banking & Large-scale Systems',
            'company-b': 'Tourism & Hospitality Technology (Northern Thailand)',
            'company-c': 'International Operations & Cross-border Solutions'
        }
        
        return specializations.get(tenant_id, 'General Business Solutions')
    
    def _get_fallback_reason(self, tenant_id: str) -> str:
        """Get reason for fallback usage"""
        
        if not self.modular_available:
            return 'modular_system_not_available'
        elif tenant_id not in self.supported_companies:
            return f'{tenant_id}_not_supported_yet'
        else:
            return 'modular_system_error'
    
    def get_modular_statistics(self) -> Dict[str, Any]:
        """📊 Enhanced statistics with Tourism support"""
        
        modular_rate = 0
        if self.usage_stats['total_queries'] > 0:
            modular_rate = (self.usage_stats['modular_queries'] / 
                          self.usage_stats['total_queries']) * 100
        
        # Get prompt manager stats if available
        prompt_stats = {}
        if self.prompt_manager:
            try:
                prompt_stats = self.prompt_manager.get_all_statistics()
            except:
                pass
        
        return {
            'modular_system_available': self.modular_available,
            'total_queries': self.usage_stats['total_queries'],
            'modular_queries': self.usage_stats['modular_queries'],
            'fallback_queries': self.usage_stats['fallback_queries'],
            'modular_usage_rate': round(modular_rate, 2),
            'supported_companies': self.supported_companies,  # 🆕 Now includes A & B
            'fallback_companies': ['company-c'],  # 🆕 Only C uses fallback
            'company_breakdown': self.usage_stats['company_breakdown'],
            'prompt_system_stats': prompt_stats,
            'enhanced_features': [
                'enterprise_banking_prompts',      # Company A
                'tourism_hospitality_prompts',     # Company B (🆕)
                'regional_cultural_awareness',     # Company B (🆕)
                'multi_domain_expertise',          # Both A & B
                'gradual_migration_support'
            ]
        }
    
    # 🔥 FIXED: Add missing methods that original agent has
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Delegate streaming to original agent"""
        async for chunk in self.original_agent.process_enhanced_question_streaming(question, tenant_id):
            yield chunk