import React, { createContext, useContext, useState, useCallback } from "react";

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
}

interface ToastContextType {
  toasts: Toast[];
  toast: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    // Return a fallback that just logs to console if provider is missing
    return {
      toast: (toast: Omit<Toast, "id">) => {
        console.log("Toast:", toast);
      },
      toasts: [],
      dismiss: () => {},
    };
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((newToast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(7);
    const toastWithId = { ...newToast, id };

    setToasts((prev) => [...prev, toastWithId]);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
};

// Toast container component
const ToastContainer: React.FC<{
  toasts: Toast[];
  dismiss: (id: string) => void;
}> = ({ toasts, dismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto min-w-[300px] max-w-md rounded-lg border p-4 shadow-lg transition-all duration-300 ${
            toast.variant === "destructive"
              ? "bg-destructive text-destructive-foreground border-destructive"
              : "bg-background text-foreground border-border"
          }`}
        >
          {toast.title && <div className="font-semibold">{toast.title}</div>}
          {toast.description && (
            <div className="mt-1 text-sm opacity-90">{toast.description}</div>
          )}
          <button
            onClick={() => dismiss(toast.id)}
            className="absolute top-2 right-2 text-foreground/50 hover:text-foreground"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};
