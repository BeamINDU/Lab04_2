// pages/api/database/schemas.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { Pool } from 'pg';

// Database connection with better error handling
const createPool = () => {
  try {
    return new Pool({
      user: process.env.DB_USER || 'postgres',
      host: process.env.DB_HOST || 'localhost',
      database: process.env.DB_NAME || 'company_management',
      password: process.env.DB_PASSWORD || 'password',
      port: parseInt(process.env.DB_PORT || '15432'), // ใช้ port ตาม docker-compose.yml
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    });
  } catch (error) {
    console.error('Failed to create database pool:', error);
    throw error;
  }
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  console.log(`📍 API ${req.method} /api/database/schemas called`);
  
  try {
    // Authentication check
    const session = await getServerSession(req, res, authOptions);
    if (!session?.user) {
      console.log('❌ Unauthorized access attempt');
      return res.status(401).json({ error: 'Unauthorized' });
    }

    console.log(`✅ Authenticated user: ${session.user.email}`);
    console.log(`🏢 Company: ${session.user.companyCode}`);

    if (req.method === 'GET') {
      return await handleGetSchemas(req, res, session);
    } else if (req.method === 'POST') {
      return await handleCreateSchema(req, res, session);
    } else {
      res.setHeader('Allow', ['GET', 'POST']);
      return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
    }

  } catch (error) {
    console.error('❌ API Error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

async function handleGetSchemas(req: NextApiRequest, res: NextApiResponse, session: any) {
  console.log('📋 Getting schemas...');
  
  let pool: Pool | null = null;
  let client = null;

  try {
    // สำหรับการทดสอบ ให้ return mock data ก่อน
    if (process.env.NODE_ENV === 'development' && !process.env.DB_PASSWORD) {
      console.log('🧪 Using mock data for development');
      const mockSchemas = [
        {
          name: 'public',
          type: 'default',
          description: 'Default public schema',
          tables: ['employees', 'projects', 'departments'],
          tableDetails: [
            { name: 'employees', comment: 'Employee information' },
            { name: 'projects', comment: 'Project data' },
            { name: 'departments', comment: 'Department structure' }
          ],
          createdAt: new Date().toISOString()
        },
        {
          name: 'analytics',
          type: 'custom',
          description: 'Analytics and reporting schema',
          tables: ['reports', 'metrics'],
          tableDetails: [
            { name: 'reports', comment: 'Generated reports' },
            { name: 'metrics', comment: 'Performance metrics' }
          ],
          createdAt: new Date().toISOString()
        }
      ];

      return res.status(200).json({ 
        success: true,
        schemas: mockSchemas,
        company: session.user.companyCode,
        mode: 'mock'
      });
    }

    // Real database connection
    pool = createPool();
    client = await pool.connect();
    
    console.log('✅ Database connected successfully');

    // Get all schemas with their tables
    const schemasQuery = `
      SELECT 
        schema_name,
        obj_description(oid, 'pg_namespace') as description
      FROM information_schema.schemata s
      LEFT JOIN pg_namespace n ON n.nspname = s.schema_name
      WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
      ORDER BY schema_name;
    `;

    const tablesQuery = `
      SELECT 
        table_schema,
        table_name,
        obj_description(pgc.oid, 'pg_class') as table_comment
      FROM information_schema.tables t
      LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
      WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
      AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name;
    `;

    console.log('🔍 Executing schema queries...');
    const [schemasResult, tablesResult] = await Promise.all([
      client.query(schemasQuery),
      client.query(tablesQuery)
    ]);

    console.log(`📊 Found ${schemasResult.rows.length} schemas`);
    console.log(`📊 Found ${tablesResult.rows.length} tables`);

    // Group tables by schema
    const tablesBySchema = tablesResult.rows.reduce((acc: any, table: any) => {
      if (!acc[table.table_schema]) {
        acc[table.table_schema] = [];
      }
      acc[table.table_schema].push({
        name: table.table_name,
        comment: table.table_comment
      });
      return acc;
    }, {});

    // Combine schemas with their tables
    const schemas = schemasResult.rows.map((schema: any) => ({
      name: schema.schema_name,
      description: schema.description,
      type: schema.schema_name === 'public' ? 'default' : 'custom',
      tables: (tablesBySchema[schema.schema_name] || []).map((t: any) => t.name),
      tableDetails: tablesBySchema[schema.schema_name] || [],
      createdAt: new Date().toISOString()
    }));

    console.log('✅ Schemas processed successfully');

    return res.status(200).json({
      success: true,
      schemas,
      company: session.user.companyCode
    });

  } catch (error) {
    console.error('❌ Database error:', error);
    
    // Return mock data as fallback
    console.log('🔄 Falling back to mock data');
    const fallbackSchemas = [
      {
        name: 'public',
        type: 'default',
        description: 'Default public schema (fallback)',
        tables: [],
        tableDetails: [],
        createdAt: new Date().toISOString()
      }
    ];

    return res.status(200).json({
      success: true,
      schemas: fallbackSchemas,
      company: session.user.companyCode,
      mode: 'fallback',
      warning: 'Database connection failed, using fallback data'
    });

  } finally {
    if (client) {
      try {
        client.release();
        console.log('🔌 Database client released');
      } catch (error) {
        console.error('❌ Error releasing client:', error);
      }
    }
    if (pool) {
      try {
        await pool.end();
        console.log('🔌 Database pool closed');
      } catch (error) {
        console.error('❌ Error closing pool:', error);
      }
    }
  }
}

async function handleCreateSchema(req: NextApiRequest, res: NextApiResponse, session: any) {
  console.log('➕ Creating new schema...');
  
  const { name, description } = req.body;
  
  if (!name || name.trim() === '') {
    return res.status(400).json({ error: 'Schema name is required' });
  }

  // For development, return success without database operation
  if (process.env.NODE_ENV === 'development' && !process.env.DB_PASSWORD) {
    console.log(`🧪 Mock schema creation: ${name}`);
    return res.status(201).json({ 
      success: true, 
      message: `Schema "${name}" created successfully (mock)`,
      mode: 'mock'
    });
  }

  let pool: Pool | null = null;
  let client = null;

  try {
    pool = createPool();
    client = await pool.connect();
    
    await client.query('BEGIN');
    
    // Create schema
    await client.query(`CREATE SCHEMA IF NOT EXISTS "${name}"`);
    
    // Add comment if description provided
    if (description) {
      await client.query(
        `COMMENT ON SCHEMA "${name}" IS $1`,
        [description]
      );
    }
    
    await client.query('COMMIT');
    
    console.log(`✅ Schema "${name}" created successfully`);
    
    return res.status(201).json({ 
      success: true, 
      message: `Schema "${name}" created successfully` 
    });

  } catch (error) {
    if (client) {
      try {
        await client.query('ROLLBACK');
      } catch (rollbackError) {
        console.error('❌ Rollback error:', rollbackError);
      }
    }
    
    console.error('❌ Schema creation error:', error);
    return res.status(500).json({ 
      error: 'Failed to create schema',
      details: error instanceof Error ? error.message : 'Unknown error'
    });

  } finally {
    if (client) {
      try {
        client.release();
      } catch (error) {
        console.error('❌ Error releasing client:', error);
      }
    }
    if (pool) {
      try {
        await pool.end();
      } catch (error) {
        console.error('❌ Error closing pool:', error);
      }
    }
  }
}