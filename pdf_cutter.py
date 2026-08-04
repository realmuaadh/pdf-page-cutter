import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import io
import os
import json
from pypdf import PdfReader, PdfWriter

# Optional: page thumbnails for the visual cut preview. The app still works
# (numeric entry only) if these are not installed.
try:
    import pypdfium2 as pdfium
    from PIL import ImageTk
    PREVIEW_OK = True
except Exception:
    PREVIEW_OK = False

# Required only for partial-page cuts: PyMuPDF actually deletes the content in
# the discarded band rather than covering it, so the text cannot be recovered
# by a text extractor. Plain whole-page extraction works without it.
try:
    import pymupdf
    REDACT_OK = True
except Exception:
    try:
        import fitz as pymupdf          # PyMuPDF < 1.24 module name
        REDACT_OK = True
    except Exception:
        REDACT_OK = False


# ── Redaction helper ────────────────────────────────────────────────────────
def redact_bands(data, specs):
    """Permanently delete horizontal bands of content from selected pages.

    data  : PDF file contents as bytes.
    specs : {page_index: (top_frac, bottom_frac)} — the fraction of the page,
            measured from the VISUAL top and bottom, to erase.

    Returns the modified PDF as bytes. Text, images and vector art inside a
    band are removed from the file, not merely hidden, so nothing leaks into
    text extraction. The band is filled white and the page keeps its size.
    """
    doc = pymupdf.open(stream=data, filetype="pdf")
    try:
        for idx, (top, bot) in specs.items():
            top = max(0.0, min(1.0, top))
            bot = max(0.0, min(1.0, bot))
            if top <= 0 and bot <= 0:
                continue
            page = doc[idx]
            r = page.rect                  # rotation-aware ("visual") rect
            # Annotation coordinates are interpreted in UNROTATED page space,
            # so map the visual band back through the derotation matrix.
            m = page.derotation_matrix
            bands = []
            if top > 0:
                bands.append(pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + top * r.height))
            if bot > 0:
                bands.append(pymupdf.Rect(r.x0, r.y1 - bot * r.height, r.x1, r.y1))
            for b in bands:
                page.add_redact_annot(b * m, fill=(1, 1, 1))
            page.apply_redactions(
                images=pymupdf.PDF_REDACT_IMAGE_REMOVE,
                graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
                text=pymupdf.PDF_REDACT_TEXT_REMOVE,
            )
        out = io.BytesIO()
        doc.save(out, garbage=3, deflate=True)
        return out.getvalue()
    finally:
        doc.close()

# ── Config persistence ──────────────────────────────────────────────────────
CONFIG_DIR  = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PDFPageCutter")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

