Front Stage Server
============================

Author: Andrew Millar
Version: 0.2.0

Changes For ras-front-stage Server
============================================

* Updated logging content and format
* Fixed HTTP redirect errors
* survey_id and ru_id no longer hardcoded for secure messages
* Improved error handling from external services
* Fixed bug where draft was still saved after sending


Known Issues For Front Stage Server
============================================
* Sign in with 10 bad passwords does not show you a different error message
* HTTP 500 errors are displayed on the screen when coming from other micro services
* Error when logging in with unverified user
