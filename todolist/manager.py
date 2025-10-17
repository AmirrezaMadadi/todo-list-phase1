import os
from datetime import date
from typing import List, Optional, Tuple
from .models import Task, Project

try:
    MAX_PROJECTS = int(os.getenv("MAX_NUMBER_OF_PROJECT", 5))
    MAX_TASKS = int(os.getenv("MAX_NUMBER_OF_TASK", 20))
except ValueError:
    MAX_PROJECTS = 5
    MAX_TASKS = 20


class ToDoListManager:
    def __init__(self):
        self.projects: List[Project] = []
        self.MAX_PROJECTS = MAX_PROJECTS
        self.MAX_TASKS = MAX_TASKS
        self.total_tasks_count = 0
        print(f"ToDoList Initialized. Max Projects: {self.MAX_PROJECTS}, Max Total Tasks: {self.MAX_TASKS}")

    def _validate_word_limit(self, text: Optional[str], max_words: int, field_name: str) -> Tuple[bool, str]:
        if not text:
            return True, ""
        word_count = len([w for w in text.split() if w])
        if word_count > max_words:
            if field_name == "Project name":
                friendly = "نام"
            elif field_name == "Task title":
                friendly = "عنوان"
            elif field_name in ["Project description", "Task description"]:
                friendly = "توضیحات"
            else:
                friendly = field_name
            return False, f"خطای اعتبارسنجی {friendly}: {field_name.capitalize()} exceeds the {max_words}-word limit."
        return True, ""

    def add_project(self, name: str, description: Optional[str] = None) -> Tuple[bool, str]:
        if self.total_tasks_count >= self.MAX_TASKS:
            return False, f"خطا: سقف کل تسک‌ها ({self.MAX_TASKS}) رسیده است."
        if len(self.projects) >= self.MAX_PROJECTS:
            return False, f"خطا: سقف تعداد پروژه ({self.MAX_PROJECTS}) رسیده است."
        if any(p.name == name for p in self.projects):
            return False, f"خطا: پروژه‌ای با نام '{name}' از قبل موجود است."

        ok_name, msg_name = self._validate_word_limit(name, 30, "Project name")
        if not ok_name:
            return False, msg_name
        ok_desc, msg_desc = self._validate_word_limit(description, 150, "Project description")
        if not ok_desc:
            return False, msg_desc

        project = Project(name=name, description=description)
        self.projects.append(project)
        return True, f"پروژه '{name}' با شناسه {project.id} با موفقیت اضافه شد."

    def remove_project(self, project_id: int) -> Tuple[bool, str]:
        try:
            proj = next(p for p in self.projects if p.id == project_id)
            self.total_tasks_count -= len(proj.tasks)
            self.projects.remove(proj)
            return True, f"پروژه با شناسه {project_id} با موفقیت حذف شد."
        except StopIteration:
            return False, f"خطا: پروژه‌ای با شناسه {project_id} یافت نشد."

    def list_projects(self) -> List[dict]:
        return [{'id': p.id, 'name': p.name, 'description': p.description, 'task_count': len(p.tasks)} for p in self.projects]

    def add_task(self, project_id: int, title: str, description: Optional[str] = None,
                 due_date: Optional[date] = None) -> Tuple[bool, str]:
        if self.total_tasks_count >= self.MAX_TASKS:
            return False, f"خطا: سقف کل تسک‌ها ({self.MAX_TASKS}) رسیده است."
        try:
            proj = next(p for p in self.projects if p.id == project_id)
            ok_title, msg_title = self._validate_word_limit(title, 30, "Task title")
            if not ok_title:
                return False, msg_title
            ok_desc, msg_desc = self._validate_word_limit(description, 150, "Task description")
            if not ok_desc:
                return False, msg_desc
            task = Task(title=title, description=description, due_date=due_date)
            proj.tasks.append(task)
            self.total_tasks_count += 1
            return True, f"تسک '{title}' با شناسه {task.id} به پروژه '{proj.name}' اضافه شد."
        except StopIteration:
            return False, f"خطا: پروژه‌ای با شناسه {project_id} یافت نشد."

    def remove_task(self, project_id: int, task_id: int) -> Tuple[bool, str]:
        try:
            proj = next(p for p in self.projects if p.id == project_id)
        except StopIteration:
            return False, f"خطا: پروژه‌ای با شناسه {project_id} یافت نشد."
        try:
            t = next(t for t in proj.tasks if t.id == task_id)
            proj.tasks.remove(t)
            self.total_tasks_count -= 1
            return True, f"تسک با شناسه {task_id} از پروژه '{proj.name}' با موفقیت حذف شد."
        except StopIteration:
            return False, f"خطا: تسکی با شناسه {task_id} در پروژه '{proj.name}' یافت نشد."

    def toggle_task_completion(self, project_id: int, task_id: int) -> Tuple[bool, str]:
        try:
            proj = next(p for p in self.projects if p.id == project_id)
        except StopIteration:
            return False, f"خطا: پروژه‌ای با شناسه {project_id} یافت نشد."
        try:
            t = next(t for t in proj.tasks if t.id == task_id)
            t.is_completed = not t.is_completed
            s = "تکمیل شده" if t.is_completed else "ناتمام"
            return True, f"وضعیت تسک با شناسه {task_id} به '{s}' تغییر یافت."
        except StopIteration:
            return False, f"خطا: تسکی با شناسه {task_id} در پروژه '{proj.name}' یافت نشد."

    def edit_task(self, project_id: int, task_id: int,
                  new_title: Optional[str] = None,
                  new_description: Optional[str] = None,
                  new_due_date: Optional[date] = None) -> Tuple[bool, str]:
        try:
            proj = next(p for p in self.projects if p.id == project_id)
        except StopIteration:
            return False, f"خطا: پروژه‌ای با شناسه {project_id} یافت نشد."
        try:
            t = next(t for t in proj.tasks if t.id == task_id)
        except StopIteration:
            return False, f"خطا: تسکی با شناسه {task_id} در پروژه '{proj.name}' یافت نشد."

        changes = []
        if new_title is not None and new_title != t.title:
            ok, msg = self._validate_word_limit(new_title, 30, "Task title")
            if not ok:
                return False, msg
            t.title = new_title
            changes.append("عنوان")
        if new_description is not None and new_description != t.description:
            ok, msg = self._validate_word_limit(new_description, 150, "Task description")
            if not ok:
                return False, msg
            t.description = new_description
            changes.append("توضیحات")
        if new_due_date is not None and new_due_date != t.due_date:
            t.due_date = new_due_date
            changes.append("تاریخ سررسید")

        if not changes:
            return True, f"تسک با شناسه {task_id}: هیچ تغییری اعمال نشد."
        return True, f"تسک با شناسه {task_id} با موفقیت ویرایش شد: {', '.join(changes)}"
