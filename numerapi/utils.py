""" collection of utility functions"""

import os
import decimal
import logging
import time
import datetime
import uuid
import json

import dateutil.parser
import requests
import tqdm

logger = logging.getLogger(__name__)

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def load_secrets() -> tuple:
    """load secrets from environment variables or dotenv file"""

    try:
        from dotenv import load_dotenv # pylint: disable-msg=import-outside-toplevel
        load_dotenv()
    except ImportError:
        pass

    public_id = os.getenv("NUMERAI_PUBLIC_ID")
    secret_key = os.getenv("NUMERAI_SECRET_KEY")

    return public_id, secret_key


def parse_datetime_string(string: str) -> datetime.datetime | None:
    """try to parse string to datetime object"""
    if string is None:
        return None
    return dateutil.parser.parse(string)


def parse_float_string(string: str) -> decimal.Decimal | None:
    """try to parse string to decimal.Decimal object"""
    if string is None:
        return None
    try:
        val = decimal.Decimal(string.replace(",", ""))
    except decimal.InvalidOperation:
        val = None
    return val


def replace(dictionary: dict, key: str, function):
    """apply a function to dict item"""
    if dictionary is not None and key in dictionary:
        dictionary[key] = function(dictionary[key])


def download_file(url: str, dest_path: str, show_progress_bars: bool = True):
    """downloads a file and shows a progress bar. allow resuming a download"""
    file_size = 0
    req = requests.get(url, stream=True, timeout=600)
    req.raise_for_status()

    # Total size in bytes.
    total_size = int(req.headers.get('content-length', 0))
    temp_path = dest_path + ".temp"

    if os.path.exists(dest_path):
        logger.info("target file already exists")
        file_size = os.stat(dest_path).st_size  # File size in bytes
        if file_size == total_size:
            # Download complete
            logger.info("download complete")
            return dest_path

    if os.path.exists(temp_path):
        file_size = os.stat(temp_path).st_size  # File size in bytes

        if file_size < total_size:
            # Download incomplete
            logger.info("resuming download")
            resume_header = {'Range': f'bytes={file_size}-'}
            req = requests.get(url, headers=resume_header, stream=True,
                               verify=False, allow_redirects=True, timeout=600)
        else:
            # Error, delete file and restart download
            logger.error("deleting file and restarting")
            os.remove(temp_path)
            file_size = 0
    else:
        # File does not exist, starting download
        logger.info("starting download")

    # write dataset to file and show progress bar
    pbar = tqdm.tqdm(total=total_size, unit='B', unit_scale=True,
                     desc=dest_path, disable=not show_progress_bars)
    # Update progress bar to reflect how much of the file is already downloaded
    pbar.update(file_size)
    with open(temp_path, "ab") as dest_file:
        for chunk in req.iter_content(DOWNLOAD_CHUNK_SIZE):
            dest_file.write(chunk)
            pbar.update(len(chunk))
    # move temp file to target destination
    os.replace(temp_path, dest_path)
    return dest_path


def post_with_err_handling(url: str, body: dict, headers: dict,
                           *, timeout: int | None = None,
                           retries: int = 3, delay: int = 1, backoff: int = 2
                           ) -> dict:
    """send `post` request and handle (some) errors that might occur"""
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        while 500 <= resp.status_code < 600 and retries > 1:
            time.sleep(delay)
            delay *= backoff
            retries -= 1
            resp = requests.post(url, json=body,
                                 headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.HTTPError as err:
        logger.error(f"Http Error: {err}")
    except requests.exceptions.ConnectionError as err:
        logger.error(f"Error Connecting: {err}")
    except requests.exceptions.Timeout as err:
        logger.error(f"Timeout Error: {err}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Oops, something went wrong: {err}")
    except json.decoder.JSONDecodeError as err:
        logger.error(f"Did not receive a valid JSON: {err}")

    return {}


def is_valid_uuid(val: str) -> bool:
    """ check if the given string is a valid UUID """
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False
