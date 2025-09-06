from flask import Flask
import logging

# ------------------------
# OpenTelemetry imports
# ------------------------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Logs SDK
from opentelemetry.sdk.logs import LoggerProvider
from opentelemetry.sdk.logs.export import BatchLogProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ------------------------
# Resource
# ------------------------
resource = Resource(attributes={"service.name": "flask-app"})

# ------------------------
# Tracing
# ------------------------
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces"
)
span_processor = BatchSpanProcessor(otlp_trace_exporter)
trace_provider.add_span_processor(span_processor)

# ------------------------
# Logging
# ------------------------
logger_provider = LoggerProvider(resource=resource)
logs_exporter = OTLPLogExporter(endpoint="http://opentelemetry-collector-svc:4318/v1/logs")
log_processor = BatchLogProcessor(logs_exporter)
logger_provider.add_log_processor(log_processor)

from opentelemetry import logs
logs.set_logger_provider(logger_provider)

logger = logs.get_logger("flask-app")

# ------------------------
# Flask app
# ------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logger.emit("Received request at / endpoint")
        return "Hello from Flask + OpenTelemetry! Traces and Logs exported."

@app.route("/error")
def error_route():
    with tracer.start_as_current_span("error-span"):
        try:
            1 / 0
        except ZeroDivisionError as e:
            logger.emit(f"An error occurred: {e}", severity_text="ERROR")
            return "Error route triggered, check OTEL logs.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
