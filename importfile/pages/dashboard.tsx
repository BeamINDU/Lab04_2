// importfile/pages/dashboard.tsx - Updated for Unified System
import { useSession } from 'next-auth/react';
import AuthGuard from '../components/AuthGuard';
import Layout from '../components/Layout';
import UnifiedDataManagementSystem from '../components/SchemaManagementSystem';

export default function Dashboard() {
  return (
    <AuthGuard>
      <Layout>
        <UnifiedDataManagementSystem />
      </Layout>
    </AuthGuard>
  );
}