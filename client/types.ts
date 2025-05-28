export enum TaskStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  FAILED = 'failed',
  RETRY = 'retry',
}

export interface Task {
  id: string; // UUID from backend
  task_name: string;
  args?: any[];
  kwargs?: Record<string, any>;
  status: TaskStatus;
  priority?: string | number; // API create payload suggests string, response example shows number
  result?: any;
  error_message?: string | null;
  retry_count: number;
  max_retries: number;
  created_at: string; // ISO date string from API
  updated_at: string; // ISO date string from API
  started_at?: string | null; // ISO date string from API
  completed_at?: string | null; // ISO date string from API
  next_retry_at?: string | null; // ISO date string from API
}
