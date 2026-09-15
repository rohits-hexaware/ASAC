import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface Props {
  diagram: string;
  className?: string;
}

let mermaidInitialized = false;

export default function MermaidDiagram({ diagram, className = '' }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'neutral',
        securityLevel: 'loose',
        flowchart: { curve: 'basis' },
      });
      mermaidInitialized = true;
    }

    const render = async () => {
      if (!containerRef.current || !diagram) return;
      try {
        const id = `mermaid-${Date.now()}`;
        const { svg } = await mermaid.render(id, diagram);
        containerRef.current.innerHTML = svg;
      } catch {
        containerRef.current.innerHTML = `<pre class="text-xs text-gray-600 p-4 bg-gray-50 rounded overflow-auto">${diagram}</pre>`;
      }
    };

    render();
  }, [diagram]);

  return (
    <div
      ref={containerRef}
      className={`flex justify-center overflow-auto p-4 bg-white rounded-lg border border-gray-200 ${className}`}
    />
  );
}
