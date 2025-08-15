import { Pool } from 'pg';

// Database connection pools for each company
const connectionPools: Map<string, Pool> = new Map();

export function getCompanyDatabase(companyCode: string): Pool {
  if (!connectionPools.has(companyCode)) {
    const dbName = `siamtech_${companyCode}`;
    const connectionString = process.env.DATABASE_URL?.replace(
      /\/[^/]+$/,
      `/${dbName}`
    );

    const pool = new Pool({
      connectionString,
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    connectionPools.set(companyCode, pool);
  }

  return connectionPools.get(companyCode)!;
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

export async function getAllTables(companyCode: string) {
  const pool = getCompanyDatabase(companyCode);
  
  const query = `
    SELECT table_name, 
           obj_description(c.oid) as table_comment
    FROM information_schema.tables t
    LEFT JOIN pg_class c ON c.relname = t.table_name
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
  `;

  const result = await pool.query(query);
  return result.rows;
}
