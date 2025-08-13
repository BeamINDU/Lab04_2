import os
import json
import asyncio
import aiohttp
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# MESSAGE FILTER CLASS
# =============================================================================

class OpenWebUIMessageFilter:
    """🎯 Filter สำหรับจัดการ OpenWebUI Title Generation Requests"""
    
    def __init__(self):
        self.title_gen_patterns = [
            r"Generate a concise.*title.*summarizing the chat history",
            r"Your entire response must consist solely of the JSON object",
            r'JSON format:\s*\{\s*"title":\s*".*"\s*\}',
            r"### Task:\s*Generate.*title",
            r"### Guidelines:",
            r"### Output:",
            r"### Examples:",
            r"### Chat History:",
            r"<chat_history>",
            r"</chat_history>",
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                 for pattern in self.title_gen_patterns]
    
    def is_title_generation_request(self, message: str) -> bool:
        if not message or not isinstance(message, str):
            return False
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                return True
        return False
    
    def extract_user_question_from_mixed_request(self, message: str) -> Optional[str]:
        if not self.is_title_generation_request(message):
            return message.strip()
        
        # หาส่วนที่เป็น chat history
        chat_history_match = re.search(r'<chat_history>(.*?)</chat_history>', 
                                      message, re.DOTALL | re.IGNORECASE)
        
        if chat_history_match:
            chat_content = chat_history_match.group(1).strip()
            user_question = self._extract_last_user_question(chat_content)
            if user_question:
                logger.info(f"🎯 Extracted user question: {user_question[:50]}...")
                return user_question
        
        return None
    
    def _extract_last_user_question(self, chat_content: str) -> Optional[str]:
        user_messages = []
        patterns = [
            r'USER:\s*(.+?)(?=ASSISTANT:|$)',
            r'user:\s*(.+?)(?=assistant:|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, chat_content, re.IGNORECASE | re.DOTALL)
            user_messages.extend(matches)
        
        if user_messages:
            last_question = user_messages[-1].strip()
            last_question = re.sub(r'\n+', ' ', last_question)
            last_question = re.sub(r'\s+', ' ', last_question)
            
            if last_question and not self._is_system_text(last_question):
                return last_question
        
        return None
    
    def _is_system_text(self, text: str) -> bool:
        system_indicators = [
            "Generate a concise", "JSON format", "Guidelines:",
            "Examples:", "Your entire response", "### Task", "### Output"
        ]
        
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in system_indicators)
    
    def generate_title_response(self, chat_history: str = "") -> str:
        if "พนักงาน" in chat_history and "แผนก" in chat_history:
            return '{"title": "👥 พนักงานในแผนก IT"}'
        elif "พนักงาน" in chat_history:
            return '{"title": "👥 ข้อมูลพนักงาน"}'
        elif "โปรเจค" in chat_history or "project" in chat_history.lower():
            return '{"title": "📋 ข้อมูลโปรเจค"}'
        return '{"title": "💬 การสนทนาทั่วไป"}'

    def process_message(self, message: str) -> Dict[str, Any]:
        result = {
            "is_title_request": False,
            "user_question": None,
            "title_response": None,
            "should_process_rag": False
        }
        
        if not message or not isinstance(message, str):
            return result
        
        if self.is_title_generation_request(message):
            result["is_title_request"] = True
            result["title_response"] = self.generate_title_response(message)
            
            user_question = self.extract_user_question_from_mixed_request(message)
            if user_question:
                result["user_question"] = user_question
                result["should_process_rag"] = True
        else:
            result["user_question"] = message.strip()
            result["should_process_rag"] = True
        
        return result

# =============================================================================
# STREAMING RESPONSE FIXER 
# =============================================================================

