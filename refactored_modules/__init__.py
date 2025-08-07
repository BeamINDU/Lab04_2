# __init__.py
# 📦 Package initialization for Enhanced PostgreSQL Agent

"""
Enhanced PostgreSQL + Ollama Agent
====================================

A refactored, clean architecture implementation of the multi-tenant AI agent.

Main Components:
- TenantConfigManager: Handles multi-tenant configurations
- DatabaseHandler: Manages all database operations
- SchemaDiscoveryService: Provides database schema information
- BusinessLogicMapper: Maps business concepts to SQL logic
- AIService: Handles AI/Ollama communications
- PromptGenerator: Creates enhanced prompts for AI
- IntentClassifier: Classifies user intent
- EnhancedPostgresOllamaAgent: Main agent orchestrator
"""

from .tenant_config import TenantConfigManager, TenantConfig
from .database_handler import DatabaseHandler
from .schema_discovery import SchemaDiscoveryService
from .business_logic_mapper import BusinessLogicMapper
from .ai_service import AIService
from .prompt_generator import PromptGenerator
from .intent_classifier import IntentClassifier
from .enhanced_postgres_agent_refactored import EnhancedPostgresOllamaAgent
from .universal_prompt_system import (
    UniversalPromptGenerator,
    UniversalPromptIntegration, 
    EnhancedAgentWithUniversalPrompt,
    UniversalPromptMigrationGuide,
    CompanyContext,
    TypeSafetySQLValidator
)

__version__ = "2.1.0"
__author__ = "SiamTech Development Team"
__description__ = "Enhanced multi-tenant PostgreSQL + Ollama AI Agent with clean architecture"

# Export main classes
__all__ = [
    'TenantConfigManager',
    'TenantConfig', 
    'DatabaseHandler',
    'SchemaDiscoveryService',
    'BusinessLogicMapper',
    'AIService',
    'PromptGenerator',
    'IntentClassifier',
    'EnhancedPostgresOllamaAgent'
    'UniversalPromptGenerator',
    'UniversalPromptIntegration',
    'EnhancedAgentWithUniversalPrompt',
    'UniversalPromptMigrationGuide',
    'CompanyContext',
    'TypeSafetySQLValidator'
]