import React from 'react';
import { Task, TaskStatus } from '../types';

interface TaskCardProps {
  task: Task;
}

const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
  const getStatusColorClasses = () => {
    switch (task.status) {
      case TaskStatus.PENDING:
        return 'border-blue-500 bg-blue-50';
      case TaskStatus.RETRY:
        return 'border-yellow-500 bg-yellow-50';
      case TaskStatus.PROCESSING:
        return 'border-orange-500 bg-orange-50 animate-pulse';
      case TaskStatus.SUCCESS:
        return 'border-green-500 bg-green-50';
      case TaskStatus.FAILED:
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const formatDateTime = (dateString?: string | null): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const renderValue = (value: any) => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  }

  return (
    <div className={`p-4 rounded-lg shadow-md border-l-4 ${getStatusColorClasses()} transition-all duration-300 ease-in-out mb-3`}>
      <h3 className="text-lg font-semibold text-gray-800 truncate" title={task.task_name}>{task.task_name}</h3>
      <p className="text-xs text-gray-500 mb-1">ID: {task.id}</p>
      
      {(task.args && task.args.length > 0) && (
        <details className="mb-1">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-indigo-500">View Args</summary>
          <pre className="mt-1 text-xs bg-gray-100 text-gray-700 p-1.5 rounded-md overflow-auto max-h-20">
            {renderValue(task.args)}
          </pre>
        </details>
      )}
      {task.kwargs && Object.keys(task.kwargs).length > 0 && (
        <details className="mb-1">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-indigo-500">View Kwargs</summary>
          <pre className="mt-1 text-xs bg-gray-100 text-gray-700 p-1.5 rounded-md overflow-auto max-h-20">
            {renderValue(task.kwargs)}
          </pre>
        </details>
      )}
      
      <div className="text-sm space-y-1 mt-2">
        <p className="text-gray-700">
          <span className="font-medium">Status:</span> 
          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-semibold
            ${task.status === TaskStatus.PENDING ? 'bg-blue-100 text-blue-700' : ''}
            ${task.status === TaskStatus.RETRY ? 'bg-yellow-100 text-yellow-700' : ''}
            ${task.status === TaskStatus.PROCESSING ? 'bg-orange-100 text-orange-700' : ''}
            ${task.status === TaskStatus.SUCCESS ? 'bg-green-100 text-green-700' : ''}
            ${task.status === TaskStatus.FAILED ? 'bg-red-100 text-red-700' : ''}
          `}>
            {task.status.toUpperCase().replace('_', ' ')}
          </span>
        </p>
        <p className="text-gray-700">
          <span className="font-medium">Attempts:</span> {task.retry_count} / {task.max_retries}
        </p>
        {task.priority && (
          <p className="text-gray-700">
            <span className="font-medium">Priority:</span> {String(task.priority)}
          </p>
        )}
        <p className="text-xs text-gray-500">
          <span className="font-medium">Created:</span> {formatDateTime(task.created_at)}
        </p>
        <p className="text-xs text-gray-500">
          <span className="font-medium">Updated:</span> {formatDateTime(task.updated_at)}
        </p>
        {task.started_at && (
          <p className="text-xs text-gray-500">
            <span className="font-medium">Started:</span> {formatDateTime(task.started_at)}
          </p>
        )}
        {task.completed_at && (
           <p className="text-xs text-gray-500">
            <span className="font-medium">Completed:</span> {formatDateTime(task.completed_at)}
          </p>
        )}
        {task.status === TaskStatus.RETRY && task.next_retry_at && (
           <p className="text-xs text-gray-500">
            <span className="font-medium">Next Retry:</span> {formatDateTime(task.next_retry_at)}
          </p>
        )}
      </div>

      {task.status === TaskStatus.SUCCESS && task.result !== undefined && task.result !== null && (
        <div className="mt-2">
          <p className="text-xs font-medium text-gray-600">Result:</p>
          <pre className="text-xs bg-green-50 text-green-800 p-1.5 rounded-md overflow-auto max-h-24 border border-green-200">
            {renderValue(task.result)}
          </pre>
        </div>
      )}
      {task.status === TaskStatus.FAILED && task.error_message && (
        <div className="mt-2">
          <p className="text-xs font-medium text-red-600">Error:</p>
          <p className="text-xs text-red-700 bg-red-50 p-1.5 rounded-md overflow-auto max-h-24 border border-red-200">
            {task.error_message}
          </p>
        </div>
      )}
    </div>
  );
};

export default TaskCard;