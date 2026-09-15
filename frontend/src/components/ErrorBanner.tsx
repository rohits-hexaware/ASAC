import { AlertTriangle, X } from 'lucide-react';

interface Props {
  message: string;
  onDismiss?: () => void;
  onAction?: () => void;
  actionLabel?: string;
  variant?: 'error' | 'warning';
}

export default function ErrorBanner({ message, onDismiss, onAction, actionLabel = 'Retry', variant = 'error' }: Props) {
  const colors =
    variant === 'error'
      ? 'bg-red-50 border-red-200 text-red-800'
      : 'bg-amber-50 border-amber-200 text-amber-800';

  return (
    <div className={`flex items-center justify-between gap-3 p-4 rounded-lg border ${colors}`}>
      <div className="flex items-start gap-3 flex-1">
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p className="flex-1 text-sm">{message}</p>
      </div>
      <div className="flex items-center gap-2">
        {onAction && (
          <button
            onClick={onAction}
            className="px-3 py-1 bg-white/80 border border-current text-xs font-semibold rounded hover:bg-white transition-colors"
          >
            {actionLabel}
          </button>
        )}
        {onDismiss && (
          <button onClick={onDismiss} className="flex-shrink-0 hover:opacity-70 p-1">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
