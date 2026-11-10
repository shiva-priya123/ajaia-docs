import { FileText, LogOut } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { APP_NAME } from '../../utils/constants';
import Avatar from '../ui/Avatar';

interface HeaderProps {
  /** Page-specific content shown after the logo (e.g. the document title). */
  children?: ReactNode;
  /** Page-specific actions shown before the user menu. */
  actions?: ReactNode;
}

export default function Header({ children, actions }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-3 sm:gap-3 sm:px-6">
        <Link to="/" className={`${children ? 'hidden sm:flex' : 'flex'} shrink-0 items-center gap-2 rounded-md text-slate-900`} aria-label={`${APP_NAME} home`}>
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <FileText className="h-4.5 w-4.5" aria-hidden />
          </span>
          {!children && <span className="text-base font-semibold">{APP_NAME}</span>}
        </Link>

        <div className="flex min-w-0 flex-1 items-center gap-1 sm:gap-3">{children}</div>

        {actions}

        {user && (
          <div className="flex shrink-0 items-center gap-2 sm:border-l sm:border-slate-200 sm:pl-3">
            <span className="hidden sm:inline-flex">
              <Avatar name={user.name} size="sm" />
            </span>
            <span className="hidden text-sm font-medium text-slate-700 md:inline">{user.name}</span>
            <button
              type="button"
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
