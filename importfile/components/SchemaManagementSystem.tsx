import React, { useState, useCallback } from 'react';
import { Upload, FileText, Table, Download, AlertCircle, CheckCircle, Plus, X, Eye, Settings } from 'lucide-react';

// Types
interface Column {
  name: string;
  type: string;
  length?: number;
  isPrimary: boolean;
  isRequired: boolean;
  isUnique: boolean;
  defaultValue?: string;
  inferredType?: string;
  sampleData?: any[];
}

interface FileAnalysis {
  fileName: string;
  fileType: string;
  totalRows: number;
  detectedColumns: Column[];
  sampleData: any[];
  encoding?: string;
}

const EnhancedTableCreator = () => {
  const [currentStep, setCurrentStep] = useState(1); // 1: Basic Info, 2: File Upload, 3: Column Config, 4: Review
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Basic table info
  const [tableInfo, setTableInfo] = useState({
    schema: 'public',
    name: '',
    description: ''
  });

  // File upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [importMode, setImportMode] = useState<'manual' | 'file'>('manual');

  // Columns
  const [columns, setColumns] = useState<Column[]>([
    { name: 'id', type: 'SERIAL', isPrimary: true, isRequired: true, isUnique: true }
  ]);

  // Available data types
  const dataTypes = [
    'SERIAL', 'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC', 'REAL', 'DOUBLE PRECISION',
    'VARCHAR', 'CHAR', 'TEXT', 'BOOLEAN', 'DATE', 'TIME', 'TIMESTAMP', 'JSON', 'JSONB', 'UUID'
  ];

  // File handling
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');
    }
  }, []);

  const analyzeFile = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/analyze-file', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('ไม่สามารถวิเคราะห์ไฟล์ได้');
      }

      const analysis = await response.json();
      setFileAnalysis(analysis);
      
      // Auto-populate columns from analysis
      if (analysis.detectedColumns) {
        setColumns(analysis.detectedColumns);
      }

      setCurrentStep(3);
      setSuccess('วิเคราะห์ไฟล์สำเร็จ!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาด');
    } finally {
      setLoading(false);
    }
  };

  // Column management
  const addColumn = () => {
    setColumns([...columns, {
      name: '',
      type: 'VARCHAR',
      length: 255,
      isPrimary: false,
      isRequired: false,
      isUnique: false
    }]);
  };

  const removeColumn = (index: number) => {
    setColumns(columns.filter((_, i) => i !== index));
  };

  const updateColumn = (index: number, field: keyof Column, value: any) => {
    const updated = [...columns];
    updated[index] = { ...updated[index], [field]: value };
    setColumns(updated);
  };

  // Type inference helpers
  const getTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      'SERIAL': 'bg-blue-100 text-blue-800',
      'INTEGER': 'bg-green-100 text-green-800',
      'VARCHAR': 'bg-yellow-100 text-yellow-800',
      'TEXT': 'bg-purple-100 text-purple-800',
      'BOOLEAN': 'bg-red-100 text-red-800',
      'DATE': 'bg-indigo-100 text-indigo-800',
      'TIMESTAMP': 'bg-pink-100 text-pink-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  // Create table
  const createTable = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/database/create-table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...tableInfo,
          columns,
          importFile: importMode === 'file' ? selectedFile?.name : null
        })
      });

      if (!response.ok) {
        throw new Error('ไม่สามารถสร้างตารางได้');
      }

      const result = await response.json();
      setSuccess(`สร้างตาราง "${tableInfo.name}" สำเร็จ!`);
      
      // Import data if file was selected
      if (importMode === 'file' && selectedFile) {
        await importData();
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาด');
    } finally {
      setLoading(false);
    }
  };

  const importData = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('tableName', tableInfo.name);
    formData.append('schema', tableInfo.schema);

    try {
      const response = await fetch('/api/database/import-data', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('ไม่สามารถนำเข้าข้อมูลได้');
      }

      const result = await response.json();
      setSuccess(prev => prev + ` นำเข้าข้อมูล ${result.importedRows} แถวสำเร็จ!`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาดในการนำเข้าข้อมูล');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">สร้างตารางใหม่</h1>
          <div className="text-sm text-gray-500">
            สำหรับ SiamTech Main Office
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center space-x-4 mb-6">
          {[
            { step: 1, label: 'ข้อมูลพื้นฐาน', icon: FileText },
            { step: 2, label: 'นำเข้าไฟล์', icon: Upload },
            { step: 3, label: 'กำหนดคอลัมน์', icon: Settings },
            { step: 4, label: 'ตรวจสอบ', icon: Eye }
          ].map(({ step, label, icon: Icon }) => (
            <div key={step} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep >= step ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                {currentStep > step ? <CheckCircle size={16} /> : <Icon size={16} />}
              </div>
              <span className={`ml-2 text-sm ${
                currentStep >= step ? 'text-green-600 font-medium' : 'text-gray-600'
              }`}>
                {label}
              </span>
              {step < 4 && <div className="w-8 h-0.5 bg-gray-200 ml-4" />}
            </div>
          ))}
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
          <AlertCircle className="text-red-500 mr-2" size={20} />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
          <CheckCircle className="text-green-500 mr-2" size={20} />
          <span className="text-green-700">{success}</span>
        </div>
      )}

      {/* Step 1: Basic Information */}
      {currentStep === 1 && (
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-lg font-semibold mb-4">ข้อมูลพื้นฐานของตาราง</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schema *
                </label>
                <select
                  value={tableInfo.schema}
                  onChange={(e) => setTableInfo({...tableInfo, schema: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="public">public</option>
                  <option value="test1">test1</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ชื่อตาราง *
                </label>
                <input
                  type="text"
                  value={tableInfo.name}
                  onChange={(e) => setTableInfo({...tableInfo, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ชื่อตาราง"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                คำอธิบาย
              </label>
              <textarea
                value={tableInfo.description}
                onChange={(e) => setTableInfo({...tableInfo, description: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="คำอธิบายเกี่ยวกับตาราง"
              />
            </div>
          </div>

          <div className="bg-blue-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">เลือกวิธีการสร้างตาราง</h3>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="importMode"
                  value="manual"
                  checked={importMode === 'manual'}
                  onChange={(e) => setImportMode(e.target.value as 'manual')}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">สร้างด้วยตนเอง</div>
                  <div className="text-sm text-gray-600">กำหนดคอลัมน์และประเภทข้อมูลเอง</div>
                </div>
              </label>
              
              <label className="flex items-center">
                <input
                  type="radio"
                  name="importMode"
                  value="file"
                  checked={importMode === 'file'}
                  onChange={(e) => setImportMode(e.target.value as 'file')}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">นำเข้าจากไฟล์</div>
                  <div className="text-sm text-gray-600">วิเคราะห์โครงสร้างจากไฟล์ CSV, Excel หรือ JSON</div>
                </div>
              </label>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => setCurrentStep(importMode === 'file' ? 2 : 3)}
              disabled={!tableInfo.name}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              ถัดไป
            </button>
          </div>
        </div>
      )}

      {/* Step 2: File Upload */}
      {currentStep === 2 && importMode === 'file' && (
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-lg font-semibold mb-4">อัพโหลดไฟล์</h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              {selectedFile ? (
                <div className="space-y-4">
                  <FileText className="mx-auto text-green-500" size={48} />
                  <div>
                    <div className="font-medium text-gray-900">{selectedFile.name}</div>
                    <div className="text-sm text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={analyzeFile}
                      disabled={loading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                    >
                      {loading ? 'กำลังวิเคราะห์...' : 'วิเคราะห์ไฟล์'}
                    </button>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                    >
                      เลือกใหม่
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="mx-auto text-gray-400" size={48} />
                  <div>
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-500">เลือกไฟล์</span>
                      <span className="text-gray-500"> หรือลากไฟล์มาวางที่นี่</span>
                    </label>
                    <input
                      id="file-upload"
                      type="file"
                      accept=".csv,.xlsx,.xls,.json"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                  <div className="text-sm text-gray-500">
                    รองรับไฟล์: CSV, Excel (.xlsx, .xls), JSON
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              ย้อนกลับ
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Column Configuration */}
      {currentStep === 3 && (
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">กำหนดคอลัมน์</h2>
              <button
                onClick={addColumn}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
              >
                <Plus size={16} className="mr-2" />
                เพิ่มคอลัมน์
              </button>
            </div>

            {/* File Analysis Summary */}
            {fileAnalysis && (
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium mb-2">ผลการวิเคราะห์ไฟล์:</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">ไฟล์:</span>
                    <div className="font-medium">{fileAnalysis.fileName}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">ประเภท:</span>
                    <div className="font-medium">{fileAnalysis.fileType.toUpperCase()}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">จำนวนแถว:</span>
                    <div className="font-medium">{fileAnalysis.totalRows}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">คอลัมน์:</span>
                    <div className="font-medium">{fileAnalysis.detectedColumns.length}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Columns Table */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 px-4 py-2 text-left">ชื่อคอลัมน์</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">ประเภทข้อมูล</th>
                    <th className="border border-gray-300 px-4 py-2 text-center">ความยาว</th>
                    <th className="border border-gray-300 px-4 py-2 text-center">PK</th>
                    <th className="border border-gray-300 px-4 py-2 text-center">จำเป็น</th>
                    <th className="border border-gray-300 px-4 py-2 text-center">ไม่ซ้ำ</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">ค่าเริ่มต้น</th>
                    <th className="border border-gray-300 px-4 py-2 text-center">ลบ</th>
                  </tr>
                </thead>
                <tbody>
                  {columns.map((column, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="border border-gray-300 px-4 py-2">
                        <input
                          type="text"
                          value={column.name}
                          onChange={(e) => updateColumn(index, 'name', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="ชื่อคอลัมน์"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        <div className="space-y-1">
                          <select
                            value={column.type}
                            onChange={(e) => updateColumn(index, 'type', e.target.value)}
                            className="w-full px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          >
                            {dataTypes.map(type => (
                              <option key={type} value={type}>{type}</option>
                            ))}
                          </select>
                          {column.inferredType && column.inferredType !== column.type && (
                            <div className={`text-xs px-2 py-1 rounded ${getTypeColor(column.inferredType)}`}>
                              แนะนำ: {column.inferredType}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        {['VARCHAR', 'CHAR'].includes(column.type) && (
                          <input
                            type="number"
                            value={column.length || ''}
                            onChange={(e) => updateColumn(index, 'length', parseInt(e.target.value) || undefined)}
                            className="w-20 px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            placeholder="255"
                          />
                        )}
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={column.isPrimary}
                          onChange={(e) => updateColumn(index, 'isPrimary', e.target.checked)}
                          className="rounded"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={column.isRequired}
                          onChange={(e) => updateColumn(index, 'isRequired', e.target.checked)}
                          className="rounded"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={column.isUnique}
                          onChange={(e) => updateColumn(index, 'isUnique', e.target.checked)}
                          className="rounded"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        <input
                          type="text"
                          value={column.defaultValue || ''}
                          onChange={(e) => updateColumn(index, 'defaultValue', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="Default value"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-center">
                        {columns.length > 1 && (
                          <button
                            onClick={() => removeColumn(index)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <X size={16} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Sample Data Preview */}
            {fileAnalysis?.sampleData && (
              <div className="mt-6">
                <h3 className="font-medium mb-2">ตัวอย่างข้อมูล (5 แถวแรก):</h3>
                <div className="overflow-x-auto bg-white border rounded-lg">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {Object.keys(fileAnalysis.sampleData[0] || {}).map(key => (
                          <th key={key} className="px-4 py-2 text-left border">{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {fileAnalysis.sampleData.slice(0, 5).map((row, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          {Object.values(row).map((value, j) => (
                            <td key={j} className="px-4 py-2 border">{String(value)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between">
            <button
              onClick={() => setCurrentStep(importMode === 'file' ? 2 : 1)}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              ย้อนกลับ
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              disabled={columns.length === 0 || columns.some(col => !col.name)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              ถัดไป
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Review and Create */}
      {currentStep === 4 && (
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-lg font-semibold mb-4">ตรวจสอบข้อมูลก่อนสร้างตาราง</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Table Info */}
              <div>
                <h3 className="font-medium mb-3">ข้อมูลตาราง</h3>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Schema:</span> {tableInfo.schema}</div>
                  <div><span className="font-medium">ชื่อตาราง:</span> {tableInfo.name}</div>
                  <div><span className="font-medium">คำอธิบาย:</span> {tableInfo.description || '-'}</div>
                  <div><span className="font-medium">จำนวนคอลัมน์:</span> {columns.length}</div>
                  {importMode === 'file' && fileAnalysis && (
                    <div><span className="font-medium">ไฟล์:</span> {fileAnalysis.fileName}</div>
                  )}
                </div>
              </div>

              {/* Columns Summary */}
              <div>
                <h3 className="font-medium mb-3">สรุปคอลัมน์</h3>
                <div className="space-y-1 text-sm max-h-40 overflow-y-auto">
                  {columns.map((col, i) => (
                    <div key={i} className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded ${getTypeColor(col.type)}`}>
                        {col.type}
                      </span>
                      <span className="font-medium">{col.name}</span>
                      {col.isPrimary && <span className="text-xs bg-yellow-100 text-yellow-800 px-1 rounded">PK</span>}
                      {col.isRequired && <span className="text-xs bg-red-100 text-red-800 px-1 rounded">Required</span>}
                      {col.isUnique && <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">Unique</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Generated SQL Preview */}
            <div className="mt-6">
              <h3 className="font-medium mb-2">SQL ที่จะถูกสร้าง:</h3>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                <pre>{generateSQL()}</pre>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              ย้อนกลับ
            </button>
            <button
              onClick={createTable}
              disabled={loading}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  กำลังสร้าง...
                </>
              ) : (
                <>
                  <Table className="mr-2" size={16} />
                  สร้างตาราง
                  {importMode === 'file' && ' + นำเข้าข้อมูล'}
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // Helper function to generate SQL
  function generateSQL(): string {
    const columnDefs = columns.map(col => {
      let def = `  "${col.name}" ${col.type}`;
      
      if (col.length && ['VARCHAR', 'CHAR'].includes(col.type)) {
        def += `(${col.length})`;
      }
      
      if (col.isRequired && !col.isPrimary) {
        def += ' NOT NULL';
      }
      
      if (col.isUnique && !col.isPrimary) {
        def += ' UNIQUE';
      }
      
      if (col.defaultValue) {
        def += ` DEFAULT ${col.defaultValue}`;
      }
      
      return def;
    }).join(',\n');

    const primaryKeys = columns.filter(col => col.isPrimary).map(col => `"${col.name}"`);
    const primaryKeyDef = primaryKeys.length > 0 ? `,\n  PRIMARY KEY (${primaryKeys.join(', ')})` : '';

    return `CREATE TABLE "${tableInfo.schema}"."${tableInfo.name}" (\n${columnDefs}${primaryKeyDef}\n);${
      tableInfo.description ? 
      `\n\nCOMMENT ON TABLE "${tableInfo.schema}"."${tableInfo.name}" IS '${tableInfo.description}';` : 
      ''
    }`;
  }
};

export default EnhancedTableCreator;