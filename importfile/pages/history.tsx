import AuthGuard from '../components/AuthGuard';
import { ImportHistoryPage } from '../components/Layout';

export default function History() {
  return (
    <AuthGuard>
      <ImportHistoryPage />
    </AuthGuard>
  );
}
