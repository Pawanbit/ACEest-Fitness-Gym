pipeline {
    agent any
    options { timestamps(); disableConcurrentBuilds() }
    triggers { pollSCM('H/5 * * * *') }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build & Validate') {
            steps {
                sh 'python3 -m compileall -q app.py tests'
                sh 'python3 -m pip install --user -r requirements-dev.txt'
                sh 'python3 -m pytest -q'
            }
        }
        stage('Docker Build') {
            steps { sh 'docker build -t aceest-fitness:jenkins-${BUILD_NUMBER} .' }
        }
    }
    post {
        always { echo 'ACEest Jenkins build finished. Review stage results above.' }
    }
}
