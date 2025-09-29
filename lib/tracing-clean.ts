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
    async (span) => {
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
    async (span) => {
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
    async (span) => {
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

export function setEmbeddingOutput(span: Span, vector: number[], dimensions: number) {
  // Standard OpenInference fields
  span.setAttribute(EMBEDDING_VECTOR, JSON.stringify(vector));
  // Also provide the nested Phoenix-friendly structure
  span.setAttribute(`${EMBEDDING_EMBEDDINGS}.0.embedding.vector`, JSON.stringify(vector));
  span.setAttribute('embedding.dimensions', dimensions);
}

export function setRetrieverOutput(span: Span, documents: Array<{id?: string; content: string; score?: number}>) {
  const formattedDocs = documents.map((doc, idx) => ({
    document_id: doc.id || idx.toString(),
    content: doc.content.substring(0, 200),
    score: doc.score || 0,
  }));

  // Prefer an array of strings for better Phoenix rendering
  span.setAttribute(
    RETRIEVAL_DOCUMENTS,
    formattedDocs.map((d) => d.content)
  );
  // Keep full JSON as a separate attribute for debugging
  span.setAttribute('retrieval.documents_json', JSON.stringify(formattedDocs));
  // Also add flattened, indexed attributes for Phoenix table rendering
  formattedDocs.forEach((doc, idx) => {
    span.setAttribute(`retrieval.documents.${idx}.document_id`, doc.document_id);
    span.setAttribute(`retrieval.documents.${idx}.content`, doc.content);
    span.setAttribute(`retrieval.documents.${idx}.score`, doc.score);
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