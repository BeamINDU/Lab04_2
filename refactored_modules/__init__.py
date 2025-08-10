from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .ai_service import AIService
from .enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent


__version__ = "2.1.0"
__author__ = "SiamTech Development Team"
__description__ = "Enhanced multi-tenant PostgreSQL + Ollama AI Agent with clean architecture"

# Export main classes
__all__ = [
    'TenantConfigManager',
    'TenantConfig', 
    'DatabaseHandler',
    'AIService',
    'EnhancedPostgresOllamaAgent'
]