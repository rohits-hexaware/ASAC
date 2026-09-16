import { useEffect, useState } from 'react';
import mermaid from 'mermaid';

interface Props {
  diagram: string;
  className?: string;
}

let mermaidInitialized = false;
let renderSequence = 0;

export default function MermaidDiagram({ diagram, className = '' }: Props) {
  const [svg, setSvg] = useState<string | null>(null);
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'neutral',
        securityLevel: 'loose',
        suppressErrorRendering: true,
        flowchart: { curve: 'basis' },
      });
      mermaidInitialized = true;
    }

    let cancelled = false;

    const render = async () => {
      if (!diagram) {
        setSvg(null);
        setRenderError(false);
        return;
      }

      try {
        const id = `mermaid-${Date.now()}-${renderSequence++}`;
        const { svg: renderedSvg } = await mermaid.render(id, diagram);
        if (!cancelled) {
          setSvg(renderedSvg);
          setRenderError(false);
        }
      } catch {
        if (!cancelled) {
          setSvg(null);
          setRenderError(true);
        }
      }
    };

    render();
    return () => {
      cancelled = true;
    };
  }, [diagram]);

  return (
    <div
      className={`min-h-[180px] max-h-[560px] overflow-auto p-4 bg-white rounded-lg border border-gray-200 ${className}`}
      role="img"
      aria-label="Architecture diagram"
    >
      {svg && <div className="flex min-w-max justify-center" dangerouslySetInnerHTML={{ __html: svg }} />}
      {renderError && (
        <div className="rounded border border-amber-200 bg-amber-50 p-3">
          <p className="text-sm font-medium text-amber-900">Diagram preview unavailable</p>
          <p className="mt-1 text-xs text-amber-800">The architecture details remain available in the component list below.</p>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-xs text-gray-700">{diagram}</pre>
        </div>
      )}
    </div>
  );
}
