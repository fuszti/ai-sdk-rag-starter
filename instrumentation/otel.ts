// @ts-nocheck
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto';
import { BatchSpanProcessor, Sampler, SamplingDecision, SamplingResult } from '@opentelemetry/sdk-trace-base';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { diag, DiagConsoleLogger, DiagLogLevel, Context, SpanKind, Attributes, Link } from '@opentelemetry/api';
import { SemanticConventions, OpenInferenceSpanKind } from '@arizeai/openinference-semantic-conventions';

diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.WARN);

const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: 'ai-rag-app',
  'project.name': 'rag-demo',
});

const { OPENINFERENCE_SPAN_KIND } = SemanticConventions;

class RAGOnlySampler implements Sampler {
  shouldSample(
    _context: Context,
    _traceId: string,
    spanName: string,
    _spanKind: SpanKind,
    attributes?: Attributes,
    _links?: Link[],
  ): SamplingResult {
    const kind = attributes?.[OPENINFERENCE_SPAN_KIND] as unknown;
    const isRagSpan =
      kind === OpenInferenceSpanKind.LLM ||
      kind === OpenInferenceSpanKind.EMBEDDING ||
      kind === OpenInferenceSpanKind.RETRIEVER;
    const isWhitelistedName = (
      spanName === 'chat-completion' ||
      spanName === 'query-embedding' ||
      spanName === 'batch-embedding' ||
      spanName === 'knowledge-retrieval'
    );
    return {
      decision: (isRagSpan || isWhitelistedName)
        ? SamplingDecision.RECORD_AND_SAMPLED
        : SamplingDecision.NOT_RECORD,
    };
  }
  toString(): string { return 'RAGOnlySampler'; }
}

const exporter = new OTLPTraceExporter({
  url: process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT || 'http://localhost:6006/v1/traces',
  headers: {},
});

const provider = new NodeTracerProvider({
  resource,
  sampler: new RAGOnlySampler(),
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();

console.log('🎯 Clean OpenTelemetry initialized - MANUAL SPANS ONLY');
console.log('📍 Sending traces to:', process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT || 'http://localhost:6006/v1/traces');

process.on('SIGTERM', () => {
  provider.shutdown().finally(() => process.exit(0));
});


