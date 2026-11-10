import { Upload } from 'lucide-react';
import { useRef, useState, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadFile } from '../../api/upload.api';
import { IMPORT_EXTENSIONS, IMPORT_MAX_BYTES } from '../../utils/constants';
import { getErrorMessage } from '../../utils/errors';
import { validateImportFile } from '../../utils/files';

export const IMPORT_HINT = `${IMPORT_EXTENSIONS.join(', ')} · up to ${IMPORT_MAX_BYTES / (1024 * 1024)} MB`;

export default function UploadButton({ onError }: { onError: (message: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);

  async function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ''; // allow choosing the same file again after an error
    if (!file) return;

    const problem = validateImportFile(file);
    if (problem) {
      onError(problem);
      return;
    }

    setUploading(true);
    try {
      const result = await uploadFile(file);
      navigate(`/documents/${result.document_id}`, { state: { imported: file.name } });
    } catch (err) {
      onError(getErrorMessage(err, `Could not import “${file.name}”.`));
      setUploading(false);
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={IMPORT_EXTENSIONS.join(',')}
        className="sr-only"
        onChange={handleChange}
        data-testid="import-input"
        aria-label="Import a file"
        tabIndex={-1}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        title={`Create a new document from a file (${IMPORT_HINT})`}
        className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 disabled:opacity-60"
      >
        <Upload className="h-4 w-4" aria-hidden />
        {uploading ? 'Importing…' : 'Import file'}
      </button>
    </>
  );
}
