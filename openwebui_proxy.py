import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

class ProxyConfig:
    def __init__(self):
        self.n8n_base_url = os.getenv('N8N_BASE_URL', 'http://n8n:5678')
        self.rag_service_url = os.getenv('RAG_SERVICE_URL', 'http://rag-service:5000')
        self.default_tenant = os.getenv('DEFAULT_TENANT', 'company-a')
        self.force_tenant = os.getenv('FORCE_TENANT')
        self.port = int(os.getenv('PORT', '8001'))
        self.tenant_configs = {
            'company-a': {
                'name': 'SiamTech Bangkok HQ', 
                'model': 'llama3.1:8b', 
                'language': 'th', 
                'webhook_path': 'company-a-chat'
            },
            'company-b': {
                'name': 'SiamTech Chiang Mai Regional', 
                'model': 'llama3.1:8b', 
                'language': 'th', 
                'webhook_path': 'company-b-chat'
            },
            'company-c': {
                'name': 'SiamTech International', 
                'model': 'llama3.1:8b', 
                'language': 'en', 
                'webhook_path': 'company-c-chat'
            }
        }

config = ProxyConfig()
app = FastAPI(title=f"OpenWebUI Streaming Proxy - {config.force_tenant or 'Multi-Tenant'} v3.0", version="3.0.0")

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
# STREAMING HELPER FUNCTIONS
# =============================================================================

def get_tenant_id() -> str:
    return config.force_tenant or config.default_tenant

def get_tenant_config(tenant_id: str) -> Dict:
    return config.tenant_configs.get(tenant_id, config.tenant_configs['company-a'])

