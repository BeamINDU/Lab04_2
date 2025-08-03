# 🔥 แก้ไข openwebui_proxy.py ให้รองรับ streaming จริง

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (เดิม)
# =============================================================================

class ProxyConfig:
    def __init__(self):
        self.n8n_base_url = os.getenv('N8N_BASE_URL', 'http://n8n:5678')
        self.rag_service_url = os.getenv('ENHANCED_RAG_SERVICE', 'http://rag-service:5000')  # 🔥 เพิ่ม
        self.default_tenant = os.getenv('DEFAULT_TENANT', 'company-a')
        self.force_tenant = os.getenv('FORCE_TENANT')
        self.port = int(os.getenv('PORT', '8001'))
        self.tenant_configs = {
            'company-a': {'name': 'SiamTech Bangkok HQ', 'model': 'llama3.1:8b', 'language': 'th'},
            'company-b': {'name': 'SiamTech Chiang Mai Regional', 'model': 'llama3.1:8b', 'language': 'th'},
            'company-c': {'name': 'SiamTech International', 'model': 'llama3.1:8b', 'language': 'en'}
        }

config = ProxyConfig()
app = FastAPI(title=f"OpenWebUI Streaming Proxy v3.0", version="3.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# =============================================================================
# MODELS (เดิม)
# =============================================================================

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False

# =============================================================================
# 🔥 STREAMING FUNCTIONS - ใหม่หมด
# =============================================================================

def get_tenant_id() -> str:
    return config.force_tenant or config.default_tenant

def get_tenant_config(tenant_id: str) -> Dict:
    return config.tenant_configs.get(tenant_id, config.tenant_configs['company-a'])

async def call_rag_service_streaming(tenant_id: str, message: str):
    """🔥 เรียก RAG service แบบ streaming จริงๆ"""
    
    payload = {
        "query": message,
        "tenant_id": tenant_id,
        "agent_type": "enhanced_sql",
        "temperature": 0.7,
        "include_insights": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.rag_service_url}/enhanced-rag-query-stream",
                json=payload,
                headers={"X-Tenant-ID": tenant_id},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    # 🔥 อ่าน streaming response จาก RAG service
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    data_str = line_str[6:]  # ตัด "data: " ออก
                                    if data_str and data_str != '[DONE]':
                                        data = json.loads(data_str)
                                        yield data
                                except json.JSONDecodeError:
                                    continue
                else:
                    yield {"type": "error", "message": f"RAG service error: HTTP {response.status}"}
                    
    except Exception as e:
        logger.error(f"RAG service streaming error: {e}")
        yield {"type": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"}

# =============================================================================
# 🔥 MAIN STREAMING ENDPOINT - แก้ไขทั้งหมด
# =============================================================================

@app.post("/v1/chat/completions")
async def chat_completions_streaming(request: ChatCompletionRequest):
    """🔥 OpenAI-compatible endpoint with REAL streaming"""
    
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    try:
        if not request.messages:
            raise HTTPException(400, "No messages provided")
        
        # Extract user message
        user_message = ""
        for msg in request.messages:
            if hasattr(msg, 'dict'):
                msg_data = msg.dict()
            elif isinstance(msg, dict):
                msg_data = msg
            else:
                msg_data = {"role": "user", "content": str(msg)}
            
            if msg_data.get("role") == "user":
                user_message = msg_data.get("content", "")
        
        if not user_message:
            raise HTTPException(400, "No user message found")
        
        logger.info(f"🔥 Streaming request for {tenant_id}: {user_message[:50]}...")
        
        # 🚀 ถ้าขอ streaming
        if request.stream:
            async def generate_openai_streaming():
                try:
                    # ส่ง initial chunk
                    initial_chunk = {
                        "id": f"chatcmpl-streaming-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {"role": "assistant", "content": ""},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(initial_chunk)}\n\n"
                    
                    # 🔥 เรียก RAG service แบบ streaming
                    answer_started = False
                    full_answer = ""
                    
                    async for chunk in call_rag_service_streaming(tenant_id, user_message):
                        chunk_type = chunk.get("type", "")
                        
                        # 📊 แสดง status (optional)
                        if chunk_type == "status":
                            status_chunk = {
                                "id": f"chatcmpl-status-{int(datetime.now().timestamp())}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": f"⏳ {chunk.get('message', '')}\n"},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(status_chunk)}\n\n"
                        
                        # 🔥 ส่ง answer chunks
                        elif chunk_type == "answer_chunk":
                            if not answer_started:
                                # ส่ง newline เพื่อแยกจาก status
                                separator_chunk = {
                                    "id": f"chatcmpl-sep-{int(datetime.now().timestamp())}",
                                    "object": "chat.completion.chunk",
                                    "created": int(datetime.now().timestamp()),
                                    "model": tenant_config['model'],
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": "\n💬 "},
                                        "finish_reason": None
                                    }]
                                }
                                yield f"data: {json.dumps(separator_chunk)}\n\n"
                                answer_started = True
                            
                            # ส่ง actual content
                            content = chunk.get("content", "")
                            full_answer += content
                            
                            content_chunk = {
                                "id": f"chatcmpl-content-{int(datetime.now().timestamp())}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": content},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
                        
                        # ✅ จบแล้ว
                        elif chunk_type == "answer_complete":
                            # ส่ง metadata สรุป (optional)
                            summary_chunk = {
                                "id": f"chatcmpl-summary-{int(datetime.now().timestamp())}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": f"\n\n📊 ข้อมูล: {chunk.get('db_results_count', 0)} รายการ | SQL: {chunk.get('sql_generation_method', 'AI')}"},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(summary_chunk)}\n\n"
                            break
                        
                        # ❌ Error
                        elif chunk_type == "error":
                            error_chunk = {
                                "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": f"\n❌ {chunk.get('message', 'เกิดข้อผิดพลาด')}"},
                                    "finish_reason": "stop"
                                }]
                            }
                            yield f"data: {json.dumps(error_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                    
                    # ส่ง final chunk
                    final_chunk = {
                        "id": f"chatcmpl-final-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"🔥 Streaming error: {e}")
                    error_chunk = {
                        "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"\n❌ เกิดข้อผิดพลาดในระบบ: {str(e)}"},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_openai_streaming(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        
        # 🔄 Non-streaming (เดิม) - เรียก RAG service ปกติ
        else:
            # เรียก RAG service แบบปกติ
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": user_message,
                    "tenant_id": tenant_id,
                    "agent_type": "enhanced_sql"
                }
                
                async with session.post(
                    f"{config.rag_service_url}/enhanced-rag-query",
                    json=payload,
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("answer", "ไม่สามารถรับคำตอบได้")
                    else:
                        answer = f"เกิดข้อผิดพลาด (HTTP {response.status})"
            
            return {
                "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": tenant_config['model'],
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(answer.split()),
                    "total_tokens": len(user_message.split()) + len(answer.split())
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔥 Unexpected error: {e}")
        return {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "error": str(e)
        }

# =============================================================================
# เหลือ endpoints อื่นๆ เดิม
# =============================================================================

@app.get("/health")
async def health():
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "status": "healthy",
        "service": "OpenWebUI Streaming Proxy v3.0",
        "version": "3.0.0",
        "tenant_id": tenant_id,
        "tenant_name": tenant_config['name'],
        "model": tenant_config['model'],
        "rag_service": config.rag_service_url,
        "streaming_enabled": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models():
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "object": "list",
        "data": [{
            "id": "llama3.1:8b",
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": f"siamtech-{tenant_id}",
            "streaming_supported": True,
            "siamtech_metadata": {
                "tenant_id": tenant_id,
                "tenant_name": tenant_config['name'],
                "language": tenant_config['language'],
                "proxy_version": "3.0.0"
            }
        }]
    }

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    print("🔗 OpenWebUI Streaming Proxy v3.0")
    print("=" * 50)
    print(f"🏢 Tenant: {tenant_config['name']} ({tenant_id})")
    print(f"🤖 Model: {tenant_config['model']}")
    print(f"🌐 Language: {tenant_config['language']}")
    print(f"📡 RAG Service: {config.rag_service_url}")
    print(f"🔧 Port: {config.port}")
    print(f"🔥 Streaming: ENABLED")
    print("=" * 50)
    
    uvicorn.run("openwebui_proxy:app", host="0.0.0.0", port=config.port, reload=False)