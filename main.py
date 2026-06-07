import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import threading
import time
from classes import Building, Apartment, Meter, SensorData, Alert, User, Report
from functions import DatabaseManager, AnalyticsEngine, NotificationService
from styles import apply_styles, Colors


class SmartEnergySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart-система електрозабезпечення ЖК Gravity Park")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  # Розгорнути на весь екран
        # Ініціалізація бази даних
        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine(self.db)
        self.notifications = NotificationService()
       
        # Застосування стилів
        apply_styles(self.root)
       
        # Статус імітації
        self.simulation_running = False
        self.simulation_threads = {}  # Окремі потоки для кожного будинку
        self.selected_building = None
       
        # Створення інтерфейсу
        self.create_widgets()
       
        # Завантаження початкових даних
        self.load_data()
       
    def create_widgets(self):
        # Верхня панель з градієнтом
        top_frame = tk.Frame(self.root, bg=Colors.PRIMARY, height=100)
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        top_frame.pack_propagate(False)
       
        # Заголовок
        title_container = tk.Frame(top_frame, bg=Colors.PRIMARY)
        title_container.pack(expand=True)
       
        tk.Label(
            title_container,
            text="⚡ Smart Energy System",
            font=("Segoe UI", 24, "bold"),
            bg=Colors.PRIMARY,
            fg="white"
        ).pack()
       
        tk.Label(
            title_container,
            text="ЖК Gravity Park • Система електрозабезпечення",
            font=("Segoe UI", 11),
            bg=Colors.PRIMARY,
            fg="#B3E5FC"
        ).pack()
       
        # Головний контейнер
        main_container = tk.Frame(self.root, bg=Colors.BG)
        main_container.pack(fill=tk.BOTH, expand=True)
       
        # Ліва панель - меню та повідомлення
        left_panel = tk.Frame(main_container, bg=Colors.SURFACE, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)
       
        # Меню навігації
        nav_frame = tk.Frame(left_panel, bg=Colors.SURFACE)
        nav_frame.pack(fill=tk.X, pady=15)
       
        tk.Label(
            nav_frame,
            text="📋 Навігація",
            font=("Segoe UI", 13, "bold"),
            bg=Colors.SURFACE,
            fg=Colors.TEXT
        ).pack(pady=(0, 10), padx=15, anchor=tk.W)
       
        # Кнопки меню
        menu_buttons = [
            ("📊", "Моніторинг", self.show_monitoring),
            ("🏢", "Будинки", self.show_buildings),
            ("🏠", "Квартири", self.show_apartments),
            ("⚡", "Лічильники", self.show_meters),
            ("🚨", "Аварії", self.show_alerts),
            ("📄", "Звіти", self.show_reports),
        ]
       
        for icon, text, command in menu_buttons:
            btn_frame = tk.Frame(nav_frame, bg=Colors.SURFACE)
            btn_frame.pack(fill=tk.X, padx=10, pady=3)
           
            btn = tk.Button(
                btn_frame,
                text=f"{icon}  {text}",
                command=command,
                bg="white",
                fg=Colors.TEXT,
                font=("Segoe UI", 10),
                relief=tk.FLAT,
                cursor="hand2",
                anchor=tk.W,
                padx=15,
                pady=10
            )
            btn.pack(fill=tk.X)
           
            def on_enter(e, b=btn):
                b.config(bg=Colors.PRIMARY, fg="white")
            def on_leave(e, b=btn):
                b.config(bg="white", fg=Colors.TEXT)
           
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
       
        # Розділювач
        tk.Frame(left_panel, bg=Colors.BG, height=2).pack(fill=tk.X, pady=15)
       
