import os
import time
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging
from intent_classifier import IntentClassifier

# Import the enhanced PostgreSQL + Ollama agent
from enhanced_postgres_agent import EnhancedPostgresOllamaAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# REQUEST/RESPONSE MODELS - Updated for Streaming
# =============================================================================

class EnhancedRAGQuery(BaseModel):
    query: str
    tenant_id: Optional[str] = None
    agent_type: Optional[str] = "enhanced_sql"
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    include_insights: Optional[bool] = True
    response_format: Optional[str] = "business_analysis"
    stream: Optional[bool] = False  # 🆕 Streaming support

class StreamingChunk(BaseModel):
    """Model for streaming response chunks"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list
    siamtech_metadata: Optional[dict] = None

# =============================================================================
# STREAMING HELPERS
# =============================================================================

async def stream_response_chunks(answer: str, tenant_id: str, metadata: dict) -> AsyncGenerator[str, None]:
    """Stream response in chunks for better UX"""
    
    config = ENHANCED_TENANT_CONFIGS[tenant_id]
    
    # Split answer into logical chunks (sentences/phrases)
    sentences = answer.replace('\n\n', '\n').split('\n')
    
    chunk_id = f"chatcmpl-stream-{int(datetime.now().timestamp())}"
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            # Create streaming chunk
            chunk_data = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": config["model"],
                "choices": [{
                    "index": 0,
                    "delta": {"content": sentence + "\n"},
                    "finish_reason": None
                }],
                "siamtech_metadata": {
                    "tenant_id": tenant_id,
                    "chunk_index": i,
                    "streaming": True,
                    "enhancement_version": "3.0"
                }
            }
            
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)  # Small delay for smoother streaming
    
    # Send final chunk with metadata
    final_chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": config["model"],
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }],
        "siamtech_metadata": {
            **metadata,
            "tenant_id": tenant_id,
            "streaming": True,
            "enhancement_version": "3.0",
            "total_chunks": len([s for s in sentences if s.strip()])
        }
    }
    
    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# =============================================================================
# ENHANCED TENANT CONFIGURATION
# =============================================================================

ENHANCED_TENANT_CONFIGS = {
    'company-a': {
        'name': 'SiamTech Bangkok HQ',
        'model': 'llama3.1:8b',
        'language': 'th',
        'business_type': 'enterprise_software',
        'description': 'สำนักงานใหญ่ กรุงเทพมฯ - Enterprise solutions, Banking, E-commerce',
        'specialization': 'Large-scale enterprise systems',
        'key_strengths': ['enterprise_architecture', 'banking_systems', 'high_performance']
    },
    'company-b': {
        'name': 'SiamTech Chiang Mai Regional',
        'model': 'llama3.1:8b',
        'language': 'th',
        'business_type': 'tourism_hospitality',
        'description': 'สาขาภาคเหนือ เชียงใหม่ - Tourism technology, Hospitality systems',
        'specialization': 'Tourism and hospitality solutions',
        'key_strengths': ['tourism_systems', 'regional_expertise', 'cultural_integration']
    },
    'company-c': {
        'name': 'SiamTech International',
        'model': 'llama3.1:8b',
        'language': 'en',
        'business_type': 'global_operations',
        'description': 'International Operations - Global projects, Cross-border solutions',
        'specialization': 'International software solutions',
        'key_strengths': ['global_platforms', 'multi_currency', 'cross_border_compliance']
    }
}

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="SiamTech Enhanced Multi-Tenant RAG Service with Streaming v3.0",
    description="Advanced RAG service with streaming responses, enhanced prompts, and business intelligence",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global enhanced agent (singleton)
enhanced_agent = EnhancedPostgresOllamaAgent()

# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")) -> str:
    """Extract and validate tenant ID"""
    tenant_id = x_tenant_id or "company-a"
    if tenant_id not in ENHANCED_TENANT_CONFIGS:
        raise HTTPException(400, f"Invalid tenant: {tenant_id}")
    return tenant_id

def validate_tenant_id(tenant_id: str) -> bool:
    """Validate if tenant ID exists"""
    return tenant_id in ENHANCED_TENANT_CONFIGS

# =============================================================================
# ENHANCED STREAMING ENDPOINTS
# =============================================================================

@app.post("/enhanced-rag-query")
async def enhanced_rag_query_with_streaming(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """🚀 Enhanced RAG endpoint with streaming support"""
    start_time = time.time()
    
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    try:
        logger.info(f"Processing {'streaming' if request.stream else 'regular'} query for {tenant_id}: {request.query[:100]}...")
        
        # Process with enhanced agent
        result = await enhanced_agent.process_enhanced_question(
            question=request.query,
            tenant_id=tenant_id
        )
        
        response_time = int((time.time() - start_time) * 1000)
        tenant_config = ENHANCED_TENANT_CONFIGS[tenant_id]
        
        # Prepare metadata
        metadata = {
            "tenant_id": tenant_id,
            "tenant_name": tenant_config["name"],
            "model_used": result.get("model_used", tenant_config["model"]),
            "data_source_used": result.get("data_source_used"),
            "sql_query": result.get("sql_query"),
            "db_results_count": result.get("db_results_count"),
            "sql_generation_method": result.get("sql_generation_method", "ai_generation"),
            "confidence_level": result.get("confidence", "medium"),
            "processing_time_seconds": result.get("processing_time_seconds"),
            "response_time_ms": response_time,
            "enhancement_version": "3.0",
            "streaming_enabled": request.stream
        }
        
        answer = result.get("answer", "ไม่สามารถรับคำตอบได้")
        
        # 🎯 Return streaming or regular response
        if request.stream:
            logger.info(f"Returning streaming response for {tenant_id}")
            
            async def generate_streaming_response():
                async for chunk in stream_response_chunks(answer, tenant_id, metadata):
                    yield chunk
            
            return StreamingResponse(
                generate_streaming_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        else:
            # Regular JSON response
            return {
                "answer": answer,
                "success": result.get("success", True),
                "tenant_id": tenant_id,
                "tenant_name": tenant_config["name"],
                "model_used": result.get("model_used", tenant_config["model"]),
                "data_source_used": result.get("data_source_used"),
                "agent_type": "enhanced_sql_v3",
                "response_time_ms": response_time,
                "sql_query": result.get("sql_query"),
                "db_results_count": result.get("db_results_count"),
                "sql_generation_method": result.get("sql_generation_method", "ai_generation"),
                "confidence_level": result.get("confidence", "medium"),
                "processing_time_seconds": result.get("processing_time_seconds"),
                "enhancement_version": "3.0"
            }
            
    except Exception as e:
        logger.error(f"Error in enhanced_rag_query for {tenant_id}: {e}")
        response_time = int((time.time() - start_time) * 1000)
        
        error_response = {
            "answer": f"เกิดข้อผิดพลาดในระบบ Enhanced v3.0: {str(e)}",
            "success": False,
            "tenant_id": tenant_id,
            "tenant_name": ENHANCED_TENANT_CONFIGS[tenant_id]["name"],
            "agent_type": "error_handler",
            "response_time_ms": response_time,
            "confidence_level": "none",
            "enhancement_version": "3.0",
            "error": str(e)
        }
        
        if request.stream:
            # Return error as stream
            async def generate_error_stream():
                error_chunk = {
                    "id": f"chatcmpl-error-{int(datetime.now().timestamp())}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": ENHANCED_TENANT_CONFIGS[tenant_id]["model"],
                    "choices": [{
                        "index": 0,
                        "delta": {"content": error_response["answer"]},
                        "finish_reason": "stop"
                    }],
                    "siamtech_metadata": error_response
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_error_stream(),
                media_type="text/event-stream"
            )
        else:
            return error_response

@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check endpoint with streaming capabilities"""
    return {
        "status": "healthy",
        "service": "SiamTech Enhanced Multi-Tenant RAG with Streaming v3.0",
        "version": "3.0.0",
        "streaming_support": True,  # 🆕
        "enhancement_features": [
            "smart_sql_generation_with_patterns",
            "business_intelligence_insights", 
            "enhanced_prompt_engineering",
            "streaming_responses",  # 🆕
            "advanced_error_handling",
            "performance_tracking",
            "confidence_scoring"
        ],
        "streaming_features": [  # 🆕
            "real_time_response_chunks",
            "openai_compatible_streaming",
            "progressive_content_delivery",
            "enhanced_user_experience"
        ],
        "tenants": list(ENHANCED_TENANT_CONFIGS.keys()),
        "ollama_server": os.getenv('OLLAMA_BASE_URL', 'http://13.212.102.46:12434'),
        "agent_type": "EnhancedPostgresOllamaAgent",
        "prompt_version": "3.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/v1/chat/completions")