# ── Translations ────────────────────────────────────────────────────────────
T = {
    "en": {
        "title":           "PDF Page Cutter",
        "header":          "PDF Page Cutter",
        "sec_input":       "INPUT PDF",
        "browse":          "Browse…",
        "no_file":         "No file selected",
        "total_pages":     "Total pages: {n}",
        "sec_range":       "PAGE RANGE",
        "from_lbl":        "From page",
        "to_lbl":          "to page",
        "sec_folder":      "SAVE TO FOLDER",
        "sec_name":        "OUTPUT FILE NAME",
        "dot_pdf":         ".pdf",
        "save_btn":        "  Save Pages  ",
        "status_saved":    "Saved {count} page(s) successfully.",
        "sec_cut":         "PARTIAL PAGE CUT  (drag the lines)",
        "cut_first":       "First page — start at",
        "cut_last":        "Last page — end at",
        "cut_reset":       "Reset",
        "cut_hint":        "Cut-away content is permanently deleted, not just hidden.",
        "cut_nopreview":   "Preview unavailable\n(install pypdfium2 + Pillow)",
        "cut_pick_pdf":    "Select a PDF to preview",
        "err_cut_order":   "On a single page, the start position must be above the end position.",
        "err_no_pymupdf":  ("Partial page cuts need PyMuPDF, which is not installed.\n\n"
                            "Install it with:\n    pip install PyMuPDF\n\n"
                            "Or set the cut back to 0% / 100% to save whole pages."),
        "warn_no_file":    "Please select a PDF file first.",
        "warn_no_folder":  "Please choose an output folder.",
        "err_int":         "Page numbers must be integers.",
        "err_ge1":         "Page numbers must be at least 1.",
        "err_order":       "Start page must be ≤ end page.",
        "err_overflow":    "End page ({end}) exceeds total pages ({total}).",
        "err_read":        "Could not read PDF:\n{e}",
        "err_save":        "Failed to save PDF:\n{e}",
        "err_title":       "Error",
        "warn_title":      "Warning",
        "overwrite_title": "Overwrite?",
        "overwrite_q":     '"{name}" already exists. Overwrite?',
        "done_title":      "Done!",
        "done_msg":        "Saved {count} page(s) to:\n{path}\n\nOpen the folder?",
        "lang_menu":       "Language",
        "rtl":             False,
    },
    "ar": {
        "title":           "قاطع صفحات PDF",
        "header":          "قاطع صفحات PDF",
        "sec_input":       "ملف PDF المصدر",
        "browse":          "استعراض…",
        "no_file":         "لم يتم اختيار ملف",
        "total_pages":     "إجمالي الصفحات: {n}",
        "sec_range":       "نطاق الصفحات",
        "from_lbl":        "من صفحة",
        "to_lbl":          "إلى صفحة",
        "sec_folder":      "مجلد الحفظ",
        "sec_name":        "اسم الملف الناتج",
        "dot_pdf":         ".pdf",
        "save_btn":        "  حفظ الصفحات  ",
        "status_saved":    "تم حفظ {count} صفحة بنجاح.",
        "sec_cut":         "قص جزئي للصفحة  (اسحب الخطوط)",
        "cut_first":       "الصفحة الأولى — البداية عند",
        "cut_last":        "الصفحة الأخيرة — النهاية عند",
        "cut_reset":       "إعادة تعيين",
        "cut_hint":        "المحتوى المقصوص يُحذف نهائياً، ولا يتم إخفاؤه فقط.",
        "cut_nopreview":   "المعاينة غير متاحة\n(ثبّت pypdfium2 و Pillow)",
        "cut_pick_pdf":    "اختر ملف PDF للمعاينة",
        "err_cut_order":   "في حالة الصفحة الواحدة، يجب أن يكون موضع البداية أعلى من موضع النهاية.",
        "err_no_pymupdf":  ("القص الجزئي للصفحة يتطلب مكتبة PyMuPDF غير المثبتة.\n\n"
                            "ثبّتها بالأمر:\n    pip install PyMuPDF\n\n"
                            "أو أعد ضبط القص إلى 0% / 100% لحفظ صفحات كاملة."),
        "warn_no_file":    "يرجى اختيار ملف PDF أولاً.",
        "warn_no_folder":  "يرجى اختيار مجلد الحفظ.",
        "err_int":         "يجب أن تكون أرقام الصفحات أعداداً صحيحة.",
        "err_ge1":         "يجب أن تكون أرقام الصفحات 1 على الأقل.",
        "err_order":       "يجب أن تكون الصفحة الأولى ≤ الصفحة الأخيرة.",
        "err_overflow":    "الصفحة الأخيرة ({end}) تتجاوز إجمالي الصفحات ({total}).",
        "err_read":        "تعذر قراءة ملف PDF:\n{e}",
        "err_save":        "فشل حفظ ملف PDF:\n{e}",
        "err_title":       "خطأ",
        "warn_title":      "تحذير",
        "overwrite_title": "استبدال؟",
        "overwrite_q":     'الملف "{name}" موجود بالفعل. هل تريد استبداله؟',
        "done_title":      "تم!",
        "done_msg":        "تم حفظ {count} صفحة في:\n{path}\n\nهل تريد فتح المجلد؟",
        "lang_menu":       "اللغة",
        "rtl":             True,
    },
}

LANG_NAMES = {"en": "English", "ar": "العربية"}


