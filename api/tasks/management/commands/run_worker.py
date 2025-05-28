import logging
from django.core.management.base import BaseCommand, CommandError
from django_task_queue.worker import Worker, WorkerPool

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Chạy task worker để xử lý tasks từ queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='default',
            help='Tên queue để worker xử lý (default: default)'
        )
        
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='Số lượng workers chạy song song (default: 1)'
        )
        
        parser.add_argument(
            '--worker-id',
            type=str,
            help='ID cụ thể cho worker (chỉ dùng khi workers=1)'
        )
        
        parser.add_argument(
            '--poll-interval',
            type=int,
            default=1,
            help='Thời gian chờ giữa các lần poll queue (seconds, default: 1)'
        )
        
        parser.add_argument(
            '--max-tasks',
            type=int,
            help='Số lượng tasks tối đa để xử lý trước khi dừng worker'
        )
        
        parser.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Log level (default: INFO)'
        )

    def handle(self, *args, **options):
        # Setup logging
        log_level = getattr(logging, options['log_level'])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        queue_name = options['queue']
        num_workers = options['workers']
        worker_id = options['worker_id']
        poll_interval = options['poll_interval']
        max_tasks = options['max_tasks']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting {num_workers} worker(s) for queue "{queue_name}"...'
            )
        )
        
        try:
            if num_workers == 1:
                # Single worker
                worker = Worker(
                    queue_name=queue_name,
                    worker_id=worker_id,
                    poll_interval=poll_interval,
                    max_tasks_per_run=max_tasks
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Worker {worker.worker_id} started')
                )
                
                worker.start()
                
            else:
                # Multiple workers using WorkerPool
                if worker_id:
                    raise CommandError(
                        '--worker-id không thể sử dụng với nhiều workers. '
                        'Sử dụng --workers=1 hoặc bỏ --worker-id'
                    )
                
                worker_pool = WorkerPool(
                    num_workers=num_workers,
                    queue_name=queue_name
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Worker pool with {num_workers} workers started')
                )
                
                worker_pool.start()
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nReceived interrupt signal, shutting down...')
            )
        except Exception as e:
            raise CommandError(f'Worker failed: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('Worker(s) stopped successfully')
        ) 