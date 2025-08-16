// pages/api/schema/create-schema.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { getCompanyDatabase } from '../../../lib/database';
import { z } from 'zod';

const CreateSchemaSchema = z.object({
  name: z.string().min(1, 'Schema name is required'),
  description: z.string().optional(),
  companyCode: z.string().min(1, 'Company code is required')
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session?.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const validatedData = CreateSchemaSchema.parse(req.body);
    const { name, description, companyCode } = validatedData;

    // Get database connection
    const pool = getCompanyDatabase(companyCode);
    
    // Create schema
    const createSchemaSQL = `CREATE SCHEMA IF NOT EXISTS "${name}";`;
    await pool.query(createSchemaSQL);

    // Add comment if description provided
    if (description) {
      const commentSQL = `COMMENT ON SCHEMA "${name}" IS '${description}';`;
      await pool.query(commentSQL);
    }

    // Log the creation
    console.log(`Schema "${name}" created for company ${companyCode} by ${session.user.email}`);

    return res.status(200).json({
      success: true,
      message: `Schema "${name}" created successfully`,
      schema: { name, description }
    });

  } catch (error) {
    console.error('Error creating schema:', error);
    return res.status(500).json({
      error: 'Failed to create schema',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

