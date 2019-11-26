#/bin/bash
# usage: ./delete_users.sh [filename]

# First check all the required environment variables are set
for env_var in SECURITY_USER_NAME SECURITY_USER_PASSWORD PARTY_URL OAUTH_URL; do
    if [ -z ${!env_var} ]
    then
        echo "$env_var is missing"
        exit 1
    fi
done

# Next check the filename has been passed in
if [ -z $1 ]
then
    echo "File name needs to be provided e.g., ./delete_users.sh accounts.txt"
    exit 1
fi

# Then read all the lines in the file, one by one, and delete them by hitting the endpoints
while read email; do
    PARTY_JSON='{"email":"'"$email"'"}'
    echo "========== Beginning deletion of  $email =========="
    echo "-- Disabling all enrolments for $email --"
    enrolments_response=$(curl --write-out %{http_code} --silent --output /dev/null -d $PARTY_JSON -H "Content-Type: application/json" --user ${SECURITY_USER_NAME}:${SECURITY_USER_PASSWORD} -X PATCH ${PARTY_URL}/party-api/v1/respondents/disable-user-enrolments)
    echo "Response from disabling enrolments in party [$enrolments_response]"
    if [[ $enrolments_response -ne 200 ]]; then
        echo "Failed to disable enrolments"
        exit
    fi

    echo "-- Deleting $email from party --"
    party_delete_response=$(curl --write-out %{http_code} --silent --output /dev/null -d $PARTY_JSON -H "Content-Type: application/json" --user ${SECURITY_USER_NAME}:${SECURITY_USER_PASSWORD} -X DELETE ${PARTY_URL}/party-api/v1/respondents/email)
    echo "Response from deleting email from party [$party_delete_response]"
    if [[ $party_delete_response -ne 204 ]]; then
        echo "Failed to delete respondent from party"
        exit
    fi
    echo "-- Deleting $email from auth --"
    auth_delete_response=$(curl --write-out %{http_code} --silent --output /dev/null -F "username=$email" --user ${SECURITY_USER_NAME}:${SECURITY_USER_PASSWORD} -X DELETE ${OAUTH_URL}/api/account/user)
    echo "Response from deleting email from auth [$auth_delete_response]"
    if [[ $auth_delete_response -ne 204 ]]; then
        echo "Failed to delete respondent from auth"
        exit
    fi

    echo "========== Finished deleting $email =========="
done < $1
