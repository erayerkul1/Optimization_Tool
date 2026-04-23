"""
Fastener Force Analyzer  v4
MSC Nastran · FX=Tension, FY/FZ=Shear
Tüm metrikler · Element ID filtresi
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv, math
from pathlib import Path

METRICS = [
    {"id": "M01", "label": "M01  FZ",
     "fn": lambda fx, fy, fz: fz},
    {"id": "M02", "label": "M02  -FZ",
     "fn": lambda fx, fy, fz: -fz},
    {"id": "M03", "label": "M03  FY",
     "fn": lambda fx, fy, fz: fy},
    {"id": "M04", "label": "M04  -FY",
     "fn": lambda fx, fy, fz: -fy},
    {"id": "M05", "label": "M05  FX",
     "fn": lambda fx, fy, fz: fx},
    {"id": "M06", "label": "M06  -FX",
     "fn": lambda fx, fy, fz: -fx},
    {"id": "M07", "label": "M07  |FX|",
     "fn": lambda fx, fy, fz: abs(fx)},
    {"id": "M08", "label": "M08  Vr=√(FY²+FZ²)",
     "fn": lambda fx, fy, fz: math.sqrt(fy**2 + fz**2)},
    {"id": "M09", "label": "M09  √(FZ²+FY²)",
     "fn": lambda fx, fy, fz: math.sqrt(fz**2 + fy**2)},
    {"id": "M10", "label": "M10  √(FZ²+FY²)+|FX|",
     "fn": lambda fx, fy, fz: math.sqrt(fz**2 + fy**2) + abs(fx)},
    {"id": "M11", "label": "M11  √((2FZ)²+FY²)",
     "fn": lambda fx, fy, fz: math.sqrt((2*fz)**2 + fy**2)},
    {"id": "M12", "label": "M12  √(FZ²+(2FY)²)",
     "fn": lambda fx, fy, fz: math.sqrt(fz**2 + (2*fy)**2)},
    {"id": "M13", "label": "M13  √((2FZ)²+FY²)+|FX|",
     "fn": lambda fx, fy, fz: math.sqrt((2*fz)**2 + fy**2) + abs(fx)},
    {"id": "M14", "label": "M14  √(FZ²+(2FY)²)+|FX|",
     "fn": lambda fx, fy, fz: math.sqrt(fz**2 + (2*fy)**2) + abs(fx)},
    {"id": "M15", "label": "M15  |FX|+Vr",
     "fn": lambda fx, fy, fz: abs(fx) + math.sqrt(fy**2 + fz**2)},
    {"id": "M16", "label": "M16  FX+Vr",
     "fn": lambda fx, fy, fz: fx + math.sqrt(fy**2 + fz**2)},
    {"id": "M17", "label": "M17  √((2FX)²+Vr²)",
     "fn": lambda fx, fy, fz: math.sqrt((2*fx)**2 + fy**2 + fz**2)},
    {"id": "M18", "label": "M18  √(FX²+(2Vr)²)",
     "fn": lambda fx, fy, fz: math.sqrt(fx**2 + (2*fy)**2 + (2*fz)**2)},
    {"id": "M19", "label": "M19  √(FX²+FY²+FZ²)",
     "fn": lambda fx, fy, fz: math.sqrt(fx**2 + fy**2 + fz**2)},
]

BG, BG2, BG3 = "#0d1117", "#161b22", "#21262d"
BORDER = "#30363d"
ACCENT = "#58a6ff"
GREEN  = "#3fb950"
RED_   = "#f85149"
TEXT   = "#e6edf3"
MUTED  = "#8b949e"
FM = ("Consolas", 10)
FH = ("Consolas", 11, "bold")
FS = ("Consolas", 9)
FT = ("Consolas", 9, "bold")


def calc_all(fx, fy, fz):
    return {m["id"]: m["fn"](fx, fy, fz) for m in METRICS}


def entry_cfg(**kw):
    return dict(bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                font=FM, bd=0, highlightthickness=1,
                highlightbackground=BORDER, highlightcolor=ACCENT, **kw)


class FastenerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fastener Force Analyzer  ·  MSC Nastran  ·  FX=Tension  FY/FZ=Shear")
        self.geometry("1600x820")
        self.minsize(1200, 650)
        self.configure(bg=BG)

        self.raw_data    = []
        self.filtered    = []
        self.mode_var    = tk.StringVar(value="max")
        self.thresh_var  = tk.StringVar(value="")
        self.eid_all_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._style_ttk()
        self._on_mode_change()
        self._on_eid_toggle()

    # ── STYLE ─────────────────────────────────────────────────────────────────
    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview",
            background=BG2, foreground=TEXT, fieldbackground=BG2,
            font=FM, rowheight=22, borderwidth=0)
        s.configure("Treeview.Heading",
            background=BG3, foreground=MUTED, font=FS,
            relief="flat", borderwidth=0)
        s.map("Treeview",
            background=[("selected", "#1f3a5f")],
            foreground=[("selected", TEXT)])
        for o in ("Vertical", "Horizontal"):
            s.configure(f"{o}.TScrollbar",
                background=BG3, troughcolor=BG2, borderwidth=0, arrowsize=11)
        s.configure("TCombobox",
            fieldbackground=BG, background=BG3, foreground=TEXT,
            selectbackground="#1f3a5f", selectforeground=TEXT)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg="#0d2137", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ⚙  FASTENER FORCE ANALYZER",
                 font=("Consolas", 13, "bold"), fg=ACCENT, bg="#0d2137").pack(side="left", padx=20)
        tk.Label(hdr, text="FX=Tension  |  FY/FZ=Shear  |  19 Metrik  |  Element-bazlı",
                 font=FS, fg=MUTED, bg="#0d2137").pack(side="left", padx=6)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG2, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._build_left(left)

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    # ── SOL PANEL ─────────────────────────────────────────────────────────────
    def _build_left(self, p):
        pad = {"padx": 14, "pady": 4}

        # CSV
        sec = self._sec(p, "📂  CSV DOSYASI")
        tk.Button(sec, text="Dosya Seç…", command=self._load_csv,
                  bg="#238636", fg="white", font=FH, relief="flat",
                  cursor="hand2", padx=8, pady=6,
                  activebackground="#2ea043", activeforeground="white"
                  ).pack(fill="x", **pad)
        self.file_lbl = tk.Label(sec, text="Henüz dosya seçilmedi",
                                 font=FS, fg=MUTED, bg=BG2,
                                 wraplength=260, justify="left")
        self.file_lbl.pack(fill="x", padx=14, pady=(0, 6))

        # Element ID filtresi
        sec2 = self._sec(p, "🔢  ELEMENT ID FİLTRESİ")
        self.eid_all_cb = tk.Checkbutton(
            sec2, text="Tüm elementler", variable=self.eid_all_var,
            bg=BG2, fg=TEXT, selectcolor=BG, activebackground=BG2,
            font=FS, cursor="hand2", command=self._on_eid_toggle)
        self.eid_all_cb.pack(anchor="w", padx=14, pady=(4, 2))
        tk.Label(sec2, text="ID'ler (virgülle: 123,456,789):",
                 font=FS, fg=MUTED, bg=BG2).pack(anchor="w", padx=14)
        self.eid_entry = tk.Entry(sec2, **entry_cfg(), width=20)
        self.eid_entry.pack(fill="x", padx=14, pady=(3, 8), ipady=5)

        # Filtre metriği
        sec3 = self._sec(p, "📐  FİLTRE METRİĞİ")
        tk.Label(sec3, text="MAX / MIN / Eşik için metrik:",
                 font=FS, fg=MUTED, bg=BG2).pack(anchor="w", padx=14, pady=(4, 2))
        self.metric_var = tk.StringVar()
        self.metric_cb = ttk.Combobox(
            sec3, textvariable=self.metric_var,
            values=[m["label"] for m in METRICS],
            state="readonly", font=FS, width=26)
        self.metric_cb.current(len(METRICS) - 1)   # M19 varsayılan
        self.metric_cb.pack(fill="x", padx=14, pady=(0, 8))

        # Filtre modu
        sec4 = self._sec(p, "🔍  FİLTRE MODU")
        for val, txt in [
            ("max",   "Her element → MAX"),
            ("min",   "Her element → MIN"),
            ("above", "Eşik ÜSTÜ  >"),
            ("below", "Eşik ALTI  <"),
        ]:
            tk.Radiobutton(sec4, text=txt, variable=self.mode_var, value=val,
                bg=BG2, fg=MUTED, selectcolor=BG2, activebackground=BG2,
                font=FS, cursor="hand2",
                command=self._on_mode_change).pack(anchor="w", padx=16, pady=2)

        tf = tk.Frame(sec4, bg=BG2)
        tf.pack(fill="x", padx=14, pady=6)
        tk.Label(tf, text="Eşik değeri:", font=FS, fg=MUTED, bg=BG2).pack(anchor="w")
        self.thresh_entry = tk.Entry(tf, textvariable=self.thresh_var,
                                     **entry_cfg(), width=20)
        self.thresh_entry.pack(fill="x", pady=3, ipady=5)

        tk.Button(p, text="▶   FİLTRELE", command=self._apply_filter,
                  bg=ACCENT, fg="#0d1117", font=("Consolas", 11, "bold"),
                  relief="flat", cursor="hand2", pady=9,
                  activebackground="#79c0ff", activeforeground="#0d1117"
                  ).pack(fill="x", padx=14, pady=8)

        self.stat_lbl = tk.Label(p, text="", font=FS, fg=MUTED,
                                 bg=BG2, justify="left", wraplength=270)
        self.stat_lbl.pack(fill="x", padx=14, pady=2)

        tk.Button(p, text="⬇  CSV Olarak Kaydet", command=self._export_csv,
                  bg=BG3, fg=TEXT, font=FM, relief="flat",
                  cursor="hand2", pady=7, activebackground=BORDER
                  ).pack(fill="x", padx=14, pady=(4, 16))

    # ── SAĞ PANEL ─────────────────────────────────────────────────────────────
    def _build_right(self, p):
        top = tk.Frame(p, bg=BG2, pady=8)
        top.pack(fill="x")
        self.result_lbl = tk.Label(top,
            text="Sonuçlar  —  CSV yükleyip Filtrele'ye basın",
            font=FH, fg=MUTED, bg=BG2)
        self.result_lbl.pack(side="left", padx=20)
        self.row_count_lbl = tk.Label(top, text="", font=FS, fg=GREEN, bg=BG2)
        self.row_count_lbl.pack(side="left", padx=4)
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x")

        self.tree_frame = tk.Frame(p, bg=BG)
        self.tree_frame.pack(fill="both", expand=True)
        self._build_tree()

        self.status_bar = tk.Label(p, text="Hazır", font=FS, fg=MUTED,
                                   bg=BG3, anchor="w", padx=12, pady=4)
        self.status_bar.pack(fill="x", side="bottom")

    def _build_tree(self):
        for w in self.tree_frame.winfo_children():
            w.destroy()
        cols = ["Element ID", "Load Case ID", "FX", "FY", "FZ"] + [m["id"] for m in METRICS]
        self.tree = ttk.Treeview(self.tree_frame, columns=cols,
                                  show="headings", selectmode="extended")
        self.tree.heading("Element ID",   text="Element ID")
        self.tree.column("Element ID",    width=90, anchor="center", minwidth=70)
        self.tree.heading("Load Case ID", text="LC ID")
        self.tree.column("Load Case ID",  width=70, anchor="center", minwidth=60)
        for fc in ["FX", "FY", "FZ"]:
            self.tree.heading(fc, text=fc)
            self.tree.column(fc, width=90, anchor="center", minwidth=60)
        for m in METRICS:
            self.tree.heading(m["id"], text=m["id"])
            self.tree.column(m["id"],  width=80, anchor="center", minwidth=60)
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

    # ── EVENTS ────────────────────────────────────────────────────────────────
    def _on_mode_change(self):
        if hasattr(self, "thresh_entry"):
            state = "normal" if self.mode_var.get() in ("above", "below") else "disabled"
            self.thresh_entry.configure(state=state)

    def _on_eid_toggle(self):
        if hasattr(self, "eid_entry"):
            self.eid_entry.configure(
                state="disabled" if self.eid_all_var.get() else "normal")

    def _get_metric(self):
        val = self.metric_var.get().strip().split()[0]  # "M19  ..." → "M19"
        return next((m for m in METRICS if m["id"] == val), METRICS[-1])

    # ── CSV YÜKLE ─────────────────────────────────────────────────────────────
    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="CSV Dosyası Seç",
            filetypes=[("CSV", "*.csv"), ("Tüm Dosyalar", "*.*")])
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                messagebox.showerror("Hata", "CSV boş."); return

            col_map = {k.strip().lower(): k for k in rows[0].keys()}
            REQUIRED = {
                "element id":   "Element ID",
                "load case id": "Load Case ID",
                "fx": "FX", "fy": "FY", "fz": "FZ",
            }
            missing = [v for n, v in REQUIRED.items() if n not in col_map]
            if missing:
                messagebox.showerror("Hata",
                    f"Eksik sütunlar: {', '.join(missing)}\n"
                    f"Mevcut: {', '.join(rows[0].keys())}"); return

            self.raw_data = []
            for row in rows:
                nr = {std: row.get(col_map[norm], "") for norm, std in REQUIRED.items()}
                for k, v in row.items():
                    if k.strip().lower() not in REQUIRED:
                        nr[k] = v
                self.raw_data.append(nr)

            eids = len({r["Element ID"] for r in self.raw_data})
            self.file_lbl.configure(
                text=f"✓ {Path(path).name}\n{len(rows)} satır", fg=GREEN)
            self.stat_lbl.configure(
                text=f"Toplam: {len(rows)} satır  |  {eids} element", fg=MUTED)
            self.status_bar.configure(text=f"Yüklendi: {path}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # ── FİLTRELE ──────────────────────────────────────────────────────────────
    def _apply_filter(self):
        if not self.raw_data:
            messagebox.showwarning("Uyarı", "Önce CSV yükleyin."); return

        mode   = self.mode_var.get()
        metric = self._get_metric()
        mid    = metric["id"]

        if mode in ("above", "below"):
            try:    thresh = float(self.thresh_var.get())
            except: messagebox.showerror("Hata", "Geçerli eşik girin."); return
        else:
            thresh = None

        # Element ID filtresi
        if self.eid_all_var.get():
            eid_filter = None
        else:
            raw_eids = self.eid_entry.get().strip()
            if not raw_eids:
                messagebox.showerror("Hata",
                    "Element ID girin veya 'Tüm elementler' seçin."); return
            eid_filter = {e.strip() for e in raw_eids.split(",") if e.strip()}

        # Zenginleştir + (EID, LCID) bazında duplicate kaldır
        enriched = []
        seen_keys = set()
        for row in self.raw_data:
            eid = row.get("Element ID", "")
            if eid_filter is not None and eid not in eid_filter:
                continue
            key = (eid, row.get("Load Case ID", ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            try:
                fx = float(row["FX"]); fy = float(row["FY"]); fz = float(row["FZ"])
            except ValueError:
                fx = fy = fz = 0.0
            enriched.append({**row, "_vals": calc_all(fx, fy, fz),
                              "_fx": fx, "_fy": fy, "_fz": fz})

        # Element ID bazında grupla
        groups: dict = {}
        for row in enriched:
            groups.setdefault(row["Element ID"], []).append(row)

        result = []
        for rows in groups.values():
            valid = [r for r in rows if not math.isnan(r["_vals"][mid])]
            if not valid:
                continue
            if mode == "max":
                result.append(max(valid, key=lambda r: r["_vals"][mid]))
            elif mode == "min":
                result.append(min(valid, key=lambda r: r["_vals"][mid]))
            elif mode == "above":
                result.extend(r for r in valid if r["_vals"][mid] > thresh)
            elif mode == "below":
                result.extend(r for r in valid if r["_vals"][mid] < thresh)

        self.filtered = result
        self._fill_tree(result)

        fvals = [r["_vals"][mid] for r in result]
        if fvals:
            self.stat_lbl.configure(
                text=(f"Satır: {len(fvals)}   "
                      f"Min: {min(fvals):.3f}   "
                      f"Max: {max(fvals):.3f}   "
                      f"Ort: {sum(fvals)/len(fvals):.3f}"),
                fg=GREEN)
        else:
            self.stat_lbl.configure(text="Eşleşen satır yok", fg=RED_)

        self.result_lbl.configure(
            text=f"Filtre: {mid} [{mode.upper()}]  —  Tüm 19 metrik", fg=TEXT)
        self.row_count_lbl.configure(text=f"  {len(result)} satır")
        self.status_bar.configure(
            text=f"Tamamlandı: {len(result)} satır  |  Filtre metriği: {metric['label']}")

    def _fill_tree(self, data):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(data):
            self.tree.insert("", "end", tags=("even" if i % 2 == 0 else "odd",),
                values=(
                    row.get("Element ID", ""),
                    row.get("Load Case ID", ""),
                    f"{row['_fx']:.4f}",
                    f"{row['_fy']:.4f}",
                    f"{row['_fz']:.4f}",
                    *[f"{row['_vals'][m['id']]:.3f}" for m in METRICS]
                ))
        self.tree.tag_configure("even", background=BG)
        self.tree.tag_configure("odd",  background=BG2)

    # ── EXPORT ────────────────────────────────────────────────────────────────
    def _export_csv(self):
        if not self.filtered:
            messagebox.showwarning("Uyarı", "Önce filtreleme yapın."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="fastener_filtered.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Element ID", "Load Case ID", "FX", "FY", "FZ"]
                           + [m["label"] for m in METRICS])
                for row in self.filtered:
                    w.writerow([
                        row.get("Element ID", ""),
                        row.get("Load Case ID", ""),
                        f"{row['_fx']:.6f}",
                        f"{row['_fy']:.6f}",
                        f"{row['_fz']:.6f}",
                    ] + [f"{row['_vals'][m['id']]:.6f}" for m in METRICS])
            messagebox.showinfo("Başarılı", f"Kaydedildi:\n{path}")
            self.status_bar.configure(text=f"Kaydedildi: {path}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # ── YARDIMCI ──────────────────────────────────────────────────────────────
    def _sec(self, parent, title):
        frm = tk.Frame(parent, bg=BG2)
        frm.pack(fill="x", pady=(6, 0))
        tk.Label(frm, text=title, font=FT, fg=MUTED,
                 bg=BG2).pack(anchor="w", padx=14, pady=(8, 2))
        tk.Frame(frm, bg=BORDER, height=1).pack(fill="x", padx=14)
        return frm


if __name__ == "__main__":
    app = FastenerApp()
    app.mainloop()
