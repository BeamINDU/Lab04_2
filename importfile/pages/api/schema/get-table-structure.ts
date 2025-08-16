// pages/api/schema/get-table-structure.ts
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

    const { companyCode, tableName, schema = 'public' } = req.query;
    
    if (!companyCode || !tableName) {
      return res.status(400).json({ error: 'Company code and table name are required' });
    }

    const pool = getCompanyDatabase(companyCode as string);

    // Get table structure
    const structureQuery = `
      SELECT
        column_name,
        data_type,
        character_maximum_length,
        is_nullable,
        column_default,
        is_identity,
        identity_generation
      FROM information_schema.columns
      WHERE table_schema = $1 AND table_name = $2
      ORDER BY ordinal_position;
    `;

    // Get constraints
    const constraintsQuery = `
      SELECT
        tc.constraint_name,
        tc.constraint_type,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      LEFT JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
      WHERE tc.table_schema = $1 AND tc.table_name = $2;
    `;

    // Get indexes
    const indexesQuery = `
      SELECT
        indexname,
        indexdef
      FROM pg_indexes
      WHERE schemaname = $1 AND tablename = $2;
    `;

    const [structureResult, constraintsResult, indexesResult] = await Promise.all([
      pool.query(structureQuery, [schema, tableName]),
      pool.query(constraintsQuery, [schema, tableName]),
      pool.query(indexesQuery, [schema, tableName])
    ]);

    return res.status(200).json({
      success: true,
      table: {
        name: tableName,
        schema: schema,
        columns: structureResult.rows,
        constraints: constraintsResult.rows,
        indexes: indexesResult.rows
      }
    });

  } catch (error) {
    console.error('Error getting table structure:', error);
    return res.status(500).json({
      error: 'Failed to get table structure',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}