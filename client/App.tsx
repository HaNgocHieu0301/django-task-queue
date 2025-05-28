
import React, { useState, useEffect, useCallback } from 'react';
import { Task, TaskStatus } from './types';
import { API_POLL_INTERVAL, API_BASE_URL } from './constants';
import TaskForm from './components/TaskForm';
import { TaskList, PendingIcon, InProgressIcon, CompletedIcon, FailedIcon } from './components/TaskList';

// Helper to transform API task to frontend Task type (especially for dates if needed by other logic)
// For now, TaskCard handles date strings directly, so this transformation is minimal.
// API returns dates as strings. Task interface defines them as strings.
const transformApiTask = (apiTask: any): Task => {
  return {
    ...apiTask,
    // Ensure all required fields are present, even if API might omit them when null
    args: apiTask.args || undefined,
    kwargs: apiTask.kwargs || undefined,
    priority: apiTask.priority || undefined,
    result: apiTask.result !== undefined ? apiTask.result : undefined,
    error_message: apiTask.error_message || null,
    started_at: apiTask.started_at || null,
    completed_at: apiTask.completed_at || null,
    next_retry_at: apiTask.next_retry_at || null,
  } as Task;
};

interface TaskFormData {
  name: string;
  argsStr: string;
  kwargsStr: string;
  otherPayloadStr: string;
}

const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isAddingTask, setIsAddingTask] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/tasks/`);
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      // The API wrapper seems to be { success: true, data: [...] }
      // Or directly an array, based on the curl examples. Assuming data is the array of tasks.
      // If it's wrapped: const taskArray = data.data || [];
      const taskArray = Array.isArray(data) ? data : (data.data || []); 
      setTasks(taskArray.map(transformApiTask));
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred while fetching tasks.");
      // setTasks([]); // Optionally clear tasks on error or keep stale data
    }
  }, []);

  useEffect(() => {
    fetchTasks(); // Initial fetch
    const intervalId = setInterval(fetchTasks, API_POLL_INTERVAL);
    return () => clearInterval(intervalId);
  }, [fetchTasks]);

  const handleAddTask = useCallback(async (taskData: TaskFormData) => {
    setIsAddingTask(true);
    setError(null);

    let parsedArgs: any[] | undefined;
    let parsedKwargs: Record<string, any> | undefined;

    // Validate and parse Args
    if (taskData.argsStr.trim()) {
      try {
        const tempArgs = JSON.parse(taskData.argsStr);
        if (!Array.isArray(tempArgs)) {
          alert('Validation Error: "Args" field must be a valid JSON array (e.g., [1, "value"]).');
          setIsAddingTask(false);
          return;
        }
        parsedArgs = tempArgs;
      } catch (e) {
        alert('Validation Error: "Args" field contains invalid JSON.\n' + (e instanceof Error ? e.message : String(e) ));
        setIsAddingTask(false);
        return;
      }
    }

    // Validate and parse Kwargs
    if (taskData.kwargsStr.trim()) {
      try {
        const tempKwargs = JSON.parse(taskData.kwargsStr);
        if (typeof tempKwargs !== 'object' || tempKwargs === null || Array.isArray(tempKwargs)) {
          alert('Validation Error: "Kwargs" field must be a valid JSON object (e.g., {"key": "value"}).');
          setIsAddingTask(false);
          return;
        }
        parsedKwargs = tempKwargs;
      } catch (e) {
        alert('Validation Error: "Kwargs" field contains invalid JSON.\n' + (e instanceof Error ? e.message : String(e)));
        setIsAddingTask(false);
        return;
      }
    }
    
    // Use Other Payload if Args and Kwargs were not provided
    if (!parsedArgs && !parsedKwargs && taskData.otherPayloadStr.trim()) {
      // For simplicity, we wrap the otherPayloadStr in an array.
      // If it's intended to be a number, it's sent as a string here.
      // The backend would need to handle type conversion if necessary.
      parsedArgs = [taskData.otherPayloadStr];
    }

    const apiTaskPayload: any = {
      task_name: taskData.name,
    };
    if (parsedArgs) apiTaskPayload.args = parsedArgs;
    if (parsedKwargs) apiTaskPayload.kwargs = parsedKwargs;
    // Add default priority or other fields if needed by API and not in form
    // apiTaskPayload.priority = "normal"; 
    // apiTaskPayload.max_retries = 3;

    try {
      const response = await fetch(`${API_BASE_URL}/tasks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiTaskPayload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error during task creation."}));
        throw new Error(`Failed to add task: ${response.status} - ${errorData.detail || response.statusText}`);
      }
      await fetchTasks(); // Re-fetch tasks to get the latest list including the new one
    } catch (err) {
      console.error("Failed to add task:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred while adding task.");
    } finally {
      setIsAddingTask(false);
    }
  }, [fetchTasks]);


  const pendingTasks = tasks.filter(task => task.status === TaskStatus.PENDING || task.status === TaskStatus.RETRY)
                            .sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  const inProgressTasks = tasks.filter(task => task.status === TaskStatus.PROCESSING);
  const completedTasks = tasks.filter(task => task.status === TaskStatus.SUCCESS)
                             .sort((a,b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
  const failedTasks = tasks.filter(task => task.status === TaskStatus.FAILED)
                           .sort((a,b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-gray-100 p-4 md:p-8">
      <header className="mb-10 text-center">
        <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-red-500">
          Task Queue Visualizer
        </h1>
        <p className="text-slate-400 mt-2 text-lg">Visualizing a task queue interacting with a backend API.</p>
      </header>

      {error && (
        <div className="my-4 p-4 bg-red-700 border border-red-900 text-white rounded-md text-center shadow-lg">
          <p><strong>Error:</strong> {error}</p>
          <button onClick={() => setError(null)} className="mt-2 px-3 py-1 bg-red-800 hover:bg-red-900 rounded text-sm">Dismiss</button>
        </div>
      )}

      <div className="mb-12 max-w-2xl mx-auto">
        <TaskForm onAddTask={handleAddTask} isLoading={isAddingTask} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <TaskList title="Pending & Retry" tasks={pendingTasks} icon={<PendingIcon />} />
        <TaskList title="In Progress" tasks={inProgressTasks} icon={<InProgressIcon />} />
        <TaskList title="Completed" tasks={completedTasks} icon={<CompletedIcon />} />
        <TaskList title="Failed" tasks={failedTasks} icon={<FailedIcon />} />
      </div>
      
      <footer className="text-center mt-12 py-6 border-t border-slate-700">
        <p className="text-sm text-slate-500">
          Interacting with Django Task Queue API at <code className="bg-slate-700 px-1 rounded">{API_BASE_URL}</code>.
        </p>
         <p className="text-xs text-slate-600 mt-1">
          Polling for updates every {API_POLL_INTERVAL/1000} seconds.
        </p>
      </footer>
    </div>
  );
};

export default App;
