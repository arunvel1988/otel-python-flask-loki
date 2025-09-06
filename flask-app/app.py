from flask import Flask
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, OTLPLogExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ------------------------
# OpenTelemetry Resources
# ------------------------
resource = Resource(attributes={"service.name": "flask-app"})

# ------------------------
# Tracing Setup
# ------------------------
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces"
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

tracer = trace.get_tracer(__name__)

# ------------------------
# Logging Setup
# ------------------------
logger_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/logs"
)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Attach logging handler to Python logging
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

logger = logging.getLogger("flask-app")

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logger.info("Received request at / endpoint")
        return "Hello from Flask + OpenTelemetry! Traces and Logs exported."

@app.route("/error")
def error_route():
    with tracer.start_as_current_span("error-span"):
        try:
            1 / 0
        except ZeroDivisionError as e:
            logger.error(f"An error occurred: {e}")
            return "Error route triggered, check OTEL logs.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
