// pages/api/schema/drop-schema.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { getCompanyDatabase } from '../../../lib/database';
import { z } from 'zod';

const DropSchemaSchema = z.object({
  companyCode: z.string().min(1),
  schemaName: z.string().min(1),
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

    const validatedData = DropSchemaSchema.parse(req.body);
    const { companyCode, schemaName, cascade } = validatedData;

    // Prevent dropping system schemas
    if (['public', 'information_schema', 'pg_catalog'].includes(schemaName)) {
      return res.status(400).json({ error: 'Cannot drop system schemas' });
    }

    const pool = getCompanyDatabase(companyCode);
    
    const dropSQL = `DROP SCHEMA "${schemaName}" ${cascade ? 'CASCADE' : 'RESTRICT'};`;
    await pool.query(dropSQL);

    console.log(`Schema "${schemaName}" dropped for company ${companyCode} by ${session.user.email}`);

    return res.status(200).json({
      success: true,
      message: `Schema "${schemaName}" dropped successfully`
    });

  } catch (error) {
    console.error('Error dropping schema:', error);
    return res.status(500).json({
      error: 'Failed to drop schema',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
