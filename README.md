# DailyFlow – Personal Productivity Planner

**DailyFlow** is a clean, offline desktop planner built with Python and CustomTkinter. It brings your tasks, daily schedule, focus sessions and quick notes into one simple window, so you can see what needs doing, plan when to do it, and track your progress without needing an account or an internet connection.

> *Your plans. Your progress.*

---

## Features

### Dashboard
- Daily overview with today's date
- Live counts of total, pending and completed tasks
- Overall progress bar showing the percentage of tasks completed
- Quick view of your pending tasks (with due dates) and today's schedule

### My Tasks
- Add tasks with a **priority** (Low, Medium, High) and an optional **due date**
- Select a task to mark it complete (or undo it) or delete it
- Completed tasks stay visible so you can see what you've achieved

### Daily Planner
- Assign activities and appointments to a specific date and time
- Entries are automatically sorted chronologically
- Remove items you no longer need
- Today's entries show up on the Dashboard

### Focus Timer
- Built-in Pomodoro-style timer with a 25-minute focus mode and a 5-minute break mode
- Start, pause and reset controls
- Sound alert and pop-up message when a session ends

### Notes
- A free-form notepad for quick thoughts, reminders and ideas
- Saved with a single click

### Local, private storage
- All data is saved to a local `planner_data.json` file on your computer
- Automatically migrates data from older versions of the app (`study_data.json`)

---

## Requirements

- Python **3.10** or newer
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

## Installation

1. Clone or download this project:

   ```bash
   git clone https://github.com/leesimasiku05/dailyflow.git
   cd dailyflow
   ```

2. Install the dependency:

   ```bash
   python -m pip install customtkinter
   ```

3. Run the app:

   ```bash
   python dailyflow_planner.py
   ```

## Usage

| Page | What to do |
|------|------------|
| **Dashboard** | Check your progress and what's coming up today |
| **My Tasks** | Type a task, choose a priority, optionally enter a due date (`YYYY-MM-DD`), then click **Add task**. Click a task to select it, then use **Mark complete / undo** or **Delete selected** |
| **Daily Planner** | Enter an activity, a date (`YYYY-MM-DD`) and a time (`HH:MM`, 24-hour), then click **Add to plan** |
| **Focus Timer** | Choose *25 min focus* or *5 min break*, then press **Start** |
| **Notes** | Write anything you like and click **Save notes** |

## Data storage

DailyFlow stores everything in `planner_data.json`, created in the folder where you run the app. The structure looks like this:

```json
{
    "tasks": [
        {
            "id": "unique-id",
            "title": "Finish assignment",
            "priority": "High",
            "due_date": "2026-11-12",
            "completed": false
        }
    ],
    "schedule": [
        {
            "id": "unique-id",
            "title": "Study group",
            "date": "2026-11-09",
            "time": "14:00"
        }
    ],
    "notes": "Your notes here..."
}
```

To back up your data, copy this file. To start fresh, delete it.

## Project structure

```
dailyflow/
├── dailyflow_planner.py   # The whole application
├── planner_data.json      # Created automatically on first save
└── README.md
```

## Roadmap ideas

- Edit existing tasks and schedule items
- Date picker instead of typing dates
- Filter and sort tasks by priority or due date
- Custom timer lengths and a long-break option
- Dark mode toggle
- Reminders and notifications for upcoming items

## Contributing

Suggestions and pull requests are welcome. If you find a bug or have an idea, open an issue.
