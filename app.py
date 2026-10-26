from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from azure.storage.filedatalake import DataLakeServiceClient

from models import ProfileRequest
from profiler import profile_dataframe
from validator import validate

import pandas as pd
import io
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

ACCOUNT_NAME = "mstorageaccount213"

service_client = DataLakeServiceClient(
    account_url=f"https://{ACCOUNT_NAME}.dfs.core.windows.net",
    credential=DefaultAzureCredential()
)

@app.get("/debug")
def debug():
    return {
        "account": ACCOUNT_NAME
    }

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/profile")
async def profile(request: ProfileRequest):

    print("=" * 80)
    print("PROFILE REQUEST")
    print(json.dumps(request.model_dump(), indent=2))
    print("=" * 80)

    try:

        dataset = request.dataset

        bronze_fs = service_client.get_file_system_client(
            "bronze"
        )

        paths = list(bronze_fs.get_paths(path=dataset))

        csv_file = next(
            (
                p.name
                for p in paths
                if p.name.lower().endswith(".csv")
            ),
            None
        )

        if not csv_file:
            return {
                "success": False,
                "error": f"No CSV found for dataset '{dataset}'"
            }

        print(f"Reading {csv_file}")

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

        generated_rules = (
            request.rules.get(
                "generated_rules",
                []
            )
        )

        profile_result = profile_dataframe(
            df,
            [
                "row_count",
                "column_count",
                "null_percentages",
                "distinct_counts"
            ]
        )

        validation_result = validate(
            df,
            generated_rules
        )

        result = {
            "success": True,
            "dataset": dataset,
            "rows": len(df),
            "columns": len(df.columns),
            "profile": profile_result,
            "validation": validation_result
        }

        silver_fs = (
            service_client
            .get_file_system_client("silver")
        )

        output_path = (
            f"{dataset}/"
            f"profile_results.json"
        )

        output_file = (
            silver_fs
            .get_file_client(output_path)
        )

        output_file.upload_data(
            json.dumps(result, indent=2),
            overwrite=True
        )

        print(f"Wrote {output_path}")

        return result

    except Exception as ex:

        print(str(ex))

        return {
            "success": False,
            "error": str(ex)
        }

@app.get("/debug-storage")
def debug_storage():

    fs = service_client.get_file_system_client("bronze")

    paths = [p.name for p in fs.get_paths()]

    return {
        "count": len(paths)
    }