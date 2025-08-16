import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { 
  Database, Plus, Table, Upload, History, Search,
  RefreshCw, Layout, ArrowLeft, AlertCircle, Check,
  FileText, Download, Settings, Eye, Trash2,
  Save, Copy, Filter, BarChart3, Zap, FileSpreadsheet,
  CheckCircle, XCircle, Edit, Brain, Sparkles
} from 'lucide-react';
import { X } from "lucide-react";

// ============================================================================
// TYPES & INTERFACES
// ============================================================================
interface Company {
  code: string;
  name: string;
  dbName: string;
}

interface Schema {
  name: string;
  type: 'default' | 'custom';
  description?: string;
  tables: string[];
  createdAt: string;
}

interface Column {
  name: string;
  type: string;
  length?: number;
  isPrimary: boolean;
  isRequired: boolean;
  isUnique: boolean;
  defaultValue: string;
  references?: { table: string; column: string };
  detectedType?: string;
  confidence?: number;
  sampleValues?: string[];
}

interface ImportFile {
  file: File | null;
  name: string;
  type: string;
  size: number;
}

interface FileAnalysis {
  totalRows: number;
  hasHeader: boolean;
  detectedColumns: Column[];
  sampleData: any[];
  encoding: string;
  delimiter?: string;
  confidence: number;
}

interface CreateTableMode {
  type: 'manual' | 'from-file' | 'existing-structure';
  fileAnalysis?: FileAnalysis;
}

