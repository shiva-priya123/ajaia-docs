import { Plus } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createDocument } from '../../api/documents.api';
import { DEFAULT_DOC_TITLE } from '../../utils/constants';
import { getErrorMessage } from '../../utils/errors';

export default function NewDocButton({ onError }: { onError: (message: string) => void }) {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);

  async function handleClick() {
    setCreating(true);
    try {
      const doc = await createDocument(DEFAULT_DOC_TITLE);
      navigate(`/documents/${doc.id}`, { state: { isNew: true } });
    } catch (err) {
      onError(getErrorMessage(err, 'Could not create a document.'));
      setCreating(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={creating}
      className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
    >
      <Plus className="h-4 w-4" aria-hidden />
      {creating ? 'Creating…' : 'New document'}
    </button>
  );
}
