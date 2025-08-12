# Smart Site Mapper Documentation

## Overview

The Smart Site Mapper (`scripts/smart_site_mapper.py`) is an intelligent file processing system that automatically organizes Google Drive files into a structured site format with document completeness tracking.

## Key Features

- **Pattern-based file categorization** - Automatically recognizes plans, lots, platmaps, and other document types
- **Lot completeness tracking** - Monitors which documents are available for each lot
- **Flexible configuration** - Control display, requirements, and overrides via `sites.config.json`
- **Type-safe implementation** - Uses TypedDict for robust type checking
- **Smart document references** - Intelligent fallback logic for missing documents

## Configuration File: sites.config.json

### Global Settings

```json
{
  "global": {
    "default_bedrooms": 3,
    "default_bathrooms": 2,
    "default_sqft": 2000,
    "strict_mode": true,
    "max_misc_docs": 5
  }
}
```

### Site Configuration

```json
{
  "sites": [{
    "slug": "lancaster-12",
    "name": "Lancaster 12",
    "aliases": ["LANCASTER", "LANCASTER 12"],
    "drive_folder_id": "FOLDER_ID",
    "lot_count": 12,
    "lot_details": {...},
    "lot_requirements": {...},
    "plan_details": {...},
    "document_overrides": {...}
  }]
}
```

## Lot Details Configuration

Define specific information for individual lots:

```json
"lot_details": {
  "2": {
    "apn": "3203-063-002",
    "address": "43741 Verella Ct",
    "status": "Owned",
    "size": "~0.25 acres",
    "has_title_report": true,
    "has_grading": false,
    "has_plan_assignment": false,
    "doc_refs": {
      "title_report": "DRIVE_FILE_ID"
    }
  }
}
```

### Available Fields

- `apn` - Assessor's Parcel Number
- `address` - Physical address
- `status` - Ownership status (e.g., "Owned", "Available", "Pending")
- `size` - Lot size description
- `has_title_report` - Boolean flag for title report availability
- `has_grading` - Boolean flag for grading plan availability
- `has_plan_assignment` - Boolean flag for plan assignment
- `doc_refs` - Direct references to specific documents

## Lot Requirements

Control how lots are displayed and tracked:

```json
"lot_requirements": {
  "show_missing": true,
  "hide_incomplete": false,
  "required_docs": ["title_report", "grading", "plan_assignment"],
  "show_status_in_size": false
}
```

### Options

- `show_missing` - Display which documents are missing
- `hide_incomplete` - Hide lots that don't have all required documents
- `required_docs` - List of documents needed for 100% completion
- `show_status_in_size` - Include status in the size field (deprecated)

## Plan Details

Specify details for each floor plan:

```json
"plan_details": {
  "1": {
    "bedrooms": 4,
    "bathrooms": 3,
    "sqft": 2168,
    "stories": 1,
    "garage_sf": 440
  }
}
```

## Document Overrides

Rename, redescribe, or hide documents:

```json
"document_overrides": {
  "platmap": {
    "title": "Custom Title",
    "description": "Custom description"
  },
  "entitlements": {
    "hide": true
  }
}
```

## File Pattern Recognition

The mapper recognizes files based on patterns:

### Plans
- `plan 1`, `plan 01`, `plan1`
- `model 1`, `unit 1`, `type 1`

### Lots
- `lot 1`, `lot 01`, `parcel 1`

### Document Types
- **Platmap**: `plat map`, `tentative map`, `lot map`, `site map`
- **Entitlements**: `entitlement`, `permit`, `approval`, `zoning`
- **Grading**: `grading plan`, `grading`, `elevation`, `topograph`
- **LLC Info**: `llc`, `company`, `corporate`, `business`
- **Presentation**: `presentation`, `slide`, `deck`, `overview`

## Completeness Calculation

Completeness is calculated as a percentage based on required documents:

```
completeness = (available_required_docs / total_required_docs) * 100
```

Example:
- Required: `["title_report", "grading", "plan_assignment"]`
- Available: `["title_report"]`
- Completeness: 33%

## Output Format

The mapper generates a `data.json` file with:

```json
{
  "siteName": "Lancaster 12",
  "plans": [...],
  "lots": [
    {
      "id": "lot-2",
      "number": "Lot 2",
      "title": "Lot 2",
      "size": "~0.25 acres",
      "description": "APN 3203-063-002 • ~0.25 acres • Owned • 33% complete",
      "completeness": 33,
      "docRefs": {
        "title_report": "FILE_ID",
        "platmap": "FILE_ID"
      },
      "features": ["APN 3203-063-002", "Owned"]
    }
  ],
  "projectDocs": [...]
}
```

## Usage

### Basic Usage

```bash
python scripts/smart_site_mapper.py
```

### With Options

```bash
python scripts/smart_site_mapper.py \
  --config sites.config.json \
  --inventory file-mapping.json \
  --sites-dir sites \
  --dry-run
```

### Command Line Arguments

- `--config` - Path to configuration file (default: `sites.config.json`)
- `--inventory` - Path to Drive inventory file (default: `file-mapping.json`)
- `--sites-dir` - Directory for output files (default: `sites`)
- `--dry-run` - Preview changes without writing files

## Integration with Make

```bash
# Generate site data
make map

# Or with specific site
make map SITE=lancaster-12
```

## Document Reference Fallback Logic

For lot buttons, the mapper uses intelligent fallback:

1. Check for lot-specific documents (`title_report`, `grading`, `plan_assignment`)
2. Fall back to the general platmap
3. Use individual lot file if available

This ensures buttons always link to the most relevant document.

## Adding New Sites

1. Add site configuration to `sites.config.json`
2. Create Drive inventory with `audit_drive_files.py`
3. Run the mapper: `python scripts/smart_site_mapper.py`
4. Review generated `sites/[slug]/data.json`
5. Deploy the updated site

## Troubleshooting

### Files Not Categorizing Correctly

Check file naming patterns match expected formats. The mapper is case-insensitive but requires specific keywords.

### Completeness Not Calculating

Ensure `lot_requirements.required_docs` is set and matches the `has_*` flags or `doc_refs` keys.

### Documents Not Hiding

Set `hide: true` in `document_overrides` for the specific document category.

## Type Safety

The mapper uses TypedDict for type checking:

```python
class LotDetails(TypedDict, total=False):
    apn: str
    address: str
    status: str
    size: str
    has_title_report: bool
    has_grading: bool
    has_plan_assignment: bool
    doc_refs: NotRequired[Dict[str, str]]
```

Run type checking with:
```bash
make check
```

## Best Practices

1. **Keep file names consistent** - Use standard patterns like "SITE PLAN 1.pdf"
2. **Set required documents** - Define what constitutes a complete lot
3. **Use lot_details** - Provide rich information for available lots
4. **Hide incomplete sections** - Use `hide_incomplete: true` for cleaner display
5. **Document overrides** - Clarify misleading file names or hide irrelevant files

## Example Workflow

1. **Audit Drive files**: `make drive-audit`
2. **Configure site**: Edit `sites.config.json`
3. **Run mapper**: `python scripts/smart_site_mapper.py`
4. **Review output**: Check `sites/[slug]/data.json`
5. **Test locally**: `make serve`
6. **Deploy**: `make pack` and upload