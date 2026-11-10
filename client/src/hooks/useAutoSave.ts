import { useCallback, useEffect, useRef, useState } from 'react';
import { updateDocument, type DocumentUpdatePayload } from '../api/documents.api';
import type { Document } from '../types';
import { AUTO_SAVE_DELAY_MS } from '../utils/constants';
import { getErrorMessage, getStatus } from '../utils/errors';

export type SaveStatus = 'idle' | 'pending' | 'saving' | 'saved' | 'error' | 'conflict';

type Changes = Pick<DocumentUpdatePayload, 'title' | 'content'>;

interface Options {
  documentId: string;
  /** `updated_at` of the version the editor was loaded from. */
  initialVersion: string;
  enabled: boolean;
  delayMs?: number;
  onSaved?: (doc: Document) => void;
}

/**
 * Debounced auto-save.
 *
 * - Edits are merged into one pending payload and sent after `delayMs` of quiet.
 * - Only one request is in flight at a time; edits made meanwhile are sent next.
 * - Each save carries the version it was based on; if someone else saved first the
 *   server answers 409 and we stop and surface a conflict instead of overwriting.
 * - Failed saves keep their changes, so "Retry" (or the next edit) resends them.
 */
export function useAutoSave({ documentId, initialVersion, enabled, delayMs = AUTO_SAVE_DELAY_MS, onSaved }: Options) {
  const [status, setStatus] = useState<SaveStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  const pending = useRef<Changes>({});
  const version = useRef<string | null>(initialVersion);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = useRef<Promise<void> | null>(null);
  const conflicted = useRef(false);
  const onSavedRef = useRef(onSaved);
  onSavedRef.current = onSaved;

  const hasPending = () => Object.keys(pending.current).length > 0;

  const save = useCallback(
    async (opts: { force?: boolean } = {}): Promise<void> => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }
      // Serialise requests: wait for the previous save, then send what's left.
      while (inFlight.current) await inFlight.current;
      if (!enabled || !hasPending() || (conflicted.current && !opts.force)) return;

      const changes = pending.current;
      pending.current = {};
      const payload: DocumentUpdatePayload = { ...changes };
      if (!opts.force && version.current) payload.expected_updated_at = version.current;

      setStatus('saving');
      const request = updateDocument(documentId, payload)
        .then((doc) => {
          version.current = doc.updated_at;
          conflicted.current = false;
          setError(null);
          setLastSavedAt(new Date());
          setStatus(hasPending() ? 'pending' : 'saved');
          onSavedRef.current?.(doc);
        })
        .catch((err: unknown) => {
          // Put the unsaved changes back underneath anything typed since.
          pending.current = { ...changes, ...pending.current };
          if (getStatus(err) === 409) {
            conflicted.current = true;
            setStatus('conflict');
            setError(getErrorMessage(err));
          } else {
            setStatus('error');
            setError(getErrorMessage(err, 'Could not save your changes.'));
          }
        })
        .finally(() => {
          inFlight.current = null;
        });
      inFlight.current = request;
      await request;
    },
    [documentId, enabled],
  );

  /** Record a change and (re)start the debounce timer. */
  const queue = useCallback(
    (changes: Changes) => {
      if (!enabled) return;
      pending.current = { ...pending.current, ...changes };
      if (conflicted.current) return; // wait for the user to resolve
      setStatus('pending');
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void save(), delayMs);
    },
    [enabled, delayMs, save],
  );

  const flush = useCallback(() => save(), [save]);
  /** Resolve a conflict by overwriting the server copy with ours. */
  const overwrite = useCallback(() => save({ force: true }), [save]);

  // Warn before closing the tab with unsaved work; flush on unmount (navigation).
  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasPending() || inFlight.current) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', onBeforeUnload);
      if (hasPending() && !conflicted.current) void save();
    };
  }, [save]);

  return { status, error, lastSavedAt, queue, flush, overwrite };
}
