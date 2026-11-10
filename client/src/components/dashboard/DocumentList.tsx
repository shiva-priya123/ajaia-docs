import type { ReactNode } from 'react';
import type { Document } from '../../types';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
  documents: Document[];
  emptyState: ReactNode;
  onDelete?: (doc: Document) => Promise<void> | void;
}

export default function DocumentList({ documents, emptyState, onDelete }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center text-sm text-slate-500">
        {emptyState}
      </div>
    );
  }
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {documents.map((doc) => (
        <li key={doc.id} className="flex">
          <div className="w-full">
            <DocumentCard document={doc} onDelete={onDelete} />
          </div>
        </li>
      ))}
    </ul>
  );
}
