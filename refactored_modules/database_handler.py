import psycopg2
from decimal import Decimal
from typing import Dict, Any, List
import logging
from .tenant_config import TenantConfig

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """🗄️ Handles all database operations with proper Decimal handling"""
    
    def __init__(self, tenant_configs: Dict[str, TenantConfig]):
        self.tenant_configs = tenant_configs
    
    def get_database_connection(self, tenant_id: str) -> psycopg2.extensions.connection:
        """Get database connection for specific tenant"""
        if tenant_id not in self.tenant_configs:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        config = self.tenant_configs[tenant_id]
        
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database for {tenant_id}: {e}")
            raise
    
    def execute_sql_query(self, tenant_id: str, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results with Decimal handling"""
        conn = None
        try:
            conn = self.get_database_connection(tenant_id)
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # 🔧 Convert Decimals immediately
                processed_row = {}
                for key, value in row_dict.items():
                    if isinstance(value, Decimal):
                        processed_row[key] = float(value)
                    else:
                        processed_row[key] = value
                results.append(processed_row)
                
            logger.info(f"Query executed successfully for {tenant_id}: {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"SQL execution failed for {tenant_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def process_decimal_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """🔧 Convert Decimal objects to float for JSON serialization"""
        processed_data = []
        for row in data:
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, Decimal):
                    processed_row[key] = float(value)
                else:
                    processed_row[key] = value
            processed_data.append(processed_row)
        return processed_data
    
    def validate_sql_query(self, sql: str, tenant_id: str) -> bool:
        """Validate SQL query for safety"""
        sql_upper = sql.upper()
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            return False
        return sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
