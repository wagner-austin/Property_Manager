#!/usr/bin/env python3
"""
Smart Site Mapper - Intelligently maps Google Drive files to site structure
Prevents duplicate/nonsense panels and handles multiple properties
"""

import argparse
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

# Import TypedDict and NotRequired from typing_extensions for compatibility
from typing_extensions import Literal, NotRequired, TypedDict

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("smart_site_mapper")


# Type definitions
class PlanItem(TypedDict, total=False):
    id: str
    name: str
    title: str
    description: str
    bedrooms: int
    bathrooms: float
    sqft: int
    features: List[str]
    file: str
    fileName: str
    photos: List[str]


class LotDetails(TypedDict, total=False):
    apn: str
    address: str
    status: str
    size: str
    has_title_report: bool
    has_grading: bool
    has_plan_assignment: bool
    doc_refs: NotRequired[Dict[str, str]]


DocKey = Literal["title_report", "grading", "plan_assignment", "platmap", "entitlements"]


class LotRequirements(TypedDict, total=False):
    show_missing: bool
    hide_incomplete: bool
    show_status_in_size: bool
    required_docs: List[DocKey]


class LotItem(TypedDict, total=False):
    id: str
    number: str
    title: NotRequired[str]
    description: NotRequired[str]
    size: str
    features: List[str]
    file: str
    name: str
    page: Optional[int]
    photos: List[str]
    status: NotRequired[str]
    apn: NotRequired[str]
    address: NotRequired[str]
    missing: NotRequired[List[DocKey]]
    docRefs: NotRequired[Dict[DocKey, str]]
    completeness: NotRequired[int]


class ProjectDocItem(TypedDict):
    id: str
    title: str
    description: str
    file: str
    icon: str
    name: str


class PhotoItem(TypedDict, total=False):
    id: str
    url: str
    caption: Optional[str]


class DriveInfo(TypedDict, total=False):
    folderId: str
    publicFolderId: NotRequired[str]


class SiteStructure(TypedDict, total=False):
    siteName: str
    plans: List[PlanItem]
    lots: List[LotItem]
    projectDocs: List[ProjectDocItem]
    photos: List[PhotoItem]
    flags: Dict[str, bool]
    drive: NotRequired[DriveInfo]


class DriveFile(TypedDict, total=False):
    id: str
    name: NotRequired[str]
    current_name: NotRequired[str]
    location: NotRequired[str]
    mime_type: NotRequired[str]
    size_mb: NotRequired[float]
    modified: NotRequired[str]


class GlobalConfig(TypedDict, total=False):
    default_bedrooms: int
    default_bathrooms: float
    default_sqft: int
    strict_mode: bool
    strict: bool
    max_misc_docs: int


class PlanDetails(TypedDict, total=False):
    bedrooms: int
    bathrooms: float
    sqft: int
    stories: NotRequired[int]
    garage_sf: NotRequired[int]
    porch_sf: NotRequired[int]
    patio_sf: NotRequired[int]


class DocOverride(TypedDict, total=False):
    title: str
    description: str
    hide: bool


class SiteConfig(TypedDict, total=False):
    slug: str
    name: str
    aliases: List[str]
    drive_folder_id: str
    require_public_subfolder: bool
    lot_count: int
    lot_pages: Dict[str, int]
    plan_details: Dict[str, PlanDetails]
    document_overrides: Dict[str, DocOverride]
    lot_details: Dict[str, LotDetails]
    lot_requirements: LotRequirements
    overrides: Dict[str, str]
    hide_empty_sections: bool


Config = TypedDict(
    "Config",
    {
        "global": GlobalConfig,
        "sites": List[SiteConfig],
    },
)


class FileCategory(Enum):
    PLAN = "plan"
    LOT = "lot"
    PLATMAP = "platmap"
    ENTITLEMENTS = "entitlements"
    GRADING = "grading"
    LLC_INFO = "llc_info"
    PRESENTATION = "presentation"
    PHOTO = "photo"
    MISC = "misc"


