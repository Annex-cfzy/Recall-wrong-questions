#!/usr/bin/env python3
"""Package Recall for Aliyun FC 'code upload' deploy (no Docker / no ACR).

Produces recall-fc.zip containing:
  - backend/app/               (FastAPI source)
  - backend/requirements.txt
  - backend/frontend/dist/     (built SPA, copied in here so main.py finds it)

Usage (on YOUR machine, with Node + Python available):
  python deploy/build_fc_package.py

Then upload the generated recall-fc.zip to an Aliyun FC function
(Python 3.12 runtime) and configure:
  Start command : python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
  Env vars      : MOCK_EXTERNAL=true
                  RECALL_DATA_DIR=/tmp/recall-data
                  RECALL_DB_PATH=/tmp/recall-data/recall.db
                  RECALL_UPLOAD_DIR=/tmp/recall-uploads
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # deploy/ -> project root
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST_SRC = FRONTEND / "dist"
DIST_DST = BACKEND / "frontend" / "dist"
ZIP_PATH = ROOT / "recall-fc.zip"

EXCLUDE_DIRS = {
    ".venv", "venv", "__pycache__", "node_modules", ".git",
    "uploads", "data", ".pytest_cache", "tests",
}
EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def _npm_build_command() -> tuple:
    """Return (command, use_shell) for `npm run build`.

    On Windows `npm` is really `npm.cmd`; a bare non-shell subprocess call
    raises FileNotFoundError because CreateProcess won't resolve the `.cmd`
    extension. Falling back to shell=True lets cmd.exe resolve it.
    """
    if os.name == "nt":
        return "npm run build", True
    return ["npm", "run", "build"], False


def build_frontend() -> None:
    if not (FRONTEND / "package.json").exists():
        sys.exit(f"[ERR] frontend/package.json not found at {FRONTEND}")
    cmd, use_shell = _npm_build_command()
    print("[1/4] Building frontend (npm run build) ...")
    try:
        subprocess.run(cmd, cwd=str(FRONTEND), check=True, shell=use_shell)
    except FileNotFoundError:
        sys.exit(
            "[ERR] 未检测到 npm。请先安装 Node.js LTS (https://nodejs.org)，\n"
            "      安装完成后重新打开终端再运行本脚本。"
        )


def copy_dist() -> None:
    if not DIST_SRC.is_dir():
        sys.exit(f"[ERR] {DIST_SRC} missing — frontend build may have failed.")
    print("[2/4] Copying dist into backend/frontend/dist ...")
    if DIST_DST.exists():
        shutil.rmtree(DIST_DST)
    shutil.copytree(DIST_SRC, DIST_DST)


def _excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts) or path.suffix in EXCLUDE_SUFFIXES


def _add(zf: zipfile.ZipFile, path: Path, base: Path) -> None:
    zf.write(path, str(path.relative_to(base)).replace(os.sep, "/"))


def package() -> None:
    print(f"[3/4] Zipping backend/ -> {ZIP_PATH.name} ...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in (BACKEND / "app").rglob("*"):
            if path.is_file() and not _excluded(path):
                _add(zf, path, BACKEND)
        req = BACKEND / "requirements.txt"
        if req.exists():
            zf.write(req, "requirements.txt")
        for path in DIST_DST.rglob("*"):
            if path.is_file():
                _add(zf, path, BACKEND)
    size = ZIP_PATH.stat().st_size / 1024 / 1024
    print(f"[4/4] Done. Package: {ZIP_PATH} ({size:.1f} MB)")


if __name__ == "__main__":
    try:
        build_frontend()
        copy_dist()
        package()
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERR] 构建或打包失败：{e}")
    print("\nNext: upload recall-fc.zip to Aliyun FC (Python 3.12) and set the "
          "start command + env vars listed above / in 部署上线指南.md.")
