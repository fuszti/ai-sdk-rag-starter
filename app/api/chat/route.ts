import { createResource } from '@/lib/actions/resources';
import { openai } from '@ai-sdk/openai';
import {
  convertToModelMessages,
  streamText,
  tool,
  UIMessage,
  stepCountIs,
} from 'ai';
import { z } from 'zod';
import { findRelevantContent } from '@/lib/ai/embedding';
import { createLLMSpan, setLLMOutput, addLLMInputMessages, addLLMOutputMessages } from '@/lib/tracing-clean';

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const extractText = (msg: any): string => {
    const c = msg?.content;
    if (typeof c === 'string') return c;
    if (Array.isArray(c)) {
      return c
        .map((part: any) => {
          if (typeof part === 'string') return part;
          if (part?.type === 'text') return part.text ?? '';
          if (part?.type === 'input_text') return part.text ?? '';
          if (part?.type === 'tool-call' || part?.type === 'tool-result') return '';
          if (part?.type === 'image' || part?.type === 'image_url') return '[image]';
          return typeof part?.text === 'string' ? part.text : '';
        })
        .filter(Boolean)
        .join('\n');
    }
    if (c && typeof c === 'object' && typeof c.text === 'string') return c.text;
    return '';
  };

  // Build provider-ready messages to mirror exactly what the model receives
  const providerMessages = convertToModelMessages(messages as any);

  const flattenProviderContent = (m: any): string => {
    const c = m?.content;
    if (typeof c === 'string') return c;
    if (Array.isArray(c)) {
      return c
        .map((part: any) => {
          if (typeof part === 'string') return part;
          if (part?.type === 'text') return part.text ?? '';
          if (part?.type === 'input_text') return part.text ?? '';
          if (part?.type === 'tool_call' || part?.type === 'tool-result') return '';
          if (part?.type === 'image_url' || part?.type === 'image') return '[image]';
          if (typeof part?.content === 'string') return part.content;
          return '';
        })
        .filter(Boolean)
        .join('\n');
    }
    if (c && typeof c === 'object' && typeof c.text === 'string') return c.text;
    return '';
  };

  const lastUserMessage = flattenProviderContent(
    [...providerMessages].reverse().find((m: any) => m.role === 'user')
  );

  return createLLMSpan(
    'chat-completion',
    'gpt-4o-mini',
    lastUserMessage,
    async (span) => {
      // Record input messages for Phoenix/OpenInference viewers (exactly what the model sees)
      addLLMInputMessages(
        span,
        providerMessages.map((m: any) => ({ role: m.role, content: flattenProviderContent(m) }))
      );
      const result = streamText({
        model: openai('gpt-4o-mini'),
        messages: providerMessages,
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
        onError: async (error) => {
          try {
            span.recordException(error as any);
          } finally {
            span.end();
          }
        },
        onFinish: async ({ text, usage, finishReason }) => {
          if (text) {
            const u: any = usage;
            const prompt = u?.promptTokens ?? u?.inputTokens;
            const completion = u?.completionTokens ?? u?.outputTokens;
            const total = u?.totalTokens ?? (typeof prompt === 'number' && typeof completion === 'number' ? prompt + completion : undefined);
            setLLMOutput(span, text, { prompt, completion, total });
            // Also record output messages array
            addLLMOutputMessages(span, [{ role: 'assistant', content: text }]);
          }
          span.end();
        },
      });

      return result.toUIMessageStreamResponse();
    },
    { deferEnd: true }
  );
}