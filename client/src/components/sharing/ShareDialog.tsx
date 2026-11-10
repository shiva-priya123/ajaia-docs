import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { createShare, deleteShare, getShares, updateShare } from '../../api/shares.api';
import { getUsers } from '../../api/users.api';
import { useAuth } from '../../hooks/useAuth';
import type { Document, Permission, Share, User } from '../../types';
import { getErrorMessage } from '../../utils/errors';
import Alert from '../ui/Alert';
import Modal from '../ui/Modal';
import Spinner from '../ui/Spinner';
import ShareList from './ShareList';
import UserSelect from './UserSelect';

interface ShareDialogProps {
  document: Document;
  onClose: () => void;
}

export default function ShareDialog({ document: doc, onClose }: ShareDialogProps) {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [shares, setShares] = useState<Share[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState('');
  const [permission, setPermission] = useState<Permission>('editor');
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getUsers(), getShares(doc.id)])
      .then(([u, s]) => {
        if (cancelled) return;
        setUsers(u);
        setShares(s);
      })
      .catch((err) => !cancelled && setError(getErrorMessage(err, 'Could not load sharing settings.')))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [doc.id]);

  const available = useMemo(() => {
    const sharedIds = new Set(shares.map((s) => s.user_id));
    return users.filter((u) => u.id !== doc.owner_id && !sharedIds.has(u.id));
  }, [users, shares, doc.owner_id]);

  async function handleShare(e: FormEvent) {
    e.preventDefault();
    if (!selectedUser) {
      setError('Choose someone to share with.');
      return;
    }
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const share = await createShare(doc.id, selectedUser, permission);
      setShares((s) => [...s, share]);
      setSelectedUser('');
      setNotice(`${share.user_name} can now ${share.permission === 'editor' ? 'edit' : 'view'} this document.`);
    } catch (err) {
      setError(getErrorMessage(err, 'Could not share the document.'));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleChangePermission(share: Share, next: Permission) {
    setBusyId(share.id);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateShare(doc.id, share.id, next);
      setShares((s) => s.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setError(getErrorMessage(err, 'Could not change access.'));
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemove(share: Share) {
    setBusyId(share.id);
    setError(null);
    setNotice(null);
    try {
      await deleteShare(doc.id, share.id);
      setShares((s) => s.filter((x) => x.id !== share.id));
      setNotice(`Removed ${share.user_name}'s access.`);
    } catch (err) {
      setError(getErrorMessage(err, 'Could not remove access.'));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Modal title={`Share “${doc.title}”`} onClose={onClose}>
      {loading ? (
        <Spinner className="py-8" label="Loading people…" />
      ) : (
        <div className="space-y-4">
          {error && <Alert onDismiss={() => setError(null)}>{error}</Alert>}
          {notice && (
            <Alert tone="success" onDismiss={() => setNotice(null)}>
              {notice}
            </Alert>
          )}

          <form onSubmit={handleShare} className="flex flex-col gap-2 sm:flex-row">
            <UserSelect users={available} value={selectedUser} onChange={setSelectedUser} disabled={submitting} />
            <div className="flex gap-2">
              <select
                aria-label="Permission"
                value={permission}
                onChange={(e) => setPermission(e.target.value as Permission)}
                className="rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm text-slate-800 focus:border-blue-500 focus:outline-none"
              >
                <option value="editor">Can edit</option>
                <option value="viewer">Can view</option>
              </select>
              <button
                type="submit"
                disabled={submitting || !selectedUser}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Sharing…' : 'Share'}
              </button>
            </div>
          </form>

          <div>
            <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">People with access</h3>
            {user && (
              <ShareList
                owner={user}
                shares={shares}
                busyId={busyId}
                onChangePermission={handleChangePermission}
                onRemove={handleRemove}
              />
            )}
          </div>

          <p className="text-xs text-slate-500">
            People you add see this document under <span className="font-medium">Shared with me</span>. Viewers can
            read it; editors can change the title and content.
          </p>
        </div>
      )}
    </Modal>
  );
}
