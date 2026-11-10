import { Eye, FileText, PencilLine, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Document } from '../../types';
import { extractPlainText } from '../../utils/docText';
import { formatDate } from '../../utils/formatDate';

interface DocumentCardProps {
  document: Document;
  onDelete?: (doc: Document) => Promise<void> | void;
}

export default function DocumentCard({ document: doc, onDelete }: DocumentCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const preview = extractPlainText(doc.content);
  const isOwner = doc.role === 'owner';

  return (
    <article className="group relative flex flex-col rounded-xl border border-slate-200 bg-white shadow-xs transition hover:border-slate-300 hover:shadow-md">
      <Link to={`/documents/${doc.id}`} className="flex flex-1 flex-col p-4 focus:outline-none" aria-label={`Open ${doc.title}`}>
        <div className="mb-3 h-24 overflow-hidden rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-500">
          {preview || <span className="italic text-slate-400">Empty document</span>}
        </div>
        <h3 className="flex items-center gap-2 font-medium text-slate-900">
          <FileText className="h-4 w-4 shrink-0 text-blue-600" aria-hidden />
          <span className="truncate">{doc.title}</span>
        </h3>
        <p className="mt-1 text-xs text-slate-500">Edited {formatDate(doc.updated_at)}</p>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          {isOwner ? (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">Owned by you</span>
          ) : (
            <>
              <span className="rounded-full bg-blue-50 px-2 py-0.5 font-medium text-blue-700">Shared by {doc.owner_name}</span>
              {doc.role === 'editor' ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
                  <PencilLine className="h-3 w-3" aria-hidden /> Can edit
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800">
                  <Eye className="h-3 w-3" aria-hidden /> View only
                </span>
              )}
            </>
          )}
        </div>
      </Link>

      {isOwner && onDelete && (
        <div className="border-t border-slate-100 px-4 py-2 text-xs">
          {confirming ? (
            <div className="flex items-center justify-between gap-2">
              <span className="text-slate-600">Delete for everyone?</span>
              <span className="flex gap-1">
                <button
                  type="button"
                  className="rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100"
                  onClick={() => setConfirming(false)}
                  disabled={deleting}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="rounded-md bg-red-600 px-2 py-1 font-medium text-white hover:bg-red-700 disabled:opacity-60"
                  disabled={deleting}
                  onClick={async () => {
                    setDeleting(true);
                    try {
                      await onDelete(doc);
                    } finally {
                      setDeleting(false);
                      setConfirming(false);
                    }
                  }}
                >
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </span>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-slate-500 hover:bg-red-50 hover:text-red-700"
              aria-label={`Delete ${doc.title}`}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden /> Delete
            </button>
          )}
        </div>
      )}
    </article>
  );
}
