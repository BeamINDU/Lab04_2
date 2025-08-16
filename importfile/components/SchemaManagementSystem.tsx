// components/SchemaManagementSystem.tsx - Complete Multi-tenant version with Bug Fixes

import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { 
  Database, Plus, Table, Upload, History, Search,
  RefreshCw, Layout, ArrowLeft, AlertCircle, Check,
  FileText, Download, Settings, Eye, Trash2,
  Save, Copy, Filter, Building, Users, X,
  CheckCircle, Loader
} from 'lucide-react';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================
interface Company {
  id: string;
  code: string;
  name: string;
  dbName: string;
  description: string;
  location: string;
}

interface Schema {
  name: string;
  type: 'default' | 'custom';
  description?: string;
  tables: string[];
  tableDetails?: Array<{ name: string; comment?: string }>;
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

  const showSuccess = (text: string) => {
    setMessage({ type: 'success', text });
    console.log('✅ Success:', text);
  };
  
  const showError = (text: string) => {
    setMessage({ type: 'error', text });
    console.error('❌ Error:', text);
  };
  
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
  const [error, setError] = useState('');
  
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

  // Debug states
  useEffect(() => {
    console.log('🔄 Component state changed:');
    console.log('- Loading:', loading);
    console.log('- Current Company:', currentCompany?.name || 'null');
    console.log('- Schemas:', schemas.length);
    console.log('- Error:', error || 'none');
    console.log('- Session Status:', status);
  }, [loading, currentCompany, schemas.length, error, status]);

  // ============================================================================
  // API FUNCTIONS - Multi-tenant version with improved error handling
  // ============================================================================
  
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    console.log(`🌐 apiCall called with endpoint: ${endpoint}`);
    console.log(`🔧 Options:`, options);
    
