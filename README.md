Model server deployment using minikube

This repository deploys a local AI model server on a minikube cluster.

Files:

- `model-deployment.yaml` — Kubernetes manifest for PVC, Deployment, and Service
- `model_server/Dockerfile` — Docker image build instructions for the FastAPI model server
- `model_server/requirements.txt` — Python dependencies for the containerized app
- `model_server/app.py` — FastAPI application source
- `DEPLOYMENT.md` — documentation for the local deployment process

Deployment steps:

1. Start minikube on Docker:

   ```bash
   sudo minikube delete --all
   sudo minikube start --driver=docker --force
   ```

2. Build the Docker image in minikube's daemon:

   ```bash
   sudo -i bash -lc 'cd /home/anuj0209/Github && eval "$(minikube -p minikube docker-env)" && docker build -t model-server:latest -f model_server/Dockerfile .'
   ```

3. Deploy to Kubernetes:

   ```bash
   sudo kubectl apply -f model-deployment.yaml
   sudo kubectl rollout restart deployment/model-server
   sudo kubectl rollout status deployment/model-server --timeout=120s
   ```

4. Verify the pod and logs:

   ```bash
   sudo kubectl get pods -l app=model-server -o wide
   sudo kubectl logs pod/$(sudo kubectl get pods -l app=model-server -o jsonpath='{.items[0].metadata.name}')
   ```

Troubleshooting notes:

- Build the image inside minikube so the cluster can use the local image without pulling from Docker Hub.
- Add `python-multipart` to `model_server/requirements.txt` for FastAPI file upload support.
- Use `imagePullPolicy: IfNotPresent` to allow Kubernetes to reuse the local image.

Jenkins deployment

- Use `Jenkinsfile` to build the image, optionally push it to a Docker registry, and update the Kubernetes deployment.
- Configure Jenkins with a `kubeconfig` file credential for cluster access, and a Docker credential named `dockerhub` if using a registry.
- Ensure the Jenkins kubeconfig credential contains embedded TLS certificate/key data instead of local host file references such as `/home/anuj0209/.minikube/profiles/minikube/client.crt`.
- If no registry is configured, Jenkins will build the local image and deploy it directly if the Jenkins agent has access to the same Docker environment as the cluster.

Note: `jenkins-deployment.yaml` has been removed because it was not needed for this local minikube model deployment flow.
