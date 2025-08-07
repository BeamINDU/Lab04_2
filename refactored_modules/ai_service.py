# ai_service.py
# 🤖 AI/Ollama Communication Service

import os
import json
import asyncio
import aiohttp
from typing import AsyncGenerator
import logging
from .tenant_config import TenantConfig

logger = logging.getLogger(__name__)

class AIService:
    """🤖 Handles all AI/Ollama communications"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434')
    
    async def call_ollama_api(self, tenant_config: TenantConfig, prompt: str, 
                             context_data: str = "", temperature: float = 0.7) -> str:
        """Enhanced Ollama API call with better error handling"""
        
        # Prepare system prompt
        if context_data:
            full_prompt = f"{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        # Prepare request payload with enhanced options
        payload = {
            "model": tenant_config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 800,      # ลดจาก 2000
                "top_k": 20,             # ลดจาก 40
                "top_p": 0.8,           # ลดจาก 0.9
                "repeat_penalty": 1.0,   # ลดจาก 1.1
                "num_ctx": 2048         # จำกัด context
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)  # Increased timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', 'ไม่สามารถรับคำตอบจาก AI ได้')
                    else:
                        logger.error(f"Enhanced Ollama API error: {response.status}")
                        return f"เกิดข้อผิดพลาดในการเรียก AI (HTTP {response.status})"
                        
        except asyncio.TimeoutError:
            logger.error("Enhanced Ollama API timeout")
            return "AI ใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Enhanced Ollama API call failed: {e}")
            return f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"
    
    async def call_ollama_api_streaming(self, tenant_config: TenantConfig, prompt: str, 
                                       context_data: str = "", temperature: float = 0.7) -> AsyncGenerator:
        """🔥 NEW: Streaming version of call_ollama_api"""
        
        # Prepare system prompt
        if context_data:
            full_prompt = f"{prompt}\n\nContext Data:\n{context_data}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        # Prepare request payload with streaming enabled
        payload = {
            "model": tenant_config.model_name,
            "prompt": full_prompt,
            "stream": True,  # 🔥 Enable streaming!
            "options": {
                "temperature": temperature,
                "num_predict": 800,
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.0,
                "num_ctx": 2048
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        # 🔥 Process streaming response
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    if 'response' in data and data['response']:
                                        # Yield each token as it comes
                                        yield data['response']
                                    
                                    # Check if streaming is complete
                                    if data.get('done', False):
                                        break
                                        
                                except json.JSONDecodeError:
                                    # Skip invalid JSON lines
                                    continue
                    else:
                        yield f"เกิดข้อผิดพลาดในการเรียก AI (HTTP {response.status})"
                        
        except asyncio.TimeoutError:
            yield "AI ใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except Exception as e:
            yield f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"