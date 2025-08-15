import { Pool } from 'pg';

const pools: { [key: string]: Pool } = {};
export function getCompanyDatabase(companyCode: string): Pool {
  if (!pools[companyCode]) {
    // 🔥 เชื่อมต่อไปยัง chatbot company databases
    const dbConfigs: { [key: string]: any } = {
      'company_a': {
        host: 'postgres-company-a',
        port: 5432,
        database: 'siamtech_company_a',
        user: 'postgres',
        password: 'password123',
      },
      'company_b': {
        host: 'postgres-company-b', 
        port: 5432,
        database: 'siamtech_company_b',
        user: 'postgres',
        password: 'password123',
      },
      'company_c': {
        host: 'postgres-company-c',
        port: 5432, 
        database: 'siamtech_company_c',
        user: 'postgres',
        password: 'password123',
      },
    };

    const config = dbConfigs[companyCode];
    if (!config) {
      throw new Error(`No database configuration for company: ${companyCode}`);
    }

    pools[companyCode] = new Pool(config);
  }

  return pools[companyCode];
}

export async function getAllTables(companyCode: string) {
  const pool = getCompanyDatabase(companyCode);
  
  const query = `
    SELECT 
      table_name,
      NULL as table_comment
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
  `;
  
  const result = await pool.query(query);
  return result.rows;
}

export async function getTableSchema(companyCode: string, tableName: string) {
  const pool = getCompanyDatabase(companyCode);
  
  const query = `
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default,
      character_maximum_length,
      numeric_precision,
      numeric_scale
    FROM information_schema.columns
    WHERE table_name = $1
    AND table_schema = 'public'
    ORDER BY ordinal_position;
  `;
  
  const result = await pool.query(query, [tableName]);
  return result.rows;
}