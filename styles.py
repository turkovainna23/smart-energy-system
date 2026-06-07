import tkinter as tk
from tkinter import ttk


class Colors:
    """Палітра кольорів системи - сучасний дизайн"""
    PRIMARY = "#0D47A1"      # Глибокий синій
    SECONDARY = "#37474F"    # Темно-сірий
    ACCENT = "#FF6D00"       # Яскравий помаранчевий
    SUCCESS = "#2E7D32"      # Зелений
    WARNING = "#F57F17"      # Жовтий
    DANGER = "#C62828"       # Червоний
    BG = "#ECEFF1"          # Світло-сірий фон
    SURFACE = "#FFFFFF"      # Білий
    TEXT = "#212121"         # Темний текст
    TEXT_LIGHT = "#757575"   # Світлий текст
    HOVER = "#1565C0"        # Синій при наведенні


def apply_styles(root):
    """Застосування глобальних стилів"""
   
    # Налаштування кореневого вікна
    root.configure(bg=Colors.BG)
   
    # Створення стилів для ttk
    style = ttk.Style()
    style.theme_use('clam')
   
    # Стиль для Treeview (таблиць)
    style.configure(
        "Treeview",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        rowheight=30,
        fieldbackground=Colors.SURFACE,
        borderwidth=0
    )
   
    style.configure(
        "Treeview.Heading",
        background=Colors.PRIMARY,
        foreground="white",
        relief="flat",
        font=("Arial", 10, "bold")
    )
   
    style.map(
        "Treeview",
        background=[("selected", Colors.PRIMARY)],
        foreground=[("selected", "white")]
    )
   
    # Стиль для Entry
    style.configure(
        "TEntry",
        fieldbackground=Colors.SURFACE,
        borderwidth=2,
        relief="solid"
    )
   
    # Стиль для Button
    style.configure(
        "TButton",
        background=Colors.PRIMARY,
        foreground="white",
        borderwidth=0,
        focuscolor="none",
        font=("Arial", 10)
    )
   
    style.map(
        "TButton",
        background=[("active", Colors.ACCENT)]
    )
   
    # Стиль для Label
    style.configure(
        "TLabel",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        font=("Arial", 10)
    )
   
    # Стиль для Frame
    style.configure(
        "TFrame",
        background=Colors.SURFACE
    )
   
    # Стиль для LabelFrame
    style.configure(
        "TLabelframe",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        borderwidth=2,
        relief="solid"
    )
   
    style.configure(
        "TLabelframe.Label",
        background=Colors.SURFACE,
        foreground=Colors.PRIMARY,
        font=("Arial", 12, "bold")
    )


def create_card_frame(parent, title=None, bg=Colors.SURFACE):
    """Створення картки з тінню"""
    card = tk.Frame(
        parent,
        bg=bg,
        relief=tk.RAISED,
        borderwidth=2
    )
   
    if title:
        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 14, "bold"),
            bg=bg,
            fg=Colors.TEXT
        )
        title_label.pack(pady=10, padx=10, anchor=tk.W)
   
    return card


def create_stat_card(parent, label, value, color=Colors.PRIMARY):
    """Створення статистичної картки"""
    card = tk.Frame(
        parent,
        bg=color,
        relief=tk.RAISED,
        borderwidth=2
    )
   
    value_label = tk.Label(
        card,
        text=str(value),
        font=("Arial", 28, "bold"),
        bg=color,
        fg="white"
    )
    value_label.pack(pady=(15, 5))
   
    label_widget = tk.Label(
        card,
        text=label,
        font=("Arial", 11),
        bg=color,
        fg="white"
    )
    label_widget.pack(pady=(5, 15))
   
    return card


def create_button(parent, text, command, bg=Colors.PRIMARY, fg="white", **kwargs):
    """Створення стилізованої кнопки"""
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=("Arial", 10, "bold"),
        relief=tk.FLAT,
        cursor="hand2",
        padx=15,
        pady=8,
        **kwargs
    )
   
    # Ефекти при наведенні
    def on_enter(e):
        button.config(bg=Colors.ACCENT if bg == Colors.PRIMARY else Colors.PRIMARY)
   
    def on_leave(e):
        button.config(bg=bg)
   
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
   
    return button


def create_input_field(parent, label_text, row, default_value=""):
    """Створення поля введення з міткою"""
    tk.Label(
        parent,
        text=label_text,
        bg=Colors.SURFACE,
        fg=Colors.TEXT,
        font=("Arial", 10)
    ).grid(row=row, column=0, padx=10, pady=10, sticky=tk.W)
   
    entry = tk.Entry(
        parent,
        width=30,
        font=("Arial", 10),
        relief=tk.SOLID,
        borderwidth=1
    )
    entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.EW)
   
    if default_value:
        entry.insert(0, default_value)
   
    return entry


