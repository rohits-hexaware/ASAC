import { Loader2 } from 'lucide-react';

interface Props {
  progress: number;
  message?: string;
}

const STAGES = [
  'Analyzing requirements...',
  'Designing architecture...',
  'Running security review...',
  'Generating documentation...',
  'Finalizing results...',
];

export default function LoadingState({ progress, message }: Props) {
  const stageIndex = Math.min(Math.floor(progress / 20), STAGES.length - 1);
  const displayMessage = message || STAGES[stageIndex];

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Loader2 className="w-12 h-12 text-brand-600 animate-spin mb-6" />
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Running Analysis Pipeline</h3>
      <p className="text-sm text-gray-600 mb-6 text-center max-w-md">{displayMessage}</p>
      <div className="w-full max-w-md">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-brand-600 h-2.5 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-4">This typically takes 10–30 seconds</p>
    </div>
  );
}
