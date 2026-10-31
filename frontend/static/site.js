const tools = [
  { id: "create-pdf", title: "Create PDF", desc: "Turn your text into a polished PDF.", category: "Create", icon: "✦", fields: [
    { name: "title", label: "Document title", value: "My Document" }, { name: "author", label: "Author", value: "PDF Tools User" },
    { name: "page_size", label: "Page size", type: "select", options: [["A4", "A4"], ["Letter", "Letter"]] },
    { name: "orientation", label: "Orientation", type: "select", options: [["Portrait", "portrait"], ["Landscape", "landscape"]] },
    { name: "font_size", label: "Font size (6–72 pt)", type: "number", value: "11", min: "6", max: "72" },
    { name: "image", label: "Optional header image", type: "file", accept: "image/png,image/jpeg,image/bmp" },
    { name: "text_content", label: "Document text", type: "textarea", value: "Type your document text here...", full: true },
    { name: "filename", label: "Download filename", value: "document.pdf" },
  ]},
  { id: "merge-pdfs", title: "Merge PDFs", desc: "Combine documents in the order you choose.", category: "Organize", icon: "▤", popular: true, fields: [
    { name: "files", label: "PDF files (select at least two)", type: "files", accept: ".pdf", multiple: true, minFiles: 2, full: true },
    { name: "filename", label: "Download filename", value: "merged.pdf", full: true },
  ]},
  { id: "split-pdf", title: "Split PDF", desc: "Separate pages or extract page ranges.", category: "Organize", icon: "⫶", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "mode", label: "Split mode", type: "select", options: [["Every page", "all"], ["Selected page range", "range"], ["Page chunks", "chunk"]] },
    { name: "page_ranges", label: "Page range", value: "1-3", hint: "Used in selected-range mode. Example: 1-3, 5" },
    { name: "chunk_size", label: "Pages per chunk", type: "number", value: "1", min: "1" },
  ]},
  { id: "lock-pdf", title: "Protect PDF", desc: "Encrypt a PDF with a password.", category: "Secure", icon: "◇", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "user_password", label: "Open password", type: "password" }, { name: "owner_password", label: "Owner password (optional)", type: "password" },
    { name: "algorithm", label: "Encryption", type: "select", options: [["AES-256 (recommended)", "AES-256"], ["AES-128", "AES-128"]] },
  ]},
  { id: "unlock-pdf", title: "Unlock PDF", desc: "Remove password protection with the correct password.", category: "Secure", icon: "♧", fields: [
    { name: "file", label: "Protected PDF", type: "file", accept: ".pdf", full: true }, { name: "password", label: "Current PDF password", type: "password", full: true },
  ]},
  { id: "compress-pdf", title: "Compress PDF", desc: "Optimize PDF structure and image size.", category: "Optimize", icon: "⇣", popular: true, fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "level", label: "Compression", type: "select", options: [["Balanced", "medium"], ["High — downsample images", "high"], ["Light — lossless", "low"]] },
  ]},
  { id: "watermark-pdf", title: "Watermark PDF", desc: "Stamp selected pages with text or an image.", category: "Edit", icon: "◈", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "text", label: "Watermark text", value: "CONFIDENTIAL" }, { name: "color_hex", label: "Text color", type: "color", value: "#EF233C" },
    { name: "rotation", label: "Rotation", type: "select", options: [["45°", "45"], ["0°", "0"], ["90°", "90"]] },
    { name: "opacity", label: "Opacity (%)", type: "number", value: "30", min: "0", max: "100" },
    { name: "pages", label: "Pages", value: "all", hint: "Example: all, 1, 1-5" },
    { name: "image", label: "Optional stamp image (overrides text)", type: "file", accept: "image/png,image/jpeg,image/bmp", full: true },
  ]},
  { id: "pdf-to-ppt", title: "PDF to PowerPoint", desc: "Create editable slides from PDF text; scanned pages are read with OCR.", category: "Convert", popular: true, icon: "▰", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "dpi", label: "OCR resolution (36–600 DPI)", type: "number", value: "150", min: "36", max: "600" },
    { name: "language", label: "OCR language code", value: "eng", hint: "Use an installed Tesseract language, such as eng." },
    { name: "widescreen", label: "Widescreen slides", type: "checkbox", checked: true },
  ]},
  { id: "pdf-to-word", title: "PDF to Word", desc: "Extract PDF text into a Word document.", category: "Convert", icon: "▣", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
  ]},
  { id: "pdf-to-image", title: "PDF to Images", desc: "Export pages as PNG, JPEG, or WebP.", category: "Convert", icon: "▧", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "img_format", label: "Image format", type: "select", options: [["PNG", "png"], ["JPEG", "jpeg"], ["WebP", "webp"]] },
    { name: "dpi", label: "Resolution (36–600 DPI)", type: "number", value: "150", min: "36", max: "600" },
    { name: "pages", label: "Pages", value: "all", hint: "Example: all, odd, 1-5" },
  ]},
  { id: "ocr", title: "OCR", desc: "Recognize text in scanned PDF pages.", category: "Extract", icon: "⌕", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "output_format", label: "Output", type: "select", options: [["Text file", "txt"], ["Searchable PDF", "pdf"]] },
    { name: "language", label: "Tesseract language code", value: "eng", hint: "Install Tesseract and language data for scanned pages." },
    { name: "dpi", label: "Resolution (150–600 DPI)", type: "number", value: "300", min: "150", max: "600" },
    { name: "pages", label: "Pages", value: "all", hint: "Example: all, 1-3" },
  ]},
  { id: "extract-text", title: "Extract Text", desc: "Get text and page-level word counts.", category: "Extract", icon: "≡", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true }, { name: "pages", label: "Pages", value: "all", full: true },
  ]},
  { id: "ppt-to-pdf", title: "PowerPoint to PDF", desc: "Convert a presentation to PDF.", category: "Convert", icon: "▰", fields: [
    { name: "file", label: "PowerPoint file", type: "file", accept: ".ppt,.pptx", full: true },
  ]},
  { id: "word-to-pdf", title: "Word to PDF", desc: "Convert a Word document to PDF.", category: "Convert", icon: "▣", fields: [
    { name: "file", label: "Word file", type: "file", accept: ".doc,.docx", full: true },
  ]},
  { id: "rotate-pdf", title: "Rotate Pages", desc: "Rotate all pages or a selected page range.", category: "Edit", icon: "⤾", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "angle", label: "Rotation", type: "select", options: [["90° clockwise", "90"], ["180°", "180"], ["270° clockwise", "270"]] },
    { name: "page_selection", label: "Pages", value: "all", hint: "Example: all, 1-3, 5" },
  ]},
  { id: "delete-pages", title: "Delete Pages", desc: "Remove selected pages while keeping the rest.", category: "Edit", icon: "⊖", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "pages_to_delete", label: "Pages to remove", value: "1", hint: "Example: 2, 4-6", full: true },
  ]},
  { id: "reorder-pages", title: "Reorder Pages", desc: "Choose a new sequence for your document.", category: "Organize", icon: "⇅", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "page_order", label: "New page order", value: "3, 2, 1, 4-10", hint: "Use page numbers or ranges; use 'reverse' to reverse the order.", full: true },
  ]},
  { id: "pdf-information", title: "PDF Information", desc: "View document properties and metadata.", category: "Inspect", icon: "ⓘ", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
  ]},
  { id: "update-metadata", title: "Update Metadata", desc: "Edit title, author, subject, and keywords.", category: "Edit", icon: "✎", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "title", label: "Title" }, { name: "author", label: "Author" }, { name: "subject", label: "Subject" }, { name: "keywords", label: "Keywords" },
  ]},
  { id: "pdf-preview", title: "PDF Preview", desc: "Render a page at your chosen zoom level.", category: "Inspect", icon: "◉", fields: [
    { name: "file", label: "PDF file", type: "file", accept: ".pdf", full: true },
    { name: "page_number", label: "Page number", type: "number", value: "1", min: "1" },
    { name: "zoom", label: "Zoom (0.5–3)", type: "number", value: "1", min: "0.5", max: "3", step: "0.25" },
  ]},
];

