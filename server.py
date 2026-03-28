"""Minimal Flask server for hosting HTML5 crossword solver + INASRA shares."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, request, send_file, send_from_directory, url_for

from inasra_adapter import generate_share_token, normalize_inasra_ipuz, read_ipuz, write_ipuz

BASE_DIR = Path(__file__).resolve().parent
SHARE_DIR = BASE_DIR / "shared_puzzles"
MANIFEST_PATH = SHARE_DIR / "manifest.json"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
    SHARE_DIR.mkdir(parents=True, exist_ok=True)

    @app.route("/")
    def root() -> object:
        return send_from_directory(BASE_DIR, "index.html")

    @app.route("/play/<token>")
    def play(token: str) -> object:
        ensure_shared_puzzle_exists(token)
        return redirect(url_for("root", id=token))

    @app.route("/api/puzzle/<token>.ipuz")
    def serve_puzzle(token: str) -> object:
        path = SHARE_DIR / f"{token}.ipuz"
        if not path.exists():
            abort(404)
        return send_file(
            path,
            mimetype="application/json",
            as_attachment=False,
            download_name=f"{token}.ipuz",
        )

    @app.route("/api/puzzle/<token>/meta")
    def serve_puzzle_meta(token: str) -> object:
        path = SHARE_DIR / f"{token}.ipuz"
        if not path.exists():
            abort(404)
        puzzle = read_ipuz(path)
        return jsonify(
            {
                "token": token,
                "title": puzzle.get("title"),
                "author": puzzle.get("author"),
                "origin": puzzle.get("origin"),
                "fakeclues": bool(puzzle.get("fakeclues")),
            }
        )

    @app.route("/publish", methods=["POST"])
    def publish_route() -> object:
        upload = request.files.get("puzzle")
        if upload is None or not upload.filename:
            return jsonify({"error": "Expected a file upload in form field 'puzzle'."}), 400
        token = publish_puzzle_file(upload.stream.read(), original_name=upload.filename)
        return (
            jsonify(
                {
                    "token": token,
                    "play_url": url_for("play", token=token, _external=True),
                    "puzzle_url": url_for("serve_puzzle", token=token, _external=True),
                }
            ),
            201,
        )

    @app.route("/<path:asset_path>")
    def assets(asset_path: str) -> object:
        candidate = BASE_DIR / asset_path
        if candidate.is_file():
            return send_from_directory(BASE_DIR, asset_path)
        abort(404)

    return app


def ensure_shared_puzzle_exists(token: str) -> None:
    if not (SHARE_DIR / f"{token}.ipuz").exists():
        abort(404)


def publish_puzzle_file(file_bytes: bytes, original_name: str = "puzzle.ipuz") -> str:
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    token = generate_unique_token()
    raw_path = SHARE_DIR / f"{token}.raw.ipuz"
    normalized_path = SHARE_DIR / f"{token}.ipuz"

    raw_path.write_bytes(file_bytes)
    puzzle = read_ipuz(raw_path)
    normalized = normalize_inasra_ipuz(puzzle)
    write_ipuz(normalized_path, normalized)
    update_manifest(
        token=token,
        title=normalized.get("title") or original_name,
        original_name=original_name,
    )
    return token


def generate_unique_token() -> str:
    while True:
        token = generate_share_token()
        if not (SHARE_DIR / f"{token}.ipuz").exists():
            return token


def update_manifest(*, token: str, title: str, original_name: str) -> None:
    manifest: dict[str, dict[str, str]] = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest[token] = {
        "title": title,
        "original_name": original_name,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the HTML5 crossword solver with INASRA share support."
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Run the Flask development server.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=5000)
    serve_parser.add_argument("--debug", action="store_true")

    publish_parser = subparsers.add_parser("publish", help="Normalize and publish an iPuz file.")
    publish_parser.add_argument("path", help="Path to the source .ipuz file")
    publish_parser.add_argument("--base-url", default="http://127.0.0.1:5000")

    args = parser.parse_args()
    app = create_app()

    if args.command == "publish":
        path = Path(args.path).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Puzzle file not found: {path}")
        token = publish_puzzle_file(path.read_bytes(), original_name=path.name)
        base = args.base_url.rstrip("/")
        print(f"Published: {path.name}")
        print(f"Token:     {token}")
        print(f"Play URL:  {base}/play/{token}")
        print(f"Puzzle:    {base}/api/puzzle/{token}.ipuz")
        return

    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 5000)
    debug = bool(getattr(args, "debug", False))
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
