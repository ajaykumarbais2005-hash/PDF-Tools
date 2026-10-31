"""
PDF TOOLS - Backend Processing Engine
Handles all PDF, Word, PowerPoint, Image, and OCR operations.
"""

import os
import sys
import io
import math
import shutil
import subprocess
import tempfile
from datetime import datetime
from xml.sax.saxutils import escape
from PIL import Image

# Core PDF libraries
import pymupdf  # PyMuPDF
import pypdf
from reportlab.lib import pagesizes
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Office formats
import docx
import pptx
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt


# ==========================================
# HELPER UTILITIES
# ==========================================

def _paths_match(path_a, path_b):
    return os.path.normcase(os.path.abspath(path_a)) == os.path.normcase(os.path.abspath(path_b))


def _prepare_output_path(input_path, output_path):
    """Write beside the source first when replacing the source file itself."""
    if not _paths_match(input_path, output_path):
        return output_path
    folder = os.path.dirname(os.path.abspath(output_path))
    suffix = os.path.splitext(output_path)[1] or ".pdf"
    descriptor, temp_path = tempfile.mkstemp(prefix=".mits_pdf_", suffix=suffix, dir=folder)
    os.close(descriptor)
    os.remove(temp_path)
    return temp_path


def _finish_output_path(temp_path, output_path):
    if not _paths_match(temp_path, output_path):
        os.replace(temp_path, output_path)


def _remove_temporary_output(temp_path, output_path):
    if not _paths_match(temp_path, output_path) and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


