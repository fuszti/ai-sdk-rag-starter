import { db } from '@/lib/db';
import { resources, embeddings } from '@/lib/db/schema/resources';
import { generateEmbeddings } from '@/lib/ai/embedding';
import { nanoid } from '@/lib/utils';

interface PreDefinedMemory {
  id: string;
  content: string;
}

const PRE_DEFINED_MEMORIES: PreDefinedMemory[] = [
  {
    id: 'test-memory-1',
    content: 'I had a wonderful sunset dinner at Cafe Luna with my college friend Sarah last Tuesday. We talked about her new job in marketing and reminisced about our study abroad trip to Italy.'
  },
  {
    id: 'test-memory-2',
    content: 'Bought groceries at Whole Foods yesterday: organic bananas, quinoa, Greek yogurt, spinach, and dark chocolate. Spent about $65 total.'
  },
  {
    id: 'test-memory-3',
    content: 'Meeting with Dr. Johnson about my knee injury is scheduled for next Friday at 2 PM. Need to bring previous X-rays and insurance card.'
  },
  {
    id: 'test-memory-4',
    content: 'Mom\'s birthday is coming up on March 15th. She mentioned wanting a new garden hose and some kitchen towels. Budget around $50.'
  },
  {
    id: 'test-memory-5',
    content: 'Started reading "The Seven Husbands of Evelyn Hugo" by Taylor Jenkins Reid. Really enjoying it so far - finished chapter 3 last night.'
  }
];

export async function seedTestEmbeddings(): Promise<void> {
  console.log('🌱 Seeding test embeddings...');

  try {
    // Check if resources already exist
    const existingResources = await db.select().from(resources);

    if (existingResources.length > 0) {
      console.log('✅ Test resources already exist, skipping seeding');
      return;
    }

    // Insert resources and generate embeddings
    for (const memory of PRE_DEFINED_MEMORIES) {
      console.log(`📝 Processing: ${memory.content.substring(0, 50)}...`);

      // Insert resource
      await db.insert(resources).values({
        id: memory.id,
        content: memory.content
      });

      // Generate and insert embeddings
      const embeddingsData = await generateEmbeddings(memory.content);

      const embeddingsToInsert = embeddingsData.map((embedding) => ({
        id: nanoid(),
        resourceId: memory.id,
        content: embedding.content,
        embedding: embedding.embedding,
      }));

      await db.insert(embeddings).values(embeddingsToInsert);

      console.log(`✅ Created ${embeddingsToInsert.length} embeddings for memory ${memory.id}`);
    }

    console.log('🎉 Test embeddings seeded successfully!');

  } catch (error) {
    console.error('❌ Error seeding test embeddings:', error);
    throw error;
  }
}

// Export for use in API route
export { PRE_DEFINED_MEMORIES };