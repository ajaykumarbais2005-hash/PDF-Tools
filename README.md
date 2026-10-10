# PDF Tools

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)

A desktop and local web application for merging, splitting, compressing, converting,
and organizing PDF documents. Files are processed on your computer, with optional
OCR and Office-conversion support.

## Requirements

- Python 3.10 or newer
- The Python packages listed in `requirements.txt`
- Windows for the bundled app icon behavior and File Explorer shortcuts

Install the pinned Python dependencies from the project folder:

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt` pins the application and runtime dependency versions used
for validation. Update those pins together and run the test suite when upgrading
dependencies.

PDF-to-PowerPoint creates editable text boxes and uses OCR for scanned pages.
Scanned-page OCR requires Tesseract OCR and the selected language data (English
is `eng`). Text positioning is approximate and original graphics are not
included in the editable slides. Office conversions use a built-in
`.docx`/`.pptx` fallback; LibreOffice is optional for more faithful rendering
and is required for legacy `.doc` and `.ppt` files.

On Windows, the optional components can be installed separately with:

```powershell
winget install --id UB-Mannheim.TesseractOCR --exact
winget install --id TheDocumentFoundation.LibreOffice --exact
```

## Launch

From the project folder, run:

```powershell
python main.py
```

In VS Code, open this folder and choose **Run Application** from the Tasks menu,
or launch the **Run PDF Tools (main.py)** debug configuration.

## Launch the website locally

The project also includes a browser-based interface for the existing PDF tools.
Install the requirements above, then run:

```powershell
python web_app.py
```

Open `http://127.0.0.1:5000` in a browser. The website listens only on this
computer; it is not exposed to other devices or the public internet. The first
visit creates the administrator account. Administrators can issue one-time
invitations and manage accounts from **Manage accounts**. Desktop and website
accounts use the same local account database.

Uploaded files are processed locally and are limited to 100 MB each. Temporary
results expire after two hours and are removed on subsequent website activity;
download a result before it expires. OCR of scanned pages still requires Tesseract OCR and language data;
Office conversions may use the optional LibreOffice installation described
above.

## Authorized accounts

The first launch on a Windows user profile prompts you to create the local
administrator account. The administrator signs in and uses **Manage Users**
to issue a one-time registration invitation to each approved user. Users choose
their own username and password from **Create account with invitation** on the
sign-in screen. Invitations expire after seven days and are stored as hashes;
registration creates a standard user account, never an administrator account.
Administrators can also add accounts directly, reset passwords, and disable
accounts. There is no unrestricted public sign-up or demo OTP bypass. Passwords
must be at least 12 characters; the account database stores salted
PBKDF2-HMAC-SHA256 hashes, not plain-text passwords. Five failed sign-in
attempts lock that username for 60 seconds, and an idle signed-in session locks
after 15 minutes.

For compatibility with existing installations, the local account database is
stored at
`%LOCALAPPDATA%\MITS PDF Utility\accounts.sqlite3` for the current Windows
account. This is a per-Windows-account desktop sign-in gate, not a college-wide
identity service: another Windows profile has its own first-run setup. Anyone
with access to the same already-unlocked Windows profile can use its signed-in
desktop session, so protect the Windows account and lock the PC when away.

The app icon is provided as `mits_pdf_icon.png` and `mits_pdf_icon.ico`.

## Output safety

Each file-producing tool writes to a temporary file, checks the result, and
publishes it only after validation. Replacing an existing output requires
confirmation, and a selected source file cannot be chosen as the output. Split
and image-export tools refuse to overwrite files already present in the chosen
destination folder.
