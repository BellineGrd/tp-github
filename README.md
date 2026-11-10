# CLI Task Tracker

## Project context

This project is a lightweight command-line task tracker for organizing everyday work. Tasks are stored in a local JSON file, so they persist between runs without a database or network connection.

## Objectives

- Provide a simple, reliable way to manage a personal task list.
- Keep task data locally and preserve it across application restarts.
- Use clear Python code, automated tests, and straightforward documentation.

## Features

- Add tasks with a non-empty description.
- List pending and completed tasks with their IDs.
- Mark tasks as completed or toggle their completion status.
- Delete a task by its ID.
- Save changes atomically to local JSON storage.
- Use either an interactive menu or direct command-line commands.

## Technology stack

- **Language:** Python 3.10+
- **Storage:** JSON file on the local filesystem
- **Dependencies:** Python standard library only
- **Version control:** Git; GitHub can be configured as a remote repository

## Requirements

- Python 3.10 or later

## Interactive usage

From this folder, start the interactive application:

```powershell
python main.py
```

Choose an option to add, list, complete, or delete tasks, or exit the application. Each task has a short ID printed when it is added.

By default, tasks are saved in `tasks.json` beside the application. To use a different file:

```powershell
python main.py --data-file .\data\tasks.json
```

## Direct command-line usage

The task manager also supports one-command operations:

```powershell
python task_manager.py add "Prepare the lab report"
python task_manager.py list
python task_manager.py complete <task-id>
python task_manager.py delete <task-id>
```

`toggle <task-id>` switches a task between pending and completed; `remove <task-id>` is also available as an alias for deletion.

The JSON file is created automatically and updated atomically to reduce the chance of losing data if a write is interrupted. Keep your task file backed up if you need to preserve your personal task list.

## Tests

Run the standard-library test suite from this folder:

```powershell
python -m unittest -v
```

## GitHub setup

To synchronize this project with GitHub, configure your Git author identity and add your repository URL as the `origin` remote, then commit the app files and push. The existing `TP_CN3_GitHub_2026.pdf` is local material and is excluded from Git; it is not modified or removed.
