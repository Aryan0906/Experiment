/**
 * StatusTracker Component
 * Displays real-time processing status with a stepper UI
 */
import React from 'react';
import type { Product } from '../types';

interface StatusTrackerProps {
    status: Product['status'];
    errorMessage?: string | null;
}

const steps = [
    { id: 'queued', label: 'Queued' },
    { id: 'extracting_attributes', label: 'Extracting Attributes' },
    { id: 'detecting_anomalies', label: 'Detecting Anomalies' },
    { id: 'done', label: 'Complete' },
];

export const StatusTracker: React.FC<StatusTrackerProps> = ({ status, errorMessage }) => {
    const getCurrentStepIndex = () => {
        switch (status) {
            case 'queued':
                return 0;
            case 'extracting_attributes':
                return 1;
            case 'detecting_anomalies':
                return 2;
            case 'done':
            case 'error':
                return 3;
            default:
                return 0;
        }
    };

    const currentStepIndex = getCurrentStepIndex();

    if (status === 'error') {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <div className="text-red-600 text-lg font-semibold mb-2">Processing Failed</div>
                <p className="text-red-500 text-sm">{errorMessage || 'An unknown error occurred'}</p>
            </div>
        );
    }

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
                {steps.map((step, index) => {
                    const isCompleted = index < currentStepIndex;
                    const isCurrent = index === currentStepIndex;
                    const isPending = index > currentStepIndex;

                    return (
                        <React.Fragment key={step.id}>
                            <div className="flex flex-col items-center">
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                                        isCompleted
                                            ? 'bg-green-500 text-white'
                                            : isCurrent
                                            ? 'bg-blue-500 text-white animate-pulse'
                                            : 'bg-gray-200 text-gray-500'
                                    }`}
                                >
                                    {isCompleted ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        index + 1
                                    )}
                                </div>
                                <span
                                    className={`mt-2 text-xs font-medium ${
                                        isCurrent ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400'
                                    }`}
                                >
                                    {step.label}
                                </span>
                            </div>
                            {index < steps.length - 1 && (
                                <div
                                    className={`flex-1 h-1 mx-2 rounded ${
                                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                                    }`}
                                />
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
            {status !== 'done' && (
                <div className="mt-4 text-center">
                    <p className="text-sm text-gray-500">Processing your product image...</p>
                </div>
            )}
        </div>
    );
};

export default StatusTracker;
