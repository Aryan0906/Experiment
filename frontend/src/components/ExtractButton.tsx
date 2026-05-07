import React, { useState } from 'react';
import { API_URL } from '../types';

interface ExtractButtonProps {
    sellerId: number;
    onComplete: () => void;
    disabled?: boolean;
}

export const ExtractButton: React.FC<ExtractButtonProps> = ({ sellerId, onComplete, disabled }) => {
    const [status, setStatus] = useState<string>("idle");
    const [progress, setProgress] = useState<number>(0);
    const [error, setError] = useState<string>("");

    const handleExtract = async () => {
        setError("");
        setStatus("starting");
        setProgress(0);

        try {
            const res = await fetch(`${API_URL}/api/extract?seller_id=${sellerId}`, { method: "POST" });
            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: "Extraction failed" }));
                setError(data.detail || "Extraction failed");
                setStatus("idle");
                return;
            }

            const data = await res.json();
            const jobId = data.job_id;
            setStatus("processing");

            // Poll job status
            const interval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${API_URL}/api/jobs/${jobId}`);
                    if (!statusRes.ok) {
                        clearInterval(interval);
                        setError("Failed to check job status");
                        setStatus("idle");
                        return;
                    }

                    const statusData = await statusRes.json();
                    setStatus(statusData.status);
                    setProgress(statusData.progress || 0);

                    if (statusData.status === "completed") {
                        clearInterval(interval);
                        setStatus("done");
                        onComplete();
                        // Reset to idle after showing "Done" briefly
                        setTimeout(() => setStatus("idle"), 2000);
                    } else if (statusData.status === "failed") {
                        clearInterval(interval);
                        setError("Extraction failed");
                        setStatus("idle");
                    }
                } catch {
                    clearInterval(interval);
                    setError("Lost connection");
                    setStatus("idle");
                }
            }, 1000);
        } catch {
            setError("Network error");
            setStatus("idle");
        }
    };

    const isProcessing = status === "processing" || status === "starting";

    return (
        <div className="relative">
            <button
                onClick={handleExtract}
                disabled={isProcessing || disabled}
                className={`
                    px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200
                    flex items-center gap-2 shadow-lg
                    ${isProcessing
                        ? 'bg-indigo-600/50 text-indigo-300 cursor-wait'
                        : status === "done"
                            ? 'bg-emerald-600 text-white'
                            : disabled
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-indigo-600 text-white hover:bg-indigo-500 hover:shadow-indigo-500/20 active:scale-95'
                    }
                `}
            >
                {isProcessing ? (
                    <>
                        <div className="animate-spin h-4 w-4 border-2 border-indigo-300 border-t-transparent rounded-full"></div>
                        Extracting... {progress}%
                    </>
                ) : status === "done" ? (
                    <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Done!
                    </>
                ) : (
                    <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Extract Attributes
                    </>
                )}
            </button>

            {/* Progress bar */}
            {isProcessing && (
                <div className="absolute -bottom-2 left-0 right-0 h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-indigo-500 transition-all duration-300 rounded-full"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}

            {/* Error message */}
            {error && (
                <p className="absolute top-full mt-2 text-xs text-red-400 whitespace-nowrap">{error}</p>
            )}
        </div>
    );
};
