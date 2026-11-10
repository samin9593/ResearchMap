"""Shared colors, tables and Matplotlib figures."""

from tkinter import ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap, PowerNorm
from matplotlib.figure import Figure


BACKGROUND = "#F5F2EE"
PAPER = "#FCFAF7"
SIDEBAR = "#EDE9E3"
BLUE = "#78939A"
SAGE = "#A3AE9B"
TERRACOTTA = "#A86660"
BORDER = "#D8D3CE"
INK = "#444B4A"
MUTED = "#626B68"
ACCENT = "#41616A"
ACTIVE = "#DCE6E5"
STRIPE = "#F4F1ED"
FONT = "Helvetica Neue"
SERIF = "Georgia"


def card(parent):
    return ctk.CTkFrame(parent, fg_color=PAPER, corner_radius=16, border_width=1, border_color=BORDER)


def label(parent, text, size=13, color=INK, bold=False, serif=False, **kwargs):
    font = ctk.CTkFont(family=SERIF if serif else FONT, size=size, weight="bold" if bold else "normal")
    return ctk.CTkLabel(parent, text=text, text_color=color, font=font, anchor="w", **kwargs)


def button(parent, text, command, primary=True):
    return ctk.CTkButton(
        parent, text=text, command=command, height=36, width=116, corner_radius=8,
        fg_color=ACCENT if primary else PAPER, hover_color="#345059" if primary else ACTIVE,
        text_color="#FFFFFF" if primary else ACCENT, text_color_disabled=MUTED,
        border_width=0 if primary else 1, border_color=BORDER,
        font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
    )


def configure_tables(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "Research.Treeview", background=PAPER, fieldbackground=PAPER,
        foreground=INK, rowheight=31, borderwidth=0, relief="flat", font=(FONT, 12),
    )
    style.configure(
        "Research.Treeview.Heading", background=STRIPE, foreground=MUTED,
        borderwidth=0, relief="flat", padding=(8, 6), font=(FONT, 11, "bold"),
    )
    style.map(
        "Research.Treeview", background=[("selected", ACTIVE)],
        foreground=[("selected", INK)],
    )


def table(parent, columns, height):
    """Create a compact table with alternating rows and a vertical scrollbar."""
    frame = ctk.CTkFrame(parent, fg_color=PAPER)
    names = [name for name, _, _ in columns]
    tree = ttk.Treeview(
        frame, columns=names, height=height, show="headings", style="Research.Treeview",
        selectmode="browse",
    )
    for name, width, stretch in columns:
        tree.heading(name, text=name, anchor="w")
        tree.column(name, width=width, minwidth=48, stretch=stretch, anchor="w")
    tree.tag_configure("alternate", background=STRIPE)
    scrollbar = ctk.CTkScrollbar(frame, command=tree.yview, fg_color=PAPER, button_color=BORDER)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y", padx=(5, 0))
    return frame, tree


def fill_table(tree, rows):
    tree.delete(*tree.get_children())
    for position, (row_id, values) in enumerate(rows):
        tree.insert("", "end", iid=str(row_id), values=values, tags=("alternate",) if position % 2 else ())


def keyword_figure(keywords, height):
    figure = Figure(figsize=(5, height), dpi=120, facecolor=PAPER, layout="constrained")
    axes = figure.add_subplot(facecolor=PAPER)
    terms = keywords.iloc[::-1]
    colors = [BLUE] * len(terms)
    colors[-1] = TERRACOTTA
    axes.barh(terms["keyword"], terms["mean_tfidf"], height=0.57, color=colors, zorder=3)
    axes.set_xlabel("Mean TF-IDF", color=MUTED, fontsize=9, labelpad=5)
    axes.tick_params(axis="both", length=0, labelsize=9, colors=INK, pad=5)
    axes.grid(axis="x", color=BORDER, linewidth=0.65, alpha=0.7)
    for spine in axes.spines.values():
        spine.set_visible(False)
    return figure


def similarity_figure(similarity):
    figure = Figure(figsize=(5.4, 4.1), dpi=120, facecolor=PAPER, layout="constrained")
    axes = figure.add_subplot(facecolor=PAPER)
    colors = LinearSegmentedColormap.from_list("research", ["#F0EAE1", SAGE, BLUE, ACCENT])
    colors.set_bad(BORDER)
    values = similarity.to_numpy().copy()
    # The diagonal is hidden so comparisons between different papers stand out.
    for index in range(len(values)):
        values[index, index] = float("nan")
    image = axes.imshow(values, norm=PowerNorm(gamma=0.7, vmin=0, vmax=1), cmap=colors, interpolation="nearest")
    count = len(similarity)
    ticks = range(count) if count <= 18 else range(0, count, (count + 9) // 10)
    axes.set_xticks(ticks, [str(index + 1) for index in ticks])
    axes.set_yticks(ticks, [str(index + 1) for index in ticks])
    axes.set_xlabel("Paper number", color=MUTED, fontsize=9, labelpad=6)
    axes.set_ylabel("Paper number", color=MUTED, fontsize=9, labelpad=6)
    axes.tick_params(length=0, labelsize=8, colors=INK)
    for spine in axes.spines.values():
        spine.set_visible(False)
    scale = figure.colorbar(image, ax=axes, ticks=[0, 0.25, 0.5, 0.75, 1], shrink=0.84)
    scale.ax.tick_params(length=0, labelsize=8, colors=MUTED)
    scale.outline.set_visible(False)
    return figure


def embed_figure(parent, figure):
    canvas = FigureCanvasTkAgg(figure, master=parent)
    canvas.get_tk_widget().configure(background=PAPER, highlightthickness=0)
    canvas.draw()
    return canvas.get_tk_widget()
