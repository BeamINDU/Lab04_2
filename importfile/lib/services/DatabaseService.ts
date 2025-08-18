// lib/services/DatabaseService.ts
import { Pool } from 'pg';
import { getCompanyDatabase } from '../database';

export interface DatabaseColumn {
  name: string;
  type: string;
  length?: number;
  isPrimary?: boolean;
  isRequired?: boolean;
  isUnique?: boolean;
  defaultValue?: string;
  comment?: string;
  references?: {
    table: string;
    column: string;
  };
}

export interface CreateTableOptions {
  companyCode: string;
  schema: string;
  tableName: string;
  description?: string;
  columns: DatabaseColumn[];
  ifNotExists?: boolean;
}

export interface SchemaInfo {
  name: string;
  description?: string;
  tables: TableInfo[];
  createdAt?: Date;
}

export interface TableInfo {
  name: string;
  schema: string;
  comment?: string;
  columnCount: number;
  hasData: boolean;
  createdAt?: Date;
}

export interface ImportResult {
  success: boolean;
  totalRows: number;
  successRows: number;
  errorRows: number;
  errors: Array<{
    row: number;
    column?: string;
    error: string;
    data?: any;
  }>;
  executionTime: number;
}

/**
 * Enhanced Database Service สำหรับจัดการ database operations
 * ออกแบบมาเพื่อให้มีความยืดหยุ่นและปลอดภัยสูง
 */
export class DatabaseService {
  private pool: Pool;
  private companyCode: string;

  constructor(companyCode: string) {
    this.companyCode = companyCode;
    this.pool = getCompanyDatabase(companyCode);
  }

