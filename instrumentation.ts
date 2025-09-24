import { registerOTel } from '@vercel/otel';
// import { BraintrustExporter } from 'braintrust';

export function register() {
  registerOTel({
    serviceName: 'rag-chatbot-demo',
    // traceExporter: new BraintrustExporter({
    //   parent: `project_name:${process.env.PROJECT_NAME || 'rag-chatbot-demo'}`,
    //   filterAISpans: true, // Only send AI-related spans
    // }),
  });
}