    try {
      const url = `/api${endpoint}`;
      const headers = {
        'Content-Type': 'application/json',
        'x-company-code': currentCompany?.code || '',
        ...options.headers,
      };
      
      console.log(`📍 Full URL: ${url}`);
      console.log(`📋 Headers:`, headers);
      
      const response = await fetch(url, {
        headers,
        ...options,
      });

      console.log(`📊 Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        let errorMessage = 'Unknown error';
        try {
          const errorData = await response.json();
          console.log(`📋 Error data:`, errorData);
          errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;
        } catch (parseError) {
          console.log(`❌ Failed to parse error response:`, parseError);
          errorMessage = `HTTP ${response.status} - ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log(`📨 API Response:`, result);
      return result;

    } catch (error) {
      console.error(`❌ API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  // Load current user's company info
  const loadCompanyInfo = async () => {
    console.log('🔍 loadCompanyInfo called');
    
    if (!session?.user) {
      console.log('❌ No session or user found');
      return;
    }
    
    console.log('✅ Session exists, proceeding with API call');
    
    try {
      setLoading(true);
      setError('');
      
      const response = await apiCall('/user/company');
      
      if (response.success && response.data) {
        setCurrentCompany(response.data.company);
        console.log('✅ Company info loaded:', response.data.company);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Error loading company info:', error);
      setError(`Failed to load company information: ${errorMessage}`);
      showError('ไม่สามารถโหลดข้อมูลบริษัทได้');
    } finally {
      setLoading(false);
      console.log('🏁 loadCompanyInfo finished');
    }
  };

  // Load schemas from user's company database
  const loadSchemas = async () => {
    console.log('🔍 loadSchemas called');
    
    if (!currentCompany) {
      console.log('❌ No current company for loadSchemas');
      return;
    }
    
    console.log('✅ Current company exists, proceeding with schema loading');
    
    try {
      setLoading(true);
      setError('');
      
      const response = await apiCall('/database/schemas');
      
      if (response.success && response.schemas) {
        setSchemas(response.schemas);
        console.log('✅ Schemas loaded successfully:', response.schemas);
        
        if (response.mode === 'fallback') {
          console.log('⚠️ Using fallback data:', response.warning);
          showError('ใช้ข้อมูลสำรองเนื่องจากไม่สามารถเชื่อมต่อฐานข้อมูลได้');
        }
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Error loading schemas:', error);
      setError(`Failed to load schemas: ${errorMessage}`);
      showError('ไม่สามารถโหลดข้อมูล Schema ได้');
      
      // Set empty schemas as fallback
      setSchemas([]);
    } finally {
      setLoading(false);
      console.log('🏁 loadSchemas finished');
    }
  };

  // Create new schema in user's company database
  const handleCreateSchema = async () => {
    if (!newSchema.name.trim()) {
      showError('กรุณาใส่ชื่อ Schema');
      return;
    }

    try {
      setLoading(true);
      
      await apiCall('/database/schemas', {
        method: 'POST',
        body: JSON.stringify({
          name: newSchema.name,
          description: newSchema.description
        }),
      });

      showSuccess(`สร้าง Schema "${newSchema.name}" ใน ${currentCompany?.name} สำเร็จ!`);
      setNewSchema({ name: '', description: '' });
      setCurrentView('overview');
      await loadSchemas();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Error creating schema:', error);
      showError(`เกิดข้อผิดพลาดในการสร้าง Schema: ${errorMessage}`);
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
      showError('กรุณาใส่ชื่อคอลัมน์ให้ครบ');
      return;
    }

    try {
      setLoading(true);
      
      await apiCall('/database/tables', {
        method: 'POST',
        body: JSON.stringify({
          schema: newTable.schema,
          tableName: newTable.name,
          description: newTable.description,
          columns: newTable.columns
        }),
      });

      showSuccess(`สร้างตาราง "${newTable.name}" ใน Schema "${newTable.schema}" สำเร็จ!`);
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
        }]
      });
      setCurrentView('overview');
      await loadSchemas();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Error creating table:', error);
      showError(`เกิดข้อผิดพลาดในการสร้างตาราง: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  // Add column to new table
  const addColumn = () => {
    setNewTable(prev => ({
      ...prev,
      columns: [...prev.columns, {
        name: '',
        type: 'VARCHAR',
        length: 255,
        isPrimary: false,
        isRequired: false,
        isUnique: false,
        defaultValue: ''
      }]
    }));
  };

  // Remove column from new table
  const removeColumn = (index: number) => {
    setNewTable(prev => ({
      ...prev,
      columns: prev.columns.filter((_, i) => i !== index)
    }));
  };

  // Update column in new table
  const updateColumn = (index: number, field: keyof Column, value: any) => {
    setNewTable(prev => ({
      ...prev,
      columns: prev.columns.map((col, i) => 
        i === index ? { ...col, [field]: value } : col
      )
    }));
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
    console.log('🔄 Session effect triggered, status:', status);
    if (status === 'authenticated' && session?.user) {
      console.log('✅ Authenticated, calling loadCompanyInfo');
      loadCompanyInfo();
    }
  }, [session, status]);

  useEffect(() => {
    console.log('🔄 Company effect triggered');
    if (currentCompany) {
      console.log('✅ Company exists, calling loadSchemas');
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
                Code: {currentCompany?.code}
              </span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className="text-blue-100">Welcome, {session?.user?.name}</p>
          <p className="text-blue-200 text-sm">{session?.user?.email}</p>
        </div>
      </div>
    </div>
  );

  const renderNotification = () => {
    if (!message.text) return null;
    
    return (
      <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
        message.type === 'success' 
          ? 'bg-green-100 border border-green-400 text-green-700'
          : 'bg-red-100 border border-red-400 text-red-700'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {message.type === 'success' ? 
              <CheckCircle className="h-5 w-5 mr-2" /> : 
              <AlertCircle className="h-5 w-5 mr-2" />
            }
            <span className="font-medium">{message.text}</span>
          </div>
          <button onClick={clear} className="ml-2">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  };

  const renderNavigationTabs = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div className="flex flex-wrap gap-2">
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

        <button
          onClick={() => setCurrentView('create-table')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            currentView === 'create-table'
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Table className="h-4 w-4 inline mr-2" />
          สร้างตาราง
        </button>

        <button
          onClick={() => setCurrentView('import-data')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            currentView === 'import-data'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Upload className="h-4 w-4 inline mr-2" />
          นำเข้าข้อมูล
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
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Database className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{schemas.length}</h3>
              <p className="text-gray-600">Schemas</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Table className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {schemas.reduce((total, schema) => total + schema.tables.length, 0)}
              </h3>
              <p className="text-gray-600">Tables</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Building className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{currentCompany?.name}</h3>
              <p className="text-gray-600">Company</p>
            </div>
          </div>
        </div>
      </div>

      {/* Schemas List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Database Schemas</h2>
          <button
            onClick={() => setCurrentView('create-schema')}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            สร้าง Schema ใหม่
          </button>
        </div>

        {schemas.length === 0 ? (
          <div className="text-center py-12">
            <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">ไม่พบ Schema ในฐานข้อมูล</p>
            <button
              onClick={() => setCurrentView('create-schema')}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              สร้าง Schema แรก
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {schemas.map((schema, index) => (
              <div key={index} className="border rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <Database className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="font-medium text-gray-900">{schema.name}</h3>
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      schema.type === 'default' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {schema.type === 'default' ? 'ระบบ' : 'กำหนดเอง'}
                    </span>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">
                  {schema.description || 'ไม่มีคำอธิบาย'}
                </p>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    {schema.tables.length} ตาราง
                  </span>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentView('create-table')}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      เพิ่มตาราง
                    </button>
                  </div>
                </div>
                
                {schema.tables.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {schema.tables.slice(0, 3).map((table) => (
                      <div key={table} className="text-sm text-gray-500 bg-gray-50 px-2 py-1 rounded">
                        {table}
                      </div>
                    ))}
                    {schema.tables.length > 3 && (
                      <div className="text-sm text-gray-400">
                        และอีก {schema.tables.length - 3} ตาราง...
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
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
            {loading ? <Loader className="h-4 w-4 mr-2 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
            {loading ? 'กำลังสร้าง...' : 'สร้าง Schema'}
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

        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Schema *</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">ชื่อตาราง *</label>
            <input
              type="text"
              value={newTable.name}
              onChange={(e) => setNewTable(prev => ({ ...prev, name: e.target.value }))}
              placeholder="เช่น users, products, orders"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">คำอธิบาย</label>
            <input
              type="text"
              value={newTable.description}
              onChange={(e) => setNewTable(prev => ({ ...prev, description: e.target.value }))}
              placeholder="คำอธิบายเกี่ยวกับตารางนี้"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Columns */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">คอลัมน์</h3>
            <button
              onClick={addColumn}
              className="flex items-center px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            >
              <Plus className="h-4 w-4 mr-1" />
              เพิ่มคอลัมน์
            </button>
          </div>

          <div className="space-y-4">
            {newTable.columns.map((column, index) => (
              <div key={index} className="grid grid-cols-12 gap-2 items-center p-4 border rounded-lg">
                {/* Column Name */}
                <div className="col-span-3">
                  <input
                    type="text"
                    placeholder="ชื่อคอลัมน์"
                    value={column.name}
                    onChange={(e) => updateColumn(index, 'name', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Data Type */}
                <div className="col-span-2">
                  <select
                    value={column.type}
                    onChange={(e) => updateColumn(index, 'type', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="SERIAL">SERIAL</option>
                    <option value="INTEGER">INTEGER</option>
                    <option value="BIGINT">BIGINT</option>
                    <option value="VARCHAR">VARCHAR</option>
                    <option value="TEXT">TEXT</option>
                    <option value="BOOLEAN">BOOLEAN</option>
                    <option value="DATE">DATE</option>
                    <option value="TIMESTAMP">TIMESTAMP</option>
                    <option value="DECIMAL">DECIMAL</option>
                    <option value="JSON">JSON</option>
                  </select>
                </div>

                {/* Length */}
                <div className="col-span-1">
                  {['VARCHAR', 'DECIMAL'].includes(column.type) && (
                    <input
                      type="number"
                      placeholder="Length"
                      value={column.length || ''}
                      onChange={(e) => updateColumn(index, 'length', parseInt(e.target.value) || undefined)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}
                </div>

                {/* Checkboxes */}
                <div className="col-span-1 text-center">
                  <input
                    type="checkbox"
                    checked={column.isPrimary}
                    onChange={(e) => updateColumn(index, 'isPrimary', e.target.checked)}
                    className="rounded"
                    title="Primary Key"
                  />
                </div>

                <div className="col-span-1 text-center">
                  <input
                    type="checkbox"
                    checked={column.isRequired}
                    onChange={(e) => updateColumn(index, 'isRequired', e.target.checked)}
                    className="rounded"
                    title="Required"
                  />
                </div>

                <div className="col-span-1 text-center">
                  <input
                    type="checkbox"
                    checked={column.isUnique}
                    onChange={(e) => updateColumn(index, 'isUnique', e.target.checked)}
                    className="rounded"
                    title="Unique"
                  />
                </div>

                {/* Default Value */}
                <div className="col-span-2">
                  <input
                    type="text"
                    placeholder="Default value"
                    value={column.defaultValue}
                    onChange={(e) => updateColumn(index, 'defaultValue', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Remove Button */}
                <div className="col-span-1 text-center">
                  {newTable.columns.length > 1 && (
                    <button
                      onClick={() => removeColumn(index)}
                      className="text-red-600 hover:text-red-800"
                      title="ลบคอลัมน์"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Column Headers */}
          <div className="grid grid-cols-12 gap-2 items-center p-2 bg-gray-50 rounded text-xs text-gray-600 font-medium mt-2">
            <div className="col-span-3">ชื่อคอลัมน์</div>
            <div className="col-span-2">ชนิดข้อมูล</div>
            <div className="col-span-1">ขนาด</div>
            <div className="col-span-1 text-center">PK</div>
            <div className="col-span-1 text-center">จำเป็น</div>
            <div className="col-span-1 text-center">ไม่ซ้ำ</div>
            <div className="col-span-2">ค่าเริ่มต้น</div>
            <div className="col-span-1 text-center">ลบ</div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            ยกเลิก
          </button>
          
          <button
            onClick={handleCreateTable}
            disabled={loading || !newTable.name.trim() || newTable.columns.some(col => !col.name.trim())}
            className="flex items-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader className="h-4 w-4 mr-2 animate-spin" /> : <Table className="h-4 w-4 mr-2" />}
            {loading ? 'กำลังสร้าง...' : 'สร้างตาราง'}
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
            <p className="text-gray-600">นำเข้าข้อมูลจากไฟล์ CSV, Excel</p>
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
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">เลือกไฟล์</label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600 mb-2">ลากไฟล์มาวางที่นี่ หรือ</p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              เลือกไฟล์
            </label>
          </div>
          
          {selectedFile.file && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600">
                    ขนาด: {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <button
                  onClick={() => setSelectedFile({ file: null, name: '', type: '', size: 0 })}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Target Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Schema เป้าหมาย</label>
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">เลือก Schema</option>
              {schemas.map(schema => (
                <option key={schema.name} value={schema.name}>{schema.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ตารางเป้าหมาย</label>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              disabled={!selectedSchema}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            >
              <option value="">เลือกตาราง</option>
              {selectedSchema && schemas
                .find(s => s.name === selectedSchema)?.tables
                .map(table => (
                  <option key={table} value={table}>{table}</option>
                ))}
            </select>
          </div>
        </div>

        {/* Import Options */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">ตัวเลือกการนำเข้า</h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="hasHeader"
                checked={importOptions.hasHeader}
                onChange={(e) => setImportOptions(prev => ({ ...prev, hasHeader: e.target.checked }))}
                className="rounded"
              />
              <label htmlFor="hasHeader" className="ml-2 text-sm text-gray-700">
                แถวแรกเป็นหัวตาราง (Header)
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">จัดการข้อมูลซ้ำ</label>
              <select
                value={importOptions.onDuplicate}
                onChange={(e) => setImportOptions(prev => ({ ...prev, onDuplicate: e.target.value as 'skip' | 'update' | 'error' }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="skip">ข้าม (Skip)</option>
                <option value="update">อัพเดต (Update)</option>
                <option value="error">หยุดและแจ้งข้อผิดพลาด (Error)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">ขนาด Batch</label>
              <input
                type="number"
                value={importOptions.batchSize}
                onChange={(e) => setImportOptions(prev => ({ ...prev, batchSize: parseInt(e.target.value) || 1000 }))}
                min="100"
                max="10000"
                step="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentView('overview')}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            ยกเลิก
          </button>
          
          <button
            disabled={!selectedFile.file || !selectedSchema || !selectedTable || loading}
            className="flex items-center px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            {loading ? 'กำลังนำเข้า...' : 'เริ่มนำเข้าข้อมูล'}
          </button>
        </div>
      </div>
    </div>
  );

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  // Debug info for development
  const renderDebugInfo = () => {
    return (
      <div className="fixed bottom-4 left-4 bg-black text-white p-3 rounded text-xs z-50 max-w-xs">
        <div><strong>Debug Info:</strong></div>
        <div>Session Status: {status}</div>
        <div>Loading: {loading ? 'true' : 'false'}</div>
        <div>Company: {currentCompany ? currentCompany.name : 'null'}</div>
        <div>Schemas: {schemas.length}</div>
        <div>Error: {error || 'none'}</div>
        <div>Current View: {currentView}</div>
        <div>Should Show Main: {!!(status === 'authenticated' && currentCompany) ? 'YES' : 'NO'}</div>
      </div>
    );
  };

  // Debug current render state
  console.log('🎨 Rendering component with state:', {
    status,
    loading,
    currentCompany: !!currentCompany,
    error: !!error,
    hasSchemas: schemas.length > 0
  });

  // Loading states
  if (status === 'loading') {
    console.log('🔄 Rendering: Session loading');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader className="h-16 w-16 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">กำลังโหลดข้อมูล session...</p>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    console.log('🔄 Rendering: Unauthenticated');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">กรุณาเข้าสู่ระบบ</p>
        </div>
      </div>
    );
  }

  // Check if we have session but no company yet (and not errored)
  if (status === 'authenticated' && !currentCompany && !error) {
    console.log('🔄 Rendering: Loading company info');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader className="h-16 w-16 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">กำลังโหลดข้อมูลบริษัท...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-red-800 font-medium mb-2 text-center">เกิดข้อผิดพลาด</h3>
          <p className="text-red-700 mb-4 text-center">{error}</p>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={() => {
                setError('');
                if (session?.user) loadCompanyInfo();
              }}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              ลองใหม่
            </button>
            <button 
              onClick={() => window.location.reload()}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              รีโหลดหน้า
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main application
  console.log('🔄 Rendering: Main application');
  console.log('  - Has company:', !!currentCompany);
  console.log('  - Company name:', currentCompany?.name);
  console.log('  - Schemas count:', schemas.length);
  console.log('  - Loading:', loading);
  console.log('  - Error:', error);
  
  return (
    <div className="min-h-screen bg-gray-50">
      {renderDebugInfo()}
      {renderNotification()}
      
      <div className="max-w-7xl mx-auto p-6">
        {renderCompanyHeader()}
        {renderNavigationTabs()}
        
        {loading && currentView !== 'overview' ? (
          <div className="text-center py-12">
            <Loader className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">กำลังดำเนินการ...</p>
          </div>
        ) : (
          <>
            {currentView === 'overview' && renderOverview()}
            {currentView === 'create-schema' && renderCreateSchema()}
            {currentView === 'create-table' && renderCreateTable()}
            {currentView === 'import-data' && renderImportData()}
          </>
        )}
      </div>
    </div>
  );
};

export default SchemaManagementSystem;