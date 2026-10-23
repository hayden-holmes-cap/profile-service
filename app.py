print("PROFILE SERVICE STARTING")
from fastapi import FastAPI

from azure.storage.filedatalake import (
    DataLakeServiceClient
)

import pandas as pd
import io
import json

from models import ProfileRequest
from profiler import profile_dataframe
from validator import validate

app = FastAPI()

import os

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
ACCOUNT_NAME="mstorageaccount213"
try:
    credential = DefaultAzureCredential()
    print("CREDENTIAL CREATED")

    service_client = DataLakeServiceClient(
        account_url=f"https://{ACCOUNT_NAME}.dfs.core.windows.net",
        credential=credential
    )

    print("SERVICE CLIENT CREATED")

except Exception as e:
    print("STARTUP FAILED")
    print(str(e))
    raise


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/profile")
async def profile(
        request: ProfileRequest
):

    print("=" * 50)
    print("PROFILE REQUEST")

    bronze_fs = (
        service_client
        .get_file_system_client(
            request.zone
        )
    )

    target_path = (
        f"{request.dataset}/"
        f"{request.filename}"
    )

    print(
        f"Reading {target_path}"
    )

    file_client = (
        bronze_fs
        .get_file_client(
            target_path
        )
    )

    content = (
        file_client
        .download_file()
        .readall()
    )

    df = pd.read_csv(
        io.BytesIO(content)
    )

    profile_result = (
        profile_dataframe(
            df,
            request.profile_dimensions
        )
    )

    validation_result = (
        validate(
            df,
            request.validation_rules
        )
    )

    result = {

        "dataset": request.dataset,

        "filename": request.filename,

        "profile": profile_result,

        "validation": validation_result
    }

    silver_fs = (
        service_client
        .get_file_system_client(
            "silver"
        )
    )

    output_path = (
        f"{request.dataset}/"
        f"{request.filename}.profile.json"
    )

    silver_file = (
        silver_fs
        .get_file_client(
            output_path
        )
    )

    silver_file.upload_data(
        json.dumps(
            result,
            indent=2
        ),
        overwrite=True
    )

    print(
        f"Wrote {output_path}"
    )

    return result
