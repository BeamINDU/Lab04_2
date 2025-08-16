import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { 
  Database, Plus, Table, Upload, History, Search,
  RefreshCw, Layout, ArrowLeft, AlertCircle, Check,
  FileText, Download, Settings, Eye, Trash2,
  Save, Copy, Filter
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
}

interface ImportFile {
  file: File | null;
  name: string;
  type: string;
  size: number;
}

// ============================================================================
// CUSTOM HOOKS
// ============================================================================
const useNotification = () => {
  const [message, setMessage] = useState<{ type: 'success' | 'error' | ''; text: string }>({ type: '', text: '' });

  const showSuccess = (text: string) => setMessage({ type: 'success', text });
  const showError = (text: string) => setMessage({ type: 'error', text });
  const clear = () => setMessage({ type: '', text: '' });

  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(clear, 5000);
      return () => clearTimeout(timer);
    }
  }, [message.text]);

  return { message, showSuccess, showError, clear };
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================
const UnifiedDataManagementSystem: React.FC = () => {
  const { data: session, status } = useSession();
  
  // State Management
  const [currentView, setCurrentView] = useState<'overview' | 'import-data' | 'create-schema' | 'create-table' | 'manage-tables'>('overview');
  const [currentCompany, setCurrentCompany] = useState<Company | null>(null);
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Import States
  const [selectedFile, setSelectedFile] = useState<ImportFile>({
    file: null, name: '', type: '', size: 0
  });
  const [selectedTable, setSelectedTable] = useState('');
  const [selectedSchema, setSelectedSchema] = useState('public');
  const [importOptions, setImportOptions] = useState({
    hasHeader: true,
    onDuplicate: 'skip',
    batchSize: 1000
  });
  
  // Schema Management States
  const [newSchema, setNewSchema] = useState({ name: '', description: '' });
  const [newTable, setNewTable] = useState({
    name: '',
    description: '',
    schema: 'public',
    columns: [{ 
      name: 'id', 
      type: 'SERIAL', 
      isPrimary: true, 
      isRequired: true, 
      isUnique: false, 
      defaultValue: '' 
    }] as Column[]
  });

  const { message, showSuccess, showError } = useNotification();

  const dataTypes = [
    'SERIAL', 'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC',
    'VARCHAR', 'TEXT', 'CHAR', 'BOOLEAN', 
    'DATE', 'TIME', 'TIMESTAMP', 'TIMESTAMPTZ',
    'JSON', 'JSONB', 'UUID', 'ARRAY'
  ];

  // Setup company from session
  useEffect(() => {
    if (session?.user) {
      const company: Company = {
        code: session.user.companyCode || 'company_a',
        name: session.user.companyName || 'Unknown Company',
        dbName: `siamtech_${session.user.companyCode || 'company_a'}`
      };
      setCurrentCompany(company);
      loadSchemas();
    }
  }, [session]);

  // Event Handlers
  const loadSchemas = async () => {
    setLoading(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockSchemas: Schema[] = [
        { 
          name: 'public', 
          type: 'default', 
          tables: ['employees', 'projects', 'departments', 'clients'], 
          createdAt: '2024-01-01' 
        },
        { 
          name: 'hr_management', 
          type: 'custom', 
          tables: ['payroll', 'benefits', 'performance_reviews'], 
          createdAt: '2024-02-15' 
        },
        { 
          name: 'analytics', 
          type: 'custom', 
          tables: ['reports', 'metrics', 'dashboards'], 
          createdAt: '2024-03-01' 
        }
      ];
      
      setSchemas(mockSchemas);
      showSuccess('โหลดข้อมูล Schema สำเร็จ');
    } catch (error) {
      showError('เกิดข้อผิดพลาดในการโหลดข้อมูล');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile({
        file,
        name: file.name,
        type: file.type,
        size: file.size
      });
    }
  };

  const handleImport = async () => {
    if (!selectedFile.file || !selectedTable) {
      showError('กรุณาเลือกไฟล์และตารางปลายทาง');
      return;
    }

    setLoading(true);
    try {
      // Mock import process
      await new Promise(resolve => setTimeout(resolve, 2000));
      showSuccess(`นำเข้าข้อมูลสำเร็จ! ไฟล์: ${selectedFile.name} → ตาราง: ${selectedTable}`);
      
      // Reset form
      setSelectedFile({ file: null, name: '', type: '', size: 0 });
      setSelectedTable('');
    } catch (error) {
      showError('เกิดข้อผิดพลาดในการนำเข้าข้อมูล');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchema = async () => {
    if (!newSchema.name.trim()) {
      showError('กรุณาใส่ชื่อ Schema');
      return;
    }

    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      showSuccess(`สร้าง Schema "${newSchema.name}" สำเร็จ!`);
      setNewSchema({ name: '', description: '' });
      loadSchemas();
    } catch (error) {
      showError('เกิดข้อผิดพลาดในการสร้าง Schema');
    } finally {
      setLoading(false);
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
      await new Promise(resolve => setTimeout(resolve, 1500));
      showSuccess(`สร้างตาราง "${newTable.name}" ใน Schema "${newTable.schema}" สำเร็จ!`);
      
      // Reset form
      setNewTable({
        name: '',
        description: '',
        schema: 'public',
        columns: [{ 
          name: 'id', 
          type: 'SERIAL', 
          isPrimary: true, 
          isRequired: true, 
          isUnique: false, 
          defaultValue: '' 
        }]
      });
      
      loadSchemas();
    } catch (error) {
      showError('เกิดข้อผิดพลาดในการสร้างตาราง');
    } finally {
      setLoading(false);
    }
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

  const updateColumn = (index: number, field: keyof Column, value: any) => {
    setNewTable(prev => ({
      ...prev,
      columns: prev.columns.map((col, i) => 
        i === index ? { ...col, [field]: value } : col
      )
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

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'csv': return '📊';
      case 'xlsx': case 'xls': return '📈';
      case 'json': return '📋';
      default: return '📄';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Loading state
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

  if (!session || !currentCompany) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">ไม่ได้เข้าสู่ระบบ</h2>
          <p className="text-gray-600">กรุณาเข้าสู่ระบบก่อนใช้งาน</p>
        </div>
      </div>
    );
  }

  // Render Methods
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Company Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
          onClick={() => setCurrentView('import-data')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow text-left"
        >
          <div className="flex items-center mb-4">
            <Upload className="h-8 w-8 text-green-600 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900">นำเข้าข้อมูล</h3>
          </div>
          <p className="text-gray-600 text-sm">
            อัพโหลดและนำเข้าข้อมูลจากไฟล์ CSV, Excel หรือ JSON เข้าสู่ตารางที่มีอยู่
          </p>
        </button>

        <button
          onClick={() => setCurrentView('create-table')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow text-left"
        >
          <div className="flex items-center mb-4">
            <Table className="h-8 w-8 text-blue-600 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900">สร้างตารางใหม่</h3>
          </div>
          <p className="text-gray-600 text-sm">
            ออกแบบและสร้างตารางใหม่พร้อมกำหนด columns และ constraints
          </p>
        </button>

        <button
          onClick={() => setCurrentView('create-schema')}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow text-left"
        >
          <div className="flex items-center mb-4">
            <Database className="h-8 w-8 text-purple-600 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900">สร้าง Schema</h3>
          </div>
          <p className="text-gray-600 text-sm">
            สร้าง Schema ใหม่เพื่อจัดกลุ่มตารางตามหน้าที่การใช้งาน
          </p>
        </button>
      </div>

      {/* Schemas Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Schemas และตารางในระบบ</h2>
            <button
              onClick={loadSchemas}
              disabled={loading}
              className="flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              รีเฟรช
            </button>
          </div>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="ค้นหา Schema หรือ Table..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {schemas.filter(schema =>
                schema.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                schema.tables.some(table => table.toLowerCase().includes(searchTerm.toLowerCase()))
              ).map((schema, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <Database className="h-5 w-5 text-blue-600 mr-2" />
                      <h3 className="font-medium text-gray-900">{schema.name}</h3>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      schema.type === 'default' 
                        ? 'bg-gray-100 text-gray-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {schema.type === 'default' ? 'ระบบ' : 'กำหนดเอง'}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-3">
                    {schema.tables.length} ตาราง
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mb-3">
                    {schema.tables.slice(0, 3).map((table, idx) => (
                      <span 
                        key={idx} 
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded cursor-pointer hover:bg-gray-200"
                        onClick={() => {
                          setSelectedTable(table);
                          setSelectedSchema(schema.name);
                          setCurrentView('import-data');
                        }}
                      >
                        {table}
                      </span>
                    ))}
                    {schema.tables.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        +{schema.tables.length - 3}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <button 
                      onClick={() => {
                        setNewTable(prev => ({ ...prev, schema: schema.name }));
                        setCurrentView('create-table');
                      }}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      เพิ่มตาราง
                    </button>
                    
                    <button 
                      onClick={() => {
                        setSelectedSchema(schema.name);
                        setCurrentView('import-data');
                      }}
                      className="flex items-center justify-center px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                    >
                      <Upload className="h-4 w-4" />
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

  const renderImportData = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">นำเข้าข้อมูล</h2>
            <p className="text-gray-600">อัพโหลดและนำเข้าข้อมูลจากไฟล์ลงฐานข้อมูล</p>
          </div>
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            กลับ
          </button>
        </div>

        {/* File Upload */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">1. เลือกไฟล์</h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">เลือกไฟล์เพื่อนำเข้า</p>
                <p className="text-sm text-gray-500">รองรับ CSV, Excel, JSON (สูงสุด 10MB)</p>
              </label>
            </div>

            {selectedFile.file && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{getFileIcon(selectedFile.name)}</span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <button
                    onClick={() => setSelectedFile({ file: null, name: '', type: '', size: 0 })}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">2. เลือกปลายทาง</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Schema</label>
                <select
                  value={selectedSchema}
                  onChange={(e) => setSelectedSchema(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  {schemas.map(schema => (
                    <option key={schema.name} value={schema.name}>{schema.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">ตารางปลายทาง</label>
                <select
                  value={selectedTable}
                  onChange={(e) => setSelectedTable(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">เลือกตาราง...</option>
                  {schemas.find(s => s.name === selectedSchema)?.tables.map(table => (
                    <option key={table} value={table}>{table}</option>
                  ))}
                </select>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">ตัวเลือกการนำเข้า</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={importOptions.hasHeader}
                      onChange={(e) => setImportOptions(prev => ({ ...prev, hasHeader: e.target.checked }))}
                      className="rounded mr-2"
                    />
                    <span className="text-sm text-blue-800">แถวแรกเป็น Header</span>
                  </label>
                  
                  <div>
                    <label className="block text-sm font-medium text-blue-800 mb-1">จัดการข้อมูลซ้ำ</label>
                    <select
                      value={importOptions.onDuplicate}
                      onChange={(e) => setImportOptions(prev => ({ ...prev, onDuplicate: e.target.value }))}
                      className="w-full px-2 py-1 border border-blue-300 rounded text-sm"
                    >
                      <option value="skip">ข้าม</option>
                      <option value="update">อัปเดต</option>
                      <option value="error">แสดงข้อผิดพลาด</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Import Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleImport}
            disabled={loading || !selectedFile.file || !selectedTable}
            className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
            ) : (
              <Upload className="h-5 w-5 mr-2" />
            )}
            เริ่มนำเข้าข้อมูล
          </button>
        </div>
      </div>
    </div>
  );

  const renderCreateSchema = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">สร้าง Schema ใหม่</h2>
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            กลับ
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ชื่อ Schema *</label>
            <input
              type="text"
              value={newSchema.name}
              onChange={(e) => setNewSchema(prev => ({ ...prev, name: e.target.value }))}
              placeholder="เช่น inventory, hr_management"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">คำอธิบาย</label>
            <input
              type="text"
              value={newSchema.description}
              onChange={(e) => setNewSchema(prev => ({ ...prev, description: e.target.value }))}
              placeholder="คำอธิบายโดยย่อของ Schema"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleCreateSchema}
            disabled={loading || !newSchema.name.trim()}
            className="flex items-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
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
  );

  const renderCreateTable = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">สร้างตารางใหม่</h2>
            <p className="text-gray-600">Schema: {newTable.schema}</p>
          </div>
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            กลับ
          </button>
        </div>

        {/* Table Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
              placeholder="คำอธิบายโดยย่อของตาราง"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Columns Configuration */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">กำหนด Columns</h3>
            <button
              onClick={addColumn}
              className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              เพิ่ม Column
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 px-4 py-2 text-left">ชื่อ Column</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">ประเภทข้อมูล</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">ความยาว</th>
                  <th className="border border-gray-300 px-4 py-2 text-center">Primary</th>
                  <th className="border border-gray-300 px-4 py-2 text-center">Required</th>
                  <th className="border border-gray-300 px-4 py-2 text-center">Unique</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Default</th>
                  <th className="border border-gray-300 px-4 py-2 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {newTable.columns.map((column, index) => (
                  <tr key={index}>
                    <td className="border border-gray-300 px-2 py-2">
                      <input
                        type="text"
                        value={column.name}
                        onChange={(e) => updateColumn(index, 'name', e.target.value)}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="column_name"
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2">
                      <select
                        value={column.type}
                        onChange={(e) => updateColumn(index, 'type', e.target.value)}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        {dataTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    </td>
                    <td className="border border-gray-300 px-2 py-2">
                      <input
                        type="number"
                        value={column.length || ''}
                        onChange={(e) => updateColumn(index, 'length', parseInt(e.target.value) || undefined)}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="100"
                        disabled={!['VARCHAR', 'CHAR', 'DECIMAL', 'NUMERIC'].includes(column.type)}
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={column.isPrimary}
                        onChange={(e) => updateColumn(index, 'isPrimary', e.target.checked)}
                        className="rounded"
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={column.isRequired}
                        onChange={(e) => updateColumn(index, 'isRequired', e.target.checked)}
                        className="rounded"
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={column.isUnique}
                        onChange={(e) => updateColumn(index, 'isUnique', e.target.checked)}
                        className="rounded"
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2">
                      <input
                        type="text"
                        value={column.defaultValue}
                        onChange={(e) => updateColumn(index, 'defaultValue', e.target.value)}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="'value' or NULL"
                      />
                    </td>
                    <td className="border border-gray-300 px-2 py-2 text-center">
                      <button
                        onClick={() => removeColumn(index)}
                        disabled={newTable.columns.length <= 1}
                        className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* SQL Preview */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">SQL Preview</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
            <pre className="text-sm font-mono">
              {newTable.name ? generateSQL() : '-- กรุณาใส่ชื่อตารางก่อน'}
            </pre>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleCreateTable}
            disabled={loading || !newTable.name.trim() || newTable.columns.some(col => !col.name.trim())}
            className="flex items-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            สร้างตาราง
          </button>
          
          <button
            onClick={() => {
              navigator.clipboard.writeText(generateSQL());
              showSuccess('คัดลอก SQL สำเร็จ!');
            }}
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <Copy className="h-4 w-4 mr-2" />
            คัดลอก SQL
          </button>
        </div>
      </div>
    </div>
  );

  // Main Render
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Database className="h-8 w-8 text-blue-600 mr-3" />
                ระบบจัดการข้อมูลแบบครบวงจร
              </h1>
              <p className="text-gray-600 mt-2">
                นำเข้าข้อมูล จัดการ Schema และ Tables สำหรับ {currentCompany?.name}
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setCurrentView('overview')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  currentView === 'overview'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Layout className="h-4 w-4 inline mr-2" />
                ภาพรวม
              </button>
              
              <button
                onClick={() => setCurrentView('import-data')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  currentView === 'import-data'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Upload className="h-4 w-4 inline mr-2" />
                นำเข้าข้อมูล
              </button>
              
              <button
                onClick={() => setCurrentView('create-table')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  currentView === 'create-table'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Table className="h-4 w-4 inline mr-2" />
                สร้างตาราง
              </button>
              
              <button
                onClick={loadSchemas}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 inline mr-2 ${loading ? 'animate-spin' : ''}`} />
                รีเฟรช
              </button>
            </div>
          </div>
        </div>

        {/* Notification */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-lg flex items-center ${
            message.type === 'success' 
              ? 'bg-green-100 text-green-800 border border-green-200' 
              : 'bg-red-100 text-red-800 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <Check className="h-5 w-5 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 mr-2" />
            )}
            {message.text}
          </div>
        )}

        {/* Main Content */}
        {currentView === 'overview' && renderOverview()}
        {currentView === 'import-data' && renderImportData()}
        {currentView === 'create-schema' && renderCreateSchema()}
        {currentView === 'create-table' && renderCreateTable()}
      </div>
    </div>
  );
};

export default UnifiedDataManagementSystem;