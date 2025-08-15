import { useSession } from 'next-auth/react';
import AuthGuard from '../components/AuthGuard';
import Layout from '../components/Layout';
import DataImportInterface from '../components/DataImportInterface';

export default function Dashboard() {
  return (
    <AuthGuard>
      <Layout>
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
            <DataImportInterface />
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
