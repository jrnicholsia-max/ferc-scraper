# Docket Scraper

A small Python project that reads docket numbers from an Excel file, queries the FERC eLibrary, and writes results back to Excel.

## Repository layout

- `main.py` - application entry point
- `ferc_api.py` - FERC API request and response parsing
- `data_io.py` - input/output (i/o) utilities
- `data/` - folder for i/o data files
- `paths.py` - file paths for i/o data files
- `requirements.txt` - Python dependencies

## Future priorities

- Expanding to state-level Public Utility Commission docket systems, prioritizing states in Northeast (New York and New England) and PJM Interconnection footprint
- Enhancing usability (especially in updating and using the i/o data files) and providing instructions for users unfamiliar with Python
- Improving filters to screen out low-importance filings (e.g., petitition to intervene, request to update service list, etc.)
- Improving output for user-specific workflow (e.g., comment summaries in Eyes & Ears)