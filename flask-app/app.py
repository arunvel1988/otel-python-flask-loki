from flask import Flask
import logging
import time
import random

# OpenTelemetry core
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Logging
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# OTLP Trace Exporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Flask instrumentation
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ------------------------
# OpenTelemetry Setup
# ------------------------
resource = Resource(attributes={"service.name": "flask-app"})

# ---- Traces ----
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces",
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
tracer = trace.get_tracer(__name__)

# ---- Logs ----
logger_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/logs",
)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)
logging.getLogger().setLevel(logging.INFO)

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# ------------------------
# Demo Endpoints
# ------------------------

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logging.info("Received request at / endpoint")
        return "Hello from Flask + OpenTelemetry! ✅ Traces and Logs are exported."

@app.route("/compute")
def compute():
    with tracer.start_as_current_span("compute-span") as span:
        logging.info("Start compute simulation")
        result = sum(i * i for i in range(1, 1000))
        time.sleep(random.uniform(0.1, 0.5))  # simulate work
        logging.info(f"Compute result: {result}")
        return f"Compute done! Result: {result}"

@app.route("/db")
def fake_db():
    with tracer.start_as_current_span("db-span") as span:
        logging.info("Start fake DB operation")
        with tracer.start_as_current_span("query-span"):
            time.sleep(random.uniform(0.1, 0.3))  # simulate DB query
            logging.info("DB query completed")
        with tracer.start_as_current_span("update-span"):
            time.sleep(random.uniform(0.1, 0.2))  # simulate DB update
            logging.info("DB update completed")
        return "Fake DB operation done!"

@app.route("/error")
def error_route():
    with tracer.start_as_current_span("error-span"):
        try:
            1 / 0
        except ZeroDivisionError as e:
            logging.error(f"An error occurred: {e}")
            return "Error route triggered, check OTEL logs.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