def create_table(parent, columns, data=None):
    """Створення таблиці з даними"""
    # Фрейм для таблиці
    table_frame = tk.Frame(parent, bg=Colors.SURFACE)
   
    # Створення Treeview
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        selectmode="browse"
    )
   
    # Налаштування колонок
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor=tk.CENTER)
   
    # Скролбар
    scrollbar_y = ttk.Scrollbar(
        table_frame,
        orient=tk.VERTICAL,
        command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar_y.set)
   
    scrollbar_x = ttk.Scrollbar(
        table_frame,
        orient=tk.HORIZONTAL,
        command=tree.xview
    )
    tree.configure(xscrollcommand=scrollbar_x.set)
   
    # Розміщення елементів
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")
   
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)
   
    # Заповнення даними
    if data:
        for row in data:
            tree.insert("", tk.END, values=row)
   
    return table_frame, tree


def create_alert_badge(parent, alert_type, severity):
    """Створення бейджа для аварії"""
    colors = {
        "Low": Colors.SUCCESS,
        "Medium": Colors.WARNING,
        "High": Colors.ACCENT,
        "Critical": Colors.DANGER
    }
   
    bg_color = colors.get(severity, Colors.TEXT_LIGHT)
   
    badge = tk.Label(
        parent,
        text=alert_type,
        bg=bg_color,
        fg="white",
        font=("Arial", 9, "bold"),
        padx=8,
        pady=4,
        relief=tk.FLAT
    )
   
    return badge


def create_progress_bar(parent, value, max_value=100, color=Colors.SUCCESS):
    """Створення прогрес-бару"""
    frame = tk.Frame(parent, bg=Colors.SURFACE, height=30)
   
    # Фон
    bg_canvas = tk.Canvas(
        frame,
        bg="#E0E0E0",
        height=20,
        highlightthickness=0
    )
    bg_canvas.pack(fill=tk.X, padx=5, pady=5)
   
    # Заповнення
    percentage = min(100, (value / max_value) * 100)
   
    def draw_progress():
        width = bg_canvas.winfo_width()
        fill_width = int(width * percentage / 100)
        bg_canvas.delete("all")
        bg_canvas.create_rectangle(
            0, 0, fill_width, 20,
            fill=color,
            outline=""
        )
        bg_canvas.create_text(
            width // 2, 10,
            text=f"{percentage:.1f}%",
            fill=Colors.TEXT,
            font=("Arial", 9, "bold")
        )
   
    bg_canvas.after(100, draw_progress)
   
    return frame


def create_gauge(parent, value, max_value, label, unit, color=Colors.PRIMARY):
    """Створення круглого індикатора"""
    size = 150
   
    canvas = tk.Canvas(
        parent,
        width=size,
        height=size + 40,
        bg=Colors.SURFACE,
        highlightthickness=0
    )
   
    # Фонове коло
    canvas.create_oval(
        10, 10, size - 10, size - 10,
        outline=Colors.TEXT_LIGHT,
        width=8
    )
   
    # Заповнене коло
    percentage = min(100, (value / max_value) * 100)
    extent = int(360 * percentage / 100)
   
    canvas.create_arc(
        10, 10, size - 10, size - 10,
        start=90,
        extent=-extent,
        outline=color,
        width=8,
        style=tk.ARC
    )
   
    # Значення в центрі
    canvas.create_text(
        size // 2, size // 2 - 10,
        text=f"{value:.1f}",
        font=("Arial", 24, "bold"),
        fill=Colors.TEXT
    )
   
    canvas.create_text(
        size // 2, size // 2 + 15,
        text=unit,
        font=("Arial", 10),
        fill=Colors.TEXT_LIGHT
    )
   
    # Мітка знизу
    canvas.create_text(
        size // 2, size + 20,
        text=label,
        font=("Arial", 11, "bold"),
        fill=Colors.TEXT
    )
   
    return canvas


def show_notification(parent, message, type="info"):
    """Показ сповіщення"""
    colors = {
        "info": Colors.PRIMARY,
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "error": Colors.DANGER
    }
   
    bg_color = colors.get(type, Colors.PRIMARY)
   
    notification = tk.Frame(
        parent,
        bg=bg_color,
        relief=tk.RAISED,
        borderwidth=2
    )
   
    notification.place(relx=0.5, rely=0.1, anchor=tk.CENTER)
   
    label = tk.Label(
        notification,
        text=message,
        bg=bg_color,
        fg="white",
        font=("Arial", 12, "bold"),
        padx=20,
        pady=10
    )
    label.pack()
   
    # Автоматичне приховування через 3 секунди
    parent.after(3000, notification.destroy)
   
    return notification


def apply_hover_effect(widget, enter_bg, leave_bg):
    """Додавання ефекту при наведенні"""
    def on_enter(e):
        widget.config(bg=enter_bg)
   
    def on_leave(e):
        widget.config(bg=leave_bg)
   
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

