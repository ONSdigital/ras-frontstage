#/bin/bash

# First check all the required environment variables are set
for env_var in SECURITY_USER_NAME SECURITY_USER_PASSWORD PARTY_URL OAUTH_URL; do
    if [ -z ${!env_var} ]
    then
        echo "$env_var is missing"
        exit 1
    fi
done

# Then read all the lines in the file and delete them by hitting the endpoints
while read email; do
    PARTY_JSON='{"email":"'"$email"'"}'
    echo "========== Beginning deletion of  $email =========="
    echo "-- Deleting $email from party --"
    curl -v -d $PARTY_JSON -H "Content-Type: application/json" --user ${SECURITY_USER_NAME}:${SECURITY_USER_PASSWORD} -X DELETE ${PARTY_URL}/party-api/v1/respondents/email

    echo "-- Deleting $email from auth --"
    curl -v -F "username=$email" --user ${SECURITY_USER_NAME}:${SECURITY_USER_PASSWORD} -X DELETE ${OAUTH_URL}/api/account/user

    echo "========== Finished deleting $email =========="
done < accounts-to-be-deleted.txt
