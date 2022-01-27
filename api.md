# ras frontage ui routes

This page documents the Fronstage endpoints that can be hit.

## Info Endpoints

`/info`
* GET request to this endpoint displays the info of the frontstage ui.

## Privacy Endpoints

`/privacy-and-data-protection`
* GET request to this endpoint displays the privacy-and-data-protection of the frontstage ui.

## Security Endpoints

`/.well-known`
* GET Request to this endpoint displays security page of the frontstage ui.

## Contact us Endpoints

`/help`
* GET and POST Request to this endpoint allows you to access the hep page.
* GET `/vulnerability-reporting`
* GET and POST `/info-ons`
* GET and POST `/help-with-my-password`
* GET `/something-else`

`/contact-us`
* GET Request to this endpoint allows you to access the contact page.

## Account Endpoints

`/account`
* GET and POST
* GET and POST `/change-password`
* POST `/change-account-email-address`
* GET and POST `/change-account-details`
* GET `/something-else` Gets the something else once the option is selected
* POST `/something-else` Sends secure message for the something else pages

`/delete`
* GET and POST

`/confirm-account-email-change/<token>`
* GET 

`/resend-account-email-change-expired-token/<token>`
* GET

`/share-surveys`
* GET

`/share-surveys/business-selection`
* GET and POST

`/share-surveys/survey-selection`
* GET and POST

`/share-surveys/recipient-email-address`
* GET and POST

`/share-surveys/send-instruction`
* GET and POST

`/share-surveys/done`
* GET

`/transfer-surveys`
* GET 

`/transfer-surveys/business-selection`
* GET and POST

`/transfer-surveys/survey-selection`
* GET and POST

`/transfer-surveys/recipient-email-address`
* GET and POST

`/transfer-surveys/send-instruction`
* GET and POST

`/transfer-surveys/done`
* GET

`/share-surveys/accept-share-surveys/<token>`
* GET Endpoint to verify token and retrieve the summary page

`/confirm-share-surveys/<batch>`
* GET Accept endpoint when a share survey summary is accepted

`/confirm-share-surveys/<batch>/existing-account`
* GET Accept redirect endpoint for accepting share surveys for existing account

`/transfer-surveys/accept-transfer-surveys/<token>`
* GET Endpoint to verify transfer token and retrieve the summary page

`/confirm-transfer-surveys/<batch>`
* GET Accept endpoint when a transfer survey summary is accepted

`/confirm-transfer-surveys/<batch>/existing-account`
* GET Accept redirect endpoint for accepting transfer surveys for existing account

## Register Endpoints

`/create-account`
* GET and POST

`/create-account/enter-account-details`
* GET and POST

`/pending-surveys/create-account/enter-account-details`
* GET and POST Registration endpoint for account creation and verification against share surveys  and transfer surveys (Account does not exist)

`/create-account/check-email`

`/activate-account/<token>`
* GET

`/create-account/confirm-organisation-survey`
* GET

## Passwords Endpoints

`/forgot-password`
* GET and POST

`/forgot-password/check-email`
* GET

`/reset-password/<token>`
* GET and POST

`/reset-password/confirmation`
* GET

`/reset-password/check-email`
* GET

`/resend-password-email-expired-token/<token>`
* GET

## Secure Messaging Endpoints

`/create-message/`
* GET and POST

`/threads/<thread_id>`
* GET and POST Endpoint to view conversations by thread_id

`/threads`
* GET

## Sign-in Endpoints

`/`
* GET and POST 

`/resend-verification/<party_id>`
* GET Deprecated: to be removed when not in use

`/resend-verification-expired-token/<token>`
* GET 

`/logout`

## Surveys Endpoints

`/access-survey`
* GET 

`/add-survey`
* GET and POST

`/add-survey/confirm-organisation-survey`
* GET 

`/add-survey/add-survey-submit`
* GET 

`/download-survey`
* GET

`/<tag>`
* GET Displays the list of surveys for the respondent by tag.
* `tag` Represents the state the survey is in (e.g., todo, history, etc)

`/upload-survey`
* POST

`/upload-failed`
* GET

## Surveys help Endpoints

`/surveys-help`
* GET Survey Help page provided survey_ref and ru_ref and creates flash session for selection

`/help`
* GET Survey Help page provided survey_ref and ru_ref are in session
* POST Help to complete this survey option for respective survey

`/help/<option>`
* GET For help completing this survey's additional options (sub options)
* POST Provides additional options once sub options are selected

`/help/<option>/<sub_option>`
* GET Provides additional options with sub option provided

`/help/<option>/<sub_option>/send-message`
* GET Send message page once the option and sub option is selected
* POST Sends secure message for the help pages

## Frontstage endpoint calls

## Auth Controller Endpoints

`AUTH_URL/api/v1/tokens/`
* POST Checks if the users credentials are valid. On success it returns an empty dict.
* params `username`, `password`

`AUTH_URL/api/account/user`
* DELETE Delete a user when provided a username. 
* force_delete will always be true if deletion is initiated by user
* params `username`

## Banner Controller Endpoints

`BANNER_SERVICE_URL/banner`
* GET The currently active banner.

## Case Controller Endpoints

`CASE_URL/cases/{case_id}`
* GET a case by case id.
* params `case_id`

`CASE_URL/cases/iac/{enrolment_code}`
* GET a case by enrolment code.
* params `enrolment_code`

`CASE_URL/categories`
* GET case categories.

`CASE_URL/cases/partyid/{party_id}`
* GET cases by party id.
* params `party_id`, `case_url`, `case_auth`, `case_events=False`, `iac=True`

`CASE_URL/cases/{case_id}/events`
* POST case events.
* params `case_id`, `party_id`, `category`, `description`

