"use client";

import { useSystemStatus } from "@/hooks/useSystemStatus";

export function SystemStatus() {
  const { data, isLoading, isError } = useSystemStatus();

  let status: { label: string; dot: string } = { label: "Checking…", dot: "bg-slate-500" };

  if (isError) {
    status = { label: "Offline", dot: "bg-red-500" };
  } else if (!isLoading && data?.status === "healthy") {
    status = { label: "Ready", dot: "bg-emerald-500" };
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-4 py-1.5 text-sm text-slate-300">
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${status.dot}`} />
      System Status: {status.label}
    </div>
  );
}
