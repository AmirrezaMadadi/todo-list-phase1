import unittest
import os
from datetime import date, timedelta

# تنظیم محدودیت‌ها برای پروژه و تسک
os.environ["MAX_NUMBER_OF_PROJECT"] = "3"
os.environ["MAX_NUMBER_OF_TASK"] = "10"

from todolist.manager import ToDoListManager
from todolist.models import task_id_generator, project_id_generator


class TestToDoListManager(unittest.TestCase):
    """تست‌های واحد برای ToDoListManager"""

    def setUp(self):
        """راه‌اندازی اولیه قبل از اجرای هر تست."""
        # بازنشانی شمارنده‌های ID تا هر تست مستقل باشد
        task_id_generator.current_id = 0
        project_id_generator.current_id = 0

        # نمونه‌ی اصلی برای تست‌ها
        self.manager = ToDoListManager()
        self.project_name = "Project Alpha"
        self.task_title = "Buy groceries"
        self.due_date = date.today() + timedelta(days=7)
        self.long_title = " ".join([f"Word{i}" for i in range(31)])

        # افزودن پروژه‌ی پیش‌فرض (ID = 1)
        ok, msg = self.manager.add_project(self.project_name, "A test project.")
        self.assertTrue(ok, f"Setup failed: {msg}")
        self.project_id = self.manager.projects[0].id

        # افزودن تسک پیش‌فرض (ID = 1)
        ok, msg = self.manager.add_task(self.project_id, self.task_title, due_date=self.due_date)
        self.assertTrue(ok, f"Setup failed: {msg}")
        self.task_id = self.manager.projects[0].tasks[0].id

    # ======================== Project Tests ========================

    def test_add_and_list_project(self):
        """بررسی افزودن و لیست کردن پروژه‌ها"""
        success, msg = self.manager.add_project("Project Beta", "Another test project.")
        self.assertTrue(success, msg)
        self.assertEqual(len(self.manager.projects), 2)

        result = self.manager.list_projects()
        self.assertEqual(len(result), 2)
        self.assertIn("Project Beta", [p['name'] for p in result])

    def test_add_project_max_limit(self):
        """بررسی محدودیت حداکثر پروژه‌ها"""
        self.manager.add_project("P2")
        self.manager.add_project("P3")

        success, msg = self.manager.add_project("P4")
        self.assertFalse(success)
        self.assertIn("خطا: سقف تعداد پروژه (3) رسیده است.", msg)
        self.assertEqual(len(self.manager.projects), 3)

    def test_add_project_duplicate_name(self):
        """بررسی جلوگیری از نام تکراری پروژه"""
        success, msg = self.manager.add_project(self.project_name, "Duplicate test.")
        self.assertFalse(success)
        self.assertIn("خطا: پروژه‌ای با نام 'Project Alpha' از قبل موجود است.", msg)

    def test_add_project_word_limit_validation(self):
        """بررسی محدودیت تعداد کلمات در نام و توضیحات پروژه"""
        too_long_name = self.long_title
        ok, msg = self.manager.add_project(too_long_name, "Valid description.")
        self.assertFalse(ok)
        self.assertIn("Project name exceeds the 30-word limit.", msg)

        long_desc = " ".join([f"word{i}" for i in range(151)])
        ok, msg = self.manager.add_project("Project Long Desc", long_desc)
        self.assertFalse(ok)
        self.assertIn("Project description exceeds the 150-word limit.", msg)

    def test_remove_project(self):
        """بررسی حذف پروژه"""
        self.manager.add_project("Project To Remove")
        remove_id = next(p.id for p in self.manager.projects if p.name == "Project To Remove")

        ok, msg = self.manager.remove_project(remove_id)
        self.assertTrue(ok, msg)
        self.assertNotIn("Project To Remove", [p.name for p in self.manager.projects])
        self.assertEqual(len(self.manager.projects), 1)

        # پروژه‌ی ناموجود
        ok, msg = self.manager.remove_project(999)
        self.assertFalse(ok)
        self.assertIn("خطا: پروژه‌ای با شناسه 999 یافت نشد.", msg)

    def test_remove_project_updates_total_task_count(self):
        """بررسی به‌روزرسانی شمارنده‌ی کل تسک‌ها هنگام حذف پروژه"""
        self.manager.add_project("Temp Project", "Holds tasks.")
        pid = self.manager.projects[-1].id
        self.manager.add_task(pid, "Task 1")
        self.manager.add_task(pid, "Task 2")

        self.assertEqual(self.manager.total_tasks_count, 3)

        ok, msg = self.manager.remove_project(pid)
        self.assertTrue(ok)
        self.assertEqual(self.manager.total_tasks_count, 1)

    # ======================== Task Tests ========================

    def test_add_and_remove_task(self):
        """بررسی افزودن و حذف تسک"""
        self.assertEqual(len(self.manager.projects[0].tasks), 1)

        ok, msg = self.manager.add_task(self.project_id, "Take out the trash")
        self.assertTrue(ok, msg)
        self.assertEqual(self.manager.total_tasks_count, 2)

        ok, msg = self.manager.remove_task(self.project_id, self.task_id)
        self.assertTrue(ok, msg)
        self.assertEqual(self.manager.total_tasks_count, 1)

        ok, msg = self.manager.remove_task(self.project_id, 999)
        self.assertFalse(ok)
        self.assertIn("خطا: تسکی با شناسه 999 در پروژه 'Project Alpha' یافت نشد.", msg)

    def test_add_task_max_limit(self):
        """بررسی محدودیت تعداد کل تسک‌ها"""
        for i in range(2, self.manager.MAX_TASKS + 1):
            self.manager.add_task(self.project_id, f"Task {i}")

        self.assertEqual(self.manager.total_tasks_count, self.manager.MAX_TASKS)
        ok, msg = self.manager.add_task(self.project_id, "Extra Task")
        self.assertFalse(ok)
        self.assertIn("خطا: سقف کل تسک‌ها (10) رسیده است.", msg)

    def test_toggle_task_completion(self):
        """بررسی تغییر وضعیت تکمیل تسک"""
        task = self.manager.projects[0].tasks[0]
        self.assertFalse(task.is_completed)

        ok, msg = self.manager.toggle_task_completion(self.project_id, self.task_id)
        self.assertTrue(ok, msg)
        self.assertTrue(task.is_completed)

        ok, msg = self.manager.toggle_task_completion(self.project_id, self.task_id)
        self.assertTrue(ok, msg)
        self.assertFalse(task.is_completed)

        ok, msg = self.manager.toggle_task_completion(self.project_id, 999)
        self.assertFalse(ok)
        self.assertIn("خطا: تسکی با شناسه 999 در پروژه 'Project Alpha' یافت نشد.", msg)

    def test_edit_task(self):
        """بررسی ویرایش عنوان، توضیحات و تاریخ تسک"""
        new_title = "New Task Title"
        new_desc = "Updated description."
        new_due = date.today() + timedelta(days=10)

        ok, msg = self.manager.edit_task(
            self.project_id, self.task_id,
            new_title=new_title,
            new_description=new_desc,
            new_due_date=new_due
        )
        self.assertTrue(ok, msg)

        t = self.manager.projects[0].tasks[0]
        self.assertEqual((t.title, t.description, t.due_date),
                         (new_title, new_desc, new_due))
        self.assertIn("عنوان, توضیحات, تاریخ سررسید", msg)

        ok, msg = self.manager.edit_task(self.project_id, 999, new_title="Test")
        self.assertFalse(ok)
        self.assertIn("خطا: تسکی با شناسه 999 در پروژه 'Project Alpha' یافت نشد.", msg)

    def test_edit_task_word_limit_validation(self):
        """بررسی محدودیت تعداد کلمات هنگام ویرایش تسک"""
        ok, msg = self.manager.edit_task(self.project_id, self.task_id, new_title=self.long_title)
        self.assertFalse(ok)
        self.assertIn("Task title exceeds the 30-word limit.", msg)

        too_long_desc = " ".join([f"word{i}" for i in range(151)])
        ok, msg = self.manager.edit_task(self.project_id, self.task_id, new_description=too_long_desc)
        self.assertFalse(ok)
        self.assertIn("Task description exceeds the 150-word limit.", msg)

    def test_get_tasks_by_project(self):
        """بررسی دریافت تسک‌ها با شناسه پروژه"""
        self.manager.add_task(self.project_id, "Another Task")
        tasks = self.manager.projects[0].tasks

        self.assertEqual(len(tasks), 2)
        titles = [t.title for t in tasks]
        self.assertIn(self.task_title, titles)
        self.assertIn("Another Task", titles)

    def test_find_task_in_non_existent_project(self):
        """بررسی عملیات روی پروژه‌ی ناموجود"""
        ok, msg = self.manager.remove_task(999, self.task_id)
        self.assertFalse(ok)
        self.assertIn("خطا: پروژه‌ای با شناسه 999 یافت نشد.", msg)

    def test_add_task_long_description_validation(self):
        """بررسی اعتبارسنجی توضیحات هنگام افزودن تسک"""
        too_long_desc = " ".join([f"word{i}" for i in range(151)])
        ok, msg = self.manager.add_task(self.project_id, "Short Title", description=too_long_desc)
        self.assertFalse(ok)
        self.assertIn("Task description exceeds the 150-word limit.", msg)