// ============================================================================
// CUSTOM HOOKS
// ============================================================================
const useNotification = () => {
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | ''; text: string }>({ type: '', text: '' });

  const showSuccess = (text: string) => setMessage({ type: 'success', text });
  const showError = (text: string) => setMessage({ type: 'error', text });
  const showInfo = (text: string) => setMessage({ type: 'info', text });
  const clear = () => setMessage({ type: '', text: '' });

  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(clear, 5000);
      return () => clearTimeout(timer);
    }
  }, [message.text]);

  return { message, showSuccess, showError, showInfo, clear };
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================
const EnhancedTableManagement: React.FC = () => {
  const { data: session, status } = useSession();
  
  // State Management
  const [currentView, setCurrentView] = useState<'overview' | 'create-table' | 'create-schema' | 'import-wizard'>('overview');
  const [currentCompany] = useState<Company>({
    code: 'company_a',
    name: 'SiamTech Solutions',
    dbName: 'siamtech_company_a'
  });
  
  // ============================================================================
  // PERSISTENT DATA MANAGEMENT
  // ============================================================================
  const STORAGE_KEY = `schemas_${currentCompany.code}`;

  // Load schemas from localStorage
  const loadSchemasFromStorage = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsedSchemas = JSON.parse(stored);
        // Always ensure public schema exists
        const hasPublic = parsedSchemas.some((s: Schema) => s.name === 'public');
        if (!hasPublic) {
          parsedSchemas.unshift({
            name: 'public',
            type: 'default',
            description: 'Default PostgreSQL schema',
            tables: [],
            createdAt: '2024-01-01'
          });
        }
        return parsedSchemas;
      }
    } catch (error) {
      console.error('Error loading schemas from storage:', error);
    }
    
    // Default schemas if nothing in storage
    return [
      { 
        name: 'public', 
        type: 'default', 
        description: 'Default PostgreSQL schema',
        tables: [], 
        createdAt: '2024-01-01' 
      }
    ];
  };

  // Save schemas to localStorage
  const saveSchemasToStorage = (schemas: Schema[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(schemas));
    } catch (error) {
      console.error('Error saving schemas to storage:', error);
      showError('ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่');
    }
  };

  // Initialize schemas from storage
  const [schemas, setSchemas] = useState<Schema[]>(() => loadSchemasFromStorage());

  const [loading, setLoading] = useState(false);
  const [createMode, setCreateMode] = useState<CreateTableMode>({ type: 'manual' });
  
  // Schema Creation States
  const [newSchema, setNewSchema] = useState({ name: '', description: '' });
  
  // File Analysis States
  const [selectedFile, setSelectedFile] = useState<ImportFile>({
    file: null, name: '', type: '', size: 0
  });
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Table Creation States - Dynamic schema selection
  const [newTable, setNewTable] = useState({
    name: '',
    description: '',
    schema: 'public',
    createAndImport: false,
    columns: [{ 
      name: 'id', 
      type: 'SERIAL', 
      isPrimary: true, 
      isRequired: true, 
      isUnique: false, 
      defaultValue: '' 
    }] as Column[]
  });

  const { message, showSuccess, showError, showInfo, clear } = useNotification();

  const dataTypes = [
    'SERIAL', 'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC',
    'VARCHAR', 'TEXT', 'CHAR', 'BOOLEAN', 
    'DATE', 'TIME', 'TIMESTAMP', 'TIMESTAMPTZ',
    'JSON', 'JSONB', 'UUID', 'ARRAY'
  ];

  // ============================================================================
  // DYNAMIC DATA LOADING
  // ============================================================================
  const loadSchemasFromDatabase = async () => {
    try {
      const response = await fetch(`/api/schema/list-schemas?companyCode=${currentCompany.code}`);
      const result = await response.json();

      if (response.ok && result.success) {
        return result.schemas;
      } else {
        console.warn('Failed to load schemas from database:', result.error);
        return null;
      }
    } catch (error) {
      console.error('Error loading schemas from database:', error);
      return null;
    }
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Try to load from database first
      const dbSchemas = await loadSchemasFromDatabase();
      
      if (dbSchemas) {
        // Use database data and save to localStorage
        setSchemas(dbSchemas);
        saveSchemasToStorage(dbSchemas);
        showSuccess(`โหลดข้อมูลจากฐานข้อมูลสำเร็จ! พบ ${dbSchemas.length} schemas`);
      } else {
        // Fallback to localStorage
        const storedSchemas = loadSchemasFromStorage();
        setSchemas(storedSchemas);
        showInfo('โหลดข้อมูลจาก localStorage (ออฟไลน์)');
      }

    } catch (error) {
      showError('เกิดข้อผิดพลาดในการโหลดข้อมูล');
      // Final fallback
      const storedSchemas = loadSchemasFromStorage();
      setSchemas(storedSchemas);
    } finally {
      setLoading(false);
    }
  };

  // Update schemas with persistence
  const updateSchemas = (newSchemas: Schema[]) => {
    setSchemas(newSchemas);
    saveSchemasToStorage(newSchemas);
  };

  // Load data on component mount
  useEffect(() => {
    // Load from storage first
    const storedSchemas = loadSchemasFromStorage();
    setSchemas(storedSchemas);
    
    // Then load additional sample data if needed (optional)
    loadInitialData();
  }, []);

  // ============================================================================
  // FILE ANALYSIS FUNCTIONS
  // ============================================================================
  const analyzeDataType = (values: any[]): { type: string; confidence: number; length?: number } => {
    if (!values || values.length === 0) return { type: 'TEXT', confidence: 0.5 };

    const nonEmptyValues = values.filter(v => v !== null && v !== undefined && v !== '');
    if (nonEmptyValues.length === 0) return { type: 'TEXT', confidence: 0.3 };

    let integerCount = 0;
    let decimalCount = 0;
    let dateCount = 0;
    let booleanCount = 0;
    let maxLength = 0;

    nonEmptyValues.forEach(value => {
      const str = String(value).trim();
      maxLength = Math.max(maxLength, str.length);

      // Integer check
      if (/^-?\d+$/.test(str)) {
        integerCount++;
      }
      // Decimal check
      else if (/^-?\d+\.\d+$/.test(str)) {
        decimalCount++;
      }
      // Date check
      else if (!isNaN(Date.parse(str)) && str.length > 8) {
        dateCount++;
      }
      // Boolean check
      else if (/^(true|false|yes|no|1|0)$/i.test(str)) {
        booleanCount++;
      }
    });

    const total = nonEmptyValues.length;
    const threshold = 0.8; // 80% confidence

    if (integerCount / total >= threshold) {
      const maxVal = Math.max(...nonEmptyValues.map(v => parseInt(v)));
      return { 
        type: maxVal > 2147483647 ? 'BIGINT' : 'INTEGER', 
        confidence: integerCount / total 
      };
    }

    if ((integerCount + decimalCount) / total >= threshold) {
      return { type: 'DECIMAL', confidence: (integerCount + decimalCount) / total };
    }

    if (dateCount / total >= threshold) {
      return { type: 'TIMESTAMP', confidence: dateCount / total };
    }

    if (booleanCount / total >= threshold) {
      return { type: 'BOOLEAN', confidence: booleanCount / total };
    }

    // Default to VARCHAR with appropriate length
    const suggestedLength = Math.min(Math.max(maxLength * 1.5, 50), 500);
    return { 
      type: 'VARCHAR', 
      confidence: 0.7,
      length: Math.ceil(suggestedLength / 50) * 50 // Round to nearest 50
    };
  };

  const analyzeCSVFile = async (file: File): Promise<FileAnalysis> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          const lines = text.split('\n').filter(line => line.trim());
          
          if (lines.length === 0) {
            throw new Error('ไฟล์ว่างเปล่า');
          }

          // Detect delimiter
          const firstLine = lines[0];
          const delimiters = [',', ';', '\t', '|'];
          let bestDelimiter = ',';
          let maxColumns = 0;

          delimiters.forEach(delimiter => {
            const columns = firstLine.split(delimiter).length;
            if (columns > maxColumns) {
              maxColumns = columns;
              bestDelimiter = delimiter;
            }
          });

          // Parse data
          const rows = lines.map(line => line.split(bestDelimiter));
          const hasHeader = isNaN(Number(rows[0][0])) || rows[0].some(cell => /[a-zA-Z]/.test(cell));
          
          const headerRow = hasHeader ? rows[0] : rows[0].map((_, i) => `column_${i + 1}`);
          const dataRows = hasHeader ? rows.slice(1, Math.min(rows.length, 101)) : rows.slice(0, 100);

          // Analyze each column
          const detectedColumns: Column[] = headerRow.map((header, index) => {
            const columnData = dataRows.map(row => row[index]);
            const analysis = analyzeDataType(columnData);
            
            return {
              name: header.toLowerCase().replace(/[^a-z0-9_]/g, '_'),
              type: analysis.type,
              length: analysis.length,
              isPrimary: false,
              isRequired: false,
              isUnique: false,
              defaultValue: '',
              detectedType: analysis.type,
              confidence: analysis.confidence,
              sampleValues: columnData.slice(0, 3).filter(v => v)
            };
          });

          // Set primary key if there's an ID column
          const idColumn = detectedColumns.find(col => 
            col.name.toLowerCase().includes('id') && 
            col.type === 'INTEGER'
          );
          if (idColumn) {
            idColumn.isPrimary = true;
            idColumn.isRequired = true;
            idColumn.type = 'SERIAL';
          }

          resolve({
            totalRows: lines.length - (hasHeader ? 1 : 0),
            hasHeader,
            detectedColumns,
            sampleData: dataRows.slice(0, 5).map(row => {
              const obj: any = {};
              headerRow.forEach((header, i) => {
                obj[header] = row[i] || '';
              });
              return obj;
            }),
            encoding: 'UTF-8',
            delimiter: bestDelimiter,
            confidence: detectedColumns.reduce((sum, col) => sum + (col.confidence || 0), 0) / detectedColumns.length
          });

        } catch (error) {
          reject(error);
        }
      };
      reader.readAsText(file);
    });
  };

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile({
      file,
      name: file.name,
      type: file.type,
      size: file.size
    });

    if (createMode.type === 'from-file') {
      setIsAnalyzing(true);
      try {
        const analysis = await analyzeCSVFile(file);
        setFileAnalysis(analysis);
        
        // Update table columns with detected structure
        setNewTable(prev => ({
          ...prev,
          name: file.name.split('.')[0].toLowerCase().replace(/[^a-z0-9_]/g, '_'),
          columns: analysis.detectedColumns,
          createAndImport: true
        }));

        showSuccess(`วิเคราะห์ไฟล์สำเร็จ! พบ ${analysis.detectedColumns.length} columns จาก ${analysis.totalRows} rows`);
      } catch (error) {
        showError(`เกิดข้อผิดพลาด: ${error instanceof Error ? error.message : 'ไม่สามารถวิเคราะห์ไฟล์ได้'}`);
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  const handleCreateTable = async () => {
    if (!newTable.name.trim()) {
      showError('กรุณาใส่ชื่อตาราง');
      return;
    }

    if (newTable.columns.some(col => !col.name.trim())) {
      showError('กรุณาใส่ชื่อ Column ให้ครบถ้วน');
      return;
    }

    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));

      if (newTable.createAndImport && selectedFile.file) {
        showSuccess(`สร้างตาราง "${newTable.name}" และนำเข้าข้อมูล ${fileAnalysis?.totalRows} แถวสำเร็จ!`);
      } else {
        showSuccess(`สร้างตาราง "${newTable.name}" สำเร็จ!`);
      }
      
      // Reset form
      setNewTable({
        name: '',
        description: '',
        schema: 'public',
        createAndImport: false,
        columns: [{ 
          name: 'id', 
          type: 'SERIAL', 
          isPrimary: true, 
          isRequired: true, 
          isUnique: false, 
          defaultValue: '' 
        }]
      });
      
      setSelectedFile({ file: null, name: '', type: '', size: 0 });
      setFileAnalysis(null);
      setCreateMode({ type: 'manual' });
      
    } catch (error) {
      showError('เกิดข้อผิดพลาดในการสร้างตาราง');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchema = async () => {
    if (!newSchema.name.trim()) {
      showError('กรุณาใส่ชื่อ Schema');
      return;
    }

    // Check if schema already exists
    const schemaExists = schemas.some(schema => 
      schema.name.toLowerCase() === newSchema.name.trim().toLowerCase()
    );
    
    if (schemaExists) {
      showError(`Schema "${newSchema.name}" มีอยู่แล้วในระบบ`);
      return;
    }

    setLoading(true);
    try {
      // Call real API to create schema in database
      const response = await fetch('/api/schema/create-schema', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newSchema.name.trim(),
          description: newSchema.description,
          companyCode: currentCompany.code
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to create schema');
      }
      
      // Add new schema to the list
      const newSchemaObj: Schema = {
        name: newSchema.name.trim(),
        type: 'custom',
        description: newSchema.description,
        tables: [],
        createdAt: new Date().toISOString().split('T')[0]
      };
      
      const updatedSchemas = [...schemas, newSchemaObj];
      updateSchemas(updatedSchemas);
      showSuccess(`สร้าง Schema "${newSchema.name}" ในฐานข้อมูลสำเร็จ! 🎉`);
      setNewSchema({ name: '', description: '' });
      
    } catch (error) {
      showError(`เกิดข้อผิดพลาด: ${error instanceof Error ? error.message : 'ไม่สามารถสร้าง Schema ได้'}`);
    } finally {
      setLoading(false);
    }
  };

  const updateColumn = (index: number, field: keyof Column, value: any) => {
    setNewTable(prev => ({
      ...prev,
      columns: prev.columns.map((col, i) => 
        i === index ? { ...col, [field]: value } : col
      )
    }));
  };

  const addColumn = () => {
    setNewTable(prev => ({
      ...prev,
      columns: [
        ...prev.columns,
        { 
          name: '', 
          type: 'VARCHAR', 
          length: 100,
          isPrimary: false, 
          isRequired: false, 
          isUnique: false,
          defaultValue: ''
        }
      ]
    }));
  };

  const removeColumn = (index: number) => {
    if (newTable.columns.length > 1) {
      setNewTable(prev => ({
        ...prev,
        columns: prev.columns.filter((_, i) => i !== index)
      }));
    }
  };

  const generateSQL = () => {
    const tableName = newTable.name;
    const columns = newTable.columns.map(col => {
      let def = `  ${col.name} ${col.type}`;
      
      if (col.type === 'VARCHAR' && col.length) def += `(${col.length})`;
      if (col.isPrimary) def += ' PRIMARY KEY';
      if (col.isRequired && !col.isPrimary) def += ' NOT NULL';
      if (col.isUnique && !col.isPrimary) def += ' UNIQUE';
      if (col.defaultValue && !col.isPrimary) def += ` DEFAULT ${col.defaultValue}`;
      
      return def;
    }).join(',\n');

    return `CREATE TABLE ${newTable.schema}.${tableName} (\n${columns}\n);`;
  };

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================
  const getTotalTables = () => {
    return schemas.reduce((total, schema) => total + schema.tables.length, 0);
  };

  const getSchemaStats = () => {
    const defaultSchemas = schemas.filter(s => s.type === 'default').length;
    const customSchemas = schemas.filter(s => s.type === 'custom').length;
    return { defaultSchemas, customSchemas, totalTables: getTotalTables() };
  };

  const deleteSchema = async (schemaName: string) => {
    if (schemaName === 'public') {
      showError('ไม่สามารถลบ Schema "public" ได้');
      return;
    }

    const schema = schemas.find(s => s.name === schemaName);
    if (schema && schema.tables.length > 0) {
      showError(`ไม่สามารถลบ Schema "${schemaName}" ได้ เนื่องจากมีตาราง ${schema.tables.length} ตาราง`);
      return;
    }

    if (!confirm(`คุณต้องการลบ Schema "${schemaName}" หรือไม่? การดำเนินการนี้ไม่สามารถย้อนกลับได้`)) {
      return;
    }

    setLoading(true);
    try {
      // Call real API to delete schema from database
      const response = await fetch('/api/schema/drop-schema', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          companyCode: currentCompany.code,
          schemaName: schemaName,
          cascade: false
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete schema');
      }

      const updatedSchemas = schemas.filter(s => s.name !== schemaName);
      updateSchemas(updatedSchemas);
      showSuccess(`ลบ Schema "${schemaName}" จากฐานข้อมูลสำเร็จ! 🗑️`);
    } catch (error) {
      showError(`เกิดข้อผิดพลาด: ${error instanceof Error ? error.message : 'ไม่สามารถลบ Schema ได้'}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteTable = async (schemaName: string, tableName: string) => {
    if (!confirm(`คุณต้องการลบตาราง "${tableName}" จาก Schema "${schemaName}" หรือไม่?\nการดำเนินการนี้จะลบข้อมูลทั้งหมดในตารางและไม่สามารถย้อนกลับได้`)) {
      return;
    }

    setLoading(true);
    try {
      // Call real API to drop table from database
      const response = await fetch('/api/schema/drop-table', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          companyCode: currentCompany.code,
          tableName: tableName,
          schema: schemaName
        }),
      });

      if (response.ok) {
        const updatedSchemas = schemas.map(schema => 
          schema.name === schemaName 
            ? { ...schema, tables: schema.tables.filter(t => t !== tableName) }
            : schema
        );
        updateSchemas(updatedSchemas);
        showSuccess(`ลบตาราง "${tableName}" จากฐานข้อมูลสำเร็จ! 🗑️`);
      } else {
        const result = await response.json();
        throw new Error(result.error || 'Failed to delete table');
      }
    } catch (error) {
      showError(`เกิดข้อผิดพลาด: ${error instanceof Error ? error.message : 'ไม่สามารถลบตารางได้'}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // RENDER METHODS
  // ============================================================================
  const renderCreateModeSelector = () => (
    <div className="bg-gray-50 rounded-lg p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">เลือกวิธีการสร้างตาราง</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setCreateMode({ type: 'manual' })}
          className={`p-4 rounded-lg border-2 transition-all ${
            createMode.type === 'manual' 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <Edit className="h-8 w-8 text-gray-600 mx-auto mb-2" />
          <div className="font-medium">สร้างเอง</div>
          <div className="text-sm text-gray-500 mt-1">กำหนด columns แบบ manual</div>
        </button>

        <button
          onClick={() => setCreateMode({ type: 'from-file' })}
          className={`p-4 rounded-lg border-2 transition-all ${
            createMode.type === 'from-file' 
              ? 'border-green-500 bg-green-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <Brain className="h-8 w-8 text-gray-600 mx-auto mb-2" />
          <div className="font-medium">วิเคราะห์จากไฟล์</div>
          <div className="text-sm text-gray-500 mt-1">Auto-detect จาก CSV/Excel</div>
        </button>

        <button
          onClick={() => setCreateMode({ type: 'existing-structure' })}
          className={`p-4 rounded-lg border-2 transition-all ${
            createMode.type === 'existing-structure' 
              ? 'border-purple-500 bg-purple-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <Copy className="h-8 w-8 text-gray-600 mx-auto mb-2" />
          <div className="font-medium">คัดลอกจากตารางอื่น</div>
          <div className="text-sm text-gray-500 mt-1">ใช้โครงสร้างที่มีอยู่</div>
        </button>
      </div>
    </div>
  );

  const renderFileAnalysisSection = () => {
    if (createMode.type !== 'from-file') return null;

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <FileSpreadsheet className="h-5 w-5 mr-2" />
          อัพโหลดไฟล์เพื่อวิเคราะห์โครงสร้าง
        </h3>

        {!selectedFile.file ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <div className="text-lg font-medium text-gray-600 mb-2">
              ลากไฟล์มาวาง หรือ คลิกเพื่อเลือกไฟล์
            </div>
            <div className="text-sm text-gray-500 mb-4">
              รองรับ CSV, Excel (.xlsx, .xls) ขนาดไม่เกิน 10MB
            </div>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer"
            >
              <Upload className="h-4 w-4 mr-2" />
              เลือกไฟล์
            </label>
          </div>
        ) : (
          <div className="space-y-4">
            {/* File Info */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <FileSpreadsheet className="h-8 w-8 text-green-600 mr-3" />
                <div>
                  <div className="font-medium">{selectedFile.name}</div>
                  <div className="text-sm text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedFile({ file: null, name: '', type: '', size: 0 });
                  setFileAnalysis(null);
                }}
                className="text-red-500 hover:text-red-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Analysis Loading */}
            {isAnalyzing && (
              <div className="text-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                <div className="text-lg font-medium">กำลังวิเคราะห์ไฟล์...</div>
                <div className="text-sm text-gray-500">กรุณารอสักครู่</div>
              </div>
            )}

            {/* Analysis Results */}
            {fileAnalysis && !isAnalyzing && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    <span className="font-medium text-green-800">วิเคราะห์ไฟล์สำเร็จ</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">จำนวนแถว:</span>
                      <span className="font-medium ml-2">{fileAnalysis.totalRows.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Columns:</span>
                      <span className="font-medium ml-2">{fileAnalysis.detectedColumns.length}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Header:</span>
                      <span className="font-medium ml-2">{fileAnalysis.hasHeader ? 'มี' : 'ไม่มี'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">ความแม่นยำ:</span>
                      <span className="font-medium ml-2">{Math.round(fileAnalysis.confidence * 100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Sample Data Preview */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">ตัวอย่างข้อมูล (5 แถวแรก)</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(fileAnalysis.sampleData[0] || {}).map(key => (
                            <th key={key} className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {fileAnalysis.sampleData.map((row, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            {Object.values(row).map((value, i) => (
                              <td key={i} className="px-4 py-2 text-sm text-gray-600 border-b">
                                {String(value)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderColumnEditor = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {createMode.type === 'from-file' ? 'ตรวจสอบและแก้ไข Columns' : 'กำหนด Columns'}
        </h3>
        <button
          onClick={addColumn}
          className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          เพิ่ม Column
        </button>
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {newTable.columns.map((column, index) => (
          <div key={index} className="grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 bg-gray-50 rounded-lg">
            {/* Column Name */}
            <div className="lg:col-span-3">
              <label className="block text-xs font-medium text-gray-700 mb-1">ชื่อ Column</label>
              <input
                type="text"
                value={column.name}
                onChange={(e) => updateColumn(index, 'name', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                placeholder="column_name"
              />
            </div>

            {/* Data Type */}
            <div className="lg:col-span-2">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                ชนิดข้อมูล
                {column.detectedType && (
                  <span className="ml-1 text-green-600 text-xs">
                    (แนะนำ: {column.detectedType})
                  </span>
                )}
              </label>
              <select
                value={column.type}
                onChange={(e) => updateColumn(index, 'type', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
              >
                {dataTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {/* Length */}
            {column.type === 'VARCHAR' && (
              <div className="lg:col-span-1">
                <label className="block text-xs font-medium text-gray-700 mb-1">Length</label>
                <input
                  type="number"
                  value={column.length || ''}
                  onChange={(e) => updateColumn(index, 'length', parseInt(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                  placeholder="100"
                />
              </div>
            )}

            {/* Constraints */}
            <div className="lg:col-span-4 space-y-2">
              <label className="block text-xs font-medium text-gray-700">Constraints</label>
              <div className="flex flex-wrap gap-2">
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={column.isPrimary}
                    onChange={(e) => updateColumn(index, 'isPrimary', e.target.checked)}
                    className="mr-1"
                  />
                  Primary
                </label>
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={column.isRequired}
                    onChange={(e) => updateColumn(index, 'isRequired', e.target.checked)}
                    className="mr-1"
                  />
                  Required
                </label>
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={column.isUnique}
                    onChange={(e) => updateColumn(index, 'isUnique', e.target.checked)}
                    className="mr-1"
                  />
                  Unique
                </label>
              </div>
            </div>

            {/* Sample Values */}
            {column.sampleValues && column.sampleValues.length > 0 && (
              <div className="lg:col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">ตัวอย่างข้อมูล</label>
                <div className="text-xs text-gray-500">
                  {column.sampleValues.slice(0, 2).map((val, i) => (
                    <div key={i} className="truncate">{String(val)}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="lg:col-span-1 flex items-end">
              <button
                onClick={() => removeColumn(index)}
                disabled={newTable.columns.length === 1}
                className="p-2 text-red-500 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* SQL Preview */}
      <div className="mt-6">
        <h4 className="font-medium text-gray-900 mb-2">SQL Preview</h4>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
          <pre>{generateSQL()}</pre>
        </div>
      </div>
    </div>
  );

  const renderCreateTable = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Smart Table Creator</h2>
          <p className="text-gray-600 mt-1">สร้างตารางใหม่ด้วย AI-powered analysis</p>
        </div>
        <button
          onClick={() => setCurrentView('overview')}
          className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          กลับ
        </button>
      </div>

      {/* Mode Selector */}
      {renderCreateModeSelector()}

      {/* File Analysis Section */}
      {renderFileAnalysisSection()}

      {/* Table Basic Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">ข้อมูลพื้นฐานของตาราง</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ชื่อตาราง *</label>
            <input
              type="text"
              value={newTable.name}
              onChange={(e) => setNewTable(prev => ({ ...prev, name: e.target.value }))}
              placeholder="เช่น products, customers"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Schema</label>
            <select
              value={newTable.schema}
              onChange={(e) => setNewTable(prev => ({ ...prev, schema: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              {schemas.map(schema => (
                <option key={schema.name} value={schema.name}>{schema.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">คำอธิบาย</label>
            <input
              type="text"
              value={newTable.description}
              onChange={(e) => setNewTable(prev => ({ ...prev, description: e.target.value }))}
              placeholder="คำอธิบายตาราง"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Import Option */}
        {createMode.type === 'from-file' && selectedFile.file && fileAnalysis && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={newTable.createAndImport}
                onChange={(e) => setNewTable(prev => ({ ...prev, createAndImport: e.target.checked }))}
                className="mr-3"
              />
              <div>
                <span className="font-medium text-blue-800">สร้างตารางและนำเข้าข้อมูลทันที</span>
                <div className="text-sm text-blue-600 mt-1">
                  จะนำเข้าข้อมูล {fileAnalysis.totalRows.toLocaleString()} แถว จากไฟล์ {selectedFile.name}
                </div>
              </div>
            </label>
          </div>
        )}
      </div>

      {/* Column Editor */}
      {renderColumnEditor()}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          {newTable.createAndImport && fileAnalysis && (
            <div className="flex items-center">
              <Sparkles className="h-4 w-4 mr-2 text-purple-500" />
              <span>จะสร้างตารางและนำเข้าข้อมูล {fileAnalysis.totalRows.toLocaleString()} แถวทันที</span>
            </div>
          )}
        </div>
        
        <div className="flex space-x-4">
          <button
            onClick={() => {
              setNewTable({
                name: '',
                description: '',
                schema: 'public',
                createAndImport: false,
                columns: [{ 
                  name: 'id', 
                  type: 'SERIAL', 
                  isPrimary: true, 
                  isRequired: true, 
                  isUnique: false, 
                  defaultValue: '' 
                }]
              });
              setSelectedFile({ file: null, name: '', type: '', size: 0 });
              setFileAnalysis(null);
              setCreateMode({ type: 'manual' });
            }}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            ล้างข้อมูล
          </button>
          
          <button
            onClick={handleCreateTable}
            disabled={loading || !newTable.name.trim()}
            className="flex items-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : newTable.createAndImport ? (
              <Zap className="h-4 w-4 mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {newTable.createAndImport ? 'สร้างตาราง + นำเข้าข้อมูล' : 'สร้างตาราง'}
          </button>
        </div>
      </div>
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Enhanced Table Management</h1>
            <p className="text-blue-100 mt-2">Smart table creation with AI-powered file analysis</p>
          </div>
          <Database className="h-12 w-12 text-blue-200" />
        </div>
      </div>

      {/* Database Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Database className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{schemas.length}</div>
              <div className="text-sm text-gray-500">Total Schemas</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Table className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{getTotalTables()}</div>
              <div className="text-sm text-gray-500">Total Tables</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Settings className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{getSchemaStats().customSchemas}</div>
              <div className="text-sm text-gray-500">Custom Schemas</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-blue-500 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{getSchemaStats().defaultSchemas}</div>
              <div className="text-sm text-gray-500">Default Schemas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Company Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">บริษัทของคุณ</h2>
        <div className="flex items-center p-4 rounded-lg border-2 border-blue-500 bg-blue-50">
          <Database className="h-8 w-8 text-blue-600 mr-4" />
          <div>
            <div className="font-medium text-gray-900">{currentCompany.name}</div>
            <div className="text-sm text-gray-500 mt-1">{currentCompany.dbName}</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button
          onClick={() => setCurrentView('create-table')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all text-left group"
        >
          <div className="flex items-center mb-4">
            <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
              <Brain className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Smart Table Creator</h3>
              <div className="flex items-center mt-1">
                <Sparkles className="h-4 w-4 text-purple-500 mr-1" />
                <span className="text-sm text-purple-600 font-medium">AI-Powered</span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-sm">
            สร้างตารางใหม่ด้วยการวิเคราะห์ไฟล์อัตโนมัติ หรือออกแบบเอง พร้อมนำเข้าข้อมูลทันที
          </p>
          <div className="mt-4 flex items-center text-sm text-green-600">
            <CheckCircle className="h-4 w-4 mr-2" />
            Auto-detect data types
          </div>
          <div className="flex items-center text-sm text-green-600 mt-1">
            <CheckCircle className="h-4 w-4 mr-2" />
            One-click create & import
          </div>
        </button>

        <button
          onClick={() => setCurrentView('create-schema')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all text-left group"
        >
          <div className="flex items-center mb-4">
            <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
              <Database className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Create Schema</h3>
              <div className="flex items-center mt-1">
                <Settings className="h-4 w-4 text-purple-500 mr-1" />
                <span className="text-sm text-purple-600 font-medium">Organization</span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-sm">
            สร้าง Schema ใหม่เพื่อจัดกลุ่มตารางตามหน้าที่การใช้งาน และจัดระเบียบฐานข้อมูล
          </p>
          <div className="mt-4 flex items-center text-sm text-purple-600">
            <CheckCircle className="h-4 w-4 mr-2" />
            Logical grouping
          </div>
          <div className="flex items-center text-sm text-purple-600 mt-1">
            <CheckCircle className="h-4 w-4 mr-2" />
            Better organization
          </div>
        </button>

        <button
          onClick={() => setCurrentView('import-wizard')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all text-left group"
        >
          <div className="flex items-center mb-4">
            <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
              <Upload className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Import Wizard</h3>
              <div className="flex items-center mt-1">
                <BarChart3 className="h-4 w-4 text-blue-500 mr-1" />
                <span className="text-sm text-blue-600 font-medium">Advanced</span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-sm">
            นำเข้าข้อมูลเข้าสู่ตารางที่มีอยู่แล้ว พร้อมตัวเลือกการจัดการข้อมูลขั้นสูง
          </p>
          <div className="mt-4 flex items-center text-sm text-blue-600">
            <CheckCircle className="h-4 w-4 mr-2" />
            Batch processing
          </div>
          <div className="flex items-center text-sm text-blue-600 mt-1">
            <CheckCircle className="h-4 w-4 mr-2" />
            Error handling & validation
          </div>
        </button>
      </div>

      {/* Schemas Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Database Schemas</h2>
              <p className="text-sm text-gray-500 mt-1">
                จัดการและดู Schema ทั้งหมดในฐานข้อมูล
              </p>
            </div>
            <div className="flex space-x-2">
              <button 
                onClick={() => {
                  loadInitialData(); // This will now load from database first
                }}
                disabled={loading}
                className="flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                รีเฟรชจาก DB
              </button>
              
              <button 
                onClick={() => {
                  const freshSchemas = loadSchemasFromStorage();
                  setSchemas(freshSchemas);
                  showSuccess('รีเฟรชจาก localStorage สำเร็จ');
                }}
                disabled={loading}
                className="flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                รีเฟรช Local
              </button>
              
              <button 
                onClick={() => {
                  if (confirm('คุณต้องการล้างข้อมูลทั้งหมดและเริ่มใหม่หรือไม่?')) {
                    localStorage.removeItem(STORAGE_KEY);
                    const defaultSchemas = loadSchemasFromStorage();
                    setSchemas(defaultSchemas);
                    showSuccess('ล้างข้อมูลและรีเซ็ตเรียบร้อย');
                  }
                }}
                className="flex items-center px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                รีเซ็ต
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : schemas.length === 0 ? (
            <div className="text-center py-8">
              <Database className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">ไม่มี Schema</h3>
              <p className="text-gray-500 mb-4">เริ่มต้นด้วยการสร้าง Schema แรกของคุณ</p>
              <button
                onClick={() => setCurrentView('create-schema')}
                className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                สร้าง Schema แรก
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {schemas.map((schema) => (
                <div key={schema.name} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <Database className="h-5 w-5 text-gray-500 mr-2" />
                      <span className="font-medium text-gray-900">{schema.name}</span>
                      <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                        schema.type === 'default' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {schema.type === 'default' ? 'Default' : 'Custom'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">{schema.tables.length} tables</span>
                      {schema.type === 'custom' && schema.tables.length === 0 && (
                        <button
                          onClick={() => deleteSchema(schema.name)}
                          className="text-red-500 hover:text-red-700 p-1"
                          title="ลบ Schema"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {schema.description && (
                    <div className="text-sm text-gray-600 mb-3">
                      {schema.description}
                    </div>
                  )}
                  
                  {schema.tables.length > 0 ? (
                    <div className="mb-3">
                      <div className="text-sm text-gray-600 mb-2">Tables:</div>
                      <div className="flex flex-wrap gap-2">
                        {schema.tables.map((table, idx) => (
                          <div key={idx} className="flex items-center">
                            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                              {table}
                            </span>
                            <button
                              onClick={() => deleteTable(schema.name, table)}
                              className="ml-1 text-red-500 hover:text-red-700"
                              title="ลบตาราง"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400 mb-3">ไม่มีตาราง</div>
                  )}
                  
                  <div className="flex justify-between items-center pt-3 border-t border-gray-100">
                    <div className="text-xs text-gray-500">
                      Created: {new Date(schema.createdAt).toLocaleDateString('th-TH')}
                    </div>
                    <button
                      onClick={() => {
                        setNewTable(prev => ({ ...prev, schema: schema.name }));
                        setCurrentView('create-table');
                      }}
                      className="flex items-center px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      เพิ่มตาราง
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderCreateSchema = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Create New Schema</h2>
          <p className="text-gray-600 mt-1">จัดระเบียบตารางด้วยการสร้าง Schema ใหม่</p>
        </div>
        <button
          onClick={() => setCurrentView('overview')}
          className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          กลับ
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-6">
          <Database className="h-6 w-6 text-purple-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">Schema Information</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ชื่อ Schema *
            </label>
            <input
              type="text"
              value={newSchema.name}
              onChange={(e) => setNewSchema(prev => ({ ...prev, name: e.target.value }))}
              placeholder="เช่น inventory, hr_management, analytics"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              ใช้ตัวอักษรภาษาอังกฤษ ตัวเลข และ underscore เท่านั้น
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              คำอธิบาย
            </label>
            <input
              type="text"
              value={newSchema.description}
              onChange={(e) => setNewSchema(prev => ({ ...prev, description: e.target.value }))}
              placeholder="คำอธิบายโดยย่อของ Schema"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              อธิบายว่า Schema นี้ใช้สำหรับจัดเก็บข้อมูลประเภทใด
            </p>
          </div>
        </div>

        {/* Schema Benefits */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-6">
          <h4 className="text-lg font-medium text-purple-900 mb-4">ประโยชน์ของการใช้ Schema</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-purple-600 mr-3 mt-0.5" />
              <div>
                <div className="font-medium text-purple-800">จัดกลุ่มตารางตามหน้าที่</div>
                <div className="text-sm text-purple-600">แยกตารางตามประเภทการใช้งาน</div>
              </div>
            </div>
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-purple-600 mr-3 mt-0.5" />
              <div>
                <div className="font-medium text-purple-800">ความปลอดภัยของข้อมูล</div>
                <div className="text-sm text-purple-600">ควบคุมสิทธิ์การเข้าถึงได้ละเอียด</div>
              </div>
            </div>
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-purple-600 mr-3 mt-0.5" />
              <div>
                <div className="font-medium text-purple-800">หลีกเลี่ยงความซ้ำซ้อน</div>
                <div className="text-sm text-purple-600">ป้องกันชื่อตารางที่ซ้ำกัน</div>
              </div>
            </div>
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-purple-600 mr-3 mt-0.5" />
              <div>
                <div className="font-medium text-purple-800">จัดการง่ายขึ้น</div>
                <div className="text-sm text-purple-600">ค้นหาและบำรุงรักษาสะดวก</div>
              </div>
            </div>
          </div>
        </div>

        {/* Current Schemas */}
        <div className="mb-6">
          <h4 className="text-lg font-medium text-gray-900 mb-3">Schemas ที่มีอยู่ในระบบ</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schemas.map((schema) => (
              <div key={schema.name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <Database className="h-4 w-4 text-gray-500 mr-2" />
                    <span className="font-medium text-gray-900">{schema.name}</span>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    schema.type === 'default' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {schema.type === 'default' ? 'Default' : 'Custom'}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {schema.tables.length} tables: {schema.tables.slice(0, 3).join(', ')}
                  {schema.tables.length > 3 && '...'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            <span className="font-medium">หมายเหตุ:</span> Schema ที่สร้างแล้วจะไม่สามารถลบได้หากมีตารางอยู่ภายใน
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={() => setNewSchema({ name: '', description: '' })}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              ล้างข้อมูล
            </button>
            
            <button
              onClick={handleCreateSchema}
              disabled={loading || !newSchema.name.trim()}
              className="flex items-center px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              สร้าง Schema
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // ============================================================================
  // MAIN RENDER
  // ============================================================================
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification */}
      {message.text && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
          message.type === 'success' 
            ? 'bg-green-100 border border-green-200 text-green-800'
            : message.type === 'error'
            ? 'bg-red-100 border border-red-200 text-red-800'
            : 'bg-blue-100 border border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-center">
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5 mr-2" />
            ) : message.type === 'error' ? (
              <XCircle className="h-5 w-5 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 mr-2" />
            )}
            <span className="font-medium">{message.text}</span>
            <button
              onClick={clear}
              className="ml-auto pl-3"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'overview' && renderOverview()}
        {currentView === 'create-table' && renderCreateTable()}
        {currentView === 'create-schema' && renderCreateSchema()}
        {currentView === 'import-wizard' && (
          <div className="text-center py-20">
            <Upload className="h-20 w-20 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Import Wizard</h2>
            <p className="text-gray-600">ฟีเจอร์นี้กำลังพัฒนา...</p>
            <button
              onClick={() => setCurrentView('overview')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              กลับหน้าหลัก
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedTableManagement;