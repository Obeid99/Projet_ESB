pipeline {
    agent any

    environment {
        APP_IMAGE = "esb-frontend:latest" // Replace with your Docker image name for esb-frontend
        BACKEND_PORT = "5000"
        FRONTEND_PORT = "3000"
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/Obeid99/Projet_ESB.git', branch: 'integration'
            }
        }

        stage('Build Combined Docker Image') {
            steps {
                sh 'docker build -t $APP_IMAGE .'
            }
        }

        stage('Run Combined Container') {
            steps {
                sh 'docker run -d -p $BACKEND_PORT:5000 -p $FRONTEND_PORT:3000 --name test-app --env-file backend-production/.env $APP_IMAGE'
            }
        }

        stage('Test Backend') {
            steps {
                sh 'curl --retry 5 --retry-delay 3 http://localhost:$BACKEND_PORT/health || echo "Backend health check failed"'
            }
        }

        stage('Test Frontend') {
            steps {
                sh 'curl --retry 5 --retry-delay 3 http://localhost:$FRONTEND_PORT || echo "Frontend health check failed"'
            }
        }

        stage('Cleanup') {
            steps {
                sh 'docker stop test-app || true && docker rm test-app || true'
            }
        }
    }
}