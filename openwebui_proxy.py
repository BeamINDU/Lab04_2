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
# CONFIGURATION
# =============================================================================

class ProxyConfig:
    def __init__(self):
        self.n8n_base_url = os.getenv('N8N_BASE_URL', 'http://n8n:5678')
        self.default_tenant = os.getenv('DEFAULT_TENANT', 'company-a')
        self.force_tenant = os.getenv('FORCE_TENANT')
        self.port = int(os.getenv('PORT', '8001'))
        self.tenant_configs = {
            'company-a': {'name': 'SiamTech Bangkok HQ', 'model': 'llama3.1:8b', 'language': 'th', 'webhook_path': 'company-a-chat'},
            'company-b': {'name': 'SiamTech Chiang Mai Regional', 'model': 'llama3.1:8b', 'language': 'th', 'webhook_path': 'company-b-chat'},
            'company-c': {'name': 'SiamTech International', 'model': 'llama3.1:8b', 'language': 'en', 'webhook_path': 'company-c-chat'}
        }

config = ProxyConfig()
app = FastAPI(title=f"OpenWebUI Proxy - {config.force_tenant or 'Multi-Tenant'} (Fixed)", version="2.2.0")

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
# HELPER FUNCTIONS
# =============================================================================

def get_tenant_id() -> str:
    return config.force_tenant or config.default_tenant

def get_tenant_config(tenant_id: str) -> Dict:
    return config.tenant_configs.get(tenant_id, config.tenant_configs['company-a'])

