"""Local browser interface for the PDF Tools processing engine."""

import io
import os
import secrets
import shutil
import tempfile
import time
import zipfile
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

import auth_store
import backend


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
SESSION_IDLE_SECONDS = 15 * 60
JOB_LIFETIME_SECONDS = 2 * 60 * 60
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".bmp"}


def _data_directory(database_path):
    directory = Path(database_path).resolve().parent / "web_jobs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _load_or_create_secret(directory):
    configured = os.environ.get("MITS_PDF_SECRET_KEY")
    if configured:
        return configured

    key_path = directory / ".web_session_key"
    try:
        with key_path.open("x", encoding="ascii") as key_file:
            value = secrets.token_hex(32)
            key_file.write(value)
            return value
    except FileExistsError:
        return key_path.read_text(encoding="ascii").strip()


def create_app(account_store=None, data_directory=None):
    """Create the local web app; injectable storage keeps tests isolated."""
    app = Flask(__name__)
    account_store = account_store or auth_store.AuthStore()
    job_directory = Path(data_directory) if data_directory else _data_directory(account_store.database_path)
    job_directory.mkdir(parents=True, exist_ok=True)

    app.config.update(
        SECRET_KEY=_load_or_create_secret(job_directory),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=SESSION_IDLE_SECONDS,
    )
    app.extensions["account_store"] = account_store
    app.extensions["job_directory"] = job_directory
    app.extensions["downloads"] = {}

    def current_user():
        return session.get("user")

    def csrf_token():
        token = session.get("_csrf_token")
        if token is None:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_requests():
        if request.method == "POST":
            expected = session.get("_csrf_token", "")
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("_csrf_token", "")
            if not expected or not secrets.compare_digest(expected, supplied):
                if request.path.startswith("/api/"):
                    return jsonify(error="Your session expired. Refresh the page and try again."), 400
                abort(400, "Your session expired. Refresh the page and try again.")

        user = current_user()
        if not user:
            return None
        if time.time() - session.get("_last_activity", 0) > SESSION_IDLE_SECONDS:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify(error="Your session expired. Sign in again."), 401
            return redirect(url_for("login"))
        if not account_store.is_session_valid(
            user.get("username"), user.get("role"), user.get("session_version")
        ):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify(error="This account session is no longer valid. Sign in again."), 401
            return redirect(url_for("login"))
        session["_last_activity"] = time.time()
        cleanup_old_jobs()
        return None

    def signed_in(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user():
                if request.path.startswith("/api/"):
                    return jsonify(error="Sign in to continue."), 401
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def admin_only(view):
        @wraps(view)
        @signed_in
        def wrapped(*args, **kwargs):
            if current_user().get("role") != "admin":
                return jsonify(error="Administrator access is required."), 403
            return view(*args, **kwargs)
        return wrapped

    def set_login(user):
        session.clear()
        session.permanent = True
        session["user"] = user
        session["_last_activity"] = time.time()
        csrf_token()

    def render_auth(mode, error=None):
        return render_template(
            "auth.html",
            mode=mode,
            error=error,
            username=request.form.get("username", ""),
            needs_setup=account_store.needs_setup(),
        )

    @app.get("/")
    def home():
        if account_store.needs_setup():
            return redirect(url_for("setup"))
        if not current_user():
            return redirect(url_for("login"))
        return render_template("index.html", user=current_user())

    @app.get("/brand-icon")
    def brand_icon():
        return send_file(Path(__file__).resolve().parent / "mits_pdf_icon.png", mimetype="image/png")

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if not account_store.needs_setup():
            return redirect(url_for("login"))
        if request.method == "POST":
            try:
                account_store.create_initial_admin(
                    request.form.get("username"), request.form.get("password")
                )
                set_login(account_store.authenticate(
                    request.form.get("username"), request.form.get("password")
                ))
                return redirect(url_for("home"))
            except (auth_store.AuthenticationError, ValueError) as error:
                return render_auth("setup", str(error)), 400
        return render_auth("setup")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if account_store.needs_setup():
            return redirect(url_for("setup"))
        if current_user():
            return redirect(url_for("home"))
        if request.method == "POST":
            try:
                set_login(account_store.authenticate(
                    request.form.get("username"), request.form.get("password")
                ))
                return redirect(url_for("home"))
            except (auth_store.AuthenticationError, ValueError) as error:
                return render_auth("login", str(error)), 401
        return render_auth("login")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if account_store.needs_setup():
            return redirect(url_for("setup"))
        if request.method == "POST":
            try:
                account_store.register_user(
                    request.form.get("invitation"),
                    request.form.get("username"),
                    request.form.get("password"),
                )
                set_login(account_store.authenticate(
                    request.form.get("username"), request.form.get("password")
                ))
                return redirect(url_for("home"))
            except (auth_store.AuthenticationError, ValueError) as error:
                return render_auth("register", str(error)), 400
        return render_auth("register")

    @app.post("/logout")
    @signed_in
    def logout():
        session.clear()
        return redirect(url_for("login"))

    def cleanup_old_jobs():
        now = time.time()
        downloads = app.extensions["downloads"]
        for token, item in list(downloads.items()):
            if now - item["created"] > JOB_LIFETIME_SECONDS:
                shutil.rmtree(item["directory"], ignore_errors=True)
                downloads.pop(token, None)
        for directory in job_directory.iterdir():
            if directory.is_dir() and directory.name.startswith("job_"):
                try:
                    expired = now - directory.stat().st_mtime > JOB_LIFETIME_SECONDS
                except OSError:
                    continue
                if expired:
                    shutil.rmtree(directory, ignore_errors=True)

    def save_upload(upload, directory, index=0):
        if not upload or not upload.filename:
            raise ValueError("Choose a file to upload.")
        filename = secure_filename(upload.filename)
        suffix = Path(filename).suffix.lower()
        if not suffix or suffix not in ALLOWED_EXTENSIONS:
            raise ValueError("That file type is not supported.")
        saved_path = directory / f"{index}_{filename}"
        upload.save(saved_path)
        if saved_path.stat().st_size == 0:
            raise ValueError(f"{filename} is empty.")
        return str(saved_path)

    def option(name, default=""):
        return request.form.get(name, default)

    def output_name(value, default):
        value = secure_filename(value or "")
        return value or default

    def public_result(result):
        return {
            key: value
            for key, value in result.items()
            if key not in {"output_path", "file_path", "files"}
        } if isinstance(result, dict) else result

    def output_response(directory, result, message, download_path=None, download_name=None):
        payload = {"message": message, "result": public_result(result)}
        if download_path:
            if not Path(download_path).is_file():
                raise RuntimeError("The operation completed without creating its expected output file.")
            token = secrets.token_urlsafe(24)
            app.extensions["downloads"][token] = {
                "owner": current_user()["username"],
                "path": str(download_path),
                "name": download_name or Path(download_path).name,
                "directory": str(directory),
                "created": time.time(),
            }
            payload["download_url"] = url_for("download_file", token=token)
        return jsonify(payload)

    @app.get("/api/csrf")
    @signed_in
    def get_csrf():
        return jsonify(token=csrf_token())

    @app.post("/api/tools/<tool_name>")
    @signed_in
    def run_tool(tool_name):
        cleanup_old_jobs()
        job_path = Path(tempfile.mkdtemp(prefix="job_", dir=job_directory))
        try:
            result = None
            download_path = None
            download_name = None
            uploads = request.files.getlist("files")
            primary_upload = request.files.get("file")
            output_pdf = job_path / "result.pdf"
            input_path = None

            if tool_name == "create-pdf":
                image = save_upload(request.files.get("image"), job_path, 0) if request.files.get("image") else None
                result = backend.create_pdf(
                    str(output_pdf),
                    title=option("title", "Untitled Document"),
                    author=option("author", "PDF Tools User"),
                    text_content=option("text_content"),
                    page_size=option("page_size", "A4"),
                    orientation=option("orientation", "portrait"),
                    image_path=image,
                    font_size=option("font_size", "11"),
                )
                download_path = output_pdf
                download_name = output_name(option("filename"), "document.pdf")
                message = "Your PDF is ready."

            elif tool_name == "merge-pdfs":
                inputs = [save_upload(file, job_path, index) for index, file in enumerate(uploads)]
                result = backend.merge_pdfs(inputs, str(output_pdf))
                download_path = output_pdf
                download_name = output_name(option("filename"), "merged.pdf")
                message = f"Merged {result['total_pages']} pages."

            elif tool_name == "split-pdf":
                input_path = save_upload(primary_upload, job_path)
                out_dir = job_path / "split"
                result = backend.split_pdf(
                    input_path, str(out_dir), option("mode", "all"),
                    option("page_ranges"), option("chunk_size", "1"),
                )
                download_path = job_path / "split.zip"
                with zipfile.ZipFile(download_path, "w", zipfile.ZIP_DEFLATED) as archive:
                    for file_path in result["files"]:
                        archive.write(file_path, arcname=Path(file_path).name)
                download_name = "split_pages.zip"
                message = f"Created {result['count']} PDF files."

            elif tool_name in {"lock-pdf", "unlock-pdf", "compress-pdf", "watermark-pdf",
                               "pdf-to-ppt", "pdf-to-word", "pdf-to-image", "ocr",
                               "extract-text", "rotate-pdf", "delete-pages", "reorder-pages",
                               "pdf-information", "update-metadata", "pdf-preview"}:
                input_path = save_upload(primary_upload, job_path)

                if tool_name == "lock-pdf":
                    result = backend.lock_pdf(input_path, str(output_pdf), option("user_password"),
                                              option("owner_password") or None, option("algorithm", "AES-256"))
                    download_name, message = "protected.pdf", "Your protected PDF is ready."
                elif tool_name == "unlock-pdf":
                    result = backend.unlock_pdf(input_path, str(output_pdf), option("password"))
                    download_name, message = "unlocked.pdf", "Your unlocked PDF is ready."
                elif tool_name == "compress-pdf":
                    result = backend.compress_pdf(input_path, str(output_pdf), option("level", "medium"))
                    download_name, message = "compressed.pdf", "Your compressed PDF is ready."
                elif tool_name == "watermark-pdf":
                    image = save_upload(request.files.get("image"), job_path, 1) if request.files.get("image") else None
                    result = backend.watermark_pdf(
                        input_path, str(output_pdf), text=option("text", "CONFIDENTIAL"),
                        rotation=option("rotation", "45"), opacity=float(option("opacity", "30")) / 100,
                        color_hex=option("color_hex", "#EF233C"), image_path=image,
                        pages=option("pages", "all"),
                    )
                    download_name, message = "watermarked.pdf", "Your watermarked PDF is ready."
                elif tool_name == "pdf-to-ppt":
                    result = backend.pdf_to_ppt(input_path, str(job_path / "result.pptx"),
                                                dpi=option("dpi", "150"),
                                                widescreen=option("widescreen", "true") == "true")
                    output_pdf = job_path / "result.pptx"
                    download_name, message = "converted.pptx", "Your PowerPoint file is ready."
                elif tool_name == "pdf-to-word":
                    result = backend.pdf_to_word(input_path, str(job_path / "result.docx"))
                    output_pdf = job_path / "result.docx"
                    download_name, message = "converted.docx", "Your Word document is ready."
                elif tool_name == "pdf-to-image":
                    out_dir = job_path / "images"
                    result = backend.pdf_to_images(
                        input_path, str(out_dir), option("img_format", "png"),
                        option("dpi", "150"), option("pages", "all"),
                    )
                    output_pdf = job_path / "images.zip"
                    with zipfile.ZipFile(output_pdf, "w", zipfile.ZIP_DEFLATED) as archive:
                        for file_path in result["files"]:
                            archive.write(file_path, arcname=Path(file_path).name)
                    download_name, message = "pdf_images.zip", f"Exported {result['count']} images."
                elif tool_name == "ocr":
                    extension = "pdf" if option("output_format") == "pdf" else "txt"
                    output_pdf = job_path / f"ocr_result.{extension}"
                    result = backend.ocr_pdf(
                        input_path, str(output_pdf), option("output_format", "txt"),
                        option("language", "eng"), option("dpi", "300"), option("pages", "all"),
                    )
                    download_name, message = f"ocr_result.{extension}", "OCR processing is complete."
                elif tool_name == "extract-text":
                    result = backend.extract_text_from_pdf(input_path, option("pages", "all"))
                    output_pdf = job_path / "extracted_text.txt"
                    output_pdf.write_text(result["text"], encoding="utf-8")
                    download_name, message = "extracted_text.txt", "Text extraction is complete."
                elif tool_name == "rotate-pdf":
                    result = backend.rotate_pdf(input_path, str(output_pdf), option("angle", "90"),
                                                option("page_selection", "all"))
                    download_name, message = "rotated.pdf", "Your rotated PDF is ready."
                elif tool_name == "delete-pages":
                    result = backend.delete_pages(input_path, str(output_pdf), option("pages_to_delete"))
                    download_name, message = "pages_removed.pdf", "Your updated PDF is ready."
                elif tool_name == "reorder-pages":
                    result = backend.reorder_pages(input_path, str(output_pdf), option("page_order"))
                    download_name, message = "reordered.pdf", "Your reordered PDF is ready."
                elif tool_name == "pdf-information":
                    result = backend.get_pdf_info(input_path)
                    shutil.rmtree(job_path, ignore_errors=True)
                    return jsonify(message="PDF information loaded.", result=public_result(result))
                elif tool_name == "update-metadata":
                    metadata = {key: option(key) for key in ("title", "author", "subject", "keywords")}
                    result = backend.update_pdf_metadata(input_path, str(output_pdf), metadata)
                    download_name, message = "updated_metadata.pdf", "Your updated PDF is ready."
                elif tool_name == "pdf-preview":
                    page_number = int(option("page_number", "1")) - 1
                    zoom = float(option("zoom", "1"))
                    if not 0.5 <= zoom <= 3:
                        raise ValueError("Preview zoom must be between 0.5 and 3.")
                    image = backend.render_pdf_page_image(input_path, page_number, zoom)
                    image_buffer = io.BytesIO()
                    image.save(image_buffer, format="PNG")
                    result = {
                        "page_number": page_number + 1,
                        "image": "data:image/png;base64," + __import__("base64").b64encode(
                            image_buffer.getvalue()
                        ).decode("ascii"),
                    }
                    shutil.rmtree(job_path, ignore_errors=True)
                    return jsonify(message="PDF page rendered.", result=result)
                download_path = output_pdf

            elif tool_name == "ppt-to-pdf":
                input_path = save_upload(primary_upload, job_path)
                result = backend.ppt_to_pdf(input_path, str(output_pdf))
                download_name, message = "converted.pdf", "Your PDF is ready."
                download_path = output_pdf
            elif tool_name == "word-to-pdf":
                input_path = save_upload(primary_upload, job_path)
                result = backend.word_to_pdf(input_path, str(output_pdf))
                download_name, message = "converted.pdf", "Your PDF is ready."
                download_path = output_pdf
            else:
                shutil.rmtree(job_path, ignore_errors=True)
                return jsonify(error="That tool is not available."), 404

            return output_response(job_path, result, message, download_path, download_name)
        except (ValueError, OSError, RuntimeError, IndexError) as error:
            shutil.rmtree(job_path, ignore_errors=True)
            return jsonify(error=str(error)), 400
        except Exception:
            shutil.rmtree(job_path, ignore_errors=True)
            app.logger.exception("PDF tool failed: %s", tool_name)
            return jsonify(error="The operation failed unexpectedly. Check the server log for details."), 500

    @app.get("/download/<token>")
    @signed_in
    def download_file(token):
        cleanup_old_jobs()
        item = app.extensions["downloads"].get(token)
        if not item or item["owner"] != current_user()["username"]:
            abort(404)
        path = Path(item["path"])
        if not path.is_file() or not path.resolve().is_relative_to(Path(item["directory"]).resolve()):
            abort(404)
        return send_file(path, as_attachment=True, download_name=item["name"])

    @app.get("/api/admin/users")
    @admin_only
    def admin_users():
        return jsonify(users=account_store.list_users())

    @app.post("/api/admin/invitations")
    @admin_only
    def create_invitation():
        try:
            token = account_store.create_invitation(current_user())
            return jsonify(invitation=token, expires_in_days=7)
        except auth_store.AuthenticationError as error:
            return jsonify(error=str(error)), 400

    @app.post("/api/admin/users/<username>/enabled")
    @admin_only
    def change_user_status(username):
        try:
            enabled = request.get_json(silent=True).get("enabled")
            if not isinstance(enabled, bool):
                raise ValueError("Choose whether the account should be enabled.")
            account_store.set_user_enabled(current_user(), username, enabled)
            return jsonify(success=True)
        except (auth_store.AuthenticationError, ValueError, AttributeError) as error:
            return jsonify(error=str(error)), 400

    @app.post("/api/admin/users/<username>/password")
    @admin_only
    def reset_user_password(username):
        try:
            password = (request.get_json(silent=True) or {}).get("password")
            account_store.reset_password(current_user(), username, password)
            return jsonify(success=True)
        except (auth_store.AuthenticationError, ValueError) as error:
            return jsonify(error=str(error)), 400

    @app.errorhandler(413)
    def upload_too_large(_error):
        return jsonify(error="Files must be 100 MB or smaller."), 413

    return app


app = create_app()


if __name__ == "__main__":
    print("PDF Tools is starting at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
