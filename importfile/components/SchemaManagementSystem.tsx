// components/SchemaManagementSystem.tsx - Complete Multi-tenant version

import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { 
  Database, Plus, Table, Upload, History, Search,
  RefreshCw, Layout, ArrowLeft, AlertCircle, Check,
  FileText, Download, Settings, Eye, Trash2,
  Save, Copy, Filter, Building, Users
} from 'lucide-react';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================
interface Company {
  code: string;
  name: string;
  dbName: string;
  description: string;
  location: string;
  port: number;
  userRole?: string;
  userName?: string;
  userEmail?: string;
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
// MAIN COMPONENT - Multi-Tenant Version
// ============================================================================
const SchemaManagementSystem: React.FC = () => {
  const { data: session, status } = useSession();
  const { message, showSuccess, showError, clear } = useNotification();
  
  // State Management
  const [currentView, setCurrentView] = useState<'overview' | 'import-data' | 'create-schema' | 'create-table' | 'manage-tables'>('overview');
  const [currentCompany, setCurrentCompany] = useState<Company | null>(null);
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Form states
  const [selectedFile, setSelectedFile] = useState<ImportFile>({ file: null, name: '', type: '', size: 0 });
  const [selectedSchema, setSelectedSchema] = useState('');
  const [selectedTable, setSelectedTable] = useState('');
  const [importOptions, setImportOptions] = useState({
    hasHeader: true,
    onDuplicate: 'skip' as 'skip' | 'update' | 'error',
    batchSize: 1000
  });

  const [newSchema, setNewSchema] = useState({ name: '', description: '' });
  const [newTable, setNewTable] = useState({
    name: '',
    description: '',
    schema: 'public',
    columns: [{ 
      name: 'id', 
      type: 'SERIAL', 
      length: undefined,
      isPrimary: true, 
      isRequired: true, 
      isUnique: false, 
      defaultValue: '' 
    } as Column]
  });

  // ============================================================================
  // API FUNCTIONS - Multi-tenant version
  // ============================================================================
  
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`/api${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'x-company-code': currentCompany?.code || '',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  };

  // Load current user's company info
  const loadCompanyInfo = async () => {
    if (!session?.user) return;
    
    try {
      const response = await apiCall('/user/company');
      setCurrentCompany(response.company);
    } catch (error: any) {
      console.error('Error loading company info:', error);
      showError('ไม่สามารถโหลดข้อมูลบริษัทได้');
    }
  };

  // Load schemas from user's company database
  const loadSchemas = async () => {
    if (!currentCompany) return;
    
    setLoading(true);
    try {
      const response = await apiCall('/database/schemas');
      setSchemas(response.schemas);
    } catch (error: any) {
      console.error('Error loading schemas:', error);
      showError('ไม่สามารถโหลดข้อมูล Schema ได้');
    } finally {
      setLoading(false);
    }
  };

  // Create new schema in user's company database
  const handleCreateSchema = async () => {
    if (!newSchema.name.trim()) {
      showError('กรุณาใส่ชื่อ Schema');
      return;
    }

    setLoading(true);
    try {
      await apiCall('/database/schemas', {
        method: 'POST',
        body: JSON.stringify({
          name: newSchema.name,
          description: newSchema.description
        }),
      });

      showSuccess(`สร้าง Schema "${newSchema.name}" ใน ${currentCompany?.name} สำเร็จ!`);
      setNewSchema({ name: '', description: '' });
      loadSchemas();
    } catch (error: any) {
      console.error('Error creating schema:', error);
      showError(`เกิดข้อผิดพลาดในการสร้าง Schema: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Create new table in user's company database
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
      await apiCall('/database/tables', {
        method: 'POST',
        body: JSON.stringify({
          name: newTable.name,
          schema: newTable.schema,
          description: newTable.description,
          columns: newTable.columns
        }),
      });

      showSuccess(`สร้างตาราง "${newTable.name}" ใน ${currentCompany?.name} สำเร็จ!`);
      
      // Reset form
      setNewTable({
        name: '',
        description: '',
        schema: 'public',
        columns: [{ 
          name: 'id', 
          type: 'SERIAL', 
          length: undefined,
          isPrimary: true, 
          isRequired: true, 
          isUnique: false, 
          defaultValue: '' 
        } as Column]
      });
      
      loadSchemas();
    } catch (error: any) {
      console.error('Error creating table:', error);
      showError(`เกิดข้อผิดพลาดในการสร้างตาราง: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Import data to user's company database
  const handleImport = async () => {
    if (!selectedFile.file || !selectedTable || !selectedSchema) {
      showError('กรุณาเลือกไฟล์, Schema และตารางปลายทาง');
      return;
    }

    setLoading(true);
    try {
      // Parse file data
      let data;
      const fileContent = await selectedFile.file.text();
      
      if (selectedFile.type === 'text/csv') {
        // Parse CSV
        const lines = fileContent.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        data = lines.slice(importOptions.hasHeader ? 1 : 0)
          .filter(line => line.trim())
          .map(line => {
            const values = line.split(',');
            const row: any = {};
            headers.forEach((header, index) => {
              row[header] = values[index]?.trim() || null;
            });
            return row;
          });
      } else if (selectedFile.type === 'application/json') {
        data = JSON.parse(fileContent);
      } else {
        throw new Error('รองรับเฉพาะไฟล์ CSV และ JSON เท่านั้น');
      }

      // Import to company database
      const response = await apiCall('/database/import', {
        method: 'POST',
        body: JSON.stringify({
          schemaName: selectedSchema,
          tableName: selectedTable,
          data: data,
          options: importOptions
        }),
      });

      showSuccess(`${response.message} (${response.insertedRows} แถว)`);
      
      // Reset form
      setSelectedFile({ file: null, name: '', type: '', size: 0 });
      setSelectedTable('');
      setSelectedSchema('');
    } catch (error: any) {
      console.error('Error importing data:', error);
      showError(`เกิดข้อผิดพลาดในการนำเข้าข้อมูล: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================

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
    if (!newTable.name.trim()) return '-- กรุณาใส่ชื่อตารางก่อน';
    
    const validColumns = newTable.columns.filter(col => col.name.trim());
    if (validColumns.length === 0) return '-- กรุณาเพิ่ม Column อย่างน้อย 1 อัน';
    
    let sql = `CREATE TABLE "${newTable.schema}"."${newTable.name}" (\n`;
    
    const columnDefs = validColumns.map(col => {
      let def = `  "${col.name}" ${col.type}`;
      if (col.length && ['VARCHAR', 'CHAR'].includes(col.type.toUpperCase())) {
        def += `(${col.length})`;
      }
      if (col.isRequired && !col.isPrimary) def += ' NOT NULL';
      if (col.isUnique && !col.isPrimary) def += ' UNIQUE';
      if (col.defaultValue && !col.type.includes('SERIAL')) {
        def += ` DEFAULT ${isNaN(col.defaultValue as any) ? `'${col.defaultValue}'` : col.defaultValue}`;
      }
      return def;
    });
    
    sql += columnDefs.join(',\n');
    
    const primaryKeys = validColumns.filter(col => col.isPrimary);
    if (primaryKeys.length > 0) {
      sql += `,\n  PRIMARY KEY (${primaryKeys.map(col => `"${col.name}"`).join(', ')})`;
    }
    
    sql += '\n);';
    
    if (newTable.description) {
      sql += `\n\nCOMMENT ON TABLE "${newTable.schema}"."${newTable.name}" IS '${newTable.description}';`;
    }
    
    return sql;
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

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    if (session?.user) {
      loadCompanyInfo();
    }
  }, [session]);

