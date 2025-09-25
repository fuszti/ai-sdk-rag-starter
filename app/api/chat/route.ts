import { createResource } from '@/lib/actions/resources';
import { openai } from '@ai-sdk/openai';
import {
  convertToModelMessages,
  generateText,
  streamText,
  tool,
  UIMessage,
  stepCountIs,
} from 'ai';
import { z } from 'zod';
import { findRelevantContent } from '@/lib/ai/embedding';
import { NextResponse } from 'next/server';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const messages: UIMessage[] = body?.messages || [];

    if (!Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: "Messages array is required" },
        { status: 400 }
      );
    }

    const accept = req.headers.get('accept') ?? '';
    const wantsJson = accept.includes('application/json') &&
      !accept.includes('text/event-stream') &&
      !accept.includes('application/x-ndjson');

    const common = {
      model: openai('gpt-4'),
      messages: messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content || '',
      })),
    stopWhen: stepCountIs(5),
    system: `You are a helpful assistant. Check your knowledge base before answering any questions.
    Only respond to questions using information from tool calls.
    if no relevant information is found in the tool calls, respond, "Sorry, I don't know."
    But follow the conversation, so use information from both the tool calls and the conversation.`,
    tools: {
      addResource: tool({
        description: `add a resource to your knowledge base.
          If the user provides a random piece of knowledge unprompted, use this tool without asking for confirmation.`,
        inputSchema: z.object({
          content: z
            .string()
            .describe('the content or resource to add to the knowledge base'),
        }),
        execute: async ({ content }) => createResource({ content }),
      }),
      getInformation: tool({
        description: `get information from your knowledge base to answer questions.`,
        inputSchema: z.object({
          question: z.string().describe('the users question'),
        }),
        execute: async ({ question }) => findRelevantContent(question),
      }),
    },
  } as const;

  if (wantsJson) {
    const { text } = await generateText(common);
    return NextResponse.json(
      { answer: text },
      { status: 200, headers: { 'Cache-Control': 'no-store' } },
    );
  }

  const result = streamText(common);
  return result.toUIMessageStreamResponse();

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}