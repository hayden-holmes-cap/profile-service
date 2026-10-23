def validate(df, rules):

    output = []

    for rule in rules:

        if rule.rule == "not_null":

            actual = (
                1 -
                df[rule.column].isnull().mean()
            )

            output.append({
                "column": rule.column,
                "rule": rule.rule,
                "actual": round(actual, 4),
                "threshold": rule.threshold,
                "passed": bool(actual >= rule.threshold)
            })

        elif rule.rule == "regex":

            matches = (
                df[rule.column]
                .astype(str)
                .str.match(rule.regex)
            )

            actual = matches.mean()

            output.append({
                "column": rule.column,
                "rule": rule.rule,
                "actual": round(actual, 4),
                "threshold": rule.threshold,
                "passed": bool(actual >= rule.threshold)
            })

    return output