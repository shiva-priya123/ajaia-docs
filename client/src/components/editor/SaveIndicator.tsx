import { AlertTriangle, Check, CloudOff, Eye, Loader2 } from 'lucide-react';
import type { SaveStatus } from '../../hooks/useAutoSave';

interface SaveIndicatorProps {
  status: SaveStatus;
  readOnly: boolean;
  lastSavedAt: Date | null;
  onRetry: () => void;
}

export default function SaveIndicator({ status, readOnly, lastSavedAt, onRetry }: SaveIndicatorProps) {
  const base = 'inline-flex shrink-0 items-center gap-1.5 text-xs whitespace-nowrap';

  if (readOnly) {
    return (
      <span className={`${base} rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800`}>
        <Eye className="h-3.5 w-3.5" aria-hidden /> <span className="max-sm:sr-only">View only</span>
      </span>
    );
  }

  let content;
  switch (status) {
    case 'pending':
      content = (
        <span className="inline-flex items-center gap-1.5 text-slate-500">
          <span className="h-2 w-2 rounded-full bg-amber-400" aria-hidden />
          <span className="hidden sm:inline">Unsaved changes</span>
          <span className="sr-only sm:hidden">Unsaved changes</span>
        </span>
      );
      break;
    case 'saving':
      content = (
        <span className="inline-flex items-center gap-1.5 text-slate-500">
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> <span className="max-sm:sr-only">Saving…</span>
        </span>
      );
      break;
    case 'saved':
      content = (
        <span className="inline-flex items-center gap-1.5 text-emerald-700" title={lastSavedAt ? `Saved at ${lastSavedAt.toLocaleTimeString()}` : undefined}>
          <Check className="h-3.5 w-3.5" aria-hidden /> <span className="max-sm:sr-only">Saved</span>
        </span>
      );
      break;
    case 'error':
      content = (
        <span className="inline-flex items-center gap-1.5 text-red-700">
          <CloudOff className="h-3.5 w-3.5" aria-hidden /> Not saved
          <button type="button" onClick={onRetry} className="font-medium underline underline-offset-2">
            Retry
          </button>
        </span>
      );
      break;
    case 'conflict':
      content = (
        <span className="inline-flex items-center gap-1.5 text-amber-700">
          <AlertTriangle className="h-3.5 w-3.5" aria-hidden /> <span className="max-sm:sr-only">Edit conflict</span>
        </span>
      );
      break;
    default:
      content = <span className="text-slate-400 max-sm:sr-only">All changes saved</span>;
  }

  return (
    <span className={base} role="status" aria-live="polite">
      {content}
    </span>
  );
}
