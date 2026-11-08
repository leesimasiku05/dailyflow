import customtkinter as ctk
import json
import os
import uuid
from datetime import date, datetime, timedelta

# ============================================================
# PERSONAL PRODUCTIVITY PLANNER
# Requirements: Python 3.10+ and customtkinter
# Install: python -m pip install customtkinter
# ============================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_TITLE = "DailyFlow - Personal Productivity Planner"
DATA_FILE = "planner_data.json"

COLORS = {
    "sidebar": "#17243A",
    "sidebar_hover": "#263954",
    "background": "#F4F6FA",
    "card": "#FFFFFF",
    "text": "#1F2937",
    "muted": "#718096",
    "blue": "#3978E8",
    "green": "#239B72",
    "red": "#D9534F",
    "border": "#E5EAF1",
}


def make_id():
    return str(uuid.uuid4())


def load_data():
    """Load planner data and migrate the old Study Assistant format."""
    default = {"tasks": [], "schedule": [], "notes": ""}

    if not os.path.exists(DATA_FILE):
        # Also migrate the original filename if it exists.
        old_file = "study_data.json"
        if os.path.exists(old_file):
            try:
                with open(old_file, "r", encoding="utf-8") as file:
                    old = json.load(file)
                tasks = []
                for title in old.get("tasks", []):
                    tasks.append({
                        "id": make_id(), "title": str(title),
                        "priority": "Medium", "due_date": "",
                        "completed": False
                    })
                for title in old.get("completed", []):
                    tasks.append({
                        "id": make_id(), "title": str(title),
                        "priority": "Medium", "due_date": "",
                        "completed": True
                    })
                default["tasks"] = tasks
            except (json.JSONDecodeError, OSError, TypeError):
                pass
        return default

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        if not isinstance(loaded, dict):
            return default

        # Convert older task strings into structured task records.
        converted = []
        for item in loaded.get("tasks", []):
            if isinstance(item, str):
                converted.append({
                    "id": make_id(), "title": item,
                    "priority": "Medium", "due_date": "",
                    "completed": False
                })
            elif isinstance(item, dict):
                item.setdefault("id", make_id())
                item.setdefault("title", "Untitled task")
                item.setdefault("priority", "Medium")
                item.setdefault("due_date", "")
                item.setdefault("completed", False)
                converted.append(item)

        # Support the original separate completed list if present.
        for item in loaded.get("completed", []):
            if isinstance(item, str):
                converted.append({
                    "id": make_id(), "title": item,
                    "priority": "Medium", "due_date": "",
                    "completed": True
                })

        return {
            "tasks": converted,
            "schedule": loaded.get("schedule", []),
            "notes": loaded.get("notes", "")
        }
    except (json.JSONDecodeError, OSError, TypeError):
        return default


data = load_data()


