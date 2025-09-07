from flask import Flask, render_template_string, request
import logging
import time
import random

# ------------------------
# OpenTelemetry Core Setup
# ------------------------
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource

# Traces
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Flask instrumentation
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ------------------------
# Resource (common labels)
# ------------------------
resource = Resource(attributes={"service.name": "flask-app"})

# ---- Traces ----
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/traces"
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
tracer = trace.get_tracer(__name__)

# ---- Logs ----
logger_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/logs"
)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)
logging.getLogger().setLevel(logging.INFO)

# ---- Metrics ----
metric_exporter = OTLPMetricExporter(
    endpoint="http://opentelemetry-collector-svc:4318/v1/metrics"
)
reader = PeriodicExportingMetricReader(metric_exporter)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)

# Example metrics
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Number of HTTP requests processed",
)

latency_histogram = meter.create_histogram(
    name="http_request_duration_seconds",
    description="Request duration in seconds",
)

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    request_counter.add(1, {"method": request.method, "endpoint": request.path})
    latency_histogram.record(duration, {"method": request.method, "endpoint": request.path})
    return response

# ------------------------
# Demo Endpoints
# ------------------------
@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logging.info("Received request at / endpoint")
        html = """
        <html>
        <head><title>Flask + OpenTelemetry Demo</title></head>
        <body>
            <h1>Flask + OpenTelemetry Demo</h1>
            <ul>
                <li><a href="/db">/db</a> - Simulates a database operation.</li>
                <li><a href="/compute">/compute</a> - Performs a CPU-intensive computation.</li>
                <li><a href="/error">/error</a> - Simulates an error.</li>
            </ul>
            <p>Now exporting: <b>Traces</b>, <b>Logs</b>, <b>Metrics</b> → OTEL Collector → Tempo/Loki/Prometheus</p>
        </body>
        </html>
        """
        return render_template_string(html)

@app.route("/compute")
def compute():
    with tracer.start_as_current_span("compute-span"):
        logging.info("Start compute simulation")
        result = sum(i * i for i in range(1, 1000))
        time.sleep(random.uniform(0.1, 0.5))
        logging.info(f"Compute result: {result}")
        return f"Compute done! Result: {result}"

@app.route("/db")
def fake_db():
    with tracer.start_as_current_span("db-span"):
        logging.info("Start fake DB operation")
        with tracer.start_as_current_span("query-span"):
            time.sleep(random.uniform(0.1, 0.3))
            logging.info("DB query completed")
        with tracer.start_as_current_span("update-span"):
            time.sleep(random.uniform(0.1, 0.2))
            logging.info("DB update completed")
        return "DB operation executed!"

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
