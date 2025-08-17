// pages/api/analyze-file.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../lib/auth';
import multer from 'multer';
import * as XLSX from 'xlsx';
import csv from 'csv-parser';
import { createReadStream } from 'fs';
import { promises as fs } from 'fs';

// Configure multer for file upload
const upload = multer({
  dest: 'uploads/',
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
  },
});

// Disable Next.js body parser for this route
export const config = {
  api: {
    bodyParser: false,
  },
};

function runMiddleware(req: any, res: any, fn: any) {
  return new Promise((resolve, reject) => {
    fn(req, res, (result: any) => {
      if (result instanceof Error) {
        return reject(result);
      }
      return resolve(result);
    });
  });
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session?.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Run multer middleware
    await runMiddleware(req, res, upload.single('file'));

    const { file } = req as any;

    if (!file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    console.log(`📁 Analyzing file: ${file.originalname}`);

    // Analyze file based on type
    const fileExtension = file.originalname.split('.').pop()?.toLowerCase();
    let analysis: any;

    switch (fileExtension) {
      case 'csv':
        analysis = await analyzeCsvFile(file.path, file.originalname);
        break;
      case 'xlsx':
      case 'xls':
        analysis = await analyzeExcelFile(file.path, file.originalname);
        break;
      case 'json':
        analysis = await analyzeJsonFile(file.path, file.originalname);
        break;
      default:
        throw new Error(`Unsupported file type: ${fileExtension}`);
    }

    // Clean up uploaded file
    await fs.unlink(file.path);

    console.log(`✅ File analysis complete: ${analysis.detectedColumns.length} columns detected`);

    res.status(200).json({
      success: true,
      ...analysis
    });

  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('❌ Error analyzing file:', errorMessage);
    res.status(500).json({ 
      error: 'Failed to analyze file',
      details: errorMessage 
    });
  }
}

// Add interface for better type safety
interface DetectedColumn {
  name: string;
  type: string;
  length?: number;
  isPrimary: boolean;
  isRequired: boolean;
  isUnique: boolean;
  inferredType: string;
  sampleData: any[];
  originalName: string;
}

async function analyzeCsvFile(filePath: string, fileName: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const results: any[] = [];
    let headers: string[] = [];
    
    createReadStream(filePath)
      .pipe(csv())
      .on('headers', (headerList) => {
        headers = headerList;
      })
      .on('data', (data) => {
        if (results.length < 100) { // Sample first 100 rows for analysis
          results.push(data);
        }
      })
      .on('end', () => {
        try {
          const analysis = analyzeDataStructure(results, fileName, 'csv');
          resolve(analysis);
        } catch (error) {
          reject(error);
        }
      })
      .on('error', reject);
  });
}

async function analyzeExcelFile(filePath: string, fileName: string): Promise<any> {
  const workbook = XLSX.readFile(filePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { raw: false });
  
  return analyzeDataStructure(jsonData, fileName, 'excel');
}

async function analyzeJsonFile(filePath: string, fileName: string): Promise<any> {
  const content = await fs.readFile(filePath, 'utf8');
  const jsonData = JSON.parse(content);
  
  const dataArray = Array.isArray(jsonData) ? jsonData : [jsonData];
  
  return analyzeDataStructure(dataArray, fileName, 'json');
}