# Секція повідомлень 
        msg_header = tk.Frame(left_panel, bg=Colors.SURFACE) 
        msg_header.pack(fill=tk.X, padx=15, pady=(0, 10)) 
        
        tk.Label( 
            msg_header, 
            text="💬 Повідомлення", 
            font=("Segoe UI", 13, "bold"), 
            bg=Colors.SURFACE, 
            fg=Colors.TEXT 
        ).pack(side=tk.LEFT) 
        
        # Кнопка очистки повідомлень 
        tk.Button( 
            msg_header, 
            text="🗑️", 
            command=self.clear_messages, 
            bg=Colors.DANGER, 
            fg="white", 
            font=("Segoe UI", 9, "bold"), 
            relief=tk.FLAT, 
            cursor="hand2", 
            padx=8, 
            pady=4 
        ).pack(side=tk.RIGHT) 
        
        # Фрейм для повідомлень зі скролом 
        messages_container = tk.Frame(left_panel, bg=Colors.SURFACE) 
        messages_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10)) 
 
        # Canvas для скролу 
        self.messages_canvas = tk.Canvas(messages_container, bg=Colors.SURFACE, highlightthickness=0) 
        messages_scrollbar = tk.Scrollbar(messages_container, orient="vertical", command=self.messages_canvas.yview) 
 
        self.messages_frame = tk.Frame(self.messages_canvas, bg=Colors.SURFACE) 
 
        # Зв'язуємо розмір контенту з областю скролу 
        self.messages_frame.bind( 
            "<Configure>", 
            lambda e: self.messages_canvas.configure( 
                scrollregion=self.messages_canvas.bbox("all"), 
                width=messages_container.winfo_width() 
            ) 
        ) 
 
        self.messages_canvas.create_window((0, 0), window=self.messages_frame, anchor="nw") 
        self.messages_canvas.configure(yscrollcommand=messages_scrollbar.set) 
 
        # ⚡ Прокрутка колесиком тільки коли мишка над списком 
        def _on_mousewheel(event): 
            self.messages_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units") 
 
        self.messages_canvas.bind("<Enter>", lambda e: self.messages_canvas.bind_all("<MouseWheel>", _on_mousewheel)) 
        self.messages_canvas.bind("<Leave>", lambda e: self.messages_canvas.unbind_all("<MouseWheel>")) 
 
        self.messages_canvas.pack(side="left", fill="both", expand=True) 
        messages_scrollbar.pack(side="right", fill="y") 
        
        # Додаємо початкове повідомлення 
        self.add_system_message("Система запущена і готова до роботи", "success")
       
        # Права панель - контент
        self.content_frame = tk.Frame(main_container, bg=Colors.BG)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
       
        # Показуємо моніторинг за замовчуванням
        self.show_monitoring()
   
    def add_system_message(self, message, msg_type="info"):
        """Додавання системного повідомлення"""
        colors = {
            "info": ("#E3F2FD", Colors.PRIMARY, "ℹ️"),
            "warning": ("#FFF3E0", Colors.WARNING, "⚠️"),
            "error": ("#FFEBEE", Colors.DANGER, "❌"),
            "success": ("#E8F5E9", Colors.SUCCESS, "✅")
        }
       
        bg_color, border_color, icon = colors.get(msg_type, colors["info"])
       
        msg_frame = tk.Frame(
            self.messages_frame,
            bg=bg_color,
            relief=tk.SOLID,
            borderwidth=1,
            cursor="hand2"
        )
        msg_frame.pack(fill=tk.X, pady=3, padx=3)
       
        # Контейнер для тексту
        text_container = tk.Frame(msg_frame, bg=bg_color)
        text_container.pack(fill=tk.X, padx=8, pady=8)
       
        # Час та іконка
        header_frame = tk.Frame(text_container, bg=bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 3))
       
        time_str = datetime.now().strftime("%H:%M:%S")
        tk.Label(
            header_frame,
            text=f"{icon} {time_str}",
            font=("Segoe UI", 8, "bold"),
            bg=bg_color,
            fg=border_color
        ).pack(side=tk.LEFT)
       
        # Текст повідомлення
        msg_label = tk.Label(
            text_container,
            text=message,
            font=("Segoe UI", 9),
            bg=bg_color,
            fg=Colors.TEXT,
            wraplength=220,
            justify=tk.LEFT,
            anchor=tk.W
        )
        msg_label.pack(fill=tk.X)
       
        # Ефект при наведенні
        def on_enter(e):
            msg_frame.config(bg="#FAFAFA")
            text_container.config(bg="#FAFAFA")
            header_frame.config(bg="#FAFAFA")
            msg_label.config(bg="#FAFAFA")
       
        def on_leave(e):
            msg_frame.config(bg=bg_color)
            text_container.config(bg=bg_color)
            header_frame.config(bg=bg_color)
            msg_label.config(bg=bg_color)
       
        msg_frame.bind("<Enter>", on_enter)
        msg_frame.bind("<Leave>", on_leave)
        text_container.bind("<Enter>", on_enter)
        text_container.bind("<Leave>", on_leave)
       
        # Автоматична прокрутка вниз
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)
       
        # Обмеження кількості повідомлень (не більше 100)
        messages = self.messages_frame.winfo_children()
        if len(messages) > 100:
            messages[0].destroy()
   
    def clear_messages(self):
        """Очистити всі повідомлення"""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.add_system_message("Повідомлення очищено", "info")
   
    def add_resident_message(self, building_name, apartment, message):
        """Повідомлення від мешканця"""
        self.add_system_message(
            f"🏠 {building_name}\nКв.{apartment}: {message}",
            "warning"
        )
   
    def add_engineer_message(self, message):
        """Повідомлення від інженерного відділу"""
        self.add_system_message(f"👷 Інженерний відділ:\n{message}", "success")
   
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
   
    def show_monitoring(self):
        self.clear_content()
       
        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))
       
        tk.Label(
            header,
            text="📊 Моніторинг системи в реальному часі",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)
       
        # Canvas зі скролом для всього контенту
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG)
       
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
       
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
       
        # Вибір будинку
        selector_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        selector_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
       
        tk.Label(
            selector_frame,
            text="🏢 Оберіть будинок для моніторингу:",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg=Colors.TEXT
        ).pack(side=tk.LEFT, padx=20, pady=15)
       
        buildings = self.db.get_all_buildings()
        if buildings:
            building_names = [f"{b['address']} (ID: {b['id']})" for b in buildings]
           
            self.selected_building_var = tk.StringVar(value=building_names[0])
           
            building_menu = ttk.Combobox(
                selector_frame,
                textvariable=self.selected_building_var,
                values=building_names,
                state="readonly",
                font=("Segoe UI", 10),
                width=40
            )
            building_menu.pack(side=tk.LEFT, padx=10, pady=15)
           
            tk.Button(
                selector_frame,
                text="🔍 Показати",
                command=lambda: self.update_monitoring_display(scrollable_frame, buildings),
                bg=Colors.PRIMARY,
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                padx=20,
                pady=8
            ).pack(side=tk.LEFT, padx=10)
           
            # Показуємо перший будинок за замовчуванням
            self.update_monitoring_display(scrollable_frame, buildings)
       
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
       
        # Додаємо прокрутку мишею
        self.bind_mousewheel(canvas)
   
    def update_monitoring_display(self, parent, buildings):
        """Оновлення відображення моніторингу"""
        # Видаляємо старий контент (крім селектора будинку зверху)
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame) and widget != parent.winfo_children()[0]:
                widget.destroy()

        # Знаходимо обраний будинок
        selected_text = self.selected_building_var.get()
        building_id = int(selected_text.split("ID: ")[1].rstrip(")"))
        building = self.db.get_building_by_id(building_id)

        # Статистичні картки
        stats_frame = tk.Frame(parent, bg=Colors.BG)
        stats_frame.pack(fill=tk.X, padx=5, pady=10)

        stats = self.db.get_building_stats(building_id)

        stat_items = [
            ("Всього квартир", stats['apartments_count'], Colors.PRIMARY),
            ("Активних лічильників", stats['active_meters'], Colors.SUCCESS),
            ("Активних аварій", stats['active_alerts'], Colors.DANGER),
            ("Середнє споживання", f"{stats['avg_power']:.1f} кВт", Colors.ACCENT),
        ]

        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_frame, bg=color, relief=tk.RAISED, bd=2)
            card.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)

            tk.Label(
                card,
                text=str(value),
                font=("Segoe UI", 24, "bold"),
                bg=color,
                fg="white",
            ).pack(pady=(10, 0))

            tk.Label(
                card,
                text=label,
                font=("Segoe UI", 10),
                bg=color,
                fg="white",
            ).pack(pady=(0, 10))

        # ОДИН спільний банер про режим роботи будинку
        mode_frame = tk.Frame(parent, bg=Colors.BG)
        mode_frame.pack(fill=tk.X, padx=5)

        # Пробуємо дізнатися, чи є критична аварія (якщо метод існує)
        has_critical = False
        if hasattr(self.db, "building_has_critical_alert"):
            try:
                has_critical = self.db.building_has_critical_alert(building_id)
            except Exception:
                has_critical = False

        if has_critical:
            mode_text = (
                "☀️ Будинок працює в АВТОНОМНОМУ режимі: "
                "живлення від сонячних панелей (активні критичні аварії)."
            )
            mode_bg = "#FFFDE7"
            mode_fg = Colors.WARNING
        elif stats.get("active_alerts", 0) > 0:
            mode_text = (
                "⚠️ Будинок працює від основної електромережі, "
                "є активні серйозні аварії. Перегляньте розділ 'Аварії'."
            )
            mode_bg = "#FFF3E0"
            mode_fg = Colors.DANGER
        else:
            mode_text = (
                "⚡ Будинок працює від основної електромережі, "
                "активних серйозних/критичних аварій немає."
            )
            mode_bg = "#E8F5E9"
            mode_fg = Colors.SUCCESS

        tk.Label(
            mode_frame,
            text=mode_text,
            font=("Segoe UI", 10, "bold"),
            bg=mode_bg,
            fg=mode_fg,
            padx=15,
            pady=8,
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(0, 10))

        # Графік / таблиця споживання квартир
        graph_frame = tk.LabelFrame(
            parent,
            text=f"📊 Споживання квартир будинку: {building['address']}",
            bg="white",
            fg=Colors.TEXT,
            font=("Segoe UI", 12, "bold"),
            relief=tk.RAISED,
            borderwidth=2,
        )
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)

        # Таблиця квартир
        tree_frame = tk.Frame(graph_frame, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = (
            "Квартира",
            "Поверх",
            "Напруга (В)",
            "Струм (А)",
            "Потужність (кВт)",
            "Статус",
        )
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Завантаження даних квартир (можеш залишити як було або відсортувати за номером)
        apartments_data = self.db.get_building_apartments_monitoring(building_id)

        for apt in apartments_data:
            status = "✅ Норма" if apt["power"] < 10 else "⚠️ Перевантаження"
            tree.insert(
                "",
                tk.END,
                values=(
                    apt["number"],
                    apt["floor"],
                    f"{apt['voltage']:.1f}" if apt["voltage"] else "-",
                    f"{apt['current']:.2f}" if apt["current"] else "-",
                    f"{apt['power']:.2f}" if apt["power"] else "-",
                    status,
                ),
            )

   
    def show_buildings(self):
        self.clear_content()

        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="🏢 Управління будинками",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)

        # Кнопки управління
        btn_frame = tk.Frame(header, bg=Colors.BG)
        btn_frame.pack(side=tk.RIGHT)

        tk.Button(
            btn_frame,
            text="➕ Додати будинок",
            command=self.add_building,
            bg=Colors.SUCCESS,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=5)

        # Canvas зі скролом для списку будинків
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=Colors.BG)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        buildings = self.db.get_all_buildings()

        if not buildings:
            tk.Label(
                scrollable,
                text="Немає будинків. Додайте перший будинок!",
                font=("Segoe UI", 12),
                bg=Colors.BG,
                fg=Colors.TEXT_LIGHT
            ).pack(pady=50)
        else:
            for building in buildings:
                self.create_building_card(scrollable, building)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Прокрутка колесом миші
        self.bind_mousewheel(canvas)

   
    def create_building_card(self, parent, building):
        """Створення картки будинку"""
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=2)
        card.pack(fill=tk.X, pady=10, padx=5)

        # Верхня частина - інфо
        top_section = tk.Frame(card, bg="white")
        top_section.pack(fill=tk.X, padx=20, pady=15)

        # Ліва частина - основна інформація
        left_info = tk.Frame(top_section, bg="white")
        left_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            left_info,
            text=building['address'],
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=Colors.TEXT
        ).pack(anchor=tk.W)

        tk.Label(
            left_info,
            text=f"📍 {building['city']} • 🏗️ {building['developer']}",
            font=("Segoe UI", 9),
            bg="white",
            fg=Colors.TEXT_LIGHT
        ).pack(anchor=tk.W, pady=(5, 0))

        # Статистика
        stats_frame = tk.Frame(left_info, bg="white")
        stats_frame.pack(anchor=tk.W, pady=(10, 0))

        stats = self.db.get_building_stats(building['id'])

        stat_items = [
            ("🏢", f"{building['floors_count']} поверхів"),
            ("🔲", f"{building['sections_count']} секцій"),
            ("🏠", f"{stats['apartments_count']} квартир"),
            ("⚡", f"{stats['active_meters']} лічильників")
        ]

        for icon, text in stat_items:
            tk.Label(
                stats_frame,
                text=f"{icon} {text}",
                font=("Segoe UI", 9),
                bg="white",
                fg=Colors.TEXT
            ).pack(side=tk.LEFT, padx=(0, 15))

        # Режим живлення (мережа / сонячні панелі)
        mode_frame = tk.Frame(left_info, bg="white")
        mode_frame.pack(anchor=tk.W, pady=(8, 0))

        is_critical = self.db.building_has_critical_alert(building['id'])
        if is_critical:
            mode_text = (
                "☀️ Автономний режим: будинок живиться від сонячних панелей "
                "(критична аварія в мережі)"
            )
            mode_fg = Colors.WARNING
        else:
            mode_text = "⚡ Нормальний режим: живлення від міської електромережі"
            mode_fg = Colors.SUCCESS

        tk.Label(
            mode_frame,
            text=mode_text,
            font=("Segoe UI", 9, "bold"),
            bg="white",
            fg=mode_fg
        ).pack(anchor=tk.W)

        # Права частина - кнопки управління
        right_buttons = tk.Frame(top_section, bg="white")
        right_buttons.pack(side=tk.RIGHT)

        # Кнопка налаштувань
        tk.Button(
            right_buttons,
            text="⚙️ Налаштування",
            command=lambda: self.edit_building(building),
            bg="#F5F5F5",
            fg=Colors.TEXT,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.TOP, pady=2)

        # Кнопка звичайної імітації
        is_running = building['id'] in self.simulation_threads
        btn_text = "⏸️ Зупинити" if is_running else "▶️ Імітація"
        btn_color = Colors.WARNING if is_running else Colors.PRIMARY

        tk.Button(
            right_buttons,
            text=btn_text,
            command=lambda: self.toggle_simulation(building['id']),
            bg=btn_color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.TOP, pady=2)

        # Кнопка КРИТИЧНОЇ аварії (тумблер)
        crit_label = (
            "☀️ Вимкнути критичну аварію"
            if is_critical else
            "☀️ Увімкнути критичну аварію (сонячні панелі)"
        )

        tk.Button(
            right_buttons,
            text=crit_label,
            command=lambda: self.simulate_critical_alert(building['id']),
            bg=Colors.ACCENT,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.TOP, pady=2)

        # Кнопка видалення
        tk.Button(
            right_buttons,
            text="🗑️ Видалити",
            command=lambda: self.delete_building(building['id']),
            bg=Colors.DANGER,
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.TOP, pady=2)

        # Нижня частина - коротка статистика
        if stats['avg_power'] > 0:
            bottom_section = tk.Frame(card, bg="#F8F9FA")
            bottom_section.pack(fill=tk.X, padx=20, pady=(0, 15))

            tk.Label(
                bottom_section,
                text=(
                    f"⚡ Середнє споживання: {stats['avg_power']:.2f} кВт | "
                    f"📊 Пікове: {stats['peak_power']:.2f} кВт | "
                    f"⚠️ Активних аварій: {stats['active_alerts']}"
                ),
                font=("Segoe UI", 9),
                bg="#F8F9FA",
                fg=Colors.TEXT
            ).pack(pady=10)


   
    def show_apartments(self):
        self.clear_content()

        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="🏠 Управління квартирами",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)

        tk.Button(
            header,
            text="➕ Додати квартиру",
            command=self.add_apartment,
            bg=Colors.SUCCESS,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side=tk.RIGHT)

        # Отримуємо будинки для фільтру
        buildings = self.db.get_all_buildings()
        if not buildings:
            tk.Label(
                self.content_frame,
                text="Немає будинків. Спочатку додайте будинок.",
                font=("Segoe UI", 12),
                bg=Colors.BG,
                fg=Colors.TEXT_LIGHT
            ).pack(pady=30)
            return

        building_options = [f"{b['address']} (ID: {b['id']})" for b in buildings]
        self.apartments_building_var = tk.StringVar(value=building_options[0])

        filter_frame = tk.Frame(self.content_frame, bg=Colors.BG)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            filter_frame,
            text="🏢 Оберіть будинок:",
            font=("Segoe UI", 10),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT, padx=(5, 5))

        building_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.apartments_building_var,
            values=building_options,
            state="readonly",
            width=40
        )
        building_menu.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Canvas зі скролом
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Таблиця квартир
        table_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("ID", "Будинок", "Номер", "Поверх", "Площа (м²)", "Власник")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        all_apartments = self.db.get_all_apartments_with_buildings()

        def get_selected_building_id():
            text = self.apartments_building_var.get()
            try:
                return int(text.split("ID: ")[1].rstrip(")"))
            except Exception:
                return buildings[0]['id']

        def load_apartments_for_building(*_):
            # очистити таблицю
            for row in tree.get_children():
                tree.delete(row)

            building_id = get_selected_building_id()
            filtered = [a for a in all_apartments if a['building_id'] == building_id]

            # впорядкувати по номеру квартири
            filtered = sorted(
                filtered,
                key=lambda a: int(a['number']) if str(a['number']).isdigit() else str(a['number'])
            )

            for apt in filtered:
                tree.insert("", tk.END, values=(
                    apt['id'],
                    apt['building_address'],
                    apt['number'],
                    apt['floor'],
                    apt['area_sqm'],
                    apt['owner_name']
                ))

        building_menu.bind("<<ComboboxSelected>>", load_apartments_for_building)
        load_apartments_for_building()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

   
    def show_meters(self):
        self.clear_content()

        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="⚡ Управління лічильниками",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)

        # Будинки для фільтра
        buildings = self.db.get_all_buildings()
        if not buildings:
            tk.Label(
                self.content_frame,
                text="Немає будинків. Спочатку додайте будинок.",
                font=("Segoe UI", 12),
                bg=Colors.BG,
                fg=Colors.TEXT_LIGHT
            ).pack(pady=30)
            return

        building_options = [f"{b['address']} (ID: {b['id']})" for b in buildings]
        self.meters_building_var = tk.StringVar(value=building_options[0])

        filter_frame = tk.Frame(self.content_frame, bg=Colors.BG)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            filter_frame,
            text="🏢 Оберіть будинок:",
            font=("Segoe UI", 10),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT, padx=(5, 5))

        building_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.meters_building_var,
            values=building_options,
            state="readonly",
            width=40
        )
        building_menu.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Canvas зі скролом
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Таблиця лічильників
        table_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("ID", "Будинок", "Квартира", "Тип", "Серійний номер", "Статус")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        all_meters = self.db.get_all_meters_with_buildings()

        def get_selected_building_id():
            text = self.meters_building_var.get()
            try:
                return int(text.split("ID: ")[1].rstrip(")"))
            except Exception:
                return buildings[0]['id']

        def load_meters_for_building(*_):
            for row in tree.get_children():
                tree.delete(row)

            building_id = get_selected_building_id()
            building = self.db.get_building_by_id(building_id)
            address = building['address']

            filtered = [m for m in all_meters if m['building_address'] == address]

            # впорядкувати за номером квартири
            filtered = sorted(
                filtered,
                key=lambda m: int(m['apartment_number']) if str(m['apartment_number']).isdigit()
                else str(m['apartment_number'])
            )

            for meter in filtered:
                tree.insert("", tk.END, values=(
                    meter['id'],
                    meter['building_address'],
                    meter['apartment_number'],
                    meter['type'],
                    meter['serial_number'],
                    meter['status']
                ))

        building_menu.bind("<<ComboboxSelected>>", load_meters_for_building)
        load_meters_for_building()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

   
    def show_alerts(self):
        self.clear_content()

        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="🚨 Аварійні сповіщення",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)

        # Будинки для фільтра
        buildings = self.db.get_all_buildings()
        if not buildings:
            tk.Label(
                self.content_frame,
                text="Немає будинків. Спочатку додайте будинок.",
                font=("Segoe UI", 12),
                bg=Colors.BG,
                fg=Colors.TEXT_LIGHT
            ).pack(pady=30)
            return

        building_options = [f"{b['address']} (ID: {b['id']})" for b in buildings]
        self.alerts_building_var = tk.StringVar(value=building_options[0])

        filter_frame = tk.Frame(self.content_frame, bg=Colors.BG)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            filter_frame,
            text="🏢 Оберіть будинок:",
            font=("Segoe UI", 10),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT, padx=(5, 5))

        building_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.alerts_building_var,
            values=building_options,
            state="readonly",
            width=40
        )
        building_menu.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Canvas зі скролом
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Таблиця аварій
        table_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("ID", "Будинок", "Квартира", "Час", "Тип", "Критичність", "Статус")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        all_alerts = self.db.get_all_alerts_with_buildings()

        def get_selected_building_id():
            text = self.alerts_building_var.get()
            try:
                return int(text.split("ID: ")[1].rstrip(")"))
            except Exception:
                return buildings[0]['id']

        def load_alerts_for_building(*_):
            for row in tree.get_children():
                tree.delete(row)

            building_id = get_selected_building_id()
            building = self.db.get_building_by_id(building_id)
            address = building['address']

            filtered = [a for a in all_alerts if a['building_address'] == address]

            # вже й так впорядковано за часом у SQL, але можна ще раз:
            filtered = sorted(filtered, key=lambda a: a['timestamp'], reverse=True)

            for alert in filtered:
                status = "✅ Вирішено" if alert['resolved'] else "⚠️ Активно"
                tree.insert("", tk.END, values=(
                    alert['id'],
                    alert['building_address'],
                    alert['apartment_number'],
                    alert['timestamp'],
                    alert['type'],
                    alert['severity'],
                    status
                ))

        building_menu.bind("<<ComboboxSelected>>", load_alerts_for_building)
        load_alerts_for_building()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

   
    def add_building(self):
        """Діалог додавання будинку"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати будинок")
        dialog.geometry("500x550")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
       
        # Заголовок
        header = tk.Frame(dialog, bg=Colors.PRIMARY, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
       
        tk.Label(
            header,
            text="➕ Новий будинок",
            font=("Segoe UI", 16, "bold"),
            bg=Colors.PRIMARY,
            fg="white"
        ).pack(pady=15)
       
        # Форма
        form_frame = tk.Frame(dialog, bg="white")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
       
        fields = [
            ("📍 Адреса:", "address", "Наприклад: вул. Солом'янська, 1"),
            ("🏢 Кількість поверхів:", "floors", "25"),
            ("🔲 Кількість секцій:", "sections", "4"),
            ("🏗️ Забудовник:", "developer", "Київміськбуд"),
            ("📍 Місто:", "city", "Київ"),
            ("🏠 Кількість квартир:", "apartments", "100")
        ]
       
        entries = {}
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Segoe UI", 10),
                bg="white",
                fg=Colors.TEXT
            ).grid(row=i, column=0, sticky=tk.W, pady=10)
           
            entry = tk.Entry(
                form_frame,
                width=30,
                font=("Segoe UI", 10),
                relief=tk.SOLID,
                borderwidth=1
            )
            entry.grid(row=i, column=1, pady=10, padx=(10, 0), sticky=tk.EW)
            entry.insert(0, placeholder)
            entries[key] = entry
       
        form_frame.columnconfigure(1, weight=1)
       
        # Кнопки
        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
       
        def save():
            try:
                building = Building(
                    address=entries['address'].get(),
                    floors_count=int(entries['floors'].get()),
                    sections_count=int(entries['sections'].get()),
                    developer=entries['developer'].get(),
                    city=entries['city'].get()
                )
                building_id = self.db.add_building(building)
               
                # Автоматичне створення квартир
                apartments_count = int(entries['apartments'].get())
                for i in range(1, apartments_count + 1):
                    apartment = Apartment(
                        building_id=building_id,
                        number=f"{i}",
                        floor=(i // 4) + 1,
                        area_sqm=50 + (i % 10) * 5,
                        tariff_plan="Стандартний",
                        owner_name=f"Власник кв. {i}"
                    )
                    apt_id = self.db.add_apartment(apartment)
                   
                    # Створення лічильника
                    meter = Meter(
                        apartment_id=apt_id,
                        meter_type="Smart",
                        serial_number=f"GM{building_id}{apt_id:04d}",
                        firmware_version="2.1.0"
                    )
                    self.db.add_meter(meter)
               
                self.add_system_message(
                    f"Будинок '{building.address}' успішно додано з {apartments_count} квартирами",
                    "success"
                )
                messagebox.showinfo("Успіх", f"Будинок та {apartments_count} квартир успішно створено!")
                dialog.destroy()
                self.show_buildings()
            except ValueError as e:
                messagebox.showerror("Помилка", f"Неправильний формат даних: {e}")
       
        tk.Button(
            btn_frame,
            text="✔️ Зберегти",
            command=save,
            bg=Colors.SUCCESS,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
       
        tk.Button(
            btn_frame,
            text="❌ Скасувати",
            command=dialog.destroy,
            bg="#E0E0E0",
            fg=Colors.TEXT,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
   
    def edit_building(self, building):
        """Редагування будинку"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Налаштування будинку")
        dialog.geometry("500x450")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
       
        # Заголовок
        header = tk.Frame(dialog, bg=Colors.PRIMARY, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
       
        tk.Label(
            header,
            text="⚙️ Налаштування будинку",
            font=("Segoe UI", 16, "bold"),
            bg=Colors.PRIMARY,
            fg="white"
        ).pack(pady=15)
       
        # Форма
        form_frame = tk.Frame(dialog, bg="white")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
       
        fields = [
            ("📍 Адреса:", "address", building['address']),
            ("🏢 Кількість поверхів:", "floors", str(building['floors_count'])),
            ("🔲 Кількість секцій:", "sections", str(building['sections_count'])),
            ("🏗️ Забудовник:", "developer", building['developer']),
            ("📍 Місто:", "city", building['city'])
        ]
       
        entries = {}
        for i, (label, key, value) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Segoe UI", 10),
                bg="white",
                fg=Colors.TEXT
            ).grid(row=i, column=0, sticky=tk.W, pady=10)
           
            entry = tk.Entry(
                form_frame,
                width=30,
                font=("Segoe UI", 10),
                relief=tk.SOLID,
                borderwidth=1
            )
            entry.grid(row=i, column=1, pady=10, padx=(10, 0), sticky=tk.EW)
            entry.insert(0, value)
            entries[key] = entry
       
        form_frame.columnconfigure(1, weight=1)
       
        # Кнопки
        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
       
        def save():
            try:
                self.db.update_building(
                    building['id'],
                    address=entries['address'].get(),
                    floors_count=int(entries['floors'].get()),
                    sections_count=int(entries['sections'].get()),
                    developer=entries['developer'].get(),
                    city=entries['city'].get()
                )
                self.add_system_message(
                    f"Будинок '{entries['address'].get()}' оновлено",
                    "success"
                )
                messagebox.showinfo("Успіх", "Зміни збережено!")
                dialog.destroy()
                self.show_buildings()
            except ValueError as e:
                messagebox.showerror("Помилка", f"Неправильний формат даних: {e}")
       
        tk.Button(
            btn_frame,
            text="✔️ Зберегти зміни",
            command=save,
            bg=Colors.SUCCESS,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
       
        tk.Button(
            btn_frame,
            text="❌ Скасувати",
            command=dialog.destroy,
            bg="#E0E0E0",
            fg=Colors.TEXT,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
   
    def delete_building(self, building_id):
        """Видалення будинку"""
        if messagebox.askyesno("Підтвердження",
                              "Ви впевнені? Це видалить будинок та всі пов'язані дані!"):
            # Зупиняємо імітацію якщо запущена
            if building_id in self.simulation_threads:
                self.stop_building_simulation(building_id)
           
            self.db.delete_building(building_id)
            self.add_system_message("Будинок видалено", "warning")
            messagebox.showinfo("Успіх", "Будинок успішно видалено!")
            self.show_buildings()
   
    def toggle_simulation(self, building_id):
        """Перемикання імітації для будинку"""
        if building_id in self.simulation_threads:
            self.stop_building_simulation(building_id)
        else:
            self.start_building_simulation(building_id)
       
        # Оновлюємо відображення
        self.show_buildings()

    def simulate_critical_alert(self, building_id: int):
        """
        Перемикає критичну аварію для будинку:
        якщо критичної аварії ще немає – створюємо її і переводимо будинок в автономний режим,
        якщо вже є – усуваємо і повертаємо на міську мережу.
        """
        building = self.db.get_building_by_id(building_id)

        # Якщо вже є активна критична аварія -> вимикаємо автономний режим
        if self.db.building_has_critical_alert(building_id):
            self.db.resolve_building_critical_alerts(building_id)
            self.add_system_message(
                f"✅ Критична аварія в будинку '{building['address']}' усунена. "
                f"Живлення повернуто до міської електромережі.",
                "success"
            )
            self.add_engineer_message(
                f"Для будинку '{building['address']}' відновлено живлення з мережі, "
                f"автономний режим вимкнено."
            )
        else:
            # Ввімкнути критичну аварію = перевести на сонячні панелі
            meters = self.db.get_building_meters(building_id)
            if not meters:
                messagebox.showwarning(
                    "Критична аварія",
                    "У будинку немає лічильників, неможливо зімітувати аварію."
                )
                return

            meter = meters[0]

            alert = Alert(
                alert_type="GridFailure",
                severity="Critical",
                message=(
                    "Дуже серйозна аварія в мережі. "
                    "Будинок перейшов в автономний режим (сонячні панелі)."
                ),
                meter_id=meter["id"],
                apartment_id=meter["apartment_id"]
            )
            self.db.add_alert(alert)

            self.add_system_message(
                f"⚠️ Критична аварія в будинку '{building['address']}'. "
                f"Будинок перейшов в автономний режим (сонячні панелі).",
                "warning"
            )
            self.add_resident_message(
                building["address"],
                meter["apartment_number"],
                "У мережі сталася дуже серйозна аварія. "
                "Система переключила будинок на живлення від сонячних панелей."
            )

        # Перемалювати картки будинків (щоб одразу було видно режим)
        self.show_buildings()

   
    def start_building_simulation(self, building_id):
        """Запуск імітації для конкретного будинку"""
        if building_id not in self.simulation_threads:
            building = self.db.get_building_by_id(building_id)
            self.add_system_message(
                f"Розпочато імітацію будинку '{building['address']}'",
                "info"
            )
           
            stop_event = threading.Event()
            thread = threading.Thread(
                target=self.run_building_simulation,
                args=(building_id, stop_event),
                daemon=True
            )
            self.simulation_threads[building_id] = {
                'thread': thread,
                'stop_event': stop_event
            }
            thread.start()

    def simulate_critical_alert(self, building_id: int):
        """
        Перемикає критичну аварію для будинку:
        якщо критичної аварії ще немає – створюємо її і переводимо будинок в автономний режим,
        якщо вже є – усуваємо і повертаємо на міську мережу.
        """
        building = self.db.get_building_by_id(building_id)

        # Якщо вже є активна критична аварія -> вимикаємо автономний режим
        if self.db.building_has_critical_alert(building_id):
            self.db.resolve_building_critical_alerts(building_id)
            self.add_system_message(
                f"✅ Критична аварія в будинку '{building['address']}' усунена. "
                f"Живлення повернуто до міської електромережі.",
                "success"
            )
            self.add_engineer_message(
                f"Для будинку '{building['address']}' відновлено живлення з мережі, "
                f"автономний режим вимкнено."
            )
        else:
            # Ввімкнути критичну аварію = перевести на сонячні панелі
            meters = self.db.get_building_meters(building_id)
            if not meters:
                messagebox.showwarning(
                    "Критична аварія",
                    "У будинку немає лічильників, неможливо зімітувати аварію."
                )
                return

            meter = meters[0]

            alert = Alert(
                alert_type="GridFailure",
                severity="Critical",
                message=(
                    "Дуже серйозна аварія в мережі. "
                    "Будинок перейшов в автономний режим (сонячні панелі)."
                ),
                meter_id=meter["id"],
                apartment_id=meter["apartment_id"]
            )
            self.db.add_alert(alert)

            self.add_system_message(
                f"⚠️ Критична аварія в будинку '{building['address']}'. "
                f"Будинок перейшов в автономний режим (сонячні панелі).",
                "warning"
            )
            self.add_resident_message(
                building["address"],
                meter["apartment_number"],
                "У мережі сталася дуже серйозна аварія. "
                "Система переключила будинок на живлення від сонячних панелей."
            )

        # Перемалювати картки будинків (щоб одразу було видно режим)
        self.show_buildings()

   
    def stop_building_simulation(self, building_id):
        """Зупинка імітації для конкретного будинку"""
        if building_id in self.simulation_threads:
            building = self.db.get_building_by_id(building_id)
            self.simulation_threads[building_id]['stop_event'].set()
           
            # Генерація звіту
            self.generate_building_report(building_id)
           
            del self.simulation_threads[building_id]
            self.add_engineer_message(
                f"Імітація будинку '{building['address']}' зупинена. Звіт створено."
            )
   
    def add_apartment(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати квартиру")
        dialog.geometry("400x400")
        dialog.configure(bg=Colors.SURFACE)
       
        fields = [
            ("ID будинку:", "building_id"),
            ("Номер квартири:", "number"),
            ("Поверх:", "floor"),
            ("Площа (м²):", "area"),
            ("Тарифний план:", "tariff"),
            ("Ім'я власника:", "owner")
        ]
       
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label, bg=Colors.SURFACE, fg=Colors.TEXT).grid(
                row=i, column=0, padx=10, pady=10, sticky=tk.W
            )
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entries[key] = entry
       
        def save():
            apartment = Apartment(
                building_id=int(entries['building_id'].get()),
                number=entries['number'].get(),
                floor=int(entries['floor'].get()),
                area_sqm=float(entries['area'].get()),
                tariff_plan=entries['tariff'].get(),
                owner_name=entries['owner'].get()
            )
            apt_id = self.db.add_apartment(apartment)
           
            # Автоматично створюємо лічильник
            meter = Meter(
                apartment_id=apt_id,
                meter_type="Smart",
                serial_number=f"GM{apt_id:06d}",
                firmware_version="1.0.0"
            )
            self.db.add_meter(meter)
           
            messagebox.showinfo("Успіх", "Квартиру і лічильник успішно додано!")
            dialog.destroy()
            self.show_apartments()
       
        tk.Button(
            dialog,
            text="Зберегти",
            command=save,
            bg=Colors.SUCCESS,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).grid(row=len(fields), column=0, columnspan=2, pady=20)
   
    def start_simulation(self):
        if not self.simulation_running:
            self.simulation_running = True
            self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
            self.simulation_thread.start()
            messagebox.showinfo("Імітація", "Імітацію автономної роботи запущено!")
   
    def stop_simulation(self):
        self.simulation_running = False
        messagebox.showinfo("Імітація", "Імітацію автономної роботи зупинено!")
   
    def run_building_simulation(self, building_id, stop_event):
        """Імітація автономної роботи для конкретного будинку"""
        building = self.db.get_building_by_id(building_id)
        simulation_start = datetime.now()
        cycle_count = 0
       
        while not stop_event.is_set():
            cycle_count += 1
            meters = self.db.get_building_meters(building_id)
           
            for meter in meters:
                if meter['status'] == 'Active':
                    # Генерація даних сенсора
                    sensor_data = self.analytics.generate_sensor_data(meter['id'])
                    self.db.add_sensor_data(sensor_data)
                   
                    # Перевірка на аварії
                    alert = self.analytics.check_for_anomalies(sensor_data)
                    if alert:
                        alert.meter_id = meter['id']
                        alert.apartment_id = meter['apartment_id']
                        alert_id = self.db.add_alert(alert)
                       
                        # Повідомлення від мешканця
                        self.root.after(0, lambda: self.add_resident_message(
                            building['address'],
                            meter['apartment_number'],
                            f"{alert.message}"
                        ))
                       
                        # Повідомлення від інженера
                        self.root.after(0, lambda: self.add_engineer_message(
                            f"Виявлено {alert.alert_type} у будинку {building['address']}, кв.{meter['apartment_number']}. Реагуємо!"
                        ))
                       
                        # Імітація усунення проблеми
                        time.sleep(2)
                        self.db.resolve_alert(alert_id, "Інженер", "Проблему усунуто дистанційно")
                       
                        self.root.after(0, lambda: self.add_engineer_message(
                            f"Аварію усунуто у кв.{meter['apartment_number']}"
                        ))
           
            # Пауза між циклами
            time.sleep(3)
       
        # Після зупинки - зберігаємо звіт
        simulation_end = datetime.now()
        duration = (simulation_end - simulation_start).total_seconds()
       
        self.db.save_simulation_report(
            building_id=building_id,
            start_time=simulation_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=simulation_end.strftime("%Y-%m-%d %H:%M:%S"),
            cycles_count=cycle_count,
            duration_seconds=duration
        )
   
    def generate_building_report(self, building_id):
        """Генерація звіту по будинку"""
        building = self.db.get_building_by_id(building_id)
        stats = self.db.get_building_detailed_stats(building_id)
       
        report = Report(
            scope="Building",
            period_start=datetime.now().strftime("%Y-%m-%d 00:00:00"),
            period_end=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            avg_power=stats['avg_power'],
            peak_power=stats['peak_power'],
            total_energy=stats['total_energy'],
            total_cost=stats['total_cost'],
            alerts_count=stats['alerts_count']
        )
       
        self.db.add_report(building_id, report)

    def building_has_critical_alert(self, building_id: int) -> bool:
        """Перевіряє, чи є в будинку активна серйозна аварія (High),
        щоб показати перехід в автономний режим (сонячні панелі)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
              AND al.severity = 'High'
              AND al.resolved = 0
        """, (building_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

   
    def show_reports(self):
        """Показати звіти"""
        self.clear_content()

        # Заголовок
        header = tk.Frame(self.content_frame, bg=Colors.BG)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="📄 Звіти по будинках",
            font=("Segoe UI", 18, "bold"),
            bg=Colors.BG,
            fg=Colors.TEXT
        ).pack(side=tk.LEFT)

        # Canvas зі скролом
        canvas = tk.Canvas(self.content_frame, bg=Colors.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Отримуємо всі будинки та їх звіти
        buildings = self.db.get_all_buildings()

        for building in buildings:
            report_card = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, borderwidth=2)
            report_card.pack(fill=tk.X, expand=True, pady=10, padx=5)

            # Заголовок звіту
            tk.Label(
                report_card,
                text=f"🏢 {building['address']}",
                font=("Segoe UI", 14, "bold"),
                bg="white",
                fg=Colors.TEXT
            ).pack(anchor=tk.W, padx=20, pady=(15, 5))

            # Статистика
            stats = self.db.get_building_detailed_stats(building['id'])

            stats_frame = tk.Frame(report_card, bg="white")
            stats_frame.pack(fill=tk.X, expand=True, padx=20, pady=10)

            # Метрики (без вартості)
            metrics = [
                ("⚡ Середня потужність", f"{stats['avg_power']:.2f} кВт", Colors.PRIMARY),
                ("📊 Пікова потужність", f"{stats['peak_power']:.2f} кВт", Colors.ACCENT),
                ("💡 Загальне споживання", f"{stats['total_energy']:.2f} кВт·год", Colors.SUCCESS),
            ]

            for i, (label, value, color) in enumerate(metrics):
                metric_frame = tk.Frame(stats_frame, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
                metric_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                stats_frame.columnconfigure(i, weight=1)

                tk.Label(
                    metric_frame,
                    text=value,
                    font=("Segoe UI", 16, "bold"),
                    bg="#F8F9FA",
                    fg=color
                ).pack(pady=(10, 0))

                tk.Label(
                    metric_frame,
                    text=label,
                    font=("Segoe UI", 8),
                    bg="#F8F9FA",
                    fg=Colors.TEXT_LIGHT
                ).pack(pady=(0, 10))

            # Аварії
            alerts_frame = tk.Frame(report_card, bg="white")
            alerts_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

            tk.Label(
                alerts_frame,
                text=(
                    f"🚨 Аварійні ситуації: {stats['alerts_count']} | "
                    f"✅ Вирішено: {stats['resolved_alerts']} | "
                    f"⚠️ Активно: {stats['active_alerts']}"
                ),
                font=("Segoe UI", 10),
                bg="white",
                fg=Colors.TEXT
            ).pack(anchor=tk.W)

            # Квартири з проблемами
            if stats['problem_apartments']:
                tk.Label(
                    report_card,
                    text="⚠️ Квартири з найбільшою кількістю аварій:",
                    font=("Segoe UI", 10, "bold"),
                    bg="white",
                    fg=Colors.DANGER
                ).pack(anchor=tk.W, padx=20, pady=(5, 10))

                for apt in stats['problem_apartments'][:5]:
                    tk.Label(
                        report_card,
                        text=f"   • Квартира {apt['number']}: {apt['alerts_count']} аварій",
                        font=("Segoe UI", 9),
                        bg="white",
                        fg=Colors.TEXT
                    ).pack(anchor=tk.W, padx=20, pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Прокрутка колесом миші
        self.bind_mousewheel(canvas)

   
    def load_data(self):
        """Завантаження початкових даних"""
        # Перевірка чи є дані в БД
        buildings = self.db.get_all_buildings()
        if not buildings:
            # Створення тестового будинку
            building = Building(
                address="вул. Солом'янська, 1",
                floors_count=25,
                sections_count=4,
                developer="Київміськбуд",
                city="Київ"
            )
            building_id = self.db.add_building(building)
           
            # Додаємо квартири
            for i in range(1, 21):  # 20 квартир для тесту
                apartment = Apartment(
                    building_id=building_id,
                    number=f"{i}",
                    floor=(i // 4) + 1,
                    area_sqm=50 + i * 2,
                    tariff_plan="Стандартний",
                    owner_name=f"Власник кв. {i}"
                )
                apt_id = self.db.add_apartment(apartment)
               
                meter = Meter(
                    apartment_id=apt_id,
                    meter_type="Smart",
                    serial_number=f"GM{building_id}{apt_id:04d}",
                    firmware_version="2.1.0"
                )
                self.db.add_meter(meter)
           
            self.add_system_message(
                f"Створено тестовий будинок з 20 квартирами",
                "info"
            )
   
    def bind_mousewheel(self, canvas):
        """Прив'язка прокрутки колесом миші до canvas"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
       
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartEnergySystem(root)
    root.mainloop()
