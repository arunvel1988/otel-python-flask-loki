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


##########################################################################

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        logging.info("Received request at / endpoint")
        
        # Fancy HTML response with OpenTelemetry info
        html = """
        <html>
        <head>
            <title>Flask + OpenTelemetry Demo</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f0f8ff; margin: 40px; }
                h1 { color: #2c3e50; }
                p { font-size: 1.1em; color: #34495e; }
                a { text-decoration: none; color: #2980b9; font-weight: bold; }
                a:hover { color: #e74c3c; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Welcome to Flask + OpenTelemetry Demo!</h1>
                <p>This endpoint is instrumented with <strong>OpenTelemetry</strong>:</p>
                <ul>
                    <li><strong>Trace:</strong> Groups all operations for a request.</li>
                    <li><strong>Span:</strong> Measures individual operations within a trace (e.g., this page rendering).</li>
                    <li><strong>Logs:</strong> Recorded events sent along with traces to observability backend.</li>
                </ul>
                <p>Explore other demo endpoints:</p>
                <ul>
                    <li><a href="/db">/db</a> - Simulates a database operation.</li>
                    <li><a href="/compute">/compute</a> - Performs a CPU-intensive computation.</li>
                    <li><a href="/error">/error</a> - Simulates an error for tracing and logging.</li>
                </ul>
                <p>All traces and logs from these endpoints are exported to your configured <strong>OpenTelemetry Collector → Tempo</strong> pipeline, viewable in Grafana.</p>
                <p>Enjoy exploring distributed tracing! 🌟</p>
            </div>
        </body>
        </html>
        """
        return render_template_string(html)




####################################################################################

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
