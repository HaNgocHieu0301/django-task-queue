from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from .models import Task, TaskPriority
from .serializers import TaskSerializer
from django_task_queue.queue_manager import QueueManager

# Create queue manager instance
queue_manager = QueueManager()

class TaskViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Tạo Task mới
        
        POST /api/tasks/
        Body: {
            "task_name": "string",
            "priority": "low|normal|high|critical" (optional, default: normal),
            "args": [] (optional, default: []),
            "kwargs": {} (optional, default: {}),
            "max_retries": int (optional, default: 3),
            "retry_delay": int (optional, default: 60),
            "queue_name": "string" (optional, default: "default")
        }
        """
        try:
            data = request.data.copy()
            
            # Map priority string to enum value
            priority_mapping = {
                'low': TaskPriority.LOW,
                'normal': TaskPriority.NORMAL,
                'high': TaskPriority.HIGH,
                'critical': TaskPriority.CRITICAL,
            }
            
            priority_str = data.get('priority', 'normal').lower()
            if priority_str not in priority_mapping:
                return Response(
                    {
                        'success': False,
                        'message': 'Dữ liệu không hợp lệ',
                        'errors': {'priority': ['Priority phải là một trong: low, normal, high, critical']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prepare data for queue manager
            task_data = {
                'task_name': data.get('task_name'),
                'priority': priority_mapping[priority_str],
                'args': data.get('args', []),
                'kwargs': data.get('kwargs', {}),
                'max_retries': data.get('max_retries', 3),
                'retry_delay': data.get('retry_delay', 60),
                'queue_name': data.get('queue_name', 'default')
            }
            
            # Validate required fields
            if not task_data['task_name']:
                return Response(
                    {
                        'success': False,
                        'message': 'Dữ liệu không hợp lệ',
                        'errors': {'task_name': ['Task name là bắt buộc']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate args type
            if not isinstance(task_data['args'], list):
                return Response(
                    {
                        'success': False,
                        'message': 'Dữ liệu không hợp lệ',
                        'errors': {'args': ['Args phải là một list']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate kwargs type
            if not isinstance(task_data['kwargs'], dict):
                return Response(
                    {
                        'success': False,
                        'message': 'Dữ liệu không hợp lệ',
                        'errors': {'kwargs': ['Kwargs phải là một dict']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create task via queue manager
            task_id = queue_manager.enqueue_task(**task_data)
            task = Task.objects.get(id=task_id)
            
            return Response(
                {
                    'success': True,
                    'message': 'Task đã được tạo thành công',
                    'data': TaskSerializer(task).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': 'Có lỗi xảy ra khi tạo task',
                    'errors': {'detail': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request, *args, **kwargs):
        """
        Lấy danh sách Tasks với filtering
        
        GET /api/tasks/
        Query params:
        - status: filter theo status
        - priority: filter theo priority
        - queue_name: filter theo queue_name
        """
        queryset = self.get_queryset()
        
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = request.GET.get('priority')
        if priority_filter:
            # Map priority string to enum value
            priority_mapping = {
                'low': TaskPriority.LOW,
                'normal': TaskPriority.NORMAL,
                'high': TaskPriority.HIGH,
                'critical': TaskPriority.CRITICAL,
            }
            
            priority_str = priority_filter.lower()
            if priority_str in priority_mapping:
                queryset = queryset.filter(priority=priority_mapping[priority_str])
        
        queue_filter = request.GET.get('queue_name')
        if queue_filter:
            queryset = queryset.filter(queue_name=queue_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            {
                'success': True,
                'message': 'Lấy danh sách tasks thành công',
                'data': serializer.data,
                'count': queryset.count()
            },
            status=status.HTTP_200_OK
        )
