"""
🏗️ Enterprise Schema Validator - FIXED VERSION
====================================================================

Fixed Issues:
1. SQL query tuple index errors
2. Better error handling for schema discovery
3. Fallback schema when discovery fails
4. More robust database introspection
"""

import os
import json
import asyncio
import aiohttp
import psycopg2
from typing import Dict, Any, Optional, List, Tuple, Set
import logging
from dataclasses import dataclass
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseSchema:
    """Auto-discovered database schema"""
    tables: Dict[str, List[str]]  # table_name -> [column_names]
    table_types: Dict[str, Dict[str, str]]  # table -> column -> data_type
    table_descriptions: Dict[str, str]  # business context
    primary_keys: Dict[str, str]  # table -> primary_key_column
    foreign_keys: Dict[str, List[str]]  # table -> [foreign_key_columns]

class SchemaDiscoveryService:
    """🔍 Auto-discover database schema instead of hard-coding - FIXED"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.tenant_configs = tenant_configs
        self.discovered_schemas: Dict[str, DatabaseSchema] = {}
        
    async def discover_all_schemas(self) -> Dict[str, DatabaseSchema]:
        """Discover schemas for all tenants automatically"""
        for tenant_id in self.tenant_configs.keys():
            try:
                schema = await self.discover_tenant_schema(tenant_id)
                self.discovered_schemas[tenant_id] = schema
                logger.info(f"✅ Schema discovered for {tenant_id}: {len(schema.tables)} tables")
            except Exception as e:
                logger.error(f"❌ Schema discovery failed for {tenant_id}: {e}")
                # Create fallback schema
                fallback_schema = self._create_fallback_schema(tenant_id)
                self.discovered_schemas[tenant_id] = fallback_schema
                logger.info(f"⚠️ Using fallback schema for {tenant_id}")
        
        return self.discovered_schemas
    
    async def discover_tenant_schema(self, tenant_id: str) -> DatabaseSchema:
        """🔍 Auto-discover schema from actual database - FIXED VERSION"""
        config = self.tenant_configs[tenant_id]
        
        conn = None
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password
            )
            cursor = conn.cursor()
            
            # 1. Discover all tables - FIXED QUERY
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            table_results = cursor.fetchall()
            tables = [row[0] for row in table_results] if table_results else []
            
            # 2. Discover columns for each table
            table_columns = {}
            table_types = {}
            
            for table in tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                column_results = cursor.fetchall()
                
                columns = []
                column_types = {}
                
                for row in column_results:
                    if len(row) >= 3:  # Safety check
                        col_name, data_type, is_nullable = row[0], row[1], row[2]
                        columns.append(col_name)
                        column_types[col_name] = {
                            'type': data_type,
                            'nullable': is_nullable == 'YES'
                        }
                
                table_columns[table] = columns
                table_types[table] = column_types
            
            # 3. Discover primary keys - SIMPLIFIED
            primary_keys = {}
            for table in tables:
                try:
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.key_column_usage
                        WHERE table_schema = 'public'
                        AND table_name = %s
                        AND constraint_name LIKE '%_pkey'
                        LIMIT 1;
                    """, (table,))
                    
                    pk_result = cursor.fetchone()
                    if pk_result and len(pk_result) > 0:
                        primary_keys[table] = pk_result[0]
                    else:
                        # Fallback: assume 'id' is primary key
                        if 'id' in table_columns.get(table, []):
                            primary_keys[table] = 'id'
                except Exception as e:
                    # Fallback for primary key discovery
                    if 'id' in table_columns.get(table, []):
                        primary_keys[table] = 'id'
                    logger.warning(f"PK discovery failed for {table}: {e}")
            
            # 4. Discover foreign keys - SIMPLIFIED
            foreign_keys = {}
            for table in tables:
                try:
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.key_column_usage
                        WHERE table_schema = 'public'
                        AND table_name = %s
                        AND constraint_name LIKE '%_fkey';
                    """, (table,))
                    
                    fk_results = cursor.fetchall()
                    fk_columns = [row[0] for row in fk_results if len(row) > 0]
                    
                    if fk_columns:
                        foreign_keys[table] = fk_columns
                except Exception as e:
                    logger.warning(f"FK discovery failed for {table}: {e}")
                    # Continue without foreign keys for this table
            
            # 5. Add business context based on discovered schema
            table_descriptions = self._generate_business_context(table_columns, tenant_id)
            
            logger.info(f"✅ Schema discovered for {tenant_id}: {len(tables)} tables, {sum(len(cols) for cols in table_columns.values())} columns")
            
            return DatabaseSchema(
                tables=table_columns,
                table_types=table_types,
                table_descriptions=table_descriptions,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys
            )
            
        except Exception as e:
            logger.error(f"❌ Schema discovery failed for {tenant_id}: {e}")
            # 🚨 FALLBACK: Return minimal known schema
            return self._create_fallback_schema(tenant_id)
            
        finally:
            if conn:
                conn.close()
    
    def _create_fallback_schema(self, tenant_id: str) -> DatabaseSchema:
        """🛡️ Create fallback schema when discovery fails"""
        
        # Known basic schema for all companies
        fallback_tables = {
            'employees': ['id', 'name', 'department', 'position', 'salary', 'hire_date', 'email'],
            'projects': ['id', 'name', 'client', 'budget', 'status', 'start_date', 'end_date', 'tech_stack'],
            'employee_projects': ['employee_id', 'project_id', 'role', 'allocation']
        }
        
        fallback_types = {}
        for table, columns in fallback_tables.items():
            fallback_types[table] = {}
            for col in columns:
                if col == 'id' or col.endswith('_id'):
                    fallback_types[table][col] = {'type': 'integer', 'nullable': False}
                elif col in ['salary', 'budget', 'allocation']:
                    fallback_types[table][col] = {'type': 'numeric', 'nullable': True}
                elif col.endswith('_date'):
                    fallback_types[table][col] = {'type': 'date', 'nullable': True}
                else:
                    fallback_types[table][col] = {'type': 'character varying', 'nullable': True}
        
        fallback_primary_keys = {
            'employees': 'id',
            'projects': 'id'
        }
        
        fallback_foreign_keys = {
            'employee_projects': ['employee_id', 'project_id']
        }
        
        fallback_descriptions = {
            'employees': f'Employee data for {tenant_id} (fallback schema)',
            'projects': f'Project data for {tenant_id} (fallback schema)', 
            'employee_projects': f'Employee-project relationships for {tenant_id} (fallback schema)'
        }
        
        logger.warning(f"⚠️ Using fallback schema for {tenant_id}")
        
        return DatabaseSchema(
            tables=fallback_tables,
            table_types=fallback_types,
            table_descriptions=fallback_descriptions,
            primary_keys=fallback_primary_keys,
            foreign_keys=fallback_foreign_keys
        )
    
    def _generate_business_context(self, tables: Dict[str, List[str]], tenant_id: str) -> Dict[str, str]:
        """Generate business context based on discovered tables"""
        context = {}
        
        for table_name, columns in tables.items():
            if table_name == 'employees':
                context[table_name] = f"Employee information with {len(columns)} attributes"
            elif table_name == 'projects':
                context[table_name] = f"Project data with {len(columns)} fields"
            elif table_name == 'employee_projects':
                context[table_name] = "Employee-project assignment relationships"
            elif 'client' in table_name:
                context[table_name] = f"Client information with {len(columns)} fields"
            elif 'department' in table_name:
                context[table_name] = f"Department data with {len(columns)} attributes"
            else:
                context[table_name] = f"Business data table with {len(columns)} columns"
        
        return context

class IntelligentQueryValidator:
    """🧠 Smart query validator using discovered schema - FIXED"""
    
    def __init__(self, schema_service: SchemaDiscoveryService):
        self.schema_service = schema_service
        self.schemas = schema_service.discovered_schemas
    
    def validate_query_intent(self, question: str, tenant_id: str) -> Tuple[bool, str, List[str]]:
        """🔍 Validate if question can be answered with available schema"""
        
        if tenant_id not in self.schemas:
            return False, "Schema not discovered for tenant", []
        
        schema = self.schemas[tenant_id]
        question_lower = question.lower()
        
        # 1. Extract potential data concepts from question
        requested_concepts = self._extract_data_concepts(question_lower)
        
        # 2. Check if concepts exist in actual schema
        available_concepts = self._get_available_concepts(schema)
        
        # 3. Find mismatches
        missing_concepts = []
        suggested_alternatives = []
        
        for concept in requested_concepts:
            if not self._concept_exists_in_schema(concept, available_concepts):
                missing_concepts.append(concept)
                # Find closest match
                alternative = self._find_closest_concept(concept, available_concepts)
                if alternative:
                    suggested_alternatives.append(alternative)
        
        if missing_concepts:
            suggestion_text = self._generate_helpful_response(
                missing_concepts, suggested_alternatives, schema, tenant_id
            )
            return False, suggestion_text, missing_concepts
        
        return True, "Query can be answered with available data", []
    
    def _extract_data_concepts(self, question: str) -> List[str]:
        """Extract data concepts from natural language question"""
        
        # Common business data concepts mapping
        concept_patterns = {
            # Financial concepts
            'sales': ['sales', 'ยอดขาย', 'การขาย', 'เซลล์'],
            'revenue': ['revenue', 'รายได้', 'ผลตอบแทน', 'income'],
            'profit': ['profit', 'กำไร', 'ผลกำไร', 'margin'],
            'cost': ['cost', 'ต้นทุน', 'ค่าใช้จ่าย', 'expense'],
            
            # Personal data concepts
            'gender': ['gender', 'เพศ', 'ชาย', 'หญิง', 'male', 'female'],
            'age': ['age', 'อายุ', 'วัย', 'ปีเกิด', 'birth'],
            'address': ['address', 'ที่อยู่', 'บ้าน', 'location'],
            'phone': ['phone', 'โทรศัพท์', 'เบอร์', 'contact'],
            
            # Time-based aggregations (if not supported)
            'monthly': ['monthly', 'รายเดือน', 'เป็นรายเดือน', 'ต่อเดือน'],
            'daily': ['daily', 'รายวัน', 'เป็นรายวัน', 'ต่อวัน'],
            'quarterly': ['quarterly', 'รายไตรมาส', 'ต่อไตรมาส'],
            
            # Inventory/Product (if not in our business model)
            'inventory': ['inventory', 'สต็อก', 'สินค้า', 'product'],
            'customer': ['customer', 'ลูกค้า', 'คลื่น', 'client'] # Note: we have 'client' but maybe not 'customer'
        }
        
        detected_concepts = []
        for concept, patterns in concept_patterns.items():
            if any(pattern in question for pattern in patterns):
                detected_concepts.append(concept)
        
        return detected_concepts
    
    def _get_available_concepts(self, schema: DatabaseSchema) -> Set[str]:
        """Get all available data concepts from schema"""
        concepts = set()
        
        # Add table names as concepts
        for table_name in schema.tables.keys():
            concepts.add(table_name)
            
            # Add column names as concepts
            for column in schema.tables[table_name]:
                concepts.add(column)
                
                # Map column names to business concepts
                if 'salary' in column.lower():
                    concepts.add('salary')
                    concepts.add('pay')
                    concepts.add('compensation')
                elif 'budget' in column.lower():
                    concepts.add('budget')
                    concepts.add('cost')
                    concepts.add('funding')
                elif 'name' in column.lower():
                    concepts.add('name')
                    concepts.add('title')
                elif 'department' in column.lower():
                    concepts.add('department')
                    concepts.add('division')
                    concepts.add('team')
        
        return concepts
    
    def _concept_exists_in_schema(self, concept: str, available_concepts: Set[str]) -> bool:
        """Check if a concept exists in the schema"""
        
        # Direct match
        if concept in available_concepts:
            return True
            
        # Fuzzy matching for related concepts
        concept_mappings = {
            'sales': ['budget', 'revenue'],  # We don't have sales, but budget might be close
            'revenue': ['budget', 'salary'],  # Budget/salary are closest to revenue
            'profit': ['budget'],
            'gender': [],  # No equivalent
            'age': [],     # No equivalent
            'monthly': ['date', 'hire_date', 'start_date'],  # We have dates but not monthly aggregation
        }
        
        if concept in concept_mappings:
            return any(alt in available_concepts for alt in concept_mappings[concept])
        
        return False
    
    def _find_closest_concept(self, missing_concept: str, available_concepts: Set[str]) -> Optional[str]:
        """Find the closest available concept to suggest"""
        
        suggestions = {
            'sales': 'project budget',
            'revenue': 'project budget or employee salary',
            'profit': 'project budget',
            'monthly': 'data by project or employee (no time aggregation)',
            'gender': 'employee department or position',
            'age': 'employee hire date',
            'customer': 'project client'
        }
        
        return suggestions.get(missing_concept)
    
    def _generate_helpful_response(self, missing_concepts: List[str], 
                                 suggested_alternatives: List[str],
                                 schema: DatabaseSchema, 
                                 tenant_id: str) -> str:
        """Generate helpful response explaining what data is available"""
        
        config = self.schema_service.tenant_configs[tenant_id]
        
        if config.language == 'th':
            response = f"ขออภัยครับ ไม่มีข้อมูล {', '.join(missing_concepts)} ในฐานข้อมูล\n\n"
            
            response += "📊 ข้อมูลที่มีจริงๆ:\n"
            for table_name, columns in schema.tables.items():
                response += f"• {table_name}: {', '.join(columns[:5])}"
                if len(columns) > 5:
                    response += f" และอีก {len(columns)-5} คอลัมน์"
                response += "\n"
            
            if suggested_alternatives:
                response += f"\n💡 ข้อมูลที่ใกล้เคียง: {', '.join(suggested_alternatives)}\n"
            
            response += "\n🔍 ลองถามเกี่ยวกับ:\n"
            for table in schema.tables.keys():
                response += f"• ข้อมูล {table}\n"
                
        else:  # English
            response = f"Sorry, we don't have {', '.join(missing_concepts)} data in our database.\n\n"
            
            response += "📊 Available data:\n"
            for table_name, columns in schema.tables.items():
                response += f"• {table_name}: {', '.join(columns[:5])}"
                if len(columns) > 5:
                    response += f" and {len(columns)-5} more columns"
                response += "\n"
            
            if suggested_alternatives:
                response += f"\n💡 Similar data available: {', '.join(suggested_alternatives)}\n"
            
            response += "\n🔍 Try asking about:\n"
            for table in schema.tables.keys():
                response += f"• {table} data\n"
        
        return response

class EnterpriseQueryValidator:
    """🏗️ Enterprise-grade query validator with auto-discovery - FIXED"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.schema_service = SchemaDiscoveryService(tenant_configs)
        self.query_validator = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize by discovering all schemas"""
        if not self._initialized:
            logger.info("🔍 Discovering database schemas...")
            await self.schema_service.discover_all_schemas()
            self.query_validator = IntelligentQueryValidator(self.schema_service)
            self._initialized = True
            logger.info("✅ Enterprise Query Validator initialized")
    
    async def validate_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """🎯 Main validation method - replaces all hard-coded checks"""
        
        if not self._initialized:
            await self.initialize()
        
        # Validate using discovered schema
        can_answer, response_text, missing_concepts = self.query_validator.validate_query_intent(
            question, tenant_id
        )
        
        if not can_answer:
            return {
                'can_answer': False,
                'response': response_text,
                'missing_concepts': missing_concepts,
                'validation_method': 'schema_discovery',
                'available_tables': list(self.schema_service.discovered_schemas[tenant_id].tables.keys()) if tenant_id in self.schema_service.discovered_schemas else []
            }
        
        return {
            'can_answer': True,
            'validation_method': 'schema_discovery',
            'available_tables': list(self.schema_service.discovered_schemas[tenant_id].tables.keys())
        }
    
    def get_safe_sql_context(self, tenant_id: str) -> str:
        """Generate SQL context from discovered schema"""
        if tenant_id not in self.schema_service.discovered_schemas:
            return "No schema available"
        
        schema = self.schema_service.discovered_schemas[tenant_id]
        
        context = "📋 EXACT DATABASE SCHEMA (AUTO-DISCOVERED):\n\n"
        
        for table_name, columns in schema.tables.items():
            context += f"🗃️ TABLE: {table_name}\n"
            context += f"   COLUMNS: {', '.join(columns)}\n"
            
            # Add data types if available
            if table_name in schema.table_types:
                type_info = []
                for col in columns[:3]:  # Show first 3 column types
                    if col in schema.table_types[table_name]:
                        col_type = schema.table_types[table_name][col]['type']
                        type_info.append(f"{col}({col_type})")
                if type_info:
                    context += f"   TYPES: {', '.join(type_info)}\n"
            
            context += f"   EXAMPLE: SELECT {', '.join(columns[:3])} FROM {table_name} LIMIT 5;\n\n"
        
        return context
    
    def get_schema_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive schema summary"""
        if tenant_id not in self.schema_service.discovered_schemas:
            return {'error': 'Schema not discovered'}
        
        schema = self.schema_service.discovered_schemas[tenant_id]
        
        return {
            'tenant_id': tenant_id,
            'total_tables': len(schema.tables),
            'tables': {
                table_name: {
                    'columns': columns,
                    'column_count': len(columns),
                    'primary_key': schema.primary_keys.get(table_name),
                    'foreign_keys': schema.foreign_keys.get(table_name, []),
                    'description': schema.table_descriptions.get(table_name, '')
                }
                for table_name, columns in schema.tables.items()
            },
            'discovery_method': 'postgresql_information_schema',
            'last_discovered': datetime.now().isoformat()
        }

