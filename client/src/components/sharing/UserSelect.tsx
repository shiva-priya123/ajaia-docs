import type { User } from '../../types';

interface UserSelectProps {
  users: User[];
  value: string;
  onChange: (userId: string) => void;
  disabled?: boolean;
}

export default function UserSelect({ users, value, onChange, disabled }: UserSelectProps) {
  return (
    <select
      aria-label="Person to share with"
      value={value}
      disabled={disabled || users.length === 0}
      onChange={(e) => onChange(e.target.value)}
      className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400"
    >
      <option value="">{users.length === 0 ? 'Everyone already has access' : 'Choose a person…'}</option>
      {users.map((u) => (
        <option key={u.id} value={u.id}>
          {u.name} ({u.email})
        </option>
      ))}
    </select>
  );
}
