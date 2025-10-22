# Deploying the Application

This guide covers the deployment of the `scrapeme` application using Docker Compose and Kubernetes.

## Docker Compose

For a simple, single-node deployment, you can use the provided `docker-compose.production.yaml` file.

### 1. Configuration

Create a `.env` file with the necessary environment variables. You can use the `.env.example` file as a template.

### 2. Running the Application

To start the application, run the following command:

```bash
docker-compose -f docker-compose.production.yaml up -d
```

This will start the `scrapeme` application and a Prometheus container for monitoring.

## Kubernetes

For a scalable and production-ready deployment, you can use the Kubernetes manifests in the `k8s` directory.

### 1. Namespace

Create a dedicated namespace for the application:

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configuration

Create a `ConfigMap` and a `Secret` with the application configuration and secrets:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
```

### 3. Deployment

Deploy the application using the `Deployment` manifest:

```bash
kubectl apply -f k8s/deployment.yaml
```

This will create a `Deployment` with a configurable number of replicas.

### 4. Service

Expose the application using a `Service`:

```bash
kubectl apply -f k8s/service.yaml
```

### 5. Horizontal Pod Autoscaler (HPA)

To automatically scale the application based on CPU utilization, you can use the `HorizontalPodAutoscaler`:

```bash
kubectl apply -f k8s/hpa.yaml
```

### 6. CronJob

The `k8s/cronjob.yaml` manifest defines a `CronJob` that runs the scraper on a schedule.