def save_data():
    """Save all planner information locally as JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


class PlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(950, 650)
        self.configure(fg_color=COLORS["background"])

        self.selected_task_id = None
        self.timer_running = False
        self.timer_after_id = None
        self.remaining_seconds = 25 * 60
        self.timer_mode = "Focus"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=22)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------------- GENERAL UI ----------------------

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="DailyFlow", text_color="white",
            font=ctk.CTkFont(size=25, weight="bold")
        ).pack(anchor="w", padx=24, pady=(30, 4))

        ctk.CTkLabel(
            sidebar, text="PERSONAL PRODUCTIVITY",
            text_color="#AAB8CC", font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="w", padx=25, pady=(0, 35))

        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("My Tasks", self.show_tasks),
            ("Daily Planner", self.show_schedule),
            ("Focus Timer", self.show_timer),
            ("Notes", self.show_notes),
        ]

        for label, command in nav_items:
            ctk.CTkButton(
                sidebar, text=label, command=command, anchor="w",
                height=43, corner_radius=9,
                fg_color="transparent", hover_color=COLORS["sidebar_hover"],
                text_color="#F3F6FA",
                font=ctk.CTkFont(size=14)
            ).pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(
            sidebar, text="Your plans. Your progress.",
            text_color="#AAB8CC", font=ctk.CTkFont(size=11)
        ).pack(side="bottom", pady=22)

    def clear_content(self):
        # Stop any pending timer callback when leaving the timer page.
        for widget in self.content.winfo_children():
            widget.destroy()

    def page_heading(self, title, subtitle):
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ctk.CTkLabel(
            header, text=title, text_color=COLORS["text"],
            font=ctk.CTkFont(size=27, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text=subtitle, text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", pady=(3, 0))

    def card(self, parent, **kwargs):
        return ctk.CTkFrame(
            parent, fg_color=COLORS["card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"], **kwargs
        )

    def refresh_current_page(self):
        # Refresh the visible page after data changes.
        if getattr(self, "current_page", "") == "Dashboard":
            self.show_dashboard()
        elif getattr(self, "current_page", "") == "My Tasks":
            self.show_tasks()
        elif getattr(self, "current_page", "") == "Daily Planner":
            self.show_schedule()

    # ---------------------- DASHBOARD ----------------------

    def show_dashboard(self):
        self.current_page = "Dashboard"
        self.clear_content()
        self.page_heading("Dashboard", f"Here is your overview for {date.today().strftime('%A, %d %B %Y')}.")

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1, 2), weight=1)

        total = len(data["tasks"])
        completed = sum(1 for task in data["tasks"] if task.get("completed"))
        pending = total - completed
        percent = int(completed / total * 100) if total else 0

        stats = [
            ("Total tasks", total, COLORS["blue"]),
            ("Still to do", pending, "#D28A28"),
            ("Completed", completed, COLORS["green"]),
        ]
        for column, (label, value, accent) in enumerate(stats):
            box = self.card(body, height=115)
            box.grid(row=0, column=column, sticky="ew", padx=7, pady=(0, 15))
            box.grid_propagate(False)
            ctk.CTkLabel(box, text=label, text_color=COLORS["muted"],
                         font=ctk.CTkFont(size=13)).pack(anchor="w", padx=18, pady=(17, 2))
            ctk.CTkLabel(box, text=str(value), text_color=accent,
                         font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w", padx=18)

        progress = self.card(body)
        progress.grid(row=1, column=0, columnspan=3, sticky="ew", padx=7, pady=5)
        ctk.CTkLabel(progress, text="Overall progress",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(17, 8))
        ctk.CTkProgressBar(progress, progress_color=COLORS["green"]).pack(
            fill="x", padx=20, pady=(0, 7)
        )
        bar = progress.winfo_children()[-1]
        bar.set(percent / 100)
        ctk.CTkLabel(progress, text=f"{percent}% of your tasks completed",
                     text_color=COLORS["muted"]).pack(anchor="w", padx=20, pady=(0, 17))

        lower = ctk.CTkFrame(body, fg_color="transparent")
        lower.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        lower.grid_columnconfigure((0, 1), weight=1)

        tasks_box = self.card(lower)
        tasks_box.grid(row=0, column=0, sticky="nsew", padx=7)
        ctk.CTkLabel(tasks_box, text="Pending tasks",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=15)

        pending_tasks = [t for t in data["tasks"] if not t.get("completed")]
        if not pending_tasks:
            ctk.CTkLabel(tasks_box, text="You're all caught up. Add a task to get started!",
                         text_color=COLORS["muted"], wraplength=350).pack(anchor="w", padx=18, pady=8)
        else:
            for task in pending_tasks[:6]:
                due = f"  •  Due {task['due_date']}" if task.get("due_date") else ""
                ctk.CTkLabel(
                    tasks_box, text=f"•  {task['title']}{due}",
                    text_color=COLORS["text"], anchor="w", wraplength=390
                ).pack(fill="x", padx=18, pady=5)

        schedule_box = self.card(lower)
        schedule_box.grid(row=0, column=1, sticky="nsew", padx=7)
        ctk.CTkLabel(schedule_box, text="Today's plan",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=15)
        todays_items = [x for x in data["schedule"] if x.get("date") == date.today().isoformat()]
        todays_items.sort(key=lambda x: x.get("time", ""))
        if not todays_items:
            ctk.CTkLabel(schedule_box, text="Nothing scheduled for today yet.",
                         text_color=COLORS["muted"]).pack(anchor="w", padx=18, pady=8)
        else:
            for item in todays_items[:6]:
                ctk.CTkLabel(
                    schedule_box, text=f"{item.get('time', '')}   {item.get('title', '')}",
                    text_color=COLORS["text"], anchor="w", wraplength=390
                ).pack(fill="x", padx=18, pady=5)

    # ---------------------- TASK MANAGEMENT ----------------------

    def show_tasks(self):
        self.current_page = "My Tasks"
        self.clear_content()
        self.page_heading("My Tasks", "Create tasks, set priorities and due dates, and track what you finish.")

        controls = self.card(self.content)
        controls.grid(row=1, column=0, sticky="new", pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)

        self.task_title_entry = ctk.CTkEntry(
            controls, placeholder_text="What do you need to get done?", height=40
        )
        self.task_title_entry.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="ew")

        self.priority_menu = ctk.CTkOptionMenu(
            controls, values=["Low", "Medium", "High"], width=115
        )
        self.priority_menu.set("Medium")
        self.priority_menu.grid(row=0, column=1, padx=8, pady=15)

        self.due_entry = ctk.CTkEntry(controls, placeholder_text="Due date YYYY-MM-DD", width=175)
        self.due_entry.grid(row=0, column=2, padx=8, pady=15)

        ctk.CTkButton(controls, text="Add task", width=105,
                      command=self.add_task).grid(row=0, column=3, padx=(8, 15), pady=15)

        action_row = ctk.CTkFrame(self.content, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(action_row, text="Mark complete / undo", command=self.toggle_task).pack(side="left", padx=(0, 8))
        ctk.CTkButton(action_row, text="Delete selected", fg_color=COLORS["red"],
                      hover_color="#B94440", command=self.delete_task).pack(side="left")

        self.task_rows = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", label_text="Select a task below"
        )
        self.task_rows.grid(row=3, column=0, sticky="nsew")
        self.content.grid_rowconfigure(3, weight=1)
        self.populate_tasks()

    def populate_tasks(self):
        for widget in self.task_rows.winfo_children():
            widget.destroy()

        if not data["tasks"]:
            ctk.CTkLabel(self.task_rows, text="No tasks yet. Add your first task above.",
                         text_color=COLORS["muted"]).pack(pady=25)
            return

        for task in data["tasks"]:
            selected = task["id"] == self.selected_task_id
            row = ctk.CTkFrame(
                self.task_rows, fg_color="#EAF1FF" if selected else COLORS["card"],
                corner_radius=10, border_width=1, border_color=COLORS["border"]
            )
            row.pack(fill="x", padx=3, pady=5)

            status = "✓" if task.get("completed") else "○"
            title = task.get("title", "Untitled task")
            if task.get("completed"):
                title = f"{title}  (completed)"

            details = f"Priority: {task.get('priority', 'Medium')}"
            if task.get("due_date"):
                details += f"     Due: {task['due_date']}"

            button = ctk.CTkButton(
                row, text=f"{status}   {title}\n{details}",
                anchor="w", height=65, fg_color="transparent",
                hover_color="#DCE7FA", text_color=COLORS["text"],
                command=lambda task_id=task["id"]: self.select_task(task_id)
            )
            button.pack(fill="x", padx=6, pady=4)

    def select_task(self, task_id):
        self.selected_task_id = task_id
        self.populate_tasks()

    def add_task(self):
        title = self.task_title_entry.get().strip()
        due = self.due_entry.get().strip()

        if not title:
            self.show_message("Please enter a task title.")
            return

        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                self.show_message("Use the date format YYYY-MM-DD, for example 2026-11-08.")
                return

        data["tasks"].append({
            "id": make_id(),
            "title": title,
            "priority": self.priority_menu.get(),
            "due_date": due,
            "completed": False
        })
        save_data()
        self.task_title_entry.delete(0, "end")
        self.due_entry.delete(0, "end")
        self.populate_tasks()

    def get_selected_task(self):
        for task in data["tasks"]:
            if task["id"] == self.selected_task_id:
                return task
        return None

    def toggle_task(self):
        task = self.get_selected_task()
        if not task:
            self.show_message("Select a task first.")
            return
        task["completed"] = not task.get("completed", False)
        save_data()
        self.populate_tasks()

    def delete_task(self):
        task = self.get_selected_task()
        if not task:
            self.show_message("Select a task first.")
            return
        data["tasks"] = [t for t in data["tasks"] if t["id"] != self.selected_task_id]
        self.selected_task_id = None
        save_data()
        self.populate_tasks()

    # ---------------------- DAILY PLANNER ----------------------

    def show_schedule(self):
        self.current_page = "Daily Planner"
        self.clear_content()
        self.page_heading("Daily Planner", "Give your day structure by assigning activities to dates and times.")

        form = self.card(self.content)
        form.grid(row=1, column=0, sticky="new", pady=(0, 15))
        form.grid_columnconfigure(0, weight=1)

        self.activity_entry = ctk.CTkEntry(form, placeholder_text="Activity or appointment")
        self.activity_entry.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="ew")
        self.schedule_date_entry = ctk.CTkEntry(form, width=145, placeholder_text="YYYY-MM-DD")
        self.schedule_date_entry.insert(0, date.today().isoformat())
        self.schedule_date_entry.grid(row=0, column=1, padx=8, pady=15)
        self.schedule_time_entry = ctk.CTkEntry(form, width=100, placeholder_text="HH:MM")
        self.schedule_time_entry.grid(row=0, column=2, padx=8, pady=15)
        ctk.CTkButton(form, text="Add to plan", command=self.add_schedule_item).grid(
            row=0, column=3, padx=(8, 15), pady=15
        )

        self.schedule_rows = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        self.schedule_rows.grid(row=2, column=0, sticky="nsew")
        self.content.grid_rowconfigure(2, weight=1)
        self.populate_schedule()

    def add_schedule_item(self):
        title = self.activity_entry.get().strip()
        day = self.schedule_date_entry.get().strip()
        time = self.schedule_time_entry.get().strip()

        if not title:
            self.show_message("Enter an activity first.")
            return
        try:
            datetime.strptime(day, "%Y-%m-%d")
            datetime.strptime(time, "%H:%M")
        except ValueError:
            self.show_message("Enter a valid date (YYYY-MM-DD) and time (HH:MM).")
            return

        data["schedule"].append({
            "id": make_id(), "title": title, "date": day, "time": time
        })
        save_data()
        self.activity_entry.delete(0, "end")
        self.schedule_time_entry.delete(0, "end")
        self.populate_schedule()

    def populate_schedule(self):
        for widget in self.schedule_rows.winfo_children():
            widget.destroy()

        items = sorted(data["schedule"], key=lambda x: (x.get("date", ""), x.get("time", "")))
        if not items:
            ctk.CTkLabel(self.schedule_rows, text="Your planner is empty.",
                         text_color=COLORS["muted"]).pack(pady=25)
            return

        for item in items:
            row = self.card(self.schedule_rows)
            row.pack(fill="x", padx=3, pady=5)
            label = f"{item.get('date', '')}   {item.get('time', '')}     {item.get('title', '')}"
            ctk.CTkLabel(row, text=label, text_color=COLORS["text"],
                         anchor="w").pack(side="left", fill="x", expand=True, padx=15, pady=15)
            ctk.CTkButton(
                row, text="Remove", width=80, fg_color=COLORS["red"],
                hover_color="#B94440",
                command=lambda item_id=item["id"]: self.delete_schedule_item(item_id)
            ).pack(side="right", padx=10)

    def delete_schedule_item(self, item_id):
        data["schedule"] = [x for x in data["schedule"] if x.get("id") != item_id]
        save_data()
        self.populate_schedule()

    # ---------------------- POMODORO TIMER ----------------------

    def show_timer(self):
        self.current_page = "Focus Timer"
        self.clear_content()
        self.page_heading("Focus Timer", "Work in focused sessions, then take a short break.")

        panel = self.card(self.content)
        panel.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panel, text="POMODORO SESSION",
                     text_color=COLORS["muted"],
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=(45, 8))

        self.timer_label = ctk.CTkLabel(
            panel, text=self.format_time(self.remaining_seconds),
            font=ctk.CTkFont(size=70, weight="bold"), text_color=COLORS["text"]
        )
        self.timer_label.grid(row=1, column=0, pady=10)

        self.timer_mode_label = ctk.CTkLabel(
            panel, text=self.timer_mode, text_color=COLORS["blue"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.timer_mode_label.grid(row=2, column=0, pady=5)

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=3, column=0, pady=20)
        ctk.CTkButton(buttons, text="Start", width=110, command=self.start_timer).pack(side="left", padx=6)
        ctk.CTkButton(buttons, text="Pause", width=110, command=self.pause_timer).pack(side="left", padx=6)
        ctk.CTkButton(buttons, text="Reset", width=110, command=self.reset_timer).pack(side="left", padx=6)

        modes = ctk.CTkFrame(panel, fg_color="transparent")
        modes.grid(row=4, column=0, pady=(5, 40))
        ctk.CTkButton(modes, text="25 min focus", command=lambda: self.set_timer(25, "Focus")).pack(side="left", padx=6)
        ctk.CTkButton(modes, text="5 min break", command=lambda: self.set_timer(5, "Break")).pack(side="left", padx=6)

    @staticmethod
    def format_time(seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_timer(self, minutes, mode):
        self.pause_timer()
        self.timer_mode = mode
        self.remaining_seconds = minutes * 60
        self.update_timer_display()

    def update_timer_display(self):
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            self.timer_label.configure(text=self.format_time(self.remaining_seconds))
            self.timer_mode_label.configure(text=self.timer_mode)

    def start_timer(self):
        if self.timer_running:
            return
        self.timer_running = True
        self.tick_timer()

    def tick_timer(self):
        if not self.timer_running:
            return
        if self.remaining_seconds <= 0:
            self.timer_running = False
            self.timer_after_id = None
            self.bell()
            self.show_message(f"{self.timer_mode} session finished!")
            return
        self.remaining_seconds -= 1
        self.update_timer_display()
        self.timer_after_id = self.after(1000, self.tick_timer)

    def pause_timer(self):
        self.timer_running = False
        if self.timer_after_id is not None:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

    def reset_timer(self):
        self.pause_timer()
        self.remaining_seconds = 25 * 60 if self.timer_mode == "Focus" else 5 * 60
        self.update_timer_display()

    # ---------------------- NOTES ----------------------

    def show_notes(self):
        self.current_page = "Notes"
        self.clear_content()
        self.page_heading("Notes", "A space for quick thoughts, reminders and ideas.")

        notes_card = self.card(self.content)
        notes_card.grid(row=1, column=0, sticky="nsew")
        notes_card.grid_rowconfigure(0, weight=1)
        notes_card.grid_columnconfigure(0, weight=1)

        self.notes_text = ctk.CTkTextbox(
            notes_card, font=ctk.CTkFont(size=14),
            corner_radius=10, border_width=0
        )
        self.notes_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.notes_text.insert("1.0", data.get("notes", ""))

        ctk.CTkButton(notes_card, text="Save notes", command=self.save_notes).grid(
            row=1, column=0, sticky="e", padx=15, pady=(0, 15)
        )

    def save_notes(self):
        data["notes"] = self.notes_text.get("1.0", "end-1c")
        save_data()
        self.show_message("Your notes have been saved.")

    # ---------------------- UTILITIES ----------------------

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("DailyFlow")
        dialog.geometry("360x150")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, wraplength=300,
                     text_color=COLORS["text"]).pack(padx=20, pady=25)
        ctk.CTkButton(dialog, text="OK", width=90, command=dialog.destroy).pack(pady=5)

    def on_close(self):
        self.pause_timer()
        save_data()
        self.destroy()


if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()
