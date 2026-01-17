import { useEffect, useState, useCallback } from 'react';
import './Toast.css';

export interface ToastMessage {
    id: string;
    type: 'error' | 'success';
    message: string;
}

interface ToastProps {
    toast: ToastMessage;
    onDismiss: (id: string) => void;
    duration?: number;
}

function Toast({ toast, onDismiss, duration = 5000 }: ToastProps) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onDismiss(toast.id);
        }, duration);

        return () => clearTimeout(timer);
    }, [toast.id, onDismiss, duration]);

    return (
        <div className={`toast toast-${toast.type}`} role="alert">
            <span className="toast-icon">{toast.type === 'error' ? '⚠️' : '✓'}</span>
            <span className="toast-message">{toast.message}</span>
            <button className="toast-close" onClick={() => onDismiss(toast.id)} aria-label="Dismiss">
                ×
            </button>
        </div>
    );
}

interface ToastContainerProps {
    toasts: ToastMessage[];
    onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
    if (toasts.length === 0) return null;

    return (
        <div className="toast-container">
            {toasts.map((toast) => (
                <Toast key={toast.id} toast={toast} onDismiss={onDismiss} />
            ))}
        </div>
    );
}

// Custom hook for managing toasts
export function useToast() {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const showToast = useCallback((type: 'error' | 'success', message: string) => {
        const id = crypto.randomUUID();
        setToasts((prev) => [...prev, { id, type, message }]);
    }, []);

    const dismissToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    return {
        toasts,
        showToast,
        dismissToast,
    };
}