const iconPaths = {
  "create-pdf": '<path d="M7 3.8h7l4 4V20H7z"/><path d="M14 4v4h4M9.5 13h5M9.5 16h5"/><path d="M4 7.5v13h10"/>',
  "merge-pdfs": '<path d="M5 4h10l3 3v13H5z"/><path d="M15 4v4h3M8 12h7M8 15h7"/><path d="M3 7v14h12"/>',
  "split-pdf": '<path d="M6 4h9l3 3v13H6z"/><path d="M15 4v4h3M9 12h6M9 15h6"/><path d="m4 9-2 2 2 2M20 9l2 2-2 2"/>',
  "lock-pdf": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v2"/>',
  "unlock-pdf": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 7.4-2M12 14v2"/>',
  "compress-pdf": '<path d="M7 3.8h7l4 4V20H7z"/><path d="M14 4v4h4M12 11v6m-3-3 3 3 3-3"/>',
  "watermark-pdf": '<path d="M6 4h9l3 3v13H6z"/><path d="M15 4v4h3M8 15h8"/><path d="m10 12 2 2 4-4"/>',
  "pdf-to-ppt": '<rect x="3.5" y="5" width="12" height="14" rx="1.5"/><path d="M7 9h5M7 12h5M7 15h3"/><path d="M16 9h4v10h-4M17 12h2"/>',
  "pdf-to-word": '<path d="M5 3.8h10l4 4V20H5z"/><path d="M15 4v4h4M8 12h8M8 15h8M8 18h5"/>',
  "pdf-to-image": '<rect x="4" y="5" width="16" height="14" rx="2"/><circle cx="9" cy="10" r="1.4"/><path d="m6 17 4-4 3 3 2-2 3 3"/>',
  "ocr": '<circle cx="10.8" cy="10.8" r="6.3"/><path d="m16 16 4.5 4.5M8 13V9l2 2 2-2v4M14 9v4"/>',
  "extract-text": '<path d="M6 4h12v16H6z"/><path d="M9 8h6M9 11h6M9 14h6M9 17h4"/>',
  "ppt-to-pdf": '<path d="M4 5h10l3 3v11H4z"/><path d="M14 5v4h3M7 12h6"/><path d="M14 14h6v6h-6zM16 17h2"/>',
  "word-to-pdf": '<path d="M4 5h10l3 3v11H4z"/><path d="M14 5v4h3M7 12h6"/><path d="m14 17 2 2 4-5"/>',
  "rotate-pdf": '<path d="M19 8a8 8 0 0 0-14-2L3 8"/><path d="M3 4v4h4M5 16a8 8 0 0 0 14 2l2-2"/><path d="M21 20v-4h-4"/>',
  "delete-pages": '<path d="M6 5h12v15H6zM9 5V3h6v2M4 5h16"/><path d="m9 10 6 6m0-6-6 6"/>',
  "reorder-pages": '<path d="M6 4h12v4H6zM6 10h12v4H6zM6 16h12v4H6z"/><path d="m3 7 2-2 2 2m-2-2v8m16 2-2 2-2-2m2 2v-8"/>',
  "pdf-information": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  "update-metadata": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L9 17l-4 1 1-4z"/>',
  "pdf-preview": '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.5"/>',
};
const svgIcon = (id, className = "") =>
  `<svg class="${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${iconPaths[id] || iconPaths["pdf-information"]}</svg>`;