# ── Language chooser ────────────────────────────────────────────────────────
def choose_language(saved=None):
    """Show a compact language-picker dialog; return 'en' or 'ar'."""
    dlg = tk.Tk()
    dlg.withdraw()
    dlg.title("PDF Page Cutter")

    win = tk.Toplevel(dlg)
    win.title("Choose Language / اختر اللغة")
    win.resizable(False, False)
    win.configure(bg="white")

    chosen = tk.StringVar(value=saved or "en")

    # Header stripe
    hdr = tk.Frame(win, bg="#2563eb", height=48)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="PDF Page Cutter",
             font=("Segoe UI", 13, "bold"), bg="#2563eb", fg="white").pack(pady=12)

    body = tk.Frame(win, bg="white", padx=30, pady=20)
    body.pack(fill="both")

    tk.Label(body, text="Choose Language / اختر اللغة",
             font=("Segoe UI", 10), bg="white", fg="#374151").pack(pady=(0, 14))

    for code, name in LANG_NAMES.items():
        rb = tk.Radiobutton(body, text=name, variable=chosen, value=code,
                            font=("Segoe UI", 11), bg="white",
                            activebackground="white", fg="#1f2937",
                            selectcolor="#dbeafe")
        rb.pack(anchor="w", pady=3)

    def confirm():
        save_config({"lang": chosen.get()})
        win.destroy()
        dlg.destroy()

    tk.Button(body, text="OK / موافق", command=confirm,
              font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white",
              activebackground="#1d4ed8", relief="flat",
              padx=18, pady=6).pack(pady=(16, 0))

    # Center on screen
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", confirm)
    dlg.wait_window(win)
    return chosen.get()