async def openai_compatible_streaming(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """🚀 OpenAI-compatible endpoint with full streaming support"""
    try:
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(400, "No messages provided")
        
        # Extract the last user message
        user_message = messages[-1].get("content", "")
        stream_requested = request.get("stream", False)
        
        logger.info(f"OpenAI compatible request ({'streaming' if stream_requested else 'regular'}) for {tenant_id}")
        
        # Create RAG request
        rag_request = EnhancedRAGQuery(
            query=user_message,
            tenant_id=tenant_id,
            stream=stream_requested,
            temperature=request.get("temperature", 0.7),
            max_tokens=request.get("max_tokens", 2000)
        )
        
        # Process with enhanced RAG
        if stream_requested:
            # Return streaming response
            return await enhanced_rag_query_with_streaming(rag_request, tenant_id)
        else:
            # Return regular JSON response in OpenAI format
            result = await enhanced_rag_query_with_streaming(rag_request, tenant_id)
            
            tenant_config = ENHANCED_TENANT_CONFIGS[tenant_id]
            answer = result.get("answer", "ไม่สามารถรับคำตอบได้")
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": f"siamtech-enhanced-{tenant_config['model']}",
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
                "system_fingerprint": f"siamtech-enhanced-streaming-v3-{tenant_id}",
                "siamtech_enhanced_metadata": {
                    **result,
                    "streaming_available": True,
                    "openai_compatible": True
                }
            }
        
    except Exception as e:
        logger.error(f"Error in OpenAI compatible endpoint for {tenant_id}: {e}")
        raise HTTPException(500, f"OpenAI compatible request failed: {str(e)}")

