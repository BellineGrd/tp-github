from __future__ import annotations

import uuid

from dataclasses import dataclass

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
