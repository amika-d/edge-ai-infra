'use client';

import React, { useState } from 'react';
import { ChevronDown, Plus, X } from 'lucide-react';
import type { Document } from '@/lib/types';

interface DocumentSelectorProps {
  selectedDocuments: Document[];
  onDocumentsChange: (documents: Document[]) => void;
}

const DEMO_DOCUMENTS: Document[] = [
  { id: '1', name: 'API Documentation', type: 'markdown' },
  { id: '2', name: 'User Guide', type: 'pdf' },
  { id: '3', name: 'Architecture Design', type: 'markdown' },
  { id: '4', name: 'Privacy Policy', type: 'text' },
];

export function DocumentSelector({ selectedDocuments, onDocumentsChange }: DocumentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleDocument = (doc: Document) => {
    const isSelected = selectedDocuments.some(d => d.id === doc.id);
    if (isSelected) {
      onDocumentsChange(selectedDocuments.filter(d => d.id !== doc.id));
    } else {
      onDocumentsChange([...selectedDocuments, doc]);
    }
  };

  const removeDocument = (id: string) => {
    onDocumentsChange(selectedDocuments.filter(d => d.id !== id));
  };

  return (
    <div className="space-y-2">
      <label className="text-xs font-semibold text-zinc-400 uppercase">Documents</label>
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-left text-sm text-zinc-300 hover:border-zinc-700 transition-colors flex items-center justify-between"
        >
          <span>{selectedDocuments.length === 0 ? 'Select documents...' : `${selectedDocuments.length} selected`}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg z-50">
            <div className="max-h-48 overflow-y-auto">
              {DEMO_DOCUMENTS.map(doc => (
                <label
                  key={doc.id}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-800 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedDocuments.some(d => d.id === doc.id)}
                    onChange={() => toggleDocument(doc)}
                    className="rounded border-zinc-700"
                  />
                  <span className="text-sm text-zinc-300 flex-1">{doc.name}</span>
                  <span className="text-xs text-zinc-500">{doc.type}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {selectedDocuments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedDocuments.map(doc => (
            <div
              key={doc.id}
              className="flex items-center gap-2 px-2 py-1 bg-zinc-800 rounded-full text-xs text-zinc-300"
            >
              {doc.name}
              <button
                onClick={() => removeDocument(doc.id)}
                className="hover:text-zinc-100 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
