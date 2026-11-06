"""Запись пациентов на прием: настольное приложение для регистратуры."""

import re
from datetime import date, datetime
from tkinter import messagebox, ttk

import customtkinter as ctk
from tkcalendar import DateEntry

from database import Database


BG = "#F5F6F4"
PANEL = "#FFFFFF"
TEXT = "#263238"
MUTED = "#728078"
ACCENT = "#35776B"
LINE = "#DEE4E0"

ctk.set_appearance_mode("light")

MANAGERS = {
    "Пациенты": {
        "table": "patients",
        "columns": ["ID", "Фамилия", "Имя", "Отчество", "Дата рождения", "Телефон", "Адрес"],
        "fields": ["Фамилия", "Имя", "Отчество", "Дата рождения", "Телефон", "Адрес"],
        "select": "SELECT id,last_name,first_name,middle_name,birth_date,phone,address FROM patients ORDER BY last_name",
        "insert": "INSERT INTO patients(last_name,first_name,middle_name,birth_date,phone,address) VALUES(%s,%s,%s,%s,%s,%s)",
        "update": "UPDATE patients SET last_name=%s,first_name=%s,middle_name=%s,birth_date=%s,phone=%s,address=%s WHERE id=%s",
    },
    "Врачи": {
        "table": "doctors",
        "columns": ["ID", "Фамилия", "Имя", "Отчество", "Специализация ID", "Кабинет", "Телефон"],
        "fields": ["Фамилия", "Имя", "Отчество", "Специализация ID", "Кабинет", "Телефон"],
        "select": "SELECT id,last_name,first_name,middle_name,specialization_id,office,phone FROM doctors ORDER BY last_name",
        "insert": "INSERT INTO doctors(last_name,first_name,middle_name,specialization_id,office,phone) VALUES(%s,%s,%s,%s,%s,%s)",
        "update": "UPDATE doctors SET last_name=%s,first_name=%s,middle_name=%s,specialization_id=%s,office=%s,phone=%s WHERE id=%s",
    },
    "Специализации": {
        "table": "specializations",
        "columns": ["ID", "Название", "Описание"],
        "fields": ["Название", "Описание"],
        "select": "SELECT id,name,description FROM specializations ORDER BY name",
        "insert": "INSERT INTO specializations(name,description) VALUES(%s,%s)",
        "update": "UPDATE specializations SET name=%s,description=%s WHERE id=%s",
    },
}

