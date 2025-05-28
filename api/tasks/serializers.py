from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer cho Task model
    """
    
    class Meta:
        model = Task
        fields = [
            'id', 'task_name', 'status', 'priority', 'args', 'kwargs',
            'result', 'error_message', 'retry_count', 'max_retries',
            'retry_delay', 'next_retry_at', 'created_at', 'updated_at',
            'started_at', 'completed_at', 'worker_id', 'queue_name'
        ]
        read_only_fields = [
            'id', 'status', 'result', 'error_message', 'retry_count',
            'next_retry_at', 'created_at', 'updated_at', 'started_at',
            'completed_at', 'worker_id'
        ]
    
    def validate_task_name(self, value):
        """
        Validate task_name không được rỗng
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Task name không được để trống")
        return value.strip()
    
    def validate_args(self, value):
        """
        Validate args phải là list
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Args phải là một list")
        return value
    
    def validate_kwargs(self, value):
        """
        Validate kwargs phải là dict
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Kwargs phải là một dictionary")
        return value 