# ── Cut preview widget ──────────────────────────────────────────────────────
class CutPreview(tk.Frame):
    """A page thumbnail with a draggable horizontal cut line.

    mode "start" → everything ABOVE the line is discarded (first page).
    mode "end"   → everything BELOW the line is discarded (last page).
    `var` holds the line position as a percentage measured from the page top.
    """
    PAD = 5

    def __init__(self, parent, strings, mode, var, box_w=148, box_h=196):
        super().__init__(parent, bg="white")
        self.s = strings
        self.mode = mode
        self.var = var
        self.box_w, self.box_h = box_w, box_h
        self.img_tk = None
        self.img_x = self.PAD
        self.img_y = self.PAD
        self.img_w, self.img_h = box_w, box_h
        self._doc = None          # remembered so a resize can re-render
        self._index = 0

        tk.Label(self, text=strings["cut_first"] if mode == "start" else strings["cut_last"],
                 font=("Segoe UI", 8, "bold"), bg="white", fg="#374151").pack()

        self.canvas = tk.Canvas(self, width=box_w + 2 * self.PAD,
                                height=box_h + 2 * self.PAD,
                                bg="white", highlightthickness=0, cursor="sb_v_double_arrow")
        self.canvas.pack(pady=(4, 4))
        self.canvas.bind("<Button-1>", self._on_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        entry_row = tk.Frame(self, bg="white")
        entry_row.pack()
        tk.Spinbox(entry_row, textvariable=var, from_=0, to=100, increment=1,
                   width=5, font=("Segoe UI", 9), relief="solid", bd=1,
                   command=self.redraw).pack(side="left")
        tk.Label(entry_row, text="%", font=("Segoe UI", 9),
                 bg="white", fg="#6b7280").pack(side="left", padx=(3, 0))

        # Keep the trace so it can be detached when the widget is rebuilt
        # (the language switch tears the whole UI down and re-creates it).
        self._trace_id = var.trace_add("write", lambda *_: self.redraw())
        self.bind("<Destroy>", self._on_destroy)
        self.redraw()

    def _on_destroy(self, event):
        if event.widget is not self or self._trace_id is None:
            return
        try:
            self.var.trace_remove("write", self._trace_id)
        except Exception:
            pass
        self._trace_id = None

    # ── helpers ──────────────────────────────────────────────────────────────
    def _pct(self):
        try:
            return max(0.0, min(100.0, float(self.var.get())))
        except Exception:
            return 0.0 if self.mode == "start" else 100.0

    def _on_drag(self, event):
        pct = (event.y - self.img_y) / max(1, self.img_h) * 100.0
        self.var.set(round(max(0.0, min(100.0, pct)), 1))

    # ── thumbnail ────────────────────────────────────────────────────────────
    def clear(self):
        self.img_tk = None
        self._doc = None
        self.img_w, self.img_h = self.box_w, self.box_h
        self.img_x = self.img_y = self.PAD
        self.redraw()

    def set_box(self, box_w, box_h):
        """Resize the thumbnail area and re-render at the new scale."""
        box_w, box_h = int(box_w), int(box_h)
        if box_w == self.box_w and box_h == self.box_h:
            return
        self.box_w, self.box_h = box_w, box_h
        try:
            self.canvas.config(width=box_w + 2 * self.PAD,
                               height=box_h + 2 * self.PAD)
        except Exception:
            return
        if self._doc is not None:
            self.set_page(self._doc, self._index)
        else:
            self.clear()

    def set_page(self, doc, index):
        """Render page `index` of an open pypdfium2 document into the thumbnail."""
        self._doc, self._index = doc, index
        if not PREVIEW_OK or doc is None:
            return self.clear()
        try:
            page = doc[index]
            pw, ph = page.get_size()          # already accounts for /Rotate
            scale = min(self.box_w / pw, self.box_h / ph)
            pil = page.render(scale=scale).to_pil().convert("RGB")
            self.img_tk = ImageTk.PhotoImage(pil)
            self.img_w, self.img_h = pil.size
            self.img_x = self.PAD + (self.box_w - self.img_w) // 2
            self.img_y = self.PAD + (self.box_h - self.img_h) // 2
        except Exception:
            return self.clear()
        self.redraw()

    # ── painting ─────────────────────────────────────────────────────────────
    def redraw(self):
        c = self.canvas
        try:
            if not c.winfo_exists():
                return
        except Exception:
            return
        c.delete("all")
        x0, y0 = self.img_x, self.img_y
        x1, y1 = x0 + self.img_w, y0 + self.img_h

        if self.img_tk is not None:
            c.create_image(x0, y0, anchor="nw", image=self.img_tk)
        else:
            c.create_rectangle(x0, y0, x1, y1, fill="#f9fafb", outline="")
            msg = self.s["cut_pick_pdf"] if PREVIEW_OK else self.s["cut_nopreview"]
            c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=msg,
                          font=("Segoe UI", 8), fill="#9ca3af",
                          width=self.box_w - 12, justify="center")

        y = y0 + self.img_h * self._pct() / 100.0

        # Hatched grey over the part that will be blanked out.
        if self.mode == "start":
            hy0, hy1 = y0, y
        else:
            hy0, hy1 = y, y1
        if hy1 - hy0 > 0.5:
            c.create_rectangle(x0, hy0, x1, hy1, fill="#6b7280",
                               stipple="gray50", outline="")

        c.create_rectangle(x0, y0, x1, y1, outline="#d1d5db")
        c.create_line(x0, y, x1, y, fill="#dc2626", width=2)
        c.create_rectangle((x0 + x1) / 2 - 13, y - 3, (x0 + x1) / 2 + 13, y + 3,
                           fill="#dc2626", outline="")


