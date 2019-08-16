# ras frontstage routes

This page documents the ras frontstage routes that can be hit.

## Passwords endpoints

To reset a password
`passwords/reset-password/<token>`
* POST request to this endpoint allows you to reset your password
* GET request to this endpoint allows you to get the password reset form
* `token` is used to be able to access the reset page

`passwords/reset-password/confirmation`
* GET request to this endpoint renders confirmation page that password's been changed.

`passwords/resend-password-email-expired-token/<token>`
* GET request to this endpoint is used to resend an e-mail to a user if their token has expired.

`passwords/forgot-password`
* GET request to this endpoint will return the forgot password page.
* POST request to this endpoint will send a reset password request to the party service.

`passwords/forgot-password/check-email`
* GET request to this endpoint is used to render the check e-mail template for forgot-password.

---

## Register endpoints

`register/activate-account/<token>`
* GET request to this endpoint is used to verify the e-mail address for the respondent.

`register/create-account/confirm-organisation-survey`
* GET request to this endpoint is used to confirm the organisation and survey details that the respondent is enrolling for.

`register/create-account`
* GET request to this endpoint will render a page to enter an enrolment code.
* POST request to this endpoint will validate the enrolment code used and display organisation and survey details.

`register/create-account/enter-account-details`
* GET request to this endpoint will display a form to enter in account details.
* POST request to this endpoint will attempt to create an account for this respondent.

`register/create-account/check-your-email`
* GET request to this endpoint will render a page that will tell the user to verify their account via e-mail.

`register/create-account/check-email`
* GET request to this endpoint will display to the user that they've almost created their account.

---

## Secure messaging endpoints

`secure-message/create-message`
* GET request to this endpoint will display a form for the user to send a message.
* POST request to this endpoint will send a message.

`secure-message/thread/<thread-id>`
* GET request to this endpoint will display a conversation to the user using the `thread-id`.
* POST request to this endpoint will send a message from the conversation view.
* The `thread-id` is the ID of the conversation between the respondent and the internal user.

`secure-message/threads`
* GET request to this endpoint will display the list of conversations that the user currently has.

---

## Sign-in endpoints

`sign-in`
* GET request to this endpoint will return the log-in page for ras-frontstage.
* POST request to this endpoint will log-in the user to be to see their survey list.

`sign-in/resend_verification/<party_id>`
* GET request to this endpoint will resend a verification e-mail to the respondent.
* `party_id` is the ID of the respondent.

`sign-in/resend-verification-expired-token/<token>`
* GET request to this endpoint will resend a verification e-mail if the verification token has expired.

`sign-in/logout`
* GET request to this endpoint will sign-out the user from their session.

---

## Surveys endpoints

`surveys/access_survey`
* GET request to this endpoint will allow the respondent to upload and download a survey.

`surveys/add-survey`
* POST request to this endpoint will allow the respondent to add another survey to their account.

`surveys/add-survey/confirm-organisation-survey`
* GET request to this endpoint will display to the user the survey they are adding to their account.

`surveys/add-survey/add-survey-submit`
* GET request to this endpoint will assign the new survey to the respondent.

`surveys/download_survey`
* GET request to this endpoint will download a survey that the respondent will need to complete.

`surveys/upload_survey`
* POST request to this endpoint will upload a collection instrument to the collection instrument service.

`surveys/upload_failed`
* GET request to this endpoint will render an error page if it fails to upload the collection instrument.

`surveys/<tag>`
* GET request to this endpoint will display to the respondent the surveys that they need to complete.
* `tag` can be either to-do or history.

---

## Contact us endpoints

`/contact-us`
* GET request to this endpoint will display contact details for the ONS.

---

## Cookies privacy endpoints

`/cookies-privacy`
* GET request to this endpoint will display cookies and privacy details that ONS collects on frontstage.

---

## Info endpoint

`/info`
* GET request to this endpoint displays the current version of ras-frontstage.