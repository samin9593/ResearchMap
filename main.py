"""ResearchMap's CustomTkinter desktop application."""

from pathlib import Path
from tkinter import Canvas, StringVar, filedialog, messagebox

import customtkinter as ctk

from analyzer import analyze_papers, load_papers
from ui_components import (
    ACCENT, ACTIVE, BACKGROUND, BLUE, BORDER, FONT, INK, MUTED, PAPER, SAGE, SIDEBAR,
    TERRACOTTA, button, card, configure_tables, embed_figure, fill_table, keyword_figure,
    label, similarity_figure, table,
)


import sys

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
SAMPLE_PATH = BASE_DIR / "data" / "sample_papers.csv"
PAGES = ("Dashboard", "Import Papers", "Keyword Analysis", "Paper Similarity")


def shorten(text, limit):
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


class ResearchMap(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=BACKGROUND)
        self.title("ResearchMap")
        width = min(1240, self.winfo_screenwidth() - 48)
        height = min(795, self.winfo_screenheight() - 100)
        self.geometry(f"{width}x{height}")
        self.minsize(940, 650)
        configure_tables(self)

        self.papers = None
        self.analysis = None
        self.source = "No dataset loaded"
        self.is_sample = False
        self.query = StringVar()
        self.query.trace_add("write", self.refresh_library)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_sidebar()
        self.main = ctk.CTkFrame(self, fg_color=BACKGROUND, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.load_dataset(SAMPLE_PATH, sample=True)

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=218, fg_color=SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.pack_propagate(False)
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(29, 28))
        mark = Canvas(brand, width=28, height=28, bg=SIDEBAR, highlightthickness=0)
        mark.pack(side="left", padx=(0, 8))
        mark.create_line(5, 19, 13, 7, 23, 16, 5, 19, fill=BLUE, width=1)
        for x, y, color in ((5, 19, ACCENT), (13, 7, TERRACOTTA), (23, 16, ACCENT)):
            mark.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")
        label(brand, "ResearchMap", 20, serif=True).pack(side="left")

        label(sidebar, "WORKSPACE", 10, MUTED, bold=True).pack(anchor="w", padx=25, pady=(0, 7))
        self.nav_buttons = {}
        for number, page in enumerate(PAGES, 1):
            nav = ctk.CTkButton(
                sidebar, text=f"{number:02d}    {page}", anchor="w", height=41,
                corner_radius=8, fg_color=SIDEBAR, hover_color=ACTIVE, text_color=INK,
                font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
                command=lambda name=page: self.show_page(name),
            )
            nav.pack(fill="x", padx=16, pady=3)
            self.nav_buttons[page] = nav

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=23, pady=24)
        ctk.CTkFrame(footer, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 12))
        label(footer, "CORPUS", 10, MUTED, bold=True).pack(anchor="w")
        self.source_label = label(footer, self.source, 12, wraplength=166, justify="left")
        self.source_label.pack(anchor="w")

    def load_dataset(self, path, sample=False):
        try:
            papers = load_papers(path)
            analysis = analyze_papers(papers)
        except ValueError as error:
            messagebox.showerror("Could not load papers", str(error), parent=self)
            if self.papers is None:
                self.show_page("Import Papers")
            return
        self.papers = papers
        self.analysis = analysis
        self.source = "Fictional sample dataset" if sample else Path(path).name
        self.is_sample = sample
        self.source_label.configure(text=shorten(self.source, 44))
        self.query.set("")
        self.show_page("Dashboard" if sample else "Import Papers")

    def show_page(self, page):
        for widget in self.main.winfo_children():
            widget.destroy()
        self.library_table = None
        for name, nav in self.nav_buttons.items():
            nav.configure(fg_color=ACTIVE if name == page else SIDEBAR, text_color=ACCENT if name == page else INK)
        self.body = ctk.CTkScrollableFrame(
            self.main, fg_color=BACKGROUND, corner_radius=0, scrollbar_button_color=BORDER,
        )
        self.body.pack(fill="both", expand=True, padx=(25, 13), pady=(12, 11))
        views = {
            "Dashboard": self.dashboard, "Import Papers": self.library,
            "Keyword Analysis": self.keywords, "Paper Similarity": self.similarity,
        }
        views[page]()

    def heading(self, eyebrow, title, description):
        label(self.body, eyebrow, 10, ACCENT, bold=True).pack(anchor="w", pady=(10, 1))
        label(self.body, title, 37, serif=True).pack(anchor="w", pady=(0, 1))
        label(self.body, description, 14, MUTED, wraplength=630, justify="left").pack(anchor="w", pady=(0, 19))

    def section(self, parent, title, description):
        label(parent, title, 21, serif=True).pack(anchor="w", padx=18, pady=(13, 0))
        label(parent, description, 12, MUTED, wraplength=310, justify="left").pack(anchor="w", padx=18, pady=(0, 5))

    def empty_message(self, parent, text):
        label(parent, text, 14, MUTED, wraplength=310, justify="left").pack(anchor="w", padx=18, pady=(12, 26))

    def dashboard(self):
        self.heading("01 / OVERVIEW", "Research overview", "A reading map of the terms and textual relationships in your corpus.")
        if self.papers is None:
            self.empty_message(self.body, "Import a CSV to begin exploring your papers.")
            button(self.body, "Import papers", lambda: self.show_page("Import Papers")).pack(anchor="w")
            return

        keywords = self.analysis.keywords
        average = self.analysis.average_similarity
        cards = [
            ("TOTAL PAPERS", str(len(self.papers)), "Records in this corpus", BLUE),
            ("UNIQUE KEYWORDS", str(len(keywords)), "Terms in the vocabulary", SAGE),
            ("TOP KEYWORD", shorten(keywords.iloc[0]["keyword"], 19) if len(keywords) else "—", "Highest mean TF-IDF", TERRACOTTA),
            ("AVG. SIMILARITY", f"{average:.1%}" if average is not None else "—", "Across distinct paper pairs", BLUE),
        ]
        metrics = ctk.CTkFrame(self.body, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 16))
        for index, (caption, value, detail, color) in enumerate(cards):
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
            item = card(metrics)
            item.grid(row=0, column=index, sticky="nsew", padx=(0, 10 if index < 3 else 0))
            ctk.CTkFrame(item, width=23, height=3, corner_radius=1, fg_color=color).pack(anchor="w", padx=13, pady=(13, 2))
            label(item, caption, 9, MUTED, bold=True).pack(anchor="w", padx=13)
            label(item, value, 27 if len(value) <= 9 else 17, serif=True).pack(anchor="w", padx=13)
            label(item, detail, 10, MUTED).pack(anchor="w", padx=13, pady=(0, 10))

        panels = ctk.CTkFrame(self.body, fg_color="transparent")
        panels.pack(fill="x")
        panels.grid_columnconfigure((0, 1), weight=1, uniform="panel")
        chart = card(panels)
        chart.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.section(chart, "Leading terms", "Top 8 terms by mean TF-IDF")
        self.draw_keywords(chart, 8, 2.25)
        preview = card(panels)
        preview.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.section(preview, "Paper library", f"First {min(len(self.papers), 6)} records in import order")
        frame, tree = table(preview, [("Title", 205, True), ("Year", 51, False)], min(len(self.papers), 6))
        frame.pack(fill="x", padx=16, pady=(5, 7))
        fill_table(tree, ((index, (shorten(paper.title, 31), paper.year or "—")) for index, paper in self.papers.head(6).iterrows()))
        button(preview, "Open library", lambda: self.show_page("Import Papers"), primary=False).pack(anchor="w", padx=16, pady=(0, 13))
        label(self.body, "Fictional demonstration data" if self.is_sample else shorten(self.source, 65), 11, MUTED).pack(anchor="w", pady=(8, 0))

    def library(self):
        self.heading("02 / CORPUS", "Paper library", "Import a CSV and browse the titles, abstracts, and years in your corpus.")
        actions = ctk.CTkFrame(self.body, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 12))
        button(actions, "Import CSV", self.choose_csv).pack(side="left")
        button(actions, "Load sample", lambda: self.load_dataset(SAMPLE_PATH, sample=True), primary=False).pack(side="left", padx=8)
        label(actions, "UTF-8 CSV  •  title, abstract, year", 11, MUTED).pack(side="right")

        panel = card(self.body)
        panel.pack(fill="x")
        toolbar = ctk.CTkFrame(panel, fg_color="transparent")
        toolbar.pack(fill="x", padx=17, pady=(15, 8))
        search = ctk.CTkEntry(
            toolbar, width=255, height=35, fg_color=PAPER, border_color=BORDER,
            border_width=1, text_color=INK, font=(FONT, 13), textvariable=self.query,
        )
        label(toolbar, "Search papers", 12, MUTED, bold=True).pack(side="left", padx=(0, 8))
        search.pack(side="left")
        self.match_count = label(toolbar, "", 11, MUTED)
        self.match_count.pack(side="right")
        frame, self.library_table = table(panel, [("No.", 48, False), ("Title", 490, True), ("Year", 64, False)], 7)
        frame.pack(fill="x", padx=17, pady=(0, 7))
        self.library_table.bind("<<TreeviewSelect>>", self.show_abstract)

        self.paper_title = label(panel, "", 18, serif=True, wraplength=620, justify="left")
        self.paper_title.pack(anchor="w", padx=18)
        self.abstract = ctk.CTkTextbox(
            panel, height=90, fg_color=PAPER, text_color=INK, wrap="word",
            font=ctk.CTkFont(family=FONT, size=13), border_width=0,
            scrollbar_button_color=BORDER,
        )
        self.abstract.pack(fill="x", padx=12, pady=(0, 12))
        self.refresh_library()

    def choose_csv(self):
        path = filedialog.askopenfilename(parent=self, title="Import papers", filetypes=[("CSV files", "*.csv"), ("All files", "*")])
        if path:
            self.load_dataset(path)

    def refresh_library(self, *_):
        tree = getattr(self, "library_table", None)
        if tree is None:
            return
        query = self.query.get().strip()
        papers = self.papers
        if papers is not None and query:
            matches = papers.apply(lambda column: column.str.contains(query, case=False, regex=False))
            papers = papers.loc[matches.any(axis=1)]
        if papers is not None:
            fill_table(tree, ((index, (index + 1, paper.title, paper.year or "—")) for index, paper in papers.iterrows()))
        count = 0 if papers is None else len(papers)
        self.match_count.configure(text=f"{count} of {0 if self.papers is None else len(self.papers)} papers")
        self.set_abstract("Select a paper", "The abstract for the selected paper will appear here.")

    def show_abstract(self, _event):
        selection = self.library_table.selection()
        if selection:
            paper = self.papers.loc[int(selection[0])]
            self.set_abstract(paper.title, paper.abstract or "No abstract was provided.")

    def set_abstract(self, title, abstract):
        self.paper_title.configure(text=title)
        self.abstract.configure(state="normal")
        self.abstract.delete("1.0", "end")
        self.abstract.insert("1.0", abstract)
        self.abstract.configure(state="disabled")

    def draw_keywords(self, panel, limit, height):
        if self.analysis is None or self.analysis.keywords.empty:
            self.empty_message(panel, "There are no usable terms to chart. Try papers with longer titles or abstracts.")
            return
        embed_figure(panel, keyword_figure(self.analysis.keywords.head(limit), height)).pack(fill="x", padx=15, pady=(1, 10))

    def keywords(self):
        self.heading("03 / TEXT ANALYSIS", "Keyword analysis", "Explore which terms carry the most weight across titles and abstracts.")
        panel = card(self.body)
        panel.pack(fill="x")
        toolbar = ctk.CTkFrame(panel, fg_color="transparent")
        toolbar.pack(fill="x", padx=18, pady=(14, 1))
        label(toolbar, "Ranked terms", 22, serif=True).pack(side="left")
        export = button(toolbar, "Export CSV", self.export_keywords)
        export.pack(side="right")
        if self.analysis is None or self.analysis.keywords.empty:
            export.configure(state="disabled")
        label(panel, "Top 15 terms by mean TF-IDF. The CSV includes all ranked terms.", 12, MUTED).pack(anchor="w", padx=18, pady=(0, 4))
        self.draw_keywords(panel, 15, 3.75)
        label(self.body, "TF-IDF measures term importance within this corpus.", 12, MUTED).pack(anchor="w", pady=(11, 0))

    def export_keywords(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Export keyword analysis", defaultextension=".csv",
            initialfile="keyword_analysis.csv", filetypes=[("CSV files", "*.csv")],
        )
        if path:
            try:
                self.analysis.keywords.to_csv(path, index=False, encoding="utf-8")
            except OSError as error:
                messagebox.showerror("Could not save CSV", str(error), parent=self)
            else:
                messagebox.showinfo("Keywords exported", f"Saved {len(self.analysis.keywords)} terms to {Path(path).name}.", parent=self)

    def similarity(self):
        self.heading("04 / DOCUMENT COMPARISON", "Paper similarity", "Compare titles and abstracts using cosine similarity on TF-IDF vectors.")
        if self.analysis is None or self.analysis.average_similarity is None:
            panel = card(self.body)
            panel.pack(fill="x")
            self.section(panel, "Pairwise similarity", "Cosine similarity requires two papers with usable terms.")
            self.empty_message(panel, "Import at least two papers with usable text to see the heatmap and related papers.")
            return

        panels = ctk.CTkFrame(self.body, fg_color="transparent")
        panels.pack(fill="x")
        panels.grid_columnconfigure(0, weight=3, uniform="similarity")
        panels.grid_columnconfigure(1, weight=2, uniform="similarity")
        chart = card(panels)
        chart.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.section(chart, "Pairwise similarity", "Numbers follow import order. Gray cells show self-comparisons or unavailable scores.")
        embed_figure(chart, similarity_figure(self.analysis.similarity)).pack(fill="x", padx=12, pady=(0, 11))

        related = card(panels)
        related.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.section(related, "Closest papers", "Select a paper to see up to three textual matches.")
        frame, self.paper_picker = table(related, [("No.", 48, False), ("Paper title", 170, True)], 4)
        frame.pack(fill="x", padx=15, pady=(3, 7))
        fill_table(self.paper_picker, ((index, (index + 1, shorten(paper.title, 30))) for index, paper in self.papers.iterrows()))
        self.matches = ctk.CTkFrame(related, fg_color="transparent")
        self.matches.pack(fill="x", padx=17, pady=(0, 9))
        self.paper_picker.bind("<<TreeviewSelect>>", self.show_related)
        self.paper_picker.selection_set("0")
        self.show_related()
        label(self.body, "Cosine similarity measures textual overlap between papers.", 12, MUTED).pack(anchor="w", pady=(10, 0))

    def show_related(self, _event=None):
        selected = self.paper_picker.selection()
        if not selected:
            return
        for widget in self.matches.winfo_children():
            widget.destroy()
        related = self.analysis.related_papers(int(selected[0]))
        if related.empty:
            label(self.matches, "No comparable papers for this selection.", 12, MUTED, wraplength=220, justify="left").pack(anchor="w")
        for index, score in related.items():
            row = ctk.CTkFrame(self.matches, fg_color="transparent")
            row.pack(fill="x", pady=2)
            title = self.papers.at[index, "title"]
            label(row, f"{index + 1:02d}  {shorten(title, 60)}", 12, wraplength=170, justify="left").pack(side="left")
            label(row, f"{score:.1%}", 12, ACCENT, bold=True).pack(side="right")


if __name__ == "__main__":
    ResearchMap().mainloop()
