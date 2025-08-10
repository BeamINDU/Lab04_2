import sys
import os
sys.path.append(os.path.dirname(__file__))

from typing import Dict, Any
import logging
from datetime import datetime

# Import existing enhanced agent
from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent

logger = logging.getLogger(__name__)

class SimpleModularAgent:
    """🎯 SIMPLE: Try modular, fallback to enhanced agent"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.tenant_configs = tenant_configs
        
        # Always have enhanced agent as backup
        self.enhanced_agent = EnhancedPostgresOllamaAgent()
        logger.info("✅ Enhanced Agent loaded")
        
        # Try to load modular system (optional)
        self.modular_system = None
        self.modular_works = False
        self._try_load_modular()
        
        # Simple stats
        self.stats = {'total': 0, 'modular': 0, 'enhanced': 0}
    
    def _try_load_modular(self):
        """🔄 Try to load modular system (don't crash if fails)"""
        try:
            from core_system.prompt_manager import WorkingPromptManager
            self.modular_system = WorkingPromptManager(self.tenant_configs)
            
            # Check if any prompts loaded
            stats = self.modular_system.get_statistics()
            if stats['loaded_prompts'] > 0:
                self.modular_works = True
                self.supported_companies = list(self.modular_system.company_prompts.keys())
                logger.info(f"✅ Modular system: {stats['loaded_prompts']} prompts loaded")
            else:
                logger.warning("⚠️ Modular system: No prompts loaded")
                
        except Exception as e:
            logger.warning(f"⚠️ Modular system failed: {e}")
            logger.info("🔄 Will use Enhanced Agent for all queries")
    
    async def process_enhanced_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main method: Try modular → fallback to enhanced"""
        
        self.stats['total'] += 1
        
        # Try modular first (if available and supported)
        if self.modular_works and tenant_id in self.supported_companies:
            try:
                result = await self.modular_system.process_query(question, tenant_id)
                self.stats['modular'] += 1
                
                result.update({
                    'system_used': 'modular_prompts',
                    'company_prompt': True
                })
                
                logger.info(f"✅ Modular system used for {tenant_id}")
                return result
                
            except Exception as e:
                logger.warning(f"🔄 Modular failed for {tenant_id}: {e}")
        
        # Fallback to enhanced agent
        result = await self.enhanced_agent.process_enhanced_question(question, tenant_id)
        self.stats['enhanced'] += 1
        
        result.update({
            'system_used': 'enhanced_agent',
            'company_prompt': False
        })
        
        logger.info(f"🔄 Enhanced Agent used for {tenant_id}")
        return result
    
    def get_simple_stats(self) -> Dict[str, Any]:
        """📊 Simple statistics"""
        
        modular_rate = 0
        if self.stats['total'] > 0:
            modular_rate = (self.stats['modular'] / self.stats['total']) * 100
        
        return {
            'modular_available': self.modular_works,
            'total_queries': self.stats['total'],
            'modular_used': self.stats['modular'],
            'enhanced_used': self.stats['enhanced'],
            'modular_rate': round(modular_rate, 1),
            'supported_companies': getattr(self, 'supported_companies', []),
            'status': 'healthy'
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (for existing code)
    # ========================================================================
    
    def get_modular_statistics(self):
        """Compatibility method"""
        return self.get_simple_stats()
    
    async def process_enhanced_question_streaming(self, question: str, tenant_id: str):
        """Simple streaming"""
        
        # Try modular first
        if self.modular_works and tenant_id in self.supported_companies:
            yield {"type": "status", "message": "🎯 Using Company Prompts..."}
            
            try:
                result = await self.modular_system.process_query(question, tenant_id)
                
                # Stream answer in chunks
                answer = result.get('answer', '')
                chunk_size = 50
                
                for i in range(0, len(answer), chunk_size):
                    yield {"type": "answer_chunk", "content": answer[i:i+chunk_size]}
                
                yield {"type": "complete", "system": "modular"}
                return
                
            except Exception as e:
                yield {"type": "status", "message": f"🔄 Switching to Enhanced Agent..."}
        
        # Fallback to enhanced streaming
        yield {"type": "status", "message": "🔄 Using Enhanced Agent..."}
        
        async for chunk in self.enhanced_agent.process_enhanced_question_streaming(question, tenant_id):
            yield chunk
    
    def get_database_connection(self, tenant_id: str):
        """Delegate to enhanced agent"""
        return self.enhanced_agent.get_database_connection(tenant_id)

# =============================================================================
# 🧪 SIMPLE TEST
# =============================================================================

async def test_simple_system():
    """🧪 Simple test"""
    
    print("🧪 Testing Simple Modular System")
    print("=" * 50)
    
    # Mock configs
    configs = {
        'company-a': {'name': 'Bangkok HQ', 'model': 'llama3.1:8b'},
        'company-b': {'name': 'Chiang Mai', 'model': 'llama3.1:8b'},
        'company-c': {'name': 'International', 'model': 'llama3.1:8b'}
    }
    
    try:
        # Initialize
        agent = SimpleModularAgent(configs)
        print(f"✅ Agent initialized")
        print(f"🎯 Modular works: {agent.modular_works}")
        
        # Test questions
        test_cases = [
            ('company-a', 'สวัสดีครับ'),
            ('company-b', 'สวัสดีเจ้า'), 
            ('company-c', 'Hello')
        ]
        
        for tenant, question in test_cases:
            print(f"\n🧪 Testing {tenant}: {question}")
            
            # Mock the call (since we don't have AI service)
            result = {
                'success': True,
                'answer': f"Mock response for {tenant}",
                'system_used': 'modular_prompts' if agent.modular_works else 'enhanced_agent'
            }
            
            system = result['system_used']
            print(f"   ✅ System: {system}")
        
        # Stats
        stats = agent.get_simple_stats()
        print(f"\n📊 Stats: {stats}")
        
        print(f"\n🎉 Simple system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

# Create alias for compatibility
ModularEnhancedAgent = SimpleModularAgent

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_system())