print("PROFILE SERVICE STARTING")

import io
import json
import os
import traceback

import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from models import ProfileRequest
from profiler import profile_dataframe
from validator import validate


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Storage
# --------------------------------------------------

ACCOUNT_NAME = "mstorageaccount213"

if not ACCOUNT_NAME:
    raise Exception(
        "STORAGE_ACCOUNT environment variable is missing"
    )

service_client = DataLakeServiceClient(
    account_url=f"https://{ACCOUNT_NAME}.dfs.core.windows.net",
    credential=DefaultAzureCredential()
)

print(f"Connected to storage account: {ACCOUNT_NAME}")


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/debug")
def debug():
    return {
        "storage_account": ACCOUNT_NAME
    }


@app.get("/debug-storage")
def debug_storage():

    try:

        bronze_fs = service_client.get_file_system_client(
            "bronze"
        )

        paths = [
            p.name
            for p in bronze_fs.get_paths()
        ]

        return {
            "success": True,
            "count": len(paths),
            "paths": paths[:10]
        }

    except Exception as ex:

        traceback.print_exc()

        return {
            "success": False,
            "error": str(ex)
        }


# --------------------------------------------------
# Profile
# --------------------------------------------------

@app.post("/profile")
async def profile(request: ProfileRequest):

    try:

        print("=" * 80)
        print("PROFILE REQUEST")
        print(json.dumps(
            request.model_dump(),
            indent=2
        ))
        print("=" * 80)

        dataset = request.dataset

        # ------------------------------------------
        # Locate dataset file in bronze
        # ------------------------------------------

        bronze_fs = service_client.get_file_system_client(
            "bronze"
        )

        paths = list(
            bronze_fs.get_paths(
                path=dataset
            )
        )

        csv_file = next(
            (
                p.name
                for p in paths
                if p.name.lower().endswith(".csv")
            ),
            None
        )

        if csv_file is None:

            return {
                "success": False,
                "error": (
                    f"No CSV file found "
                    f"for dataset '{dataset}'"
                )
            }

        print(f"Reading file: {csv_file}")

        # ------------------------------------------
        # Read CSV
        # ------------------------------------------

        file_client = bronze_fs.get_file_client(
            csv_file
        )

        content = (
            file_client
            .download_file()
            .readall()
        )

        df = pd.read_csv(
            io.BytesIO(content)
        )

        print(
            f"Loaded dataframe with "
            f"{len(df)} rows and "
            f"{len(df.columns)} columns"
        )

        # ------------------------------------------
        # Rules
        # ------------------------------------------

        generated_rules = (
            request.rules.get(
                "generated_rules",
                []
            )
        )

        print(
            f"Executing "
            f"{len(generated_rules)} rules"
        )

        # ------------------------------------------
        # Profiling
        # ------------------------------------------

        profile_result = profile_dataframe(
            df,
            [
                "row_count",
                "column_count",
                "null_percentages",
                "distinct_counts"
            ]
        )

        # ------------------------------------------
        # Validation
        # ------------------------------------------

        validation_result = validate(
            df,
            generated_rules
        )

        result = {
            "success": True,
            "dataset": dataset,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "profile": profile_result,
            "validation": validation_result
        }

        # ------------------------------------------
        # Write results to silver
        # ------------------------------------------

        silver_fs = service_client.get_file_system_client(
            "silver"
        )

        try:
            silver_fs.create_directory(
                dataset
            )
        except Exception:
            pass

        output_path = (
            f"{dataset}/"
            f"profile_results.json"
        )

        print(
            f"Writing results to "
            f"{output_path}"
        )

        output_file = silver_fs.get_file_client(
            output_path
        )

        output_file.upload_data(
            json.dumps(
                result,
                indent=2,
                default=str
            ),
            overwrite=True
        )

        print(
            f"Successfully wrote "
            f"{output_path}"
        )

        return result

    except Exception as ex:

        traceback.print_exc()

        return {
            "success": False,
            "error": str(ex)
        }