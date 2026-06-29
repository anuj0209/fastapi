pipeline {
  agent any
  parameters {
    string(name: 'DOCKER_REGISTRY', defaultValue: '', description: 'Optional Docker registry host (e.g. docker.io/username). Leave empty to use local Docker image.')
    booleanParam(name: 'SKIP_DEPLOY', defaultValue: false, description: 'Skip the Kubernetes deployment stage.')
    string(name: 'KUBE_CREDENTIAL_ID', defaultValue: 'kubeconfig', description: 'Jenkins credential ID for the kubeconfig file.')
  }
  environment {
    IMAGE_NAME = 'model-server'
    IMAGE_TAG = "${BUILD_NUMBER}"
    DEPLOYMENT_NAME = 'model-server'
    KUBE_DEPLOYMENT_FILE = 'model-deployment.yaml'
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Build') {
      steps {
        sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f model_server/Dockerfile .'
      }
    }
    stage('Test') {
      steps {
        sh 'echo "No tests defined yet"'
      }
    }
    stage('Push Image') {
      when {
        expression { return params.DOCKER_REGISTRY?.trim() }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
          sh '''
            FULL_IMAGE="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin "${DOCKER_REGISTRY}"
            docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"
            docker push "${FULL_IMAGE}"
            echo "${FULL_IMAGE}" > image_name.txt
          '''
        }
      }
    }
    stage('Deploy to Kubernetes') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        withCredentials([file(credentialsId: params.KUBE_CREDENTIAL_ID, variable: 'JENKINS_KUBECONFIG')]) {
          sh '''
            export KUBECONFIG="/tmp/kubeconfig-jenkins"
            cp "${JENKINS_KUBECONFIG}" "${KUBECONFIG}"

            echo "Flattening kubeconfig to embed TLS credentials..."
            kubectl config view --flatten --minify --embed-certs --kubeconfig "${KUBECONFIG}" > /tmp/kubeconfig-jenkins.flattened
            export KUBECONFIG="/tmp/kubeconfig-jenkins.flattened"

            echo "Applying Kubernetes deployment..."
            kubectl apply -f "${KUBE_DEPLOYMENT_FILE}" --insecure-skip-tls-verify --validate=false

            IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
            if [ -f image_name.txt ]; then
              IMAGE=$(cat image_name.txt)
            fi

            echo "Updating deployment with image: ${IMAGE}"
            kubectl set image deployment/${DEPLOYMENT_NAME} ${IMAGE_NAME}="${IMAGE}" --record --insecure-skip-tls-verify

            echo "Waiting for rollout..."
            kubectl rollout status deployment/${DEPLOYMENT_NAME} --timeout=120s --insecure-skip-tls-verify
          '''
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '**/target/*.jar', allowEmptyArchive: true
    }
  }
}
