# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) chatbot starter project built with Next.js 14 using the Vercel AI SDK. The application provides a foundation for building chatbots that respond with information from a knowledge base, with capabilities to store and retrieve information using PostgreSQL with pgvector for vector embeddings.

## Development Commands

### Core Development
- `pnpm dev` - Start development server
- `pnpm build` - Build production application
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

### Database Operations
- `pnpm db:generate` - Generate Drizzle migrations from schema changes
- `pnpm db:migrate` - Run database migrations
- `pnpm db:push` - Push schema changes directly to database (development)
- `pnpm db:pull` - Pull schema from database (introspect)
- `pnpm db:studio` - Open Drizzle Studio database GUI
- `pnpm db:drop` - Drop database tables
- `pnpm db:check` - Check migration files

## Architecture

### Tech Stack
- **Frontend**: Next.js 14 with App Router, React 18
- **Styling**: TailwindCSS with shadcn-ui components
- **Database**: PostgreSQL with pgvector extension via Drizzle ORM
- **AI**: Vercel AI SDK with OpenAI integration
- **Package Manager**: pnpm (required - see packageManager field)

### Project Structure
```
├── app/                    # Next.js App Router pages
├── components/            # React components
│   └── ui/               # shadcn-ui base components
├── lib/
│   ├── actions/          # Server actions
│   ├── db/              # Database configuration and schema
│   │   ├── schema/      # Drizzle schema definitions
│   │   └── migrations/  # Database migration files
│   ├── env.mjs         # Environment variable validation (T3 Env)
│   └── utils.ts        # Utility functions
```

### Database Architecture
- Uses Drizzle ORM with PostgreSQL
- Primary entity: `resources` table for storing content
- Schema validation using Drizzle-Zod integration
- Environment variables managed through @t3-oss/env-nextjs

### Key Patterns
- Server Actions for database operations (`lib/actions/`)
- Type-safe environment variables with runtime validation
- Zod schema validation for API inputs
- shadcn-ui component system with Radix UI primitives

## Development Notes

### Environment Setup
- Requires `DATABASE_URL` environment variable for PostgreSQL connection
- Uses `.env.local` for local development (see `.env.example`)

### Database Workflow
1. Modify schema in `lib/db/schema/`
2. Run `pnpm db:generate` to create migrations
3. Run `pnpm db:migrate` to apply migrations
4. Use `pnpm db:studio` to inspect database visually

### Component Development
- Follow shadcn-ui patterns for new UI components
- Use Tailwind classes with `clsx` and `tailwind-merge` utilities
- Leverage Radix UI for accessible component primitives