const categories = ["All tools", "Create", "Organize", "Convert", "Edit", "Secure", "Optimize", "Extract", "Inspect"];
const grid = document.querySelector("#tool-grid");
const popular = document.querySelector("#popular-tools");
const tabs = document.querySelector("#category-tabs");
let activeCategory = "All tools";
let activeTool = null;
let lastFocusedElement = null;
let processingTool = false;
let activeDialog = null;

function searchableTools() {
  const search = document.querySelector("#tool-search").value.trim().toLowerCase();
  return tools.filter((tool) => `${tool.title} ${tool.desc} ${tool.category}`.toLowerCase().includes(search));
}

function card(tool, compact = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = compact ? "popular-card" : "tool-card";
  button.addEventListener("click", () => openTool(tool));
  const icon = document.createElement("span");
  icon.className = `tool-icon tone-${tool.category.toLowerCase()}`;
  icon.innerHTML = svgIcon(tool.id);
  if (compact) {
    const content = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = tool.title;
    const description = document.createElement("small");
    description.textContent = tool.desc;
    content.append(title, description);
    button.append(icon, content);
  } else {
    const top = document.createElement("span");
    top.className = "tool-card-top";
    const arrow = document.createElement("span");
    arrow.className = "arrow";
    arrow.textContent = "↗";
    top.append(icon, arrow);
    const title = document.createElement("strong");
    title.textContent = tool.title;
    const description = document.createElement("p");
    description.textContent = tool.desc;
    button.append(top, title, description);
  }
  return button;
}