# ── Main application ────────────────────────────────────────────────────────
class PDFCutterApp:
    def __init__(self, root, lang="en"):
        self.root = root
        self.lang = lang
        self.s    = T[lang]

        self.pdf_path   = tk.StringVar()
        self.total_pages = tk.IntVar(value=0)
        self.start_page = tk.StringVar(value="1")
        self.end_page   = tk.StringVar(value="1")
        self.output_dir = tk.StringVar()
        self.output_name = tk.StringVar(value="output.pdf")

        # Partial-page cut: percentages measured from the top of the page.
        self.start_pct = tk.DoubleVar(value=0.0)
        self.end_pct   = tk.DoubleVar(value=100.0)
        self.doc = None            # open pypdfium2 document, for thumbnails
        self._refresh_job = None
        self._fit_job = None

        self.root.title(self.s["title"])
        self.root.resizable(True, True)
        self.root.minsize(540, 470)
        self.root.configure(bg="#f0f0f0")

        self._build_ui()
        self._center(600, 760)

        self.start_page.trace_add("write", lambda *_: self._schedule_preview())
        self.end_page.trace_add("write",   lambda *_: self._schedule_preview())

    # ── Geometry ─────────────────────────────────────────────────────────────
    def _center(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        # Never open taller than the screen, or the Save button lands off-screen
        # on smaller displays. Leave room for the taskbar and title bar.
        w = max(self.root.minsize()[0], min(w, sw - 40))
        h = max(self.root.minsize()[1], min(h, sh - 90))
        self.root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")

    # ── Layout helpers ────────────────────────────────────────────────────────
    def _pack_side(self, primary=True):
        """Return pack side respecting RTL."""
        if self.s["rtl"]:
            return "right" if primary else "left"
        return "left" if primary else "right"

    def _anchor(self):
        return "e" if self.s["rtl"] else "w"

    def _justify(self):
        return tk.RIGHT if self.s["rtl"] else tk.LEFT

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        s = self.s
        rtl = s["rtl"]

        # ── Menu bar ─────────────────────────────────────────────────────────
        menubar = tk.Menu(self.root)
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English",  command=lambda: self._switch_lang("en"))
        lang_menu.add_command(label="العربية",  command=lambda: self._switch_lang("ar"))
        menubar.add_cascade(label=s["lang_menu"], menu=lang_menu)
        self.root.config(menu=menubar)

        # ── Header stripe ─────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#2563eb", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=s["header"],
                 font=("Segoe UI", 16, "bold"),
                 bg="#2563eb", fg="white").pack(
                     side=self._pack_side(), padx=20, pady=12)

        # ── White card ────────────────────────────────────────────────────────
        card = tk.Frame(self.root, bg="white")
        card.pack(fill="both", expand=True, padx=20, pady=16)
        # Stop the card's children from dictating the window size — the window
        # drives the card, not the other way round. Without this, growing a
        # thumbnail would grow the window, which would grow the thumbnail...
        card.pack_propagate(False)

        def sec(parent, text):
            tk.Label(parent, text=text,
                     font=("Segoe UI", 9, "bold"),
                     bg="white", fg="#6b7280",
                     anchor=self._anchor(),
                     justify=self._justify()).pack(
                         fill="x", padx=16, pady=(12, 0))

        def row(parent):
            f = tk.Frame(parent, bg="white")
            f.pack(fill="x", padx=16, pady=3)
            return f

        primary = self._pack_side(True)
        secondary = self._pack_side(False)

        # Three bands. `top` and `bottom` claim their natural height first, so
        # the fixed controls can never be squeezed out; `middle` then expands
        # into whatever is left over and carries the resizable thumbnails.
        # Packing order matters here: top, then bottom, then the expander.
        top_area = tk.Frame(card, bg="white")
        top_area.pack(side="top", fill="x")
        bottom_area = tk.Frame(card, bg="white")
        bottom_area.pack(side="bottom", fill="x")
        mid_area = tk.Frame(card, bg="white")
        mid_area.pack(side="top", fill="both", expand=True)

        # ── Input PDF ─────────────────────────────────────────────────────────
        sec(top_area, s["sec_input"])
        r1 = row(top_area)
        tk.Button(r1, text=s["browse"], command=self._pick_pdf,
                  font=("Segoe UI", 9), bg="#2563eb", fg="white",
                  activebackground="#1d4ed8", relief="flat",
                  padx=10).pack(side=secondary, padx=(0, 6) if not rtl else (6, 0))
        tk.Entry(r1, textvariable=self.pdf_path,
                 font=("Segoe UI", 10), state="readonly",
                 width=42, relief="solid", bd=1,
                 justify=self._justify()).pack(side=primary, fill="x")

        self.pages_label = tk.Label(top_area, text=s["no_file"],
                                    font=("Segoe UI", 9), bg="white", fg="#9ca3af",
                                    anchor=self._anchor())
        self.pages_label.pack(fill="x", padx=16)

        # ── Page range ────────────────────────────────────────────────────────
        sec(top_area, s["sec_range"])
        r2 = row(top_area)
        if not rtl:
            tk.Label(r2, text=s["from_lbl"],
                     font=("Segoe UI", 10), bg="white").pack(side="left")
            tk.Spinbox(r2, textvariable=self.start_page, from_=1, to=9999,
                       width=6, font=("Segoe UI", 10),
                       relief="solid", bd=1).pack(side="left", padx=(6, 16))
            tk.Label(r2, text=s["to_lbl"],
                     font=("Segoe UI", 10), bg="white").pack(side="left")
            tk.Spinbox(r2, textvariable=self.end_page, from_=1, to=9999,
                       width=6, font=("Segoe UI", 10),
                       relief="solid", bd=1).pack(side="left", padx=(6, 0))
        else:
            tk.Spinbox(r2, textvariable=self.end_page, from_=1, to=9999,
                       width=6, font=("Segoe UI", 10),
                       relief="solid", bd=1).pack(side="right")
            tk.Label(r2, text=s["to_lbl"],
                     font=("Segoe UI", 10), bg="white").pack(side="right", padx=(16, 6))
            tk.Spinbox(r2, textvariable=self.start_page, from_=1, to=9999,
                       width=6, font=("Segoe UI", 10),
                       relief="solid", bd=1).pack(side="right")
            tk.Label(r2, text=s["from_lbl"],
                     font=("Segoe UI", 10), bg="white").pack(side="right", padx=(0, 6))

        # ── Partial page cut ──────────────────────────────────────────────────
        sec(mid_area, s["sec_cut"])
        # expand=True: this is the section that soaks up any extra height when
        # the window is resized, so the thumbnails grow with the window.
        cut_row = tk.Frame(mid_area, bg="white")
        cut_row.pack(fill="both", expand=True, padx=16, pady=(4, 0))
        self.cut_row = cut_row
        cut_row.bind("<Configure>", lambda e: self._schedule_fit())

        inner = tk.Frame(cut_row, bg="white")
        inner.pack(expand=True)

        self.prev_start = CutPreview(inner, s, "start", self.start_pct)
        self.prev_end   = CutPreview(inner, s, "end",   self.end_pct)
        first, second = (self.prev_end, self.prev_start) if rtl else (self.prev_start, self.prev_end)
        first.pack(side="left", padx=(0, 14))
        second.pack(side="left")

        hint_row = tk.Frame(mid_area, bg="white")
        hint_row.pack(fill="x", padx=16, pady=(2, 0))
        tk.Button(hint_row, text=s["cut_reset"], command=self._reset_cut,
                  font=("Segoe UI", 8), bg="#e5e7eb", fg="#374151",
                  activebackground="#d1d5db", relief="flat",
                  padx=8).pack(side=secondary)
        tk.Label(hint_row, text=s["cut_hint"], font=("Segoe UI", 8),
                 bg="white", fg="#9ca3af",
                 anchor=self._anchor()).pack(side=primary, fill="x")

        # ── Output folder ─────────────────────────────────────────────────────
        sec(bottom_area, s["sec_folder"])
        r3 = row(bottom_area)
        tk.Button(r3, text=s["browse"], command=self._pick_dir,
                  font=("Segoe UI", 9), bg="#2563eb", fg="white",
                  activebackground="#1d4ed8", relief="flat",
                  padx=10).pack(side=secondary, padx=(0, 6) if not rtl else (6, 0))
        tk.Entry(r3, textvariable=self.output_dir,
                 font=("Segoe UI", 10), state="readonly",
                 width=42, relief="solid", bd=1,
                 justify=self._justify()).pack(side=primary, fill="x")

        # ── Output name ───────────────────────────────────────────────────────
        sec(bottom_area, s["sec_name"])
        r4 = row(bottom_area)
        if not rtl:
            tk.Entry(r4, textvariable=self.output_name,
                     font=("Segoe UI", 10), width=38,
                     relief="solid", bd=1).pack(side="left")
            tk.Label(r4, text=s["dot_pdf"],
                     font=("Segoe UI", 10), bg="white",
                     fg="#6b7280").pack(side="left", padx=(4, 0))
        else:
            tk.Label(r4, text=s["dot_pdf"],
                     font=("Segoe UI", 10), bg="white",
                     fg="#6b7280").pack(side="right")
            tk.Entry(r4, textvariable=self.output_name,
                     font=("Segoe UI", 10), width=38,
                     relief="solid", bd=1,
                     justify=tk.RIGHT).pack(side="right", padx=(0, 4))

        # ── Divider + save ────────────────────────────────────────────────────
        tk.Frame(bottom_area, bg="#e5e7eb", height=1).pack(fill="x", padx=16,
                                                           pady=(14, 0))
        btn_row = tk.Frame(bottom_area, bg="white")
        btn_row.pack(fill="x", padx=16, pady=12)

        self.status_label = tk.Label(btn_row, text="",
                                     font=("Segoe UI", 9), bg="white", fg="#16a34a",
                                     anchor=self._anchor())
        self.status_label.pack(side=primary, fill="x", expand=True)

        tk.Button(btn_row, text=s["save_btn"],
                  command=self._save_pages,
                  font=("Segoe UI", 11, "bold"),
                  bg="#16a34a", fg="white",
                  activebackground="#15803d",
                  relief="flat", padx=12, pady=6).pack(side=secondary)

        self._schedule_fit()

    # ── Language switch ───────────────────────────────────────────────────────
    def _switch_lang(self, lang):
        if lang == self.lang:
            return
        save_config({"lang": lang})
        for w in self.root.winfo_children():
            w.destroy()
        self.lang = lang
        self.s    = T[lang]
        self._build_ui()
        self.root.title(self.s["title"])
        if self.pdf_path.get():
            self.pages_label.config(
                text=self.s["total_pages"].format(n=self.total_pages.get()), fg="#374151")
        self._refresh_previews()

    # ── Cut preview plumbing ──────────────────────────────────────────────────
    def _reset_cut(self):
        self.start_pct.set(0.0)
        self.end_pct.set(100.0)

    # Vertical space each preview needs for its title label and spinbox row.
    PREVIEW_CHROME = 56
    FLOOR_BOX = (60, 80)
    MAX_BOX = (900, 1200)

    def _schedule_fit(self):
        """Debounce thumbnail re-rendering while the window is being dragged."""
        if self._fit_job is not None:
            try:
                self.root.after_cancel(self._fit_job)
            except Exception:
                pass
        self._fit_job = self.root.after(180, self._fit_previews)

    def _fit_previews(self):
        """Scale the two thumbnails to whatever space the window now offers."""
        self._fit_job = None
        if not hasattr(self, "prev_start"):
            return
        try:
            if not self.cut_row.winfo_exists():
                return
            avail_w = self.cut_row.winfo_width()
            avail_h = self.cut_row.winfo_height()
        except Exception:
            return
        if avail_w < 2 or avail_h < 2:        # not laid out yet
            return

        # Two previews side by side, 14px gap, 5px canvas padding each side.
        # Never ask for MORE than the space we were given, or the toplevel's
        # geometry propagation would grow the window right back and the two
        # would fight each other.
        box_w = (avail_w - 14) // 2 - 2 * CutPreview.PAD
        box_h = avail_h - self.PREVIEW_CHROME - 2 * CutPreview.PAD
        box_w = max(self.FLOOR_BOX[0], min(self.MAX_BOX[0], box_w))
        box_h = max(self.FLOOR_BOX[1], min(self.MAX_BOX[1], box_h))

        for prev in (self.prev_start, self.prev_end):
            prev.set_box(box_w, box_h)

    def _schedule_preview(self):
        """Debounce preview re-rendering while the spinboxes are being typed in."""
        if self._refresh_job is not None:
            try:
                self.root.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = self.root.after(250, self._refresh_previews)

    def _refresh_previews(self):
        self._refresh_job = None
        if self.doc is None:
            self.prev_start.clear()
            self.prev_end.clear()
            return
        total = self.total_pages.get()
        try:
            start = int(self.start_page.get())
            end   = int(self.end_page.get())
        except ValueError:
            return
        if not (1 <= start <= total and 1 <= end <= total):
            return
        self.prev_start.set_page(self.doc, start - 1)
        self.prev_end.set_page(self.doc, end - 1)
        self._schedule_fit()

    # ── File pickers ──────────────────────────────────────────────────────────
    def _pick_pdf(self):
        path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return
        try:
            reader = PdfReader(path)
            n = len(reader.pages)
        except Exception as e:
            messagebox.showerror(self.s["err_title"],
                                 self.s["err_read"].format(e=e))
            return
        self.pdf_path.set(path)
        self.total_pages.set(n)
        self.pages_label.config(text=self.s["total_pages"].format(n=n), fg="#374151")
        self.start_page.set("1")
        self.end_page.set(str(n))
        if not self.output_dir.get():
            self.output_dir.set(os.path.dirname(path))
        base = os.path.splitext(os.path.basename(path))[0]
        self.output_name.set(f"{base}_pages.pdf")
        self.status_label.config(text="")

        # (Re)open the document for thumbnails and reset the cut lines.
        if self.doc is not None:
            try:
                self.doc.close()
            except Exception:
                pass
            self.doc = None
        if PREVIEW_OK:
            try:
                # Load from bytes so the source file is never left locked open,
                # which would block saving over it on Windows.
                with open(path, "rb") as fh:
                    self.doc = pdfium.PdfDocument(fh.read())
            except Exception:
                self.doc = None
        self._reset_cut()
        self._refresh_previews()

    def _pick_dir(self):
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_dir.set(path)

    # ── Save logic ────────────────────────────────────────────────────────────
    def _save_pages(self):
        s = self.s
        src = self.pdf_path.get()
        if not src:
            messagebox.showwarning(s["warn_title"], s["warn_no_file"])
            return
        out_dir = self.output_dir.get()
        if not out_dir:
            messagebox.showwarning(s["warn_title"], s["warn_no_folder"])
            return
        try:
            start = int(self.start_page.get())
            end   = int(self.end_page.get())
        except ValueError:
            messagebox.showerror(s["err_title"], s["err_int"])
            return
        total = self.total_pages.get()
        if start < 1 or end < 1:
            messagebox.showerror(s["err_title"], s["err_ge1"])
            return
        if start > end:
            messagebox.showerror(s["err_title"], s["err_order"])
            return
        if end > total:
            messagebox.showerror(s["err_title"], s["err_overflow"].format(end=end, total=total))
            return

        # Partial-page cut positions, as fractions from the top of the page.
        def _frac(var, default):
            try:
                return max(0.0, min(1.0, float(var.get()) / 100.0))
            except Exception:
                return default
        top_cut = _frac(self.start_pct, 0.0)    # erase above this on the first page
        bot_cut = _frac(self.end_pct, 1.0)      # erase below this on the last page
        if start == end and top_cut > 0 and bot_cut < 1 and top_cut >= bot_cut:
            messagebox.showerror(s["err_title"], s["err_cut_order"])
            return
        cutting = top_cut > 0 or bot_cut < 1
        if cutting and not REDACT_OK:
            messagebox.showerror(s["err_title"], s["err_no_pymupdf"])
            return

        name = self.output_name.get().strip() or "output"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        out_path = os.path.join(out_dir, name)

        if os.path.exists(out_path):
            if not messagebox.askyesno(s["overwrite_title"],
                                       s["overwrite_q"].format(name=name)):
                return
        try:
            reader = PdfReader(src)
            writer = PdfWriter()
            for i in range(start - 1, end):
                writer.add_page(reader.pages[i])
            buf = io.BytesIO()
            writer.write(buf)
            data = buf.getvalue()

            if cutting:
                last = end - start                     # index of the last page kept
                specs = {}
                if top_cut > 0:
                    specs[0] = [top_cut, 0.0]
                if bot_cut < 1:
                    specs.setdefault(last, [0.0, 0.0])[1] = 1.0 - bot_cut
                data = redact_bands(data, {k: tuple(v) for k, v in specs.items()})

            with open(out_path, "wb") as f:
                f.write(data)
        except Exception as e:
            messagebox.showerror(s["err_title"], s["err_save"].format(e=e))
            return

        count = end - start + 1
        self.status_label.config(text=s["status_saved"].format(count=count))
        if messagebox.askyesno(s["done_title"],
                               s["done_msg"].format(count=count, path=out_path)):
            os.startfile(out_dir)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cfg  = load_config()
    lang = cfg.get("lang")
    if lang not in T:
        lang = choose_language()

    root = tk.Tk()
    PDFCutterApp(root, lang)
    root.mainloop()
