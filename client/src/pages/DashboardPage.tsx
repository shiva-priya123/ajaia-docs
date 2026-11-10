import { useState } from 'react';
import { deleteDocument } from '../api/documents.api';
import DocumentList from '../components/dashboard/DocumentList';
import NewDocButton from '../components/dashboard/NewDocButton';
import UploadButton, { IMPORT_HINT } from '../components/dashboard/UploadButton';
import Layout from '../components/layout/Layout';
import Alert from '../components/ui/Alert';
import Spinner from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';
import { useDocuments } from '../hooks/useDocuments';
import type { Document } from '../types';
import { getErrorMessage } from '../utils/errors';

type Tab = 'owned' | 'shared';

export default function DashboardPage() {
  const { user } = useAuth();
  const { documents, setDocuments, loading, error, reload } = useDocuments();
  const [tab, setTab] = useState<Tab>('owned');
  const [actionError, setActionError] = useState<string | null>(null);

  const owned = documents.filter((d) => d.role === 'owner');
  const shared = documents.filter((d) => d.role !== 'owner');
  const visible = tab === 'owned' ? owned : shared;

  async function handleDelete(doc: Document) {
    setActionError(null);
    try {
      await deleteDocument(doc.id);
      setDocuments((docs) => docs.filter((d) => d.id !== doc.id));
    } catch (err) {
      setActionError(getErrorMessage(err, `Could not delete “${doc.title}”.`));
    }
  }

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: 'owned', label: 'My documents', count: owned.length },
    { id: 'shared', label: 'Shared with me', count: shared.length },
  ];

  return (
    <Layout>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {user ? `Welcome back, ${user.name}` : 'Documents'}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Start a new document or import one ({IMPORT_HINT}).
          </p>
        </div>
        <div className="flex gap-2">
          <UploadButton onError={setActionError} />
          <NewDocButton onError={setActionError} />
        </div>
      </div>

      {actionError && (
        <div className="mt-6">
          <Alert onDismiss={() => setActionError(null)}>{actionError}</Alert>
        </div>
      )}

      <div role="tablist" aria-label="Documents" className="mt-8 flex gap-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition ${
              tab === t.id
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.label}
            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{t.count}</span>
          </button>
        ))}
      </div>

      <section className="mt-6" role="tabpanel">
        {loading ? (
          <Spinner className="py-16" label="Loading documents…" />
        ) : error ? (
          <Alert
            action={
              <button type="button" onClick={() => void reload()} className="font-medium underline">
                Retry
              </button>
            }
          >
            {error}
          </Alert>
        ) : (
          <DocumentList
            documents={visible}
            onDelete={handleDelete}
            emptyState={
              tab === 'owned'
                ? 'You have no documents yet. Create one or import a file to get started.'
                : 'Nothing has been shared with you yet. Documents others share with you will appear here.'
            }
          />
        )}
      </section>
    </Layout>
  );
}
