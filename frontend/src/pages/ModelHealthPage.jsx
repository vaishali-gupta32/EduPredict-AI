import { useQuery } from '@tanstack/react-query'
import { AlertCircle, CheckCircle, Award } from 'lucide-react'
import client from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'

const MetricCard = ({ label, value, color, target, suffix = '' }) => {
    const pct = Math.min(100, Math.round((value / target) * 100))
    return (
        <div className="stat-card">
            <p className="text-xs text-slate-500 mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{(value * 100).toFixed(1)}{suffix}</p>
            <div className="mt-2 bg-slate-800 rounded-full h-1.5">
                <div className={`h-1.5 rounded-full transition-all`} style={{ width: `${pct}%`, background: color.includes('green') || color.includes('emerald') ? '#22c55e' : color.includes('amber') ? '#f59e0b' : '#6366f1' }} />
            </div>
            <p className="text-xs text-slate-600 mt-1">Target: {(target * 100).toFixed(0)}%</p>
        </div>
    )
}

export default function ModelHealthPage() {
    const { data: metrics, isLoading } = useQuery({
        queryKey: ['model-metrics'],
        queryFn: async () => { const { data } = await client.get('/model/metrics'); return data },
        refetchInterval: 60_000,
    })

    if (isLoading) return <LoadingSpinner message="Loading model metrics..." />

    const cm = metrics?.confusion_matrix || []
    const labels = ['High', 'Medium', 'At Risk']

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-100">Model Health</h1>
                    <p className="text-slate-400 text-sm mt-1">Champion model performance metrics and drift monitoring</p>
                </div>
                {metrics && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700">
                        <Award size={16} className="text-indigo-400" />
                        <div>
                            <p className="text-xs text-slate-400">Champion Model</p>
                            <p className="text-sm font-semibold text-slate-200">{metrics.model_name}</p>
                        </div>
                        <span className="text-xs font-mono text-slate-500 ml-2">{metrics.model_version}</span>
                    </div>
                )}
            </div>

            {/* Drift Warning */}
            {metrics?.model_drift_warning && (
                <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3">
                    <AlertCircle size={18} />
                    <div>
                        <p className="font-medium text-sm">Model Drift Detected</p>
                        <p className="text-xs opacity-80">Performance metrics have dropped below acceptable thresholds. Retraining recommended.</p>
                    </div>
                </div>
            )}

            {!metrics?.model_drift_warning && metrics && (
                <div className="flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl px-4 py-3">
                    <CheckCircle size={18} />
                    <p className="font-medium text-sm">Model is performing within acceptable thresholds</p>
                </div>
            )}

            {/* Metric Cards */}
            {metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard label="Accuracy" value={metrics.accuracy} target={0.88} color="text-indigo-400" suffix="%" />
                    <MetricCard label="ROC-AUC" value={metrics.roc_auc} target={0.88} color="text-purple-400" suffix="%" />
                    <MetricCard label="F1 (At Risk)" value={metrics.f1_at_risk} target={0.82} color="text-amber-400" suffix="%" />
                    <MetricCard label="Precision" value={metrics.precision} target={0.80} color="text-emerald-400" suffix="%" />
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
                {/* Additional metrics */}
                {metrics && (
                    <div className="card">
                        <h3 className="section-title">Full Metrics</h3>
                        <div className="space-y-3">
                            {[
                                ['Accuracy', metrics.accuracy, '≥ 88%'],
                                ['ROC-AUC', metrics.roc_auc, '≥ 88%'],
                                ['F1 Score (At Risk)', metrics.f1_at_risk, '≥ 82%'],
                                ['F1 Score (Macro)', metrics.f1_macro, '—'],
                                ['Precision', metrics.precision, '≥ 80%'],
                                ['Recall', metrics.recall, '—'],
                            ].map(([label, val, target]) => val != null && (
                                <div key={label} className="flex justify-between items-center">
                                    <span className="text-sm text-slate-400">{label}</span>
                                    <div className="text-right">
                                        <span className="text-sm font-semibold text-slate-200">{(val * 100).toFixed(2)}%</span>
                                        <span className="text-xs text-slate-600 ml-2">(target {target})</span>
                                    </div>
                                </div>
                            ))}
                            <div className="pt-2 border-t border-slate-800">
                                <div className="flex justify-between text-xs text-slate-500">
                                    <span>Trained at</span>
                                    <span>{metrics.trained_at ? new Date(metrics.trained_at).toLocaleString() : '—'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Confusion Matrix */}
                {cm.length > 0 && (
                    <div className="card">
                        <h3 className="section-title">Confusion Matrix</h3>
                        <div className="overflow-x-auto">
                            <table className="text-xs">
                                <thead>
                                    <tr>
                                        <th className="px-2 py-1 text-slate-500 text-right">Actual ↓ / Pred →</th>
                                        {labels.slice(0, cm.length).map(l => (
                                            <th key={l} className="px-3 py-2 text-slate-400 font-semibold">{l}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {cm.map((row, ri) => (
                                        <tr key={ri}>
                                            <td className="px-2 py-2 text-slate-400 font-semibold text-right pr-4">{labels[ri]}</td>
                                            {row.map((val, ci) => (
                                                <td
                                                    key={ci}
                                                    className={`px-3 py-2 text-center font-mono rounded text-sm font-bold ${ri === ci ? 'bg-indigo-600/30 text-indigo-300' : 'text-slate-400'
                                                        }`}
                                                >
                                                    {val}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <p className="text-xs text-slate-600 mt-2 italic">Diagonal = correct predictions</p>
                        </div>
                    </div>
                )}

                {!metrics && (
                    <div className="card col-span-2 text-center py-10">
                        <AlertCircle size={32} className="text-amber-400 mx-auto mb-3" />
                        <p className="text-slate-300 font-medium">No model trained yet</p>
                        <p className="text-slate-500 text-sm mt-1">Run <code className="bg-slate-800 px-1 rounded">python ml/train.py</code> from the backend directory.</p>
                    </div>
                )}
            </div>
        </div>
    )
}
