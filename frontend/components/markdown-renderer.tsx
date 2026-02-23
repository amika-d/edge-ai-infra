import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const parseMarkdown = (text: string) => {
    // Split by code blocks first
    const parts = text.split(/```[\s\S]*?```/);
    const codeBlocks = text.match(/```[\s\S]*?```/g) || [];

    let partIndex = 0;
    let codeIndex = 0;

    return text.split(/(\n|```[\s\S]*?```)/g).map((segment, i) => {
      // Handle code blocks
      if (segment.startsWith('```')) {
        const language = segment.match(/^```(\w+)?/)?.[1] || 'text';
        const code = segment.replace(/^```\w*\n?/, '').replace(/\n?```$/, '');
        return (
          <pre key={i} className="bg-zinc-900 rounded p-3 my-2 overflow-x-auto border border-zinc-800">
            <code className={`text-sm font-mono text-zinc-300 language-${language}`}>
              {code}
            </code>
          </pre>
        );
      }

      if (segment === '\n') {
        return <br key={i} />;
      }

      // Parse inline markdown
      let processed = segment;
      const elements: React.ReactNode[] = [];
      let lastIndex = 0;

      // Bold
      const boldRegex = /\*\*(.*?)\*\*/g;
      let match;
      while ((match = boldRegex.exec(segment)) !== null) {
        elements.push(segment.substring(lastIndex, match.index));
        elements.push(
          <strong key={`bold-${i}-${lastIndex}`} className="font-semibold">
            {match[1]}
          </strong>
        );
        lastIndex = match.index + match[0].length;
      }

      if (lastIndex > 0) {
        elements.push(segment.substring(lastIndex));
        return <span key={i}>{elements}</span>;
      }

      // Inline code
      const codeRegex = /`([^`]+)`/g;
      while ((match = codeRegex.exec(segment)) !== null) {
        elements.push(segment.substring(lastIndex, match.index));
        elements.push(
          <code
            key={`inline-code-${i}-${lastIndex}`}
            className="bg-zinc-800 px-2 py-0.5 rounded text-sm font-mono text-zinc-300"
          >
            {match[1]}
          </code>
        );
        lastIndex = match.index + match[0].length;
      }

      if (lastIndex > 0) {
        elements.push(segment.substring(lastIndex));
        return <span key={i}>{elements}</span>;
      }

      // Lists
      if (segment.startsWith('- ') || segment.startsWith('* ')) {
        const items = segment.split('\n').filter(line => line.trim().startsWith('- ') || line.trim().startsWith('* '));
        return (
          <ul key={i} className="list-disc list-inside my-2 space-y-1">
            {items.map((item, idx) => (
              <li key={idx} className="text-zinc-300">
                {item.replace(/^[-*]\s/, '')}
              </li>
            ))}
          </ul>
        );
      }

      return <span key={i}>{segment}</span>;
    });
  };

  return (
    <div className="prose prose-invert prose-sm max-w-none break-words text-zinc-300">
      {parseMarkdown(content)}
    </div>
  );
}
