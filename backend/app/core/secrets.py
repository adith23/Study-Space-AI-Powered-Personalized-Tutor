"""
Load secrets from AWS SSM Parameter Store into environment variables.

Called once during Lambda cold start. On subsequent warm invocations,
the _SSM_LOADED flag prevents redundant fetches.

In development (ENVIRONMENT != "production"), this is a no-op.
"""
import os
import logging

logger = logging.getLogger(__name__)


def load_ssm_secrets(prefix: str = "/study-space/production/"):
    """
    Fetch all parameters under the given prefix from SSM
    and inject them as environment variables.

    Only runs when ENVIRONMENT == "production".
    Skips if already loaded (_SSM_LOADED flag).
    """
    if os.getenv("ENVIRONMENT") != "production":
        return

    if os.getenv("_SSM_LOADED"):
        return  # Already loaded on a previous warm invocation

    try:
        import boto3

        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
        loaded_count = 0

        paginator = ssm.get_paginator("get_parameters_by_path")
        for page in paginator.paginate(
            Path=prefix,
            WithDecryption=True,
            Recursive=False,
        ):
            for param in page["Parameters"]:
                # /study-space/production/DATABASE_URL → DATABASE_URL
                key = param["Name"].rsplit("/", 1)[-1]
                os.environ[key] = param["Value"]
                loaded_count += 1

        os.environ["_SSM_LOADED"] = "true"
        logger.info("Loaded %d secrets from SSM prefix: %s", loaded_count, prefix)

    except Exception as e:
        logger.error("Failed to load SSM secrets: %s", e)
        raise
