import requests
from datetime import date

SEARCH_PAGE_URL = "https://elibrary.ferc.gov/eLibrary/search"
ADVANCED_SEARCH_URL = "https://elibrary.ferc.gov/eLibraryWebAPI/api/Search/AdvancedSearch"


def build_search_payload(dnumber, start_date):
    """Return JSON payload for the specified docket number and start date."""
    return {
        "searchText": "*",
        "searchFullText": True,
        "searchDescription": True,
        "dateSearches": [
            {
                "dateType": "filed_date",
                "startDate": start_date,
                "endDate": str(date.today()),
            }
        ],
        "availability": None,
        "affiliations": [],
        "categories": [],
        "libraries": [],
        "accessionNumber": None,
        "eFiling": False,
        "docketSearches": [{"docketNumber": dnumber, "subDocketNumbers": []}],
        "resultsPerPage": 100,
        "curPage": 0,
        "classTypes": [],
        "sortBy": "",
        "groupBy": "NONE",
        "idolResultID": "",
        "allDates": False,
    }


def fetch_search_results(dnumber, start_date, session=None):
    """Return JSON search results from the FERC eLibrary API."""
    s = session or requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.3856.84",
        "Accept": "application/json, text/plain, */*",
        "Referer": SEARCH_PAGE_URL,
    }
    s.headers.update(headers)
    s.get(SEARCH_PAGE_URL, timeout=30)

    response = s.post(ADVANCED_SEARCH_URL, json=build_search_payload(dnumber, start_date), timeout=30)
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        raise RuntimeError(f"Invalid JSON response: {response.text[:400]}")


def parse_search_hits(json_data):
    """Extract search hit records from the API response."""
    hits = json_data.get("searchHits") or json_data.get("results") or json_data.get("hits") or []
    records = []

    for hit in hits:
        title = hit.get("description") or hit.get("documentTitle") or "No title"
        if "service list" in title.lower():
            continue

        accession_number = hit.get("acesssionNumber") or hit.get("accessionNumber") or ""

        records.append({
            "title": title,
            "date": hit.get("filedDate") or hit.get("issuedDate") or hit.get("postedDate") or "",
            "accession_number": accession_number,
            "accession_url": f"https://elibrary.ferc.gov/eLibrary/filelist?accession_number={accession_number}" if accession_number else "",
            "category": hit.get("category") or "",
        })

    return records
