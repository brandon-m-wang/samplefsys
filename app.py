import tkinter as tk
from tkinter import filedialog, font
from tkinter import ttk
from tkmacosx import Button
import shutil
import json
import sys
from pathlib import Path

ROOT_DIR = Path("/Users/brandonwang/Music/Ableton/User Library/Samples/BRANDON STASH")
CONFIG_FILE = ROOT_DIR / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    config = {
        "types": [],
        "artists": {},
    }
    save_config(config)
    return config


def save_config(config):
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=4))


class SearchableDropdown:
    def __init__(self, parent, label_text, values, on_select):
        self.var = tk.StringVar()
        self.on_select = on_select
        self.all_values = sorted(values, key=str.lower)

        frame = tk.Frame(parent, bg="#0d1117")
        frame.pack(fill="x", pady=10, padx=20)

        tk.Label(
            frame,
            text=label_text,
            font=("Monaco", 14, "bold"),
            fg="#58a6ff",
            bg="#0d1117",
        ).pack(anchor="w", pady=(0, 6))

        input_row = tk.Frame(frame, bg="#0d1117")
        input_row.pack(fill="x")

        self.entry = tk.Entry(
            input_row,
            textvariable=self.var,
            font=("Monaco", 15),
            bg="#21262d",
            fg="#f0f6fc",
            insertbackground="#58a6ff",
            relief="flat",
            bd=8,
            highlightthickness=2,
            highlightcolor="#30363d",
        )
        self.entry.pack(side=tk.LEFT, fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self.on_keyrelease)
        self.entry.bind("<FocusIn>", lambda e: self.show_listbox())

        btn_frame = tk.Frame(input_row, bg="#0d1117")
        btn_frame.pack(side=tk.RIGHT, padx=(10, 0))

        self.add_btn = Button(
            btn_frame,
            text="+",
            font=("Monaco", 14, "bold"),
            width=30,
            height=30,
            bg="#238636",
            fg="#ffffff",
            relief="flat",
            bd=0,
            activebackground="#2ea043",
            activeforeground="#ffffff",
        )
        self.add_btn.pack(side=tk.LEFT, padx=3)
        self.add_btn.bind("<Enter>", lambda e: self.add_btn.config(bg="#2ea043"))
        self.add_btn.bind("<Leave>", lambda e: self.add_btn.config(bg="#238636"))

        self.del_btn = Button(
            btn_frame,
            text="−",
            font=("Monaco", 14, "bold"),
            width=30,
            height=30,
            bg="#da3633",
            fg="#ffffff",
            relief="flat",
            bd=0,
            activebackground="#f85149",
            activeforeground="#ffffff",
        )
        self.del_btn.pack(side=tk.LEFT)
        self.del_btn.bind("<Enter>", lambda e: self.del_btn.config(bg="#f85149"))
        self.del_btn.bind("<Leave>", lambda e: self.del_btn.config(bg="#da3633"))

        self.listbox = tk.Listbox(
            frame,
            font=("Monaco", 13),
            bg="#161b22",
            fg="#f0f6fc",
            selectbackground="#238636",
            height=10,
            relief="flat",
            highlightthickness=0,
        )
        self.listbox.pack(fill="x", pady=(6, 0))
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<FocusOut>", lambda e: self.hide_listbox())
        self.listbox.pack_forget()

        self.update_list(self.all_values)

        self.add_cmd = lambda: None
        self.delete_cmd = lambda: None
        self.add_btn.config(command=self.add_cmd)
        self.del_btn.config(command=self.delete_cmd)

    def update_list(self, values):
        self.listbox.delete(0, tk.END)
        for v in values:
            self.listbox.insert(tk.END, v)

    def show_listbox(self):
        if not self.listbox.winfo_ismapped():
            self.listbox.pack(fill="x", pady=(6, 0))

    def hide_listbox(self):
        self.listbox.pack_forget()

    def on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Tab"):
            return
        typed = self.var.get().lower()
        filtered = [v for v in self.all_values if typed in v.lower()]
        self.update_list(filtered)
        if filtered:
            self.show_listbox()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.see(0)

    def on_listbox_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            value = self.listbox.get(selection[0])
            self.var.set(value)
            self.hide_listbox()
            if self.on_select:
                self.on_select()

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def set_values(self, values):
        self.all_values = sorted(values, key=str.lower)
        self.update_list(self.all_values)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("sample fsys")
        self.geometry("1100x1010")
        self.configure(bg="#0d1117")

        # ttk style (for scrollbar)
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure(
            "Stash.Vertical.TScrollbar",
            background="#21262d",
            troughcolor="#0d1117",
            bordercolor="#0d1117",
            arrowcolor="#8b949e",
        )

        self.style.map(
            "Stash.Vertical.TScrollbar",
            background=[
                ("disabled", "#21262d"),
                ("pressed", "#21262d"),
                ("active", "#21262d"),
                ("!disabled", "#21262d"),
            ],
            arrowcolor=[
                ("disabled", "#8b949e"),
                ("pressed", "#8b949e"),
                ("active", "#8b949e"),
                ("!disabled", "#8b949e"),
            ],
            bordercolor=[
                ("disabled", "#0d1117"),
                ("pressed", "#0d1117"),
                ("active", "#0d1117"),
                ("!disabled", "#0d1117"),
            ],
        )

        self.config = load_config()
        self.files = []

        # sample name var created early so we can always read it
        self.name_var = tk.StringVar()

        # only support a single file even if multiple are passed on CLI
        if len(sys.argv) > 1:
            first = next((Path(p) for p in sys.argv[1:] if Path(p).exists()), None)
            if first is not None:
                self.files = [first]
                self.after(200, self.update_status)

        header = tk.Frame(self, bg="#0d1117")
        header.pack(pady=40)
        tk.Label(
            header,
            text="sample fsys",
            font=("Menlo", 48, "bold"),
            fg="#58a6ff",
            bg="#0d1117",
        ).pack()
        self.status = tk.Label(
            header,
            text="Ready",
            font=("Monaco", 14),
            fg="#8b949e",
            bg="#0d1117",
        )
        self.status.pack(pady=8)

        controls = tk.Frame(self, bg="#0d1117")
        controls.pack(pady=10)
        Button(
            controls,
            text="Browse File",
            command=self.browse,
            font=("Monaco", 13, "bold"),
            bg="#238636",
            fg="white",
            relief="flat",
            padx=20,
            pady=12,
            activebackground="#2ea043",
        ).pack(side=tk.LEFT, padx=15)
        Button(
            controls,
            text="Clear File",
            command=self.clear_files_only,
            font=("Monaco", 13, "bold"),
            bg="#6e7681",
            fg="white",
            relief="flat",
            padx=20,
            pady=12,
        ).pack(side=tk.LEFT, padx=15)
        Button(
            controls,
            text="Clear All",
            command=self.clear_all_fields,
            font=("Monaco", 13, "bold"),
            bg="#da3633",
            fg="white",
            relief="flat",
            padx=20,
            pady=12,
            activebackground="#f85149",
        ).pack(side=tk.LEFT, padx=15)

        self.file_label = tk.Label(
            self,
            text="No file selected",
            font=("Monaco", 16),
            fg="#8b949e",
            bg="#0d1117",
        )
        self.file_label.pack(pady=20)

        # ─────────────────────────────────────────
        # Scrollable middle form WITH BORDER
        # ─────────────────────────────────────────
        self.scroll_outer = tk.Frame(self, bg="#30363d")
        self.scroll_outer.pack(fill="both", expand=True, padx=100)

        self.scroll_container = tk.Frame(self.scroll_outer, bg="#0d1117")
        self.scroll_container.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas = tk.Canvas(
            self.scroll_container,
            bg="#0d1117",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.vscroll = ttk.Scrollbar(
            self.scroll_container,
            orient="vertical",
            command=self.canvas.yview,
            style="Stash.Vertical.TScrollbar",
        )
        self.vscroll.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.vscroll.set)

        self.form = tk.Frame(self.canvas, bg="#0d1117")
        self.form_window = self.canvas.create_window(
            (0, 0), window=self.form, anchor="nw"
        )

        self.form.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.form_window, width=e.width),
        )

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 1. Type
        self.type_dd = SearchableDropdown(
            self.form,
            "1. Type:",
            [t["name"] for t in self.config["types"]],
            self.on_type_selected,
        )
        self.type_dd.add_cmd = lambda: self.add_item("type")
        self.type_dd.delete_cmd = lambda: self.delete_item("type")
        self.type_dd.add_btn.config(command=self.type_dd.add_cmd)
        self.type_dd.del_btn.config(command=self.type_dd.delete_cmd)

        self.subtype_section = tk.Frame(self.form, bg="#0d1117")
        self.artist_section = tk.Frame(self.form, bg="#0d1117")
        self.song_section = tk.Frame(self.form, bg="#0d1117")

        # existing files section
        self.existing_files_section = tk.Frame(self.form, bg="#0d1117")
        self.existing_files_listbox = None

        self.sample_name_section = tk.Frame(self.form, bg="#0d1117")
        self.prefix_section = tk.Frame(self.form, bg="#0d1117")

        # filename preview label (below scroll area, above save button), hidden initially
        self.filename_preview_label = tk.Label(
            self,
            text="Filename preview:",
            font=("Monaco", 13),
            fg="#58a6ff",
            bg="#0d1117",
        )
        # not packed yet — only when constraints are met

        # SAVE button starts grey/disabled, turns green when ready
        self.save_btn = Button(
            self,
            text="save to fsys",
            font=("Menlo", 32, "bold"),
            bg="#30363d",
            fg="#8b949e",
            relief="flat",
            state="disabled",
            command=self.save,
            height=60,
            width=400,
            activebackground="#30363d",
        )
        self.save_btn.pack(pady=60)

        self.update_status()
        self.refresh_from_config()
        self.update_save_state()

    def _on_mousewheel(self, event):
        # Only scroll if content taller than viewport
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        content_h = bbox[3] - bbox[1]
        view_h = self.canvas.winfo_height()
        if content_h <= view_h:
            return
        if event.delta:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def log(self, text, color="#58a6ff"):
        self.status.config(text=text, fg=color)
        self.update_idletasks()

    def get_current_target_dir(self):
        """Return the folder for the current type/subtype/artist/song selection."""
        tname = self.type_dd.get()
        subtype = (
            getattr(self, "subtype_dd", None).get()
            if hasattr(self, "subtype_dd")
            else ""
        )
        artist = (
            getattr(self, "artist_dd", None).get() if hasattr(self, "artist_dd") else ""
        )
        song = getattr(self, "song_dd", None).get() if hasattr(self, "song_dd") else ""
        parts = [p for p in [tname, subtype, artist, song] if p]
        if not parts:
            return None
        return ROOT_DIR.joinpath(*parts)

    def show_existing_files(self):
        """Ensure the 'existing files' section is visible and populated."""
        if self.existing_files_listbox is None:
            tk.Label(
                self.existing_files_section,
                text="Existing samples in this folder:",
                font=("Monaco", 13, "bold"),
                fg="#8b949e",
                bg="#0d1117",
            ).pack(anchor="w", padx=20, pady=(10, 6))

            self.existing_files_listbox = tk.Listbox(
                self.existing_files_section,
                font=("Monaco", 12),
                bg="#161b22",
                fg="#f0f6fc",
                selectbackground="#238636",
                height=6,
                relief="flat",
                highlightthickness=0,
            )
            self.existing_files_listbox.pack(fill="x", padx=20, pady=(0, 10))

        self.update_existing_files()
        self.existing_files_section.pack(fill="x")

    def update_existing_files(self):
        """Refresh the contents of the existing files listbox."""
        if not self.existing_files_listbox:
            return
        self.existing_files_listbox.delete(0, tk.END)
        folder = self.get_current_target_dir()
        if folder and folder.exists():
            files = sorted(
                [
                    p
                    for p in folder.iterdir()
                    if p.is_file() and not p.name.startswith(".")
                ],
                key=lambda p: p.name.lower(),
            )
            if files:
                for p in files:
                    self.existing_files_listbox.insert(tk.END, p.name)
            else:
                self.existing_files_listbox.insert(tk.END, "(no files yet)")
        else:
            self.existing_files_listbox.insert(tk.END, "(folder does not exist yet)")

    def hide_existing_files(self):
        self.existing_files_section.pack_forget()
        if self.existing_files_listbox:
            self.existing_files_listbox.delete(0, tk.END)

    def refresh_from_config(self):
        """Keep all dropdowns in sync with self.config + current selections."""
        # Types
        self.type_dd.set_values([t["name"] for t in self.config["types"]])

        # Subtypes (depend on selected type)
        if hasattr(self, "subtype_dd"):
            tname = self.type_dd.get()
            if tname:
                subs = next(
                    (x["subtypes"] for x in self.config["types"] if x["name"] == tname),
                    [],
                )
            else:
                subs = []
            self.subtype_dd.set_values(subs)

        # Artists
        if hasattr(self, "artist_dd"):
            self.artist_dd.set_values(list(self.config["artists"].keys()))

        # Songs (depend on selected artist)
        if hasattr(self, "song_dd"):
            aname = self.artist_dd.get() if hasattr(self, "artist_dd") else ""
            if aname and aname in self.config["artists"]:
                songs = [s["name"] for s in self.config["artists"][aname]["songs"]]
            else:
                songs = []
            self.song_dd.set_values(songs)

        # Existing files, if the section is visible and we have a song
        if (
            self.song_section.winfo_ismapped()
            and hasattr(self, "song_dd")
            and self.song_dd.get()
        ):
            self.update_existing_files()

    # central logic: decide if SAVE should be enabled + green
    def update_save_state(self):
        type_ok = bool(self.type_dd.get())
        subtype_ok = (
            bool(getattr(self, "subtype_dd", None).get())
            if hasattr(self, "subtype_dd")
            else False
        )
        artist_ok = (
            bool(getattr(self, "artist_dd", None).get())
            if hasattr(self, "artist_dd")
            else False
        )
        song_ok = (
            bool(getattr(self, "song_dd", None).get())
            if hasattr(self, "song_dd")
            else False
        )
        name_ok = bool(self.name_var.get().strip())
        files_ok = bool(self.files)  # only ever 0 or 1

        ready = all([type_ok, subtype_ok, artist_ok, song_ok, name_ok, files_ok])

        if ready:
            self.save_btn.config(
                state="normal",
                bg="#238636",
                fg="white",
                activebackground="#2ea043",
            )
        else:
            self.save_btn.config(
                state="disabled",
                bg="#30363d",
                fg="#8b949e",
                activebackground="#30363d",
            )

        # handle filename preview visibility + content
        if ready:
            if not self.filename_preview_label.winfo_ismapped():
                # ensure it sits above the save button
                self.filename_preview_label.pack(pady=(45, 0), before=self.save_btn)
            self.update_filename_preview()
        else:
            if self.filename_preview_label.winfo_ismapped():
                self.filename_preview_label.pack_forget()

    def update_status(self):
        if self.files:
            self.file_label.config(text="1 file ready", fg="#58a6ff")
        else:
            self.file_label.config(text="No file selected", fg="#8b949e")

    def browse(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.wav *.aiff *.mp3 *.flac *.ogg")]
        )
        if file_path:
            self.files = [Path(file_path)]
            self.log("Loaded 1 file", "#58a6ff")
            self.update_status()
            self.update_save_state()

    def clear_files_only(self):
        self.files = []
        self.update_status()
        self.log("File cleared — selections kept", "#8b949e")
        self.update_save_state()

    def clear_all_fields(self):
        self.files = []
        self.type_dd.set("")
        for sec in [
            self.subtype_section,
            self.artist_section,
            self.song_section,
            self.existing_files_section,
            self.sample_name_section,
            self.prefix_section,
        ]:
            sec.pack_forget()
        if hasattr(self, "subtype_dd"):
            self.subtype_dd.set("")
        if hasattr(self, "artist_dd"):
            self.artist_dd.set("")
        if hasattr(self, "song_dd"):
            self.song_dd.set("")
        self.name_var.set("")
        self.hide_existing_files()
        self.log("All cleared", "#8b949e")
        self.update_status()
        self.update_save_state()

    def on_type_selected(self):
        # clear downstream UI
        for sec in [
            self.subtype_section,
            self.artist_section,
            self.song_section,
            self.existing_files_section,
            self.sample_name_section,
            self.prefix_section,
        ]:
            sec.pack_forget()
        self.hide_existing_files()
        # clear dependent dropdown values
        if hasattr(self, "subtype_dd"):
            self.subtype_dd.set("")
        if hasattr(self, "artist_dd"):
            self.artist_dd.set("")
        if hasattr(self, "song_dd"):
            self.song_dd.set("")
        self.name_var.set("")
        if self.type_dd.get():
            self.show_subtype()
        self.refresh_from_config()
        self.update_save_state()

    def show_subtype(self):
        if not self.subtype_section.winfo_children():
            self.subtype_dd = SearchableDropdown(
                self.subtype_section, "2. Subtype:", [], self.on_subtype_selected
            )
            self.subtype_dd.add_cmd = lambda: self.add_item("subtype")
            self.subtype_dd.delete_cmd = lambda: self.delete_item("subtype")
            self.subtype_dd.add_btn.config(command=self.subtype_dd.add_cmd)
            self.subtype_dd.del_btn.config(command=self.subtype_dd.delete_cmd)
        t = self.type_dd.get()
        subs = next((x["subtypes"] for x in self.config["types"] if x["name"] == t), [])
        self.subtype_dd.set_values(subs)
        self.subtype_section.pack(fill="x")
        self.update_save_state()

    def on_subtype_selected(self):
        for sec in [
            self.artist_section,
            self.song_section,
            self.existing_files_section,
            self.sample_name_section,
            self.prefix_section,
        ]:
            sec.pack_forget()
        self.hide_existing_files()
        if hasattr(self, "artist_dd"):
            self.artist_dd.set("")
        if hasattr(self, "song_dd"):
            self.song_dd.set("")
        self.name_var.set("")
        self.show_artist()
        self.refresh_from_config()
        self.update_save_state()

    def show_artist(self):
        if not self.artist_section.winfo_children():
            self.artist_dd = SearchableDropdown(
                self.artist_section,
                "3. Artist:",
                list(self.config["artists"].keys()),
                self.on_artist_selected,
            )
            self.artist_dd.add_cmd = lambda: self.add_item("artist")
            self.artist_dd.delete_cmd = lambda: self.delete_item("artist")
            self.artist_dd.add_btn.config(command=self.artist_dd.add_cmd)
            self.artist_dd.del_btn.config(command=self.artist_dd.delete_cmd)
        self.artist_section.pack(fill="x")
        self.update_save_state()

    def on_artist_selected(self):
        for sec in [
            self.song_section,
            self.existing_files_section,
            self.sample_name_section,
            self.prefix_section,
        ]:
            sec.pack_forget()
        self.hide_existing_files()
        # clear song selection when artist changes
        if hasattr(self, "song_dd"):
            self.song_dd.set("")
        self.name_var.set("")
        if self.artist_dd.get():
            self.show_song()
        self.refresh_from_config()
        self.update_save_state()

    def show_song(self):
        if not self.song_section.winfo_children():
            self.song_dd = SearchableDropdown(
                self.song_section, "4. Song:", [], self.on_song_selected
            )
            self.song_dd.add_cmd = lambda: self.add_item("song")
            self.song_dd.delete_cmd = lambda: self.delete_item("song")
            self.song_dd.add_btn.config(command=self.song_dd.add_cmd)
            self.song_dd.del_btn.config(command=self.song_dd.delete_cmd)
        a = self.artist_dd.get()
        songs = [s["name"] for s in self.config["artists"].get(a, {}).get("songs", [])]
        self.song_dd.set_values(songs)
        self.song_section.pack(fill="x")
        self.update_save_state()

    def on_song_selected(self):
        for sec in [
            self.existing_files_section,
            self.sample_name_section,
            self.prefix_section,
        ]:
            sec.pack_forget()
        self.hide_existing_files()
        if self.song_dd.get():
            self.show_existing_files()
            self.show_sample_name()
        self.refresh_from_config()
        self.update_save_state()

    def show_sample_name(self):
        if not self.sample_name_section.winfo_children():
            tk.Label(
                self.sample_name_section,
                text="Sample Name:",
                font=("Monaco", 15, "bold"),
                fg="#58a6ff",
                bg="#0d1117",
            ).pack(fill="x", pady=(0, 20))

            name_entry = tk.Entry(
                self.sample_name_section,
                textvariable=self.name_var,
                font=("Monaco", 15),
                bg="#21262d",
                fg="#f0f6fc",
                insertbackground="#58a6ff",
                relief="flat",
                bd=8,
                width=60,
            )
            name_entry.pack()

            self.name_var.trace_add("write", lambda *args: self.update_save_state())

        self.sample_name_section.pack(fill="x", pady=25)

        if not self.prefix_section.winfo_children():
            # defaults
            self.prefix_song = tk.BooleanVar(value=True)
            self.prefix_bpm = tk.BooleanVar(value=False)
            self.prefix_artist = tk.BooleanVar(value=True)
            self.prefix_key = tk.BooleanVar(value=False)
            self.suffix_og = tk.BooleanVar(value=True)

            # row 1: up to 3 checkboxes
            row1 = tk.Frame(self.prefix_section, bg="#0d1117")
            row1.pack(pady=(10, 5))
            # row 2: remaining
            row2 = tk.Frame(self.prefix_section, bg="#0d1117")
            row2.pack(pady=(0, 10))

            tk.Checkbutton(
                row1,
                text="Prefix: Artist Name",
                variable=self.prefix_artist,
                command=self.update_filename_preview,
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#0d1117",
                selectcolor="#21262d",
            ).pack(side=tk.LEFT, padx=15)

            tk.Checkbutton(
                row1,
                text="Prefix: Song Name",
                variable=self.prefix_song,
                command=self.update_filename_preview,
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#0d1117",
                selectcolor="#21262d",
            ).pack(side=tk.LEFT, padx=15)

            tk.Checkbutton(
                row1,
                text="Prefix: BPM",
                variable=self.prefix_bpm,
                command=self.update_filename_preview,
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#0d1117",
                selectcolor="#21262d",
            ).pack(side=tk.LEFT, padx=15)

            tk.Checkbutton(
                row2,
                text="Prefix: Key",
                variable=self.prefix_key,
                command=self.update_filename_preview,
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#0d1117",
                selectcolor="#21262d",
            ).pack(side=tk.LEFT, padx=15)

            tk.Checkbutton(
                row2,
                text="Suffix: og",
                variable=self.suffix_og,
                command=self.update_filename_preview,
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#0d1117",
                selectcolor="#21262d",
            ).pack(side=tk.LEFT, padx=15)

        self.prefix_section.pack(pady=(0, 25))
        self.update_save_state()

    def add_item(self, kind):
        win = tk.Toplevel(self)
        win.title(f"Add {kind.capitalize()}")
        win.geometry("500x400" if kind != "song" else "500x540")
        win.configure(bg="#161b22")
        win.transient(self)
        win.grab_set()

        if kind == "song":
            if not getattr(self, "artist_dd", None) or not self.artist_dd.get():
                self.log("Select artist first!", "#f85149")
                win.destroy()
                return
            tk.Label(
                win,
                text="New Song + BPM + Key",
                font=("Monaco", 20, "bold"),
                fg="#58a6ff",
                bg="#161b22",
            ).pack(pady=30)
            tk.Label(
                win,
                text="Song name:",
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#161b22",
            ).pack()
            song_e = tk.Entry(
                win,
                width=50,
                font=("Monaco", 14),
                bg="#21262d",
                fg="#f0f6fc",
                insertbackground="#58a6ff",
            )
            song_e.pack(pady=8, padx=80)
            song_e.focus()

            tk.Label(
                win,
                text="BPM:",
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#161b22",
            ).pack()
            bpm_e = tk.Entry(
                win,
                width=20,
                font=("Monaco", 14),
                bg="#21262d",
                fg="#f0f6fc",
                insertbackground="#58a6ff",
            )
            bpm_e.pack(pady=8)

            tk.Label(
                win,
                text="Key (e.g. C# Minor):",
                font=("Monaco", 13),
                fg="#f0f6fc",
                bg="#161b22",
            ).pack()
            key_e = tk.Entry(
                win,
                width=30,
                font=("Monaco", 14),
                bg="#21262d",
                fg="#f0f6fc",
                insertbackground="#58a6ff",
            )
            key_e.pack(pady=8)

            def save_song():
                song = song_e.get().strip()
                bpm_text = bpm_e.get().strip()
                key = key_e.get().strip()

                if not song:
                    self.log("Song name required", "#f85149")
                    return

                try:
                    bpm = int(bpm_text)
                    if bpm <= 0 or bpm > 400:
                        raise ValueError
                except Exception:
                    self.log("Invalid BPM (1–400)", "#f85149")
                    return

                if not key:
                    self.log("Key required", "#f85149")
                    return

                artist = self.artist_dd.get()
                if any(
                    s["name"] == song for s in self.config["artists"][artist]["songs"]
                ):
                    self.log("Song exists", "#ffa657")
                    return

                self.config["artists"][artist]["songs"].append(
                    {"name": song, "bpm": bpm, "key": key}
                )
                save_config(self.config)
                self.refresh_from_config()
                self.show_song()
                self.song_dd.set(song)
                self.log(f"Added: {song} ({bpm} BPM, {key})", "#58a6ff")
                win.destroy()
                self.on_song_selected()

            Button(
                win,
                text="Add Song",
                bg="#238636",
                fg="white",
                font=("Monaco", 16, "bold"),
                command=save_song,
                relief="flat",
                padx=30,
                pady=12,
            ).pack(pady=30)
        else:
            tk.Label(
                win,
                text=f"New {kind.capitalize()}:",
                font=("Monaco", 20, "bold"),
                fg="#58a6ff",
                bg="#161b22",
            ).pack(pady=50)
            e = tk.Entry(
                win,
                width=50,
                font=("Monaco", 14),
                bg="#21262d",
                fg="#f0f6fc",
                insertbackground="#58a6ff",
            )
            e.pack(pady=15, padx=80)
            e.focus()

            def ok():
                v = e.get().strip()
                if not v:
                    return
                if kind == "type" and v not in [
                    t["name"] for t in self.config["types"]
                ]:
                    self.config["types"].append({"name": v, "subtypes": []})
                    save_config(self.config)
                    self.refresh_from_config()
                    self.type_dd.set(v)
                    self.on_type_selected()
                elif kind == "subtype" and self.type_dd.get():
                    t = next(
                        x
                        for x in self.config["types"]
                        if x["name"] == self.type_dd.get()
                    )
                    if v not in t["subtypes"]:
                        t["subtypes"].append(v)
                        save_config(self.config)
                        self.refresh_from_config()
                        self.show_subtype()
                        self.subtype_dd.set(v)
                        self.on_subtype_selected()
                elif kind == "artist" and v not in self.config["artists"]:
                    self.config["artists"][v] = {"songs": []}
                    save_config(self.config)
                    self.refresh_from_config()
                    self.show_artist()
                    self.artist_dd.set(v)
                    self.on_artist_selected()
                else:
                    save_config(self.config)
                    self.refresh_from_config()
                self.log(f"Added {kind}: {v}", "#58a6ff")
                win.destroy()
                self.update_save_state()

            Button(
                win,
                text="Add",
                bg="#238636",
                fg="white",
                font=("Monaco", 16),
                command=ok,
                relief="flat",
                padx=30,
                pady=12,
            ).pack(pady=30)

    def delete_item(self, kind):
        dd = getattr(self, f"{kind}_dd", None)
        if not dd or not dd.get():
            return
        value = dd.get()

        if kind == "artist":
            win = tk.Toplevel(self)
            win.title("Delete Artist")
            win.geometry("480x200")
            win.configure(bg="#161b22")
            win.transient(self)
            win.grab_set()
            tk.Label(
                win,
                text=f"Delete artist '{value}'?\nAll songs will be removed.",
                font=("Monaco", 14),
                fg="#f0f6fc",
                bg="#161b22",
            ).pack(pady=40)

            def yes_artist():
                self.config["artists"].pop(value, None)
                save_config(self.config)
                self.refresh_from_config()
                if hasattr(self, "artist_dd"):
                    self.artist_dd.set("")
                if hasattr(self, "song_dd"):
                    self.song_dd.set("")
                self.name_var.set("")
                for sec in [
                    self.song_section,
                    self.existing_files_section,
                    self.sample_name_section,
                    self.prefix_section,
                ]:
                    sec.pack_forget()
                self.hide_existing_files()
                self.log(f"Deleted artist: {value}", "#ffa657")
                win.destroy()
                self.update_save_state()

            Button(
                win,
                text="Delete",
                bg="#da3633",
                fg="white",
                font=("Monaco", 14),
                command=yes_artist,
                relief="flat",
                width=150,
                height=40,
            ).pack(side=tk.LEFT, padx=(60, 0), pady=20)
            Button(
                win,
                text="Cancel",
                command=win.destroy,
                font=("Monaco", 14),
                width=150,
                height=40,
            ).pack(side=tk.RIGHT, padx=(0, 60), pady=20)
            return

        delete_files = tk.BooleanVar()
        win = tk.Toplevel(self)
        win.title(f"Delete {kind.capitalize()}")
        win.geometry("520x260")
        win.configure(bg="#161b22")
        win.transient(self)
        win.grab_set()
        tk.Label(
            win,
            text=f"Delete '{value}'?",
            font=("Monaco", 16),
            fg="#f0f6fc",
            bg="#161b22",
        ).pack(pady=40)
        tk.Checkbutton(
            win,
            text="Also delete all files/folders on disk",
            variable=delete_files,
            font=("Monaco", 13),
            fg="#f0f6fc",
            bg="#161b22",
            selectcolor="#21262d",
        ).pack(pady=15)

        def yes_other():
            path = None
            if kind == "type":
                path = ROOT_DIR / value
                self.config["types"] = [
                    t for t in self.config["types"] if t["name"] != value
                ]
                self.type_dd.set("")
                if hasattr(self, "subtype_dd"):
                    self.subtype_dd.set("")
                if hasattr(self, "artist_dd"):
                    self.artist_dd.set("")
                if hasattr(self, "song_dd"):
                    self.song_dd.set("")
                for sec in [
                    self.subtype_section,
                    self.artist_section,
                    self.song_section,
                    self.existing_files_section,
                    self.sample_name_section,
                    self.prefix_section,
                ]:
                    sec.pack_forget()
                self.hide_existing_files()
            elif kind == "subtype":
                t = next(
                    x for x in self.config["types"] if x["name"] == self.type_dd.get()
                )
                t["subtypes"] = [s for s in t["subtypes"] if s != value]
                path = ROOT_DIR / self.type_dd.get() / value
                if hasattr(self, "subtype_dd"):
                    self.subtype_dd.set("")
                if hasattr(self, "artist_dd"):
                    self.artist_dd.set("")
                if hasattr(self, "song_dd"):
                    self.song_dd.set("")
                for sec in [
                    self.artist_section,
                    self.song_section,
                    self.existing_files_section,
                    self.sample_name_section,
                    self.prefix_section,
                ]:
                    sec.pack_forget()
                self.hide_existing_files()
            elif kind == "song":
                songs = self.config["artists"][self.artist_dd.get()]["songs"]
                self.config["artists"][self.artist_dd.get()]["songs"] = [
                    s for s in songs if s["name"] != value
                ]
                path = ROOT_DIR / self.artist_dd.get() / value
                if hasattr(self, "song_dd"):
                    self.song_dd.set("")
                self.name_var.set("")
                for sec in [
                    self.existing_files_section,
                    self.sample_name_section,
                    self.prefix_section,
                ]:
                    sec.pack_forget()
                self.hide_existing_files()

            if delete_files.get() and path and path.exists():
                shutil.rmtree(path)
            save_config(self.config)
            self.refresh_from_config()
            self.log(f"Deleted {kind}: {value}", "#ffa657")
            win.destroy()
            self.update_save_state()

        Button(
            win,
            text="Delete",
            bg="#da3633",
            fg="white",
            font=("Monaco", 14),
            command=yes_other,
            relief="flat",
            width=150,
            height=40,
        ).pack(side=tk.LEFT, padx=(60, 0), pady=20)
        Button(
            win,
            text="Cancel",
            command=win.destroy,
            font=("Monaco", 14),
            width=150,
            height=40,
        ).pack(side=tk.RIGHT, padx=(0, 60), pady=20)

    # ------- filename building & preview -------

    def build_filename(self, include_extension=True):
        base = self.name_var.get().strip()
        if not base:
            return ""

        prefix_parts = []

        # always include subtype if present (with your intentional [:-1])
        subtype = (
            self.subtype_dd.get()
            if hasattr(self, "subtype_dd") and self.subtype_dd.get()
            else ""
        )
        if subtype:
            prefix_parts.append(subtype.replace(" ", "_")[:-1])

        artist = (
            self.artist_dd.get()
            if hasattr(self, "artist_dd") and self.artist_dd.get()
            else ""
        )
        song_name = (
            self.song_dd.get()
            if hasattr(self, "song_dd") and self.song_dd.get()
            else ""
        )

        bpm = None
        key = None
        if (
            artist
            and song_name
            and artist in self.config["artists"]
            and self.config["artists"][artist]["songs"]
        ):
            for s in self.config["artists"][artist]["songs"]:
                if s["name"] == song_name:
                    bpm = s.get("bpm", None)
                    key = s.get("key", "")
                    break

        # optional prefixes (BPM / artist / song / key)
        if hasattr(self, "prefix_bpm") and self.prefix_bpm.get() and bpm is not None:
            prefix_parts.append(str(bpm))
        if hasattr(self, "prefix_artist") and self.prefix_artist.get() and artist:
            prefix_parts.append(artist.replace(" ", "_"))
        if hasattr(self, "prefix_song") and self.prefix_song.get() and song_name:
            prefix_parts.append(song_name.replace(" ", "_"))
        if hasattr(self, "prefix_key") and self.prefix_key.get() and key:
            prefix_parts.append(key.replace(" ", "_"))

        name = base
        if prefix_parts:
            name = "_".join(prefix_parts) + "_" + name

        # optional suffix
        if hasattr(self, "suffix_og") and self.suffix_og.get():
            name = name + "_og"

        if include_extension:
            if self.files:
                ext = self.files[0].suffix
            else:
                ext = ""
            name = name + ext

        return name

    def update_filename_preview(self):
        filename = self.build_filename(include_extension=True)
        if filename:
            self.filename_preview_label.config(
                text=f"Filename preview: {filename}", fg="#58a6ff"
            )
        else:
            self.filename_preview_label.config(text="Filename preview:", fg="#8b949e")

    # -------------- save --------------

    def save(self):
        if not self.files:
            self.log("No file selected!", "#f85149")
            self.update_save_state()
            return
        if not all(
            [
                self.type_dd.get(),
                (
                    getattr(self, "subtype_dd", None).get()
                    if hasattr(self, "subtype_dd")
                    else ""
                ),
                (
                    getattr(self, "artist_dd", None).get()
                    if hasattr(self, "artist_dd")
                    else ""
                ),
                (
                    getattr(self, "song_dd", None).get()
                    if hasattr(self, "song_dd")
                    else ""
                ),
                self.name_var.get().strip(),
            ]
        ):
            self.log("Fill all fields!", "#f85149")
            self.update_save_state()
            return

        song_name = self.song_dd.get()
        artist = self.artist_dd.get()
        _song_info = next(
            s for s in self.config["artists"][artist]["songs"] if s["name"] == song_name
        )

        parts = [
            p
            for p in [self.type_dd.get(), self.subtype_dd.get(), artist, song_name]
            if p
        ]
        target = ROOT_DIR.joinpath(*parts)
        target.mkdir(parents=True, exist_ok=True)

        src = self.files[0]

        # build filename WITHOUT extension, then add src.suffix
        name_no_ext = self.build_filename(include_extension=False)
        if not name_no_ext:
            self.log("Invalid name", "#f85149")
            return

        dest = target / (name_no_ext + src.suffix)
        if dest.exists():
            self.log("File not saved — target filename already exists", "#ffa657")
            return

        shutil.copy2(src, dest)
        self.log(f"SAVED 1 file → {target.name}", "#58a6ff")

        self.clear_files_only()
        self.update_existing_files()
        self.update_save_state()


if __name__ == "__main__":
    App().mainloop()