def format_file_size(size_in_bytes):
    """Format bytes to human readable string (KB, MB, GB)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


def parse_page_ranges(range_str, total_pages):
    """Parse page expressions such as ``1-3, 5``, ``odd``, or ``reverse``.

    Page numbers are one-based in the expression and zero-based in the result.
    The order entered by the user is retained, and duplicate pages are removed.
    """
    if total_pages < 1:
        raise ValueError("The PDF does not contain any pages.")

    expression = (range_str or "all").strip().lower()
    if expression in ("", "all"):
        return list(range(total_pages))
    if expression == "odd":
        return list(range(0, total_pages, 2))
    if expression == "even":
        return list(range(1, total_pages, 2))
    if expression == "reverse":
        return list(reversed(range(total_pages)))

    selected = []
    seen = set()
    for item in expression.split(","):
        item = item.strip()
        if not item:
            raise ValueError("Page ranges cannot contain an empty item.")

        if "-" in item:
            if item.count("-") != 1:
                raise ValueError(f"Invalid page range: {item!r}.")
            start_text, end_text = (part.strip() for part in item.split("-", 1))
            if (start_text and not start_text.isdigit()) or (end_text and not end_text.isdigit()):
                raise ValueError(f"Invalid page range: {item!r}.")
            if not start_text and not end_text:
                raise ValueError(f"Invalid page range: {item!r}.")
            first = int(start_text) if start_text else 1
            last = int(end_text) if end_text else total_pages
            if first < 1 or last > total_pages:
                raise ValueError(f"Page range {item!r} is outside the PDF's 1-{total_pages} page range.")
            if first > last:
                raise ValueError(f"Page range {item!r} must start before it ends.")
            candidates = range(first - 1, last)
        else:
            if not item.isdigit():
                raise ValueError(f"Invalid page number: {item!r}.")
            page_number = int(item)
            if page_number < 1 or page_number > total_pages:
                raise ValueError(f"Page {page_number} is outside the PDF's 1-{total_pages} page range.")
            candidates = (page_number - 1,)

        for page_index in candidates:
            if page_index not in seen:
                selected.append(page_index)
                seen.add(page_index)

    if not selected:
        raise ValueError("No pages were selected.")
    return selected


def open_file_in_system(file_path):
    """Open a file with the default Windows application."""
    if os.path.exists(file_path):
        os.startfile(os.path.normpath(file_path))


def reveal_in_explorer(file_path):
    """Reveal a file or folder in Windows File Explorer."""
    path = os.path.normpath(file_path)
    if os.path.isfile(path):
        subprocess.run(["explorer.exe", f"/select,{path}"])
    elif os.path.isdir(path):
        subprocess.run(["explorer.exe", path])


# ==========================================
# 1. CREATE PDF
# ==========================================

def create_pdf(output_path, title="Untitled Document", author="PDF Tools User",
               text_content="", page_size="A4", orientation="portrait",
               image_path=None, font_size=11):
    """Create a PDF with escaped text, optional image, and page settings."""
    page_key = (page_size or "A4").strip().lower()
    if page_key not in ("a4", "letter"):
        raise ValueError("Page size must be A4 or Letter.")
    psize = pagesizes.A4 if page_key == "a4" else pagesizes.letter
    if (orientation or "portrait").strip().lower() == "landscape":
        psize = pagesizes.landscape(psize)
    if not 6 <= int(font_size) <= 72:
        raise ValueError("Font size must be between 6 and 72 points.")
    if image_path and not os.path.isfile(image_path):
        raise FileNotFoundError(f"The selected image does not exist: {image_path}")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=psize,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=24, leading=28, textColor=HexColor("#101B42"), spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "DocMeta", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=10, leading=14, textColor=HexColor("#667085"), spaceAfter=18,
    )
    body_style = ParagraphStyle(
        "DocBody", parent=styles["Normal"], fontName="Helvetica",
        fontSize=int(font_size), leading=int(font_size) + 4,
        textColor=HexColor("#111827"), spaceAfter=10,
    )

    story = []
    if title:
        story.append(Paragraph(escape(str(title)), title_style))
    meta_text = f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if author:
        meta_text = f"Author: {author}  •  " + meta_text
    story.append(Paragraph(escape(meta_text), meta_style))

    if image_path:
        with Image.open(image_path) as image:
            orig_w, orig_h = image.size
        if not orig_w or not orig_h:
            raise ValueError("The selected image has invalid dimensions.")
        max_w, max_h = psize[0] - 108, 240
        scale = min(max_w / orig_w, max_h / orig_h, 1.0)
        story.append(RLImage(image_path, width=orig_w * scale, height=orig_h * scale))
        story.append(Spacer(1, 14))

    for paragraph in str(text_content or "").split("\n"):
        if paragraph.strip():
            story.append(Paragraph(escape(paragraph), body_style))
        else:
            story.append(Spacer(1, 8))
    doc.build(story)
    return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}


# ==========================================
# 2. PDF MERGER
# ==========================================

def merge_pdfs(file_paths, output_path):
    """Combine valid PDF files in the supplied order and add bookmarks."""
    if len(file_paths) < 2:
        raise ValueError("At least 2 PDF files are required to merge.")
    missing = [path for path in file_paths if not os.path.isfile(path)]
    if missing:
        raise FileNotFoundError("One or more selected PDF files no longer exist.")

    doc_out = pymupdf.open()
    toc = []
    current_page = 0
    try:
        for path in file_paths:
            with pymupdf.open(path) as doc_in:
                if len(doc_in) == 0:
                    raise ValueError(f"The PDF has no pages: {os.path.basename(path)}")
                doc_out.insert_pdf(doc_in)
                toc.append([1, os.path.splitext(os.path.basename(path))[0], current_page + 1])
                current_page += len(doc_in)
        if not current_page:
            raise ValueError("No PDF pages were available to merge.")
        doc_out.set_toc(toc)
        doc_out.save(output_path, garbage=4, deflate=True)
    finally:
        doc_out.close()

    return {
        "success": True,
        "output_path": output_path,
        "total_pages": current_page,
        "file_size": os.path.getsize(output_path),
    }


# ==========================================
# 3. PDF SPLIT
# ==========================================

def split_pdf(input_path, output_dir, mode="all", page_ranges=None, chunk_size=1):
    """Split a PDF into single pages, selected ranges, or fixed-size chunks."""
    if mode not in ("all", "range", "chunk"):
        raise ValueError("Choose a valid split mode.")
    if mode == "range" and not str(page_ranges or "").strip():
        raise ValueError("Enter the page range to extract.")
    if mode == "chunk":
        chunk_size = int(chunk_size)
        if chunk_size < 1:
            raise ValueError("Chunk size must be at least one page.")

    os.makedirs(output_dir, exist_ok=True)
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    if total_pages < 1:
        doc.close()
        raise ValueError("The PDF does not contain any pages.")
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    created_files = []
    try:
        if mode == "all":
            groups = [[index] for index in range(total_pages)]
            names = [f"{base_name}_page_{index + 1:03d}.pdf" for index in range(total_pages)]
        elif mode == "range":
            selected = parse_page_ranges(page_ranges, total_pages)
            clean_range = str(page_ranges).replace(" ", "").replace(",", "_")
            groups = [selected]
            names = [f"{base_name}_pages_{clean_range}.pdf"]
        else:
            groups = [list(range(start, min(start + chunk_size, total_pages)))
                      for start in range(0, total_pages, chunk_size)]
            names = [
                f"{base_name}_part_{part:03d}_pages_{pages[0] + 1}-{pages[-1] + 1}.pdf"
                for part, pages in enumerate(groups, start=1)
            ]

        existing = [
            os.path.join(output_dir, filename)
            for filename in names
            if os.path.exists(os.path.join(output_dir, filename))
        ]
        if existing:
            preview = "\n".join(existing[:5])
            if len(existing) > 5:
                preview += f"\n...and {len(existing) - 5} more"
            raise FileExistsError(
                "Split output would overwrite existing file(s). Choose another folder or move these files first:\n"
                + preview
            )

        for pages, filename in zip(groups, names):
            output_doc = pymupdf.open()
            try:
                for page_index in pages:
                    output_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
                output_file = os.path.join(output_dir, filename)
                output_doc.save(output_file, garbage=4, deflate=True)
                created_files.append(output_file)
            finally:
                output_doc.close()
    finally:
        doc.close()

    return {"success": True, "files": created_files, "count": len(created_files)}


# ==========================================
# 4. PDF LOCK (ENCRYPT)
# ==========================================

def lock_pdf(input_path, output_path, user_password, owner_password=None, algorithm="AES-256"):
    """Encrypt a PDF with a user password."""
    if not user_password:
        raise ValueError("Password cannot be empty.")
    temp_path = _prepare_output_path(input_path, output_path)
    try:
        with open(input_path, "rb") as source_file:
            reader = pypdf.PdfReader(source_file)
            writer = pypdf.PdfWriter()
            writer.append(reader)
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_password or user_password,
                algorithm=algorithm,
            )
            with open(temp_path, "wb") as output_file:
                writer.write(output_file)
        _finish_output_path(temp_path, output_path)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}


# ==========================================
# 5. PDF UNLOCK (DECRYPT)
# ==========================================

def unlock_pdf(input_path, output_path, password):
    """Remove encryption from a PDF when the supplied password is valid."""
    temp_path = _prepare_output_path(input_path, output_path)
    try:
        with open(input_path, "rb") as source_file:
            reader = pypdf.PdfReader(source_file)
            if reader.is_encrypted and reader.decrypt(password) == 0:
                raise ValueError("Incorrect password. Could not decrypt the PDF.")
            writer = pypdf.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(temp_path, "wb") as output_file:
                writer.write(output_file)
        _finish_output_path(temp_path, output_path)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}


# ==========================================
# 6. PDF COMPRESSION
# ==========================================

def compress_pdf(input_path, output_path, level="medium"):
    """Reduce PDF size with stream cleanup and optional image recompression."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError("Select an existing PDF file to compress.")
    level = (level or "medium").strip().lower()
    if level not in ("low", "medium", "high"):
        raise ValueError("Compression level must be Low, Medium, or High.")

    orig_size = os.path.getsize(input_path)
    temp_path = _prepare_output_path(input_path, output_path)
    doc = pymupdf.open(input_path)
    optimized_xrefs = set()
    try:
        if level == "high":
            for page in doc:
                for image_info in page.get_images(full=True):
                    xref = image_info[0]
                    if not xref or xref in optimized_xrefs:
                        continue
                    optimized_xrefs.add(xref)
                    try:
                        extracted = doc.extract_image(xref)
                        original_bytes = extracted["image"]
                        with Image.open(io.BytesIO(original_bytes)) as source_image:
                            source_image.load()
                            image = source_image.copy()
                        if image.width > 1600 or image.height > 1600:
                            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

                        buffer = io.BytesIO()
                        has_alpha = "A" in image.getbands() or "transparency" in image.info
                        if has_alpha:
                            image.convert("RGBA").save(buffer, format="PNG", optimize=True)
                        else:
                            image.convert("RGB").save(
                                buffer, format="JPEG", quality=68, optimize=True, progressive=True
                            )
                        compressed_bytes = buffer.getvalue()
                        if len(compressed_bytes) < len(original_bytes):
                            page.replace_image(xref, stream=compressed_bytes)
                    except Exception:
                        # Some embedded images (for example masks) cannot safely be recompressed.
                        continue

        save_options = {"garbage": 4, "deflate": True, "clean": True}
        if level == "high":
            save_options.update({"deflate_images": True, "deflate_fonts": True})
        elif level == "low":
            save_options = {"garbage": 3, "deflate": True}
        doc.save(temp_path, **save_options)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    finally:
        doc.close()
    _finish_output_path(temp_path, output_path)

    new_size = os.path.getsize(output_path)
    saved_bytes = max(0, orig_size - new_size)
    saved_pct = (saved_bytes / orig_size * 100) if orig_size else 0
    return {
        "success": True,
        "output_path": output_path,
        "orig_size": orig_size,
        "new_size": new_size,
        "saved_bytes": saved_bytes,
        "saved_pct": saved_pct,
        "images_checked": len(optimized_xrefs) if level == "high" else 0,
    }