function renderTools() {
  const filtered = searchableTools().filter((tool) => activeCategory === "All tools" || tool.category === activeCategory);
  grid.replaceChildren(...filtered.map((tool) => card(tool)));
  document.querySelector("#empty-state").hidden = filtered.length > 0;
  const count = document.querySelector("#tool-count");
  if (count) count.textContent = `${filtered.length} ${filtered.length === 1 ? "tool" : "tools"}${activeCategory === "All tools" ? "" : ` in ${activeCategory}`}`;
  const allToolsCount = document.querySelector("#all-tools-count");
  if (allToolsCount) allToolsCount.textContent = String(tools.length);
}

function renderCategories() {
  const filtered = searchableTools();
  tabs.replaceChildren();
  categories.forEach((category) => {
    const count = category === "All tools" ? filtered.length : filtered.filter((tool) => tool.category === category).length;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `category-tab${category === activeCategory ? " active" : ""}`;
    button.setAttribute("aria-pressed", String(category === activeCategory));
    button.setAttribute("aria-label", `${category}, ${count} ${count === 1 ? "tool" : "tools"}`);
    const name = document.createElement("span");
    name.textContent = category;
    const total = document.createElement("span");
    total.className = "category-count";
    total.textContent = String(count);
    button.append(name, total);
    button.addEventListener("click", () => {
      activeCategory = category;
      renderCategories();
      renderTools();
    });
    tabs.append(button);
  });
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function fileMatchesAccept(file, accept) {
  if (!accept) return true;
  return accept.split(",").some((entry) => {
    const rule = entry.trim().toLowerCase();
    return rule.startsWith(".")
      ? file.name.toLowerCase().endsWith(rule)
      : rule.endsWith("/*")
        ? file.type.startsWith(rule.slice(0, -1))
        : file.type.toLowerCase() === rule;
  });
}

function addField(form, field) {
  const group = document.createElement("div");
  group.className = `field-group${field.full ? " full" : ""}`;
  group.dataset.fieldName = field.name;
  const label = document.createElement("label");
  label.className = "field-label";
  label.htmlFor = `field-${field.name}`;
  label.textContent = field.label;
  let control;
  if (field.type === "select") {
    control = document.createElement("select");
    field.options.forEach(([labelText, value]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = labelText;
      control.append(option);
    });
  } else if (field.type === "textarea") {
    control = document.createElement("textarea");
    control.value = field.value || "";
  } else if (field.type === "checkbox") {
    const row = document.createElement("label");
    row.className = "checkbox-row";
    control = document.createElement("input");
    control.type = "checkbox";
    control.checked = Boolean(field.checked);
    control.name = field.name;
    control.id = `field-${field.name}`;
    row.append(control, document.createTextNode(field.label));
    group.append(row);
    return group;
  } else if (field.type === "file" || field.type === "files") {
    control = document.createElement("input");
    control.type = "file";
    control.multiple = field.type === "files";
    control.className = "file-input-hidden";
    control.id = `field-${field.name}`;
    control.name = field.name;
    if (field.accept) control.accept = field.accept;
    control.required = field.name !== "image";
    const dropzone = document.createElement("label");
    dropzone.className = "file-dropzone";
    dropzone.htmlFor = control.id;
    dropzone.tabIndex = -1;
    const prompt = document.createElement("span");
    prompt.className = "file-drop-prompt";
    prompt.textContent = "Drop files here or browse";
    const subtext = document.createElement("small");
    subtext.textContent = field.type === "files" ? "You can add multiple files" : "Choose one file";
    dropzone.append(prompt, subtext);
    const selected = document.createElement("ul");
    selected.className = "selected-files";
    selected.id = `selected-${field.name}`;
    selected.setAttribute("aria-live", "polite");
    const fileError = document.createElement("small");
    fileError.className = "field-error";
    fileError.id = `error-${field.name}`;
    fileError.hidden = true;
    fileError.setAttribute("role", "status");
    group.append(label, dropzone, control, selected, fileError);

    const showFiles = () => {
      selected.replaceChildren();
      const files = [...control.files];
      control.setCustomValidity(
        field.minFiles && files.length < field.minFiles
          ? `Select at least ${field.minFiles} PDF files.`
          : ""
      );
      files.forEach((file, index) => {
        const row = document.createElement("li");
        const fileName = document.createElement("span");
        fileName.className = "selected-file-name";
        fileName.textContent = file.name;
        const fileSize = document.createElement("small");
        fileSize.textContent = formatFileSize(file.size);
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "remove-file";
        remove.textContent = "Remove";
        remove.setAttribute("aria-label", `Remove ${file.name}`);
        remove.addEventListener("click", () => {
          const remaining = files.filter((_, fileIndex) => fileIndex !== index);
          const transfer = new DataTransfer();
          remaining.forEach((item) => transfer.items.add(item));
          control.files = transfer.files;
          showFiles();
        });
        row.append(fileName, fileSize, remove);
        selected.append(row);
      });
      fileError.hidden = true;
      fileError.textContent = "";
      dropzone.classList.toggle("has-files", files.length > 0);
    };
    control.addEventListener("change", showFiles);
    for (const eventName of ["dragenter", "dragover"]) {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("is-dragging");
      });
    }
    for (const eventName of ["dragleave", "drop"]) {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("is-dragging");
      });
    }
    dropzone.addEventListener("drop", (event) => {
      const dropped = [...event.dataTransfer.files];
      const accepted = dropped.filter((file) => fileMatchesAccept(file, field.accept));
      const rejected = dropped.length - accepted.length;
      const transfer = new DataTransfer();
      const current = field.type === "files" ? [...control.files] : [];
      [...current, ...(field.type === "files" ? accepted : accepted.slice(0, 1))].forEach((file) => {
        if (![...transfer.files].some((item) =>
          item.name === file.name && item.size === file.size && item.lastModified === file.lastModified
        )) transfer.items.add(file);
      });
      control.files = transfer.files;
      showFiles();
      if (rejected) {
        fileError.textContent = `${rejected} file${rejected === 1 ? "" : "s"} skipped: choose ${field.accept.replaceAll(",", ", ")} files.`;
        fileError.hidden = false;
      }
    });
    if (field.hint) {
      const hint = document.createElement("small");
      hint.className = "field-hint";
      hint.textContent = field.hint;
      group.append(hint);
    }
    return group;
  } else {
    control = document.createElement("input");
    control.type = field.type || "text";
    if (field.value !== undefined) control.value = field.value;
    if (field.min) control.min = field.min;
    if (field.max) control.max = field.max;
    if (field.step) control.step = field.step;
  }
  control.id = `field-${field.name}`;
  control.name = field.name;
  control.className = "field-control";
  group.append(label, control);
  if (field.hint) {
    const hint = document.createElement("small");
    hint.className = "field-hint";
    hint.textContent = field.hint;
    group.append(hint);
  }
  return group;
}

