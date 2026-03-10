import { NextRequest, NextResponse } from 'next/server';
import type { ApiResponse } from '@/lib/types';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8080';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, documentIds } = body;

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    const startTime = Date.now();

    const backendRes = await fetch(`${BACKEND_URL}/v1/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: message,
        document_id: documentIds?.[0] ?? null,
      }),
    });

    if (!backendRes.ok) {
      const err = await backendRes.text();
      return NextResponse.json({ error: err }, { status: backendRes.status });
    }

    const data = await backendRes.json();
    const latency = Date.now() - startTime;
    const completionTokens: number = data.usage?.completion_tokens ?? 0;

    const apiResponse: ApiResponse = {
      message: data.answer,
      citations: (data.citations ?? []).map((c: any, i: number) => ({
        id: String(i + 1),
        documentName: c.doc ?? '',
        page: c.page ?? undefined,
        section: c.section ?? undefined,
        relevanceScore: c.score ?? 0,
        excerpt: undefined,
      })),
      usage: {
        completionTokens,
        latency,
        tokensPerSecond: latency > 0 ? Math.round((completionTokens / latency) * 1000) : 0,
      },
    };

    return NextResponse.json(apiResponse);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
