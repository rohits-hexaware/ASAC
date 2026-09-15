import type { ConfidenceLevel } from '../types';

const styles: Record<ConfidenceLevel, string> = {
  high: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-orange-100 text-orange-800 border-orange-200',
};

interface Props {
  level: ConfidenceLevel;
  className?: string;
}

export default function ConfidenceBadge({ level, className = '' }: Props) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${styles[level]} ${className}`}
    >
      {level} confidence
    </span>
  );
}