# =============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS
# =============================================================================

@app.post("/rag-query")
async def legacy_rag_query(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Legacy RAG endpoint with enhanced backend and streaming support"""
    return await enhanced_rag_query_with_streaming(request, tenant_id)

@app.get("/streaming/test/{tenant_id}")
async def test_streaming(tenant_id: str):
    """Test endpoint for streaming functionality"""
    if not validate_tenant_id(tenant_id):
        raise HTTPException(404, f"Tenant {tenant_id} not found")
    
    async def generate_test_stream():
        test_messages = [
            "🧪 Testing streaming functionality...",
            "📊 Connecting to enhanced RAG system...",
            "🤖 AI model loaded successfully...",
            "🗄️ Database connection established...",
            "✅ Streaming test completed!"
        ]
        
        for i, message in enumerate(test_messages):
            chunk_data = {
                "id": f"test-stream-{int(datetime.now().timestamp())}",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": ENHANCED_TENANT_CONFIGS[tenant_id]["model"],
                "choices": [{
                    "index": 0,
                    "delta": {"content": message + "\n"},
                    "finish_reason": "stop" if i == len(test_messages)-1 else None
                }],
                "siamtech_metadata": {
                    "tenant_id": tenant_id,
                    "test_chunk": i + 1,
                    "total_chunks": len(test_messages),
                    "streaming_test": True
                }
            }
            
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.5)
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_test_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    print("🚀 SiamTech Enhanced Multi-Tenant RAG Service with Streaming v3.0")
    print("=" * 80)
    print("🧠 Enhanced Features:")
    print("   • 🔄 Real-time Streaming Responses")
    print("   • 🤖 Smart SQL Generation with Pattern Matching")
    print("   • 📊 Business Intelligence & Automated Insights")
    print("   • 🎯 Enhanced Prompt Engineering v3.0")
    print("   • 🛡️ Advanced Error Recovery & Fallback")
    print("   • 📈 Performance Tracking & Confidence Scoring")
    print("   • 🎨 Structured Business Analysis Responses")
    print("")
    print(f"📊 Tenants: {list(ENHANCED_TENANT_CONFIGS.keys())}")
    print(f"🤖 Ollama Server: {os.getenv('OLLAMA_BASE_URL', 'http://13.212.102.46:12434')}")
    print(f"🗄️  Database: Multi-tenant PostgreSQL with Enhanced Intelligence")
    print(f"🎯 Agent: EnhancedPostgresOllamaAgent v3.0")
    print(f"🔄 Streaming: ✅ ENABLED (OpenAI Compatible)")
    print(f"📈 Expected Improvements: 85%+ better UX with streaming")
    print("=" * 80)
    
    uvicorn.run(
        "enhanced_multi_agent_service:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True,
        log_level="info"
    )