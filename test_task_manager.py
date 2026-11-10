import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from main import run_interactive
from task_manager import Task, TaskManagerError, load_tasks, main, save_tasks


class TaskStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_file = Path(self.temporary_directory.name) / "nested" / "tasks.json"

    def test_missing_file_starts_with_an_empty_list(self) -> None:
        self.assertEqual(load_tasks(self.data_file), [])

    def test_tasks_are_saved_and_loaded_with_unicode(self) -> None:
        tasks = [Task("abcd1234", "Réviser les maths"), Task("done1234", "Submit report", True)]

        save_tasks(self.data_file, tasks)

        self.assertEqual(load_tasks(self.data_file), tasks)
        self.assertIn("Réviser les maths", self.data_file.read_text(encoding="utf-8"))

    def test_invalid_json_is_reported(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text("{", encoding="utf-8")

        with self.assertRaisesRegex(TaskManagerError, "not valid JSON"):
            load_tasks(self.data_file)

    def test_invalid_task_records_are_reported(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text(
            json.dumps({"version": 1, "tasks": [{"id": "", "description": "", "completed": 0}]}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TaskManagerError, "invalid fields"):
            load_tasks(self.data_file)


class TaskCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_file = Path(self.temporary_directory.name) / "tasks.json"

    def run_app(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(["--data-file", str(self.data_file), *arguments])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_add_list_toggle_and_remove(self) -> None:
        result, output, error = self.run_app("add", "Finish", "the", "exercise")
        self.assertEqual(result, 0)
        self.assertEqual(error, "")
        task_id = output.split()[2].rstrip(":")
        self.assertEqual(len(task_id), 8)

        result, output, _ = self.run_app("list")
        self.assertEqual(result, 0)
        self.assertIn(f"[pending] {task_id}  Finish the exercise", output)

        result, output, _ = self.run_app("toggle", task_id)
        self.assertEqual(result, 0)
        self.assertIn("now completed", output)
        self.assertTrue(load_tasks(self.data_file)[0].completed)

        result, output, _ = self.run_app("toggle", task_id)
        self.assertEqual(result, 0)
        self.assertIn("now pending", output)
        self.assertFalse(load_tasks(self.data_file)[0].completed)

        result, output, _ = self.run_app("remove", task_id)
        self.assertEqual(result, 0)
        self.assertIn("Removed task", output)
        self.assertEqual(load_tasks(self.data_file), [])

    def test_unknown_task_is_an_error_without_changing_the_file(self) -> None:
        self.run_app("add", "Keep this task")
        original_contents = self.data_file.read_text(encoding="utf-8")

        result, output, error = self.run_app("remove", "missing")

        self.assertEqual(result, 1)
        self.assertEqual(output, "")
        self.assertIn("No task found with ID missing", error)
        self.assertEqual(self.data_file.read_text(encoding="utf-8"), original_contents)

    def test_complete_and_delete_commands_persist(self) -> None:
        _, output, _ = self.run_app("add", "Complete this task")
        task_id = output.split()[2].rstrip(":")

        result, output, error = self.run_app("complete", task_id)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("now completed", output)
        self.assertTrue(load_tasks(self.data_file)[0].completed)

        result, output, error = self.run_app("delete", task_id)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Deleted task", output)
        self.assertEqual(load_tasks(self.data_file), [])

    def test_empty_list_is_clear(self) -> None:
        result, output, error = self.run_app("list")

        self.assertEqual(result, 0)
        self.assertEqual(output, "No tasks yet.\n")
        self.assertEqual(error, "")

    def test_interactive_add_list_complete_and_delete_persist(self) -> None:
        responses = iter(
            [
                "1",
                "Write documentation",
                "2",
                "3",
                lambda: load_tasks(self.data_file)[0].id,
                "2",
                "4",
                lambda: load_tasks(self.data_file)[0].id,
                "2",
                "5",
            ]
        )

        def answer(_prompt: str) -> str:
            response = next(responses)
            return response() if callable(response) else response

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            run_interactive(self.data_file, input_fn=answer)

        self.assertIn("[pending]", output.getvalue())
        self.assertIn("[completed]", output.getvalue())
        self.assertIn("Deleted task", output.getvalue())
        self.assertIn("No tasks yet.", output.getvalue())
        self.assertEqual(load_tasks(self.data_file), [])


if __name__ == "__main__":
    unittest.main()
