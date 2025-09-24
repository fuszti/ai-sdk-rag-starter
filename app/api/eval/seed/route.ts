import { seedTestEmbeddings } from '@/simulation/db/seed_embeddings';
import { NextResponse } from 'next/server';

export async function POST() {
  try {
    await seedTestEmbeddings();
    return NextResponse.json({
      success: true,
      message: 'Test embeddings seeded successfully'
    });
  } catch (error) {
    console.error('Failed to seed test embeddings:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to seed test embeddings',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}