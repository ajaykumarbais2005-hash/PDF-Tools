import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import time

import backend
import auth_dialogs
import auth_store
import tool_dialogs


APP_NAME = "PDF Tools"

BG = "#F5F7FF"
WHITE = "#FFFFFF"
PRIMARY = "#6D4CF5"
PRIMARY_DARK = "#5036C9"
DARK = "#211B3A"
TEXT = "#29263D"
SECONDARY = "#706C85"
BORDER = "#E5E1F0"
RED = "#EF233C"
SURFACE = "#FBFAFF"
SHADOW = "#E6E2F0"
TOOL_ACCENTS = (
    "#F06A8B", "#F2A640", "#39B7A2", "#6285F5",
    "#A16AE8", "#EC7180", "#40A9D6", "#7ABF63",
)
SESSION_IDLE_SECONDS = 15 * 60


class MITS_PDF_UTILITY:

    def __init__(self, root):

        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1536x1024")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG)

        self.base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.icon_sheet = None
        self.icon_images = []
        self.app_icon = None
        self.brand_images = {}
        self.tools_canvas = None
        self.auth_store = auth_store.AuthStore()
        self.current_user = None
        self.registration_mode = False
        self._idle_after = None
        self._activity_bindings = []

        self.setup_app_icon()
        self.center_window(1536, 1024)
        self.show_login()

    def setup_app_icon(self):
        try:
            icon_path = self.file_path("mits_pdf_icon.png")
            with Image.open(icon_path) as image:
                self.app_icon = ImageTk.PhotoImage(
                    image.resize((64, 64), Image.Resampling.LANCZOS)
                )
            self.root.iconphoto(True, self.app_icon)
            if os.name == "nt":
                self.root.iconbitmap(self.file_path("mits_pdf_icon.ico"))
        except (OSError, tk.TclError):
            self.app_icon = None

    def center_window(self, width, height):

        self.root.update_idletasks()
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = min(width, max(1100, sw - 60))
            h = min(height, max(700, sh - 80))
            x = (sw - w) // 2
            y = max(0, (sh - h) // 2 - 20)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def clear(self):

        if self.tools_canvas is not None:
            self.root.unbind_all("<MouseWheel>")
            self.tools_canvas = None

        for widget in self.root.winfo_children():
            widget.destroy()

        self.icon_images.clear()

    def file_path(self, filename):

        return os.path.join(
            self.base_path,
            filename
        )

    def show_login(self):
        self.clear()
        self.root.geometry("1536x1024")
        self.root.resizable(False, False)
        self.center_window(1536, 1024)
        setup_mode = self.auth_store.needs_setup()
        if setup_mode:
            self.registration_mode = False
        registration_mode = self.registration_mode and not setup_mode

        frame = tk.Frame(self.root, bg=PRIMARY)
        frame.pack(fill="both", expand=True)
        top = tk.Frame(frame, bg=WHITE, height=54)
        top.pack(fill="x")
        top.pack_propagate(False)
        self.brand_images["login"] = self.load_brand_icon(34)
        if self.brand_images["login"]:
            tk.Label(top, image=self.brand_images["login"], bg=WHITE).pack(side="left", padx=(18, 8))
        tk.Label(top, text="PDF Tools", font=("Arial", 16, "bold"), fg=DARK, bg=WHITE).pack(side="left")
        for label, command in (
            ("—", self.root.iconify),
            ("□", self.toggle_maximize),
            ("×", self.root.destroy),
        ):
            tk.Button(
                top, text=label, font=("Arial", 13), fg=TEXT, bg=WHITE,
                activebackground=WHITE, relief="flat", bd=0,
                command=command,
            ).pack(side="right", padx=9)

        body = tk.Frame(frame, bg=PRIMARY)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=PRIMARY)
        left.place(relx=0, rely=0, relwidth=0.46, relheight=1)
        tk.Label(left, text="PDF", font=("Arial", 58, "bold"), fg=WHITE, bg=PRIMARY).pack(pady=(180, 0))
        tk.Label(left, text="TOOLS", font=("Arial", 42, "bold"), fg=WHITE, bg=PRIMARY).pack()
        tk.Label(left, text="Merge, convert, and organize documents on this computer.", font=("Arial", 16), fg="#E8EBFF", bg=PRIMARY, wraplength=480, justify="center").pack(pady=12)
        tk.Label(left, text="Authorized access  ·  Private local accounts", font=("Arial", 12), fg="#E8EBFF", bg=PRIMARY).pack(pady=4)

        right = tk.Frame(body, bg=WHITE)
        right.place(relx=0.46, rely=0, relwidth=0.54, relheight=1)
        card_height = 730 if registration_mode else (650 if setup_mode else 560)
        card = tk.Frame(right, bg=WHITE, highlightbackground="#E2E7F0", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=620, height=card_height)
        heading = (
            "Create Administrator" if setup_mode
            else ("Create Your Account" if registration_mode else "Welcome Back")
        )
        subtitle = (
            "Set up the first account. The administrator can issue registration invitations."
            if setup_mode else (
                "Register with a one-time invitation code from an administrator."
                if registration_mode
                else "Sign in with an account authorized on this Windows profile."
            )
        )
        tk.Label(card, text=heading, font=("Arial", 27, "bold"), fg=DARK, bg=WHITE).pack(anchor="w", padx=48, pady=(42, 5))
        tk.Label(card, text=subtitle, font=("Arial", 11), fg=SECONDARY, bg=WHITE, wraplength=510, justify="left").pack(anchor="w", padx=48, pady=(0, 18))

        self.invitation_entry = None
        if registration_mode:
            tk.Label(card, text="Administrator invitation code", font=("Arial", 11), fg=DARK, bg=WHITE).pack(anchor="w", padx=48)
            self.invitation_entry = tk.Entry(card, font=("Arial", 12), relief="flat", highlightbackground=BORDER, highlightthickness=1)
            self.invitation_entry.pack(fill="x", padx=48, pady=(6, 12), ipady=9)
        tk.Label(card, text="Username", font=("Arial", 11), fg=DARK, bg=WHITE).pack(anchor="w", padx=48)
        self.login_entry = tk.Entry(card, font=("Arial", 12), relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.login_entry.pack(fill="x", padx=48, pady=(6, 12), ipady=9)
        tk.Label(card, text="Password (at least 12 characters)", font=("Arial", 11), fg=DARK, bg=WHITE).pack(anchor="w", padx=48)
        self.password_entry = tk.Entry(card, font=("Arial", 12), show="•", relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.password_entry.pack(fill="x", padx=48, pady=(6, 12), ipady=9)
        self.confirm_password_entry = None
        if setup_mode or registration_mode:
            tk.Label(card, text="Confirm password", font=("Arial", 11), fg=DARK, bg=WHITE).pack(anchor="w", padx=48)
            self.confirm_password_entry = tk.Entry(card, font=("Arial", 12), show="•", relief="flat", highlightbackground=BORDER, highlightthickness=1)
            self.confirm_password_entry.pack(fill="x", padx=48, pady=(6, 8), ipady=9)
            reveal_row = tk.Frame(card, bg=WHITE)
            reveal_row.pack(anchor="w", padx=44)
            self.show_password_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                reveal_row, text="Show passwords", variable=self.show_password_var,
                command=self.toggle_login_password_visibility, bg=WHITE,
            ).pack(anchor="w")
        else:
            self.show_password_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                card, text="Show password", variable=self.show_password_var,
                command=self.toggle_login_password_visibility, bg=WHITE,
            ).pack(anchor="w", padx=44, pady=(0, 8))

        self.login_status = tk.Label(card, text="", font=("Arial", 10), fg=RED, bg=WHITE, wraplength=510, justify="left")
        self.login_status.pack(anchor="w", padx=48, pady=(4, 8))
        tk.Button(
            card,
            text="Create Administrator" if setup_mode else (
                "Create Account" if registration_mode else "Sign In"
            ),
            font=("Arial", 12, "bold"), fg=WHITE, bg=PRIMARY,
            activebackground=PRIMARY_DARK, activeforeground=WHITE,
            relief="flat", bd=0, cursor="hand2",
            command=self.authenticate_login,
        ).pack(fill="x", padx=48, ipady=11, pady=(4, 0))
        if not setup_mode:
            tk.Button(
                card,
                text="Back to Sign In" if registration_mode else "Create account with invitation",
                font=("Arial", 10, "bold"),
                fg=PRIMARY,
                bg=WHITE,
                activebackground="#F3F4F6",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.toggle_registration_mode,
            ).pack(pady=(10, 0))
        footer = "Passwords are stored as salted hashes on this Windows account."
        tk.Label(card, text=footer, font=("Arial", 9), fg=SECONDARY, bg=WHITE, wraplength=500).pack(pady=(16, 0))
        if self.invitation_entry:
            self.invitation_entry.bind("<Return>", lambda event: self.login_entry.focus_set())
            self.invitation_entry.focus_set()
        else:
            self.login_entry.focus_set()
        self.login_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind(
            "<Return>",
            lambda event: self.confirm_password_entry.focus_set()
            if self.confirm_password_entry else self.authenticate_login(),
        )
        if self.confirm_password_entry:
            self.confirm_password_entry.bind("<Return>", lambda event: self.authenticate_login())

    def toggle_registration_mode(self):
        self.registration_mode = not self.registration_mode
        self.show_login()

    def toggle_maximize(self):

        current = self.root.state()

        if current == "zoomed":
            self.root.state("normal")
        else:
            self.root.state("zoomed")

    def toggle_login_password_visibility(self):
        character = "" if self.show_password_var.get() else "•"
        self.password_entry.config(show=character)
        if self.confirm_password_entry:
            self.confirm_password_entry.config(show=character)

    def authenticate_login(self):
        username = self.login_entry.get().strip()
        password = self.password_entry.get()
        if not username:
            self.login_status.config(text="Enter a username.")
            self.login_entry.focus_set()
            return

        try:
            if self.auth_store.needs_setup():
                if self.confirm_password_entry is None:
                    self.login_status.config(text="Password confirmation is unavailable.")
                    return
                confirmation = self.confirm_password_entry.get()
                if password != confirmation:
                    self.login_status.config(text="The passwords do not match.")
                    self.confirm_password_entry.focus_set()
                    return
                self.auth_store.create_initial_admin(username, password)
            elif self.registration_mode:
                if self.confirm_password_entry is None:
                    self.login_status.config(text="Password confirmation is unavailable.")
                    return
                if self.invitation_entry is None:
                    self.login_status.config(text="An invitation code is required.")
                    return
                if password != self.confirm_password_entry.get():
                    self.login_status.config(text="The passwords do not match.")
                    self.confirm_password_entry.focus_set()
                    return
                self.auth_store.register_user(
                    self.invitation_entry.get(), username, password
                )
            self.current_user = self.auth_store.authenticate(username, password)
        except auth_store.AuthenticationError as error:
            self.login_status.config(text=str(error))
            return
        self.registration_mode = False
        self.show_dashboard()

    def load_brand_icon(self, size):
        try:
            with Image.open(self.file_path("mits_pdf_icon.png")) as image:
                icon = ImageTk.PhotoImage(
                    image.resize((size, size), Image.Resampling.LANCZOS)
                )
            return icon
        except OSError as error:
            messagebox.showerror("Brand Icon Missing", f"Could not load the app icon:\n{error}", parent=self.root)
            return None

    def load_icons(self):

        path = self.file_path(
            "pdf_tools_icons.png"
        )

        if not os.path.exists(path):

            possible = [
                self.file_path(
                    "c34a9d32-72fe-4c9a-b2fc-61f48d6bebb9.png"
                ),
                self.file_path(
                    "pdf_icons.png"
                )
            ]

            for p in possible:

                if os.path.exists(p):

                    path = p
                    break

        if not os.path.exists(path):
            return None

        try:

            image = Image.open(
                path
            ).convert("RGBA")

            return image

        except Exception:

            return None

    def make_icon(self, sheet, index):

        if sheet is None:
            return None

        columns = 6
        rows = 4

        cell_width = sheet.width / columns
        cell_height = sheet.height / rows

        row = index // columns
        col = index % columns

        if row >= rows:
            return None

        left = int(
            col * cell_width
        )

        top = int(
            row * cell_height
        )

        right = int(
            (col + 1) * cell_width
        )

        bottom = int(
            (row + 1) * cell_height
        )

        crop = sheet.crop(
            (
                left,
                top,
                right,
                bottom
            )
        )

        crop.thumbnail(
            (105, 100),
            Image.Resampling.LANCZOS
        )

        final = Image.new(
            "RGBA",
            (115, 105),
            (255, 255, 255, 0)
        )

        x = (
            115 - crop.width
        ) // 2

        y = (
            105 - crop.height
        ) // 2

        final.alpha_composite(
            crop,
            (x, y)
        )

        photo = ImageTk.PhotoImage(
            final
        )

        self.icon_images.append(
            photo
        )

        return photo

    def show_dashboard(self):
        if not self.current_user:
            self.show_login()
            return

        self.clear()

        self.root.geometry(
            "1536x1024"
        )

        self.root.resizable(
            True,
            True
        )

        self.center_window(1536, 1024)
        self.create_dashboard()
        self.start_session_monitor()

    def start_session_monitor(self):
        self.stop_session_monitor()
        self._last_activity = time.monotonic()
        for sequence in ("<Any-KeyPress>", "<Any-ButtonPress>", "<MouseWheel>"):
            binding = self.root.bind_all(sequence, self._register_activity, add="+")
            if binding:
                self._activity_bindings.append((sequence, binding))
        self._idle_after = self.root.after(30_000, self._check_session_idle)

    def _register_activity(self, _event):
        self._last_activity = time.monotonic()

    def _check_session_idle(self):
        self._idle_after = None
        if not self.current_user:
            return
        if not self._current_session_valid():
            messagebox.showinfo(
                "Account Access Revoked",
                "Your account access changed. Please sign in again.",
                parent=self.root,
            )
            self.logout()
            return
        elapsed = time.monotonic() - self._last_activity
        if elapsed >= SESSION_IDLE_SECONDS:
            messagebox.showinfo(
                "Session Locked",
                "You were signed out after 15 minutes of inactivity.",
                parent=self.root,
            )
            self.logout()
            return
        self._idle_after = self.root.after(
            min(30_000, max(1_000, int((SESSION_IDLE_SECONDS - elapsed) * 1000))),
            self._check_session_idle,
        )

    def _current_session_valid(self):
        if not self.current_user:
            return False
        return self.auth_store.is_session_valid(
            self.current_user["username"],
            self.current_user["role"],
            self.current_user["session_version"],
        )

    def stop_session_monitor(self):
        if self._idle_after:
            self.root.after_cancel(self._idle_after)
            self._idle_after = None
        for sequence, binding in self._activity_bindings:
            self.root.unbind_all(sequence)
        self._activity_bindings.clear()

    def create_dashboard(self):

        main = tk.Frame(
            self.root,
            bg=BG
        )

        main.pack(
            fill="both",
            expand=True
        )

        header = tk.Frame(
            main,
            bg=WHITE,
            height=78,
            highlightbackground=SHADOW,
            highlightthickness=1
        )

        header.pack(
            fill="x",
            padx=14,
            pady=(14, 0)
        )

        header.pack_propagate(
            False
        )

        self.brand_images["dashboard"] = self.load_brand_icon(42)
        brand_wrap = tk.Frame(header, bg=WHITE)
        brand_wrap.pack(side="left", padx=(18, 10), pady=18)
        if self.brand_images["dashboard"]:
            tk.Label(
                brand_wrap, image=self.brand_images["dashboard"], bg=WHITE
            ).pack(side="left")

        tk.Label(
            brand_wrap,
            text="PDF Tools",
            font=("Arial", 21, "bold"),
            fg=PRIMARY,
            bg=WHITE
        ).pack(
            side="left",
            padx=(10, 0)
        )

        tk.Frame(
            header,
            bg=BORDER,
            width=1,
            height=30
        ).pack(
            side="left",
            padx=16
        )

        tk.Label(
            header,
            text="Merge, convert, and organize documents",
            font=("Arial", 11),
            fg=SECONDARY,
            bg=WHITE
        ).pack(
            side="left"
        )

        if self.current_user and self.current_user.get("role") == "admin":
            tk.Button(
                header,
                text="Manage Users",
                font=("Arial", 10, "bold"),
                fg=PRIMARY,
                bg="#EEF2FF",
                activebackground="#E0E7FF",
                activeforeground=PRIMARY,
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.manage_users,
            ).pack(side="right", padx=(8, 14))

        tk.Button(
            header,
            text="Logout",
            font=("Arial", 11, "bold"),
            fg=RED,
            bg=WHITE,
            activebackground=WHITE,
            activeforeground=RED,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.logout
        ).pack(side="right", padx=14)

        username = (self.current_user or {}).get("username", "")
        role = ((self.current_user or {}).get("role") or "").title()
        user_chip = tk.Frame(header, bg="#EEF3FF", highlightbackground="#D9E2FF", highlightthickness=1)
        user_chip.pack(side="right", padx=12, pady=20)
        tk.Label(
            user_chip,
            text=f"{username}  ·  {role}",
            font=("Arial", 10, "bold"),
            fg=DARK,
            bg="#EEF3FF",
            padx=12,
            pady=6,
        ).pack()

        content = tk.Frame(
            main,
            bg=BG
        )

        content.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=25
        )

        title_row = tk.Frame(
            content,
            bg=BG
        )

        title_row.pack(
            fill="x"
        )

        title_area = tk.Frame(
            title_row,
            bg=BG
        )

        title_area.pack(
            side="left"
        )

        tk.Label(
            title_area,
            text="PDF Tools",
            font=("Arial", 28, "bold"),
            fg=DARK,
            bg=BG
        ).pack(
            anchor="w"
        )

        tk.Label(
            title_area,
            text="Choose a tool to get started",
            font=("Arial", 12),
            fg=SECONDARY,
            bg=BG
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        search_frame = tk.Frame(
            title_row,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        search_frame.pack(
            side="right",
            pady=5
        )

        tk.Label(
            search_frame,
            text="⌕",
            font=("Arial", 20),
            fg=DARK,
            bg=WHITE
        ).pack(
            side="left",
            padx=(12, 4)
        )

        self.search_entry = tk.Entry(
            search_frame,
            font=("Arial", 12),
            fg="#8B95A9",
            bg=WHITE,
            relief="flat",
            bd=0,
            width=24
        )

        self.search_entry.insert(
            0,
            "Search tools..."
        )

        self.search_entry.pack(
            side="left",
            ipady=10,
            padx=(0, 10)
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.search_tools
        )

        self.search_entry.bind(
            "<FocusIn>",
            self.search_focus_in
        )

        self.search_entry.bind(
            "<FocusOut>",
            self.search_focus_out
        )

        tools_area = tk.Frame(
            content,
            bg=BG
        )

        tools_area.pack(
            fill="both",
            expand=True,
            pady=(25, 0)
        )

        canvas = tk.Canvas(
            tools_area,
            bg=BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            tools_area,
            orient="vertical",
            command=canvas.yview
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.tools_canvas = canvas

        self.tools_frame = tk.Frame(
            canvas,
            bg=BG
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=self.tools_frame,
            anchor="nw"
        )

        def configure_scroll(event):

            canvas.configure(
                scrollregion=canvas.bbox(
                    "all"
                )
            )

        self.tools_frame.bind(
            "<Configure>",
            configure_scroll
        )

        def resize_canvas(event):

            canvas.itemconfig(
                canvas_window,
                width=event.width
            )
            columns = max(1, min(6, event.width // 190))
            if columns != self._tool_columns:
                self._tool_columns = columns
                if hasattr(self, "tools"):
                    search = self.search_entry.get().strip()
                    self.draw_tools("" if search == "Search tools..." else search)

        canvas.bind(
            "<Configure>",
            resize_canvas
        )

        self.tools_canvas = canvas
        self._tool_columns = 6
        self.root.bind_all("<MouseWheel>", self.scroll_tools)

        self.icon_sheet = self.load_icons()

        self.tools = [

            (
                "Create PDF",
                "Turn your text into a PDF document"
            ),

            (
                "Merge PDFs",
                "Combine documents in the order you choose"
            ),

            (
                "Split PDF",
                "Separate pages or extract page ranges"
            ),

            (
                "Protect PDF",
                "Encrypt a PDF with a password"
            ),

            (
                "Unlock PDF",
                "Remove protection with the current password"
            ),

            (
                "Compress PDF",
                "Optimize PDF structure and image size"
            ),

            (
                "Watermark PDF",
                "Add a text or image watermark"
            ),

            (
                "PDF to PowerPoint",
                "Create editable slides from PDF text"
            ),

            (
                "PDF to Word",
                "Extract PDF text into a Word document"
            ),

            (
                "PDF to Images",
                "Export pages as PNG, JPEG, or WebP"
            ),

            (
                "OCR",
                "Recognize text from scanned PDFs"
            ),

            (
                "Extract Text",
                "Get text and page-level word counts"
            ),

            (
                "PowerPoint to PDF",
                "Convert PowerPoint to PDF"
            ),

            (
                "Word to PDF",
                "Convert Word document to PDF"
            ),

            (
                "Rotate Pages",
                "Rotate all pages or a selected range"
            ),

            (
                "Delete Pages",
                "Remove selected pages and keep the rest"
            ),

            (
                "Reorder Pages",
                "Choose a new sequence for your document"
            ),

            (
                "PDF Preview",
                "Render a page at your chosen zoom level"
            ),

            (
                "PDF Information",
                "View document properties and metadata"
            )
        ]

        self.tool_cards = []

        self.draw_tools()

    def search_focus_in(self, event):

        if self.search_entry.get() == "Search tools...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=TEXT)

    def scroll_tools(self, event):
        canvas = self.tools_canvas
        if canvas is None:
            return
        try:
            if canvas.winfo_exists() and str(event.widget).startswith(str(canvas)):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            self.tools_canvas = None

    def search_focus_out(self, event):

        if self.search_entry.get().strip() == "":
            self.search_entry.insert(0, "Search tools...")
            self.search_entry.config(fg="#8B95A9")

    def draw_tools(self, search=""):

        for widget in self.tools_frame.winfo_children():
            widget.destroy()

        self.icon_images.clear()

        filtered = []
        search_term = search.lower().strip()

        for item in self.tools:

            if not search_term or search_term in item[0].lower() or search_term in item[1].lower():

                filtered.append(
                    item
                )

        columns = max(1, self._tool_columns)
        for col in range(6):
            self.tools_frame.grid_columnconfigure(
                col,
                weight=0,
                uniform=""
            )

        for index, item in enumerate(filtered):

            name = item[0]
            description = item[1]
            accent = TOOL_ACCENTS[self.tools.index(item) % len(TOOL_ACCENTS)]

            row = index // columns
            col = index % columns

            card = tk.Frame(
                self.tools_frame,
                bg=WHITE,
                highlightbackground=BORDER,
                highlightthickness=1,
                cursor="hand2"
            )

            card.grid(
                row=row,
                column=col,
                padx=9,
                pady=9,
                sticky="nsew"
            )

            tk.Frame(card, bg=accent, height=4).pack(fill="x")

            self.tools_frame.grid_columnconfigure(
                col,
                weight=1
            )

            icon_index = self.tools.index(
                item
            )

            icon = self.make_icon(
                self.icon_sheet,
                icon_index
            )

            if icon:

                icon_label = tk.Label(
                    card,
                    image=icon,
                    bg=WHITE
                )

                icon_label.pack(
                    pady=(12, 0)
                )

            else:

                icon_label = tk.Label(
                    card,
                    text="PDF",
                    font=("Arial", 20, "bold"),
                    fg=accent,
                    bg=WHITE
                )

                icon_label.pack(
                    pady=(18, 15)
                )

            name_label = tk.Label(
                card,
                text=name,
                font=("Arial", 12, "bold"),
                fg=DARK,
                bg=WHITE
            )

            name_label.pack(
                pady=(2, 4)
            )

            desc_label = tk.Label(
                card,
                text=description,
                font=("Arial", 10),
                fg="#334155",
                bg=WHITE,
                wraplength=145,
                justify="center"
            )

            desc_label.pack(
                pady=(0, 13)
            )

            # Polished hover feedback on card
            def make_hover(c_frame, nl, dl, card_accent):
                def on_enter(e):
                    c_frame.config(highlightbackground=card_accent, bg="#FBFAFF")
                    nl.config(bg="#FBFAFF")
                    dl.config(bg="#FBFAFF")

                def on_leave(e):
                    c_frame.config(highlightbackground=BORDER, bg=WHITE)
                    nl.config(bg=WHITE)
                    dl.config(bg=WHITE)

                c_frame.bind("<Enter>", on_enter)
                c_frame.bind("<Leave>", on_leave)

            make_hover(card, name_label, desc_label, accent)

            for widget in [
                card,
                icon_label,
                name_label,
                desc_label
            ]:

                widget.bind(
                    "<Button-1>",
                    lambda event,
                    tool=name:
                    self.tool_clicked(tool)
                )

        for col in range(columns):

            self.tools_frame.grid_columnconfigure(
                col,
                weight=1,
                uniform="tools"
            )

    def search_tools(self, event=None):

        value = self.search_entry.get().strip()

        if value == "Search tools...":
            value = ""

        self.draw_tools(
            value
        )

    def tool_clicked(self, tool):

        # Open dedicated tool dialog connected to backend
        if not self._current_session_valid():
            messagebox.showwarning(
                "Sign In Required",
                "Your account is no longer authorized. Sign in again to continue.",
                parent=self.root,
            )
            self.logout()
            return
        tool_dialogs.open_tool_dialog(self.root, tool)

    def create_pdf(self):

        tool_dialogs.open_tool_dialog(self.root, "Create PDF")

    def pdf_merger(self):

        tool_dialogs.open_tool_dialog(self.root, "Merge PDFs")

    def pdf_split(self):

        tool_dialogs.open_tool_dialog(self.root, "Split PDF")

    def manage_users(self):
        if not self.current_user or self.current_user["role"] != "admin":
            messagebox.showerror("Administrator Only", "Only an administrator can manage authorized accounts.", parent=self.root)
            return
        if not self._current_session_valid():
            messagebox.showwarning("Sign In Required", "Your administrator access has changed. Sign in again.", parent=self.root)
            self.logout()
            return
        auth_dialogs.AccountManagerDialog(
            self.root, self.auth_store, self.current_user
        )

    def logout(self):
        self.stop_session_monitor()
        self.current_user = None
        self.show_login()


if __name__ == "__main__":

    root = tk.Tk()

    app = MITS_PDF_UTILITY(
        root
    )

    root.mainloop()