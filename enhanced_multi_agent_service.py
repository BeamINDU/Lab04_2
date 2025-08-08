import os
import asyncio
import uvicorn
import time
import json
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# TENANT CONFIGURATIONS (EXISTING)
# =============================================================================

ENHANCED_TENANT_CONFIGS = {
    'company-a': {
        'name': 'SiamTech Main Office',
        'model': 'llama3.1:8b',
        'language': 'th',
        'business_type': 'enterprise',
        'description': 'สำนักงานใหญ่ กรุงเทพมฯ - Enterprise solutions, Banking, E-commerce',
        'specialization': 'Large-scale enterprise systems',
        'key_strengths': ['enterprise_architecture', 'banking_systems', 'high_performance']
    },
    'company-b': {
        'name': 'SiamTech Chiang Mai Regional',
        'model': 'gemma2:9b',
        'language': 'th',
        'business_type': 'tourism_hospitality',
        'description': 'สาขาภาคเหนือ เชียงใหม่ - Tourism technology, Hospitality systems',
        'specialization': 'Tourism and hospitality solutions',
        'key_strengths': ['tourism_systems', 'regional_expertise', 'cultural_integration']
    },
    'company-c': {
        'name': 'SiamTech International',
        'model': 'phi3:14b',
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
    title="SiamTech Modular Multi-Tenant RAG Service",
    description="Enhanced RAG with modular company-specific prompts",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ENHANCED AGENT INITIALIZATION (MODULAR SUPPORT)
# =============================================================================

# Initialize Enhanced Agent with Modular Support
try:
    from integration_bridge import ModularEnhancedAgent
    enhanced_agent = ModularEnhancedAgent(ENHANCED_TENANT_CONFIGS)
    print("✅ Modular Enhanced Agent loaded successfully")
    print(f"🎯 Modular support: {enhanced_agent.modular_available}")
    if enhanced_agent.modular_available:
        print("🏢 Company A: Modular prompts active")
        print("🔄 Company B,C: Original enhanced agent (fallback)")
    else:
        print("⚠️ Modular prompts not available, using original enhanced agent for all companies")
        
except ImportError as e:
    print(f"⚠️ Modular system not found: {e}")
    print("🔄 Falling back to original enhanced agent...")
    
    # Fallback ไปใช้ original
    try:
        from refactored_modules.universal_prompt_system import UniversalPromptMigrationGuide
        from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent
        
        original_agent = EnhancedPostgresOllamaAgent()
        enhanced_agent = UniversalPromptMigrationGuide.integrate_with_existing_agent(original_agent)
        print("✅ Original Universal Prompt System loaded")
    except Exception as fallback_error:
        print(f"❌ Universal Prompt System also failed: {fallback_error}")
        from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent
        enhanced_agent = EnhancedPostgresOllamaAgent()
        print("🔄 Using basic enhanced agent")
        
except Exception as e:
    print(f"❌ Modular Enhanced Agent failed: {e}")
    print("🔄 Falling back to original enhanced agent...")
    
    try:
        from refactored_modules.enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent
        enhanced_agent = EnhancedPostgresOllamaAgent()
        print("✅ Original enhanced agent loaded")
    except Exception as fallback_error:
        print(f"❌ All systems failed: {fallback_error}")
        raise fallback_error

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class EnhancedRAGQuery(BaseModel):
    query: str
    tenant_id: Optional[str] = None
    include_metadata: bool = True
    max_results: int = 20

class EnhancedRAGResponse(BaseModel):
    answer: str
    success: bool
    tenant_id: str
    data_source_used: str
    sql_query: Optional[str] = None
    processing_time: Optional[float] = None
    system_type: Optional[str] = None
    modular_system_used: Optional[bool] = None
    architecture: Optional[str] = None
    prompt_type: Optional[str] = None

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
# CORE ENDPOINTS
# =============================================================================

@app.post("/enhanced-rag-query", response_model=EnhancedRAGResponse)
async def enhanced_rag_query(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """🎯 Main query endpoint with modular prompt support"""
    
    # Override tenant_id if provided in request
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    try:
        start_time = time.time()
        result = await enhanced_agent.process_enhanced_question(request.query, tenant_id)
        processing_time = time.time() - start_time
        
        # Ensure processing time is included
        if 'processing_time' not in result:
            result['processing_time'] = processing_time
            
        return EnhancedRAGResponse(**result)
        
    except Exception as e:
        logger.error(f"Enhanced query processing failed for {tenant_id}: {e}")
        raise HTTPException(500, f"Enhanced query processing failed: {str(e)}")

@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check endpoint with Modular System status"""
    
    # ตรวจสอบ modular system
    modular_available = hasattr(enhanced_agent, 'modular_available') and enhanced_agent.modular_available
    modular_companies = 0
    modular_statistics = {}
    
    try:
        if hasattr(enhanced_agent, 'get_modular_statistics'):
            modular_statistics = enhanced_agent.get_modular_statistics()
            modular_companies = len(modular_statistics.get('companies_supported', []))
    except Exception as e:
        logger.warning(f"Could not get modular statistics: {e}")
    
    # ตรวจสอบ original enhanced agent capabilities
    original_features = []
    try:
        if hasattr(enhanced_agent, 'universal_integration'):
            original_features.append("universal_prompt_system")
        if hasattr(enhanced_agent, 'schema_service'):
            original_features.append("schema_discovery")
        if hasattr(enhanced_agent, 'business_mapper'):
            original_features.append("business_logic_mapping")
    except Exception as e:
        logger.warning(f"Could not check original features: {e}")
    
    return {
        "status": "healthy",
        "service": "SiamTech Modular Multi-Tenant RAG",
        "version": "4.0.0",
        "architecture": "hybrid_modular_enhanced",
        
        "modular_system": {
            "available": modular_available,
            "companies_supported": modular_companies,
            "statistics": modular_statistics,
            "status": "active" if modular_available else "fallback_only"
        },
        
        "enhancement_features": [
            "company_specific_prompts",      # 🆕 ใหม่
            "modular_architecture",          # 🆕 ใหม่  
            "hybrid_system_support",         # 🆕 ใหม่
            "gradual_migration_support",     # 🆕 ใหม่
            "automatic_fallback_mechanism",  # 🆕 ใหม่
        ] + original_features + [
            "smart_sql_generation_with_patterns",
            "business_intelligence_insights",
            "enhanced_prompt_engineering",
            "advanced_error_handling",
            "performance_tracking",
            "confidence_scoring"
        ],
        
        "companies": {
            "company-a": {
                "name": ENHANCED_TENANT_CONFIGS['company-a']['name'],
                "system": "modular_prompts" if modular_available else "original_enhanced",
                "prompt_type": "EnterprisePrompt" if modular_available else "universal_prompt"
            },
            "company-b": {
                "name": ENHANCED_TENANT_CONFIGS['company-b']['name'],
                "system": "original_enhanced",
                "prompt_type": "universal_prompt"
            },
            "company-c": {
                "name": ENHANCED_TENANT_CONFIGS['company-c']['name'],
                "system": "original_enhanced", 
                "prompt_type": "universal_prompt"
            }
        },
        
        "tenants": list(ENHANCED_TENANT_CONFIGS.keys()),
        "ollama_server": os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434'),
        "agent_type": "ModularEnhancedAgent" if modular_available else "EnhancedPostgresOllamaAgent",
        "prompt_version": "4.0_modular_hybrid",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/modular-status")
async def modular_system_status():
    """📊 ตรวจสอบสถานะ modular system"""
    
    if hasattr(enhanced_agent, 'get_modular_statistics'):
        try:
            stats = enhanced_agent.get_modular_statistics()
            
            return {
                "status": "active" if stats['modular_system_available'] else "fallback_only",
                "modular_system": stats,
                "features": [
                    "Company-specific prompt isolation",
                    "Gradual migration support", 
                    "Automatic fallback mechanism",
                    "Statistics tracking"
                ],
                "architecture": "hybrid_modular_enhanced",
                "deployment_strategy": "gradual_company_migration"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback": "Using original enhanced agent"
            }
    else:
        return {
            "status": "not_available",
            "message": "Modular system not loaded",
            "fallback": "Using original enhanced agent",
            "architecture": "original_enhanced_only"
        }

@app.post("/test-modular-vs-original")
async def test_modular_vs_original():
    """🧪 ทดสอบเปรียบเทียบ modular vs original"""
    
    test_questions = [
        ("company-a", "พนักงานในแผนก IT มีใครบ้าง"),
        ("company-b", "โปรเจคท่องเที่ยวมีอะไรบ้าง"),
        ("company-c", "Which international projects have highest revenue")
    ]
    
    results = []
    
    for tenant_id, question in test_questions:
        try:
            start_time = time.time()
            result = await enhanced_agent.process_enhanced_question(question, tenant_id)
            processing_time = time.time() - start_time
            
            test_result = {
                "tenant_id": tenant_id,
                "question": question,
                "status": "success" if result.get('success') else "failed",
                "system_used": result.get('system_type', 'unknown'),
                "modular_used": result.get('modular_system_used', False),
                "processing_time": round(processing_time, 3),
                "response_length": len(result.get('answer', '')),
                "architecture": result.get('architecture', 'unknown'),
                "prompt_type": result.get('prompt_type', 'unknown')
            }
            
        except Exception as e:
            test_result = {
                "tenant_id": tenant_id,
                "question": question,
                "status": "error",
                "error": str(e)
            }
        
        results.append(test_result)
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    modular_used = len([r for r in results if r.get('modular_used')])
    
    return {
        "test_summary": {
            "total_tests": len(results),
            "successful": successful,
            "modular_system_used": modular_used,
            "fallback_used": successful - modular_used,
            "success_rate": f"{(successful/len(results)*100):.1f}%",
            "modular_rate": f"{(modular_used/len(results)*100):.1f}%"
        },
        "detailed_results": results,
        "recommendation": "✅ Ready for production" if successful >= 2 else "⚠️ Needs attention",
        "system_info": {
            "modular_available": hasattr(enhanced_agent, 'modular_available'),
            "expected_modular_companies": ["company-a"],
            "expected_fallback_companies": ["company-b", "company-c"]
        }
    }

# =============================================================================
# ENHANCED ENDPOINTS (FROM ORIGINAL)
# =============================================================================

@app.post("/enhanced-rag-query-streaming")
async def enhanced_rag_query_streaming(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """🔄 Streaming endpoint (ใช้ original agent streaming)"""
    
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    async def generate_streaming_response():
        try:
            config = ENHANCED_TENANT_CONFIGS[tenant_id]
            
            # 📊 Send initial metadata
            metadata = {
                "type": "metadata",
                "tenant_id": tenant_id,
                "tenant_name": config["name"],
                "model": config["model"],
                "status": "started",
                "system_type": "streaming"
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # 🔥 Process question with streaming
            if hasattr(enhanced_agent, 'process_enhanced_question_streaming'):
                async for chunk in enhanced_agent.process_enhanced_question_streaming(request.query, tenant_id):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)
            else:
                # Fallback for non-streaming agent
                result = await enhanced_agent.process_enhanced_question(request.query, tenant_id)
                yield f"data: {json.dumps({'type': 'answer', 'content': result['answer']})}\n\n"
                
        except Exception as e:
            error_data = {"type": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/tenants/enhanced")
async def list_enhanced_tenants():
    """List all tenants with enhanced capabilities information"""
    tenants = []
    
    for tid, config in ENHANCED_TENANT_CONFIGS.items():
        # Determine system type
        modular_available = hasattr(enhanced_agent, 'modular_available') and enhanced_agent.modular_available
        system_type = "modular_prompts" if (modular_available and tid == 'company-a') else "original_enhanced"
        prompt_type = "EnterprisePrompt" if (modular_available and tid == 'company-a') else "UniversalPrompt"
        
        tenants.append({
            "tenant_id": tid,
            "name": config["name"],
            "model": config["model"],
            "language": config["language"],
            "business_type": config["business_type"],
            "description": config["description"],
            "specialization": config["specialization"],
            "key_strengths": config["key_strengths"],
            "system_type": system_type,
            "prompt_type": prompt_type,
            "enhanced_capabilities": [
                "smart_sql_with_business_logic",
                "pattern_recognition_queries", 
                "automated_business_insights",
                "context_aware_responses",
                "domain_specific_optimization"
            ]
        })
    
    return {
        "tenants": tenants,
        "global_enhancements": {
            "sql_generation": "AI + Pattern Matching + Business Logic",
            "response_quality": "Structured business analysis with insights",
            "modular_support": "Company-specific prompts with gradual migration"
        }
    }

# =============================================================================
# LEGACY COMPATIBILITY ENDPOINTS
# =============================================================================

@app.post("/rag-query", response_model=EnhancedRAGResponse)
async def legacy_rag_query(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Legacy RAG endpoint with enhanced backend (backward compatibility)"""
    return await enhanced_rag_query(request, tenant_id)

@app.post("/smart-sql-query", response_model=EnhancedRAGResponse)
async def legacy_smart_sql_query(
    request: EnhancedRAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Legacy smart SQL endpoint with enhanced backend"""
    return await enhanced_rag_query(request, tenant_id)

# =============================================================================
# OPENAI COMPATIBILITY
# =============================================================================

@app.post("/v1/chat/completions")
async def openai_chat_completions(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """OpenAI-compatible endpoint"""
    try:
        messages = request.get("messages", [])
        stream = request.get("stream", False)
        
        if not messages:
            raise HTTPException(400, "No messages provided")
        
        user_message = messages[-1].get("content", "")
        
        if stream:
            # Handle streaming
            async def generate_openai_streaming():
                try:
                    config = ENHANCED_TENANT_CONFIGS[tenant_id]
                    
                    initial_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": f"siamtech-modular-{config['model']}",
                        "choices": [{
                            "index": 0,
                            "delta": {"role": "assistant", "content": ""},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(initial_chunk)}\n\n"
                    
                    # Process with modular agent
                    result = await enhanced_agent.process_enhanced_question(user_message, tenant_id)
                    
                    response_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": f"siamtech-modular-{config['model']}",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": result.get('answer', '')},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(response_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    error_chunk = {
                        "error": {"message": str(e), "type": "internal_error"}
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return StreamingResponse(
                generate_openai_streaming(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            result = await enhanced_agent.process_enhanced_question(user_message, tenant_id)
            config = ENHANCED_TENANT_CONFIGS[tenant_id]
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": f"siamtech-modular-{config['model']}",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant", 
                        "content": result.get("answer", "")
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(result.get("answer", "").split()),
                    "total_tokens": len(user_message.split()) + len(result.get("answer", "").split())
                }
            }
            
    except Exception as e:
        raise HTTPException(500, f"Chat completions failed: {str(e)}")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    print("🔧 DEBUG: About to start uvicorn...")
    print(f"🎯 Enhanced agent type: {type(enhanced_agent)}")
    print(f"🏨 Tourism available: {hasattr(enhanced_agent, 'modular_available')}")
    
    # เพิ่มบรรทัดนี้
    import time
    time.sleep(2)
    print("🚀 Starting uvicorn now...")
    
    uvicorn.run(
        "enhanced_multi_agent_service:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True,
        log_level="info"
    )
    