class OpenWebUIStreamingFixer:
    """🔧 แก้ไขปัญหา OpenWebUI Streaming Display"""
    
    @staticmethod
    def create_openai_chunk(content: str, finish_reason: str = None, is_first: bool = False):
        """🎯 สร้าง OpenAI-compatible chunk"""
        
        chunk_id = f"chatcmpl-{int(datetime.now().timestamp())}"
        
        if is_first:
            return {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": "llama3.1:8b",
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason
                }]
            }
        else:
            return {
                "id": chunk_id,
                "object": "chat.completion.chunk", 
                "created": int(datetime.now().timestamp()),
                "model": "llama3.1:8b",
                "choices": [{
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": finish_reason
                }]
            }
    
    @staticmethod
    def format_sse_data(data: dict) -> str:
        """🎯 Format data as Server-Sent Events"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    @staticmethod
    def get_streaming_headers():
        """📋 Get proper streaming headers"""
        return {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
            "X-Accel-Buffering": "no"
        }

# =============================================================================
# CONFIGURATION
# =============================================================================

class ProxyConfig:
    def __init__(self):
        self.rag_service_url = os.getenv('ENHANCED_RAG_SERVICE', 'http://rag-service:5000')
        self.default_tenant = os.getenv('DEFAULT_TENANT', 'company-a')
        self.force_tenant = os.getenv('FORCE_TENANT')
        self.port = int(os.getenv('PORT', '8001'))
        
        self.use_n8n = os.getenv('USE_N8N_WORKFLOW', 'true').lower() == 'true'
        self.n8n_base_url = os.getenv('N8N_BASE_URL', 'http://n8n:5678')
        
        self.n8n_webhooks = {
            'company-a': f"{self.n8n_base_url}/webhook/company-a-chat",
            'company-b': f"{self.n8n_base_url}/webhook/company-b-chat", 
            'company-c': f"{self.n8n_base_url}/webhook/company-c-chat"
        }
        
        self.tenant_configs = {
            'company-a': {'name': 'SiamTech Bangkok HQ', 'model': 'llama3.1:8b', 'language': 'th'},
            'company-b': {'name': 'SiamTech Chiang Mai Regional', 'model': 'llama3.1:8b', 'language': 'th'},
            'company-c': {'name': 'SiamTech International', 'model': 'llama3.1:8b', 'language': 'en'}
        }

config = ProxyConfig()
message_filter = OpenWebUIMessageFilter()
streaming_fixer = OpenWebUIStreamingFixer()

app = FastAPI(title=f"Fixed OpenWebUI N8N Proxy v4.2", version="4.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# =============================================================================
# MODELS
# =============================================================================

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_tenant_id() -> str:
    if config.force_tenant:
        return config.force_tenant
    return config.default_tenant

def get_tenant_config(tenant_id: str) -> Dict[str, Any]:
    return config.tenant_configs.get(tenant_id, config.tenant_configs[config.default_tenant])

# =============================================================================
# ENHANCED STREAMING GENERATOR
# =============================================================================

async def generate_openai_streaming_fixed(tenant_id: str, user_message: str, tenant_config: dict):
    """🎯 Fixed streaming generator for OpenWebUI"""
    
    try:
        logger.info(f"🎯 Starting FIXED streaming for {tenant_id}")
        
        # 1. 🚨 CRITICAL: Send initial chunk with role
        initial_chunk = streaming_fixer.create_openai_chunk("", is_first=True)
        yield streaming_fixer.format_sse_data(initial_chunk)
        
        # 2. Call N8N or RAG service
        response_received = False
        
        if config.use_n8n and tenant_id in config.n8n_webhooks:
            # N8N Webhook call
            webhook_url = config.n8n_webhooks[tenant_id]
            payload = {
                "message": user_message,
                "tenant_id": tenant_id,
                "timestamp": datetime.now().isoformat(),
                "source": "openwebui_proxy_fixed",
                "use_streaming": False  # Get complete response first
            }
            
            logger.info(f"🌐 Calling N8N webhook: {webhook_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("answer", "ไม่มีคำตอบ")
                        
                        if answer:
                            response_received = True
                            logger.info(f"✅ N8N response received: {len(answer)} characters")
                            
                            # Send answer in chunks for streaming effect
                            words = answer.split()
                            chunk_size = 3  # 3 words per chunk
                            
                            for i in range(0, len(words), chunk_size):
                                word_chunk = " ".join(words[i:i+chunk_size])
                                if i + chunk_size < len(words):
                                    word_chunk += " "
                                
                                content_chunk = streaming_fixer.create_openai_chunk(word_chunk)
                                yield streaming_fixer.format_sse_data(content_chunk)
                                
                                # Natural delay
                                await asyncio.sleep(0.1)
                    
                    else:
                        logger.error(f"❌ N8N webhook failed: {response.status}")
        
        else:
            # Direct RAG service call
            rag_url = f"{config.rag_service_url}/api/query"
            payload = {"question": user_message, "tenant_id": tenant_id, "stream": False}
            
            logger.info(f"🔄 Calling RAG service: {rag_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(rag_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("response", result.get("answer", "ไม่มีคำตอบ"))
                        
                        if answer:
                            response_received = True
                            logger.info(f"✅ RAG response received: {len(answer)} characters")
                            
                            # Send answer in chunks
                            words = answer.split()
                            chunk_size = 3
                            
                            for i in range(0, len(words), chunk_size):
                                word_chunk = " ".join(words[i:i+chunk_size])
                                if i + chunk_size < len(words):
                                    word_chunk += " "
                                
                                content_chunk = streaming_fixer.create_openai_chunk(word_chunk)
                                yield streaming_fixer.format_sse_data(content_chunk)
                                await asyncio.sleep(0.1)
                    else:
                        logger.error(f"❌ RAG service failed: {response.status}")
        
        # 3. Handle no response case
        if not response_received:
            logger.warning(f"⚠️ No response received for {tenant_id}")
            fallback_message = "🤔 ไม่สามารถประมวลผลคำตอบได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"
            fallback_chunk = streaming_fixer.create_openai_chunk(fallback_message)
            yield streaming_fixer.format_sse_data(fallback_chunk)
        
        # 4. 🚨 CRITICAL: Send final chunk
        final_chunk = streaming_fixer.create_openai_chunk("", finish_reason="stop")
        yield streaming_fixer.format_sse_data(final_chunk)
        yield "data: [DONE]\n\n"
        
        logger.info(f"✅ Completed streaming for {tenant_id}")
        
    except Exception as e:
        logger.error(f"🔥 Streaming error for {tenant_id}: {e}")
        
        # Send error message
        error_message = f"❌ เกิดข้อผิดพลาดในระบบ: {str(e)}"
        error_chunk = streaming_fixer.create_openai_chunk(error_message, finish_reason="stop")
        yield streaming_fixer.format_sse_data(error_chunk)
        yield "data: [DONE]\n\n"

# =============================================================================
# MAIN CHAT COMPLETIONS ENDPOINT - FIXED VERSION
# =============================================================================

@app.post("/v1/chat/completions")
async def chat_completions_streaming_fixed(request: ChatCompletionRequest):
    """🎯 FIXED OpenAI-compatible endpoint with proper streaming"""
    
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    try:
        if not request.messages:
            raise HTTPException(400, "No messages provided")
        
        # Extract user message
        raw_user_message = ""
        for msg in request.messages:
            if hasattr(msg, 'dict'):
                msg_data = msg.dict()
            elif isinstance(msg, dict):
                msg_data = msg
            else:
                msg_data = {"role": "user", "content": str(msg)}
            
            if msg_data.get("role") == "user":
                raw_user_message = msg_data.get("content", "")
        
        if not raw_user_message:
            raise HTTPException(400, "No user message found")
        
        # Process with message filter
        filter_result = message_filter.process_message(raw_user_message)
        
        logger.info(f"🔍 Filter result: is_title={filter_result['is_title_request']}, should_rag={filter_result['should_process_rag']}")
        
        # Handle Pure Title Generation Requests
        if filter_result["is_title_request"] and not filter_result["should_process_rag"]:
            logger.info("🎯 Pure title generation request")
            
            title_response = filter_result["title_response"]
            
            if request.stream:
                async def generate_title_stream():
                    title_chunk = streaming_fixer.create_openai_chunk(title_response, finish_reason="stop", is_first=True)
                    yield streaming_fixer.format_sse_data(title_chunk)
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate_title_stream(),
                    media_type="text/event-stream",
                    headers=streaming_fixer.get_streaming_headers()
                )
            else:
                return {
                    "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": tenant_config['model'],
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": title_response},
                        "finish_reason": "stop"
                    }]
                }
        
        # Process RAG Request
        user_message = filter_result["user_question"] or raw_user_message
        
        logger.info(f"🎯 Processing RAG for {tenant_id}: {user_message[:50]}...")
        
        # 🚀 FIXED Streaming Response
        if request.stream:
            return StreamingResponse(
                generate_openai_streaming_fixed(tenant_id, user_message, tenant_config),
                media_type="text/event-stream",
                headers=streaming_fixer.get_streaming_headers()
            )
        
        # Non-streaming Response
        else:
            try:
                if config.use_n8n and tenant_id in config.n8n_webhooks:
                    # N8N webhook call
                    webhook_url = config.n8n_webhooks[tenant_id]
                    payload = {
                        "message": user_message,
                        "tenant_id": tenant_id,
                        "timestamp": datetime.now().isoformat(),
                        "source": "openwebui_proxy_fixed"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=payload, timeout=30) as response:
                            if response.status == 200:
                                result = await response.json()
                                full_answer = result.get("answer", "ไม่สามารถประมวลผลได้")
                            else:
                                full_answer = f"❌ N8N service error: HTTP {response.status}"
                
                else:
                    # Direct RAG service
                    rag_url = f"{config.rag_service_url}/api/query"
                    payload = {"question": user_message, "tenant_id": tenant_id}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(rag_url, json=payload, timeout=30) as response:
                            if response.status == 200:
                                result = await response.json()
                                full_answer = result.get("response", result.get("answer", "ไม่สามารถประมวลผลได้"))
                            else:
                                full_answer = f"❌ RAG service error: HTTP {response.status}"
                
                # Add title if mixed request
                if filter_result["is_title_request"]:
                    full_answer += f"\n\n{filter_result['title_response']}"
                
                return {
                    "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": tenant_config['model'],
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": full_answer},
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message.split()),
                        "completion_tokens": len(full_answer.split()),
                        "total_tokens": len(user_message.split()) + len(full_answer.split())
                    }
                }
                
            except Exception as e:
                logger.error(f"❌ Non-streaming processing error: {e}")
                error_message = f"❌ เกิดข้อผิดพลาด: {str(e)}"
                
                return {
                    "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": tenant_config['model'],
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": error_message},
                        "finish_reason": "stop"
                    }]
                }
            
    except Exception as e:
        logger.error(f"🔥 Request processing error: {e}")
        raise HTTPException(500, f"Internal server error: {str(e)}")

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """🏥 Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Fixed OpenWebUI N8N Proxy v4.2",
        "streaming_fix": "enabled",
        "message_filter": "enabled",
        "n8n_enabled": config.use_n8n,
        "tenant": get_tenant_id()
    }

