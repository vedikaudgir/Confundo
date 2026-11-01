import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "mockchat.db"
APP_TABLES = {"chats", "participants", "messages"}
PRIVATE_PATHS = (
    PROJECT_ROOT / "server" / "private" / "generated",
    PROJECT_ROOT / "server" / "private" / "avatars",
    PROJECT_ROOT / "server" / "static" / "uploads",
)


def _ensure_project_root():
    if Path.cwd().resolve() != PROJECT_ROOT:
        raise RuntimeError(f"Run this command from the project root: {PROJECT_ROOT}")
    if "DATABASE_URL" in os.environ:
        raise RuntimeError(
            "DATABASE_URL is set. Unset it before resetting; this command only targets "
            "the project-root mockchat.db."
        )
    if "PRIVATE_STORAGE_DIR" in os.environ:
        raise RuntimeError(
            "PRIVATE_STORAGE_DIR is set. Unset it before resetting; no external storage "
            "directories will be removed."
        )


def _ensure_project_file(path):
    if path.is_symlink():
        raise RuntimeError(f"Refusing to delete a symlink: {path}")
    try:
        path.resolve().relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise RuntimeError(f"Refusing to delete a path outside the project: {path}") from error


def _verify_database(path):
    if path.is_symlink():
        raise RuntimeError(f"Refusing to delete a symlink: {path}")
    if not path.exists():
        return
    _ensure_project_file(path)
    with path.open("rb") as database_file:
        if database_file.read(16) != b"SQLite format 3\x00":
            raise RuntimeError(f"Refusing to delete a non-SQLite database: {path}")
    connection = sqlite3.connect(path)
    try:
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError(f"Refusing to delete a corrupt SQLite database: {path}")
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    finally:
        connection.close()
    if not APP_TABLES.issubset(tables):
        raise RuntimeError(
            f"Refusing to delete a database without ChattieBaby chat tables: {path}"
        )


def _validate_private_directory(path):
    if path.is_symlink():
        raise RuntimeError(f"Refusing to recursively remove a symlink: {path}")
    if not path.exists():
        return
    _ensure_project_file(path)
    if not path.is_dir():
        raise RuntimeError(f"Refusing to recursively remove a non-directory: {path}")


def reset():
    _ensure_project_root()
    _verify_database(DATABASE_PATH)

    database_files = (
        DATABASE_PATH,
        Path(f"{DATABASE_PATH}-wal"),
        Path(f"{DATABASE_PATH}-shm"),
    )
    for path in database_files:
        if path.is_symlink():
            raise RuntimeError(f"Refusing to delete a symlink: {path}")
        if path.exists():
            _ensure_project_file(path)
    for path in PRIVATE_PATHS:
        _validate_private_directory(path)

    output_directory = PROJECT_ROOT / "server" / "output"
    output_files = []
    if output_directory.exists():
        if output_directory.is_symlink():
            raise RuntimeError(f"Refusing to inspect a symlink: {output_directory}")
        _ensure_project_file(output_directory)
        if not output_directory.is_dir():
            raise RuntimeError(f"Refusing to inspect a non-directory: {output_directory}")
        output_files = list(output_directory.glob("*.png"))
        for path in output_files:
            if path.is_symlink():
                raise RuntimeError(f"Refusing to delete a symlink: {path}")
            _ensure_project_file(path)

    for path in database_files:
        if path.exists():
            path.unlink()
    for path in PRIVATE_PATHS:
        if path.exists():
            shutil.rmtree(path)
    for path in output_files:
        if path.is_file():
            path.unlink()

    print(f"Reset ChattieBaby SQLite database: {DATABASE_PATH}")
    print("Removed ChattieBaby private generated files, avatars, and renderer PNG outputs.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reset only the repository-local ChattieBaby SQLite database and files."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion of the project-root mockchat.db and ChattieBaby files.",
    )
    args = parser.parse_args(argv)
    if not args.yes:
        parser.error("pass --yes to confirm the ChattieBaby-only reset")
    try:
        reset()
    except (OSError, RuntimeError, sqlite3.Error) as error:
        print(f"Reset refused or failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
