import hashlib
import json
import logging
import time
import uuid

import structlog
from flask import current_app
from google.cloud import pubsub_v1, storage
from google.cloud.exceptions import GoogleCloudError

from application.controllers.gnu_encryptor import GNUEncrypter
from application.controllers.helper import (
    is_valid_file_extension,
    is_valid_file_name_length,
)
from application.controllers.service_helper import (
    get_business_party,
    get_case_group,
    get_collection_exercise,
    get_survey_ref,
)

log = structlog.wrap_logger(logging.getLogger(__name__))

FILE_EXTENSION_ERROR = "The spreadsheet must be in .xls or .xlsx format"
FILE_NAME_LENGTH_ERROR = "The file name of your spreadsheet must be less than 50 characters long"


class FileTooSmallError(Exception):
    pass


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

    def add_survey_response(self, case_id: str, file_contents, file_name: str, survey_ref: str):
        """
        Encrypt and upload survey response to gcp bucket, and put metadata about it in pubsub.

        :param case_id: A case id
        :param file_contents: The contents of the file that has been uploaded
        :param file_name: The filename
        :param survey_ref: The survey ref e.g 134 MWSS
        """

        file_name = file_name + ".gpg"
        tx_id = str(uuid.uuid4())
        bound_log = log.bind(filename=file_name, case_id=case_id, survey_id=survey_ref, tx_id=tx_id)
        bound_log.info("Putting response into bucket and sending pubsub message")
        file_size = len(file_contents)

        if self.check_if_file_size_too_small(file_size):
            bound_log.info("File size is too small")
            raise FileTooSmallError()
        else:
            try:
                results = self.put_file_into_gcp_bucket(file_contents, file_name)
            except (GoogleCloudError, KeyError):
                bound_log.exception("Something went wrong putting into the bucket")
                raise SurveyResponseError()

            try:
                payload = self.create_pubsub_payload(
                    case_id, results["md5sum"], results["fileSizeInBytes"], file_name, tx_id
                )
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

    def put_file_into_gcp_bucket(self, file_contents, filename: str):
        """
        Takes the file_contents  and puts it into a GCP bucket in encrypted form to be later used by SDX.

        Note: The payload will almost certainly change once the encryption method between us and SDX is decided.

        :param file_contents: contents of the collection instrument
        :param filename that was uploaded

        returns a dict os the size of the encrypted string and an md5
        """
        bound_log = log.bind(project=self.seft_upload_project, bucket=self.seft_upload_bucket_name)
        bound_log.info("Starting to put file in bucket")
        try:
            if not filename.strip():
                raise ValueError("Error with filename for bucket ")
        except ValueError as e:
            bound_log.info(e, filename=filename)
            raise

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
        sizeInBytes = len(encrypted_message)
        blob.upload_from_string(encrypted_message)
        bound_log.info("Successfully put file in bucket", filename=filename)
        results = {"md5sum": md5sum, "fileSizeInBytes": sizeInBytes}

        return results

    def put_message_into_pubsub(self, payload: dict, tx_id: str):
        """
        Takes some metadata about the collection instrument and puts a message on pubsub for SDX to consume.

        :param tx_id: An id used by SDX to identify the transaction
        :param payload: The payload to be put onto the pubsub topic
        """
        if self.publisher is None:
            self.publisher = pubsub_v1.PublisherClient()

        topic_path = self.publisher.topic_path(
            self.seft_upload_project, self.seft_upload_pubsub_topic
        )  # NOQA pylint:disable=no-member
        payload_bytes = json.dumps(payload).encode()
        log.info("About to publish to pubsub", topic_path=topic_path)
        future = self.publisher.publish(topic_path, data=payload_bytes, tx_id=tx_id)
        message = future.result(timeout=15)
        log.info("Publish succeeded", msg_id=message)

    def create_pubsub_payload(self, case_id, md5sum, size_bytes, file_name, tx_id: str) -> dict:
        log.info("Creating pubsub payload", case_id=case_id)

        case_group = get_case_group(case_id)
        if not case_group:
            raise SurveyResponseError("Case group not found")

        collection_exercise_id = case_group.get("collectionExerciseId")
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            raise SurveyResponseError("Collection exercise not found")

        exercise_ref = collection_exercise.get("exerciseRef")
        survey_id = collection_exercise.get("surveyId")
        survey_ref = get_survey_ref(survey_id)
        if not survey_ref:
            raise SurveyResponseError("Survey ref not found")

        ru = case_group.get("sampleUnitRef")
        exercise_ref = self._format_exercise_ref(exercise_ref)

        business_party = get_business_party(
            case_group["partyId"], collection_exercise_id=collection_exercise_id, verbose=True
        )
        if not business_party:
            raise SurveyResponseError("Business not found in party")

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

    def get_file_name_and_survey_ref(self, case_id, file_extension):
        """
        Generate the file name for the upload, if an external service can't find the relevant information
        a None is returned instead.

        .. note:: returns two seemingly disparate values because the survey_ref is needed for filename anyway,
            and resolving requires calls to http services, doing it in one function minimises network traffic.
            survey_id as returned by collection exercise is a uuid, this is resolved by a call to
            survey which returns it as surveyRef which is the 3 digit id that other services refer to as survey_id

        :param case_id: The case id of the upload
        :param file_extension: The upload file extension
        :return: file name and survey_ref or None
        """

        log.info("Generating file name", case_id=case_id)

        case_group = get_case_group(case_id)
        if not case_group:
            return None, None

        collection_exercise_id = case_group.get("collectionExerciseId")
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            return None, None

        exercise_ref = collection_exercise.get("exerciseRef")
        survey_id = collection_exercise.get("surveyId")
        survey_ref = get_survey_ref(survey_id)
        if not survey_ref:
            return None, None

        ru = case_group.get("sampleUnitRef")
        exercise_ref = self._format_exercise_ref(exercise_ref)

        business_party = get_business_party(
            case_group["partyId"], collection_exercise_id=collection_exercise_id, verbose=True
        )
        if not business_party:
            return None, None
        check_letter = business_party["checkletter"]

        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = "{ru}{check_letter}_{exercise_ref}_{survey_ref}_{time_date_stamp}{file_format}".format(
            ru=ru,
            check_letter=check_letter,
            exercise_ref=exercise_ref,
            survey_ref=survey_ref,
            time_date_stamp=time_date_stamp,
            file_format=file_extension,
        )

        log.info("Generated file name for upload", filename=file_name)

        return file_name, survey_ref

    @staticmethod
    def is_valid_file(file_name, file_extension):
        """
        Check a file is valid

        :param file_name: The file_name to check
        :param file_extension: The file extension
        :return: (boolean, String)
        """

        log.info("Checking if file is valid")
        if not is_valid_file_extension(file_extension, current_app.config.get("UPLOAD_FILE_EXTENSIONS")):
            log.info("File extension not valid", file_extension=file_extension)
            return False, FILE_EXTENSION_ERROR

        if not is_valid_file_name_length(file_name, current_app.config.get("MAX_UPLOAD_FILE_NAME_LENGTH")):
            log.info("File name too long", file_name=file_name)
            return False, FILE_NAME_LENGTH_ERROR

        return True, ""

    @staticmethod
    def check_if_file_size_too_small(file_size) -> bool:
        return file_size < 1

    @staticmethod
    def _format_exercise_ref(exercise_ref: str) -> str:
        """
        There is currently data inconsistency in the code, exercise_ref should look like 201712 not '221_201712',
        this is a work around until the data is corrected

        :param exercise_ref: exercise reference
        :return: formatted exercise reference
        """
        try:
            return exercise_ref.split("_")[1]
        except IndexError:
            return exercise_ref
