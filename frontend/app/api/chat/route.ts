import { NextRequest, NextResponse } from 'next/server';
import type { ApiResponse, Citation } from '@/lib/types';

// Mock function to generate a response based on user message
function generateMockResponse(message: string): { text: string; citations: Citation[] } {
  const responses: Record<string, { text: string; citations: Citation[] }> = {
    'api': {
      text: 'The **API documentation** provides comprehensive information about all available endpoints. You can find detailed information about request/response formats, authentication methods, and rate limiting in the official guide.\n\nKey features include:\n- RESTful endpoints for CRUD operations\n- OAuth 2.0 authentication\n- Webhook support for real-time updates\n- Comprehensive error handling\n\nFor more details, refer to the authentication section and the examples provided.',
      citations: [
        {
          id: '1',
          documentName: 'API Documentation',
          page: 1,
          section: 'Authentication',
          relevanceScore: 0.95,
          excerpt: 'OAuth 2.0 is the recommended authentication method...',
        },
        {
          id: '2',
          documentName: 'API Documentation',
          page: 5,
          section: 'Endpoints',
          relevanceScore: 0.87,
          excerpt: 'All endpoints follow RESTful conventions...',
        },
      ],
    },
    'architecture': {
      text: 'Based on the **Architecture Design** document, the system follows a microservices pattern with the following components:\n\n- **Frontend Layer**: React-based user interface\n- **API Gateway**: Central point for all requests\n- **Service Layer**: Independent microservices\n- **Data Layer**: PostgreSQL with Redis caching\n\nThis design ensures scalability and maintainability.',
      citations: [
        {
          id: '3',
          documentName: 'Architecture Design',
          page: 2,
          section: 'System Overview',
          relevanceScore: 0.92,
          excerpt: 'The microservices architecture allows independent scaling...',
        },
      ],
    },
    'database': {
      text: 'The database uses **PostgreSQL** as the primary relational database with **Redis** for caching frequently accessed data.\n\nKey components:\n- Connection pooling for performance\n- Automated backups every 6 hours\n- Read replicas for load distribution\n- Monitoring and alerting enabled',
      citations: [
        {
          id: '4',
          documentName: 'Architecture Design',
          page: 8,
          section: 'Data Storage',
          relevanceScore: 0.88,
          excerpt: 'PostgreSQL provides ACID compliance and reliability...',
        },
      ],
    },
  };

  // Find the best matching response based on keywords
  const lowerMessage = message.toLowerCase();
  for (const [key, value] of Object.entries(responses)) {
    if (lowerMessage.includes(key)) {
      return value;
    }
  }

  // Default response
  return {
    text: 'I found relevant information in your documents. You can ask me about API documentation, system architecture, database design, user guides, and privacy policies. Would you like to know more about any specific topic?',
    citations: [
      {
        id: '5',
        documentName: 'API Documentation',
        relevanceScore: 0.5,
        excerpt: 'General documentation...',
      },
    ],
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, documentIds, conversationHistory } = body;

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Simulate API processing delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const startTime = Date.now();
    const response = generateMockResponse(message);
    const latency = Date.now() - startTime;

    // Calculate mock token metrics
    const completionTokens = Math.ceil(response.text.split(/\s+/).length * 1.3);
    const tokensPerSecond = Math.round((completionTokens / latency) * 1000);

    const apiResponse: ApiResponse = {
      message: response.text,
      citations: response.citations,
      usage: {
        completionTokens,
        latency,
        tokensPerSecond,
      },
    };

    return NextResponse.json(apiResponse);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
