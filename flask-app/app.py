from flask import Flask
import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

app = Flask(__name__)

# OpenTelemetry Tracing
resource = Resource(attributes={"service.name": "flask-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="http://opentelemetry-collector-svc:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

@app.route("/")
def hello():
    with tracer.start_as_current_span("hello-span"):
        return "Hello from Flask + OpenTelemetry!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
