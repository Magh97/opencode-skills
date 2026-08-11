---
name: devops-monitoring
description: "Observabilidad con OpenTelemetry, Prometheus y Grafana (2026). Cubre traces, métricas, logs, SLO/SLI dashboards, alerting con Alertmanager, synthetic monitoring, y stack LGTM (Loki, Grafana, Tempo, Mimir). Actívala al instrumentar aplicaciones, configurar dashboards, o definir SLOs."
disable-model-invocation: true
---

# Observability & Monitoring

Guía de observabilidad con OpenTelemetry + Prometheus + Grafana (2026).

---

## Stack LGTM

```
Loki        → Logs
Grafana     → Dashboards + alerting
Tempo       → Traces
Mimir       → Metrics (long-term Prometheus storage)
```

---

## OpenTelemetry (OTel)

Estándar universal de observabilidad. Reemplaza instrumentación propietaria.

### Instrumentación en Node.js

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: 'http://otel-collector:4318/v1/traces',
  }),
  metricExporter: new OTLPMetricExporter({
    url: 'http://otel-collector:4318/v1/metrics',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
  serviceName: 'miapp-api',
});

sdk.start();
```

### Instrumentación en Python

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configurar tracer
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces"))
)
trace.set_tracer_provider(provider)

# Auto-instrumentar FastAPI
FastAPIInstrumentor.instrument_app(app)
```

### Custom spans

```python
tracer = trace.get_tracer(__name__)

@router.post("/orders")
async def create_order(body: OrderCreate, service: OrderService = Depends()):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("customer.id", body.customer_id)
        span.set_attribute("order.amount", body.amount)

        # Sub-span para operación de DB
        with tracer.start_as_current_span("db.insert_order"):
            order = await service.create(body)

        return order
```

---

## Prometheus — Métricas

```yaml
# ServiceMonitor (Prometheus Operator)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: miapp-api
spec:
  selector:
    matchLabels:
      app: miapp-api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

```python
# Exponer métricas desde FastAPI con prometheus_client
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
request_duration = Histogram(
    "http_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"],
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## Grafana — Dashboards

### SLO Dashboard (recomendado)

```promql
# SLI: % de requests exitosos
sum(rate(http_requests_total{status!~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m])) * 100

# Error budget restante mensual
(100 - <SLO_target>) - (100 - <SLI_actual>)

# Burn rate: cuánto más rápido de lo normal quemamos error budget
rate(http_requests_total{status=~"5.."}[1h]) 
/ 
rate(http_requests_total[1h]) * 100
```

### RED Metrics (todo servicio debe exponerlas)

| Métrica | Prometheus | Descripción |
|---------|------------|-------------|
| **Rate** | `rate(http_requests_total[5m])` | Requests por segundo |
| **Errors** | `rate(http_requests_total{status=~"5.."}[5m])` | Tasa de errores |
| **Duration** | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | P95 latency |

---

## Alerting (Alertmanager)

```yaml
# rules/slos.yaml
groups:
- name: slos
  rules:
  - alert: HighErrorRate
    expr: |
      sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
      /
      sum(rate(http_requests_total[5m])) by (service) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.service }}"
      description: "Error rate is {{ $value | humanizePercentage }}"

  - alert: ErrorBudgetBurn
    expr: |
      (1 - sum(rate(http_requests_total{status!~"5.."}[1h])) 
      / sum(rate(http_requests_total[1h]))) 
      > (14.4 * (1 - 0.999))
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Error budget burn rate too high"
```

---

## Logs — Loki + Promtail

```
Application → stdout (JSON) → Promtail → Loki → Grafana
```

```python
# structlog configurado para Loki
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
```

```yaml
# promtail config
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
```

---

## Synthetic Monitoring (Blackbox Exporter)

```yaml
# Probar endpoint cada 30s desde fuera del cluster
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_status_codes: [200, 201]
      method: GET
```

---

## Checklist observabilidad

- [ ] OpenTelemetry auto-instrumentation en todos los servicios
- [ ] RED metrics (Rate, Errors, Duration) expuestas en `/metrics`
- [ ] SLOs definidos y dashboards en Grafana
- [ ] Alertas para error rate > SLO y error budget burn rate
- [ ] Logs estructurados en JSON a stdout → Loki
- [ ] Traces con OTLP → Tempo (o Jaeger)
- [ ] Synthetic monitoring para endpoints críticos
- [ ] Dashboards por servicio (no uno gigante para todo)
- [ ] Alertas con runbooks (qué hacer cuando se disparan)
