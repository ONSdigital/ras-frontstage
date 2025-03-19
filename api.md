# RAS Frontage UI routes

This page documents the Fronstage ui endpoints that can be hit.

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

## Surveys help Endpoints

`/surveys-help`
* GET Survey Help page provided survey_ref and ru_ref and creates flash session for selection

`/help`
* GET Survey Help page provided survey_ref and ru_ref are in session
* POST Help to complete this survey option for respective survey

`/help/<option>`
* GET For help completing this survey's additional options (sub options)
* POST Provides additional options once sub options are selected
* `options`

`/help/<option>/<sub_option>`
* GET Provides additional options with sub option provided
* `sub_options`

`/help/<option>/<sub_option>/send-message`
* GET Send message page once the option and sub option is selected
* POST Sends secure message for the help pages
* `options`
* `sub_option`

## Sign-in Endpoints

`/`
* GET and POST
* redirects to /sign-in

`/sign-in`
* Login page

`/resend-verification/<party_id>`
* GET Deprecated: to be removed when not in use
* `party_id`

`/resend-verification-expired-token/<token>`
* GET
* `token`

`/logout`
* logs the user out

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
* `token`

`/create-account/confirm-organisation-survey`
* GET

## Passwords Endpoints

`/forgot-password`
* GET and POST

`/forgot-password/check-email`
* GET

`/reset-password/<token>`
* GET and POST
* `token`

`/reset-password/confirmation`
* GET

`/reset-password/check-email`
* GET

`/resend-password-email-expired-token/<token>`
* GET
* `token`

## Account Endpoints
* requires login

`/account`
* GET and POST
* GET and POST `/change-password`
* GET and POST `/change-account-details`
* GET `/something-else` Gets the something else once the option is selected
* POST `/something-else` Sends secure message for the something else pages

`/delete`
* GET and POST

`/confirm-account-email-change/<token>`
* GET 
* `token`

`/resend-account-email-change-expired-token/<token>`
* GET
* `token`

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
* `token`

`/confirm-share-surveys/<batch>`
* GET Accept endpoint when a share survey summary is accepted
* `batch` is the batch number

`/confirm-share-surveys/<batch>/existing-account`
* GET Accept redirect endpoint for accepting share surveys for existing account

`/transfer-surveys/accept-transfer-surveys/<token>`
* GET Endpoint to verify transfer token and retrieve the summary page
* `token`

`/confirm-transfer-surveys/<batch>`
* GET Accept endpoint when a transfer survey summary is accepted
* `batch` is the batch number

`/confirm-transfer-surveys/<batch>/existing-account`
* GET Accept redirect endpoint for accepting transfer surveys for existing account
* `batch` is the batch number

## Secure Messaging Endpoints
* requires login

`/create-message/`
* GET and POST

`/threads/<thread_id>`
* GET and POST Endpoint to view conversations by thread_id
* `thread_id`

`/threads`
* GET

## Surveys Endpoints
* requires login

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