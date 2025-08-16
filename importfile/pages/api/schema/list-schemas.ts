// pages/api/schema/list-schemas.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { getCompanyDatabase } from '../../../lib/database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session?.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { companyCode } = req.query;
    if (!companyCode || typeof companyCode !== 'string') {
      return res.status(400).json({ error: 'Company code is required' });
    }

    const pool = getCompanyDatabase(companyCode);

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

    const [schemasResult, tablesResult] = await Promise.all([
      pool.query(schemasQuery),
      pool.query(tablesQuery)
    ]);

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
      createdAt: new Date().toISOString() // You might want to track this properly
    }));

    return res.status(200).json({
      success: true,
      schemas,
      company: companyCode
    });

  } catch (error) {
    console.error('Error listing schemas:', error);
    return res.status(500).json({
      error: 'Failed to list schemas',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

