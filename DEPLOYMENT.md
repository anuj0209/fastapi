# Local Minikube Model Server Deployment

## Overview
This repository deploys a local AI model server on a minikube cluster.
The model server runs in Kubernetes using a local Docker image built inside the minikube daemon.

## Files used in this workflow
- `model-deployment.yaml` — Kubernetes manifest for PVC, Deployment, and Service
- `model_server/Dockerfile` — Docker image build instructions for the FastAPI model server
- `model_server/requirements.txt` — Python dependencies for the containerized app
- `model_server/app.py` — FastAPI app source code handling model upload and prediction

## Removed file
- `jenkins-deployment.yaml` was removed because it is unrelated to the local minikube model deployment flow.

## Prerequisites
- `minikube` installed
- `kubectl` installed and configured
- `docker` available on the host
- Access to the host Docker daemon or minikube Docker daemon

## Deployment steps

1. Start minikube on the Docker driver

```bash
sudo minikube delete --all
sudo minikube start --driver=docker --force
```

2. Build the local Docker image inside the minikube Docker daemon

```bash
sudo -i bash -lc 'cd /home/anuj0209/Github && eval "$(minikube -p minikube docker-env)" && docker build -t model-server:latest -f model_server/Dockerfile .'
```

3. Apply the Kubernetes resources

```bash
sudo kubectl apply -f model-deployment.yaml
```

4. Restart the deployment if needed

```bash
sudo kubectl rollout restart deployment/model-server
sudo kubectl rollout status deployment/model-server --timeout=120s
```

5. Verify the pod is running

```bash
sudo kubectl get pods -l app=model-server -o wide
sudo kubectl logs pod/$(sudo kubectl get pods -l app=model-server -o jsonpath='{.items[0].metadata.name}')
```

## Key fixes from this workflow

- The application required `python-multipart` for FastAPI file upload support.
  This dependency was added to `model_server/requirements.txt`.
- The local image must be built inside minikube's Docker daemon so Kubernetes can use it without pulling from Docker Hub.
- `imagePullPolicy: IfNotPresent` is used to let the node reuse the local image when available.

## Troubleshooting

- `ErrImagePull` / `ImagePullBackOff`
  - Ensure `model-server:latest` exists in minikube's Docker daemon.
  - Build it using the `minikube docker-env` shell and `docker build` inside that environment.

- `CrashLoopBackOff`
  - Check `kubectl logs` for missing Python packages or runtime errors.
  - In this case, the missing package was `python-multipart` and the app crashed before startup.

- Kubernetes TLS / minikube cert issues
  - If `kubectl` cannot connect due certificate verification, use `sudo` consistently with the same minikube profile or reinitialize minikube.

## Notes

- The model server expects a model file at `/models/model.pt`.
- Upload the model via the `/upload` endpoint before calling `/predict`.
- The service is exposed as a `NodePort` on port `30081` in `model-deployment.yaml`.

## Jenkins deployment

To deploy an update from Jenkins:

1. Configure the Jenkins job to use this repository.
2. Add a `kubeconfig` file credential in Jenkins and set its credential ID to `kubeconfig` (or override it with the `KUBE_CREDENTIAL_ID` pipeline parameter).
3. Ensure the stored kubeconfig is flattened and contains embedded TLS data (`certificate-authority-data`, `client-certificate-data`, `client-key-data`). This avoids referencing local paths such as `/home/anuj0209/.minikube/profiles/minikube/client.crt`, which Jenkins cannot access.
4. Optionally add Docker credentials for pushing images to a registry with credential ID `dockerhub`.
5. Run the Jenkins pipeline from `Jenkinsfile`. If you need to skip Kubernetes deployment until credentials are configured, set `SKIP_DEPLOY=true`.

If `DOCKER_REGISTRY` is empty, the pipeline will build the image locally and apply the deployment manifest. If `DOCKER_REGISTRY` is set, it will push the tagged image to the registry and update the deployment with the pushed image.
