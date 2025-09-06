from flask import Flask
import logging
from opentelemetry import trace, _logs
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._logs_exporter import OTLPLogExporter

app = Flask(__name__)

# === OpenTelemetry Resource ===
resource = Resource(attributes={
    "service.name": "flask-app",
    "environment": "dev"
})

# === Tracing Setup ===
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces",
    insecure=True
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

# === Logging Setup ===
log_provider = LoggerProvider(resource=resource)
_log_exporter = OTLPLogExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/logs",
    insecure=True
)
log_provider.add_log_record_processor(BatchLogRecordProcessor(_log_exporter))
_logs.set_logger_provider(log_provider)

# Python standard logging
logger = logging.getLogger("flask-app-logger")
logger.setLevel(logging.INFO)

@app.route("/")
def hello():
    logger.info("Hello endpoint called")  # log via OTEL
    with tracer.start_as_current_span("hello-span"):
        return "Hello from Flask + OpenTelemetry!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
