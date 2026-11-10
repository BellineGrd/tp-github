"""A small command-line task manager with JSON file storage."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    id: str
    description: str
    completed: bool = False

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
        }


class TaskManagerError(Exception):
    """An expected task-manager or storage error."""


def load_tasks(path: Path) -> list[Task]:
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError) as exc:
        raise TaskManagerError(f"Could not read {path}: {exc}") from exc

    try:
        data = json.loads(contents)
    except json.JSONDecodeError as exc:
        raise TaskManagerError(f"Task file {path} is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or data.get("version") != 1:
        raise TaskManagerError(f"Task file {path} has an unsupported format.")

    records = data.get("tasks")
    if not isinstance(records, list):
        raise TaskManagerError(f"Task file {path} must contain a task list.")

    tasks: list[Task] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise TaskManagerError(f"Task {index} in {path} is not an object.")

        task_id = record.get("id")
        description = record.get("description")
        completed = record.get("completed")
        if (
            not isinstance(task_id, str)
            or not task_id
            or task_id in seen_ids
            or not isinstance(description, str)
            or not description.strip()
            or not isinstance(completed, bool)
        ):
            raise TaskManagerError(f"Task {index} in {path} has invalid fields.")

        seen_ids.add(task_id)
        tasks.append(Task(task_id, description, completed))

    return tasks


def save_tasks(path: Path, tasks: list[Task]) -> None:
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(
                {"version": 1, "tasks": [task.to_dict() for task in tasks]},
                temporary_file,
                ensure_ascii=False,
                indent=2,
            )
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise TaskManagerError(
                    f"Could not save {path}: {exc}; temporary file cleanup failed: "
                    f"{cleanup_error}"
                ) from exc
        raise TaskManagerError(f"Could not save {path}: {exc}") from exc


def add_task(tasks: list[Task], description: str) -> Task:
    description = description.strip()
    if not description:
        raise TaskManagerError("Task description cannot be empty.")

    existing_ids = {task.id for task in tasks}
    task_id = uuid.uuid4().hex[:8]
    while task_id in existing_ids:
        task_id = uuid.uuid4().hex[:8]

    task = Task(task_id, description)
    tasks.append(task)
    return task


def find_task(tasks: list[Task], task_id: str) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise TaskManagerError(f"No task found with ID {task_id}.")


def complete_task(tasks: list[Task], task_id: str) -> Task:
    task = find_task(tasks, task_id)
    task.completed = True
    return task


def delete_task(tasks: list[Task], task_id: str) -> Task:
    task = find_task(tasks, task_id)
    tasks.remove(task)
    return task


def list_tasks(tasks: list[Task]) -> None:
    if not tasks:
        print("No tasks yet.")
        return

    for task in tasks:
        status = "completed" if task.completed else "pending"
        print(f"[{status}] {task.id}  {task.description}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage tasks stored in a local JSON file.")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path(__file__).with_name("tasks.json"),
        help="path to the task data file (default: tasks.json beside this script)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add", help="add a new task")
    add_parser.add_argument("description", nargs="+", help="task description")

    commands.add_parser("list", help="list all pending and completed tasks")

    complete_parser = commands.add_parser("complete", help="mark a task as completed")
    complete_parser.add_argument("task_id", help="ID of the task to complete")

    delete_parser = commands.add_parser("delete", help="delete a task")
    delete_parser.add_argument("task_id", help="ID of the task to delete")

    toggle_parser = commands.add_parser("toggle", help="toggle a task's completion status")
    toggle_parser.add_argument("task_id", help="ID of the task to toggle")

    remove_parser = commands.add_parser("remove", help="remove a task")
    remove_parser.add_argument("task_id", help="ID of the task to remove")
    return parser


def run_command(
    command: str,
    args: argparse.Namespace,
    data_file: Path,
) -> None:
    tasks = load_tasks(data_file)

    if command == "add":
        task = add_task(tasks, " ".join(args.description))
        save_tasks(data_file, tasks)
        print(f"Added task {task.id}: {task.description}")
    elif command == "list":
        list_tasks(tasks)
    elif command == "complete":
        task = complete_task(tasks, args.task_id)
        save_tasks(data_file, tasks)
        print(f"Task {task.id} is now completed.")
    elif command == "delete":
        task = delete_task(tasks, args.task_id)
        save_tasks(data_file, tasks)
        print(f"Deleted task {task.id}.")
    elif command == "toggle":
        task = find_task(tasks, args.task_id)
        task.completed = not task.completed
        save_tasks(data_file, tasks)
        status = "completed" if task.completed else "pending"
        print(f"Task {task.id} is now {status}.")
    elif command == "remove":
        task = delete_task(tasks, args.task_id)
        save_tasks(data_file, tasks)
        print(f"Removed task {task.id}.")
    else:
        raise TaskManagerError(f"Unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_command(args.command, args, args.data_file)
    except TaskManagerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