  useEffect(() => {
    if (currentCompany) {
      loadSchemas();
    }
  }, [currentCompany]);

  // ============================================================================
  // RENDER FUNCTIONS
  // ============================================================================

  const renderCompanyHeader = () => (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-sm p-6 mb-6 text-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Building className="h-8 w-8 mr-4" />
          <div>
            <h2 className="text-2xl font-bold">{currentCompany?.name}</h2>
            <p className="text-blue-100 mt-1">
              {currentCompany?.description} • {currentCompany?.location}
            </p>
            <div className="flex items-center mt-2 space-x-4">
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                Database: {currentCompany?.dbName}
              </span>
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                Port: {currentCompany?.port}
              </span>
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                Role: {currentCompany?.userRole}
              </span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className="text-blue-100">Welcome, {currentCompany?.userName}</p>
          <p className="text-blue-200 text-sm">{currentCompany?.userEmail}</p>
        </div>
      </div>
    </div>
  );

  const renderNotification = () => {
    if (!message.text) return null;
    
    return (
      <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
        message.type === 'success' 
          ? 'bg-green-100 border border-green-400 text-green-700'
          : 'bg-red-100 border border-red-400 text-red-700'
      }`}>
        <div className="flex items-center">
          {message.type === 'success' ? (
            <Check className="h-5 w-5 mr-2" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-2" />
          )}
          <span>{message.text}</span>
          <button onClick={clear} className="ml-4 text-gray-500 hover:text-gray-700">
            ×
          </button>
        </div>
      </div>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
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
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">กำลังโหลดข้อมูล...</p>
            </div>
          ) : schemas.length === 0 ? (
            <div className="text-center py-8">
              <Database className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">ไม่มี Schema ในระบบ</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {schemas.map((schema) => (
                <div key={schema.name} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900">{schema.name}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${
                      schema.type === 'default' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {schema.type === 'default' ? 'ระบบ' : 'กำหนดเอง'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    {schema.tables.length} ตาราง
                  </p>
                  <div className="space-y-1">
                    {schema.tables.map((table) => (
                      <div key={table} className="text-sm text-gray-500 bg-gray-50 px-2 py-1 rounded">
                        {table}
                      </div>
                    ))}
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
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">สร้าง Schema ใหม่</h2>
            <p className="text-gray-600">สำหรับ {currentCompany?.name}</p>
          </div>
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
              placeholder="เช่น inventory, sales, hr"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">คำอธิบาย</label>
            <input
              type="text"
              value={newSchema.description}
              onChange={(e) => setNewSchema(prev => ({ ...prev, description: e.target.value }))}
              placeholder="คำอธิบายเกี่ยวกับ Schema นี้"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="mt-6">
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
  );

  const renderCreateTable = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">สร้างตารางใหม่</h2>
            <p className="text-gray-600">สำหรับ {currentCompany?.name} - Schema: {newTable.schema}</p>
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
              <option value="public">public</option>
              {schemas.filter(s => s.type === 'custom').map(schema => (
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

        {/* Columns Definition */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Columns</h3>
            <button
              onClick={addColumn}
              className="flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              เพิ่ม Column
            </button>
          </div>

          <div className="space-y-4">
            {newTable.columns.map((column, index) => (
              <div key={index} className="grid grid-cols-12 gap-4 items-center p-4 bg-gray-50 rounded-lg">
                <div className="col-span-3">
                  <input
                    type="text"
                    value={column.name}
                    onChange={(e) => updateColumn(index, 'name', e.target.value)}
                    placeholder="Column name"
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                  />
                </div>

                <div className="col-span-2">
                  <select
                    value={column.type}
                    onChange={(e) => updateColumn(index, 'type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                  >
                    <option value="VARCHAR">VARCHAR</option>
                    <option value="INTEGER">INTEGER</option>
                    <option value="BIGINT">BIGINT</option>
                    <option value="DECIMAL">DECIMAL</option>
                    <option value="TEXT">TEXT</option>
                    <option value="DATE">DATE</option>
                    <option value="TIMESTAMP">TIMESTAMP</option>
                    <option value="BOOLEAN">BOOLEAN</option>
                    <option value="SERIAL">SERIAL</option>
                    <option value="UUID">UUID</option>
                  </select>
                </div>

                <div className="col-span-1">
                  <input
                    type="number"
                    value={column.length || ''}
                    onChange={(e) => updateColumn(index, 'length', parseInt(e.target.value) || undefined)}
                    placeholder="Length"
                    className="w-full px-2 py-2 border border-gray-300 rounded text-sm"
                    disabled={!['VARCHAR', 'CHAR'].includes(column.type)}
                  />
                </div>

                <div className="col-span-2">
                  <input
                    type="text"
                    value={column.defaultValue}
                    onChange={(e) => updateColumn(index, 'defaultValue', e.target.value)}
                    placeholder="Default"
                    className="w-full px-2 py-2 border border-gray-300 rounded text-sm"
                  />
                </div>

                <div className="col-span-3 flex space-x-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={column.isPrimary}
                      onChange={(e) => updateColumn(index, 'isPrimary', e.target.checked)}
                      className="rounded mr-1"
                    />
                    <span className="text-xs">PK</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={column.isRequired}
                      onChange={(e) => updateColumn(index, 'isRequired', e.target.checked)}
                      className="rounded mr-1"
                    />
                    <span className="text-xs">Required</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={column.isUnique}
                      onChange={(e) => updateColumn(index, 'isUnique', e.target.checked)}
                      className="rounded mr-1"
                    />
                    <span className="text-xs">Unique</span>
                  </label>
                </div>

                <div className="col-span-1 flex justify-end">
                  <button
                    onClick={() => removeColumn(index)}
                    disabled={newTable.columns.length <= 1}
                    className="text-red-500 hover:text-red-700 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SQL Preview */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">SQL Preview</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            <pre>{generateSQL()}</pre>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleCreateTable}
            disabled={loading || !newTable.name.trim() || newTable.columns.some(col => !col.name.trim())}
            className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
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

  const renderImportData = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">นำเข้าข้อมูล</h2>
            <p className="text-gray-600">สำหรับ {currentCompany?.name}</p>
          </div>
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            กลับ
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* File Upload */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">เลือกไฟล์</h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <input
                type="file"
                onChange={handleFileSelect}
                accept=".csv,.json,.xlsx"
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Upload className="h-4 w-4 mr-2" />
                เลือกไฟล์
              </label>
              <p className="text-sm text-gray-500 mt-2">
                รองรับ CSV, JSON, Excel (.xlsx)
              </p>
              
              {selectedFile.name && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                  <p className="text-sm text-green-800">
                    <strong>ไฟล์:</strong> {selectedFile.name}
                  </p>
                  <p className="text-sm text-green-600">
                    ขนาด: {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Target Selection */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">เลือกตารางปลายทาง</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Schema</label>
                <select
                  value={selectedSchema}
                  onChange={(e) => {
                    setSelectedSchema(e.target.value);
                    setSelectedTable(''); // Reset table selection
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">เลือก Schema...</option>
                  {schemas.map(schema => (
                    <option key={schema.name} value={schema.name}>{schema.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">ตาราง</label>
                <select
                  value={selectedTable}
                  onChange={(e) => setSelectedTable(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  disabled={!selectedSchema}
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
                      onChange={(e) => setImportOptions(prev => ({ ...prev, onDuplicate: e.target.value as 'skip' | 'update' | 'error' }))}
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
            disabled={loading || !selectedFile.file || !selectedTable || !selectedSchema}
            className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-2" />
            )}
            นำเข้าข้อมูล
          </button>
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
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">กรุณาเข้าสู่ระบบ</p>
        </div>
      </div>
    );
  }

  if (!currentCompany) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Building className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">กำลังโหลดข้อมูลบริษัท...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {renderNotification()}
        {renderCompanyHeader()}
        
        {/* Navigation Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Database className="h-8 w-8 text-blue-600 mr-3" />
                ระบบจัดการข้อมูลแบบครบวงจร
              </h1>
              <p className="text-gray-600 mt-2">
                นำเข้าข้อมูล จัดการ Schema และ Tables สำหรับ {currentCompany.name}
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
                onClick={() => setCurrentView('create-schema')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  currentView === 'create-schema'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Database className="h-4 w-4 inline mr-2" />
                สร้าง Schema
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        {currentView === 'overview' && renderOverview()}
        {currentView === 'create-schema' && renderCreateSchema()}
        {currentView === 'create-table' && renderCreateTable()}
        {currentView === 'import-data' && renderImportData()}
      </div>
    </div>
  );
};

export default SchemaManagementSystem;