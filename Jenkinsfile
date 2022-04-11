pipeline {
    agent none
    options {
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }
    triggers { pollSCM('H/5 * * * 1-5') }
    environment {
        CYPRESS_CACHE_FOLDER = './.cache/Cypress'
        HOME = "$WORKSPACE"
    }
    stages {
        stage('Demo: Cypress tests') {
            agent {
                docker {
                    image 'cypress/included:9.5.3'
                    args '--add-host py-web-d0.epi.bris.ac.uk:172.25.2.76 --entrypoint=""'
                }
            }
            steps {
                sh "echo $CYPRESS_CACHE_FOLDER"
                sh "echo $HOME"
                sh 'cypress run --browser chrome'
            }
        }
        stage('Production: Cypress tests') {
            agent {
                docker {
                    image 'cypress/included:9.5.3'
                    args '--add-host temmpo.org.uk:172.25.2.104 --entrypoint=""'
                }
            }
            steps {
                sh 'cypress run --browser chrome --config baseUrl=https://temmpo.org.uk'
            }
        }
    }
    post {
        failure {
            mail bcc: '', body: "Please go to ${BUILD_URL} and review the failure.", cc: '', from: '', replyTo: '', subject: "${JOB_NAME} Jenkins pipeline failed", to: 'tessa.alexander@bristol.ac.uk'
        }
    }
}