# Integration Example for Enhanced Agent
class IntegratedEnhancedAgent:
    """🚀 Integration example showing how to use Enterprise Validator"""
    
    def __init__(self, tenant_configs: Dict[str, Any]):
        self.enterprise_validator = EnterpriseQueryValidator(tenant_configs)
        
    async def process_question_with_enterprise_validation(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Process question using enterprise-grade validation"""
        
        # 1. Initialize validator (auto-discovers schemas)
        await self.enterprise_validator.initialize()
        
        # 2. Validate question using discovered schema
        validation_result = await self.enterprise_validator.validate_question(question, tenant_id)
        
        if not validation_result['can_answer']:
            # Return helpful response based on actual schema
            return {
                'answer': validation_result['response'],
                'success': True,
                'data_source_used': 'enterprise_schema_validation',
                'validation_method': validation_result['validation_method'],
                'missing_concepts': validation_result['missing_concepts'],
                'available_tables': validation_result['available_tables'],
                'enterprise_grade': True
            }
        
        # 3. If validation passes, proceed with SQL generation using discovered schema
        sql_context = self.enterprise_validator.get_safe_sql_context(tenant_id)
        
        # Continue with normal processing...
        return {
            'answer': f"Processing with enterprise validation: {question}",
            'success': True,
            'sql_context_generated': True,
            'enterprise_grade': True,
            'available_tables': validation_result['available_tables']
        }

# Demo/Test Code
async def demo_enterprise_validator():
    """🎮 Demo the enterprise validator"""
    
    # Mock tenant configs (replace with real ones)
    tenant_configs = {
        'company-a': type('Config', (), {
            'db_host': 'localhost',
            'db_port': 5432,
            'db_name': 'siamtech_company_a',
            'db_user': 'postgres',
            'db_password': 'password123',
            'language': 'th'
        })(),
        'company-b': type('Config', (), {
            'db_host': 'localhost',
            'db_port': 5433,
            'db_name': 'siamtech_company_b',
            'db_user': 'postgres',
            'db_password': 'password123',
            'language': 'th'
        })()
    }
    
    print("🏗️ Enterprise Schema Validator Demo")
    print("=" * 50)
    
    validator = EnterpriseQueryValidator(tenant_configs)
    
    # Test questions
    test_questions = [
        ("company-a", "ต้องการรู้ยอดขายเป็นรายเดือน"),  # Should be rejected with helpful alternatives
        ("company-a", "มีพนักงานชายกี่คน หญิงกี่คน"),     # Should be rejected
        ("company-a", "มีพนักงานกี่คนในแต่ละแผนก"),       # Should pass
        ("company-b", "โปรเจคไหนมีงบประมาณสูงสุด"),      # Should pass
    ]
    
    for tenant_id, question in test_questions:
        print(f"\n❓ Testing: {question}")
        print("-" * 40)
        
        try:
            result = await validator.validate_question(question, tenant_id)
            
            print(f"✅ Can Answer: {result['can_answer']}")
            print(f"🔍 Method: {result['validation_method']}")
            
            if not result['can_answer']:
                print(f"🚫 Missing: {result['missing_concepts']}")
                print(f"📊 Available Tables: {result['available_tables']}")
                print(f"💬 Response Preview: {result['response'][:100]}...")
            else:
                print(f"✅ Ready for SQL generation")
                print(f"📊 Available Tables: {result['available_tables']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show schema summary
    print(f"\n📋 Schema Summary for company-a:")
    try:
        summary = validator.get_schema_summary('company-a')
        if 'error' not in summary:
            print(f"Tables: {summary['total_tables']}")
            for table, info in summary['tables'].items():
                print(f"• {table}: {info['column_count']} columns")
        else:
            print(f"Error: {summary['error']}")
    except Exception as e:
        print(f"❌ Summary error: {e}")

if __name__ == "__main__":
    print("🏗️ Enterprise Schema Validator - FIXED VERSION")
    print("🔧 Auto-discovery with robust error handling")
    # asyncio.run(demo_enterprise_validator())