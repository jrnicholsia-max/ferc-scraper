from paths import input_path, output_path
from data_io import (format_date, load_dockets,
                       load_results, create_result_sheet, build_run_output_path)
from datetime import date
from importlib import import_module

API_DEFINITIONS = {
    "ferc": {
        "module": "api_modules.ferc_api",
        "input_sheet": "ferc",
    },
    "illinois": {
        "module": "api_modules.il_api",
        "input_sheet": "illinois",
    },
}

API_ALIASES = {
    "il": "illinois",
}

ALLOWED_APIS = {
    **{api_name: config["module"] for api_name, config in API_DEFINITIONS.items()},
    **{alias: API_DEFINITIONS[target]["module"] for alias, target in API_ALIASES.items()},
}


def get_api_config(api_key):
    normalized_api = str(api_key).strip().lower()
    canonical_api = API_ALIASES.get(normalized_api, normalized_api)
    if canonical_api not in API_DEFINITIONS:
        raise ValueError(f"Unsupported API: {api_key}")
    return API_DEFINITIONS[canonical_api]

def load_api(api_key):
    module_name = get_api_config(api_key)["module"]
    return import_module(module_name)

def main(api="ferc"):
    api_config = get_api_config(api)
    api_module = load_api(api)
    input_sheet = api_config["input_sheet"]
    run_output_path = build_run_output_path(api)
    print(
        f"Using INPUT_FILE={input_path}, TEMPLATE_OUTPUT_FILE={output_path}, "
        f"RUN_OUTPUT_FILE={run_output_path}, API={api}, INPUT_SHEET={input_sheet}"
    )

    try:
        workbook, docket_rows = load_dockets(input_sheet)
    except Exception as exc:
        print(f"Unable to load dockets from worksheet '{input_sheet}': {exc}")
        return

    if not docket_rows:
        print(f"No docket rows found in worksheet '{input_sheet}' in {input_path}.")
        return

    try:
        results_workbook = load_results()
    except Exception as exc:
        print(f"Unable to load results workbook: {exc}")
        return

    for entry in docket_rows:
        docket = entry["docket"]
        try:
            start_date = format_date(entry["start_date"])
        except ValueError as exc:
            print(f"Skipping {docket}: invalid start date ({exc}).")
            continue

        print(f"Processing docket {docket} starting {start_date}...")
        try:
            data = api_module.fetch_search_results(docket, start_date)
        except Exception as exc:
            print(f"Fetch failed for {docket}: {exc}")
            continue

        records = api_module.parse_search_hits(data)
        if records:
            create_result_sheet(results_workbook, docket, records)
            print(f"Wrote {len(records)} records to {run_output_path} sheet '{docket}'.")
        else:
            print(f"No records found for docket {docket}. Skipping results sheet.")

        entry["start_date_cell"].value = date.today()

    if "TEMPLATE" in results_workbook.sheetnames:
        results_workbook.remove(results_workbook["TEMPLATE"])
    results_workbook.save(run_output_path)
    workbook.save(input_path)
    print(f"Updated start dates in {input_path} and saved {run_output_path}.")

if __name__ == "__main__":
    main(api="ferc")