function analyzeDataStructure(data: any[], fileName: string, fileType: string) {
  if (data.length === 0) {
    throw new Error('ไฟล์ไม่มีข้อมูล');
  }

  const sampleRow = data[0];
  const columns = Object.keys(sampleRow);
  
  const detectedColumns: DetectedColumn[] = columns.map((columnName, index) => {
    const columnData = data.map(row => row[columnName]).filter(val => val != null && val !== '' && val !== 'null');
    
    const inferredType = inferColumnType(columnData);
    const sampleData = columnData.slice(0, 5);
    
    // Better primary key detection
    const isPrimaryKey = (
      // First column with 'id' in name
      (columnName.toLowerCase().includes('id') && index === 0) ||
      // Column named exactly 'id'
      columnName.toLowerCase() === 'id' ||
      // Sequential numbers starting from 1
      (inferredType.primaryType === 'INTEGER' && 
       columnData.length > 1 && 
       columnData.every((val, i) => Number(val) === i + 1))
    );
    
    // If it's a primary key, ensure it's required and unique
    const isRequired = isPrimaryKey || inferredType.hasValues > data.length * 0.8; // 80% non-null
    const isUnique = isPrimaryKey;
    
    return {
      name: sanitizeColumnName(columnName),
      type: inferredType.primaryType,
      length: inferredType.length,
      isPrimary: isPrimaryKey,
      isRequired: isRequired,
      isUnique: isUnique,
      inferredType: inferredType.primaryType,
      sampleData: sampleData,
      originalName: columnName // Keep original for debugging
    };
  });

  // Ensure we have at least one primary key
  const hasPrimaryKey = detectedColumns.some(col => col.isPrimary);
  if (!hasPrimaryKey && detectedColumns.length > 0) {
    // Make first column primary key if it's INTEGER
    const firstCol = detectedColumns[0];
    if (firstCol.type === 'INTEGER') {
      firstCol.isPrimary = true;
      firstCol.isRequired = true;
      firstCol.isUnique = true;
    } else {
      // Add an ID column
      detectedColumns.unshift({
        name: 'id',
        type: 'SERIAL',
        length: undefined,
        isPrimary: true,
        isRequired: true,
        isUnique: true,
        inferredType: 'SERIAL',
        sampleData: [],
        originalName: 'id'
      });
    }
  }

  console.log('🔍 Detected columns:', detectedColumns.map(col => `${col.name} (${col.type})`));

  return {
    fileName,
    fileType,
    totalRows: data.length,
    detectedColumns,
    sampleData: data.slice(0, 5),
    encoding: 'UTF-8'
  };
}

function inferColumnType(values: any[]) {
  if (values.length === 0) {
    return { primaryType: 'TEXT', length: undefined, hasValues: 0 };
  }

  const nonEmptyValues = values.filter(val => val != null && val !== '' && val !== 'null');
  const hasValues = nonEmptyValues.length;
  
  if (hasValues === 0) {
    return { primaryType: 'TEXT', length: undefined, hasValues: 0 };
  }
  
  // Check for different data types
  let isInteger = true;
  let isDecimal = true;
  let isBoolean = true;
  let isDate = true;
  let isTimestamp = true;
  let maxLength = 0;

  for (const value of nonEmptyValues) {
    const strValue = String(value).trim();
    maxLength = Math.max(maxLength, strValue.length);

    // Check integer (must be whole numbers only)
    if (isInteger) {
      const num = Number(strValue);
      if (isNaN(num) || !Number.isInteger(num) || strValue.includes('.')) {
        isInteger = false;
      }
    }

    // Check decimal (any valid number)
    if (isDecimal && isNaN(Number(strValue))) {
      isDecimal = false;
    }

    // Check boolean (strict checking)
    if (isBoolean) {
      const lowerVal = strValue.toLowerCase();
      if (!['true', 'false', '1', '0', 'yes', 'no', 'y', 'n'].includes(lowerVal)) {
        isBoolean = false;
      }
    }

    // Check timestamp (has both date and time)
    if (isTimestamp) {
      const dateVal = new Date(strValue);
      if (isNaN(dateVal.getTime()) || !strValue.includes(':')) {
        isTimestamp = false;
      }
    }

    // Check date (date format without time)
    if (isDate) {
      const dateVal = new Date(strValue);
      if (isNaN(dateVal.getTime()) || strValue.includes(':')) {
        isDate = false;
      }
    }
  }

  // Determine primary type with better logic
  let primaryType = 'VARCHAR';
  let length = undefined;

  if (isBoolean) {
    primaryType = 'BOOLEAN';
  } else if (isInteger) {
    // Check if values are small enough for INTEGER
    const maxVal = Math.max(...nonEmptyValues.map(v => Math.abs(Number(v))));
    primaryType = maxVal > 2147483647 ? 'BIGINT' : 'INTEGER';
  } else if (isDecimal && !isInteger) {
    primaryType = 'DECIMAL';
  } else if (isTimestamp) {
    primaryType = 'TIMESTAMP';
  } else if (isDate) {
    primaryType = 'DATE';
  } else {
    // String types
    if (maxLength > 1000) {
      primaryType = 'TEXT';
    } else {
      primaryType = 'VARCHAR';
      length = Math.max(255, Math.ceil(maxLength * 1.5)); // Add 50% buffer
    }
  }

  return { primaryType, length, hasValues };
}

function sanitizeColumnName(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9_]/g, '_')
    .replace(/^[0-9]/, '_$&')
    .toLowerCase();
}