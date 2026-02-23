'use client';

import React, { useState } from 'react';
import { ChevronDown, FileText } from 'lucide-react';
import type { Citation } from '@/lib/types';

interface CitationsPanelProps {
  citations: Citation[];
}

export function CitationsPanel({ citations }: CitationsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-zinc-800 bg-zinc-950 rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-zinc-900 transition-colors"
      >
        <span className="font-semibold text-zinc-200 flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Citations ({citations.length})
        </span>
        <ChevronDown
          className={`w-4 h-4 text-zinc-400 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {citations.map(citation => (
            <div
              key={citation.id}
              className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className="font-medium text-zinc-100">{citation.documentName}</h4>
                <span className="text-xs bg-zinc-800 px-2 py-0.5 rounded text-zinc-300">
                  {(citation.relevanceScore * 100).toFixed(0)}%
                </span>
              </div>
              {citation.section && (
                <p className="text-xs text-zinc-400 mb-1">Section: {citation.section}</p>
              )}
              {citation.page && (
                <p className="text-xs text-zinc-400">Page {citation.page}</p>
              )}
              {citation.excerpt && (
                <p className="text-xs text-zinc-300 mt-2 italic">{citation.excerpt}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