function openTool(tool) {
  activeTool = tool;
  document.querySelector("#modal-icon").innerHTML = svgIcon(tool.id);
  document.querySelector("#modal-category").textContent = tool.category;
  document.querySelector("#modal-title").textContent = tool.title;
  document.querySelector("#modal-description").textContent = tool.desc;
  const form = document.querySelector("#tool-form");
  form.replaceChildren(...tool.fields.map((field) => addField(form, field)));
  const actions = document.createElement("div");
  actions.className = "form-actions";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "button button-secondary";
  cancel.dataset.closeModal = "";
  cancel.textContent = "Cancel";
  cancel.addEventListener("click", closeTool);
  const submit = document.createElement("button");
  submit.type = "submit";
  submit.className = "button button-primary";
  submit.textContent = "Run tool →";
  actions.append(cancel, submit);
  form.append(actions);
  document.querySelector("#tool-result").hidden = true;
  document.querySelector("#tool-error").hidden = true;
  document.querySelector("#tool-progress").hidden = true;
  openDialog(document.querySelector("#tool-modal"));
  (form.querySelector(".field-control:not(.file-input-hidden)") || form.querySelector(".file-input-hidden"))?.focus();
}

function closeTool() {
  if (processingTool) return;
  closeDialog(document.querySelector("#tool-modal"));
  activeTool = null;
}

function openDialog(dialog) {
  lastFocusedElement = document.activeElement;
  activeDialog = dialog;
  dialog.hidden = false;
  document.body.classList.add("modal-open");
  (dialog.querySelector(".close-modal") || dialog).focus();
}

function closeDialog(dialog) {
  if (!dialog || dialog.hidden || (dialog.id === "tool-modal" && processingTool)) return;
  dialog.hidden = true;
  if (activeDialog === dialog) activeDialog = null;
  if (!document.querySelector(".modal-backdrop:not([hidden])")) document.body.classList.remove("modal-open");
  if (lastFocusedElement?.isConnected) lastFocusedElement.focus();
}

function closeAdmin() {
  closeDialog(document.querySelector("#admin-modal"));
}

