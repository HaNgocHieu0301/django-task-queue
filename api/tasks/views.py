from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Tạo Task mới
        
        POST /api/tasks/
        Body: {
            "task_name": "string",
            "priority": "low|normal|high|urgent" (optional, default: normal),
            "args": [] (optional, default: []),
            "kwargs": {} (optional, default: {}),
            "max_retries": int (optional, default: 3),
            "retry_delay": int (optional, default: 60),
            "queue_name": "string" (optional, default: "default")
        }
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            task = serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Task đã được tạo thành công',
                    'data': TaskSerializer(task).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                'success': False,
                'message': 'Dữ liệu không hợp lệ',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
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
            queryset = queryset.filter(priority=priority_filter)
        
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
