import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import the enhanced PostgreSQL + Ollama agent
from ollama_postgres_agent import PostgresOllamaAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RAGQuery(BaseModel):
    query: str
    tenant_id: Optional[str] = None
    agent_type: Optional[str] = "smart_sql"  # "smart_sql", "ai_only"
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7

class RAGResponse(BaseModel):
    answer: str
    success: bool
    tenant_id: str
    tenant_name: str
    model_used: Optional[str] = None
    data_source_used: Optional[str] = None
    agent_type: Optional[str] = None
    response_time_ms: int
    sql_query: Optional[str] = None
    db_results_count: Optional[int] = None
    ai_generated_sql: Optional[bool] = None
    fallback_mode: Optional[bool] = None

# =============================================================================
# TENANT CONFIGURATION
# =============================================================================

TENANT_CONFIGS = {
    'company-a': {
        'name': 'SiamTech Bangkok HQ',
        'model': 'llama3.1:8b',
        'language': 'th',
        'description': 'สำนักงานใหญ่ กรุงเทพมฯ - Enterprise solutions, Banking, E-commerce'
    },
    'company-b': {
        'name': 'SiamTech Chiang Mai Regional',
        'model': 'gemma2:9b',
        'language': 'th',
        'description': 'สาขาภาคเหนือ เชียงใหม่ - Tourism technology, Hospitality'
    },
    'company-c': {
        'name': 'SiamTech International',
        'model': 'phi3:14b',
        'language': 'en',
        'description': 'International Operations - Global projects, Cross-border solutions'
    }
}

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="SiamTech Enhanced Multi-Tenant RAG Service",
    description="Advanced RAG service with AI-generated SQL queries and smart routing",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global enhanced agent (singleton)
enhanced_agent = PostgresOllamaAgent()

# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")) -> str:
    """Extract and validate tenant ID"""
    tenant_id = x_tenant_id or "company-a"
    if tenant_id not in TENANT_CONFIGS:
        raise HTTPException(400, f"Invalid tenant: {tenant_id}")
    return tenant_id

def validate_tenant_id(tenant_id: str) -> bool:
    """Validate if tenant ID exists"""
    return tenant_id in TENANT_CONFIGS

# =============================================================================
# CORE ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "service": "SiamTech Enhanced Multi-Tenant RAG",
        "version": "5.0.0",
        "features": [
            "ai_generated_sql", 
            "multi_tenant", 
            "smart_routing", 
            "schema_aware",
            "business_context",
            "fallback_mechanism"
        ],
        "tenants": list(TENANT_CONFIGS.keys()),
        "ollama_server": os.getenv('OLLAMA_BASE_URL', 'http://192.168.11.97:12434'),
        "agent_type": "PostgresOllamaAgent",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tenants")
async def list_tenants():
    """List all available tenants with enhanced info"""
    return {
        "tenants": [
            {
                "tenant_id": tid,
                "name": config["name"],
                "model": config["model"],
                "language": config["language"],
                "description": config["description"],
                "capabilities": [
                    "smart_sql_generation", 
                    "database_query", 
                    "ai_interpretation",
                    "schema_awareness",
                    "business_context"
                ]
            }
            for tid, config in TENANT_CONFIGS.items()
        ]
    }

