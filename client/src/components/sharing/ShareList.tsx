import { X } from 'lucide-react';
import type { Permission, Share, User } from '../../types';
import Avatar from '../ui/Avatar';

interface ShareListProps {
  owner: User;
  shares: Share[];
  busyId: string | null;
  onChangePermission: (share: Share, permission: Permission) => void;
  onRemove: (share: Share) => void;
}

export default function ShareList({ owner, shares, busyId, onChangePermission, onRemove }: ShareListProps) {
  return (
    <ul className="divide-y divide-slate-100" aria-label="People with access">
      <li className="flex items-center gap-3 py-2.5">
        <Avatar name={owner.name} size="sm" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-slate-900">{owner.name} (you)</p>
          <p className="truncate text-xs text-slate-500">{owner.email}</p>
        </div>
        <span className="text-xs font-medium text-slate-500">Owner</span>
      </li>
      {shares.map((share) => (
        <li key={share.id} className="flex items-center gap-3 py-2.5">
          <Avatar name={share.user_name} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-900">{share.user_name}</p>
            <p className="truncate text-xs text-slate-500">{share.user_email}</p>
          </div>
          <select
            aria-label={`Access for ${share.user_name}`}
            value={share.permission}
            disabled={busyId === share.id}
            onChange={(e) => onChangePermission(share, e.target.value as Permission)}
            className="rounded-md border border-slate-200 bg-white py-1 pl-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none"
          >
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </select>
          <button
            type="button"
            disabled={busyId === share.id}
            onClick={() => onRemove(share)}
            className="rounded-md p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            aria-label={`Remove access for ${share.user_name}`}
            title="Remove access"
          >
            <X className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
