// pages/api/schema/drop-table.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { getCompanyDatabase } from '../../../lib/database';
import { z } from 'zod';

const DropTableSchema = z.object({
  companyCode: z.string().min(1),
  tableName: z.string().min(1),
  schema: z.string().default('public'),
  cascade: z.boolean().default(false)
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session?.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const validatedData = DropTableSchema.parse(req.body);
    const { companyCode, tableName, schema, cascade } = validatedData;

    const pool = getCompanyDatabase(companyCode);
    
    const dropSQL = `DROP TABLE ${schema}.${tableName} ${cascade ? 'CASCADE' : 'RESTRICT'};`;
    await pool.query(dropSQL);

    console.log(`Table "${tableName}" dropped from schema "${schema}" for company ${companyCode}`);

    return res.status(200).json({
      success: true,
      message: `Table "${tableName}" dropped successfully`
    });

  } catch (error) {
    console.error('Error dropping table:', error);
    return res.status(500).json({
      error: 'Failed to drop table',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
