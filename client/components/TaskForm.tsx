
import React, { useState } from 'react';

interface TaskFormProps {
  onAddTask: (taskData: { name: string; argsStr: string; kwargsStr: string; otherPayloadStr: string }) => void;
  isLoading: boolean;
}

const TaskForm: React.FC<TaskFormProps> = ({ onAddTask, isLoading }) => {
  const [name, setName] = useState<string>('');
  const [argsStr, setArgsStr] = useState<string>('');
  const [kwargsStr, setKwargsStr] = useState<string>('');
  const [otherPayloadStr, setOtherPayloadStr] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Task name is required.');
      return;
    }
    onAddTask({ name, argsStr, kwargsStr, otherPayloadStr });
    setName('');
    setArgsStr('');
    setKwargsStr('');
    setOtherPayloadStr('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 bg-white rounded-xl shadow-lg space-y-4 mb-8">
      <h2 className="text-2xl font-semibold text-gray-700 mb-4">Add New Task</h2>
      <div>
        <label htmlFor="taskName" className="block text-sm font-medium text-gray-600 mb-1">
          Task Name
        </label>
        <input
          type="text"
          id="taskName"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., add_numbers, process_image"
          className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 text-gray-800"
          required
        />
      </div>

      <div>
        <label htmlFor="taskArgs" className="block text-sm font-medium text-gray-600 mb-1">
          Args (JSON Array)
        </label>
        <textarea
          id="taskArgs"
          value={argsStr}
          onChange={(e) => setArgsStr(e.target.value)}
          rows={3}
          placeholder='e.g., [10, "hello", true]'
          className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 text-gray-800"
        />
        <p className="text-xs text-gray-500 mt-1">Provide a valid JSON array. Ignored if "Other Payload" is used while this is empty.</p>
      </div>

      <div>
        <label htmlFor="taskKwargs" className="block text-sm font-medium text-gray-600 mb-1">
          Kwargs (JSON Object)
        </label>
        <textarea
          id="taskKwargs"
          value={kwargsStr}
          onChange={(e) => setKwargsStr(e.target.value)}
          rows={3}
          placeholder='e.g., {"param1": 10, "param2": "test"}'
          className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 text-gray-800"
        />
        <p className="text-xs text-gray-500 mt-1">Provide a valid JSON object. Ignored if "Other Payload" is used while this is empty.</p>
      </div>
      
      <div>
        <label htmlFor="taskOtherPayload" className="block text-sm font-medium text-gray-600 mb-1">
          Single Item Payload (if Args & Kwargs are empty)
        </label>
        <input
          type="text"
          id="taskOtherPayload"
          value={otherPayloadStr}
          onChange={(e) => setOtherPayloadStr(e.target.value)}
          placeholder='e.g., "simple_string_payload" or 123'
          className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 text-gray-800"
        />
        <p className="text-xs text-gray-500 mt-1">Used as <code className="text-xs bg-gray-200 px-1 rounded">args: [value]</code> if Args and Kwargs fields are empty.</p>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full px-6 py-3 bg-indigo-600 text-white font-semibold rounded-md shadow-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Adding...' : 'Add Task to Queue'}
      </button>
    </form>
  );
};

export default TaskForm;
