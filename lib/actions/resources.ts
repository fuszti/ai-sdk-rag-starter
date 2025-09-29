"use server";

import {
  NewResourceParams,
  insertResourceSchema,
  resources,
  embeddings,
} from '@/lib/db/schema/resources';
import { db } from '../db';
import { generateEmbeddings } from '@/lib/ai/embedding';

export const createResource = async (input: NewResourceParams): Promise<string> => {
  try {
    const { content } = insertResourceSchema.parse(input);

    const [resource] = await db
      .insert(resources)
      .values({ content })
      .returning();

    const embeddingsData = await generateEmbeddings(content);
    await db.insert(embeddings).values(
      embeddingsData.map((embedding) => ({
        resourceId: resource.id,
        content: embedding.content,
        embedding: embedding.embedding,
      })),
    );

    return 'Resource successfully created.';
  } catch (e) {
    if (e instanceof Error)
      return e.message.length > 0 ? e.message : 'Error, please try again.';
    return 'Error, please try again.';
  }
};