  /**
   * ดึงรายชื่อ schema ทั้งหมดที่ user สามารถเข้าถึงได้
   */
  async getSchemas(): Promise<SchemaInfo[]> {
    try {
      const query = `
        SELECT 
          schema_name,
          COALESCE(
            (SELECT description FROM pg_description 
             WHERE objoid = (SELECT oid FROM pg_namespace WHERE nspname = schema_name)
             AND objsubid = 0), 
            null
          ) as description
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
      `;

      const result = await this.pool.query(query);
      
      const schemas: SchemaInfo[] = [];
      
      for (const row of result.rows) {
        const tables = await this.getTablesInSchema(row.schema_name);
        schemas.push({
          name: row.schema_name,
          description: row.description,
          tables
        });
      }

      return schemas;
    } catch (error) {
      throw new Error(`Failed to fetch schemas: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * สร้าง schema ใหม่พร้อมการตรวจสอบความปลอดภัย
   */
  async createSchema(name: string, description?: string): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // สร้าง schema
      const createQuery = `CREATE SCHEMA IF NOT EXISTS "${name}";`;
      await client.query(createQuery);
      
      // เพิ่มคำอธิบาย (ถ้ามี)
      if (description) {
        const commentQuery = `COMMENT ON SCHEMA "${name}" IS $1;`;
        await client.query(commentQuery, [description]);
      }
      
      await client.query('COMMIT');
      console.log(`✅ Schema "${name}" created successfully for company ${this.companyCode}`);
      
    } catch (error) {
      await client.query('ROLLBACK');
      throw new Error(`Failed to create schema: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      client.release();
    }
  }

  /**
   * ลบ schema พร้อมตรวจสอบความปลอดภัย
   */
  async dropSchema(name: string, cascade: boolean = false): Promise<void> {
    // ป้องกันการลบ schema ระบบ
    const protectedSchemas = ['public', 'information_schema', 'pg_catalog', 'pg_toast'];
    if (protectedSchemas.includes(name.toLowerCase())) {
      throw new Error(`Cannot drop protected schema: ${name}`);
    }

    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      const dropQuery = `DROP SCHEMA "${name}" ${cascade ? 'CASCADE' : 'RESTRICT'};`;
      await client.query(dropQuery);
      
      await client.query('COMMIT');
      console.log(`✅ Schema "${name}" dropped successfully for company ${this.companyCode}`);
      
    } catch (error) {
      await client.query('ROLLBACK');
      throw new Error(`Failed to drop schema: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      client.release();
    }
  }

  /**
   * สร้างตารางใหม่พร้อมการ validate columns
   */
  async createTable(options: CreateTableOptions): Promise<void> {
    const { schema, tableName, description, columns, ifNotExists = true } = options;
    
    // Validate input
    this.validateTableCreation(options);
    
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // สร้าง SQL สำหรับการสร้างตาราง (ไม่ใช้ parameters)
      const createTableSQL = this.generateCreateTableSQL(schema, tableName, columns, ifNotExists);
      
      console.log('=== CREATE TABLE SQL ===');
      console.log(createTableSQL);
      console.log('========================');
      
      // Execute SQL โดยไม่ใช้ parameters เพราะ CREATE TABLE ไม่รองรับ
      await client.query(createTableSQL);
      
      // เพิ่มคำอธิบายของตาราง (ใช้ parameters ได้)
      if (description) {
        const commentSQL = `COMMENT ON TABLE "${schema}"."${tableName}" IS $1`;
        await client.query(commentSQL, [description]);
      }
      
      // เพิ่มคำอธิบายของ columns (ใช้ parameters ได้)
      for (const column of columns) {
        if (column.comment) {
          const columnCommentSQL = `COMMENT ON COLUMN "${schema}"."${tableName}"."${column.name}" IS $1`;
          await client.query(columnCommentSQL, [column.comment]);
        }
      }
      
      await client.query('COMMIT');
      console.log(`✅ Table "${schema}"."${tableName}" created successfully for company ${this.companyCode}`);
      
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('❌ Error creating table:', error);
      console.error('❌ Failed SQL:', this.generateCreateTableSQL(schema, tableName, columns, ifNotExists));
      
      // ให้ข้อมูล error ที่ละเอียดขึ้น
      if (error instanceof Error) {
        throw new Error(`Failed to create table "${tableName}": ${error.message}`);
      } else {
        throw new Error(`Failed to create table "${tableName}": Unknown error`);
      }
    } finally {
      client.release();
    }
  }

  /**
   * ลบตารางพร้อมตรวจสอบ dependencies
   */
  async dropTable(schema: string, tableName: string, cascade: boolean = false): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // ตรวจสอบว่าตารางมีอยู่จริง
      const existsQuery = `
        SELECT EXISTS (
          SELECT FROM information_schema.tables 
          WHERE table_schema = $1 AND table_name = $2
        );
      `;
      const existsResult = await client.query(existsQuery, [schema, tableName]);
      
      if (!existsResult.rows[0].exists) {
        throw new Error(`Table "${schema}"."${tableName}" does not exist`);
      }
      
      const dropSQL = `DROP TABLE "${schema}"."${tableName}" ${cascade ? 'CASCADE' : 'RESTRICT'};`;
      await client.query(dropSQL);
      
      await client.query('COMMIT');
      console.log(`✅ Table "${schema}"."${tableName}" dropped successfully for company ${this.companyCode}`);
      
    } catch (error) {
      await client.query('ROLLBACK');
      throw new Error(`Failed to drop table: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      client.release();
    }
  }

  /**
   * ดึงข้อมูลตารางใน schema ที่ระบุ
   */
  private async getTablesInSchema(schemaName: string): Promise<TableInfo[]> {
    const query = `
      SELECT 
        t.table_name,
        t.table_schema,
        obj_description(c.oid, 'pg_class') as comment,
        (SELECT COUNT(*) FROM information_schema.columns 
         WHERE table_schema = t.table_schema AND table_name = t.table_name) as column_count
      FROM information_schema.tables t
      LEFT JOIN pg_class c ON c.relname = t.table_name
      WHERE t.table_schema = $1 
        AND t.table_type = 'BASE TABLE'
      ORDER BY t.table_name;
    `;

    try {
      const result = await this.pool.query(query, [schemaName]);
      
      const tables: TableInfo[] = [];
      
      for (const row of result.rows) {
        // ตรวจสอบว่ามีข้อมูลในตารางหรือไม่แบบแยกต่างหาก
        let hasData = false;
        try {
          const dataCheckQuery = `SELECT EXISTS (SELECT 1 FROM "${schemaName}"."${row.table_name}" LIMIT 1);`;
          const dataResult = await this.pool.query(dataCheckQuery);
          hasData = dataResult.rows[0].exists;
        } catch (error) {
          // ถ้าเช็คไม่ได้ (เช่น permissions) ให้ใส่ false
          hasData = false;
        }
        
        tables.push({
          name: row.table_name,
          schema: row.table_schema,
          comment: row.comment || undefined,
          columnCount: parseInt(row.column_count) || 0,
          hasData
        });
      }
      
      return tables;
    } catch (error) {
      // ถ้า query ล้มเหลว ให้ใช้วิธีง่ายๆ แทน
      const simpleQuery = `
        SELECT 
          table_name,
          table_schema
        FROM information_schema.tables 
        WHERE table_schema = $1 AND table_type = 'BASE TABLE'
        ORDER BY table_name;
      `;
      
      const result = await this.pool.query(simpleQuery, [schemaName]);
      
      return result.rows.map(row => ({
        name: row.table_name,
        schema: row.table_schema,
        comment: undefined,
        columnCount: 0,
        hasData: false
      }));
    }
  }

  /**
   * Validate การสร้างตาราง
   */
  private validateTableCreation(options: CreateTableOptions): void {
    const { tableName, columns } = options;
    
    if (!tableName || tableName.trim().length === 0) {
      throw new Error('Table name is required');
    }
    
    // ตรวจสอบชื่อตารางว่าเป็น valid identifier
    if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(tableName)) {
      throw new Error('Table name must start with a letter and contain only letters, numbers, and underscores');
    }
    
    if (!columns || columns.length === 0) {
      throw new Error('At least one column is required');
    }
    
    // ตรวจสอบ column names
    for (const col of columns) {
      if (!col.name || col.name.trim().length === 0) {
        throw new Error('All columns must have names');
      }
      
      if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(col.name)) {
        throw new Error(`Invalid column name "${col.name}". Column names must start with a letter and contain only letters, numbers, and underscores`);
      }
      
      if (!col.type || col.type.trim().length === 0) {
        throw new Error(`Column "${col.name}" must have a type`);
      }
    }
    
