// lib/services/FileImportService.ts - Updated with Correct Dependencies
import { DatabaseService, DatabaseColumn, ImportResult } from './DatabaseService';
import * as fs from 'fs';
import * as path from 'path';
import csv from 'csv-parser';
import * as XLSX from 'xlsx';

export interface ImportOptions {
  filePath: string;
  fileName: string;
  mimeType: string;
  schema: string;
  tableName: string;
  createTable: boolean;
  truncateBeforeImport: boolean;
  skipErrors: boolean;
  batchSize: number;
}

export interface FilePreview {
  headers: string[];
  sampleData: any[];
  totalRows: number;
  fileName: string;
  fileType: string;
  suggestedColumns: DatabaseColumn[];
}

/**
 * Enhanced File Import Service
 * รองรับการ import ไฟล์หลายประเภทพร้อมการตรวจสอบและ validation ที่ครบถ้วน
 */
export class FileImportService {
  private dbService: DatabaseService;

  constructor(dbService: DatabaseService) {
    this.dbService = dbService;
  }

  /**
   * Preview ไฟล์ก่อนการ import
   */
  async previewFile(filePath: string, fileName: string, mimeType: string): Promise<FilePreview> {
    const fileType = this.getFileType(mimeType, fileName);
    
    switch (fileType) {
      case 'csv':
        return await this.previewCSV(filePath, fileName);
      case 'excel':
        return await this.previewExcel(filePath, fileName);
      case 'json':
        return await this.previewJSON(filePath, fileName);
      case 'txt':
        return await this.previewTXT(filePath, fileName);
      default:
        throw new Error(`Unsupported file type: ${fileType}`);
    }
  }

  /**
   * Import ไฟล์เข้า database
   */
  async importFile(options: ImportOptions): Promise<ImportResult> {
    const startTime = Date.now();
    
    try {
      console.log(`🚀 Starting import: ${options.fileName}`);
      
      // ตรวจสอบไฟล์
      if (!fs.existsSync(options.filePath)) {
        throw new Error('File not found');
      }

      const fileType = this.getFileType(options.mimeType, options.fileName);
      
      // อ่านข้อมูลจากไฟล์
      const data = await this.readFileData(options.filePath, fileType);
      
      if (!data || data.length === 0) {
        throw new Error('No data found in file');
      }

      // สร้างตารางถ้าจำเป็น
      if (options.createTable) {
        await this.createTableFromData(options.schema, options.tableName, data);
      }

      // ล้างข้อมูลถ้าจำเป็น
      if (options.truncateBeforeImport) {
        await this.truncateTable(options.schema, options.tableName);
      }

      // Import ข้อมูล
      const result = await this.insertDataInBatches(
        options.schema,
        options.tableName,
        data,
        options.batchSize,
        options.skipErrors
      );

      const executionTime = Date.now() - startTime;
      
      console.log(`✅ Import completed: ${result.successRows}/${result.totalRows} rows in ${executionTime}ms`);
      
      return {
        ...result,
        executionTime
      };

    } catch (error) {
      const executionTime = Date.now() - startTime;
      console.error(`❌ Import failed after ${executionTime}ms:`, error);
      
      return {
        success: false,
        totalRows: 0,
        successRows: 0,
        errorRows: 0,
        errors: [{
          row: 0,
          error: error instanceof Error ? error.message : 'Unknown error'
        }],
        executionTime
      };
    } finally {
      // ลบไฟล์ temporary
      try {
        if (fs.existsSync(options.filePath)) {
          fs.unlinkSync(options.filePath);
        }
      } catch (error) {
        console.warn('Failed to delete temporary file:', error);
      }
    }
  }

  /**
   * ระบุประเภทไฟล์
   */
  private getFileType(mimeType: string, fileName: string): string {
    const extension = path.extname(fileName).toLowerCase();
    
    if (mimeType === 'text/csv' || extension === '.csv') {
      return 'csv';
    }
    
    if (mimeType === 'application/vnd.ms-excel' || 
        mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        extension === '.xlsx' || extension === '.xls') {
      return 'excel';
    }
    
    if (mimeType === 'application/json' || extension === '.json') {
      return 'json';
    }
    
    if (mimeType === 'text/plain' || extension === '.txt' || extension === '.tsv') {
      return 'txt';
    }
    
    throw new Error(`Unsupported file type: ${mimeType}`);
  }

  /**
   * Preview CSV file
   */
  private async previewCSV(filePath: string, fileName: string): Promise<FilePreview> {
    return new Promise((resolve, reject) => {
      const results: any[] = [];
      let headers: string[] = [];
      let totalRows = 0;
      
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('headers', (headerList: string[]) => {
          headers = headerList.map((h: string) => h.trim());
        })
        .on('data', (data: any) => {
          totalRows++;
          if (results.length < 10) { // เก็บแค่ 10 แถวแรกสำหรับ preview
            results.push(data);
          }
        })
        .on('end', () => {
          resolve({
            headers,
            sampleData: results,
            totalRows,
            fileName,
            fileType: 'CSV',
            suggestedColumns: this.suggestColumnsFromData(headers, results)
          });
        })
        .on('error', reject);
    });
  }

