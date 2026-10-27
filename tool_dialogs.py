"""
PDF TOOLS - Tool Dialogs & User Interfaces
Modal dialogs for all 19 PDF and Office tools.
"""

import os
import queue
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

import backend
import pymupdf

# Color palette matching PDF Tools
BG = "#F5F7FF"
WHITE = "#FFFFFF"
PRIMARY = "#6D4CF5"
PRIMARY_HOVER = "#5036C9"
DARK = "#211B3A"
TEXT = "#29263D"
SECONDARY = "#706C85"
BORDER = "#E5E1F0"
RED = "#EF233C"
CARD_BG = "#FFFFFF"
SUCCESS_GREEN = "#10B981"


class BaseToolDialog:
    """Base class providing common layout, styling, and background thread execution."""

    def __init__(self, parent, title, subtitle, width=640, height=620):
        self.parent = parent
        self.title_text = title
        self.subtitle_text = subtitle
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{title} - PDF Tools")
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.minsize(560, 480)
        self.dialog.configure(bg=BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.center_window(width, height)

        # Main container
        self.main_container = tk.Frame(self.dialog, bg=BG)
        self.main_container.pack(fill="both", expand=True)

        # Header banner
        self.build_header()

        # Scrollable content frame
        self.canvas = tk.Canvas(self.main_container, bg=BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg=BG)

        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(18, 0), pady=(12, 12))
        self.scrollbar.pack(side="right", fill="y", padx=(0, 6), pady=(12, 12))

        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.content_window, width=e.width))
        
        # Mousewheel scroll binding
        self.dialog.bind("<MouseWheel>", self._on_mousewheel)

        # Status / Action bar at bottom
        self.footer_frame = tk.Frame(self.dialog, bg=WHITE, height=65, highlightbackground=BORDER, highlightthickness=1)
        self.footer_frame.pack(fill="x", side="bottom")
        self.footer_frame.pack_propagate(False)

        self.status_label = tk.Label(self.footer_frame, text="", font=("Arial", 10), fg=SECONDARY, bg=WHITE)
        self.status_label.pack(side="left", padx=20)

        self.action_btn = tk.Button(
            self.footer_frame,
            text="Process",
            font=("Arial", 11, "bold"),
            fg=WHITE,
            bg=PRIMARY,
            activebackground=PRIMARY_HOVER,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.execute
        )
        self.action_btn.pack(side="right", padx=20)

        self.cancel_btn = tk.Button(
            self.footer_frame,
            text="Close",
            font=("Arial", 10),
            fg=SECONDARY,
            bg=WHITE,
            activebackground="#F3F4F6",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=8,
            command=self.dialog.destroy
        )
        self.cancel_btn.pack(side="right", padx=6)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def center_window(self, width, height):
        self.dialog.update_idletasks()
        try:
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            x = px + max(0, (pw - width) // 2)
            y = py + max(0, (ph - height) // 2)
        except Exception:
            sw = self.dialog.winfo_screenwidth()
            sh = self.dialog.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def build_header(self):
        header = tk.Frame(self.main_container, bg=WHITE, height=64, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=WHITE)
        left.pack(side="left", padx=20, pady=8)

        tk.Label(
            left,
            text=f"◆  {self.title_text}",
            font=("Arial", 15, "bold"),
            fg=DARK,
            bg=WHITE
        ).pack(anchor="w")

        tk.Label(
            left,
            text=self.subtitle_text,
            font=("Arial", 10),
            fg=SECONDARY,
            bg=WHITE
        ).pack(anchor="w")

    def create_card(self, title=None):
        card = tk.Frame(self.content_frame, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=12, pady=8)
        if title:
            tk.Label(card, text=title, font=("Arial", 11, "bold"), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(12, 6))
        return card

    def create_file_selector(self, label="Select PDF File", filetypes=None, multiple=False):
        if filetypes is None:
            filetypes = [("PDF Files", "*.pdf")]
        card = self.create_card(label)
        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x", padx=16, pady=(4, 12))

        entry = tk.Entry(row, font=("Arial", 10), fg=TEXT, bg="#F9FAFB", relief="flat", highlightbackground=BORDER, highlightthickness=1)
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        info_lbl = tk.Label(card, text="", font=("Arial", 9), fg=SECONDARY, bg=WHITE)
        info_lbl.pack(anchor="w", padx=16, pady=(0, 8))

        def browse():
            if multiple:
                paths = filedialog.askopenfilenames(title=f"Select {label}", filetypes=filetypes)
                if paths:
                    entry.delete(0, tk.END)
                    entry.insert(0, f"{len(paths)} files selected")
                    info_lbl.config(text=f"Total: {len(paths)} file(s) ready for processing")
                    if hasattr(self, 'on_multiple_files_selected'):
                        self.on_multiple_files_selected(paths)
            else:
                path = filedialog.askopenfilename(title=f"Select {label}", filetypes=filetypes)
                if path:
                    entry.delete(0, tk.END)
                    entry.insert(0, path)
                    try:
                        sz = backend.format_file_size(os.path.getsize(path))
                        extra = ""
                        if path.lower().endswith(".pdf"):
                            with pymupdf.open(path) as doc:
                                extra = f"  •  Pages: {len(doc)}"
                        info_lbl.config(text=f"Size: {sz}{extra}")
                    except Exception as error:
                        info_lbl.config(text=f"Could not inspect selected file: {error}", fg=RED)
                    if hasattr(self, 'on_file_selected'):
                        self.on_file_selected(path)

        btn = tk.Button(
            row,
            text="Browse...",
            font=("Arial", 10, "bold"),
            fg=WHITE,
            bg=PRIMARY,
            activebackground=PRIMARY_HOVER,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=5,
            command=browse
        )
        btn.pack(side="right")
        return entry, info_lbl

    def choose_output_path(self, title, extension, initialfile, input_paths=(), filetypes=None):
        """Choose a new output path, explicitly confirming replacement of an existing file."""
        selected = filedialog.asksaveasfilename(
            title=title,
            defaultextension=extension,
            filetypes=filetypes or [("Output File", f"*{extension}")],
            initialfile=initialfile,
            confirmoverwrite=False,
        )
        if not selected:
            return None
        if not selected.lower().endswith(extension.lower()):
            selected += extension

        output_path = os.path.abspath(selected)
        output_key = os.path.normcase(os.path.realpath(output_path))
        for input_path in input_paths:
            if input_path and os.path.normcase(os.path.realpath(os.path.abspath(input_path))) == output_key:
                messagebox.showwarning(
                    "Choose a Different Output",
                    "The output cannot replace one of the selected source files. Choose a different name to keep your original safe.",
                    parent=self.dialog,
                )
                return None

        if os.path.isdir(output_path):
            messagebox.showerror("Invalid Output", "Choose a file name, not a folder.", parent=self.dialog)
            return None
        if os.path.exists(output_path) and not messagebox.askyesno(
            "Confirm Overwrite",
            f"This file already exists:\n\n{output_path}\n\nReplace it after the new output has been verified?",
            parent=self.dialog,
        ):
            return None
        return output_path

    def _process_output(self, worker_func, output_path, output_kind):
        """Write beside the destination, validate the result, then atomically publish it."""
        output_dir = os.path.dirname(output_path) or os.curdir
        extension = os.path.splitext(output_path)[1]
        descriptor, staged_path = tempfile.mkstemp(
            prefix=".mits_pdf_", suffix=extension, dir=output_dir
        )
        os.close(descriptor)
        os.remove(staged_path)
        try:
            result = worker_func(staged_path)
            if not os.path.isfile(staged_path) or os.path.getsize(staged_path) == 0:
                raise RuntimeError("The operation did not produce a non-empty output file.")
            if output_kind == "pdf":
                with open(staged_path, "rb") as output_file:
                    if output_file.read(5) != b"%PDF-":
                        raise RuntimeError("The output is not a valid PDF file.")
                reader = backend.pypdf.PdfReader(staged_path, strict=False)
                if not reader.is_encrypted and len(reader.pages) == 0:
                    raise RuntimeError("The output PDF does not contain any pages.")
            elif output_kind == "pptx":
                backend.pptx.Presentation(staged_path)
            elif output_kind == "docx":
                backend.docx.Document(staged_path)
            elif output_kind == "text":
                with open(staged_path, "r", encoding="utf-8"):
                    pass

            os.replace(staged_path, output_path)
            if isinstance(result, dict):
                result["output_path"] = output_path
                if "file_size" in result:
                    result["file_size"] = os.path.getsize(output_path)
            return result
        finally:
            if os.path.exists(staged_path):
                os.remove(staged_path)

    def run_worker(self, worker_func, on_success, output_path=None, output_kind=None):
        """Run intensive work in the background and deliver all UI updates on Tk's thread."""
        self.action_btn.config(state="disabled")
        self.cancel_btn.config(state="disabled")
        self.status_label.config(text="Processing... Please wait", fg=PRIMARY)
        result_queue = queue.Queue()

        def thread_target():
            try:
                if output_path:
                    result = self._process_output(
                        worker_func, output_path, output_kind or "pdf"
                    )
                else:
                    result = worker_func()
                result_queue.put((True, result))
            except Exception as e:
                result_queue.put((False, str(e)))

        threading.Thread(target=thread_target, daemon=True).start()
        self.dialog.after(100, self._poll_worker, result_queue, on_success)

    def _poll_worker(self, result_queue, on_success):
        if not self.dialog.winfo_exists():
            return
        try:
            succeeded, result = result_queue.get_nowait()
        except queue.Empty:
            self.dialog.after(100, self._poll_worker, result_queue, on_success)
            return

        self.action_btn.config(state="normal")
        self.cancel_btn.config(state="normal")
        if succeeded:
            self.status_label.config(text="Completed successfully!", fg=SUCCESS_GREEN)
            on_success(result)
        else:
            self.status_label.config(text="Error occurred", fg=RED)
            messagebox.showerror(
                "Operation Failed",
                f"An error occurred while processing:\n\n{result}",
                parent=self.dialog,
            )

    def show_success_view(self, output_path, extra_info=""):
        """Displays completion view with quick buttons to open file or show in folder."""
        card = self.create_card("✓ Success")
        
        msg = f"File processed and saved successfully:\n{output_path}"
        if extra_info:
            msg += f"\n\n{extra_info}"
            
        tk.Label(card, text=msg, font=("Arial", 10), fg=DARK, bg=WHITE, justify="left", wraplength=520).pack(anchor="w", padx=16, pady=8)

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=(4, 14))

        if os.path.isfile(output_path):
            tk.Button(
                btn_row,
                text="Open File",
                font=("Arial", 10, "bold"),
                fg=WHITE,
                bg=PRIMARY,
                activebackground=PRIMARY_HOVER,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=14,
                pady=6,
                command=lambda: backend.open_file_in_system(output_path)
            ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row,
            text="Open Folder",
            font=("Arial", 10),
            fg=DARK,
            bg="#E5E7EB",
            activebackground="#D1D5DB",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=6,
            command=lambda: backend.reveal_in_explorer(output_path)
        ).pack(side="left")

        # Scroll to bottom
        self.dialog.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def execute(self):
        """Override in subclasses."""
        pass


# ==========================================
# 1. CREATE PDF DIALOG
# ==========================================

class CreatePDFDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Create PDF", "Generate a new custom PDF document with text, layout, and image.", width=660, height=680)
        self.action_btn.config(text="Generate PDF")

        # Card 1: Document Details
        c1 = self.create_card("Document Details")
        
        tk.Label(c1, text="Title", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(6, 2))
        self.title_entry = tk.Entry(c1, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.title_entry.insert(0, "My Document")
        self.title_entry.pack(fill="x", padx=16, pady=(0, 8), ipady=5)

        tk.Label(c1, text="Author", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(0, 2))
        self.author_entry = tk.Entry(c1, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.author_entry.insert(0, "PDF Tools User")
        self.author_entry.pack(fill="x", padx=16, pady=(0, 10), ipady=5)

        # Card 2: Layout & Format
        c2 = self.create_card("Page Setup")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=8)

        tk.Label(row, text="Page Size:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.size_var = tk.StringVar(value="A4")
        tk.Radiobutton(row, text="A4", variable=self.size_var, value="A4", bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="Letter", variable=self.size_var, value="Letter", bg=WHITE).pack(side="left")

        tk.Label(row, text="    Orientation:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.orient_var = tk.StringVar(value="portrait")
        tk.Radiobutton(row, text="Portrait", variable=self.orient_var, value="portrait", bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="Landscape", variable=self.orient_var, value="landscape", bg=WHITE).pack(side="left")

        # Card 3: Optional Image
        c3 = self.create_card("Optional Header Image")
        img_row = tk.Frame(c3, bg=WHITE)
        img_row.pack(fill="x", padx=16, pady=8)
        self.img_entry = tk.Entry(img_row, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.img_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        tk.Button(
            img_row, text="Browse Image", font=("Arial", 9, "bold"), fg=WHITE, bg=PRIMARY,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self.browse_image
        ).pack(side="right")

        # Card 4: Text Content
        c4 = self.create_card("Content Text")
        self.text_box = tk.Text(c4, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1, height=8)
        self.text_box.insert("1.0", "Type your document text here...\n\nParagraphs are automatically formatted into professional PDF pages.")
        self.text_box.pack(fill="both", expand=True, padx=16, pady=(4, 14))

    def browse_image(self):
        p = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", ("*.png", "*.jpg", "*.jpeg", "*.bmp"))],
        )
        if p:
            self.img_entry.delete(0, tk.END)
            self.img_entry.insert(0, p)

    def execute(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        text = self.text_box.get("1.0", tk.END).strip()
        psize = self.size_var.get()
        orient = self.orient_var.get()
        img = self.img_entry.get().strip() or None

        out_path = self.choose_output_path(
            "Save Generated PDF", ".pdf",
            f"{title.replace(' ', '_')}.pdf" if title else "document.pdf",
            filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.create_pdf(staged_path, title, author, text, psize, orient, img)

        def on_success(res):
            self.show_success_view(out_path, f"Size: {backend.format_file_size(res['file_size'])}")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 2. PDF MERGER DIALOG
# ==========================================

class PDFMergerDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Merge PDFs", "Combine multiple PDF documents into one file.", width=660, height=620)
        self.action_btn.config(text="Merge PDFs")
        self.files_list = []

        card = self.create_card("Selected PDF Files (In Order)")
        
        list_frame = tk.Frame(card, bg=WHITE)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(6, 10))

        self.listbox = tk.Listbox(list_frame, font=("Arial", 10), selectmode="single", height=8, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        lb_scroll = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=lb_scroll.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        lb_scroll.pack(side="right", fill="y")

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        tk.Button(btn_row, text="+ Add Files", font=("Arial", 9, "bold"), fg=WHITE, bg=PRIMARY, relief="flat", cursor="hand2", padx=10, pady=5, command=self.add_files).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="▲ Move Up", font=("Arial", 9), fg=DARK, bg="#F3F4F6", relief="flat", cursor="hand2", padx=8, pady=5, command=self.move_up).pack(side="left", padx=4)
        tk.Button(btn_row, text="▼ Move Down", font=("Arial", 9), fg=DARK, bg="#F3F4F6", relief="flat", cursor="hand2", padx=8, pady=5, command=self.move_down).pack(side="left", padx=4)
        tk.Button(btn_row, text="Remove", font=("Arial", 9), fg=RED, bg="#FEE2E2", relief="flat", cursor="hand2", padx=8, pady=5, command=self.remove_selected).pack(side="left", padx=4)
        tk.Button(btn_row, text="Clear All", font=("Arial", 9), fg=SECONDARY, bg="#F3F4F6", relief="flat", cursor="hand2", padx=8, pady=5, command=self.clear_all).pack(side="right")

        self.count_label = tk.Label(card, text="0 files selected", font=("Arial", 9), fg=SECONDARY, bg=WHITE)
        self.count_label.pack(anchor="w", padx=16, pady=(0, 8))

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Select PDF Files to Merge", filetypes=[("PDF Files", "*.pdf")])
        for p in paths:
            if p not in self.files_list:
                self.files_list.append(p)
                self.listbox.insert(tk.END, f"{os.path.basename(p)}  ({p})")
        self.count_label.config(text=f"{len(self.files_list)} files selected for merging")

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.files_list[idx - 1], self.files_list[idx] = self.files_list[idx], self.files_list[idx - 1]
        text = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx - 1, text)
        self.listbox.selection_set(idx - 1)

    def move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.files_list) - 1:
            return
        idx = sel[0]
        self.files_list[idx + 1], self.files_list[idx] = self.files_list[idx], self.files_list[idx + 1]
        text = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx + 1, text)
        self.listbox.selection_set(idx + 1)

    def remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.files_list.pop(idx)
        self.listbox.delete(idx)
        self.count_label.config(text=f"{len(self.files_list)} files selected")

    def clear_all(self):
        self.files_list.clear()
        self.listbox.delete(0, tk.END)
        self.count_label.config(text="0 files selected")

    def execute(self):
        if len(self.files_list) < 2:
            messagebox.showwarning("Minimum Files Required", "Please select at least 2 PDF files to merge.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Merged PDF", ".pdf", "merged_document.pdf",
            input_paths=self.files_list,
            filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.merge_pdfs(self.files_list, staged_path)

        def on_success(res):
            self.show_success_view(out_path, f"Total Pages: {res['total_pages']}  •  Size: {backend.format_file_size(res['file_size'])}")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 3. PDF SPLIT DIALOG
# ==========================================

class PDFSplitDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Split PDF", "Split a PDF into individual pages or selected page ranges.", width=640, height=620)
        self.action_btn.config(text="Split PDF")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Split")

        c2 = self.create_card("Split Mode")
        self.mode_var = tk.StringVar(value="all")

        tk.Radiobutton(c2, text="Split into single pages (extract all pages as separate PDFs)", variable=self.mode_var, value="all", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=4)

        tk.Radiobutton(c2, text="Extract specific page range (e.g. '1-3, 5, 8-10')", variable=self.mode_var, value="range", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=4)
        self.range_entry = tk.Entry(c2, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.range_entry.insert(0, "1-3, 5")
        self.range_entry.pack(fill="x", padx=36, pady=(0, 6), ipady=4)

        tk.Radiobutton(c2, text="Split into chunks of N pages each", variable=self.mode_var, value="chunk", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=4)
        chunk_row = tk.Frame(c2, bg=WHITE)
        chunk_row.pack(fill="x", padx=36, pady=(0, 10))
        tk.Label(chunk_row, text="Pages per chunk:", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")
        self.chunk_entry = tk.Entry(chunk_row, font=("Arial", 10), width=6, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.chunk_entry.insert(0, "2")
        self.chunk_entry.pack(side="left", padx=8, ipady=3)

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file to split.", parent=self.dialog)
            return

        out_dir = filedialog.askdirectory(title="Select Destination Folder for Split Files")
        if not out_dir:
            return

        mode = self.mode_var.get()
        ranges = self.range_entry.get().strip() if mode == "range" else None
        try:
            chunk_size = int(self.chunk_entry.get().strip() or "1") if mode == "chunk" else 1
            if chunk_size < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Chunk Size", "Enter a whole number of at least 1 page.", parent=self.dialog)
            return

        def worker():
            return backend.split_pdf(in_path, out_dir, mode=mode, page_ranges=ranges, chunk_size=chunk_size)

        def on_success(res):
            self.show_success_view(out_dir, f"Created {res['count']} PDF files in output folder.")

        self.run_worker(worker, on_success)


# ==========================================
# 4. PDF LOCK DIALOG
# ==========================================

class PDFLockDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Protect PDF", "Encrypt a PDF with a password.", width=620, height=580)
        self.action_btn.config(text="Lock & Encrypt")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Protect")

        c2 = self.create_card("Security Settings")
        tk.Label(c2, text="Enter Password", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(6, 2))
        self.pwd_entry = tk.Entry(c2, font=("Arial", 10), show="•", relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pwd_entry.pack(fill="x", padx=16, pady=(0, 8), ipady=5)

        tk.Label(c2, text="Confirm Password", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(0, 2))
        self.confirm_entry = tk.Entry(c2, font=("Arial", 10), show="•", relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.confirm_entry.pack(fill="x", padx=16, pady=(0, 8), ipady=5)

        self.show_pwd_var = tk.BooleanVar(value=False)
        tk.Checkbutton(c2, text="Show Password", variable=self.show_pwd_var, bg=WHITE, command=self.toggle_show_pwd).pack(anchor="w", padx=16, pady=(0, 10))

    def toggle_show_pwd(self):
        show = "" if self.show_pwd_var.get() else "•"
        self.pwd_entry.config(show=show)
        self.confirm_entry.config(show=show)

    def execute(self):
        in_path = self.file_entry.get().strip()
        pwd = self.pwd_entry.get()
        confirm = self.confirm_entry.get()

        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        if not pwd:
            messagebox.showwarning("Password Required", "Please enter a password.", parent=self.dialog)
            return

        if pwd != confirm:
            messagebox.showerror("Mismatch", "Password and confirmation password do not match.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Encrypted PDF", ".pdf", "protected_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.lock_pdf(in_path, staged_path, pwd)

        def on_success(res):
            self.show_success_view(out_path, "PDF is now password-protected with 256-bit AES encryption.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 5. PDF UNLOCK DIALOG
# ==========================================

class PDFUnlockDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Unlock PDF", "Remove password protection using the current password.", width=620, height=540)
        self.action_btn.config(text="Unlock PDF")

        self.file_entry, self.file_info = self.create_file_selector("Select Protected PDF")

        c2 = self.create_card("Decryption Password")
        tk.Label(c2, text="Current Password", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(6, 2))
        self.pwd_entry = tk.Entry(c2, font=("Arial", 10), show="•", relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pwd_entry.pack(fill="x", padx=16, pady=(0, 8), ipady=5)

        self.show_pwd_var = tk.BooleanVar(value=False)
        tk.Checkbutton(c2, text="Show Password", variable=self.show_pwd_var, bg=WHITE, command=lambda: self.pwd_entry.config(show="" if self.show_pwd_var.get() else "•")).pack(anchor="w", padx=16, pady=(0, 10))

    def execute(self):
        in_path = self.file_entry.get().strip()
        pwd = self.pwd_entry.get()

        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        if not pwd:
            messagebox.showwarning("Password Required", "Please enter the current password.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Unlocked PDF", ".pdf", "unlocked_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.unlock_pdf(in_path, staged_path, pwd)

        def on_success(res):
            self.show_success_view(out_path, "Password removed successfully. The new file can be opened without credentials.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 6. PDF COMPRESSION DIALOG
# ==========================================

class PDFCompressionDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Compress PDF", "Reduce PDF file size by optimizing its contents.", width=620, height=580)
        self.action_btn.config(text="Compress PDF")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Compress")

        c2 = self.create_card("Compression Level")
        self.level_var = tk.StringVar(value="medium")

        tk.Radiobutton(c2, text="Recommended / Balanced (Optimizes stream data & images)", variable=self.level_var, value="medium", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=4)
        tk.Radiobutton(c2, text="High Compression (Maximum size reduction, downsamples large images)", variable=self.level_var, value="high", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=4)
        tk.Radiobutton(c2, text="Light / Fast (Lossless structure cleanup)", variable=self.level_var, value="low", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=(4, 10))

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Compressed PDF", ".pdf", "compressed_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        lvl = self.level_var.get()

        def worker(staged_path):
            return backend.compress_pdf(in_path, staged_path, level=lvl)

        def on_success(res):
            orig_str = backend.format_file_size(res['orig_size'])
            new_str = backend.format_file_size(res['new_size'])
            saved_str = backend.format_file_size(res['saved_bytes'])
            self.show_success_view(
                out_path,
                f"Original Size: {orig_str}  →  Compressed: {new_str}\n"
                f"Space Saved: {saved_str} ({res['saved_pct']:.1f}% reduction)"
            )

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 7. WATERMARK PDF DIALOG
# ==========================================

class WatermarkPDFDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Watermark PDF", "Add professional text or logo watermarks to PDF pages.", width=660, height=680)
        self.action_btn.config(text="Apply Watermark")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Watermark")

        c2 = self.create_card("Watermark Content")
        self.type_var = tk.StringVar(value="text")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=4)
        tk.Radiobutton(row, text="Text Watermark", variable=self.type_var, value="text", font=("Arial", 10), bg=WHITE, command=self.toggle_type).pack(side="left")
        tk.Radiobutton(row, text="Image / Stamp Watermark", variable=self.type_var, value="image", font=("Arial", 10), bg=WHITE, command=self.toggle_type).pack(side="left", padx=16)

        # Text options
        self.text_frame = tk.Frame(c2, bg=WHITE)
        self.text_frame.pack(fill="x", padx=16, pady=(4, 10))

        tk.Label(self.text_frame, text="Watermark Text", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(anchor="w")
        self.wm_text_entry = tk.Entry(self.text_frame, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.wm_text_entry.insert(0, "CONFIDENTIAL")
        self.wm_text_entry.pack(fill="x", pady=(2, 6), ipady=4)

        opt_row = tk.Frame(self.text_frame, bg=WHITE)
        opt_row.pack(fill="x")
        
        tk.Label(opt_row, text="Color:", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")
        self.color_var = tk.StringVar(value="#EF233C")
        colors = [("Red", "#EF233C"), ("Gray", "#667085"), ("Blue", "#4F5FE8"), ("Dark", "#101B42")]
        for name, hex_val in colors:
            tk.Radiobutton(opt_row, text=name, variable=self.color_var, value=hex_val, bg=WHITE).pack(side="left", padx=3)

        tk.Label(opt_row, text="   Angle:", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")
        self.angle_var = tk.IntVar(value=45)
        for ang in [45, 0, 90]:
            tk.Radiobutton(opt_row, text=f"{ang}°", variable=self.angle_var, value=ang, bg=WHITE).pack(side="left")

        # Image option
        self.image_frame = tk.Frame(c2, bg=WHITE)
        tk.Label(self.image_frame, text="Stamp Image Path", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(anchor="w")
        i_row = tk.Frame(self.image_frame, bg=WHITE)
        i_row.pack(fill="x", pady=2)
        self.stamp_entry = tk.Entry(i_row, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.stamp_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        tk.Button(i_row, text="Browse Image", font=("Arial", 9), fg=WHITE, bg=PRIMARY, relief="flat", cursor="hand2", padx=8, pady=4, command=self.browse_stamp).pack(side="right")

        # Card 3: Target Pages & Opacity
        c3 = self.create_card("Options")
        t_row = tk.Frame(c3, bg=WHITE)
        t_row.pack(fill="x", padx=16, pady=8)

        tk.Label(t_row, text="Apply to Pages:", font=("Arial", 9), fg=DARK, bg=WHITE).pack(side="left")
        self.pages_entry = tk.Entry(t_row, font=("Arial", 10), width=14, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pages_entry.insert(0, "all")
        self.pages_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(t_row, text="(e.g. 'all', '1', '1-5')", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")

        op_row = tk.Frame(c3, bg=WHITE)
        op_row.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(op_row, text="Opacity:", font=("Arial", 9), fg=DARK, bg=WHITE).pack(side="left")
        self.opacity_scale = tk.Scale(op_row, from_=10, to=80, orient="horizontal", bg=WHITE, highlightthickness=0, length=200)
        self.opacity_scale.set(30)
        self.opacity_scale.pack(side="left", padx=8)

    def toggle_type(self):
        if self.type_var.get() == "text":
            self.image_frame.pack_forget()
            self.text_frame.pack(fill="x", padx=16, pady=(4, 10))
        else:
            self.text_frame.pack_forget()
            self.image_frame.pack(fill="x", padx=16, pady=(4, 10))

    def browse_stamp(self):
        p = filedialog.askopenfilename(
            title="Select Watermark Image",
            filetypes=[("Images", ("*.png", "*.jpg", "*.jpeg", "*.bmp"))],
        )
        if p:
            self.stamp_entry.delete(0, tk.END)
            self.stamp_entry.insert(0, p)

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Watermarked PDF", ".pdf", "watermarked_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        w_type = self.type_var.get()
        txt = self.wm_text_entry.get().strip() if w_type == "text" else None
        img_path = self.stamp_entry.get().strip() if w_type == "image" else None
        color = self.color_var.get()
        angle = self.angle_var.get()
        opacity = self.opacity_scale.get() / 100.0
        pages = self.pages_entry.get().strip() or "all"

        def worker(staged_path):
            return backend.watermark_pdf(
                in_path, staged_path, text=txt, rotation=angle,
                opacity=opacity, color_hex=color, image_path=img_path, pages=pages
            )

        def on_success(res):
            self.show_success_view(out_path, f"Watermark applied to {res['pages_watermarked']} pages.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 8. PDF TO PPT DIALOG
# ==========================================

class PDFToPPTDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "PDF to PowerPoint", "Create editable text boxes from PDF pages. Scanned pages require OCR; layout and graphics are not fully preserved.", width=620, height=560)
        self.action_btn.config(text="Convert to PPTX")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Convert")

        c2 = self.create_card("Slide Settings")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=8)

        tk.Label(row, text="Aspect Ratio:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.wide_var = tk.BooleanVar(value=True)
        tk.Radiobutton(row, text="16:9 (Widescreen)", variable=self.wide_var, value=True, bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="4:3 (Standard)", variable=self.wide_var, value=False, bg=WHITE).pack(side="left")

        row2 = tk.Frame(c2, bg=WHITE)
        row2.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(row2, text="OCR Resolution:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.dpi_var = tk.IntVar(value=150)
        tk.Radiobutton(row2, text="Standard (150 DPI)", variable=self.dpi_var, value=150, bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row2, text="High Quality (200 DPI)", variable=self.dpi_var, value=200, bg=WHITE).pack(side="left")

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save PowerPoint Presentation", ".pptx", "presentation.pptx",
            input_paths=[in_path], filetypes=[("PowerPoint Presentation", "*.pptx")],
        )
        if not out_path:
            return

        dpi = self.dpi_var.get()
        widescreen = self.wide_var.get()

        def worker(staged_path):
            return backend.pdf_to_ppt(in_path, staged_path, dpi=dpi, widescreen=widescreen)

        def on_success(res):
            self.show_success_view(out_path, f"Converted {res['slides_count']} PDF pages into presentation slides.")

        self.run_worker(worker, on_success, out_path, "pptx")


# ==========================================
# 9. PDF TO WORD DIALOG
# ==========================================

class PDFToWordDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "PDF to Word", "Convert PDF document text and structure into an editable Word (.docx) document.", width=620, height=520)
        self.action_btn.config(text="Convert to Word")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Convert")

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Word Document", ".docx", "converted_document.docx",
            input_paths=[in_path], filetypes=[("Word Document", "*.docx")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.pdf_to_word(in_path, staged_path)

        def on_success(res):
            self.show_success_view(out_path, f"Word document created successfully ({backend.format_file_size(res['file_size'])}).")

        self.run_worker(worker, on_success, out_path, "docx")


# ==========================================
# 10. PDF TO IMAGE DIALOG
# ==========================================

class PDFToImageDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "PDF to Images", "Export PDF pages as image files.", width=620, height=580)
        self.action_btn.config(text="Convert to Images")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Export")

        c2 = self.create_card("Export Settings")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=6)

        tk.Label(row, text="Format:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.fmt_var = tk.StringVar(value="png")
        for fmt in ["png", "jpeg", "webp"]:
            tk.Radiobutton(row, text=fmt.upper(), variable=self.fmt_var, value=fmt, bg=WHITE).pack(side="left", padx=8)

        row2 = tk.Frame(c2, bg=WHITE)
        row2.pack(fill="x", padx=16, pady=6)
        tk.Label(row2, text="DPI / Resolution:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.dpi_var = tk.IntVar(value=150)
        tk.Radiobutton(row2, text="150 DPI (Standard)", variable=self.dpi_var, value=150, bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row2, text="300 DPI (High Res)", variable=self.dpi_var, value=300, bg=WHITE).pack(side="left")

        row3 = tk.Frame(c2, bg=WHITE)
        row3.pack(fill="x", padx=16, pady=(6, 12))
        tk.Label(row3, text="Pages:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.pages_entry = tk.Entry(row3, font=("Arial", 10), width=16, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pages_entry.insert(0, "all")
        self.pages_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(row3, text="(e.g. 'all', '1-5', 'odd')", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_dir = filedialog.askdirectory(title="Select Destination Folder for Images")
        if not out_dir:
            return

        fmt = self.fmt_var.get()
        dpi = self.dpi_var.get()
        pages = self.pages_entry.get().strip() or "all"

        def worker():
            return backend.pdf_to_images(in_path, out_dir, img_format=fmt, dpi=dpi, pages=pages)

        def on_success(res):
            self.show_success_view(out_dir, f"Exported {res['count']} image files successfully.")

        self.run_worker(worker, on_success)


# ==========================================
# 11. OCR DIALOG
# ==========================================

class OCRDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "OCR", "Recognize text and layout from scanned PDFs and images.", width=620, height=540)
        self.action_btn.config(text="Run OCR")

        self.file_entry, self.file_info = self.create_file_selector("Select Scanned PDF")

        c2 = self.create_card("Output Options")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=10)

        tk.Label(row, text="Output Format:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.out_fmt_var = tk.StringVar(value="txt")
        tk.Radiobutton(row, text="Text Document (.txt)", variable=self.out_fmt_var, value="txt", bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="Searchable PDF (.pdf)", variable=self.out_fmt_var, value="pdf", bg=WHITE).pack(side="left")

        quality_row = tk.Frame(c2, bg=WHITE)
        quality_row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(quality_row, text="Scan quality:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.dpi_var = tk.IntVar(value=300)
        for dpi in (150, 300, 450):
            tk.Radiobutton(
                quality_row, text=f"{dpi} DPI", variable=self.dpi_var,
                value=dpi, bg=WHITE,
            ).pack(side="left", padx=5)

        language_row = tk.Frame(c2, bg=WHITE)
        language_row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(language_row, text="OCR language:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.language_entry = tk.Entry(
            language_row, font=("Arial", 10), width=12,
            relief="flat", highlightbackground=BORDER, highlightthickness=1,
        )
        self.language_entry.insert(0, "eng")
        self.language_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(language_row, text="Tesseract language code", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")

        pages_row = tk.Frame(c2, bg=WHITE)
        pages_row.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(pages_row, text="Pages:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.pages_entry = tk.Entry(
            pages_row, font=("Arial", 10), width=16,
            relief="flat", highlightbackground=BORDER, highlightthickness=1,
        )
        self.pages_entry.insert(0, "all")
        self.pages_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(pages_row, text="(e.g. 'all', '1-3', 'odd')", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        fmt = self.out_fmt_var.get()
        ext = ".pdf" if fmt == "pdf" else ".txt"
        out_path = self.choose_output_path(
            "Save OCR Output", ext, f"ocr_output{ext}",
            input_paths=[in_path], filetypes=[(f"{fmt.upper()} File", f"*{ext}")],
        )
        if not out_path:
            return

        dpi = self.dpi_var.get()
        language = self.language_entry.get().strip()
        pages = self.pages_entry.get().strip() or "all"

        def worker(staged_path):
            return backend.ocr_pdf(
                in_path, staged_path, output_format=fmt,
                language=language, dpi=dpi, pages=pages,
            )

        def on_success(res):
            note = "Optical recognition engine used." if res["ocr_engine_used"] else "Embedded layout text extracted successfully."
            self.show_success_view(out_path, f"{note}\nRecognized {res['character_count']} characters.")

        self.run_worker(worker, on_success, out_path, "pdf" if fmt == "pdf" else "text")


# ==========================================
# 12. EXTRACT TEXT DIALOG
# ==========================================

class ExtractTextDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Extract Text", "Extract pure text content and preview it directly in-app.", width=680, height=660)
        self.action_btn.config(text="Extract Text")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Extract Text From")

        c2 = self.create_card("Pages")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=8)
        tk.Label(row, text="Pages to Extract:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        self.pages_entry = tk.Entry(row, font=("Arial", 10), width=16, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pages_entry.insert(0, "all")
        self.pages_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(row, text="(e.g. 'all', '1-3', 'odd')", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(side="left")

        # Viewer card
        self.viewer_card = self.create_card("Extracted Content")
        
        stat_row = tk.Frame(self.viewer_card, bg=WHITE)
        stat_row.pack(fill="x", padx=16, pady=(6, 4))
        self.stats_label = tk.Label(stat_row, text="Ready to extract", font=("Arial", 9, "bold"), fg=SECONDARY, bg=WHITE)
        self.stats_label.pack(side="left")

        tk.Button(stat_row, text="Copy to Clipboard", font=("Arial", 9), fg=PRIMARY, bg="#EEF2FF", relief="flat", cursor="hand2", padx=8, pady=3, command=self.copy_to_clip).pack(side="right")
        tk.Button(stat_row, text="Save to .txt File", font=("Arial", 9), fg=DARK, bg="#F3F4F6", relief="flat", cursor="hand2", padx=8, pady=3, command=self.save_to_txt).pack(side="right", padx=6)

        self.text_view = tk.Text(self.viewer_card, font=("Courier New", 9), relief="flat", highlightbackground=BORDER, highlightthickness=1, height=12)
        self.text_view.pack(fill="both", expand=True, padx=16, pady=(4, 14))

    def copy_to_clip(self):
        txt = self.text_view.get("1.0", tk.END).strip()
        if txt:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(txt)
            messagebox.showinfo("Copied", "Text copied to clipboard!", parent=self.dialog)

    def save_to_txt(self):
        txt = self.text_view.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showinfo("No Text", "Extract text before saving it.", parent=self.dialog)
            return
        out_path = self.choose_output_path(
            "Save Extracted Text", ".txt", "extracted_text.txt",
            filetypes=[("Text File", "*.txt")],
        )
        if not out_path:
            return

        def worker(staged_path):
            with open(staged_path, "w", encoding="utf-8") as output_file:
                output_file.write(txt)

        def on_success(_result):
            messagebox.showinfo("Saved", f"Text saved to:\n{out_path}", parent=self.dialog)

        self.run_worker(worker, on_success, out_path, "text")

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        pages = self.pages_entry.get().strip() or "all"

        def worker():
            return backend.extract_text_from_pdf(in_path, pages=pages)

        def on_success(res):
            self.text_view.delete("1.0", tk.END)
            self.text_view.insert("1.0", res["text"])
            self.stats_label.config(text=f"Extracted {res['pages_extracted']} pages  •  {res['word_count']} words  •  {res['char_count']} chars")

        self.run_worker(worker, on_success)


# ==========================================
# 13. PPT TO PDF DIALOG
# ==========================================

class PPTToPDFDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "PowerPoint to PDF", "Convert a PowerPoint presentation to PDF.", width=620, height=520)
        self.action_btn.config(text="Convert to PDF")

        self.file_entry, self.file_info = self.create_file_selector(
            "Select PowerPoint Presentation",
            filetypes=[("PowerPoint Presentation", ("*.pptx", "*.ppt"))]
        )

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PowerPoint file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save PDF Document", ".pdf", "converted_presentation.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.ppt_to_pdf(in_path, staged_path)

        def on_success(res):
            self.show_success_view(out_path, f"Converted {res['slides_count']} slides into PDF format.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 14. WORD TO PDF DIALOG
# ==========================================

class WordToPDFDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Word to PDF", "Convert Microsoft Word documents (.docx) directly to PDF format.", width=620, height=520)
        self.action_btn.config(text="Convert to PDF")

        self.file_entry, self.file_info = self.create_file_selector(
            "Select Word Document",
            filetypes=[("Word Document", ("*.docx", "*.doc"))]
        )

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid Word file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save PDF Document", ".pdf", "converted_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.word_to_pdf(in_path, staged_path)

        def on_success(res):
            self.show_success_view(out_path, f"Created PDF document successfully ({backend.format_file_size(res['file_size'])}).")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 15. ROTATE PDF DIALOG
# ==========================================

class RotatePDFDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Rotate Pages", "Rotate all pages or a selected range in a PDF.", width=620, height=580)
        self.action_btn.config(text="Rotate & Save")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF to Rotate")

        c2 = self.create_card("Rotation Angle")
        row = tk.Frame(c2, bg=WHITE)
        row.pack(fill="x", padx=16, pady=8)

        self.angle_var = tk.IntVar(value=90)
        tk.Radiobutton(row, text="90° Clockwise ↷", variable=self.angle_var, value=90, font=("Arial", 10), bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="180° ↻", variable=self.angle_var, value=180, font=("Arial", 10), bg=WHITE).pack(side="left", padx=8)
        tk.Radiobutton(row, text="270° Counter-Clockwise ↶", variable=self.angle_var, value=270, font=("Arial", 10), bg=WHITE).pack(side="left")

        c3 = self.create_card("Page Scope")
        self.scope_var = tk.StringVar(value="all")

        tk.Radiobutton(c3, text="All Pages", variable=self.scope_var, value="all", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=3)
        tk.Radiobutton(c3, text="Odd Pages Only (1, 3, 5...)", variable=self.scope_var, value="odd", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=3)
        tk.Radiobutton(c3, text="Even Pages Only (2, 4, 6...)", variable=self.scope_var, value="even", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=3)
        
        custom_row = tk.Frame(c3, bg=WHITE)
        custom_row.pack(fill="x", padx=16, pady=(3, 10))
        tk.Radiobutton(custom_row, text="Custom Pages:", variable=self.scope_var, value="custom", font=("Arial", 10), bg=WHITE).pack(side="left")
        self.custom_pages_entry = tk.Entry(custom_row, font=("Arial", 10), width=16, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.custom_pages_entry.insert(0, "1-3, 5")
        self.custom_pages_entry.pack(side="left", padx=8, ipady=3)

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Rotated PDF", ".pdf", "rotated_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        angle = self.angle_var.get()
        scope = self.scope_var.get()
        pages = self.custom_pages_entry.get().strip() if scope == "custom" else scope

        def worker(staged_path):
            return backend.rotate_pdf(in_path, staged_path, angle=angle, page_selection=pages)

        def on_success(res):
            self.show_success_view(out_path, f"Rotated {res['pages_rotated']} pages by {angle}°.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 16. DELETE PAGES DIALOG
# ==========================================

class DeletePagesDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Delete Pages", "Remove unwanted pages from a PDF document.", width=620, height=540)
        self.action_btn.config(text="Delete Pages")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF Document")

        c2 = self.create_card("Pages to Remove")
        tk.Label(c2, text="Enter page numbers or ranges to remove:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(8, 2))
        
        self.pages_entry = tk.Entry(c2, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.pages_entry.insert(0, "1, 3, 5-7")
        self.pages_entry.pack(fill="x", padx=16, pady=(0, 6), ipady=5)

        tk.Label(c2, text="Example: '1' removes page 1; '2, 4-6' removes pages 2, 4, 5, and 6.", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(anchor="w", padx=16, pady=(0, 12))

    def execute(self):
        in_path = self.file_entry.get().strip()
        del_pages = self.pages_entry.get().strip()

        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        if not del_pages:
            messagebox.showwarning("Pages Required", "Please specify which pages to delete.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Modified PDF", ".pdf", "deleted_pages.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.delete_pages(in_path, staged_path, del_pages)

        def on_success(res):
            self.show_success_view(out_path, f"Removed {res['pages_removed']} pages. Document now has {res['pages_remaining']} pages.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 17. REORDER PAGES DIALOG
# ==========================================

class ReorderPagesDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "Reorder Pages", "Rearrange page sequence in a PDF document.", width=620, height=560)
        self.action_btn.config(text="Reorder & Save")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF Document")

        c2 = self.create_card("New Page Sequence")
        self.seq_mode = tk.StringVar(value="custom")

        tk.Radiobutton(c2, text="Custom Page Order:", variable=self.seq_mode, value="custom", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=(8, 2))
        self.order_entry = tk.Entry(c2, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.order_entry.insert(0, "3, 2, 1, 4-10")
        self.order_entry.pack(fill="x", padx=36, pady=(0, 6), ipady=5)
        tk.Label(c2, text="Example: '3, 1, 2' puts page 3 first, then page 1, then page 2.", font=("Arial", 9), fg=SECONDARY, bg=WHITE).pack(anchor="w", padx=36, pady=(0, 6))

        tk.Radiobutton(c2, text="Reverse Entire Document Order", variable=self.seq_mode, value="reverse", font=("Arial", 10), bg=WHITE).pack(anchor="w", padx=16, pady=(4, 12))

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        mode = self.seq_mode.get()
        order_str = "reverse" if mode == "reverse" else self.order_entry.get().strip()

        if not order_str:
            messagebox.showwarning("Order Required", "Please enter the desired page order.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save Reordered PDF", ".pdf", "reordered_document.pdf",
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        def worker(staged_path):
            return backend.reorder_pages(in_path, staged_path, order_str)

        def on_success(res):
            self.show_success_view(out_path, f"Document pages reordered successfully ({res['new_page_count']} pages).")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# 18. PDF PREVIEW DIALOG
# ==========================================

class PDFPreviewDialog:
    """Dedicated interactive viewer window for high-resolution PDF inspection."""

    def __init__(self, parent):
        self.parent = parent
        self.current_pdf = None
        self.total_pages = 0
        self.current_page = 0
        self.zoom = 1.0
        self.current_photo = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("PDF Preview - PDF Tools")
        self.dialog.geometry("960x780")
        self.dialog.minsize(700, 500)
        self.dialog.configure(bg=BG)
        self.dialog.transient(parent)

        # Header bar
        header = tk.Frame(self.dialog, bg=WHITE, height=54, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="◆  PDF Previewer", font=("Arial", 13, "bold"), fg=DARK, bg=WHITE).pack(side="left", padx=16)

        tk.Button(
            header, text="Open PDF File...", font=("Arial", 9, "bold"), fg=WHITE, bg=PRIMARY,
            relief="flat", cursor="hand2", padx=12, pady=5, command=self.open_pdf
        ).pack(side="left", padx=10)

        self.file_lbl = tk.Label(header, text="No PDF loaded", font=("Arial", 9), fg=SECONDARY, bg=WHITE)
        self.file_lbl.pack(side="left", padx=8)

        # Toolbar controls
        toolbar = tk.Frame(self.dialog, bg="#EEF2FF", height=44, highlightbackground=BORDER, highlightthickness=1)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        tk.Button(toolbar, text="◀ Previous", font=("Arial", 9), fg=DARK, bg=WHITE, relief="flat", cursor="hand2", padx=8, command=self.prev_page).pack(side="left", padx=(16, 4), pady=8)
        self.page_label = tk.Label(toolbar, text="Page 0 of 0", font=("Arial", 10, "bold"), fg=DARK, bg="#EEF2FF")
        self.page_label.pack(side="left", padx=8)
        tk.Button(toolbar, text="Next ▶", font=("Arial", 9), fg=DARK, bg=WHITE, relief="flat", cursor="hand2", padx=8, command=self.next_page).pack(side="left", padx=4, pady=8)

        tk.Label(toolbar, text=" | ", fg=SECONDARY, bg="#EEF2FF").pack(side="left", padx=6)

        tk.Button(toolbar, text="Zoom In (+)", font=("Arial", 9), fg=DARK, bg=WHITE, relief="flat", cursor="hand2", padx=6, command=self.zoom_in).pack(side="left", padx=2, pady=8)
        self.zoom_label = tk.Label(toolbar, text="100%", font=("Arial", 9), fg=SECONDARY, bg="#EEF2FF")
        self.zoom_label.pack(side="left", padx=4)
        tk.Button(toolbar, text="Zoom Out (-)", font=("Arial", 9), fg=DARK, bg=WHITE, relief="flat", cursor="hand2", padx=6, command=self.zoom_out).pack(side="left", padx=2, pady=8)
        tk.Button(toolbar, text="Reset", font=("Arial", 9), fg=SECONDARY, bg=WHITE, relief="flat", cursor="hand2", padx=6, command=self.zoom_reset).pack(side="left", padx=6, pady=8)

        # Canvas with scrollbars
        canvas_frame = tk.Frame(self.dialog, bg="#6B7280")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#E5E7EB", highlightthickness=0)
        self.h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.dialog.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def open_pdf(self):
        p = filedialog.askopenfilename(title="Select PDF to Preview", filetypes=[("PDF Files", "*.pdf")])
        if not p:
            return
        try:
            with pymupdf.open(p) as doc:
                total_pages = len(doc)
                if total_pages < 1:
                    raise ValueError("The selected PDF does not contain any pages.")
            self.current_pdf = p
            self.total_pages = total_pages
            self.file_lbl.config(text=f"{os.path.basename(p)} ({backend.format_file_size(os.path.getsize(p))})")
            self.current_page = 0
            self.zoom = 1.0
            self.render_current_page()
        except Exception as error:
            messagebox.showerror("Could Not Open PDF", str(error), parent=self.dialog)

    def render_current_page(self):
        if not self.current_pdf or self.total_pages == 0:
            return
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
        self.zoom_label.config(text=f"{int(self.zoom * 100)}%")

        try:
            pil_img = backend.render_pdf_page_image(self.current_pdf, self.current_page, zoom=self.zoom)
            self.current_photo = ImageTk.PhotoImage(pil_img)
            self.canvas.delete("all")
            self.canvas.create_image(max(10, (self.canvas.winfo_width() - pil_img.width) // 2), 20, anchor="nw", image=self.current_photo)
            self.canvas.config(scrollregion=(0, 0, pil_img.width + 40, pil_img.height + 40))
        except Exception as e:
            messagebox.showerror("Render Error", f"Could not render page: {e}", parent=self.dialog)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_current_page()

    def zoom_in(self):
        if self.zoom < 3.0:
            self.zoom += 0.25
            self.render_current_page()

    def zoom_out(self):
        if self.zoom > 0.5:
            self.zoom -= 0.25
            self.render_current_page()

    def zoom_reset(self):
        self.zoom = 1.0
        self.render_current_page()


# ==========================================
# 19. PDF INFORMATION DIALOG
# ==========================================

class PDFInformationDialog(BaseToolDialog):
    def __init__(self, parent):
        super().__init__(parent, "PDF Information", "Inspect and edit metadata, security, and properties.", width=660, height=660)
        self.action_btn.config(text="Save Updated Metadata")

        self.file_entry, self.file_info = self.create_file_selector("Select PDF Document")

        # Info card
        self.info_card = self.create_card("Document Properties")
        self.prop_labels = {}
        props = [
            ("File Name:", "name"),
            ("File Size:", "size"),
            ("Total Pages:", "pages"),
            ("Page Dimensions:", "dims"),
            ("Encrypted:", "enc"),
            ("Creation Date:", "created"),
            ("Modified Date:", "modified")
        ]
        for label_text, key in props:
            row = tk.Frame(self.info_card, bg=WHITE)
            row.pack(fill="x", padx=16, pady=2)
            tk.Label(row, text=label_text, font=("Arial", 9, "bold"), fg=SECONDARY, bg=WHITE, width=16, anchor="w").pack(side="left")
            val_lbl = tk.Label(row, text="—", font=("Arial", 9), fg=DARK, bg=WHITE, anchor="w")
            val_lbl.pack(side="left", fill="x", expand=True)
            self.prop_labels[key] = val_lbl

        # Editable metadata card
        self.meta_card = self.create_card("Editable Document Metadata")
        
        self.meta_entries = {}
        fields = [("Title", "title"), ("Author", "author"), ("Subject", "subject"), ("Keywords", "keywords")]
        for title, key in fields:
            tk.Label(self.meta_card, text=title, font=("Arial", 9), fg=DARK, bg=WHITE).pack(anchor="w", padx=16, pady=(4, 1))
            entry = tk.Entry(self.meta_card, font=("Arial", 10), relief="flat", highlightbackground=BORDER, highlightthickness=1)
            entry.pack(fill="x", padx=16, pady=(0, 6), ipady=4)
            self.meta_entries[key] = entry

    def on_file_selected(self, path):
        try:
            info = backend.get_pdf_info(path)
            self.prop_labels["name"].config(text=info["file_name"])
            self.prop_labels["size"].config(text=info["file_size_formatted"])
            self.prop_labels["pages"].config(text=str(info["page_count"]))
            self.prop_labels["dims"].config(text=f"{info['dimensions_pt']}  ({info['dimensions_mm']})")
            self.prop_labels["enc"].config(text="Yes (Locked)" if info["is_encrypted"] else "No (Public)")
            self.prop_labels["created"].config(text=info["creation_date"])
            self.prop_labels["modified"].config(text=info["mod_date"])

            for key in ["title", "author", "subject", "keywords"]:
                val = info.get(key, "")
                if val == "Not specified":
                    val = ""
                self.meta_entries[key].delete(0, tk.END)
                self.meta_entries[key].insert(0, val)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read PDF metadata: {e}", parent=self.dialog)

    def execute(self):
        in_path = self.file_entry.get().strip()
        if not os.path.exists(in_path):
            messagebox.showwarning("File Required", "Please select a valid PDF file.", parent=self.dialog)
            return

        out_path = self.choose_output_path(
            "Save PDF with Updated Metadata", ".pdf", os.path.basename(in_path),
            input_paths=[in_path], filetypes=[("PDF Document", "*.pdf")],
        )
        if not out_path:
            return

        meta = {
            "title": self.meta_entries["title"].get().strip(),
            "author": self.meta_entries["author"].get().strip(),
            "subject": self.meta_entries["subject"].get().strip(),
            "keywords": self.meta_entries["keywords"].get().strip()
        }

        def worker(staged_path):
            return backend.update_pdf_metadata(in_path, staged_path, meta)

        def on_success(res):
            self.show_success_view(out_path, "PDF metadata updated successfully.")

        self.run_worker(worker, on_success, out_path, "pdf")


# ==========================================
# TOOL DISPATCHER MAP
# ==========================================

TOOL_DIALOG_MAP = {
    "Create PDF": CreatePDFDialog,
    "PDF Merger": PDFMergerDialog,
    "Merge PDFs": PDFMergerDialog,
    "PDF Split": PDFSplitDialog,
    "Split PDF": PDFSplitDialog,
    "PDF Lock": PDFLockDialog,
    "Protect PDF": PDFLockDialog,
    "PDF Unlock": PDFUnlockDialog,
    "Unlock PDF": PDFUnlockDialog,
    "PDF Compression": PDFCompressionDialog,
    "Compress PDF": PDFCompressionDialog,
    "Watermark PDF": WatermarkPDFDialog,
    "PDF to PPT": PDFToPPTDialog,
    "PDF to PowerPoint": PDFToPPTDialog,
    "PDF to Word": PDFToWordDialog,
    "PDF to Image": PDFToImageDialog,
    "PDF to Images": PDFToImageDialog,
    "OCR": OCRDialog,
    "Extract Text": ExtractTextDialog,
    "PPT to PDF": PPTToPDFDialog,
    "PowerPoint to PDF": PPTToPDFDialog,
    "Word to PDF": WordToPDFDialog,
    "Rotate PDF": RotatePDFDialog,
    "Rotate Pages": RotatePDFDialog,
    "Delete Pages": DeletePagesDialog,
    "Reorder Pages": ReorderPagesDialog,
    "PDF Preview": PDFPreviewDialog,
    "PDF Information": PDFInformationDialog
}

def open_tool_dialog(parent, tool_name):
    """Factory function to open the appropriate dialog for any tool name."""
    cls = TOOL_DIALOG_MAP.get(tool_name)
    if cls:
        return cls(parent)
    else:
        messagebox.showinfo(tool_name, f"The tool '{tool_name}' is not recognized.", parent=parent)
