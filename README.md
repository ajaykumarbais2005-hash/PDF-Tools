# PDF Tools

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)

PDF Tools is a Windows desktop application with an optional local browser
interface. It can merge and split PDFs, manage pages, extract text, convert
documents, and process scanned pages with optional OCR. Files are processed on
your computer.

The **Create PDF** tool can include multiple selected images, placing each
image on its own PDF page.

The desktop interface uses Tkinter. The browser interface runs locally with
Flask and listens on `127.0.0.1`; it is not intended to be a public or
multi-device service.

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

PDF-to-PowerPoint creates editable text boxes, matches the source PDF page size
by default, and uses OCR for scanned pages. Widescreen and standard slide sizes
are also available. Scanned-page OCR requires Tesseract OCR and the selected
language data (English is `eng`). Text positioning is approximate and original
graphics are not included in the editable slides. PDF-to-Word preserves each
page's appearance with a page image background and editable, positioned text
boxes over extracted text. Editing text may change its alignment, and scanned
pages without an OCR text layer remain image-only. Office conversions use a built-in
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
python -m frontend.web_app
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

## Troubleshooting

- **OCR is unavailable:** Install Tesseract and the language data for the
  selected language. English uses the `eng` language code.
- **Office conversion looks different from the source:** Install LibreOffice
  for more faithful rendering. Legacy `.doc` and `.ppt` files require it.
- **A web result is no longer available:** Download results before they expire
  after two hours. Temporary files are cleaned up during later website
  activity.
- **The sign-in screen asks you to create an administrator:** Accounts are
  stored per Windows profile. The first launch under a Windows profile creates
  its local administrator account.

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

## Deploy the browser app separately

The browser app can be deployed with a static Vercel frontend and a Flask API
on Render. The desktop app and local browser interface remain available.

1. Deploy the repository to Render using the included `render.yaml` blueprint.
   The service uses a persistent disk for accounts, session signing data, and
   temporary processing files. The blueprint uses a paid Starter service
   because Render's free web services do not provide persistent disks.
2. Deploy the `frontend` directory as the Vercel project root.
3. The Vercel rewrites target `https://pdf-tools-api.onrender.com`. If Render
   assigns a different service URL, update the three backend destinations in
   `frontend/vercel.json` to that URL before deploying Vercel.
4. Open the Vercel URL. On first launch, create the administrator account.
   Use **Manage accounts** to create invitation codes for other users.

The Vercel frontend sends API requests through same-origin rewrites, so the
backend's secure session cookie is handled by the browser without exposing
cross-origin API access. Uploaded documents are processed on the Render
service, not on the user's computer. They are limited to 100 MB each and
temporary files are removed after two hours. Keep the Render persistent disk
enabled; deleting or replacing it removes account data.

Tesseract and LibreOffice are optional system packages and are not installed by
the default Render blueprint. OCR requires Tesseract and language data;
conversions that use LibreOffice may need a custom Render image with
LibreOffice installed.

## Output safety

Each file-producing tool writes to a temporary file, checks the result, and
publishes it only after validation. Replacing an existing output requires
confirmation, and a selected source file cannot be chosen as the output. Split
and image-export tools refuse to overwrite files already present in the chosen
destination folder.