  /**
   * Preview Excel file
   */
  private async previewExcel(filePath: string, fileName: string): Promise<FilePreview> {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
    
    if (jsonData.length === 0) {
      throw new Error('Empty Excel file');
    }
    
    const headers = (jsonData[0] as string[]).map(h => String(h).trim());
    const dataRows = jsonData.slice(1, 11); // เก็บ 10 แถวแรก
    
    const sampleData = dataRows.map(row => {
      const obj: any = {};
      headers.forEach((header, index) => {
        obj[header] = (row as any[])[index] || null;
      });
      return obj;
    });
    
    return {
      headers,
      sampleData,
      totalRows: jsonData.length - 1,
      fileName,
      fileType: 'Excel',
      suggestedColumns: this.suggestColumnsFromData(headers, sampleData)
    };
  }

  /**
   * Preview JSON file
   */
  private async previewJSON(filePath: string, fileName: string): Promise<FilePreview> {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    let jsonData: any[];
    
    try {
      const parsed = JSON.parse(fileContent);
      jsonData = Array.isArray(parsed) ? parsed : [parsed];
    } catch (error) {
      throw new Error('Invalid JSON format');
    }
    
    if (jsonData.length === 0) {
      throw new Error('Empty JSON file');
    }
    
    const headers = Object.keys(jsonData[0]);
    const sampleData = jsonData.slice(0, 10);
    
    return {
      headers,
      sampleData,
      totalRows: jsonData.length,
      fileName,
      fileType: 'JSON',
      suggestedColumns: this.suggestColumnsFromData(headers, sampleData)
    };
  }

  /**
   * Preview text file (Tab-separated or pipe-separated)
   */
  private async previewTXT(filePath: string, fileName: string): Promise<FilePreview> {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\n').filter(line => line.trim().length > 0);
    
    if (lines.length === 0) {
      throw new Error('Empty text file');
    }
    
    // ตรวจหา delimiter
    const delimiter = this.detectDelimiter(lines[0]);
    
    const headers = lines[0].split(delimiter).map(h => h.trim());
    const dataLines = lines.slice(1, 11); // เก็บ 10 แถวแรก
    
    const sampleData = dataLines.map(line => {
      const values = line.split(delimiter);
      const obj: any = {};
      headers.forEach((header, index) => {
        obj[header] = values[index]?.trim() || null;
      });
      return obj;
    });
    
    return {
      headers,
      sampleData,
      totalRows: lines.length - 1,
      fileName,
      fileType: 'Text',
      suggestedColumns: this.suggestColumnsFromData(headers, sampleData)
    };
  }

