import { trace, SpanStatusCode, SpanKind, Span } from '@opentelemetry/api';
import {
  SemanticConventions,
  OpenInferenceSpanKind,
} from '@arizeai/openinference-semantic-conventions';

export { OpenInferenceSpanKind } from '@arizeai/openinference-semantic-conventions';

const {
  OPENINFERENCE_SPAN_KIND,
  INPUT_VALUE,
  INPUT_MIME_TYPE,
  OUTPUT_VALUE,
  OUTPUT_MIME_TYPE,
  EMBEDDING_MODEL_NAME,
  EMBEDDING_EMBEDDINGS,
  EMBEDDING_VECTOR,
  LLM_MODEL_NAME,
  LLM_INPUT_MESSAGES,
  LLM_OUTPUT_MESSAGES,
  LLM_TOKEN_COUNT_PROMPT,
  LLM_TOKEN_COUNT_COMPLETION,
  LLM_TOKEN_COUNT_TOTAL,
  RETRIEVAL_DOCUMENTS,
} = SemanticConventions;

export async function createLLMSpan<T>(
  name: string,
  modelName: string,
  inputValue: string,
  fn: (span: Span) => Promise<T>,
  options?: { deferEnd?: boolean }
): Promise<T> {
  const tracer = trace.getTracer('ai-rag-app', '1.0.0');

  return tracer.startActiveSpan(
    name,
    {
      kind: SpanKind.INTERNAL,
      attributes: {
        [OPENINFERENCE_SPAN_KIND]: OpenInferenceSpanKind.LLM,
        [LLM_MODEL_NAME]: modelName,
        [INPUT_VALUE]: inputValue,
        [INPUT_MIME_TYPE]: 'text/plain',
      },
    },
    async (span: Span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        throw error;
      } finally {
        if (!options?.deferEnd) {
          span.end();
        }
      }
    }
  );
}

export async function createEmbeddingSpan<T>(
  name: string,
  modelName: string,
  inputText: string,
  fn: (span: Span) => Promise<T>
): Promise<T> {
  const tracer = trace.getTracer('ai-rag-app', '1.0.0');

  return tracer.startActiveSpan(
    name,
    {
      kind: SpanKind.INTERNAL,
      attributes: {
        [OPENINFERENCE_SPAN_KIND]: OpenInferenceSpanKind.EMBEDDING,
        [EMBEDDING_MODEL_NAME]: modelName,
        [INPUT_VALUE]: inputText,
        [INPUT_MIME_TYPE]: 'text/plain',
      },
    },
    async (span: Span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

export async function createRetrieverSpan<T>(
  name: string,
  query: string,
  fn: (span: Span) => Promise<T>
): Promise<T> {
  const tracer = trace.getTracer('ai-rag-app', '1.0.0');

  return tracer.startActiveSpan(
    name,
    {
      kind: SpanKind.INTERNAL,
      attributes: {
        [OPENINFERENCE_SPAN_KIND]: OpenInferenceSpanKind.RETRIEVER,
        [INPUT_VALUE]: query,
        [INPUT_MIME_TYPE]: 'text/plain',
      },
    },
    async (span: Span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

// Helper functions to add results to spans
export function setLLMOutput(span: Span, output: string, tokens?: { prompt?: number; completion?: number; total?: number }) {
  span.setAttribute(OUTPUT_VALUE, output.substring(0, 1000)); // Limit length
  span.setAttribute(OUTPUT_MIME_TYPE, 'text/plain');
  if (tokens) {
    if (tokens.prompt) span.setAttribute(LLM_TOKEN_COUNT_PROMPT, tokens.prompt);
    if (tokens.completion) span.setAttribute(LLM_TOKEN_COUNT_COMPLETION, tokens.completion);
    if (tokens.total) span.setAttribute(LLM_TOKEN_COUNT_TOTAL, tokens.total);
  }
}

export function setEmbeddingOutputs(
  span: Span,
  items: Array<{ text?: string; vector: number[] }>
) {
  // Emit only indexed nested attributes; set vectors as strings to match known-working format
  items.forEach((item, i) => {
    const vec = Array.isArray(item.vector) ? item.vector : Array.from(item.vector as any);
    if (typeof item.text === 'string') {
      span.setAttribute(`${EMBEDDING_EMBEDDINGS}.${i}.embedding.text`, item.text);
    }
    span.setAttribute(`${EMBEDDING_EMBEDDINGS}.${i}.embedding.vector`, JSON.stringify(vec));
    span.setAttribute(`${EMBEDDING_EMBEDDINGS}.${i}.embedding.dimensions`, vec.length);
  });
  // Top-level first vector string for compatibility
  if (items[0]) {
    const first = Array.isArray(items[0].vector) ? items[0].vector : Array.from(items[0].vector as any);
    span.setAttribute(EMBEDDING_VECTOR, JSON.stringify(first));
  }
}

export function setEmbeddingOutput(span: Span, vector: number[], text?: string) {
  setEmbeddingOutputs(span, [{ text, vector }]);
}

export function setRetrieverOutput(
  span: Span,
  documents: Array<{ id?: string; content: string; score?: number; metadata?: Record<string, any> }>
) {
  const formattedDocs = documents.map((doc, idx) => ({
    document: {
      id: doc.id || idx.toString(),
      score: doc.score || 0,
      content: (doc.content || '').substring(0, 200),
      ...(doc.metadata ? { metadata: doc.metadata } : {}),
    },
  }));

  // Do NOT set an aggregated JSON on RETRIEVAL_DOCUMENTS to avoid viewer type conflicts

  // Also add flattened attributes per Arize examples for easy table rendering
  formattedDocs.forEach((doc, idx) => {
    span.setAttribute(`retrieval.documents.${idx}.document.id`, doc.document.id);
    span.setAttribute(`retrieval.documents.${idx}.document.score`, doc.document.score);
    span.setAttribute(`retrieval.documents.${idx}.document.content`, doc.document.content);
    if ((doc.document as any).metadata !== undefined) {
      span.setAttribute(`retrieval.documents.${idx}.document.metadata`, JSON.stringify((doc.document as any).metadata));
    }
  });

  span.setAttribute(OUTPUT_VALUE, `Retrieved ${documents.length} documents`);
  span.setAttribute(OUTPUT_MIME_TYPE, 'text/plain');
  span.setAttribute('retrieval.document_count', documents.length);
}

// Phoenix-friendly helpers to record chat message arrays
export function addLLMInputMessages(span: Span, messages: Array<{ role: string; content: string }>) {
  messages.forEach((m, i) => {
    span.setAttribute(`${LLM_INPUT_MESSAGES}.${i}.message.role`, m.role);
    span.setAttribute(`${LLM_INPUT_MESSAGES}.${i}.message.content`, m.content);
  });
}

export function addLLMOutputMessages(span: Span, messages: Array<{ role: string; content: string }>) {
  messages.forEach((m, i) => {
    span.setAttribute(`${LLM_OUTPUT_MESSAGES}.${i}.message.role`, m.role);
    span.setAttribute(`${LLM_OUTPUT_MESSAGES}.${i}.message.content`, m.content);
  });
}