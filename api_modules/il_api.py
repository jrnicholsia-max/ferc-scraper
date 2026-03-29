import re
from datetime import date, datetime
from html import unescape
from urllib.parse import urljoin
import requests


BASE_URL = "https://www.icc.illinois.gov"
DOCUMENTS_PATH_TEMPLATE = "/docket/{docket}/documents"


def build_search_payload(dnumber, start_date):
	"""Return payload metadata for the specified docket number and start date."""
	docket = str(dnumber or "").strip()
	if not docket:
		raise ValueError("Docket number is required.")
	path = DOCUMENTS_PATH_TEMPLATE.format(docket=docket)
	return {
		"docket_number": docket,
		"start_date": start_date,
		"documents_path": path,
		"documents_url": urljoin(BASE_URL, path),
	}


def fetch_search_results(dnumber, start_date, session=None):
	"""Return ICC documents page content for a docket and start date."""
	payload = build_search_payload(dnumber, start_date)
	s = session or requests.Session()
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.3856.84",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"Referer": BASE_URL,
	}
	s.headers.update(headers)

	response = s.get(payload["documents_url"], timeout=30)
	response.raise_for_status()

	return {
		"docket_number": payload["docket_number"],
		"start_date": payload["start_date"],
		"documents_url": payload["documents_url"],
		"html": response.text,
	}


def _clean_html_text(raw):
	"""Decode entities and strip tags/extra whitespace from an HTML snippet."""
	no_tags = re.sub(r"<[^>]+>", " ", raw)
	return " ".join(unescape(no_tags).split())


def _parse_card_date(month_year_text, day_text):
	month_year = month_year_text.replace("-", " ").strip()
	day = day_text.strip()
	try:
		return datetime.strptime(f"{month_year} {day}", "%b %Y %d").date()
	except ValueError:
		return None


def _coerce_start_date(start_date_value):
	"""Normalize incoming start date values into a date for filtering."""
	if isinstance(start_date_value, datetime):
		return start_date_value.date()
	if isinstance(start_date_value, date):
		return start_date_value
	if isinstance(start_date_value, str):
		value = start_date_value.strip()
		for fmt in (
			"%Y-%m-%d",
			"%Y-%m-%dT%H:%M:%S",
			"%Y-%m-%dT%H:%M",
			"%Y-%m-%d %H:%M:%S",
			"%Y-%m-%d %H:%M",
			"%m/%d/%Y",
			"%m-%d-%Y",
		):
			try:
				return datetime.strptime(value, fmt).date()
			except ValueError:
				continue
	return date.min


def parse_search_hits(json_data):
	"""Extract filing records from the ICC docket documents page payload."""
	html = json_data.get("html", "")
	start_date_obj = _coerce_start_date(json_data.get("start_date", ""))

	card_pattern = re.compile(
		r'<li\s+class="soi-icc-card-list-item[^>]*>.*?'
		r'<div class="card-header"><div>(?P<month_year>[^<]+)</div><div>(?P<day>[^<]+)</div></div>.*?'
		r'<h4><a href="(?P<href>/docket/[^\"]+/documents/(?P<doc_id>\d+))">(?P<doc_type>[^<]+)</a></h4>.*?'
		r'(?P<details>(?:<span class="d-block">.*?</span>)+)',
		flags=re.DOTALL,
	)
	span_pattern = re.compile(r'<span class="d-block">(.*?)</span>', flags=re.DOTALL)

	records = []
	for match in card_pattern.finditer(html):
		card_date = _parse_card_date(match.group("month_year"), match.group("day"))
		if not card_date or card_date < start_date_obj:
			continue

		detail_fields = [_clean_html_text(x) for x in span_pattern.findall(match.group("details"))]
		description = detail_fields[0] if len(detail_fields) > 0 else ""
		filed_by = detail_fields[2] if len(detail_fields) > 2 else (detail_fields[1] if len(detail_fields) > 1 else "")

		doc_type = _clean_html_text(match.group("doc_type"))
		title = doc_type if not description else f"{doc_type}: {description}"
		if "service list" in title.lower():
			continue

		doc_id = match.group("doc_id")
		href = match.group("href")
		records.append({
			"title": title,
			"date": card_date.isoformat(),
			"accession_number": doc_id,
			"accession_url": urljoin(BASE_URL, href),
			"category": filed_by,
		})

	return records