function clearFieldErrors(form) {
  form.querySelectorAll("[aria-invalid='true']").forEach((control) => {
    control.removeAttribute("aria-invalid");
    if (control.getAttribute("aria-describedby")?.startsWith("server-error-")) {
      control.removeAttribute("aria-describedby");
    }
  });
  form.querySelectorAll(".server-field-error").forEach((error) => error.remove());
}

function showFieldError(form, fieldName, message) {
  const group = [...form.querySelectorAll(".field-group")].find((item) => item.dataset.fieldName === fieldName);
  const control = group?.querySelector("input:not([type=hidden]), select, textarea");
  if (!group || !control) return false;
  control.setAttribute("aria-invalid", "true");
  const error = document.createElement("small");
  error.className = "field-error server-field-error";
  error.id = `server-error-${fieldName}`;
  error.textContent = message;
  group.append(error);
  control.setAttribute("aria-describedby", error.id);
  control.focus();
  return true;
}

function fieldForError(message, requestedField) {
  if (requestedField && activeTool.fields.some((field) => field.name === requestedField)) return requestedField;
  const lowerMessage = message.toLowerCase();
  const directMatch = activeTool.fields.find((field) =>
    lowerMessage.includes(field.name.replaceAll("_", " ")) || lowerMessage.includes(field.label.toLowerCase())
  );
  if (directMatch) return directMatch.name;
  if (/password|decrypt|encrypted|unlock/.test(lowerMessage)) {
    const passwordField = activeTool.fields.find((field) => field.type === "password");
    if (passwordField) return passwordField.name;
  }
  if (/page|range/.test(lowerMessage)) {
    const pageField = activeTool.fields.find((field) => /page|range/i.test(`${field.name} ${field.label}`));
    if (pageField) return pageField.name;
  }
  if (/resolution|dpi|zoom/.test(lowerMessage)) {
    const resolutionField = activeTool.fields.find((field) => /dpi|zoom|resolution/i.test(`${field.name} ${field.label}`));
    if (resolutionField) return resolutionField.name;
  }
  if (/filename|file name/.test(lowerMessage)) {
    const filenameField = activeTool.fields.find((field) => /filename/i.test(field.name));
    if (filenameField) return filenameField.name;
  }
  if (/file|upload|pdf|document/.test(lowerMessage)) {
    const fileFields = activeTool.fields.filter((field) => ["file", "files"].includes(field.type));
    if (fileFields.length === 1) return fileFields[0].name;
  }
  return null;
}

function detailRows(result) {
  const excluded = new Set(["success", "output_path", "file_path", "text", "files", "image"]);
  const entries = Object.entries(result || {}).filter(([key, value]) =>
    !excluded.has(key) && (typeof value === "string" || typeof value === "number" || typeof value === "boolean")
  );
  if (!entries.length) return null;
  const dl = document.createElement("dl");
  dl.className = "result-data";
  entries.slice(0, 10).forEach(([key, value]) => {
    const item = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
    const dd = document.createElement("dd");
    dd.textContent = typeof value === "boolean" ? (value ? "Yes" : "No") : String(value);
    item.append(dt, dd);
    dl.append(item);
  });
  return dl;
}

