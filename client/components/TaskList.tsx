import React from 'react';
import { Task } from '../types';
import TaskCard from './TaskCard';

interface TaskListProps {
  title: string;
  tasks: Task[];
  icon?: React.ReactNode;
}

const TaskList: React.FC<TaskListProps> = ({ title, tasks, icon }) => {
  return (
    <div className="bg-gray-50 p-5 rounded-xl shadow-lg h-full flex flex-col">
      <div className="flex items-center mb-4">
        {icon && <span className="mr-2 text-xl text-indigo-600">{icon}</span>}
        <h2 className="text-xl font-semibold text-gray-700">{title} ({tasks.length})</h2>
      </div>
      <div className="flex-grow overflow-y-auto pr-1 space-y-3 min-h-[200px] max-h-[calc(100vh-350px)] sm:max-h-[60vh] scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200">
        {tasks.length === 0 ? (
          <p className="text-gray-500 italic text-center py-4">No tasks in this queue.</p>
        ) : (
          tasks.map(task => <TaskCard key={task.id} task={task} />)
        )}
      </div>
    </div>
  );
};

// SVG Icons remain the same
const PendingIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
const InProgressIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 animate-spin-slow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m-15.357-2A8.001 8.001 0 0019.418 15m0 0H15" />
  </svg>
);

const CompletedIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const FailedIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

export { TaskList, PendingIcon, InProgressIcon, CompletedIcon, FailedIcon };