@app.post("/smart-sql-query", response_model=RAGResponse)
async def smart_sql_query(
    request: RAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Enhanced Smart SQL query endpoint - AI generates SQL automatically"""
    start_time = time.time()
    
    # Override tenant if provided in request
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    try:
        logger.info(f"Processing smart SQL query for {tenant_id}: {request.query[:100]}...")
        
        # Process with Enhanced PostgreSQL + Ollama agent
        result = await enhanced_agent.process_question(
            question=request.query,
            tenant_id=tenant_id
        )
        
        response_time = int((time.time() - start_time) * 1000)
        tenant_config = TENANT_CONFIGS[tenant_id]
        
        return RAGResponse(
            answer=result["answer"],
            success=result.get("success", True),
            tenant_id=tenant_id,
            tenant_name=tenant_config["name"],
            model_used=result.get("model_used", tenant_config["model"]),
            data_source_used=result.get("data_source_used"),
            agent_type="smart_sql",
            response_time_ms=response_time,
            sql_query=result.get("sql_query"),
            db_results_count=result.get("db_results_count"),
            ai_generated_sql=result.get("ai_generated_sql", True),
            fallback_mode=result.get("fallback_mode", False)
        )
        
    except Exception as e:
        logger.error(f"Error in smart_sql_query for {tenant_id}: {e}")
        response_time = int((time.time() - start_time) * 1000)
        
        return RAGResponse(
            answer=f"เกิดข้อผิดพลาด: {str(e)}",
            success=False,
            tenant_id=tenant_id,
            tenant_name=TENANT_CONFIGS[tenant_id]["name"],
            agent_type="error",
            response_time_ms=response_time
        )

@app.post("/ai-only-query", response_model=RAGResponse)
async def ai_only_query(
    request: RAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """AI-only query endpoint (no database access)"""
    start_time = time.time()
    
    # Override tenant if provided in request
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    try:
        logger.info(f"Processing AI-only query for {tenant_id}: {request.query[:100]}...")
        
        # Call AI directly without database context
        ai_response = await enhanced_agent.call_ollama_api(
            tenant_id=tenant_id,
            prompt=request.query,
            context_data="",
            temperature=request.temperature or 0.7
        )
        
        response_time = int((time.time() - start_time) * 1000)
        tenant_config = TENANT_CONFIGS[tenant_id]
        
        return RAGResponse(
            answer=ai_response,
            success=True,
            tenant_id=tenant_id,
            tenant_name=tenant_config["name"],
            model_used=tenant_config["model"],
            data_source_used=f"ai_only_{tenant_config['model']}",
            agent_type="ai_only",
            response_time_ms=response_time,
            fallback_mode=False
        )
        
    except Exception as e:
        logger.error(f"Error in ai_only_query for {tenant_id}: {e}")
        response_time = int((time.time() - start_time) * 1000)
        
        return RAGResponse(
            answer=f"เกิดข้อผิดพลาด: {str(e)}",
            success=False,
            tenant_id=tenant_id,
            tenant_name=TENANT_CONFIGS[tenant_id]["name"],
            agent_type="error",
            response_time_ms=response_time
        )

@app.post("/rag-query", response_model=RAGResponse)
async def unified_rag_query(
    request: RAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Unified RAG endpoint with smart routing"""
    start_time = time.time()
    
    # Override tenant if provided in request
    if request.tenant_id and validate_tenant_id(request.tenant_id):
        tenant_id = request.tenant_id
    
    try:
        logger.info(f"Processing unified RAG query for {tenant_id}: {request.query[:100]}...")
        
        # Determine agent type
        agent_type = request.agent_type or "smart_sql"
        
        if agent_type == "ai_only":
            # AI-only mode (no database)
            ai_response = await enhanced_agent.call_ollama_api(
                tenant_id=tenant_id,
                prompt=request.query,
                context_data="",
                temperature=request.temperature or 0.7
            )
            
            response_time = int((time.time() - start_time) * 1000)
            tenant_config = TENANT_CONFIGS[tenant_id]
            
            return RAGResponse(
                answer=ai_response,
                success=True,
                tenant_id=tenant_id,
                tenant_name=tenant_config["name"],
                model_used=tenant_config["model"],
                data_source_used=f"ai_only_{tenant_config['model']}",
                agent_type="ai_only",
                response_time_ms=response_time
            )
        else:
            # Smart SQL mode (default) - uses enhanced agent
            result = await enhanced_agent.process_question(
                question=request.query,
                tenant_id=tenant_id
            )
            
            response_time = int((time.time() - start_time) * 1000)
            tenant_config = TENANT_CONFIGS[tenant_id]
            
            return RAGResponse(
                answer=result["answer"],
                success=result.get("success", True),
                tenant_id=tenant_id,
                tenant_name=tenant_config["name"],
                model_used=result.get("model_used", tenant_config["model"]),
                data_source_used=result.get("data_source_used"),
                agent_type="smart_sql",
                response_time_ms=response_time,
                sql_query=result.get("sql_query"),
                db_results_count=result.get("db_results_count"),
                ai_generated_sql=result.get("ai_generated_sql", True),
                fallback_mode=result.get("fallback_mode", False)
            )
        
    except Exception as e:
        logger.error(f"Error in unified_rag_query for {tenant_id}: {e}")
        response_time = int((time.time() - start_time) * 1000)
        
        return RAGResponse(
            answer=f"เกิดข้อผิดพลาด: {str(e)}",
            success=False,
            tenant_id=tenant_id,
            tenant_name=TENANT_CONFIGS[tenant_id]["name"],
            agent_type="error",
            response_time_ms=response_time
        )

# Legacy endpoints for compatibility
@app.post("/postgres-query", response_model=RAGResponse)
async def postgres_query(
    request: RAGQuery,
    tenant_id: str = Depends(get_tenant_id)
):
    """Legacy PostgreSQL query endpoint - now uses enhanced smart SQL"""
    return await smart_sql_query(request, tenant_id)

# =============================================================================
# OPENAI COMPATIBILITY ENDPOINTS
# =============================================================================

@app.post("/v1/chat/completions")
async def openai_chat_completions(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """OpenAI-compatible chat completions endpoint"""
    try:
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(400, "No messages provided")
        
        # Extract the last user message
        user_message = messages[-1].get("content", "")
        
        # Process with Enhanced PostgreSQL + Ollama agent
        result = await enhanced_agent.process_question(
            question=user_message,
            tenant_id=tenant_id
        )
        
        # Format as OpenAI response
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": TENANT_CONFIGS[tenant_id]["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["answer"]
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(result["answer"].split()),
                "total_tokens": len(user_message.split()) + len(result["answer"].split())
            },
            "system_fingerprint": f"siamtech-enhanced-{tenant_id}",
            "siamtech_metadata": {
                "tenant_id": tenant_id,
                "tenant_name": TENANT_CONFIGS[tenant_id]["name"],
                "data_source": result.get("data_source_used"),
                "sql_query": result.get("sql_query"),
                "db_results_count": result.get("db_results_count"),
                "ai_generated_sql": result.get("ai_generated_sql", True),
                "fallback_mode": result.get("fallback_mode", False),
                "agent_version": "5.0.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in chat completions for {tenant_id}: {e}")
        raise HTTPException(500, f"Internal server error: {str(e)}")

@app.get("/v1/models")
async def openai_models():
    """OpenAI-compatible models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": f"siamtech-enhanced-{tenant_id}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "siamtech",
                "permission": [],
                "root": config["model"],
                "parent": None,
                "siamtech_metadata": {
                    "tenant_id": tenant_id,
                    "tenant_name": config["name"],
                    "base_model": config["model"],
                    "language": config["language"],
                    "capabilities": [
                        "smart_sql_generation", 
                        "database_query", 
                        "ai_interpretation",
                        "schema_awareness",
                        "business_context",
                        "fallback_mechanism"
                    ],
                    "agent_version": "5.0.0"
                }
            }
            for tenant_id, config in TENANT_CONFIGS.items()
        ]
    }

# =============================================================================
# MONITORING & ADMIN ENDPOINTS
# =============================================================================

@app.get("/tenants/{tenant_id}/status")
async def tenant_status(tenant_id: str):
    """Get detailed status for specific tenant"""
    if not validate_tenant_id(tenant_id):
        raise HTTPException(404, f"Tenant {tenant_id} not found")
    
    try:
        # Test database connection
        db_connection = enhanced_agent.get_database_connection(tenant_id)
        db_status = "connected"
        db_connection.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test AI connection
    try:
        ai_response = await enhanced_agent.call_ollama_api(
            tenant_id=tenant_id,
            prompt="test connection",
            context_data="",
            temperature=0.1
        )
        ai_status = "connected" if ai_response and "error" not in ai_response.lower() else "error"
    except Exception as e:
        ai_status = f"error: {str(e)}"
    
    tenant_config = TENANT_CONFIGS[tenant_id]
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant_config["name"],
        "model": tenant_config["model"],
        "language": tenant_config["language"],
        "description": tenant_config["description"],
        "database_status": db_status,
        "ai_status": ai_status,
        "ollama_server": os.getenv('OLLAMA_BASE_URL', 'http://192.168.11.97:12434'),
        "features": [
            "smart_sql_generation", 
            "ai_interpretation", 
            "multi_tenant",
            "schema_awareness",
            "business_context",
            "fallback_mechanism"
        ],
        "agent_version": "5.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/database-schema/{tenant_id}")
async def get_database_schema(tenant_id: str):
    """Get database schema information for specific tenant"""
    if not validate_tenant_id(tenant_id):
        raise HTTPException(404, f"Tenant {tenant_id} not found")
    
    # Get database schema info from enhanced agent
    schema_info = enhanced_agent.database_schemas.get(tenant_id, {})
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": TENANT_CONFIGS[tenant_id]["name"],
        "database_description": schema_info.get("description", ""),
        "business_context": schema_info.get("business_context", ""),
        "tables": schema_info.get("tables", {}),
        "example_questions": {
            "th": [
                "มีพนักงานกี่คนในแต่ละแผนก",
                "พนักงานคนไหนมีเงินเดือนสูงสุด 5 คน",
                "โปรเจคที่กำลังทำอยู่มีอะไรบ้าง",
                "แผนกไหนมีคนมากที่สุด",
                "โปรเจคที่มีงบประมาณสูงกว่า 2 ล้านบาท",
                "พนักงานที่ทำงานในโปรเจคงบประมาณสูง"
            ],
            "en": [
                "How many employees are in each department?",
                "Who are the top 5 highest paid employees?",
                "What projects are currently active?",
                "Which department has the most employees?",
                "Which projects have budget over 2 million?",
                "Which employees work on high budget projects?"
            ]
        }
    }

@app.get("/test-sql-generation/{tenant_id}")
async def test_sql_generation(tenant_id: str, question: str):
    """Test SQL generation for debugging"""
    if not validate_tenant_id(tenant_id):
        raise HTTPException(404, f"Tenant {tenant_id} not found")
    
    try:
        # Generate SQL without executing
        sql_query = await enhanced_agent.generate_sql_with_ai(question, tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "question": question,
            "generated_sql": sql_query,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"SQL generation failed: {str(e)}")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    print("🚀 SiamTech Enhanced Multi-Tenant RAG Service v5.0")
    print("=" * 70)
    print(f"🧠 Features: AI-Generated SQL + Schema Awareness + Business Context")
    print(f"📊 Tenants: {list(TENANT_CONFIGS.keys())}")
    print(f"🤖 Ollama Server: {os.getenv('OLLAMA_BASE_URL', 'http://192.168.11.97:12434')}")
    print(f"🗄️  Database: Multi-tenant PostgreSQL with Enhanced Smart SQL")
    print(f"🎯 Agent: PostgresOllamaAgent v5.0 (Enhanced)")
    print("=" * 70)
    
    uvicorn.run(
        "enhanced_multi_agent_service:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True,
        log_level="info"
    )