document.querySelector("#tool-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeTool || processingTool) return;
  const form = event.currentTarget;
  const errorBox = document.querySelector("#tool-error");
  const resultBox = document.querySelector("#tool-result");
  errorBox.hidden = true;
  resultBox.hidden = true;
  clearFieldErrors(form);
  const submit = form.querySelector('[type="submit"]');
  const progressBox = document.querySelector("#tool-progress");
  const progressMessage = progressBox.querySelector(".progress-message");
  const closeButton = document.querySelector("#tool-modal .close-modal");
  const cancelButton = form.querySelector('[data-close-modal]');
  processingTool = true;
  submit.disabled = true;
  submit.textContent = "Processing…";
  form.setAttribute("aria-busy", "true");
  closeButton.disabled = true;
  cancelButton.disabled = true;
  progressMessage.textContent = "Uploading your files and starting the tool…";
  progressBox.hidden = false;
  const progressTimer = window.setInterval(() => {
    progressMessage.textContent = progressMessage.textContent.startsWith("Still")
      ? "Your files remain on this computer. Please keep this window open."
      : "Still processing locally. Larger files may take a little longer…";
  }, 12000);
  const data = new FormData();
  for (const field of activeTool.fields) {
    const control = form.elements.namedItem(field.name);
    if (!control) continue;
    if (field.type === "files") {
      [...control.files].forEach((file) => data.append("files", file));
    } else if (field.type === "file") {
      if (control.files[0]) data.append(field.name, control.files[0]);
    } else if (field.type === "checkbox") {
      data.append(field.name, control.checked ? "true" : "false");
    } else {
      data.append(field.name, control.value);
    }
  }
  try {
    progressMessage.textContent = "Processing your files locally…";
    const response = await fetch(`/api/tools/${activeTool.id}`, {
      method: "POST",
      headers: { "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content },
      body: data,
    });
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error(`The server returned an unreadable response (HTTP ${response.status}).`);
    }
    if (!response.ok) {
      const message = payload.error || `The operation could not be completed (HTTP ${response.status}).`;
      const fieldName = fieldForError(message, payload.field);
      if (fieldName) showFieldError(form, fieldName, message);
      throw new Error(message);
    }
    resultBox.replaceChildren();
    const heading = document.createElement("div");
    heading.className = "result-heading";
    const check = document.createElement("span");
    check.textContent = "✓";
    const message = document.createElement("strong");
    message.textContent = payload.message;
    heading.append(check, message);
    resultBox.append(heading);
    const summaryParts = [];
    if (payload.result?.page_count !== undefined) {
      const count = payload.result.page_count;
      summaryParts.push(`${count} ${Number(count) === 1 ? "page" : "pages"}`);
    }
    if (payload.result?.word_count !== undefined) summaryParts.push(`${payload.result.word_count} words`);
    if (summaryParts.length) {
      const summary = document.createElement("p");
      summary.className = "result-summary";
      summary.textContent = summaryParts.join(" · ");
      resultBox.append(summary);
    }
    if (payload.result?.text) {
      const detail = document.createElement("p");
      detail.className = "result-detail";
      detail.textContent = payload.result.text.slice(0, 8000);
      resultBox.append(detail);
    }
    if (payload.result?.image) {
      const image = document.createElement("img");
      image.className = "result-image";
      image.alt = `Rendered PDF page ${payload.result.page_number}`;
      image.src = payload.result.image;
      resultBox.append(image);
    }
    const rows = detailRows(payload.result);
    if (rows) resultBox.append(rows);
    if (payload.download_url) {
      const link = document.createElement("a");
      link.className = "result-download";
      link.href = payload.download_url;
      link.textContent = `Download ${activeTool.id === "merge-pdfs" ? "merged PDF" : "result"} ↓`;
      resultBox.append(link);
    }
    resultBox.hidden = false;
  } catch (error) {
    errorBox.textContent = error instanceof TypeError
      ? "Could not reach the local PDF Tools server. Check that it is running, then try again."
      : error.message;
    errorBox.hidden = false;
  } finally {
    window.clearInterval(progressTimer);
    processingTool = false;
    progressBox.hidden = true;
    form.removeAttribute("aria-busy");
    closeButton.disabled = false;
    cancelButton.disabled = false;
    submit.disabled = false;
    submit.textContent = "Run tool →";
  }
});

document.querySelector("#tool-search").addEventListener("input", () => {
  renderCategories();
  renderTools();
});
document.querySelector("#tool-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") event.preventDefault();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (activeDialog?.id === "admin-modal") closeAdmin();
    closeTool();
    closeSidebar();
  }
  if (event.key === "Tab" && activeDialog) {
    const focusable = [...activeDialog.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )].filter((element) => element.getClientRects().length > 0);
    if (!focusable.length) {
      event.preventDefault();
      activeDialog.focus();
    } else if (event.shiftKey && document.activeElement === focusable[0]) {
      event.preventDefault();
      focusable[focusable.length - 1].focus();
    } else if (!event.shiftKey && document.activeElement === focusable[focusable.length - 1]) {
      event.preventDefault();
      focusable[0].focus();
    }
  }
  if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    document.querySelector("#tool-search").focus();
  }
});
document.querySelector("#tool-modal").addEventListener("click", (event) => {
  if (event.target.id === "tool-modal" && !processingTool) closeTool();
});
document.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", () => {
  closeAdmin();
  closeTool();
}));
const sidebar = document.querySelector("#sidebar");
const menuToggle = document.querySelector("#menu-toggle");
function closeSidebar() {
  sidebar.classList.remove("open");
  document.body.classList.remove("sidebar-open");
  menuToggle.setAttribute("aria-expanded", "false");
}
function toggleSidebar() {
  const isOpen = !sidebar.classList.contains("open");
  sidebar.classList.toggle("open", isOpen);
  document.body.classList.toggle("sidebar-open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
}
menuToggle?.addEventListener("click", toggleSidebar);
document.querySelector("#sidebar-backdrop")?.addEventListener("click", closeSidebar);
document.querySelectorAll(".nav-item[href^='#']").forEach((link) => link.addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
  link.classList.add("active");
  closeSidebar();
}));
document.querySelectorAll("[data-search]").forEach((button) => button.addEventListener("click", () => {
  document.querySelector("#tool-search").value = button.dataset.search;
  activeCategory = "All tools";
  renderCategories();
  renderTools();
  document.querySelector("#tool-search").focus();
}));

