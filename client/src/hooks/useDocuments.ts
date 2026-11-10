import { useCallback, useEffect, useState } from 'react';
import { getDocuments } from '../api/documents.api';
import type { Document } from '../types';
import { getErrorMessage } from '../utils/errors';

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await getDocuments();
      docs.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
      setDocuments(docs);
    } catch (err) {
      setError(getErrorMessage(err, 'Could not load your documents.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { documents, setDocuments, loading, error, reload };
}
