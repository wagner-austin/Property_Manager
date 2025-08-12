import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

ROOT: Path = Path(__file__).resolve().parent.parent
_SETTINGS: Optional[Dict[str, Any]] = None  # cache


def _read_json(p: Path) -> Dict[str, Any]:
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # Ensure a dict for typing
    return cast(Dict[str, Any], raw if isinstance(raw, dict) else {})


def _read_dotenv() -> Dict[str, str]:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


_DOTENV: Dict[str, str] = _read_dotenv()


def _getenv(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, _DOTENV.get(name, default))


def load_settings(force: bool = False) -> Dict[str, Any]:
    global _SETTINGS
    if _SETTINGS is not None and not force:
        return _SETTINGS
    cfg = _read_json(ROOT / "config" / "settings.json")
    cfg.setdefault("sites", {})
    # env overrides
    if _getenv("PUBLIC_FOLDER_PATH"):
        cfg["publicFolderPath"] = _getenv("PUBLIC_FOLDER_PATH")
    if _getenv("PUBLIC_FOLDER_ID"):
        cfg["publicFolderId"] = _getenv("PUBLIC_FOLDER_ID")
    if _getenv("SITES_DIR"):
        cfg["sites"]["dataPath"] = _getenv("SITES_DIR")
    if _getenv("DEFAULT_SITE"):
        cfg["sites"]["defaultSite"] = _getenv("DEFAULT_SITE")
    _SETTINGS = cfg
    return _SETTINGS


def sites_dir() -> Path:
    s = load_settings().get("sites", {})
    data_path = str(s.get("dataPath", "sites"))  # force str
    return (ROOT / data_path).resolve()


def default_site() -> str:
    s = load_settings().get("sites", {})
    return str(s.get("defaultSite", "lancaster-12"))


def public_folder_path() -> Optional[Path]:
    p = load_settings().get("publicFolderPath")
    return Path(p).resolve() if isinstance(p, str) and p else None


def public_folder_id() -> Optional[str]:
    return load_settings().get("publicFolderId")


def credentials_paths() -> Tuple[Path, Path]:
    cfg = load_settings()
    cred = _getenv("GOOGLE_CREDENTIALS", cfg.get("apiKeys", {}).get("googleDrive", "")) or ""
    tok = _getenv("GOOGLE_TOKEN", cfg.get("apiKeys", {}).get("token", "")) or ""
    cred_path = Path(cred) if cred else Path("config/credentials.json")
    tok_path = Path(tok) if tok else Path("config/token.json")
    if not cred_path.is_absolute():
        cred_path = ROOT / cred_path
    if not tok_path.is_absolute():
        tok_path = ROOT / tok_path
    return cred_path.resolve(), tok_path.resolve()


def reload_settings() -> Dict[str, Any]:
    return load_settings(force=True)
