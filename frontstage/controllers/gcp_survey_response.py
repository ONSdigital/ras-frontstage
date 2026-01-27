import hashlib
import json
import logging
import time
import uuid

import structlog
from flask import current_app
from google.cloud import pubsub_v1, storage
from google.cloud.exceptions import GoogleCloudError

from frontstage.controllers.collection_exercise_controller import (
    get_collection_exercise,
)
from frontstage.controllers.gnu_encryptor import GNUEncrypter
from frontstage.controllers.survey_controller import get_survey

log = structlog.wrap_logger(logging.getLogger(__name__))

FILE_EXTENSION_ERROR = "The spreadsheet must be in .xls or .xlsx format."
FILE_NAME_LENGTH_ERROR = "The file name of your spreadsheet must be less than 50 characters long."
UPLOAD_FILE_EXTENSIONS = "xls,xlsx"
MAX_FILE_SIZE_ERROR = "The file must be smaller than 20MB."
MIN_FILE_SIZE_ERROR = "The file must be larger than 6KB."


class SurveyResponseError(Exception):
    pass


class GcpSurveyResponse:
    def __init__(self, config):
        self.config = config

        # Bucket config
        self.storage_client = None
        self.seft_upload_bucket_name = self.config["SEFT_UPLOAD_BUCKET_NAME"]
        self.seft_upload_bucket_file_prefix = self.config.get("SEFT_UPLOAD_BUCKET_FILE_PREFIX")

        # Pubsub config
        self.publisher = None
        self.seft_upload_project = self.config["SEFT_UPLOAD_PROJECT"]
        self.seft_upload_pubsub_topic = self.config["SEFT_UPLOAD_PUBSUB_TOPIC"]

    """
    The survey response from a respondent
    """

    def upload_seft_survey_response(self, case: dict, file_contents, file_name: str, survey_ref: str):
        """
        Encrypt and upload survey response to gcp bucket, and put metadata about it in pubsub.

        :param case: A case
        :param file_contents: The contents of the file that has been uploaded
        :param file_name: The filename
        :param survey_ref: The survey ref e.g 134 MWSS
        """

        file_name = file_name + ".gpg"
        tx_id = str(uuid.uuid4())
        bound_log = log.bind(filename=file_name, case_id=case["id"], survey_id=survey_ref, tx_id=tx_id)
        bound_log.info("Putting response into bucket and sending pubsub message")

        try:
            results = self.put_file_into_gcp_bucket(file_contents, file_name)
        except (GoogleCloudError, KeyError):
            bound_log.exception("Something went wrong putting into the bucket")
            raise SurveyResponseError()

        try:
            payload = self.create_pubsub_payload(case, results["md5sum"], results["fileSizeInBytes"], file_name, tx_id)
        except SurveyResponseError:
            bound_log.error("Something went wrong creating the payload", exc_info=True)
            raise

        try:
            self.put_message_into_pubsub(payload, tx_id)
        except TimeoutError:
            bound_log.exception("Publish to pubsub timed out", payload=payload)
            raise SurveyResponseError()
        except Exception as e:  # noqa
            bound_log.exception("A non-timeout error was raised when publishing to pubsub", payload=payload)

            raise SurveyResponseError()

        bound_log.unbind("filename", "case_id", "survey_id", "tx_id")

    def put_file_into_gcp_bucket(self, file_contents, filename: str):
        """
        Takes the file_contents and puts it into a GCP bucket in encrypted form to be later used by SDX.

        Note: The payload will almost certainly change once the encryption method between us and SDX is decided.

        :param file_contents: contents of the collection instrument
        :param filename that was uploaded

        returns a dict os the size of the encrypted string and an md5
        """
        bound_log = log.bind(project=self.seft_upload_project, bucket=self.seft_upload_bucket_name)
        bound_log.info("Starting to put file in bucket")

        if not filename.strip():
            bound_log.info("Error with filename for bucket", filename=filename)
            raise ValueError("Error with filename for bucket")

        if self.storage_client is None:
            self.storage_client = storage.Client(project=self.seft_upload_project)

        bucket = self.storage_client.bucket(self.seft_upload_bucket_name)
        if self.seft_upload_bucket_file_prefix:
            filename = f"{self.seft_upload_bucket_file_prefix}/{filename}"
        blob = bucket.blob(filename)
        gnugpg_secret_keys = current_app.config["ONS_GNU_PUBLIC_CRYPTOKEY"]
        ons_gnu_fingerprint = current_app.config["ONS_GNU_FINGERPRINT"]
        encrypter = GNUEncrypter(gnugpg_secret_keys)
        encrypted_message = encrypter.encrypt(file_contents, ons_gnu_fingerprint)
        md5sum = hashlib.md5(str(encrypted_message).encode()).hexdigest()
        size_in_bytes = len(encrypted_message)
        blob.upload_from_string(encrypted_message)
        bound_log.info("Successfully put file in bucket", filename=filename)
        bound_log.unbind("project", "bucket")

        results = {"md5sum": md5sum, "fileSizeInBytes": size_in_bytes}
        return results

    def put_message_into_pubsub(self, payload: dict, tx_id: str):
        """
        Takes some metadata about the collection instrument and puts a message on pubsub for SDX to consume.

        :param tx_id: An id used by SDX to identify the transaction
        :param payload: The payload to be put onto the pubsub topic
        """
        if self.publisher is None:
            self.publisher = pubsub_v1.PublisherClient()

        topic_path = self.publisher.topic_path(self.seft_upload_project, self.seft_upload_pubsub_topic)
        payload_bytes = json.dumps(payload).encode()
        log.info("About to publish to pubsub", topic_path=topic_path)
        future = self.publisher.publish(topic_path, data=payload_bytes, tx_id=tx_id)
        message = future.result(timeout=15)
        log.info("Publish succeeded", msg_id=message)

    def create_pubsub_payload(self, case, md5sum, size_bytes, file_name, tx_id: str) -> dict:
        log.info("Creating pubsub payload", case_id=case["id"])

        case_group = case.get("caseGroup")
        if not case_group:
            raise SurveyResponseError("Case group not found")

        collection_exercise_id = case_group.get("collectionExerciseId")
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            raise SurveyResponseError("Collection exercise not found")

        exercise_ref = collection_exercise.get("exerciseRef")
        survey_id = collection_exercise.get("surveyId")
        survey = get_survey(current_app.config["SURVEY_URL"], current_app.config["BASIC_AUTH"], survey_id)
        survey_ref = survey.get("surveyRef")
        if not survey_ref:
            raise SurveyResponseError("Survey ref not found")

        ru = case_group.get("sampleUnitRef")
        exercise_ref = self._format_exercise_ref(exercise_ref)

        payload = {
            "filename": file_name,
            "tx_id": tx_id,
            "survey_id": survey_ref,
            "period": exercise_ref,
            "ru_ref": ru,
            "md5sum": md5sum,
            "sizeBytes": size_bytes,
        }
        log.info("Payload created", payload=payload)

        return payload

    def create_file_name_for_upload(
        self, case: dict, business_party: dict, file_extension: str, survey_ref: str
    ) -> str | None:
        """
        Generate the file name for the upload, if an external service can't find the relevant information
        a None is returned instead.

        .. note:: returns two seemingly disparate values because the survey_ref is needed for filename anyway,
            and resolving requires calls to http services, doing it in one function minimises network traffic.
            survey_id as returned by collection exercise is a uuid, this is resolved by a call to
            survey which returns it as surveyRef which is the 3 digit id that other services refer to as survey_id

        :param case: The case
        :param business_party: A dict representing the business
        :param file_extension: The upload file extension
        :param survey_ref
        :return: The file name or None
        """
        log.info("Generating file name", case_id=case["id"])
        if not business_party:
            return None

        case_group = case.get("caseGroup")
        if not case_group:
            return None

        collection_exercise_id = case_group.get("collectionExerciseId")
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            return None

        ru = case_group.get("sampleUnitRef")
        check_letter = business_party["checkletter"]
        exercise_ref = collection_exercise.get("exerciseRef")
        exercise_ref = self._format_exercise_ref(exercise_ref)
        time_date_stamp = time.strftime("%Y%m%d%H%M%S")

        file_name = f"{ru}{check_letter}_{exercise_ref}_{survey_ref}_{time_date_stamp}{file_extension}"
        log.info("Generated file name for upload", filename=file_name)

        return file_name

    def validate_file(self, file_name: str, file_extension: str, file_size: int) -> list:
        """
        Check a file is valid
        :param file_name: The file_name to check
        :param file_extension: The file extension
        :param file_size: The size of the file in bytes
        :return: list of validation_errors
        """

        validation_errors = []

        if not self.is_valid_file_extension(file_extension, UPLOAD_FILE_EXTENSIONS):
            validation_errors.append(FILE_EXTENSION_ERROR)

        if len(file_name) > current_app.config["MAX_UPLOAD_FILE_NAME_LENGTH"]:
            validation_errors.append(FILE_NAME_LENGTH_ERROR)

        if file_size > current_app.config["MAX_UPLOAD_LENGTH"]:
            validation_errors.append(MAX_FILE_SIZE_ERROR)

        if file_size < current_app.config["MIN_UPLOAD_LENGTH"]:
            validation_errors.append(MIN_FILE_SIZE_ERROR)

        return validation_errors

    @staticmethod
    def _format_exercise_ref(exercise_ref: str) -> str:
        """
        There is currently data inconsistency in the code, exercise_ref should look like 201712 not '221_201712',
        this is a workaround until the data is corrected

        :param exercise_ref: exercise reference
        :return: formatted exercise reference
        """
        try:
            return exercise_ref.split("_")[1]
        except IndexError:
            return exercise_ref

    @staticmethod
    def is_valid_file_extension(file_name, extensions):
        """
        Check the file format is valid

        :param file_name: The file name to be checked
        :param extensions: The list of extensions that are valid
        :return: boolean
        """
        return file_name.endswith(tuple(ext.strip() for ext in extensions.split(",")))
