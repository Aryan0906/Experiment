/**
 * AnomalyWarning Component
 * Displays anomaly detection warnings with severity indicators
 */
import React from 'react';
import type { AnomalyResult } from '../types';

interface AnomalyWarningProps {
    anomalyResult: AnomalyResult;
}

const THRESHOLDS = {
    blur: 0.7,
    background: 0.6,
    counterfeit: 0.5,
};

export const AnomalyWarning: React.FC<AnomalyWarningProps> = ({ anomalyResult }) => {
    const warnings: Array<{
        type: string;
        message: string;
        score: number;
        severity: 'warning' | 'danger';
    }> = [];

    // Check blur
    if (anomalyResult.is_blurry || anomalyResult.blur_score >= THRESHOLDS.blur) {
        warnings.push({
            type: 'Blurry Image',
            message: `This image appears to be blurry (score: ${(anomalyResult.blur_score * 100).toFixed(1)}%)`,
            score: anomalyResult.blur_score,
            severity: anomalyResult.blur_score >= 0.8 ? 'danger' : 'warning',
        });
    }

    // Check wrong background
    if (anomalyResult.is_wrong_background || anomalyResult.background_score >= THRESHOLDS.background) {
        warnings.push({
            type: 'Wrong Background',
            message: `The background may not meet quality standards (score: ${(anomalyResult.background_score * 100).toFixed(1)}%)`,
            score: anomalyResult.background_score,
            severity: anomalyResult.background_score >= 0.8 ? 'danger' : 'warning',
        });
    }

    // Check counterfeit
    if (anomalyResult.is_counterfeit || anomalyResult.counterfeit_score >= THRESHOLDS.counterfeit) {
        warnings.push({
            type: 'Potential Counterfeit',
            message: `This product may be a counterfeit (score: ${(anomalyResult.counterfeit_score * 100).toFixed(1)}%)`,
            score: anomalyResult.counterfeit_score,
            severity: 'danger',
        });
    }

    if (warnings.length === 0) {
        return (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-green-700 font-medium">No anomalies detected</span>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {warnings.map((warning, index) => (
                <div
                    key={index}
                    className={`border rounded-lg p-4 ${
                        warning.severity === 'danger'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-yellow-50 border-yellow-200'
                    }`}
                >
                    <div className="flex items-start">
                        {warning.severity === 'danger' ? (
                            <svg className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        ) : (
                            <svg className="w-5 h-5 text-yellow-500 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        )}
                        <div className="flex-1">
                            <h4 className={`font-semibold ${warning.severity === 'danger' ? 'text-red-800' : 'text-yellow-800'}`}>
                                ⚠️ {warning.type}
                            </h4>
                            <p className={`text-sm mt-1 ${warning.severity === 'danger' ? 'text-red-700' : 'text-yellow-700'}`}>
                                {warning.message}
                            </p>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default AnomalyWarning;
