import re
import pandas as pd


def validate(df: pd.DataFrame, validation_rules: list):

    results = []

    for rule in validation_rules:

        column = rule.get("column")
        rule_type = rule.get("rule")

        if column not in df.columns:
            results.append({
                "column": column,
                "rule": rule_type,
                "status": "failed",
                "message": f"Column '{column}' not found"
            })
            continue

        try:

            # -------------------------
            # Uniqueness
            # -------------------------

            if rule_type == "uniqueness":

                duplicate_count = (
                    df[column]
                    .duplicated()
                    .sum()
                )

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if duplicate_count == 0
                    else "failed",
                    "duplicate_count": int(duplicate_count)
                })

            # -------------------------
            # Completeness
            # -------------------------

            elif rule_type == "completeness":

                null_count = int(
                    df[column]
                    .isna()
                    .sum()
                )

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if null_count == 0
                    else "failed",
                    "null_count": null_count
                })

            # -------------------------
            # Allowed Values
            # -------------------------

            elif rule_type == "allowed_values":

                allowed_values = rule.get(
                    "values",
                    []
                )

                invalid = df[
                    ~df[column]
                    .isin(allowed_values)
                ]

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if len(invalid) == 0
                    else "failed",
                    "invalid_count": len(invalid),
                    "allowed_values": allowed_values
                })

            # -------------------------
            # Regex
            # -------------------------

            elif rule_type == "regex":

                pattern = rule.get(
                    "pattern",
                    ""
                )

                invalid_count = 0

                for value in (
                    df[column]
                    .dropna()
                    .astype(str)
                ):

                    if not re.match(
                        pattern,
                        value
                    ):
                        invalid_count += 1

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if invalid_count == 0
                    else "failed",
                    "invalid_count": invalid_count,
                    "pattern": pattern
                })

            # -------------------------
            # Range
            # -------------------------

            elif rule_type == "range":

                min_value = rule.get("min")
                max_value = rule.get("max")

                invalid = df[
                    (df[column] < min_value)
                    | (df[column] > max_value)
                ]

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if len(invalid) == 0
                    else "failed",
                    "invalid_count": len(invalid),
                    "min": min_value,
                    "max": max_value
                })

            # -------------------------
            # Datatype
            # -------------------------

            elif rule_type == "datatype":

                expected = rule.get(
                    "datatype"
                )

                actual = str(
                    df[column].dtype
                )

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "passed"
                    if expected == actual
                    else "failed",
                    "expected": expected,
                    "actual": actual
                })

            # -------------------------
            # Unsupported
            # -------------------------

            else:

                results.append({
                    "column": column,
                    "rule": rule_type,
                    "status": "skipped",
                    "message":
                        f"Unsupported rule '{rule_type}'"
                })

        except Exception as ex:

            results.append({
                "column": column,
                "rule": rule_type,
                "status": "error",
                "message": str(ex)
            })

    return results