# ==========================================
# 7. WATERMARK PDF
# ==========================================

def watermark_pdf(input_path, output_path, text="CONFIDENTIAL",
                  font_size=48, opacity=0.30, rotation=45,
                  color_hex="#EF233C", image_path=None,
                  underlay=False, pages="all"):
    """Add a text or image watermark to selected pages of a PDF."""
    if image_path and not os.path.isfile(image_path):
        raise FileNotFoundError("The selected watermark image does not exist.")
    if not image_path and not str(text or "").strip():
        raise ValueError("Enter watermark text or select a watermark image.")
    if not 0 <= float(opacity) <= 1:
        raise ValueError("Watermark opacity must be between 0 and 1.")
    c_hex = str(color_hex).strip().lstrip("#")
    if len(c_hex) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in c_hex):
        raise ValueError("Choose a valid six-digit hex color for the watermark.")

    with pymupdf.open(input_path) as doc:
        total_pages = len(doc)
    target_pages = set(parse_page_ranges(pages, total_pages))
    r, g, b = (int(c_hex[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    temp_path = _prepare_output_path(input_path, output_path)
    writer = pypdf.PdfWriter()
    try:
        with open(input_path, "rb") as source_file:
            reader = pypdf.PdfReader(source_file)
            for idx, page in enumerate(reader.pages):
                if idx not in target_pages:
                    writer.add_page(page)
                    continue
                width, height = float(page.mediabox.width), float(page.mediabox.height)
                wm_buf = io.BytesIO()
                c = canvas.Canvas(wm_buf, pagesize=(width, height))
                c.saveState()
                c.translate(width / 2, height / 2)
                c.rotate(float(rotation))
                if image_path:
                    with Image.open(image_path) as image:
                        im_w, im_h = image.size
                    if not im_w or not im_h:
                        raise ValueError("The watermark image has invalid dimensions.")
                    max_dim = min(width, height) * 0.5
                    scale = min(max_dim / im_w, max_dim / im_h)
                    c.setFillAlpha(float(opacity))
                    c.drawImage(
                        image_path, -im_w * scale / 2, -im_h * scale / 2,
                        width=im_w * scale, height=im_h * scale, mask="auto",
                    )
                else:
                    c.setFillColor(Color(r, g, b, alpha=float(opacity)))
                    c.setFont("Helvetica-Bold", int(font_size))
                    c.drawCentredString(0, -int(font_size) / 3, str(text))
                c.restoreState()
                c.save()
                wm_buf.seek(0)
                wm_page = pypdf.PdfReader(wm_buf).pages[0]
                if underlay:
                    writer.add_page(wm_page)
                    writer.pages[-1].merge_page(page)
                else:
                    writer.add_page(page)
                    writer.pages[-1].merge_page(wm_page)
            with open(temp_path, "wb") as output_file:
                writer.write(output_file)
        _finish_output_path(temp_path, output_path)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    return {
        "success": True,
        "output_path": output_path,
        "pages_watermarked": len(target_pages),
    }


# ==========================================
# 8. PDF TO PPT
# ==========================================

def _ensure_tesseract_on_path():
    """Make a standard Windows Tesseract installation discoverable by PyMuPDF."""
    executable = shutil.which("tesseract")
    if executable:
        return executable

    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
        ]
        executable = next((path for path in candidates if os.path.isfile(path)), None)
        if executable:
            directory = os.path.dirname(executable)
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            return executable
    return None


def pdf_to_ppt(input_path, output_path, dpi=150, widescreen=True, language="eng"):
    """
    Convert PDF text into editable PowerPoint text boxes, using OCR for scanned pages.
    """
    dpi = int(dpi)
    if not 36 <= dpi <= 600:
        raise ValueError("Resolution must be between 36 and 600 DPI.")
    language = str(language or "").strip()
    if not language:
        raise ValueError("Enter a Tesseract language code, such as 'eng'.")

    doc = pymupdf.open(input_path)
    prs = pptx.Presentation()

    if widescreen:
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    else:
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

    slide_w = prs.slide_width
    slide_h = prs.slide_height
    blank_layout = prs.slide_layouts[6]
    text_box_count = 0
    ocr_pages = 0

    try:
        for page in doc:
            source_text = page.get_text("text").strip()
            if page.get_images(full=True) or not source_text:
                if not _ensure_tesseract_on_path():
                    raise RuntimeError(
                        "This PDF needs OCR to extract scanned text. Install Tesseract OCR "
                        "and the selected language data, then try again."
                    )
                tessdata = _find_tessdata_dir(language)
                if not tessdata:
                    raise RuntimeError(
                        f"Tesseract language data for '{language}' is not installed."
                    )
                ocr_pages += 1
                textpage = page.get_textpage_ocr(
                    language=language,
                    dpi=dpi,
                    full=not bool(source_text),
                    tessdata=tessdata,
                )
                page_dict = page.get_text("dict", textpage=textpage)
            else:
                page_dict = page.get_text("dict")

            slide = prs.slides.add_slide(blank_layout)
            page_rect = page.rect
            fit = min(
                slide_w / (page_rect.width * 12700),
                slide_h / (page_rect.height * 12700),
            )
            page_w = page_rect.width * fit * 12700
            page_h = page_rect.height * fit * 12700
            offset_x = (slide_w - page_w) / 2
            offset_y = (slide_h - page_h) / 2

            for block in page_dict["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        x0, y0, x1, y1 = span["bbox"]
                        left = offset_x + x0 * fit * 12700
                        top = offset_y + y0 * fit * 12700
                        width = max((x1 - x0) * fit * 12700, Inches(0.08))
                        height = max((y1 - y0) * fit * 12700, Inches(0.08))
                        shape = slide.shapes.add_textbox(left, top, width, height)
                        frame = shape.text_frame
                        frame.clear()
                        frame.word_wrap = False
                        frame.margin_left = 0
                        frame.margin_right = 0
                        frame.margin_top = 0
                        frame.margin_bottom = 0
                        frame.vertical_anchor = MSO_ANCHOR.TOP
                        paragraph = frame.paragraphs[0]
                        paragraph.space_before = Pt(0)
                        paragraph.space_after = Pt(0)
                        run = paragraph.add_run()
                        run.text = text
                        text_box_count += 1
                        font = run.font
                        font.size = Pt(max(1, span.get("size", 10) * fit))
                        flags = span.get("flags", 0)
                        font.bold = bool(flags & 16)
                        font.italic = bool(flags & 2)
                        color = span.get("color", 0)
                        font.color.rgb = RGBColor(
                            (color >> 16) & 0xFF,
                            (color >> 8) & 0xFF,
                            color & 0xFF,
                        )
    finally:
        doc.close()

    prs.save(output_path)

    return {
        "success": True,
        "output_path": output_path,
        "slides_count": len(prs.slides),
        "text_boxes": text_box_count,
        "ocr_pages": ocr_pages,
    }


# ==========================================
# 9. PDF TO WORD
# ==========================================

def pdf_to_word(input_path, output_path):
    """
    Extract structured text blocks, headings, and paragraphs from PDF
    into a Word (.docx) document.
    """
    doc = pymupdf.open(input_path)
    word_doc = docx.Document()
    
    for page_idx, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if b[6] == 0:  # text block
                text = b[4].strip()
                if text:
                    word_doc.add_paragraph(text)
        if page_idx < len(doc) - 1:
            word_doc.add_page_break()
            
    doc.close()
    word_doc.save(output_path)
    
    return {
        "success": True,
        "output_path": output_path,
        "file_size": os.path.getsize(output_path)
    }


# ==========================================
# 10. PDF TO IMAGE
# ==========================================

def pdf_to_images(input_path, output_dir, img_format="png", dpi=150, pages="all"):
    """Convert selected PDF pages to PNG, JPEG, or WebP images."""
    img_format = (img_format or "png").strip().lower()
    if img_format == "jpg":
        img_format = "jpeg"
    if img_format not in ("png", "jpeg", "webp"):
        raise ValueError("Image format must be PNG, JPEG, or WebP.")
    dpi = int(dpi)
    if not 36 <= dpi <= 600:
        raise ValueError("Resolution must be between 36 and 600 DPI.")

    os.makedirs(output_dir, exist_ok=True)
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    target_pages = parse_page_ranges(pages, total_pages)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    extension = "jpg" if img_format == "jpeg" else img_format
    output_files = [
        os.path.join(output_dir, f"{base_name}_page_{page_index + 1:03d}.{extension}")
        for page_index in target_pages
    ]
    existing = [path for path in output_files if os.path.exists(path)]
    if existing:
        doc.close()
        preview = "\n".join(existing[:5])
        if len(existing) > 5:
            preview += f"\n...and {len(existing) - 5} more"
        raise FileExistsError(
            "Image export would overwrite existing file(s). Choose another folder or move these files first:\n"
            + preview
        )

    try:
        for page_index, out_file in zip(target_pages, output_files):
            pix = doc[page_index].get_pixmap(dpi=dpi, alpha=False)
            if img_format == "webp":
                pix.pil_save(out_file, quality=90, optimize=True)
            elif img_format == "jpeg":
                pix.save(out_file, output="jpg", jpg_quality=92)
            else:
                pix.save(out_file, output="png")
    finally:
        doc.close()
    return {"success": True, "files": output_files, "count": len(output_files)}


def _find_tessdata_dir(language):
    """Find installed Tesseract language data even when its executable is not on PATH."""
    language_files = [f"{code}.traineddata" for code in language.split("+")]
    candidates = []
    configured = os.environ.get("TESSDATA_PREFIX")
    if configured:
        candidates.append(configured)
    executable = shutil.which("tesseract")
    if executable:
        candidates.append(os.path.join(os.path.dirname(executable), "tessdata"))
    if sys.platform == "win32":
        for program_files in (
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        ):
            candidates.append(os.path.join(program_files, "Tesseract-OCR", "tessdata"))
        local_programs = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Programs", "Tesseract-OCR", "tessdata",
        )
        if os.path.dirname(local_programs):
            candidates.append(local_programs)

    for candidate in candidates:
        if os.path.isdir(candidate) and all(
            os.path.isfile(os.path.join(candidate, filename))
            for filename in language_files
        ):
            return candidate
    return None


# ==========================================
# 11. OCR (TEXT RECOGNITION)
# ==========================================

def ocr_pdf(input_path, output_path, output_format="txt", language="eng", dpi=300, pages="all"):
    """Extract text from PDFs and create a searchable PDF for scanned pages.

    Scanned pages require Tesseract and its language data. Existing digital text
    is preserved without requiring OCR.
    """
    output_format = (output_format or "txt").strip().lower()
    if output_format not in ("txt", "pdf"):
        raise ValueError("OCR output format must be TXT or PDF.")
    dpi = int(dpi)
    if not 150 <= dpi <= 600:
        raise ValueError("OCR resolution must be between 150 and 600 DPI.")
    language = str(language or "").strip()
    if not language:
        raise ValueError("Enter a Tesseract language code, such as 'eng'.")

    doc = pymupdf.open(input_path)
    output_doc = pymupdf.open() if output_format == "pdf" else None
    full_text = []
    has_ocr = False
    temp_output = _prepare_output_path(input_path, output_path) if output_format == "pdf" else None
    try:
        if doc.is_encrypted:
            raise ValueError("This PDF is password-protected. Unlock it before running OCR.")
        selected_pages = set(parse_page_ranges(pages, len(doc)))
        for page_index, page in enumerate(doc):
            if page_index not in selected_pages:
                if output_doc is not None:
                    output_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
                continue
            page_text = page.get_text("text").strip()
            if len(page_text) < 10:
                try:
                    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                    tessdata = _find_tessdata_dir(language)
                    ocr_bytes = pix.pdfocr_tobytes(language=language, tessdata=tessdata)
                    ocr_doc = pymupdf.open("pdf", ocr_bytes)
                    try:
                        page_text = ocr_doc[0].get_text("text").strip()
                        if output_doc is not None:
                            output_doc.insert_pdf(ocr_doc)
                    finally:
                        ocr_doc.close()
                    has_ocr = True
                except Exception as error:
                    if not page_text:
                        raise RuntimeError(
                            f"OCR could not process page {page_index + 1}. Install Tesseract OCR "
                            f"with the '{language}' language data, then try again."
                        ) from error
                    if output_doc is not None:
                        output_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
            elif output_doc is not None:
                output_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
            full_text.append(f"--- Page {page_index + 1} ---\n{page_text}\n")

        combined = "\n".join(full_text)
        if output_format == "pdf":
            output_doc.save(temp_output, garbage=4, deflate=True)
        else:
            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write(combined)
    except Exception:
        if temp_output and os.path.exists(temp_output):
            os.remove(temp_output)
        raise
    finally:
        if output_doc is not None:
            output_doc.close()
        doc.close()

    if temp_output:
        _finish_output_path(temp_output, output_path)
    return {
        "success": True,
        "output_path": output_path,
        "ocr_engine_used": has_ocr,
        "character_count": len(combined),
    }


# ==========================================
# 12. EXTRACT TEXT
# ==========================================

def extract_text_from_pdf(input_path, pages="all"):
    """
    Extract text from PDF pages and return detailed stats and text.
    """
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    target_pages = parse_page_ranges(pages, total_pages)
    
    extracted_pages = []
    total_chars = 0
    total_words = 0
    
    for p in target_pages:
        page = doc[p]
        text = page.get_text("text").strip()
        words = len(text.split())
        chars = len(text)
        total_chars += chars
        total_words += words
        extracted_pages.append(f"=== Page {p + 1} ===\n\n{text}\n")
        
    doc.close()
    full_text = "\n".join(extracted_pages)
    
    return {
        "success": True,
        "text": full_text,
        "word_count": total_words,
        "char_count": total_chars,
        "pages_extracted": len(target_pages)
    }


# ==========================================
# 13. PPT TO PDF
# ==========================================

def _libreoffice_executable():
    """Return a LibreOffice executable when one is available on this computer."""
    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    return next((candidate for candidate in candidates if candidate and os.path.isfile(candidate)), None)


def _convert_office_file_to_pdf(input_path, output_path):
    """Use LibreOffice for faithful Office conversion when it is installed."""
    executable = _libreoffice_executable()
    if not executable:
        return False
    with tempfile.TemporaryDirectory(prefix="mits_pdf_convert_") as temp_dir:
        result = subprocess.run(
            [executable, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, input_path],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        converted = os.path.join(temp_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
        if result.returncode != 0 or not os.path.isfile(converted):
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError("LibreOffice could not convert the document." + (f"\n{details}" if details else ""))
        shutil.copy2(converted, output_path)
    return True


def ppt_to_pdf(input_path, output_path):
    """Convert a PowerPoint file to PDF, preferring full Office rendering."""
    if _convert_office_file_to_pdf(input_path, output_path):
        with pymupdf.open(output_path) as result_doc:
            return {"success": True, "output_path": output_path, "slides_count": len(result_doc)}
    if os.path.splitext(input_path)[1].lower() != ".pptx":
        raise ValueError("Legacy .ppt files require LibreOffice. Save this presentation as .pptx or install LibreOffice.")

    prs = pptx.Presentation(input_path)
    psize = pagesizes.landscape(pagesizes.letter)
    c = canvas.Canvas(output_path, pagesize=psize)
    width, height = psize
    for slide_index, slide in enumerate(prs.slides):
        c.setFillColor(HexColor("#F8FAFC"))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(HexColor("#667085"))
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(width - 40, height - 35, f"Slide {slide_index + 1}")
        y = height - 70
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for paragraph in shape.text_frame.paragraphs:
                content = paragraph.text.strip()
                if not content:
                    continue
                is_title = y == height - 70
                c.setFont("Helvetica-Bold" if is_title else "Helvetica", 20 if is_title else 12)
                c.setFillColor(HexColor("#101B42" if is_title else "#111827"))
                wrapped = content[:90] if is_title else content[:110]
                c.drawString(50 if is_title else 60, y, wrapped)
                y -= 34 if is_title else 22
                if y < 60:
                    break
            if y < 60:
                break
        c.showPage()
    c.save()
    return {"success": True, "output_path": output_path, "slides_count": len(prs.slides)}


# ==========================================
# 14. WORD TO PDF
# ==========================================

def word_to_pdf(input_path, output_path):
    """Convert a Word file to PDF, preferring LibreOffice for full rendering."""
    if _convert_office_file_to_pdf(input_path, output_path):
        with pymupdf.open(output_path) as result_doc:
            return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}
    if os.path.splitext(input_path)[1].lower() != ".docx":
        raise ValueError("Legacy .doc files require LibreOffice. Save this document as .docx or install LibreOffice.")

    doc_in = docx.Document(input_path)
    pdf_doc = SimpleDocTemplate(
        output_path, pagesize=pagesizes.letter, leftMargin=54, rightMargin=54,
        topMargin=54, bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "WordHeading", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=HexColor("#101B42"), spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "WordBody", parent=styles["Normal"], fontName="Helvetica",
        fontSize=11, leading=15, textColor=HexColor("#111827"), spaceAfter=6,
    )
    story = []
    for paragraph in doc_in.paragraphs:
        text = paragraph.text.strip()
        if text:
            style = heading_style if paragraph.style.name.startswith("Heading") else body_style
            story.append(Paragraph(escape(text), style))
        else:
            story.append(Spacer(1, 6))

    # Preserve document tables in reading order after the paragraph content.
    for table in doc_in.tables:
        rows = [[escape(cell.text.replace("\n", "<br/>")) for cell in row.cells] for row in table.rows]
        if rows:
            report_table = Table(rows, repeatRows=1, hAlign="LEFT")
            report_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#D0D5DD")),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EEF2FF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([Spacer(1, 8), report_table, Spacer(1, 8)])

    pdf_doc.build(story)
    return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}


# ==========================================
# 15. ROTATE PDF
# ==========================================

def rotate_pdf(input_path, output_path, angle=90, page_selection="all"):
    """Rotate selected PDF pages by 90, 180, or 270 degrees."""
    angle = int(angle)
    if angle not in (90, 180, 270):
        raise ValueError("Rotation angle must be 90, 180, or 270 degrees.")
    temp_path = _prepare_output_path(input_path, output_path)
    doc = pymupdf.open(input_path)
    try:
        target_pages = parse_page_ranges(page_selection, len(doc))
        for page_index in target_pages:
            page = doc[page_index]
            page.set_rotation((page.rotation + angle) % 360)
        doc.save(temp_path, garbage=4, deflate=True)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    finally:
        doc.close()
    _finish_output_path(temp_path, output_path)
    return {"success": True, "output_path": output_path, "pages_rotated": len(target_pages)}


# ==========================================
# 16. DELETE PAGES
# ==========================================

def delete_pages(input_path, output_path, pages_to_delete):
    """Remove selected pages while retaining at least one page."""
    temp_path = _prepare_output_path(input_path, output_path)
    doc = pymupdf.open(input_path)
    try:
        total_pages = len(doc)
        del_indices = parse_page_ranges(pages_to_delete, total_pages)
        if len(del_indices) >= total_pages:
            raise ValueError("Cannot delete all pages of the document.")
        keep_indices = [index for index in range(total_pages) if index not in set(del_indices)]
        doc.select(keep_indices)
        doc.save(temp_path, garbage=4, deflate=True)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    finally:
        doc.close()
    _finish_output_path(temp_path, output_path)
    return {
        "success": True,
        "output_path": output_path,
        "pages_removed": len(del_indices),
        "pages_remaining": len(keep_indices),
    }


# ==========================================
# 17. REORDER PAGES
# ==========================================

def reorder_pages(input_path, output_path, page_order):
    """Reorder PDF pages using a sequence such as ``3, 1, 2, 4-10``."""
    temp_path = _prepare_output_path(input_path, output_path)
    doc = pymupdf.open(input_path)
    try:
        total_pages = len(doc)
        if isinstance(page_order, str):
            order_indices = parse_page_ranges(page_order, total_pages)
        else:
            order_indices = list(page_order)
            if any(not isinstance(page, int) or page < 0 or page >= total_pages for page in order_indices):
                raise ValueError(f"Page indexes must be between 0 and {total_pages - 1}.")
        if not order_indices:
            raise ValueError("Enter a valid page order.")
        if len(set(order_indices)) != len(order_indices):
            raise ValueError("A page can appear only once in the new order.")
        doc.select(order_indices)
        doc.save(temp_path, garbage=4, deflate=True)
        new_page_count = len(doc)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    finally:
        doc.close()
    _finish_output_path(temp_path, output_path)
    return {"success": True, "output_path": output_path, "new_page_count": new_page_count}


# ==========================================
# 18. PDF INFORMATION
# ==========================================

def get_pdf_info(input_path):
    """
    Extract rich document information and metadata.
    """
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    is_encrypted = doc.is_encrypted
    metadata = doc.metadata or {}
    
    first_page = doc[0] if total_pages > 0 else None
    width_pt = first_page.rect.width if first_page else 0
    height_pt = first_page.rect.height if first_page else 0
    width_mm = width_pt * 25.4 / 72.0
    height_mm = height_pt * 25.4 / 72.0
    
    file_size = os.path.getsize(input_path)
    
    info = {
        "file_name": os.path.basename(input_path),
        "file_path": input_path,
        "file_size_formatted": format_file_size(file_size),
        "file_size_bytes": file_size,
        "page_count": total_pages,
        "is_encrypted": is_encrypted,
        "dimensions_pt": f"{width_pt:.1f} × {height_pt:.1f} pt",
        "dimensions_mm": f"{width_mm:.1f} × {height_mm:.1f} mm",
        "title": metadata.get("title", "") or "Not specified",
        "author": metadata.get("author", "") or "Not specified",
        "subject": metadata.get("subject", "") or "Not specified",
        "keywords": metadata.get("keywords", "") or "Not specified",
        "creator": metadata.get("creator", "") or "Not specified",
        "producer": metadata.get("producer", "") or "Not specified",
        "creation_date": metadata.get("creationDate", "") or "Not specified",
        "mod_date": metadata.get("modDate", "") or "Not specified"
    }
    
    doc.close()
    return info


def update_pdf_metadata(input_path, output_path, metadata):
    """Update editable PDF metadata while preserving other metadata fields."""
    editable = ("title", "author", "subject", "keywords")
    temp_path = _prepare_output_path(input_path, output_path)
    try:
        with pymupdf.open(input_path) as doc:
            current = doc.metadata or {}
            updated = {
                key: current.get(key, "")
                for key in ("title", "author", "subject", "keywords", "creator", "producer", "creationDate", "modDate")
            }
            for key in editable:
                if key in metadata:
                    updated[key] = str(metadata[key] or "")
            doc.set_metadata(updated)
            doc.save(temp_path, garbage=4, deflate=True)
        _finish_output_path(temp_path, output_path)
    except Exception:
        _remove_temporary_output(temp_path, output_path)
        raise
    return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}


# ==========================================
# 19. PDF RENDERING / PREVIEW
# ==========================================

def render_pdf_page_image(input_path, page_num=0, zoom=1.0):
    """
    Render a PDF page to a PIL Image for high-definition preview in Tkinter.
    """
    doc = pymupdf.open(input_path)
    if page_num < 0 or page_num >= len(doc):
        doc.close()
        raise IndexError("Page index out of bounds.")
        
    page = doc[page_num]
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    doc.close()
    return img
