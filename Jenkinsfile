pipeline {
    agent none
    options {
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }
    environment {
        HOME = "./"
        CYPRESS_CREDENTIALS = credentials('temmpo-cypress-test-account')
        NO_COLOR = 1
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
                sh 'cypress run --browser chrome'
            }
            when {
                branch 'demo_stable'
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
            when {
                branch 'prod_stable'
            }
        }
    }
    post {
        failure {
            archiveArtifacts artifacts: 'cypress/screenshots/*, cypress/videos/*', allowEmptyArchive: true, fingerprint: true
            mail bcc: '', body: "Please go to ${BUILD_URL} to review the output of the failure.  Go to ${RUN_ARTIFACTS_DISPLAY_URL} to view any artifacts, such as Cypress screenshots or videos.", cc: '', from: '', replyTo: '', subject: "${JOB_NAME} Jenkins pipeline failed", to: 'tessa.alexander@bristol.ac.uk'
        }
    }
}
