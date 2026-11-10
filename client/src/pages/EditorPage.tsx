import type { Editor } from '@tiptap/react';
import { ArrowLeft } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import SaveIndicator from '../components/editor/SaveIndicator';
import TipTapEditor from '../components/editor/TipTapEditor';
import TitleInput from '../components/editor/TitleInput';
import Header from '../components/layout/Header';
import ShareButton from '../components/sharing/ShareButton';
import Alert from '../components/ui/Alert';
import Spinner from '../components/ui/Spinner';
import { useAutoSave } from '../hooks/useAutoSave';
import { useDocument } from '../hooks/useDocument';
import type { Document } from '../types';

const BackLink = () => (
  <Link
    to="/"
    className="shrink-0 rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
    aria-label="Back to documents"
    title="Back to documents"
  >
    <ArrowLeft className="h-5 w-5" />
  </Link>
);

export default function EditorPage() {
  const { id } = useParams<{ id: string }>();
  const { document, setDocument, loading, error } = useDocument(id);

  if (loading || error || !document) {
    return (
      <div className="min-h-full">
        <Header>
          <BackLink />
        </Header>
        <main className="mx-auto max-w-3xl px-4 py-16">
          {loading ? (
            <Spinner label="Opening document…" />
          ) : (
            <Alert action={<Link to="/" className="font-medium underline">Back to documents</Link>}>
              {error?.message ?? 'Could not open this document.'}
            </Alert>
          )}
        </main>
      </div>
    );
  }

  // Keyed by id so navigating between documents resets editor + save state.
  return <DocumentEditor key={document.id} document={document} onSaved={setDocument} />;
}

function DocumentEditor({ document: doc, onSaved }: { document: Document; onSaved: (d: Document) => void }) {
  const location = useLocation();
  const navState = (location.state ?? {}) as { isNew?: boolean; imported?: string };
  const canEdit = doc.role !== 'viewer';
  const isOwner = doc.role === 'owner';

  const [title, setTitle] = useState(doc.title);
  const [importNotice, setImportNotice] = useState(navState.imported ?? null);
  const editorRef = useRef<Editor | null>(null);

  const autosave = useAutoSave({
    documentId: doc.id,
    initialVersion: doc.updated_at,
    enabled: canEdit,
    onSaved,
  });

  // Ctrl/Cmd+S saves immediately instead of opening the browser's save dialog.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (canEdit) void autosave.flush();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [autosave.flush, canEdit]);

  useEffect(() => {
    window.document.title = `${title} · Ajaia Docs`;
    return () => {
      window.document.title = 'Ajaia Docs';
    };
  }, [title]);

  const banner = (
    <>
      {autosave.status === 'conflict' && (
        <Alert
          tone="error"
          action={
            <span className="flex shrink-0 gap-3 font-medium">
              <button type="button" className="underline" onClick={() => window.location.reload()}>
                Load latest
              </button>
              <button type="button" className="underline" onClick={() => void autosave.overwrite()}>
                Keep mine
              </button>
            </span>
          }
        >
          Someone else changed this document while you were editing. Your latest changes are not saved yet. Load
          their version (discarding yours) or keep yours (replacing theirs).
        </Alert>
      )}
      {!canEdit && (
        <Alert tone="info">
          You have view-only access. Ask {doc.owner_name} for edit access if you need to make changes.
        </Alert>
      )}
      {importNotice && (
        <Alert tone="success" onDismiss={() => setImportNotice(null)}>
          Imported “{importNotice}”. Formatting such as headings, bold, italics and lists was kept; images and tables
          are not supported yet.
        </Alert>
      )}
    </>
  );

  return (
    <div className="flex min-h-full flex-col">
      <Header
        actions={
          isOwner ? (
            <ShareButton document={{ ...doc, title }} />
          ) : (
            <span className="hidden shrink-0 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 sm:inline">
              Shared by {doc.owner_name}
            </span>
          )
        }
      >
        <BackLink />
        <div className="min-w-0 max-w-xl flex-1">
          <TitleInput
            value={title}
            disabled={!canEdit}
            autoFocus={Boolean(navState.isNew)}
            onChange={(t) => {
              setTitle(t);
              autosave.queue({ title: t });
            }}
            onEnter={() => editorRef.current?.commands.focus('start')}
          />
        </div>
        <SaveIndicator
          status={autosave.status}
          readOnly={!canEdit}
          lastSavedAt={autosave.lastSavedAt}
          onRetry={() => void autosave.flush()}
        />
      </Header>

      <TipTapEditor
        initialContent={doc.content}
        editable={canEdit}
        onChange={(json) => autosave.queue({ content: json })}
        onReady={(editor) => {
          editorRef.current = editor;
        }}
        banner={banner}
      />
    </div>
  );
}
