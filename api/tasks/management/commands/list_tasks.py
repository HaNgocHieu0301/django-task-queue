from django.core.management.base import BaseCommand
from django_task_queue.task_registry import task_registry


class Command(BaseCommand):
    help = 'Hiển thị danh sách tất cả tasks đã đăng ký'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Danh sách tasks đã đăng ký:')
        )
        
        tasks = task_registry.list_tasks()
        
        if not tasks:
            self.stdout.write(
                self.style.WARNING('Không có task nào được đăng ký.')
            )
            return
        
        for task_name, description in tasks.items():
            self.stdout.write(f"\n• {task_name}")
            if description and description != "No description":
                # Format docstring nicely
                lines = description.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self.stdout.write(f"  {line.strip()}")
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTổng cộng: {len(tasks)} tasks')
        ) 