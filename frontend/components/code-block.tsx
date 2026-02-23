'use client';

import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language = 'text' }: CodeBlockProps) {
  const [isCopied, setIsCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="relative bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden my-3">
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-800">
        <span className="text-xs font-mono text-zinc-400">{language}</span>
        <button
          onClick={copyToClipboard}
          className="p-1.5 hover:bg-zinc-700 rounded transition-colors"
          title={isCopied ? 'Copied!' : 'Copy code'}
        >
          {isCopied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4 text-zinc-400 hover:text-zinc-200" />
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4">
        <code className={`text-sm font-mono text-zinc-300 language-${language}`}>
          {code}
        </code>
      </pre>
    </div>
  );
}