    // ตรวจสอบชื่อ column ซ้ำ
    const columnNames = columns.map(col => col.name.toLowerCase());
    const duplicates = columnNames.filter((name, index) => columnNames.indexOf(name) !== index);
    
    if (duplicates.length > 0) {
      throw new Error(`Duplicate column names found: ${[...new Set(duplicates)].join(', ')}`);
    }
    
    // ตรวจสอบ primary key
    const primaryKeys = columns.filter(col => col.isPrimary);
    if (primaryKeys.length === 0) {
      throw new Error('At least one primary key column is required');
    }
    
    // ตรวจสอบว่า SERIAL columns เป็น primary key
    const serialColumns = columns.filter(col => col.type === 'SERIAL');
    for (const serialCol of serialColumns) {
      if (!serialCol.isPrimary) {
        throw new Error(`SERIAL column "${serialCol.name}" should be a primary key`);
      }
    }
  }

  /**
   * สร้าง SQL สำหรับการสร้างตาราง
   */
  private generateCreateTableSQL(schema: string, tableName: string, columns: DatabaseColumn[], ifNotExists: boolean): string {
    // Sanitize และ validate ชื่อ schema และ table
    const cleanSchema = schema.replace(/[^a-zA-Z0-9_]/g, '');
    const cleanTableName = tableName.replace(/[^a-zA-Z0-9_]/g, '');
    
    const columnDefs: string[] = [];
    
    // สร้าง column definitions
    for (const col of columns) {
      const cleanColumnName = col.name.replace(/[^a-zA-Z0-9_]/g, '');
      let definition = `"${cleanColumnName}" ${this.getPostgreSQLType(col)}`;
      
      // เพิ่ม NOT NULL สำหรับ required columns (ยกเว้น SERIAL)
      if (col.isRequired && !col.isPrimary && col.type !== 'SERIAL') {
        definition += ' NOT NULL';
      }
      
      // เพิ่ม DEFAULT value (ยกเว้น SERIAL และ PRIMARY KEY)
      if (col.defaultValue && col.type !== 'SERIAL' && !col.isPrimary) {
        const defaultValue = this.formatDefaultValue(col.defaultValue, col.type);
        definition += ` DEFAULT ${defaultValue}`;
      }
      
      columnDefs.push(definition);
    }
    
    // เพิ่ม PRIMARY KEY constraint
    const primaryKeys = columns.filter(col => col.isPrimary);
    if (primaryKeys.length > 0) {
      const pkColumns = primaryKeys.map(col => `"${col.name.replace(/[^a-zA-Z0-9_]/g, '')}"`);
      columnDefs.push(`PRIMARY KEY (${pkColumns.join(', ')})`);
    }
    
    // เพิ่ม UNIQUE constraints
    const uniqueColumns = columns.filter(col => col.isUnique && !col.isPrimary);
    for (const col of uniqueColumns) {
      const cleanColName = col.name.replace(/[^a-zA-Z0-9_]/g, '');
      columnDefs.push(`UNIQUE ("${cleanColName}")`);
    }
    
    // สร้าง final SQL
    const ifNotExistsClause = ifNotExists ? 'IF NOT EXISTS ' : '';
    const sql = `CREATE TABLE ${ifNotExistsClause}"${cleanSchema}"."${cleanTableName}" (\n  ${columnDefs.join(',\n  ')}\n)`;
    
    return sql;
  }

  /**
   * Format default value ตาม data type
   */
  private formatDefaultValue(value: string, type: string): string {
    const upperValue = value.toUpperCase();
    const upperType = type.toUpperCase();
    
    // ค่าพิเศษที่ไม่ต้องใส่ quotes
    const specialValues = [
      'CURRENT_TIMESTAMP', 
      'NOW()', 
      'CURRENT_DATE', 
      'CURRENT_TIME',
      'TRUE', 
      'FALSE',
      'NULL'
    ];
    
    if (specialValues.includes(upperValue)) {
      return upperValue;
    }
    
    // ตัวเลข
    if (!isNaN(Number(value)) && ['INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC', 'REAL', 'DOUBLE'].includes(upperType)) {
      return value;
    }
    
    // Boolean values
    if (upperType === 'BOOLEAN') {
      if (['1', 'YES', 'Y', 'ON'].includes(upperValue)) return 'TRUE';
      if (['0', 'NO', 'N', 'OFF'].includes(upperValue)) return 'FALSE';
    }
    
    // String values - escape single quotes
    const escapedValue = value.replace(/'/g, "''");
    return `'${escapedValue}'`;
  }

  /**
   * แปลง column type เป็น PostgreSQL type
   */
  private getPostgreSQLType(column: DatabaseColumn): string {
    const type = column.type.toUpperCase();
    
    switch (type) {
      case 'SERIAL':
        return 'SERIAL';
      case 'INTEGER':
      case 'INT':
        return 'INTEGER';
      case 'BIGINT':
        return 'BIGINT';
      case 'VARCHAR':
        return `VARCHAR(${column.length || 255})`;
      case 'TEXT':
        return 'TEXT';
      case 'BOOLEAN':
      case 'BOOL':
        return 'BOOLEAN';
      case 'DATE':
        return 'DATE';
      case 'TIMESTAMP':
        return 'TIMESTAMP WITH TIME ZONE';
      case 'DECIMAL':
      case 'NUMERIC':
        return column.length ? `DECIMAL(${column.length})` : 'DECIMAL(10,2)';
      case 'FLOAT':
        return 'REAL';
      case 'DOUBLE':
        return 'DOUBLE PRECISION';
      case 'UUID':
        return 'UUID';
      case 'JSON':
        return 'JSON';
      case 'JSONB':
        return 'JSONB';
      default:
        // ถ้าไม่รู้จัก type ให้ใช้ TEXT เป็น default
        console.warn(`Unknown column type: ${type}, using TEXT instead`);
        return 'TEXT';
    }
  }
}