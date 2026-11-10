import { AlertCircle, CheckCircle2, X } from 'lucide-react';
import type { ReactNode } from 'react';

interface AlertProps {
  tone?: 'error' | 'success' | 'info';
  children: ReactNode;
  onDismiss?: () => void;
  action?: ReactNode;
}

const TONES = {
  error: 'border-red-200 bg-red-50 text-red-800',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
};

export default function Alert({ tone = 'error', children, onDismiss, action }: AlertProps) {
  const Icon = tone === 'success' ? CheckCircle2 : AlertCircle;
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${TONES[tone]}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="flex-1">{children}</div>
      {action}
      {onDismiss && (
        <button type="button" onClick={onDismiss} className="rounded p-0.5 opacity-70 hover:opacity-100" aria-label="Dismiss">
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
