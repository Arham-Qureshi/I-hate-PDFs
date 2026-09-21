import { useEffect, useState } from 'react';
import api from '../api/client';

interface TaskStatus {
  task_id: string;
  state: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number | null;
  error: string | null;
}

export function useTaskPolling(taskId: string | null) {
  const [status, setStatus] = useState<TaskStatus | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const res = await api.get(`/api/task/${taskId}`);
        setStatus(res.data);
        if (res.data.state === 'completed' || res.data.state === 'failed') {
          return;
        }
      } catch {
        setStatus((prev) =>
          prev ? { ...prev, state: 'failed', error: 'Failed to poll status' } : null
        );
      }
    };

    poll();
    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, [taskId]);

  return status;
}
