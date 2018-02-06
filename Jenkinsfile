pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        stage('dev') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                DEV_SECURITY = credentials('DEV_SECURITY')
                CF_USER = credentials('CF_USER')

                OAUTH_SECRET_KEY = credentials('OAUTH_SECRET_KEY')
                JWT_SECRET = credentials('JWT_SECRET')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s dev"
                sh 'cf push --no-start ras-frontstage-dev'
                sh 'cf set-env ras-frontstage-dev ONS_ENV dev'
                sh "cf set-env ras-frontstage-dev SECURITY_USER_NAME ${env.DEV_SECURITY_USR}"
                sh "cf set-env ras-frontstage-dev SECRET_KEY ${env.OAUTH_SECRET_KEY}"
                sh "cf set-env ras-frontstage-dev SECURITY_USER_PASSWORD ${env.DEV_SECURITY_PSW}"
                sh "cf set-env ras-frontstage-dev JWT_SECRET ${env.JWT_SECRET}"

                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_HOST ras-frontstage-api-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_PORT 80"
                sh 'cf start ras-frontstage-dev'
            }
        }

        stage('ci?') {
            agent none
            steps {
                script {
                    try {
                        timeout(time: 60, unit: 'SECONDS') {
                            script {
                                env.deploy_ci = input message: 'Deploy to CI?', id: 'deploy_ci', parameters: [choice(name: 'Deploy to CI', choices: 'no\nyes', description: 'Choose "yes" if you want to deploy to CI')]
                            }
                        }
                    } catch (ignored) {
                        echo 'Skipping ci deployment'
                    }
                }
            }
        }

        stage('ci') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }

            }
            when {
                environment name: 'deploy_ci', value: 'yes'
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                CI_SECURITY = credentials('CI_SECURITY')
                CF_USER = credentials('CF_USER')

                OAUTH_SECRET_KEY = credentials('OAUTH_SECRET_KEY')
                JWT_SECRET = credentials('JWT_SECRET')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s ci"
                sh 'cf push --no-start ras-frontstage-ci'
                sh 'cf set-env ras-frontstage-ci ONS_ENV ci'
                sh "cf set-env ras-frontstage-dev SECURITY_USER_NAME ${env.DEV_SECURITY_USR}"
                sh "cf set-env ras-frontstage-dev SECRET_KEY ${env.OAUTH_SECRET_KEY}"
                sh "cf set-env ras-frontstage-dev SECURITY_USER_PASSWORD ${env.DEV_SECURITY_PSW}"
                sh "cf set-env ras-frontstage-dev JWT_SECRET ${env.JWT_SECRET}"

                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_HOST ras-frontstage-api-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_PORT 80"
                sh 'cf start ras-frontstage-ci'
            }
        }

        stage('release?') {
            agent none
            steps {
                script {
                    try {
                        timeout(time: 60, unit: 'SECONDS') {
                            script {
                                env.do_release = input message: 'Do a release?', id: 'do_release', parameters: [choice(name: 'Deploy to test', choices: 'no\nyes', description: 'Choose "yes" if you want to create a tag')]
                            }
                        }
                    } catch (ignored) {
                        echo 'Skipping test deployment'
                    }
                }
            }
        }

        stage('release') {
            agent {
                docker {
                    image 'node'
                    args '-u root'
                }

            }
            environment {
                GITHUB_API_KEY = credentials('GITHUB_API_KEY')
            }
            when {
                environment name: 'do_release', value: 'yes'
            }
            steps {
                // Prune any local tags created by any other builds
                sh "git tag -l | xargs git tag -d && git fetch -t"
                sh "git remote set-url origin https://ons-sdc:${GITHUB_API_KEY}@github.com/ONSdigital/ras-collection-instrument.git"
                sh "npm install -g bmpr"
                sh "bmpr patch|xargs git push origin"
            }
        }

        stage('test') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }

            }
            when {
                environment name: 'do_release', value: 'yes'
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                TEST_SECURITY = credentials('TEST_SECURITY')
                CF_USER = credentials('CF_USER')

                OAUTH_SECRET_KEY = credentials('OAUTH_SECRET_KEY')
                JWT_SECRET = credentials('JWT_SECRET')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s test"
                sh 'cf push --no-start ras-frontstage-test'
                sh 'cf set-env ras-frontstage-test ONS_ENV test'
                sh "cf set-env ras-frontstage-dev SECURITY_USER_NAME ${env.DEV_SECURITY_USR}"
                sh "cf set-env ras-frontstage-dev SECRET_KEY ${env.OAUTH_SECRET_KEY}"
                sh "cf set-env ras-frontstage-dev SECURITY_USER_PASSWORD ${env.DEV_SECURITY_PSW}"
                sh "cf set-env ras-frontstage-dev JWT_SECRET ${env.JWT_SECRET}"

                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_HOST ras-frontstage-api-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-frontstage-dev RAS_FRONTSTAGE_API_PORT 80"
                sh 'cf start ras-frontstage-test'
            }
        }
    }

    post {
        always {
            cleanWs()
            dir('${env.WORKSPACE}@tmp') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script@tmp') {
                deleteDir()
            }
        }
    }
}