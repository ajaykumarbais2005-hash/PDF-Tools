"""Account administration dialogs for the local authorized-user list."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import auth_store


BG = "#F5F7FF"
WHITE = "#FFFFFF"
PRIMARY = "#6D4CF5"
PRIMARY_DARK = "#5036C9"
DARK = "#211B3A"
SECONDARY = "#706C85"
BORDER = "#E5E1F0"
RED = "#EF233C"


class AccountManagerDialog:
    def __init__(self, parent, store, current_user):
        self.store = store
        self.current_user = current_user
        self.current_username = current_user["username"]
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Authorized Users - PDF TOOLS")
        self.dialog.geometry("740x520")
        self.dialog.minsize(660, 440)
        self.dialog.configure(bg=BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self._center(parent)

        header = tk.Frame(self.dialog, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x")
        tk.Label(
            header, text="Authorized Users", font=("Arial", 16, "bold"),
            fg=DARK, bg=WHITE,
        ).pack(anchor="w", padx=20, pady=(12, 2))
        tk.Label(
            header, text="Only enabled accounts can sign in. Changes apply to this Windows account.",
            font=("Arial", 9), fg=SECONDARY, bg=WHITE,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        body = tk.Frame(self.dialog, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=14)
        columns = ("username", "role", "status", "created")
        self.tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        for key, label, width in (
            ("username", "Username", 190),
            ("role", "Role", 100),
            ("status", "Status", 100),
            ("created", "Created", 220),
        ):
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons = tk.Frame(self.dialog, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 16))
        self._button(buttons, "Create Invitation", self.create_invitation).pack(side="left")
        self._button(buttons, "Add User", self.add_user, primary=True).pack(side="left")
        self._button(buttons, "Reset Password", self.reset_password).pack(side="left", padx=8)
        self._button(buttons, "Enable / Disable", self.toggle_enabled).pack(side="left")
        self._button(buttons, "Close", self.dialog.destroy).pack(side="right")
        self.refresh()

    def _center(self, parent):
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - 740) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - 520) // 2)
        self.dialog.geometry(f"+{x}+{y}")

    @staticmethod
    def _button(parent, text, command, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 10, "bold" if primary else "normal"),
            fg=WHITE if primary else DARK,
            bg=PRIMARY if primary else WHITE,
            activebackground=PRIMARY_DARK if primary else "#F3F4F6",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=8,
        )

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for user in self.store.list_users():
            self.tree.insert(
                "",
                "end",
                iid=user["username"],
                values=(
                    user["username"],
                    "Administrator" if user["role"] == "admin" else "User",
                    "Enabled" if user["enabled"] else "Disabled",
                    user["created_at"],
                ),
            )

    def _selected_username(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select an Account", "Choose an account first.", parent=self.dialog)
            return None
        return selected[0]

    def add_user(self):
        window = tk.Toplevel(self.dialog)
        window.title("Add Authorized User")
        window.geometry("420x370")
        window.configure(bg=WHITE)
        window.transient(self.dialog)
        window.grab_set()
        card = tk.Frame(window, bg=WHITE)
        card.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(card, text="Create account", font=("Arial", 16, "bold"), fg=DARK, bg=WHITE).pack(anchor="w", pady=(0, 14))

        def add_field(label, show=None):
            tk.Label(card, text=label, font=("Arial", 10), fg=DARK, bg=WHITE).pack(anchor="w", pady=(5, 2))
            field = tk.Entry(card, font=("Arial", 11), show=show, relief="flat", highlightbackground=BORDER, highlightthickness=1) # type: ignore
            field.pack(fill="x", ipady=6)
            return field

        username = add_field("Username")
        password = add_field("Password (12+ characters)", show="•")
        confirm = add_field("Confirm password", show="•")
        role_var = tk.StringVar(value="user")
        role_row = tk.Frame(card, bg=WHITE)
        role_row.pack(anchor="w", pady=10)
        tk.Label(role_row, text="Role:", font=("Arial", 10), fg=DARK, bg=WHITE).pack(side="left")
        ttk.Combobox(
            role_row, textvariable=role_var, values=("user", "admin"),
            state="readonly", width=12,
        ).pack(side="left", padx=8)

        def save():
            if password.get() != confirm.get():
                messagebox.showerror("Password Mismatch", "The passwords do not match.", parent=window)
                return
            try:
                self.store.create_user(
                    self.current_user, username.get(), password.get(), role_var.get()
                )
            except auth_store.AuthenticationError as error:
                messagebox.showerror("Could Not Add User", str(error), parent=window)
                return
            self.refresh()
            window.destroy()

        self._button(card, "Create Account", save, primary=True).pack(anchor="e", pady=(8, 0))
        username.focus_set()

    def create_invitation(self):
        try:
            code = self.store.create_invitation(self.current_user)
        except auth_store.AuthenticationError as error:
            messagebox.showerror("Could Not Create Invitation", str(error), parent=self.dialog)
            return

        window = tk.Toplevel(self.dialog)
        window.title("Registration Invitation")
        window.geometry("500x220")
        window.configure(bg=WHITE)
        window.transient(self.dialog)
        window.grab_set()
        card = tk.Frame(window, bg=WHITE)
        card.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(
            card, text="Share this one-time code with the approved user.",
            font=("Arial", 11), fg=DARK, bg=WHITE, wraplength=450,
        ).pack(anchor="w", pady=(0, 12))
        code_entry = tk.Entry(card, font=("Arial", 12), relief="flat", justify="center")
        code_entry.pack(fill="x", ipady=8)
        code_entry.insert(0, code)
        code_entry.configure(state="readonly")

        def copy_code():
            window.clipboard_clear()
            window.clipboard_append(code)
            messagebox.showinfo(
                "Invitation Copied", "The invitation code is copied to the clipboard.",
                parent=window,
            )

        actions = tk.Frame(card, bg=WHITE)
        actions.pack(fill="x", pady=(16, 0))
        self._button(actions, "Copy Code", copy_code, primary=True).pack(side="left")
        self._button(actions, "Close", window.destroy).pack(side="right")
        tk.Label(
            card, text="This code expires in 7 days and can be used once.",
            font=("Arial", 9), fg=SECONDARY, bg=WHITE,
        ).pack(anchor="w", pady=(12, 0))

    def reset_password(self):
        username = self._selected_username()
        if not username:
            return
        password = simpledialog.askstring(
            "Reset Password",
            f"Enter a new password for {username} (at least 12 characters):",
            show="•",
            parent=self.dialog,
        )
        if password is None:
            return
        confirm = simpledialog.askstring(
            "Confirm Password",
            "Re-enter the new password:",
            show="•",
            parent=self.dialog,
        )
        if confirm is None:
            return
        if password != confirm:
            messagebox.showerror("Password Mismatch", "The passwords do not match.", parent=self.dialog)
            return
        try:
            self.store.reset_password(self.current_user, username, password)
        except auth_store.AuthenticationError as error:
            messagebox.showerror("Could Not Reset Password", str(error), parent=self.dialog)
            return
        messagebox.showinfo("Password Updated", f"The password for {username} was reset.", parent=self.dialog)

    def toggle_enabled(self):
        username = self._selected_username()
        if not username:
            return
        if username.casefold() == self.current_username.casefold():
            messagebox.showwarning("Current Account", "You cannot disable the account you are currently using.", parent=self.dialog)
            return
        user = next((item for item in self.store.list_users() if item["username"] == username), None)
        if not user:
            self.refresh()
            messagebox.showerror("Account Not Found", "Refresh the account list and try again.", parent=self.dialog)
            return
        try:
            self.store.set_user_enabled(
                self.current_user, username, not bool(user["enabled"])
            )
        except auth_store.AuthenticationError as error:
            messagebox.showerror("Could Not Update Account", str(error), parent=self.dialog)
            return
        self.refresh()
