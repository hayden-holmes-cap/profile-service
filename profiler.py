import pandas as pd


def profile_dataframe(df, dimensions):

    results = {}

    if "row_count" in dimensions:
        results["row_count"] = int(len(df))

    if "column_count" in dimensions:
        results["column_count"] = int(len(df.columns))

    if "completeness" in dimensions:

        completeness = {}

        for col in df.columns:

            completeness[col] = round(
                (1 - df[col].isnull().mean()) * 100,
                2
            )

        results["completeness"] = completeness

    if "uniqueness" in dimensions:

        uniqueness = {}

        for col in df.columns:

            uniqueness[col] = round(
                (
                    df[col].nunique() /
                    len(df)
                ) * 100,
                2
            )

        results["uniqueness"] = uniqueness

    return results