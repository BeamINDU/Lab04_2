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

# Import existing configs (ใช้ ENHANCED_TENANT_CONFIGS เดิม)
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

# FastAPI App Setup
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

# Dependencies
def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")) -> str:
    """Extract and validate tenant ID"""
    tenant_id = x_tenant_id or "company-a"
    if tenant_id not in ENHANCED_TENANT_CONFIGS:
        raise HTTPException(400, f"Invalid tenant: {tenant_id}")
    return tenant_id

# Main Endpoints
@app.post("/enhanced-rag-query")
async def enhanced_rag_query(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """🎯 Main query endpoint with modular prompt support"""
    
    question = request.get('query') or request.get('question')
    if not question:
        raise HTTPException(400, "No query provided")
    
    try:
        result = await enhanced_agent.process_enhanced_question(question, tenant_id)
        return result
    except Exception as e:
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
        pass
    
    # ตรวจสอบ original enhanced agent capabilities
    original_features = []
    try:
        if hasattr(enhanced_agent, 'universal_integration'):
            original_features.append("universal_prompt_system")
        if hasattr(enhanced_agent, 'schema_service'):
            original_features.append("schema_discovery")
        if hasattr(enhanced_agent, 'business_mapper'):
            original_features.append("business_logic_mapping")
    except:
        pass
    
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
            "architecture": "hybrid_modular_enhanced"
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

# Legacy endpoints compatibility
@app.post("/enhanced-rag-query-streaming")
async def enhanced_rag_query_streaming(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """🔄 Streaming endpoint (ใช้ original agent)"""
    
    question = request.get('query') or request.get('question')
    if not question:
        raise HTTPException(400, "No query provided")
    
    async def generate_streaming_response():
        try:
            async for chunk in enhanced_agent.process_enhanced_question_streaming(question, tenant_id):
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.01)
        except Exception as e:
            error_data = {"type": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

if __name__ == "__main__":
    modular_status = "✅ Available" if hasattr(enhanced_agent, 'modular_available') and enhanced_agent.modular_available else "❌ Not Available"
    
    print("🚀 SiamTech Modular Multi-Tenant RAG Service v4.0")
    print("=" * 80)
    print("🎯 Modular Features:")
    print("   • Company-specific prompt isolation")
    print("   • Hybrid modular + original system")
    print("   • Gradual migration support")
    print("   • Automatic fallback mechanism")
    print(f"   • Modular System: {modular_status}")
    print("")
    print("🧠 Enhanced Features:")
    print("   • Smart SQL Generation with Pattern Matching")
    print("   • Business Intelligence & Automated Insights")
    print("   • Enhanced Prompt Engineering")
    print("   • Advanced Error Recovery & Fallback")
    print("")
    print(f"📊 Companies: {list(ENHANCED_TENANT_CONFIGS.keys())}")
    
    if hasattr(enhanced_agent, 'modular_available') and enhanced_agent.modular_available:
        print("🎭 Company A: Modular prompts (EnterprisePrompt)")
        print("🔄 Company B,C: Original enhanced agent (UniversalPrompt)")
    else:
        print("🔄 All Companies: Original enhanced agent (UniversalPrompt)")
        
    print(f"🤖 Ollama Server: {os.getenv('OLLAMA_BASE_URL', 'http://52.74.36.160:12434')}")
    print("=" * 80)
    
    uvicorn.run(
        "enhanced_multi_agent_service:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True,
        log_level="info"
    )