  /**
   * ตรวจหา delimiter ในไฟล์ text
   */
  private detectDelimiter(firstLine: string): string {
    const delimiters = ['\t', '|', ';', ','];
    let maxCount = 0;
    let bestDelimiter = '\t';
    
    for (const delimiter of delimiters) {
      const count = (firstLine.match(new RegExp(delimiter.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
      if (count > maxCount) {
        maxCount = count;
        bestDelimiter = delimiter;
      }
    }
    
    return bestDelimiter;
  }

  /**
   * แนะนำ column types จากข้อมูล
   */
  private suggestColumnsFromData(headers: string[], sampleData: any[]): DatabaseColumn[] {
    return headers.map((header, index) => {
      const values = sampleData.map(row => row[header]).filter(v => v != null && v !== '');
      const suggestedType = this.inferColumnType(values);
      
      return {
        name: this.sanitizeColumnName(header),
        type: suggestedType.type,
        length: suggestedType.length,
        isPrimary: index === 0, // สมมติว่า column แรกเป็น primary key
        isRequired: false,
        isUnique: false,
        comment: `Auto-generated from column: ${header}`
      };
    });
  }

  /**
   * คาดเดาประเภทข้อมูลจาก values
   */
  private inferColumnType(values: any[]): { type: string; length?: number } {
    if (values.length === 0) {
      return { type: 'VARCHAR', length: 255 };
    }
    
    let allNumbers = true;
    let allIntegers = true;
    let allDates = true;
    let allBooleans = true;
    let maxLength = 0;
    
    for (const value of values) {
      const str = String(value).trim();
      maxLength = Math.max(maxLength, str.length);
      
      // ตรวจสอบตัวเลข
      if (isNaN(Number(str))) {
        allNumbers = false;
        allIntegers = false;
      } else if (!Number.isInteger(Number(str))) {
        allIntegers = false;
      }
      
      // ตรวจสอบวันที่
      if (isNaN(Date.parse(str))) {
        allDates = false;
      }
      
      // ตรวจสอบ boolean
      if (!['true', 'false', '1', '0', 'yes', 'no'].includes(str.toLowerCase())) {
        allBooleans = false;
      }
    }
    
    if (allBooleans) {
      return { type: 'BOOLEAN' };
    }
    
    if (allIntegers) {
      return { type: 'INTEGER' };
    }
    
    if (allNumbers) {
      return { type: 'DECIMAL' };
    }
    
    if (allDates) {
      return { type: 'TIMESTAMP' };
    }
    
    // Default เป็น VARCHAR
    const suggestedLength = Math.max(255, Math.ceil(maxLength * 1.2));
    return { type: 'VARCHAR', length: Math.min(suggestedLength, 1000) };
  }

  /**
   * ทำความสะอาดชื่อ column
   */
  private sanitizeColumnName(name: string): string {
    return name
      .replace(/[^a-zA-Z0-9_]/g, '_')
      .replace(/^([0-9])/, '_$1')
      .toLowerCase()
      .substring(0, 63); // PostgreSQL limit
  }

  /**
   * อ่านข้อมูลจากไฟล์
   */
  private async readFileData(filePath: string, fileType: string): Promise<any[]> {
    switch (fileType) {
      case 'csv':
        return await this.readCSVData(filePath);
      case 'excel':
        return await this.readExcelData(filePath);
      case 'json':
        return await this.readJSONData(filePath);
      case 'txt':
        return await this.readTXTData(filePath);
      default:
        throw new Error(`Unsupported file type: ${fileType}`);
    }
  }

  private async readCSVData(filePath: string): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const results: any[] = [];
      
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (data: any) => results.push(data))
        .on('end', () => resolve(results))
        .on('error', reject);
    });
  }

  private async readExcelData(filePath: string): Promise<any[]> {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    return XLSX.utils.sheet_to_json(worksheet);
  }

  private async readJSONData(filePath: string): Promise<any[]> {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const parsed = JSON.parse(fileContent);
    return Array.isArray(parsed) ? parsed : [parsed];
  }

  private async readTXTData(filePath: string): Promise<any[]> {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\n').filter(line => line.trim().length > 0);
    
    if (lines.length === 0) return [];
    
    const delimiter = this.detectDelimiter(lines[0]);
    const headers = lines[0].split(delimiter).map(h => h.trim());
    
    return lines.slice(1).map(line => {
      const values = line.split(delimiter);
      const obj: any = {};
      headers.forEach((header, index) => {
        obj[header] = values[index]?.trim() || null;
      });
      return obj;
    });
  }

  /**
   * สร้างตารางจากข้อมูล
   */
  private async createTableFromData(schema: string, tableName: string, data: any[]): Promise<void> {
    if (data.length === 0) {
      throw new Error('Cannot create table from empty data');
    }
    
    const headers = Object.keys(data[0]);
    const suggestedColumns = this.suggestColumnsFromData(headers, data.slice(0, 100));
    
    await this.dbService.createTable({
      companyCode: '', // Will be handled by the service
      schema,
      tableName,
      description: `Auto-created table for imported data`,
      columns: suggestedColumns,
      ifNotExists: true
    });
  }

  /**
   * ล้างข้อมูลในตาราง
   */
  private async truncateTable(schema: string, tableName: string): Promise<void> {
    // ใช้ DatabaseService internal pool
    const pool = (this.dbService as any).pool;
    await pool.query(`TRUNCATE TABLE "${schema}"."${tableName}" RESTART IDENTITY;`);
  }

  /**
   * Insert ข้อมูลแบบ batch
   */
  private async insertDataInBatches(
    schema: string,
    tableName: string,
    data: any[],
    batchSize: number,
    skipErrors: boolean
  ): Promise<ImportResult> {
    const pool = (this.dbService as any).pool;
    const totalRows = data.length;
    let successRows = 0;
    let errorRows = 0;
    const errors: Array<{ row: number; column?: string; error: string; data?: any }> = [];
    
    if (data.length === 0) {
      return { success: true, totalRows: 0, successRows: 0, errorRows: 0, errors: [], executionTime: 0 };
    }
    
    const columns = Object.keys(data[0]);
    const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
    const columnNames = columns.map(col => `"${col}"`).join(', ');
    
    const insertSQL = `INSERT INTO "${schema}"."${tableName}" (${columnNames}) VALUES (${placeholders})`;
    
    for (let i = 0; i < data.length; i += batchSize) {
      const batch = data.slice(i, i + batchSize);
      
      for (let j = 0; j < batch.length; j++) {
        const rowIndex = i + j + 1;
        const row = batch[j];
        
        try {
          const values = columns.map(col => row[col] === '' ? null : row[col]);
          await pool.query(insertSQL, values);
          successRows++;
        } catch (error) {
          errorRows++;
          errors.push({
            row: rowIndex,
            error: error instanceof Error ? error.message : 'Unknown error',
            data: row
          });
          
          if (!skipErrors) {
            throw new Error(`Import failed at row ${rowIndex}: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
      }
      
      // Progress log
      console.log(`📊 Progress: ${Math.min(i + batchSize, data.length)}/${data.length} rows processed`);
    }
    
    return {
      success: errorRows === 0 || skipErrors,
      totalRows,
      successRows,
      errorRows,
      errors,
      executionTime: 0 // Will be set by the caller
    };
  }
}