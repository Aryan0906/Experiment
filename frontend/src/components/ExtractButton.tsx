import React, { useState } from 'react';
import { API_URL } from '../types';

export const ExtractButton: React.FC<{sellerId: number, onComplete: () => void}> = ({ sellerId, onComplete }) => {
    const [status, setStatus] = useState<string>("idle");
    const [progress, setProgress] = useState<number>(0);

    const handleExtract = async () => {
        const res = await fetch(`${API_URL}/api/extract?seller_id=${sellerId}`, { method: "POST" });
        const data = await res.json();
        setStatus("processing");
        
        const interval = setInterval(async () => {
            const statusRes = await fetch(`${API_URL}/api/jobs/${data.job_id}`);
            const statusData = await statusRes.json();
            setStatus(statusData.status);
            setProgress(statusData.progress);
            if (statusData.status === "completed" || statusData.status === "failed") {
                clearInterval(interval);
                onComplete();
            }
        }, 2000);
    };

    return (
        <button onClick={handleExtract} disabled={status === "processing"} className="px-4 py-2 bg-blue-600 text-white rounded-md">
            {status === "processing" ? `Extracting... ${progress}%` : "Extract Attributes"}
        </button>
    );
};