@app.get("/v1/models")
async def list_models():
    """📋 List available models (OpenAI compatible)"""
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "object": "list",
        "data": [{
            "id": tenant_config['model'],
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": f"siam-tech-{tenant_id}",
            "permission": [],
            "root": tenant_config['model'],
            "parent": None,
            "streaming_fixed": True
        }]
    }

@app.get("/config")
async def get_config():
    """⚙️ Get current configuration"""
    return {
        "tenant_id": get_tenant_id(),
        "tenant_config": get_tenant_config(get_tenant_id()),
        "use_n8n": config.use_n8n,
        "rag_service_url": config.rag_service_url,
        "streaming_fix_enabled": True,
        "message_filter_enabled": True,
        "available_tenants": list(config.tenant_configs.keys())
    }

@app.get("/test-streaming")
async def test_streaming():
    """🧪 Test streaming endpoint"""
    
    async def generate_test_stream():
        fixer = OpenWebUIStreamingFixer()
        
        # Initial chunk
        initial_chunk = fixer.create_openai_chunk("", is_first=True)
        yield fixer.format_sse_data(initial_chunk)
        
        # Test content
        test_words = ["สวัสดี", "ครับ", "นี่", "คือ", "การ", "ทดสอบ", "streaming", "ระบบ"]
        
        for word in test_words:
            content_chunk = fixer.create_openai_chunk(word + " ")
            yield fixer.format_sse_data(content_chunk)
            await asyncio.sleep(0.2)
        
        # Final chunk
        final_chunk = fixer.create_openai_chunk("", finish_reason="stop")
        yield fixer.format_sse_data(final_chunk)
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_test_stream(),
        media_type="text/event-stream",
        headers=streaming_fixer.get_streaming_headers()
    )

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Starting FIXED OpenWebUI N8N Proxy v4.2")
    logger.info(f"🏢 Default Tenant: {config.default_tenant}")
    logger.info(f"🤖 N8N Integration: {'Enabled' if config.use_n8n else 'Disabled'}")
    logger.info(f"🔧 Streaming Fix: Enabled")
    logger.info(f"🔍 Message Filtering: Enabled")
    logger.info(f"🌐 Port: {config.port}")
    
    # Test streaming format on startup
    logger.info("🧪 Testing streaming format...")
    fixer = OpenWebUIStreamingFixer()
    test_chunk = fixer.create_openai_chunk("Test", is_first=True)
    logger.info(f"✅ Test chunk format: {json.dumps(test_chunk)}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.port,
        log_level="info"
    )