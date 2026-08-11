---
name: devops-cloud
description: "Cloud computing en AWS, GCP y Azure (2026). Cubre servicios serverless (Lambda, Cloud Run, Azure Functions), FinOps y cost optimization (clusters al 40% → target 70%), managed Kubernetes (EKS, GKE, AKS), CDN y edge computing, y estrategias multi-cloud. Actívala al elegir servicios cloud, optimizar costos, o migrar entre clouds."
disable-model-invocation: true
---

# Cloud & FinOps

Guía de cloud computing y optimización de costos (2026). AWS, GCP, Azure.

---

## Tabla de decisión cloud

| Criterio | AWS | GCP | Azure |
|----------|-----|-----|-------|
| **Kubernetes** | EKS | GKE (mejor integración) | AKS |
| **Serverless** | Lambda | Cloud Run | Azure Functions |
| **PostgreSQL** | RDS / Aurora | Cloud SQL / AlloyDB | Azure PostgreSQL |
| **SQL Server** | RDS | Cloud SQL | ⭐ Azure SQL (nativo) |
| **AI/ML** | SageMaker / Bedrock | ⭐ Vertex AI | Azure AI |
| **Ecosistema .NET** | Bueno | Bueno | ⭐ Óptimo |
| **FinOps tools** | Cost Explorer | Billing Reports | Cost Management |

---

## Managed Kubernetes

| Servicio | Ventaja | Cuándo |
|----------|---------|--------|
| **GKE** (Google) | Auto-pilot, mejor integración GCP | Default si estás en GCP |
| **EKS** (AWS) | EKS Auto Mode, madurez | Default si estás en AWS |
| **AKS** (Azure) | Integración con Azure AD, monitor | Default si estás en Azure |

```bash
# GKE Autopilot (sin gestionar nodos)
gcloud container clusters create-auto miapp-cluster --region us-central1

# EKS con eksctl
eksctl create cluster --name miapp --region us-east-1 --node-type t4g.medium --nodes 3
```

---

## Serverless

### AWS Lambda

```python
import json

def handler(event, context):
    order_id = event['pathParameters']['id']
    order = get_order(order_id)
    return {
        'statusCode': 200,
        'body': json.dumps(order),
    }
```

### Cloud Run (GCP)

```yaml
# Deploy de contenedor como serverless
gcloud run deploy miapp-api \
  --image ghcr.io/mi-org/miapp:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80
```

### Azure Functions

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="orders/{order_id}", methods=["GET"])
def get_order(req: func.HttpRequest) -> func.HttpResponse:
    order_id = req.route_params.get("order_id")
    order = fetch_order(order_id)
    return func.HttpResponse(json.dumps(order), status_code=200)
```

---

## FinOps — Cost Optimization

**Problema 2026**: clusters Kubernetes con <40% de utilización. Gap entre requests y usage real.

### 5 áreas de gasto (prioridad)

```
1. Compute (requests vs usage gap)        ← Mayor desperdicio
2. Cross-zone networking + egress
3. Storage + snapshots
4. Observability (logs, metrics, traces)
5. Load balancers + IPs estáticas
```

### Checklist reducción de costos (30-50% de ahorro)

```bash
# 1. Rightsizing: ajustar requests de CPU/memoria al uso real
kubectl top pods -n miapp-prod

# 2. Spot/preemptible instances para cargas no críticas
# Staging, CI runners, workers batch

# 3. Autoscaling agresivo (scale-to-zero overnight)
# HPA minReplicas: 0 (con KEDA para escalar desde 0)

# 4. Storage class con delete policy para PVCs de staging

# 5. Lifecycle policies en S3/GCS para mover objetos a cold storage
```

### Right-sizing con Vertical Pod Autoscaler (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: miapp-api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: miapp-api
  updatePolicy:
    updateMode: "Off"  # Solo recomendar, no aplicar auto
```

---

## CDN + Edge Computing

```yaml
# CloudFront (AWS) / Cloud CDN (GCP) / Azure Front Door
# Cachear contenido estático en el edge
# Reducir latencia global, descargar origen
```

```bash
# Cloudflare Workers — lógica en el edge
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Geo-redirect
    const country = request.headers.get('cf-ipcountry');
    if (url.pathname === '/' && country === 'MX') {
      return Response.redirect('https://miapp.com.mx', 302);
    }

    return fetch(request);  // Pasar al origen
  },
};
```

---

## Multi-Cloud

| Patrón | Cuándo | Complejidad |
|--------|--------|-------------|
| **DR cross-cloud** | Recuperación ante desastre en otro cloud | Media |
| **Best-of-breed** | GCP para ML, Azure para SQL Server | Alta |
| **Cloud-agnostic** | K8s + Terraform — misma app en cualquier cloud | Alta |

```hcl
# Mismo módulo de DB, diferente provider
module "database" {
  source = "./modules/database"

  # AWS
  providers = { aws = aws.us-east-1 }
  # O GCP
  # providers = { google = google.us-central1 }
}
```

---

## Checklist cloud

- [ ] Managed Kubernetes donde sea posible (GKE/EKS/AKS)
- [ ] Serverless para cargas esporádicas o APIs simples
- [ ] FinOps: rightsizing CPU/memoria al uso real
- [ ] Spot/preemptible instances para staging y CI
- [ ] Autoscaling con scale-to-zero overnight
- [ ] CDN para assets estáticos y API caching
- [ ] Backups automatizados (RDS snapshots, pg_dump cron)
- [ ] Cost alerts: presupuesto mensual con alertas al 80% y 100%
- [ ] Multi-cloud solo si hay caso de negocio claro
- [ ] Infraestructura como código (Tofu/Terraform), sin click-ops
