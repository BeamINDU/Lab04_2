import { NextApiRequest, NextApiResponse } from 'next';
import { Pool } from 'pg';

const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'siamtech_company_a',
  password: process.env.DB_PASSWORD,
  port: parseInt(process.env.DB_PORT || '5432'),
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Get all schemas
    try {
      const client = await pool.connect();
      
      const schemasQuery = `
        SELECT 
          schema_name,
          CASE 
            WHEN schema_name IN ('public', 'information_schema', 'pg_catalog') 
            THEN 'default' 
            ELSE 'custom' 
          END as type
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
      `;
      
      const schemasResult = await client.query(schemasQuery);
      const schemas = [];

      for (const schema of schemasResult.rows) {
        const tablesQuery = `
          SELECT table_name 
          FROM information_schema.tables 
          WHERE table_schema = $1 
          AND table_type = 'BASE TABLE'
          ORDER BY table_name;
        `;
        
        const tablesResult = await client.query(tablesQuery, [schema.schema_name]);
        
        schemas.push({
          name: schema.schema_name,
          type: schema.type,
          tables: tablesResult.rows.map((row: any) => row.table_name),
          createdAt: new Date().toISOString()
        });
      }

      client.release();
      res.status(200).json({ schemas });
    } catch (error: any) {
      console.error('Error fetching schemas:', error);
      res.status(500).json({ message: 'Failed to fetch schemas' });
    }
  } else if (req.method === 'POST') {
    // Create new schema
    try {
      const { name, description } = req.body;
      
      if (!name || name.trim() === '') {
        return res.status(400).json({ message: 'Schema name is required' });
      }

      const client = await pool.connect();
      
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
      client.release();
      
      res.status(201).json({ 
        success: true, 
        message: `Schema "${name}" created successfully` 
      });
    } catch (error: any) {
      console.error('Error creating schema:', error);
      res.status(500).json({ message: `Failed to create schema: ${error.message}` });
    }
  } else {
    res.setHeader('Allow', ['GET', 'POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