APPOINTMENTS = """SELECT a.id,CONCAT(p.last_name,' ',p.first_name),
    CONCAT(d.last_name,' ',d.first_name),a.appointment_date,a.appointment_time,
    a.status,a.comment FROM appointments a
    JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id"""


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Запись пациентов на прием")
        self.geometry("1160x740")
        self.minsize(960, 620)
        self.configure(fg_color=BG)
        try:
            self.db = Database()
        except Exception as error:
            messagebox.showerror("MySQL", f"Не удалось подключиться к базе данных.\n{error}")
            self.destroy()
            return

        self.nav = {}
        self._build_navigation()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(side="left", fill="both", expand=True, padx=30, pady=22)
        self._style_table()
        self.page("Главная")
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build_navigation(self):
        side = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#293A3D")
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        ctk.CTkLabel(side, text="Регистратура", font=("Segoe UI", 19, "bold"),
                     text_color="white").pack(anchor="w", padx=20, pady=(26, 24))
        for name in ["Главная", "Запись на прием", "Расписание", "Пациенты",
                     "Врачи", "Специализации", "Отчеты"]:
            button = ctk.CTkButton(
                side, text=name, anchor="w", height=36, corner_radius=5,
                fg_color="transparent", hover_color="#3B5051",
                text_color="#E2E9E6", command=lambda page=name: self.page(page),
            )
            button.pack(fill="x", padx=10, pady=2)
            self.nav[name] = button

    def _style_table(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=34, background=PANEL,
                        fieldbackground=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#EDF1EE",
                        foreground=MUTED, relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#DCEBE5")],
                  foreground=[("selected", TEXT)])

    def close(self):
        self.db.close()
        self.destroy()

    def clear(self):
        for widget in self.body.winfo_children():
            widget.destroy()
        self.table_frame = None
        self.cancel_button = None

    def button(self, parent, text, command, primary=False):
        return ctk.CTkButton(
            parent, text=text, command=command, height=34, corner_radius=5,
            fg_color=ACCENT if primary else PANEL,
            hover_color="#2A6259" if primary else "#E9EFEB",
            text_color="white" if primary else TEXT,
            border_width=0 if primary else 1, border_color=LINE,
        )

    def page(self, name):
        self.clear()
        for label, button in self.nav.items():
            button.configure(fg_color=ACCENT if label == name else "transparent")
        head = ctk.CTkFrame(self.body, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(head, text="Обзор" if name == "Главная" else name,
                     font=("Segoe UI", 24, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(head, text=date.today().strftime("%d.%m.%Y"),
                     font=("Segoe UI", 10), text_color=MUTED).pack(side="right", pady=7)

        if name == "Главная":
            self.dashboard()
        elif name in MANAGERS:
            self.manage(name)
        elif name == "Запись на прием":
            self.new_appointment()
        elif name == "Расписание":
            self.schedule()
        elif name == "Отчеты":
            self.reports()

    def table(self, columns, rows):
        if self.table_frame and self.table_frame.winfo_exists():
            self.table_frame.destroy()
        frame = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=6,
                             border_width=1, border_color=LINE)
        frame.pack(fill="both", expand=True, pady=8)
        self.table_frame = frame
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=130, anchor="w")
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.pack(side="top", fill="both", expand=True, padx=(8, 0), pady=(8, 0))
        ybar.pack(side="right", fill="y", pady=(8, 0))
        xbar.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        for row in rows:
            tree.insert("", "end", values=row)
        return tree

    def dashboard(self):
        stats = self.db.dashboard()
        strip = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=6)
        strip.pack(fill="x", pady=(0, 18))
        for index, (label, value) in enumerate(zip(
            ["Пациенты", "Врачи", "Все записи", "Сегодня"], stats
        )):
            cell = ctk.CTkFrame(strip, fg_color="transparent")
            cell.pack(side="left", fill="x", expand=True, padx=18, pady=14)
            ctk.CTkLabel(cell, text=label, text_color=MUTED,
                         font=("Segoe UI", 10)).pack(anchor="w")
            ctk.CTkLabel(cell, text=str(value), text_color=TEXT,
                         font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(3, 0))
            if index < 3:
                ctk.CTkFrame(strip, width=1, height=42, fg_color=LINE).pack(side="left")
        title = ctk.CTkFrame(self.body, fg_color="transparent")
        title.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(title, text="Ближайшие приемы", font=("Segoe UI", 15, "bold"),
                     text_color=TEXT).pack(side="left")
        self.button(title, "Новая запись", lambda: self.page("Запись на прием"), True).pack(side="right")
        rows = self.db.rows(
            APPOINTMENTS + " WHERE a.appointment_date >= %s AND a.status='активна'"
            " ORDER BY a.appointment_date,a.appointment_time LIMIT 12",
            (date.today(),),
        )
        self.table(["ID", "Пациент", "Врач", "Дата", "Время", "Статус", "Комментарий"], rows)

    def manage(self, name):
        config = MANAGERS[name]
        search = None
        if name == "Пациенты":
            search_bar = ctk.CTkFrame(self.body, fg_color="transparent")
            search_bar.pack(fill="x", pady=(0, 8))
            search = ctk.CTkEntry(search_bar, placeholder_text="Поиск по ФИО или телефону",
                                  width=300, height=36, border_color=LINE)
            search.pack(side="left", padx=(0, 6))

        form = ctk.CTkFrame(self.body, fg_color="transparent")
        form.pack(fill="x", pady=(0, 8))
        entries = []
        for index, label in enumerate(config["fields"]):
            if name == "Пациенты" and index == 3:
                entry = DateEntry(form, width=13, date_pattern="dd.mm.yyyy",
                                  locale="ru_RU", maxdate=date.today())
            else:
                entry = ctk.CTkEntry(form, placeholder_text=label, width=145,
                                     height=36, border_color=LINE)
            entry.pack(side="left", padx=(0, 6))
            entries.append(entry)

        initial = self.db.rows(config["select"])
        tree = self.table(config["columns"], initial)

        def refresh(rows=None):
            rows = rows if rows is not None else self.db.rows(config["select"])
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", "end", values=row)

        if search:
            def find():
                term = f"%{search.get().strip()}%"
                refresh(self.db.rows(
                    "SELECT id,last_name,first_name,middle_name,birth_date,phone,address "
                    "FROM patients WHERE CONCAT_WS(' ',last_name,first_name,middle_name) "
                    "LIKE %s OR phone LIKE %s ORDER BY last_name", (term, term)
                ))
            self.button(search_bar, "Найти", find, True).pack(side="left")

        def read_values():
            values = [entry.get().strip() for entry in entries]
            if name == "Пациенты":
                values[3] = entries[3].get_date().isoformat()
                birth = date.fromisoformat(values[3])
                if birth > date.today():
                    raise ValueError("Дата рождения не может быть в будущем")
                if not re.fullmatch(r"\+?[0-9()\- ]{7,20}", values[4]):
                    raise ValueError("Проверьте формат телефона")
            if name == "Врачи" and not self.db.one(
                "SELECT id FROM specializations WHERE id=%s", (values[3],)
            ):
                raise ValueError("Не найдена специализация с таким ID")
            return values

        def selected_id():
            selected = tree.selection()
            return tree.item(selected[0])["values"][0] if selected else None

        def fill(_event=None):
            selected = tree.selection()
            if not selected:
                return
            for entry, value in zip(entries, tree.item(selected[0])["values"][1:]):
                if isinstance(entry, DateEntry):
                    entry.set_date(date.fromisoformat(str(value)[:10]))
                else:
                    entry.delete(0, "end")
                    entry.insert(0, str(value or ""))

        tree.bind("<<TreeviewSelect>>", fill)

        def save(update=False):
            try:
                values = read_values()
                if not all(values):
                    raise ValueError("Заполните обязательные поля")
                record_id = selected_id() if update else None
                if update and not record_id:
                    raise ValueError("Выберите запись в таблице")
                self.db.execute(config["update"] if update else config["insert"],
                                values + [record_id] if update else values)
                refresh()
            except Exception as error:
                messagebox.showerror("Проверка данных", str(error))

        def delete():
            record_id = selected_id()
            if record_id and messagebox.askyesno("Удаление", "Удалить выбранную запись?"):
                try:
                    self.db.execute(f"DELETE FROM {config['table']} WHERE id=%s", (record_id,))
                    refresh()
                except Exception as error:
                    messagebox.showerror("Удаление невозможно", str(error))

        actions = ctk.CTkFrame(self.body, fg_color="transparent")
        actions.pack(fill="x", pady=6)
        self.button(actions, "Добавить", lambda: save(), True).pack(side="left", padx=(0, 6))
        self.button(actions, "Изменить", lambda: save(True)).pack(side="left", padx=(0, 6))
        self.button(actions, "Удалить", delete).pack(side="left")
        self.button(actions, "Обновить", refresh).pack(side="right")

    def new_appointment(self):
        panel = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=6,
                             border_width=1, border_color=LINE)
        panel.pack(fill="x", pady=(0, 12))
        fields = [
            ("Пациент · ID", "Например, 12"),
            ("Специализация · ID", "Например, 3"),
            ("Врач · ID", "Например, 7"),
            ("Дата приема", None),
            ("Время · ЧЧ:ММ", "10:30"),
            ("Комментарий", "Необязательно"),
        ]
        inputs = []
        for index, (label, placeholder) in enumerate(fields):
            row, column = divmod(index, 3)
            cell = ctk.CTkFrame(panel, fg_color="transparent")
            cell.grid(row=row, column=column, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(cell, text=label, text_color=MUTED).pack(anchor="w", pady=(0, 4))
            if placeholder is None:
                entry = DateEntry(cell, width=18, date_pattern="dd.mm.yyyy",
                                  locale="ru_RU", mindate=date.today(), state="readonly")
            else:
                entry = ctk.CTkEntry(cell, placeholder_text=placeholder,
                                     height=36, border_color=LINE)
            entry.pack(fill="x")
            inputs.append(entry)
            panel.grid_columnconfigure(column, weight=1)
        patient, specialization, doctor, day, time, comment = inputs

        def create():
            try:
                selected_day = day.get_date()
                selected_time = datetime.strptime(time.get().strip(), "%H:%M").time()
                if datetime.combine(selected_day, selected_time) <= datetime.now():
                    raise ValueError("Нельзя записать на прошедшее время")
                if not self.db.one(
                    "SELECT id FROM doctors WHERE id=%s AND specialization_id=%s",
                    (doctor.get(), specialization.get()),
                ):
                    raise ValueError("Врач не найден в указанной специализации")
                with self.db.transaction() as cursor:
                    cursor.execute(
                        "SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s "
                        "AND appointment_time=%s AND status='активна' FOR UPDATE",
                        (doctor.get(), selected_day, selected_time),
                    )
                    if cursor.fetchone():
                        raise ValueError("Это время уже занято")
                    cursor.execute(
                        "INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,status,comment) "
                        "VALUES(%s,%s,%s,%s,'активна',%s)",
                        (patient.get(), doctor.get(), selected_day, selected_time, comment.get().strip()),
                    )
                messagebox.showinfo("Запись", "Прием добавлен")
                self.appointment_table()
            except Exception as error:
                messagebox.showerror("Не удалось записать", str(error))

        self.button(panel, "Создать запись", create, True).grid(
            row=2, column=2, sticky="e", padx=12, pady=(0, 12)
        )
        self.appointment_table()

    def appointment_table(self, sql=None, params=(), cancel=True):
        old = getattr(self, "cancel_button", None)
        if old and old.winfo_exists():
            old.destroy()
        query = sql or APPOINTMENTS + " ORDER BY a.appointment_date,a.appointment_time"
        tree = self.table(
            ["ID", "Пациент", "Врач", "Дата", "Время", "Статус", "Комментарий"],
            self.db.rows(query, params),
        )
        if not cancel:
            return tree

        def cancel_selected():
            selected = tree.selection()
            if not selected:
                return
            record_id = tree.item(selected[0])["values"][0]
            if messagebox.askyesno("Отмена записи", "Отменить прием? Он останется в истории."):
                self.db.execute(
                    "UPDATE appointments SET status='отменена' WHERE id=%s AND status='активна'",
                    (record_id,),
                )
                tree.delete(selected[0])

        self.cancel_button = self.button(self.body, "Отменить выбранную запись", cancel_selected)
        self.cancel_button.pack(anchor="w", pady=6)
        return tree

    def schedule(self):
        form = ctk.CTkFrame(self.body, fg_color="transparent")
        form.pack(fill="x", pady=(0, 6))
        doctor = ctk.CTkEntry(form, placeholder_text="ID врача", height=36, border_color=LINE)
        day = DateEntry(form, width=18, date_pattern="dd.mm.yyyy", locale="ru_RU")
        doctor.pack(side="left", padx=(0, 6))
        day.pack(side="left", padx=(0, 6))

        def show():
            try:
                self.appointment_table(
                    APPOINTMENTS + " WHERE a.doctor_id=%s AND a.appointment_date=%s ORDER BY a.appointment_time",
                    (doctor.get(), day.get_date().isoformat()),
                )
            except Exception as error:
                messagebox.showerror("Расписание", str(error))

        self.button(form, "Показать", show, True).pack(side="left")

    def reports(self):
        form = ctk.CTkFrame(self.body, fg_color="transparent")
        form.pack(fill="x", pady=(0, 6))
        start = DateEntry(form, width=18, date_pattern="dd.mm.yyyy", locale="ru_RU")
        end = DateEntry(form, width=18, date_pattern="dd.mm.yyyy", locale="ru_RU")
        start.set_date(date.today())
        end.set_date(date.today())
        start.pack(side="left", padx=(0, 6))
        end.pack(side="left", padx=(0, 6))

        def show():
            try:
                first, last = start.get_date(), end.get_date()
                if last < first:
                    raise ValueError("Конец периода раньше начала")
                for widget in self.body.winfo_children()[2:]:
                    widget.destroy()
                values = (first.isoformat(), last.isoformat())
                totals = self.db.one(
                    "SELECT COUNT(*),COALESCE(SUM(status='состоялась'),0),"
                    "COALESCE(SUM(status='отменена'),0),COALESCE(SUM(status='активна'),0) "
                    "FROM appointments WHERE appointment_date BETWEEN %s AND %s",
                    values,
                )
                ctk.CTkLabel(self.body, text=f"Всего: {totals[0]}   Состоялись: {totals[1]}   "
                             f"Отменены: {totals[2]}   Активны: {totals[3]}",
                             font=("Segoe UI", 14), text_color=TEXT).pack(anchor="w", pady=8)
                rows = self.db.rows(
                    "SELECT d.id,CONCAT(d.last_name,' ',d.first_name),COUNT(a.id),"
                    "COALESCE(SUM(a.status='состоялась'),0),COALESCE(SUM(a.status='отменена'),0) "
                    "FROM doctors d LEFT JOIN appointments a ON a.doctor_id=d.id "
                    "AND a.appointment_date BETWEEN %s AND %s GROUP BY d.id ORDER BY d.last_name",
                    values,
                )
                self.table(["ID врача", "Врач", "Всего", "Состоялись", "Отменены"], rows)
            except Exception as error:
                messagebox.showerror("Отчет", str(error))

        self.button(form, "Сформировать", show, True).pack(side="left")


if __name__ == "__main__":
    App().mainloop()