async def call_n8n_webhook(tenant_id: str, message: str, conversation_history: list = None) -> Dict[str, Any]:
    """Call n8n webhook with enhanced error handling"""
    tenant_config = get_tenant_config(tenant_id)
    webhook_url = f"{config.n8n_base_url}/webhook/{tenant_config['webhook_path']}"
    
    payload = {
        "message": message,
        "tenant_id": tenant_id,
        "agent_type": "auto",
        "conversation_history": conversation_history or [],
        "settings": {"model": tenant_config['model'], "temperature": 0.7, "max_tokens": 2000},
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"n8n response type: {type(result)}")
                    logger.info(f"n8n response keys: {result.keys() if isinstance(result, dict) else 'not dict'}")
                    return result
                else:
                    logger.error(f"n8n webhook error: {response.status}")
                    return {"answer": f"เกิดข้อผิดพลาดในการเรียก workflow (HTTP {response.status})", "success": False, "tenant_id": tenant_id}
    except asyncio.TimeoutError:
        logger.error("n8n webhook timeout")
        return {"answer": "ระบบใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง", "success": False, "tenant_id": tenant_id}
    except Exception as e:
        logger.error(f"n8n webhook call failed: {e}")
        return {"answer": f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {str(e)}", "success": False, "tenant_id": tenant_id}

# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    return {
        "status": "healthy",
        "service": "OpenWebUI Proxy (Fixed)",
        "version": "2.2.0",
        "tenant_id": tenant_id,
        "tenant_name": tenant_config['name'],
        "model": tenant_config['model'],
        "n8n_url": config.n8n_base_url,
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
                    "proxy_version": "2.3.0"
                }
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Fixed chat completions endpoint with enhanced error handling"""
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    try:
        if not request.messages:
            raise HTTPException(400, "No messages provided")
        
        user_message = ""
        conversation_history = []
        
        # Enhanced message parsing
        for msg in request.messages:
            try:
                # Handle both dict and Pydantic model formats
                if hasattr(msg, 'dict'):
                    msg_data = msg.dict()
                elif isinstance(msg, dict):
                    msg_data = msg
                else:
                    # Convert to dict if it's a different type
                    msg_data = {"role": "user", "content": str(msg)}
                
                role = msg_data.get("role", "user")
                content = msg_data.get("content", "")
                
                if role == "user":
                    user_message = content
                
                conversation_history.append({"role": role, "content": content})
                
            except Exception as msg_error:
                logger.error(f"Error parsing message: {msg_error}")
                # Skip problematic messages
                continue
        
        if not user_message:
            raise HTTPException(400, "No user message found")
        
        logger.info(f"Processing chat completion for {tenant_id}: {user_message[:100]}...")
        
        # Call n8n webhook
        n8n_response = await call_n8n_webhook(tenant_id, user_message, conversation_history[:-1])
        
        # Enhanced response parsing
        answer = "ไม่สามารถรับคำตอบได้"
        success = False
        
        try:
            if isinstance(n8n_response, dict):
                # Direct access for dict
                answer = n8n_response.get("answer", "ไม่สามารถรับคำตอบได้")
                success = n8n_response.get("success", True)
            elif isinstance(n8n_response, str):
                # Handle string response
                try:
                    parsed = json.loads(n8n_response)
                    answer = parsed.get("answer", n8n_response)
                    success = parsed.get("success", True)
                except json.JSONDecodeError:
                    answer = n8n_response
                    success = True
            else:
                # Handle other types
                answer = str(n8n_response)
                success = True
                
        except Exception as parse_error:
            logger.error(f"Error parsing n8n response: {parse_error}")
            logger.error(f"Response type: {type(n8n_response)}")
            logger.error(f"Response content: {str(n8n_response)[:500]}...")
            answer = f"เกิดข้อผิดพลาดในการแปลงข้อมูล: {str(parse_error)}"
            success = False
        
        if not success:
            logger.warning(f"n8n workflow returned error for {tenant_id}")
        
        # Format as OpenAI response
        response_data = {
            "id": f"chatcmpl-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": answer
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(answer.split()),
                "total_tokens": len(user_message.split()) + len(answer.split())
            },
            "system_fingerprint": f"siamtech-{tenant_id}-v2.2",
            "siamtech_metadata": {
                "tenant_id": tenant_id,
                "tenant_name": tenant_config['name'],
                "model_used": tenant_config['model'],
                "workflow_success": success,
                "proxy_version": "2.2.0",
                "original_response_type": str(type(n8n_response))
            }
        }
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat completions for {tenant_id}: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return error response in OpenAI format
        return {
            "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": tenant_config['model'],
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "error": str(e)
        }

@app.get("/v1/chat/completions")
async def chat_completions_get():
    return {"message": "Chat completions endpoint is ready. Use POST method."}

# =============================================================================
# PROXY ENDPOINTS
# =============================================================================

@app.post("/proxy/n8n")
async def proxy_n8n(request: Dict[str, Any]):
    tenant_id = get_tenant_id()
    
    try:
        result = await call_n8n_webhook(
            tenant_id=tenant_id,
            message=request.get("message", ""),
            conversation_history=request.get("conversation_history", [])
        )
        return result
    except Exception as e:
        logger.error(f"Error in n8n proxy for {tenant_id}: {e}")
        return {"error": str(e), "success": False}

# =============================================================================
# INFO ENDPOINTS
# =============================================================================

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
        "proxy_config": {
            "n8n_base_url": config.n8n_base_url,
            "force_tenant": config.force_tenant,
            "default_tenant": config.default_tenant
        },
        "version": "2.2.0"
    }

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    tenant_id = get_tenant_id()
    tenant_config = get_tenant_config(tenant_id)
    
    print("🔗 OpenWebUI Proxy Server v2.2 (Fixed)")
    print("=" * 50)
    print(f"🏢 Tenant: {tenant_config['name']} ({tenant_id})")
    print(f"🤖 Model: {tenant_config['model']}")
    print(f"🌐 Language: {tenant_config['language']}")
    print(f"📡 n8n URL: {config.n8n_base_url}")
    print(f"🔧 Port: {config.port}")
    print(f"🛠️ Fixes: Enhanced error handling, response parsing")
    print("=" * 50)
    
    uvicorn.run("openwebui_proxy:app", host="0.0.0.0", port=config.port, reload=False)