## Collection Exercise Controller Endpoints

`COLLECTION_EXERCISE_URL/collectionexercises/{collection_exercise_id}`
* GET collection exercise.
* params `collection_exercise_id`

`COLLECTION_EXERCISE_URL/collectionexercises/{collection_exercise_id}/events`
* GET collection exercise events.
* params `collection_exercise_id`

`COLLECTION_EXERCISE_URL/collectionexercises/survey/{survey_id}`
* GET collection exercises for survey.
* `?liveOnly=true` query param if live_only is True
* params `survey_id`, `collex_url`, `collex_auth`, `live_only=None`

## Collection Instrument Controller Endpoints

`COLLECTION_INSTRUMENT_URL/collection-instrument-api/1.0.2/download/{collection_instrument_id}`
* GET Downloads the collection instrument and updates the case with the record that the instrument has been downloaded
* params `collection_instrument_id`, `case_id`, `party_id`

`COLLECTION_INSTRUMENT_URL/collection-instrument-api/1.0.2/{collection_instrument_id}`
* GET collection instrument
* params `collection_instrument_id`, `collection_instrument_url`, `collection_instrument_auth`

`COLLECTION_INSTRUMENT_URL/survey_response-api/v1/survey_responses/{case_id}`
* POST upload collection instrument
* params `upload_file`, `case_id`, `party_id`

## Conversation Controller Endpoints

`SECURE_MESSAGE_URL/threads/{thread_id}`
* GET conversations
* params `thread_id`

`SECURE_MESSAGE_URL/threads`
* GET conversation list
* params `params`

`SECURE_MESSAGE_URL/threads`
* POST send message
* params `message_json`

`SECURE_MESSAGE_URL/messages/count`
* GET message count from api
* params `session`

`SECURE_MESSAGE_URL/messages/modify/{message_id}`
* GET message count from api
* params `message_id`

## IAC Controller Endpoints

`IAC_URL/iacs/{enrolment_code}`
* GET retrieves enrolment details from IAC service for a given enrolment code
* params `enrolment_code`

## Notify Controller Endpoints

* Send message to gov.uk notify wrapper

## Party Controller Endpoints

`PARTY_URL/party-api/v1/respondents/id/{party_id}`
* GET respondents via party id 
* params `party_id`

`PARTY_URL/party-api/v1/respondents/add_survey`
* POST add survey
* params `party_id`, `enrolment_code`

`PARTY_URL/party-api/v1/respondents/change_password`
* POST change password
* params `email`, `password`

`PARTY_URL/party-api/v1/respondents`
* POST create account
* params `registration_data`

`PARTY_URL/party-api/v1/respondents/id/{respondent_data['id']}`
* PUT update account
* params `respondent_data`

`PARTY_URL/party-api/v1/businesses/id/{party_id}`
* PUT get party via business id
* params `party_id`, `party_url`, `party_auth`, `collection_exercise_id=None`, `verbose=True`

`PARTY_URL/party-api/v1/respondents/email`
* GET respondent via email
* params `email`

`PARTY_URL/party-api/v1/resend-verification-email/{party_id}`
* POST resend email verification
* params `party_id`

`PARTY_URL/party-api/v1/resend-verification-email-expired-token/{token}`
* POST resend email verification expired token
* params `token`

`PARTY_URL/party-api/v1/resend-account-email-change-expired-token/{token}`
* POST resend account email change expired token
* params `token`

`PARTY_URL/party-api/v1/respondents/request_password_change`
* POST reset password request
* params `username`

`PARTY_URL/party-api/v1/resend-password-email-expired-token/{token}`
* POST resend password email expired token
* params `token`

`PARTY_URL/party-api/v1/emailverification/{token}`
* PUT verify email
* params `token`

`PARTY_URL/party-api/v1/tokens/verify/{token}`
* GET verify token
* params `token`

`PARTY_URL/party-api/v1/pending-survey/verification/{token}`
* GET gives call to party service to verify share/transfer survey token
* params `token`

`PARTY_URL/party-api/v1/pending-survey/confirm-pending-surveys/{batch_number}`
* POST gives call to party service to confirm pending share/transfer survey
* params `batch_number`

`PARTY_URL/party-api/v1/respondents/edit-account-status/{respondent_id}`
* PUT notify respondent and party service that account is locked
* params `respondent_id`, `email_address`, `status=None`

`PARTY_URL/party-api/v1/businesses`
* GET retrieves the business details for all the business_id's that are provided
* params `business_ids`

`PARTY_URL/party-api/v1/pending-survey-users-count`
* GET returns total number of users registered against a business and survey
* params `business_id`, `survey_id`, `is_transfer`

`PARTY_URL/party-api/v1/pending-survey-users-count`
* POST register new entries to party for pending shares
* params `payload`

`PARTY_URL/party-api/v1/pending-survey-users-count`
* GET retrieves batch number for the shared survey
* params `batch_no`

`PARTY_URL/party-api/v1/pending-survey-respondent`
* GET Gives call to party service to create a new account and register the account against the email address of share
  surveys/ transfer surveys
* params `registration_data`

`PARTY_URL/party-api/v1/businesses/ref/{ru_ref}`
* GET Gives call to party service to retrieve a business using a ru_ref parameter
  surveys/ transfer surveys
* params `ru_ref`

## Survey Controller Endpoints

`SURVEY_URL/surveys/{survey_id}`
* GET retrieves a survey by survey id
* params `survey_url`, `survey_auth`, `survey_id`

`SURVEY_URL/surveys/shortname/{survey_short_name}`
* GET retrieves a survey by short name
* params `survey_short_name`

`SURVEY_URL/surveys/ref/{survey_ref}`
* GET retrieves a survey by survey ref
* params `survey_ref`