async def call_rag_service_streaming(tenant_id: str, message: str, conversation_history: list = None) -> AsyncGenerator[str, None]:
    """🆕 Call RAG service with streaming support"""
    tenant_config = get_tenant_config(tenant_id)
    
    payload = {
        "query": message,
        "tenant_id": tenant_id,
        "agent_type": "enhanced_sql",
        "include_insights": True,
        "response_format": "business_analysis",
        "stream": True  # 🆕 Request streaming
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.rag_service_url}/enhanced-rag-query",
                json=payload,
                headers={"X-Tenant-ID": tenant_id},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                if response.status != 200:
                    logger.error(f"RAG service error: {response.status}")
                    yield f"data: {json.dumps({'error': f'RAG service error: {response.status}'})}\n\n"
                    return
                
                # Check if response supports streaming
                content_type = response.headers.get('content-type', '')
                
                if 'text/event-stream' in content_type or 'application/stream+json' in content_type:
                    # 🆕 Handle actual streaming response
                    async for chunk in response.content.iter_chunked(1024):
                        if chunk:
                            try:
                                chunk_text = chunk.decode('utf-8')
                                yield chunk_text
                            except Exception as e:
                                logger.error(f"Error processing stream chunk: {e}")
                                
                else:
                    # 🔄 Fallback: Simulate streaming for non-streaming responses
                    result = await response.json()
                    answer = result.get('answer', 'ไม่สามารถรับคำตอบได้')
                    
                    # Split answer into chunks and stream
                    words = answer.split()
                    chunk_size = 3  # 3 words per chunk
                    
                    for i in range(0, len(words), chunk_size):
                        chunk = ' '.join(words[i:i + chunk_size])
                        
                        # Format as OpenAI streaming chunk
                        chunk_data = {
                            "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": tenant_config['model'],
                            "choices": [{
                                "index": 0,
                                "delta": {"content": chunk + " "},
                                "finish_reason": None
                            }],
                            "siamtech_metadata": {
                                "tenant_id": tenant_id,
                                "streaming": "simulated",
                                "chunk_index": i // chunk_size
                            }
                        }
                        
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.1)  # Small delay for realistic streaming
                    
                    # Send final chunk
                    final_chunk = {
                        "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk", 
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }],
                        "siamtech_metadata": {
                            "tenant_id": tenant_id,
                            "sql_query": result.get('sql_query'),
                            "db_results_count": result.get('db_results_count'),
                            "processing_time": result.get('processing_time_seconds'),
                            "data_source": result.get('data_source_used'),
                            "enhancement_version": "3.0"
                        }
                    }
                    
                    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    
    except asyncio.TimeoutError:
        logger.error("RAG service timeout")
        error_chunk = {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [{
                "index": 0,
                "delta": {"content": "ระบบใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"RAG service call failed: {e}")
        error_chunk = {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [{
                "index": 0,
                "delta": {"content": f"เกิดข้อผิดพลาด: {str(e)}"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

async def call_n8n_webhook_streaming(tenant_id: str, message: str, conversation_history: list = None) -> AsyncGenerator[str, None]:
    """🔄 Fallback: Call n8n webhook with simulated streaming"""
    tenant_config = get_tenant_config(tenant_id)
    webhook_url = f"{config.n8n_base_url}/webhook/{tenant_config['webhook_path']}"
    
    payload = {
        "message": message,
        "tenant_id": tenant_id,
        "agent_type": "enhanced_sql",
        "conversation_history": conversation_history or [],
        "settings": {"model": tenant_config['model'], "temperature": 0.7, "max_tokens": 2000},
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=90)) as response:
                if response.status == 200:
                    result = await response.json()
                    answer = result.get('answer', 'ไม่สามารถรับคำตอบได้')
                    
                    # Simulate streaming by chunking the response
                    words = answer.split()
                    chunk_size = 4
                    
                    for i in range(0, len(words), chunk_size):
                        chunk = ' '.join(words[i:i + chunk_size])
                        
                        chunk_data = {
                            "id": f"chatcmpl-n8n-{int(datetime.now().timestamp())}",
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": tenant_config['model'],
                            "choices": [{
                                "index": 0,
                                "delta": {"content": chunk + " "},
                                "finish_reason": None
                            }],
                            "siamtech_metadata": {
                                "tenant_id": tenant_id,
                                "source": "n8n_workflow",
                                "streaming": "simulated"
                            }
                        }
                        
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.12)
                    
                    # Final chunk
                    final_chunk = {
                        "id": f"chatcmpl-n8n-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }],
                        "siamtech_metadata": result
                    }
                    
                    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                else:
                    logger.error(f"n8n webhook error: {response.status}")
                    # Yield error as stream
                    error_chunk = {
                        "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"เกิดข้อผิดพลาดในการเรียก workflow (HTTP {response.status})"},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    
    except Exception as e:
        logger.error(f"n8n streaming call failed: {e}")
        error_chunk = {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [{
                "index": 0,
                "delta": {"content": f"เกิดข้อผิดพลาด: {str(e)}"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

# =============================================================================
# MAIN ENDPOINTS
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
        "streaming_support": True,  # 🆕
        "features": [
            "openai_compatible_streaming",
            "rag_service_integration",
            "n8n_workflow_fallback",
            "multi_tenant_isolation",
            "enhanced_error_handling"
        ],
        "endpoints": {
            "rag_service": config.rag_service_url,
            "n8n_service": config.n8n_base_url
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models():
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "object": "list",
        "data": [
            {
                "id": "llama3.1:8b",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": f"siamtech-{tenant_id}",
                "siamtech_metadata": {
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_config['name'],
                    "language": tenant_config['language'],
                    "streaming_support": True,  # 🆕
                    "proxy_version": "3.0.0"
                }
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions_streaming(request: ChatCompletionRequest):
    """🚀 Enhanced chat completions with streaming support"""
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    try:
        if not request.messages:
            raise HTTPException(400, "No messages provided")
        
        user_message = ""
        conversation_history = []
        
        # Parse messages
        for msg in request.messages:
            try:
                if hasattr(msg, 'dict'):
                    msg_data = msg.dict()
                elif isinstance(msg, dict):
                    msg_data = msg
                else:
                    msg_data = {"role": "user", "content": str(msg)}
                
                role = msg_data.get("role", "user")
                content = msg_data.get("content", "")
                
                if role == "user":
                    user_message = content
                
                conversation_history.append({"role": role, "content": content})
                
            except Exception as msg_error:
                logger.error(f"Error parsing message: {msg_error}")
                continue
        
        if not user_message:
            raise HTTPException(400, "No user message found")
        
        logger.info(f"Processing streaming request for {tenant_id}: {user_message[:100]}...")
        
        # 🎯 Check if streaming is requested
        if request.stream:
            logger.info(f"Streaming response requested for {tenant_id}")
            
            # 🆕 Try RAG service first, fallback to n8n
            async def generate_stream():
                try:
                    # Primary: RAG service streaming
                    has_rag_response = False
                    async for chunk in call_rag_service_streaming(tenant_id, user_message, conversation_history[:-1]):
                        has_rag_response = True
                        yield chunk
                    
                    if not has_rag_response:
                        logger.warning(f"RAG service didn't respond, falling back to n8n for {tenant_id}")
                        async for chunk in call_n8n_webhook_streaming(tenant_id, user_message, conversation_history[:-1]):
                            yield chunk
                            
                except Exception as e:
                    logger.error(f"Error in streaming generation: {e}")
                    # Final fallback error stream
                    error_chunk = {
                        "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": tenant_config['model'],
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"เกิดข้อผิดพลาดในระบบ streaming: {str(e)}"},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        
        else:
            # 🔄 Non-streaming mode (backward compatibility)
            logger.info(f"Non-streaming response for {tenant_id}")
            
            # Try RAG service first
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "query": user_message,
                        "tenant_id": tenant_id,
                        "agent_type": "enhanced_sql",
                        "include_insights": True,
                        "response_format": "business_analysis"
                    }
                    
                    async with session.post(
                        f"{config.rag_service_url}/enhanced-rag-query",
                        json=payload,
                        headers={"X-Tenant-ID": tenant_id},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            answer = result.get('answer', 'ไม่สามารถรับคำตอบได้')
                            
                            return {
                                "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                                "object": "chat.completion",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": answer
                                    },
                                    "finish_reason": "stop"
                                }],
                                "usage": {
                                    "prompt_tokens": len(user_message.split()),
                                    "completion_tokens": len(answer.split()),
                                    "total_tokens": len(user_message.split()) + len(answer.split())
                                },
                                "system_fingerprint": f"siamtech-{tenant_id}-v3.0",
                                "siamtech_metadata": {
                                    "tenant_id": tenant_id,
                                    "tenant_name": tenant_config['name'],
                                    "model_used": tenant_config['model'],
                                    "streaming_available": True,
                                    "proxy_version": "3.0.0",
                                    "sql_query": result.get('sql_query'),
                                    "db_results_count": result.get('db_results_count'),
                                    "data_source": result.get('data_source_used')
                                }
                            }
                        else:
                            raise Exception(f"RAG service error: {response.status}")
                            
            except Exception as rag_error:
                logger.warning(f"RAG service failed, falling back to n8n: {rag_error}")
                
                # Fallback to n8n webhook
                webhook_url = f"{config.n8n_base_url}/webhook/{tenant_config['webhook_path']}"
                payload = {
                    "message": user_message,
                    "tenant_id": tenant_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status == 200:
                            result = await response.json()
                            answer = result.get('answer', 'ไม่สามารถรับคำตอบได้')
                            
                            return {
                                "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                                "object": "chat.completion",
                                "created": int(datetime.now().timestamp()),
                                "model": tenant_config['model'],
                                "choices": [{
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": answer
                                    },
                                    "finish_reason": "stop"
                                }],
                                "usage": {
                                    "prompt_tokens": len(user_message.split()),
                                    "completion_tokens": len(answer.split()),
                                    "total_tokens": len(user_message.split()) + len(answer.split())
                                },
                                "system_fingerprint": f"siamtech-{tenant_id}-n8n-v3.0",
                                "siamtech_metadata": {
                                    "tenant_id": tenant_id,
                                    "tenant_name": tenant_config['name'],
                                    "model_used": tenant_config['model'],
                                    "data_source": "n8n_workflow_fallback",
                                    "streaming_available": True,
                                    "proxy_version": "3.0.0"
                                }
                            }
                        else:
                            raise Exception(f"n8n webhook error: {response.status}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat completions for {tenant_id}: {e}")
        
        # Return error response in OpenAI format
        return {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "error": str(e),
            "siamtech_metadata": {
                "tenant_id": tenant_id,
                "error_type": "system_error",
                "proxy_version": "3.0.0"
            }
        }

# =============================================================================
# ADDITIONAL ENDPOINTS
# =============================================================================

@app.get("/v1/chat/completions")
async def chat_completions_get():
    return {
        "message": "Chat completions endpoint is ready. Use POST method.",
        "streaming_support": True,
        "usage": "Set 'stream': true in request body for streaming response"
    }

@app.post("/proxy/rag")
async def proxy_rag(request: Dict[str, Any]):
    """Direct RAG service proxy endpoint"""
    tenant_id = get_tenant_id()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.rag_service_url}/enhanced-rag-query",
                json=request,
                headers={"X-Tenant-ID": tenant_id},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                result = await response.json()
                return result
    except Exception as e:
        logger.error(f"Error in RAG proxy for {tenant_id}: {e}")
        return {"error": str(e), "success": False}

@app.get("/tenant/info")
async def tenant_info():
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant_config['name'],
        "model": tenant_config['model'],
        "language": tenant_config['language'],
        "webhook_path": tenant_config['webhook_path'],
        "streaming_support": True,  # 🆕
        "proxy_config": {
            "rag_service_url": config.rag_service_url,
            "n8n_base_url": config.n8n_base_url,
            "force_tenant": config.force_tenant,
            "default_tenant": config.default_tenant
        },
        "version": "3.0.0",
        "features": [
            "openai_streaming_compatible",
            "rag_service_integration", 
            "progressive_fallback",
            "enhanced_error_handling"
        ]
    }

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    print("🚀 OpenWebUI Streaming Proxy Server v3.0")
    print("=" * 60)
    print(f"🏢 Tenant: {tenant_config['name']} ({tenant_id})")
    print(f"🤖 Model: {tenant_config['model']}")
    print(f"🌐 Language: {tenant_config['language']}")
    print(f"📡 RAG Service: {config.rag_service_url}")
    print(f"📡 n8n Service: {config.n8n_base_url}")
    print(f"🔧 Port: {config.port}")
    print(f"🔄 Streaming: ✅ ENABLED")
    print(f"🛡️ Features: Progressive fallback, Enhanced errors")
    print("=" * 60)
    
    uvicorn.run("openwebui_proxy:app", host="0.0.0.0", port=config.port, reload=False)