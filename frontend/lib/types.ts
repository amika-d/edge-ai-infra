export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

export interface Citation {
  id: string;
  documentName: string;
  page?: number;
  section?: string;
  relevanceScore: number;
  excerpt?: string;
}

export interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'text' | 'markdown';
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  activeDocumentId: string | null;
  selectedDocuments: Document[];
  error?: string;
}

export interface ApiResponse {
  message: string;
  citations: Citation[];
  usage: {
    completionTokens: number;
    latency: number;
    tokensPerSecond: number;
  };
}
