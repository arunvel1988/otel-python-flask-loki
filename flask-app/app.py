from flask import Flask
from opentelemetry import trace, _logs as otel_logs
from opentelemetry.sdk.resources import Resource

# --- Tracing imports ---
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# --- Logging imports ---
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# --- Flask Instrumentation ---
from opentelemetry.instrumentation.flask import FlaskInstrumentor


# ------------------------
# OpenTelemetry Resource
# ------------------------
resource = Resource.create({"service.name": "flask-app"})

# ------------------------
# Tracing Setup
# ------------------------
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces",
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
tracer = trace.get_tracer(__name__)

# ------------------------
# Logging Setup
# ------------------------
logger_provider = LoggerProvider(resource=resource)
otel_logs.set_logger_provider(logger_provider)

otlp_log_exporter = OTLPLogExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/logs",
)
logger_provider.add_log_processor(BatchLogProcessor(otlp_log_exporter))
logger = otel_logs.get_logger("flask-app")

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logger.emit("Received request at / endpoint")
        return "Hello from Flask + OpenTelemetry! (Traces + Logs)"


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
