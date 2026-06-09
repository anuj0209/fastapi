pipeline {
  agent any
  parameters {
    string(name: 'DOCKER_REGISTRY', defaultValue: '', description: 'Optional Docker registry host (e.g. docker.io/username). Leave empty to use local Docker image.')
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
      steps {
        withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG_FILE')]) {
          sh '''
            export KUBECONFIG="${KUBECONFIG_FILE}"
            kubectl apply -f "${KUBE_DEPLOYMENT_FILE}"
            IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
            if [ -f image_name.txt ]; then
              IMAGE=$(cat image_name.txt)
            fi
            kubectl set image deployment/${DEPLOYMENT_NAME} ${IMAGE_NAME}="${IMAGE}" --record
            kubectl rollout status deployment/${DEPLOYMENT_NAME} --timeout=120s
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
