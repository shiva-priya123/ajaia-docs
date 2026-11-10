import { useCallback, useEffect, useState } from 'react';
import { getDocument } from '../api/documents.api';
import type { Document } from '../types';
import { getErrorMessage, getStatus } from '../utils/errors';

export function useDocument(id: string | undefined) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status?: number; message: string } | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      setDocument(await getDocument(id));
    } catch (err) {
      const status = getStatus(err);
      const message =
        status === 404
          ? 'This document does not exist or was deleted.'
          : status === 403
            ? "You don't have access to this document. Ask the owner to share it with you."
            : getErrorMessage(err, 'Could not open this document.');
      setError({ status, message });
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  return { document, setDocument, loading, error, reload: load };
}