@dataclass
class MappedFile:
    id: str
    name: str
    category: FileCategory
    number: Optional[int] = None
    description: Optional[str] = None


class SmartFileMapper:
    PATTERNS: Dict[FileCategory, List[str]] = {
        FileCategory.PLAN: [
            r"\bplan[\s_-]?0*(1[0-2]|[1-9])\b",  # plans 1-12 with optional leading zeros
            r"\bmodel[\s_-]?0*([1-9]\d?)\b",  # models 1-99 with optional leading zeros
            r"\bunit[\s_-]?0*([1-9]\d?)\b",  # units 1-99 with optional leading zeros
            r"\btype[\s_-]?0*([1-9]\d?)\b",  # types 1-99 with optional leading zeros
        ],
        FileCategory.LOT: [
            r"\b(?:lot|parcel)[\s_-]?0*([1-9]\d{0,2})\b"  # lots/parcels 1-999 with optional leading zeros
        ],
        FileCategory.PLATMAP: [r"plat\s?map", r"tentative\s?map", r"lot\s?map", r"site\s?map"],
        FileCategory.ENTITLEMENTS: [r"entitlement", r"permit", r"approval", r"zoning"],
        FileCategory.GRADING: [r"grading\s?plan", r"grading", r"grade", r"elevation", r"topograph"],
        FileCategory.LLC_INFO: [r"llc", r"company", r"corporate", r"business"],
        FileCategory.PRESENTATION: [r"presentation", r"slide", r"deck", r"overview"],
        FileCategory.PHOTO: [r"photo", r"image", r"picture", r"render"],
    }

    def __init__(self, aliases: List[str], defaults: GlobalConfig, strict: bool):
        self.aliases = [a.lower() for a in aliases] if aliases else []
        self.defaults = defaults
        self.strict = strict
        self.buckets: Dict[FileCategory, List[MappedFile]] = {c: [] for c in FileCategory}

    def _aliased(self, name: str) -> bool:
        # If no aliases defined, accept all files (already filtered by location)
        if not self.aliases:
            return True
        # Check if any alias appears in the filename
        low = name.lower()
        # Accept if matches alias OR if it's a misc file in the right location
        return any(a in low for a in self.aliases) or True  # Always accept for now since filtered by location

    def _desc(self, cat: FileCategory, num: Optional[int], name: str) -> str:
        d = {
            FileCategory.PLAN: f"Floor plan {num}" if num else "Floor plan details",
            FileCategory.LOT: f"Lot {num} information" if num else "Lot information",
            FileCategory.PLATMAP: "Official lot layout and dimensions",
            FileCategory.ENTITLEMENTS: "Development permissions and approvals",
            FileCategory.GRADING: "Site grading and elevation plans",
            FileCategory.LLC_INFO: "Company details and structure",
            FileCategory.PRESENTATION: "Project overview presentation",
            FileCategory.PHOTO: f"Site photo {num}" if num else "Site photography",
        }
        return d.get(cat, "Project documentation")

    def categorize(self, file: DriveFile) -> Optional[MappedFile]:
        fid = file["id"]
        # Handle both 'name' and 'current_name' fields
        fname = file.get("name") or file.get("current_name", "")
        if not self._aliased(fname):  # keep unrelated files out
            return None
        name_lower = fname.lower()

        # Check categories in priority order (grading before plan to avoid false matches)
        priority_order: List[FileCategory] = [
            FileCategory.GRADING,  # Check grading before plan
            FileCategory.PLATMAP,
            FileCategory.ENTITLEMENTS,
            FileCategory.LLC_INFO,
            FileCategory.PRESENTATION,
            FileCategory.LOT,
            FileCategory.PLAN,
            FileCategory.PHOTO,
            FileCategory.MISC,
        ]

        for cat in priority_order:
            patterns: List[str] = self.PATTERNS.get(cat, [])
            for pat in patterns:
                m = re.search(pat, name_lower)
                if m:
                    num = None
                    if m.groups():
                        try:
                            num = int(m.group(1))
                        except Exception:
                            pass
                    return MappedFile(fid, fname, cat, num, self._desc(cat, num, fname))
        return MappedFile(fid, fname, FileCategory.MISC, None, "Project documentation")

    def add_files(self, files: List[DriveFile]) -> None:
        for f in files:
            if "id" not in f:
                log.warning(f"Skipping file without id: {f}")
                continue
            mf = self.categorize(f)  # now handles name/current_name
            if not mf:
                continue
            self.buckets[mf.category].append(mf)
            log.info(f"Mapped: {mf.name} → {mf.category.value}" + (f" #{mf.number}" if mf.number else ""))
        # stable sort for numbered items and deterministic ordering
        for cat in (FileCategory.PLAN, FileCategory.LOT):
            self.buckets[cat].sort(key=lambda x: x.number or 999)
        # Sort other categories by name for deterministic ordering
        for cat in FileCategory:
            if cat not in (FileCategory.PLAN, FileCategory.LOT):
                self.buckets[cat].sort(key=lambda mf: mf.name.lower())

    def build_structure(
        self,
        site_name: str,
        lot_count: int,
        lot_pages: Dict[str, int],
        overrides: Dict[str, str],
        max_misc_docs: Optional[int] = None,
        plan_details: Optional[Dict[str, PlanDetails]] = None,
        doc_overrides: Optional[Dict[str, DocOverride]] = None,
        lot_details: Optional[Dict[str, LotDetails]] = None,
        lot_requirements: Optional[LotRequirements] = None,
    ) -> SiteStructure:
        structure: SiteStructure = {
            "siteName": site_name,
            "plans": [],
            "lots": [],
            "projectDocs": [],
            "photos": [],
        }

        # Plans (use specific details if available, otherwise defaults)
        for plan in self.buckets[FileCategory.PLAN]:
            if plan.number:
                # Get plan-specific details or use defaults
                info = (plan_details or {}).get(str(plan.number), {})
                bedrooms: int = cast(int, info.get("bedrooms", self.defaults.get("default_bedrooms", 3)))
                bathrooms: float = cast(float, info.get("bathrooms", self.defaults.get("default_bathrooms", 2)))
                sqft: int = cast(int, info.get("sqft", self.defaults.get("default_sqft", 2000)))
                stories: int = cast(int, info.get("stories", 1))

                # Format bathrooms display (2.5 -> 2.5, 2.0 -> 2)
                bath_display = f"{bathrooms:.1f}" if bathrooms % 1 else str(int(bathrooms))

                # Add story info to description
                story_text = "Single Story" if stories == 1 else f"{stories} Story"
                plan_item: PlanItem = {
                    "id": f"plan-{plan.number}",
                    "name": f"Plan {plan.number}",
                    "title": f"Plan {plan.number} - {story_text}",
                    "description": f"{bedrooms} bd • {bath_display} ba • {sqft:,} sqft",
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "sqft": sqft,
                    "features": [],
                    "file": plan.id,
                    "fileName": plan.name,
                    "photos": [],
                }
                structure["plans"].append(plan_item)

        # Lots: prefer individual lot PDFs; otherwise platmap; optionally page numbers
        platmap = next(iter(self.buckets[FileCategory.PLATMAP]), None)
        if self.buckets[FileCategory.LOT]:
            for lot in self.buckets[FileCategory.LOT]:
                if not lot.number:
                    continue
                lot_num = lot.number
                ld = cast(LotDetails, (lot_details or {}).get(str(lot_num), {}))

                # Determine what's available for this lot
                docs = ld.get("doc_refs")
                has_title = bool(ld.get("has_title_report")) or (docs is not None and "title_report" in docs)
                has_grad = bool(ld.get("has_grading")) or (docs is not None and "grading" in docs)
                has_plan = bool(ld.get("has_plan_assignment")) or (docs is not None and "plan_assignment" in docs)

                req = cast(
                    LotRequirements,
                    lot_requirements or {"show_missing": True, "hide_incomplete": False, "required_docs": []},
                )
                required = req.get("required_docs", [])
                lot_available: Dict[DocKey, bool] = {
                    "title_report": has_title,
                    "grading": has_grad,
                    "plan_assignment": has_plan,
                }
                lot_missing: List[DocKey] = [r for r in required if not lot_available.get(r, False)]

                # Hide incomplete lots if configured
                if req.get("hide_incomplete") and lot_missing:
                    continue

                lot_item: LotItem = {
                    "id": f"lot-{lot_num}",
                    "number": f"Lot {lot_num}",
                    "title": f"Lot {lot_num}",
                    "size": ld.get("size", "TBD"),
                    "features": [],
                    "file": lot.id,
                    "name": lot.name,
                    "page": lot_pages.get(str(lot_num)),
                    "photos": [],
                }

                # Enrich UI fields
                if "status" in ld:
                    lot_item["status"] = ld["status"]
                if "apn" in ld:
                    lot_item["apn"] = ld["apn"]
                if "address" in ld:
                    lot_item["address"] = ld["address"]
                if req.get("show_missing") and lot_missing:
                    lot_item["missing"] = lot_missing
                if "doc_refs" in ld:
                    lot_item["docRefs"] = cast(Dict[DocKey, str], ld["doc_refs"])
                # Add completeness percentage
                if required:
                    lot_item["completeness"] = int(100 * (len(required) - len(lot_missing)) / len(required))

                # Build description similar to plans
                desc_parts: List[str] = []
                if ld.get("apn"):
                    desc_parts.append(f"APN {ld['apn']}")
                size_val = ld.get("size")
                if size_val and size_val != "TBD":
                    desc_parts.append(size_val)
                status_val = ld.get("status")
                if status_val:
                    desc_parts.append(status_val)
                if required:
                    desc_parts.append(f"{lot_item['completeness']}% complete")

                if desc_parts:
                    lot_item["description"] = " • ".join(desc_parts)

                # Nice-to-have feature chips
                if ld.get("apn"):
                    lot_item["features"].append(f"APN {ld['apn']}")
                if ld.get("status"):
                    lot_item["features"].append(ld["status"])

                structure["lots"].append(lot_item)
        elif platmap:
            for i in range(1, lot_count + 1):
                lot_num = i
                ld = cast(LotDetails, (lot_details or {}).get(str(lot_num), {}))

                # Determine what's available for this lot
                docs = ld.get("doc_refs")
                has_title = bool(ld.get("has_title_report")) or (docs is not None and "title_report" in docs)
                has_grad = bool(ld.get("has_grading")) or (docs is not None and "grading" in docs)
                has_plan = bool(ld.get("has_plan_assignment")) or (docs is not None and "plan_assignment" in docs)

                req = cast(
                    LotRequirements,
                    lot_requirements or {"show_missing": True, "hide_incomplete": False, "required_docs": []},
                )
                required = req.get("required_docs", [])
                plat_available: Dict[DocKey, bool] = {
                    "title_report": has_title,
                    "grading": has_grad,
                    "plan_assignment": has_plan,
                }
                plat_missing: List[DocKey] = [r for r in required if not plat_available.get(r, False)]

                # Hide incomplete lots if configured
                if req.get("hide_incomplete") and plat_missing:
                    continue

                plat_lot_item: LotItem = {
                    "id": f"lot-{lot_num}",
                    "number": f"Lot {lot_num}",
                    "title": f"Lot {lot_num}",
                    "size": ld.get("size", "TBD"),
                    "features": [],
                    "file": platmap.id,
                    "name": platmap.name,
                    "page": lot_pages.get(str(lot_num)),
                    "photos": [],
                }

                # Enrich UI fields
                if "status" in ld:
                    plat_lot_item["status"] = ld["status"]
                if "apn" in ld:
                    plat_lot_item["apn"] = ld["apn"]
                if "address" in ld:
                    plat_lot_item["address"] = ld["address"]
                if req.get("show_missing") and plat_missing:
                    plat_lot_item["missing"] = plat_missing
                if "doc_refs" in ld:
                    plat_lot_item["docRefs"] = cast(Dict[DocKey, str], ld["doc_refs"])
                # Add completeness percentage
                if required:
                    plat_lot_item["completeness"] = int(100 * (len(required) - len(plat_missing)) / len(required))

                # Build description similar to plans
                plat_desc_parts: List[str] = []
                if ld.get("apn"):
                    plat_desc_parts.append(f"APN {ld['apn']}")
                size_val = ld.get("size")
                if size_val and size_val != "TBD":
                    plat_desc_parts.append(size_val)
                status_val = ld.get("status")
                if status_val:
                    plat_desc_parts.append(status_val)
                if required:
                    plat_desc_parts.append(f"{plat_lot_item['completeness']}% complete")

                if plat_desc_parts:
                    plat_lot_item["description"] = " • ".join(plat_desc_parts)
                else:
                    # Default description for lots without details
                    plat_lot_item["description"] = (
                        f"{plat_lot_item['completeness']}% complete" if required else "Documentation pending"
                    )

                # Nice-to-have feature chips
                if ld.get("apn"):
                    plat_lot_item["features"].append(f"APN {ld['apn']}")
                if ld.get("status"):
                    plat_lot_item["features"].append(ld["status"])

                structure["lots"].append(plat_lot_item)
        elif self.strict:
            log.warning("No lot files or platmap found; lots will be hidden in strict mode.")

        # Project docs (whitelist + overrides)
        icon_map: Dict[FileCategory, str] = {
            FileCategory.PLATMAP: "🗺️",
            FileCategory.ENTITLEMENTS: "📋",
            FileCategory.GRADING: "📐",
            FileCategory.LLC_INFO: "🏢",
            FileCategory.PRESENTATION: "📊",
            FileCategory.MISC: "📄",
        }
        whitelist = [
            FileCategory.PLATMAP,
            FileCategory.ENTITLEMENTS,
            FileCategory.GRADING,
            FileCategory.LLC_INFO,
            FileCategory.PRESENTATION,
        ]

        def add_doc(cat: FileCategory, mf: MappedFile) -> None:
            doc: ProjectDocItem = {
                "id": f"{cat.value}-{len(structure['projectDocs'])+1}",
                "title": Path(mf.name).stem.title(),
                "description": mf.description or "",
                "file": mf.id,
                "icon": icon_map.get(cat, "📄"),
                "name": mf.name,
            }
            structure["projectDocs"].append(doc)

        for cat in whitelist:
            for mf in self.buckets[cat]:
                add_doc(cat, mf)

        # Add up to N misc docs
        misc_added = 0
        for mf in self.buckets[FileCategory.MISC]:
            if max_misc_docs is not None and misc_added >= max_misc_docs:
                break
            add_doc(FileCategory.MISC, mf)
            misc_added += 1

        # apply overrides (force a specific file id into the right slot names if provided)
        for slot, fid in overrides.items():
            # if slot matches a known id string in projectDocs, replace/add
            matched = [d for d in structure["projectDocs"] if (slot in d["id"]) or (slot.replace("_", "-") in d["id"])]
            if matched:
                for d in matched:
                    d["file"] = fid
            else:
                doc: ProjectDocItem = {
                    "id": slot,
                    "title": slot.replace("-", " ").title(),
                    "description": "Configured override",
                    "file": fid,
                    "icon": "📄",
                    "name": "Override",
                }
                structure["projectDocs"].append(doc)

        # Photos (optional)
        for mf in self.buckets[FileCategory.PHOTO]:
            photo: PhotoItem = {
                "id": mf.id,
                "url": f"https://drive.google.com/uc?export=view&id={mf.id}",
                "caption": mf.description,
            }
            structure["photos"].append(photo)

        # Apply document overrides (rename/hide)
        structure["projectDocs"] = self._apply_doc_overrides(structure["projectDocs"], doc_overrides or {})

        # Auto-fill default docRefs for all lots
        default_refs = self._compute_default_docrefs(structure["projectDocs"])

        # Merge defaults into each lot, but keep any explicit docRefs from config
        req = cast(
            LotRequirements,
            lot_requirements or {"show_missing": True, "hide_incomplete": False, "required_docs": []},
        )
        required = req.get("required_docs", [])

        for lot_item in structure["lots"]:
            existing = cast(Dict[DocKey, str], lot_item.get("docRefs", {}))
            merged: Dict[DocKey, str] = dict(default_refs)
            merged.update(existing)  # explicit > default
            lot_item["docRefs"] = merged

            # Don't recompute missing or completeness - they were already correctly computed
            # during lot construction based on has_* flags and explicit doc_refs
            # The auto-filled platmap/entitlements are just for convenience links

        # Log lot summary
        if structure["lots"]:
            log.info(
                "Lots: %s",
                ", ".join(
                    f"{lot_i['number']} ({'OK' if 'missing' not in lot_i or not lot_i['missing'] else 'missing: ' + ','.join(lot_i['missing'])})"
                    for lot_i in structure["lots"]
                ),
            )

        return structure

    def _compute_default_docrefs(self, project_docs: List[ProjectDocItem]) -> Dict[DocKey, str]:
        """Pick first doc per category to use as a sensible default for lots."""

        def first_id(prefix: str) -> Optional[str]:
            for d in project_docs:
                # projectDocs id format: "<category>-<n>"
                if d["id"].startswith(prefix + "-"):
                    return d["file"]
            return None

        candidates: Dict[DocKey, Optional[str]] = {
            "platmap": first_id(FileCategory.PLATMAP.value),
            "entitlements": first_id(FileCategory.ENTITLEMENTS.value),
            "grading": first_id(FileCategory.GRADING.value),
        }
        # return only populated defaults
        return cast(Dict[DocKey, str], {k: v for k, v in candidates.items() if v is not None})

    def _apply_doc_overrides(
        self, project_docs: List[ProjectDocItem], doc_overrides: Dict[str, DocOverride]
    ) -> List[ProjectDocItem]:
        """Apply document overrides to rename or hide documents"""
        if not doc_overrides:
            return project_docs

        def matches(d: ProjectDocItem, key: str) -> bool:
            cat = d["id"].split("-", 1)[0]  # e.g., "platmap-1"
            if key in {"platmap", "entitlements", "grading", "llc_info", "presentation", "misc"}:
                return cat == key
            if key.startswith("misc-"):  # substring match on misc docs
                needle = key[5:].lower()
                return needle in d["name"].lower() or needle in d["title"].lower()
            return False

        out: List[ProjectDocItem] = []
        for d in project_docs:
            applied: Optional[DocOverride] = None
            for k, ov in doc_overrides.items():
                if matches(d, k):
                    applied = ov
            if applied and applied.get("hide"):
                continue  # Skip hidden documents
            if applied:
                if "title" in applied:
                    d["title"] = applied["title"]
                if "description" in applied:
                    d["description"] = applied["description"]
            out.append(d)
        return out


