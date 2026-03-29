from paths import input_path, output_path
from ferc_api import fetch_search_results, parse_search_hits
from excel_io import (format_date, load_dockets,
                       load_results, create_result_sheet)
from datetime import date
from importlib import import_module

ALLOWED_APIS = {
    "ferc": "ferc_api",
}

def load_api(api_key):
    if api_key not in ALLOWED_APIS:
        raise ValueError(f"Unsupported API: {api_key}")
    module_name = ALLOWED_APIS[api_key]
    return import_module(module_name)

def main(api="ferc"):
    api_module = load_api(api)
    print(f"Using INPUT_FILE={input_path}, OUTPUT_FILE={output_path}, API={api}")

    workbook, docket_rows = load_dockets()
    if not docket_rows:
        print(f"No docket rows found in {input_path}.")
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
            print(f"Wrote {len(records)} records to {output_path} sheet '{docket}'.")
        else:
            print(f"No records found for docket {docket}. Skipping results sheet.")

        entry["start_date_cell"].value = date.today()

    results_workbook.save(output_path)
    workbook.save(input_path)
    print(f"Updated start dates in {input_path} and saved {output_path}.")

if __name__ == "__main__":
    main()
