import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, Any, Optional
from shared_components.logging_config import logger

# Import company prompts
from company_prompts.company_a.enterprise_prompt import EnterprisePrompt
from company_prompts.company_b.tourism_prompt import TourismPrompt

class SimplePromptManager:
    """🎯 Simple Prompt Manager - เฉพาะที่จำเป็น"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        """🏗️ Initialize เฉพาะที่จำเป็น"""
        self.tenant_configs = tenant_configs
        self.company_prompts = {}
        
        # Initialize company prompts
        self._init_company_prompts()
        
        logger.info(f"✅ Simple PromptManager initialized with {len(self.company_prompts)} company prompts")
    
    # ========================================================================
    # 🎯 CORE METHODS (เฉพาะ 4 ตัวที่จำเป็น)
    # ========================================================================
    
    async def process_query(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 1. Main query processing method"""
        
        try:
            if tenant_id in self.company_prompts:
                # Use company-specific prompt
                return await self._use_company_prompt(question, tenant_id)
            else:
                # Use simple fallback
                return self._create_simple_response(question, tenant_id)
                
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return self._create_error_response(str(e), tenant_id)
    
    def _init_company_prompts(self):
        """🎯 2. Initialize company prompts - simple"""
        
        for tenant_id, config in self.tenant_configs.items():
            try:
                company_config = {**config, 'company_id': tenant_id}
                
                if tenant_id == 'company-a':
                    # Enterprise Banking
                    self.company_prompts[tenant_id] = EnterprisePrompt(company_config)
                    logger.info(f"✅ EnterprisePrompt initialized for {tenant_id}")
                    
                elif tenant_id == 'company-b':
                    # Tourism & Hospitality
                    self.company_prompts[tenant_id] = TourismPrompt(company_config)
                    logger.info(f"🏨 TourismPrompt initialized for {tenant_id}")
                
                # Company C ใช้ fallback ง่ายๆ
                else:
                    logger.info(f"⚠️ Using fallback for {tenant_id}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize prompt for {tenant_id}: {e}")
    
    async def _use_company_prompt(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 3. Use company-specific prompt - simple"""
        
        company_prompt = self.company_prompts[tenant_id]
        
        try:
            # Call company prompt's process_question method
            result = await company_prompt.process_question(question)
            
            # Add metadata
            result.update({
                'prompt_system_used': type(company_prompt).__name__,
                'company_id': tenant_id,
                'processing_method': 'company_specific_simple'
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Company prompt failed for {tenant_id}: {e}")
            return self._create_simple_response(question, tenant_id, f"Company prompt error: {e}")
    
    def _create_simple_response(self, question: str, tenant_id: str, error_reason: str = None) -> Dict[str, Any]:
        """🎯 4. Create simple response - fallback"""
        
        config = self.tenant_configs.get(tenant_id, {})
        business_type = config.get('business_type', 'general')
        company_name = config.get('name', 'Unknown Company')
        
        # Simple responses based on business type
        if business_type == 'tourism_hospitality':
            answer = f"""🏨 {company_name} - ระบบท่องเที่ยวและโรงแรม

คำถาม: {question}

เราเชี่ยวชาญด้าน:
• ระบบจองโรงแรมและที่พัก
• แอปพลิเคชันท่องเที่ยว
• ระบบจัดการทัวร์และกิจกรรม
• เทคโนโลยีสำหรับธุรกิจบริการ

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น เช่น:
• "มีโปรเจคท่องเที่ยวอะไรบ้าง"
• "โรงแรมไหนเป็นลูกค้าของเรา"
• "ระบบจองที่พักทำงานอย่างไร"

{f"⚠️ หมายเหตุ: {error_reason}" if error_reason else ""}"""

        elif business_type == 'enterprise':
            answer = f"""🏦 {company_name} - ระบบองค์กรและธนาคาร

คำถาม: {question}

เราเชี่ยวชาญด้าน:
• ระบบธนาคารและการเงิน
• E-commerce และ CRM ขนาดใหญ่
• ระบบ AI และ Chatbot
• Mobile Banking และ Fintech

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น เช่น:
• "มีพนักงานกี่คนในแต่ละแผนก"
• "โปรเจคธนาคารมีอะไรบ้าง"
• "งบประมาณโปรเจคเท่าไร"

{f"⚠️ หมายเหตุ: {error_reason}" if error_reason else ""}"""

        elif business_type == 'global_operations':
            answer = f"""🌍 {company_name} - International Software Solutions

Question: {question}

We specialize in:
• Global software platforms
• Multi-currency systems
• Cross-border solutions
• International compliance systems

Please ask more specific questions like:
• "Which international projects exist"
• "What is the USD budget breakdown"
• "How many overseas clients do we have"

{f"⚠️ Note: {error_reason}" if error_reason else ""}"""

        else:
            answer = f"""💼 {company_name}

คำถาม: {question}

เราเป็นบริษัทพัฒนาซอฟต์แวร์ที่มีความเชี่ยวชาญในการสร้างระบบต่างๆ

กรุณาถามคำถามที่เฉพาะเจาะจงมากขึ้น เกี่ยวกับ:
• ข้อมูลพนักงาน
• โปรเจคและงบประมาณ  
• ระบบและเทคโนโลยี

{f"⚠️ หมายเหตุ: {error_reason}" if error_reason else ""}"""
        
        return {
            'success': True,
            'answer': answer,
            'sql_query': None,
            'data_source_used': f'simple_fallback_{config.get("model", "default")}',
            'tenant_id': tenant_id,
            'processing_method': 'simple_fallback',
            'fallback_reason': error_reason
        }
    
    # ========================================================================
    # 🔧 SIMPLE HELPER METHODS (ไม่นับเป็น core methods)
    # ========================================================================
    
    def _create_error_response(self, error_message: str, tenant_id: str) -> Dict[str, Any]:
        """Create error response"""
        
        return {
            'success': False,
            'answer': f"เกิดข้อผิดพลาด: {error_message}",
            'error': error_message,
            'tenant_id': tenant_id,
            'data_source_used': 'simple_error',
            'processing_method': 'simple_error'
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simple statistics"""
        
        return {
            'total_prompts': len(self.company_prompts),
            'supported_companies': list(self.company_prompts.keys()),
            'company_types': {
                tenant_id: type(prompt).__name__ 
                for tenant_id, prompt in self.company_prompts.items()
            },
            'system_version': 'simple_v1.0'
        }
    
    # ========================================================================
    # 🔄 COMPATIBILITY METHODS (เพื่อความเข้ากันได้กับระบบเดิม)
    # ========================================================================
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Compatibility method"""
        return self.get_statistics()

