"""Interactive command-line interface for the task manager."""

import argparse
import sys
from pathlib import Path
from typing import Callable

from task_manager import (
    TaskManagerError,
    add_task,
    complete_task,
    delete_task,
    list_tasks,
    load_tasks,
    save_tasks,
)


def run_interactive(
    data_file: Path,
    input_fn: Callable[[str], str] = input,
) -> None:
    print("Task Manager")

    while True:
        print("\n1. Add task\n2. List tasks\n3. Complete task\n4. Delete task\n5. Exit")
        try:
            choice = input_fn("Choose an option (1-5): ").strip()
        except EOFError:
            print("\nGoodbye!")
            return

        if choice == "5":
            print("Goodbye!")
            return

        try:
            tasks = load_tasks(data_file)
            if choice == "1":
                description = input_fn("Task description: ")
                task = add_task(tasks, description)
                save_tasks(data_file, tasks)
                print(f"Added task {task.id}: {task.description}")
            elif choice == "2":
                list_tasks(tasks)
            elif choice == "3":
                task_id = input_fn("Task ID to complete: ").strip()
                task = complete_task(tasks, task_id)
                save_tasks(data_file, tasks)
                print(f"Task {task.id} is now completed.")
            elif choice == "4":
                task_id = input_fn("Task ID to delete: ").strip()
                task = delete_task(tasks, task_id)
                save_tasks(data_file, tasks)
                print(f"Deleted task {task.id}.")
            else:
                print("Invalid option. Choose a number from 1 to 5.")
        except TaskManagerError as exc:
            print(f"Error: {exc}", file=sys.stderr)
        except EOFError:
            print("\nGoodbye!")
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interactively manage locally stored tasks.")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path(__file__).with_name("tasks.json"),
        help="path to the task data file (default: tasks.json beside this script)",
    )
    args = parser.parse_args(argv)
    try:
        run_interactive(args.data_file)
    except KeyboardInterrupt:
        print("\nGoodbye!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
