import { openai } from '@ai-sdk/openai';
import { embed, embedMany } from 'ai';
import { drizzleSql as sql } from '@/lib/db/schema/resources';

import { db } from '@/lib/db';
import { embeddings } from '@/lib/db/schema/resources';
import {
  createEmbeddingSpan,
  createRetrieverSpan,
  setEmbeddingOutput,
  setEmbeddingOutputs,
  setRetrieverOutput,
} from '@/lib/tracing-clean';

const embeddingModel = openai.embedding('text-embedding-3-small');

const generateChunks = (input: string): string[] => {
  return input
    .trim()
    .split('.')
    .filter(i => i !== '');
};

export const generateEmbeddings = async (
  value: string,
): Promise<Array<{ embedding: number[]; content: string }>> => {
  const chunks = generateChunks(value);

  return createEmbeddingSpan(
    'batch-embedding',
    'text-embedding-3-small',
    chunks.join(' | '),
    async (span) => {
      const { embeddings: embedRes } = await embedMany({
        model: embeddingModel,
        values: chunks,
      });

      if (!Array.isArray(embedRes)) {
        throw new Error('Expected embeddings to be an array');
      }

      const results = embedRes.map((e, i) => ({ content: chunks[i], embedding: e }));

      // Record all embeddings with their source text per OpenInference conventions
      if (embedRes.length) {
        setEmbeddingOutputs(
          span,
          embedRes.map((e, i) => ({ text: chunks[i], vector: e }))
        );
      }

      return results;
    }
  );
};

export const generateEmbedding = async (value: string): Promise<number[]> => {
  const input = value.replaceAll('\n', ' ');

  return createEmbeddingSpan(
    'query-embedding',
    'text-embedding-3-small',
    input,
    async (span) => {
      const { embedding } = await embed({
        model: embeddingModel,
        value: input,
      });

      setEmbeddingOutput(span, embedding, input);
      return embedding;
    }
  );
};

export const findRelevantContent = async (userQuery: string) => {
  return createRetrieverSpan(
    'knowledge-retrieval',
    userQuery,
    async (span) => {
      const userQueryEmbedded = await generateEmbedding(userQuery);

      // Use cosine distance via pgvector; cast RHS to vector to avoid "vector <=> record" errors
      const queryVec = sql.raw(`ARRAY[${userQueryEmbedded.join(',')}]::vector`);
      const distExpr = sql<number>`(${embeddings.embedding} <=> ${queryVec})`;

      const similarGuides = await db
        .select({ content: embeddings.content, distance: distExpr })
        .from(embeddings)
        .where(sql`${distExpr} < 0.7`)
        .orderBy(distExpr)
        .limit(4);

      if (!Array.isArray(similarGuides)) {
        console.error('similarGuides is not an array:', similarGuides);
        const noResultsMsg = 'Error retrieving documents from database.';
        return noResultsMsg;
      }

      if (similarGuides.length === 0) {
        const noResultsMsg = 'No relevant information found in the knowledge base.';
        setRetrieverOutput(span, []);
        return noResultsMsg;
      }

      // Set retriever output
      setRetrieverOutput(span, similarGuides.map((guide, idx) => ({
        id: idx.toString(),
        content: guide.content || '',
        score: typeof (guide as any).distance === 'number' ? 1 - (guide as any).distance : 0,
      })));

      return similarGuides.map(guide => guide.content || '').join('\n');
    }
  );
};