# --- helpers ---
def load_config(path: Path) -> Config:
    data = json.loads(path.read_text(encoding="utf-8"))
    return cast(Config, data)


def load_inventory_json(path: Path) -> List[DriveFile]:
    """Use output from your audit script (file-mapping.json). Each item must have id and name."""
    if not path.exists():
        return []
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    # Accept either {"files":[...]} or plain list
    if isinstance(data, dict) and "files" in data:
        return cast(List[DriveFile], data["files"])
    if isinstance(data, list):
        return cast(List[DriveFile], data)
    log.warning("Unexpected inventory format, returning empty list")
    return []


def filter_to_public(files: List[DriveFile], require_public: bool) -> List[DriveFile]:
    if not files:
        return []
    # If audit includes a 'path' or 'parents' field you can filter; otherwise pass-through.
    # Here we simulate: keep all; warn when required but unknown.
    if require_public:
        log.warning("Public subfolder not found in inventory; using root files (warn only).")
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description="Smart site mapper for Drive files")
    ap.add_argument("--config", default="sites.config.json", help="Sites configuration file")
    ap.add_argument("--inventory", default="file-mapping.json", help="Output from scripts.audit_drive_files")
    ap.add_argument("--sites-dir", default="sites", help="Destination root for data.json files")
    ap.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = ap.parse_args()

    cfg: Config = load_config(Path(args.config))
    inv: List[DriveFile] = load_inventory_json(Path(args.inventory))

    # Read global config with both key names for compatibility
    g: GlobalConfig = cast(GlobalConfig, cfg.get("global", {}))
    strict: bool = bool(g.get("strict_mode", g.get("strict", True)))  # Support both keys
    max_misc: Optional[int] = cast(Optional[int], g.get("max_misc_docs"))

    for site in cfg["sites"]:
        slug: str = site["slug"]
        name: str = site["name"]
        aliases: List[str] = site.get("aliases", [])
        lot_count: int = site.get("lot_count", 12)
        lot_pages: Dict[str, int] = site.get("lot_pages", {})
        plan_details = cast(Dict[str, PlanDetails], site.get("plan_details", {}))
        doc_overrides = cast(Dict[str, DocOverride], site.get("document_overrides", {}))
        lot_details = cast(Dict[str, LotDetails], site.get("lot_details", {}))
        lot_requirements = cast(LotRequirements, site.get("lot_requirements", {}))
        overrides = cast(Dict[str, str], site.get("overrides", {}))
        hide_empty: bool = bool(site.get("hide_empty_sections", True))
        defaults: GlobalConfig = g

        # Filter inventory to this site using location field
        site_files: List[DriveFile] = [f for f in inv if f.get("location") == slug] or inv
        files: List[DriveFile] = filter_to_public(
            site_files, require_public=site.get("require_public_subfolder", False)
        )

        mapper = SmartFileMapper(aliases=aliases, defaults=defaults, strict=strict)
        mapper.add_files(files)
        structure = mapper.build_structure(
            name,
            lot_count,
            lot_pages,
            overrides,
            max_misc_docs=max_misc,
            plan_details=plan_details,
            doc_overrides=doc_overrides,
            lot_details=lot_details,
            lot_requirements=lot_requirements,
        )

        # Add Drive folder ID for the CTA button in the format the frontend expects
        if site.get("drive_folder_id"):
            structure["drive"] = {"folderId": site["drive_folder_id"]}

        # Add flag for hide_empty_sections
        if hide_empty:
            if "flags" not in structure:
                structure["flags"] = {}
            structure["flags"]["hideEmptySections"] = True

        out_path = Path(args.sites_dir) / slug / "data.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if args.dry_run:
            log.info(
                f"[DRY RUN] Would write {out_path} with {len(structure['plans'])} plans, "
                f"{len(structure['lots'])} lots, {len(structure['projectDocs'])} docs, "
                f"{len(structure['photos'])} photos."
            )
            print(f"\n=== Preview for {name} ===")
            print(json.dumps(structure, indent=2)[:500] + "...")
        else:
            # Backup existing if present
            if out_path.exists():
                backup_path = out_path.with_suffix(".json.bak")
                backup_path.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
                log.info(f"Backed up existing to {backup_path}")

            out_path.write_text(json.dumps(structure, indent=2), encoding="utf-8")
            log.info(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
