import { Share2 } from 'lucide-react';
import { useState } from 'react';
import type { Document } from '../../types';
import ShareDialog from './ShareDialog';

export default function ShareButton({ document }: { document: Document }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Share"
        className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-blue-600 px-2.5 py-1.5 sm:px-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
      >
        <Share2 className="h-4 w-4" aria-hidden />
        <span className="hidden sm:inline">Share</span>
      </button>
      {open && <ShareDialog document={document} onClose={() => setOpen(false)} />}
    </>
  );
}
