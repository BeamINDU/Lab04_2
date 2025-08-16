// pages/api/schema/create-table.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';
import { getCompanyDatabase } from '../../../lib/database';
import { z } from 'zod';

const ColumnSchema = z.object({
  name: z.string().min(1),
  type: z.string().min(1),
  length: z.number().optional(),
  isPrimary: z.boolean().default(false),
  isRequired: z.boolean().default(false),
  isUnique: z.boolean().default(false),
  defaultValue: z.string().optional(),
  references: z.object({
    table: z.string().optional(),
    column: z.string().optional()
  }).optional()
});

const CreateTableSchema = z.object({
  companyCode: z.string().min(1),
  tableName: z.string().min(1),
  schema: z.string().default('public'),
  description: z.string().optional(),
  columns: z.array(ColumnSchema).min(1),
  sql: z.string().optional() // Pre-generated SQL (optional)
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

    const validatedData = CreateTableSchema.parse(req.body);
    const { companyCode, tableName, schema, description, columns, sql } = validatedData;

    // Get database connection
    const pool = getCompanyDatabase(companyCode);

    // Generate SQL if not provided
    let createTableSQL = sql;
    if (!createTableSQL) {
      createTableSQL = generateCreateTableSQL(tableName, columns, schema);
    }

    // Execute the SQL
    await pool.query(createTableSQL);

    // Add table comment if description provided
    if (description) {
      const commentSQL = `COMMENT ON TABLE ${schema}.${tableName} IS '${description}';`;
      await pool.query(commentSQL);
    }

    console.log(`Table "${tableName}" created in schema "${schema}" for company ${companyCode}`);

    return res.status(200).json({
      success: true,
      message: `Table "${tableName}" created successfully`,
      table: { name: tableName, schema, description, columns }
    });

  } catch (error) {
    console.error('Error creating table:', error);
    return res.status(500).json({
      error: 'Failed to create table',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

function generateCreateTableSQL(tableName: string, columns: any[], schema: string = 'public'): string {
  const columnDefs = columns.map(col => {
    let colDef = `  ${col.name} ${col.type}`;
    
    if (col.type === 'VARCHAR' && col.length) {
      colDef += `(${col.length})`;
    }
    
    if (col.isPrimary) {
      colDef += ' PRIMARY KEY';
    }
    
    if (col.isRequired && !col.isPrimary) {
      colDef += ' NOT NULL';
    }
    
    if (col.isUnique && !col.isPrimary) {
      colDef += ' UNIQUE';
    }
    
    if (col.defaultValue && !col.isPrimary) {
      colDef += ` DEFAULT ${col.defaultValue}`;
    }
    
    return colDef;
  }).join(',\n');

  const foreignKeys = columns
    .filter(col => col.references?.table && col.references?.column)
    .map(col => `  FOREIGN KEY (${col.name}) REFERENCES ${col.references.table}(${col.references.column})`)
    .join(',\n');

  let sql = `CREATE TABLE ${schema}.${tableName} (\n${columnDefs}`;
  if (foreignKeys) {
    sql += `,\n${foreignKeys}`;
  }
  sql += '\n);';

  return sql;
}


