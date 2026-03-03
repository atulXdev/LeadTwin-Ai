# Workflow: Export Data

## Objective
Export scored leads to CSV file and optionally push to Google Sheets.

## Required Inputs
- `leads` (list[dict]): List of scored and enriched lead dicts
- `project_name` (str): Project name for the file naming

## Tools to Execute
1. `tools/sheets_export.py` → `format_leads_for_export(profiles, contacts, scores, insights)` — Merge data
2. `tools/sheets_export.py` → `export_to_csv(leads, project_name)` — Write CSV to .tmp/

## Process
1. Merge enriched profiles, contacts, scores, and insights into flat lead dicts
2. Sort by score (descending — hottest leads first)
3. Write to CSV in `.tmp/{project_name}_{timestamp}.csv`
4. Return the file path

## Expected Output
- CSV file at `.tmp/leads_20250303_153000.csv`
- Columns: company_name, website, email, phone, linkedin, score, grade, insights, etc.

## Edge Cases
- **Empty leads list**: Create CSV with headers only, log warning
- **Special characters in data**: CSV writer handles UTF-8 encoding

## Future: Google Sheets Integration
- Requires `credentials.json` from Google Cloud Console
- Uses Google Sheets API v4 to push data
- Will be added in Phase 2

## Lessons Learned
(Agent updates this section as issues are discovered)