renderCategories();
renderTools();
popular.replaceChildren(...tools.filter((tool) => tool.popular).map((tool) => card(tool, true)));

const adminModal = document.querySelector("#admin-modal");
if (adminModal) {
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const list = document.querySelector("#account-list");
  const adminError = document.querySelector("#admin-error");
  const requestOptions = { headers: { "X-CSRF-Token": csrf, "Content-Type": "application/json" } };

  async function loadUsers() {
    list.textContent = "Loading accounts…";
    adminError.hidden = true;
    try {
      const response = await fetch("/api/admin/users");
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not load accounts.");
      list.replaceChildren(...data.users.map((user) => {
        const row = document.createElement("div");
        row.className = "account-row";
        const avatar = document.createElement("span");
        avatar.className = "avatar";
        avatar.textContent = user.username.slice(0, 1).toUpperCase();
        const info = document.createElement("span");
        info.className = "account-row-info";
        const name = document.createElement("strong");
        name.textContent = user.username;
        const role = document.createElement("small");
        role.textContent = `${user.role} · added ${user.created_at}`;
        info.append(name, role);
        const state = document.createElement("span");
        state.className = `account-state${user.enabled ? "" : " disabled"}`;
        state.textContent = user.enabled ? "Enabled" : "Disabled";
        row.append(avatar, info, state);
        if (user.username !== document.body.dataset.username) {
          const reset = document.createElement("button");
          reset.className = "button button-secondary button-small";
          reset.textContent = "Reset password";
          reset.addEventListener("click", async () => {
            const password = window.prompt(`Set a new password for ${user.username} (at least 12 characters):`);
            if (password === null) return;
            try {
              const update = await fetch(`/api/admin/users/${encodeURIComponent(user.username)}/password`, {
                method: "POST", ...requestOptions, body: JSON.stringify({ password }),
              });
              const result = await update.json();
              if (!update.ok) throw new Error(result.error || "Could not reset this password.");
              window.alert("Password updated. The user will need to sign in again.");
              loadUsers();
            } catch (error) { showAdminError(error.message); }
          });
          const toggle = document.createElement("button");
          toggle.className = "button button-secondary button-small";
          toggle.textContent = user.enabled ? "Disable" : "Enable";
          toggle.addEventListener("click", async () => {
            try {
              const update = await fetch(`/api/admin/users/${encodeURIComponent(user.username)}/enabled`, {
                method: "POST", ...requestOptions, body: JSON.stringify({ enabled: !user.enabled }),
              });
              const result = await update.json();
              if (!update.ok) throw new Error(result.error || "Could not update this account.");
              loadUsers();
            } catch (error) { showAdminError(error.message); }
          });
          row.append(reset, toggle);
        }
        return row;
      }));
    } catch (error) {
      showAdminError(error.message);
      list.replaceChildren();
    }
  }
  function showAdminError(message) {
    adminError.textContent = message;
    adminError.hidden = false;
  }
  document.querySelector("#open-admin").addEventListener("click", () => {
    openDialog(adminModal);
    loadUsers();
  });
  document.querySelector("#refresh-users").addEventListener("click", loadUsers);
  document.querySelector("#create-invitation").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      const response = await fetch("/api/admin/invitations", { method: "POST", ...requestOptions, body: "{}" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not create an invitation.");
      const box = document.querySelector("#invitation-result");
      box.replaceChildren();
      const title = document.createElement("strong");
      title.textContent = `One-time invitation · expires in ${data.expires_in_days} days`;
      const code = document.createElement("code");
      code.textContent = data.invitation;
      box.append(title, code);
      box.hidden = false;
    } catch (error) { showAdminError(error.message); }
    finally { button.disabled = false; }
  });
  adminModal.addEventListener("click", (event) => {
    if (event.target === adminModal) closeAdmin();
  });
}
