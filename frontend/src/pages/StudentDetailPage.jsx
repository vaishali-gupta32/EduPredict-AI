import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'
import { ArrowLeft, User, BookOpen, AlertTriangle } from 'lucide-react'
import client from '../api/client'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const IMPACT_COLOR = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#22c55e' }

export default function StudentDetailPage() {
    const { id } = useParams()
    const navigate = useNavigate()

    const { data: student, isLoading, error } = useQuery({
        queryKey: ['student', id],
        queryFn: async () => { const { data } = await client.get(`/students/${id}`); return data },
    })

    if (isLoading) return <LoadingSpinner message="Loading student profile..." />
    if (error) return <p className="text-red-400 text-center py-10">Student not found.</p>

    const pred = student.latest_prediction
    const dropoutPct = pred ? Math.round(pred.dropout_probability * 100) : 0
    const gaugeData = [{ value: dropoutPct, fill: dropoutPct > 60 ? '#ef4444' : dropoutPct > 35 ? '#f59e0b' : '#22c55e' }]
    const shapData = (pred?.top_factors || []).map(f => ({
        name: f.feature.replace(/_/g, ' '),
        value: f.value,
        impact: f.impact,
        fill: IMPACT_COLOR[f.impact] || '#6366f1',
    }))

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button onClick={() => navigate(-1)} className="p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors">
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-xl font-bold text-slate-100 font-mono">{student.student_id}</h1>
                    <p className="text-slate-400 text-sm">{student.department || '—'} · Semester {student.semester || '—'} · Age {student.age || '—'}</p>
                </div>
                {pred && <div className="ml-auto"><RiskBadge category={pred.performance_category} /></div>}
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Dropout Gauge */}
                <div className="card flex flex-col items-center justify-center">
                    <h3 className="section-title self-start">Dropout Risk</h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <RadialBarChart cx="50%" cy="80%" startAngle={180} endAngle={0} innerRadius="60%" outerRadius="100%" data={gaugeData}>
                            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                            <RadialBar dataKey="value" cornerRadius={8} background={{ fill: '#1e293b' }} />
                        </RadialBarChart>
                    </ResponsiveContainer>
                    <p className="text-4xl font-bold mt-[-30px]" style={{ color: gaugeData[0]?.fill }}>{dropoutPct}%</p>
                    <p className="text-slate-400 text-sm mt-1">Dropout Probability</p>
                    {pred && <p className="text-slate-500 text-xs mt-1">Confidence: {(pred.confidence * 100).toFixed(1)}%</p>}
                </div>

                {/* SHAP Factors */}
                <div className="card">
                    <h3 className="section-title">Top Risk Factors</h3>
                    {shapData.length > 0 ? (
                        <>
                            <ResponsiveContainer width="100%" height={160}>
                                <BarChart layout="vertical" data={shapData} margin={{ left: 0, right: 10 }}>
                                    <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                                    <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0', fontSize: '12px' }} />
                                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                        {shapData.map((entry, i) => (
                                            <rect key={i} fill={entry.fill} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                            <div className="mt-2 space-y-1">
                                {shapData.map(f => (
                                    <div key={f.name} className="flex justify-between items-center text-xs">
                                        <span className="text-slate-400 capitalize">{f.name}</span>
                                        <span className="font-mono" style={{ color: IMPACT_COLOR[f.impact] }}>{f.impact}</span>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : <p className="text-slate-500 text-sm">No SHAP data available.</p>}
                </div>

                {/* Interventions */}
                <div className="card">
                    <h3 className="section-title flex items-center gap-2"><AlertTriangle size={16} className="text-amber-400" /> Interventions</h3>
                    <div className="space-y-2">
                        {(pred?.recommended_interventions || []).map((intervention, i) => (
                            <div key={i} className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                                <span className="text-amber-400 mt-0.5 text-xs font-bold">#{i + 1}</span>
                                <span className="text-slate-300 text-sm">{intervention}</span>
                            </div>
                        ))}
                        {(!pred?.recommended_interventions?.length) && (
                            <p className="text-slate-500 text-sm">No interventions recommended.</p>
                        )}
                    </div>

                    {/* Student Info */}
                    <div className="mt-6 pt-4 border-t border-slate-800">
                        <h4 className="text-sm font-semibold text-slate-300 mb-2 flex gap-2 items-center"><User size={14} /> Profile</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            {[
                                ['Gender', student.gender],
                                ['Department', student.department],
                                ['Semester', student.semester],
                                ['Age', student.age],
                            ].map(([label, val]) => (
                                <div key={label}>
                                    <span className="text-slate-500">{label}: </span>
                                    <span className="text-slate-300">{val || '—'}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Latest Prediction Feature Snapshot */}
            {pred && (
                <div className="card">
                    <h3 className="section-title flex items-center gap-2"><BookOpen size={16} className="text-indigo-400" /> Feature Snapshot (Latest Prediction)</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                        {[
                            ['Attendance', pred.top_factors?.[0]?.value != null ? null : null, 'attendance_pct'],
                            ['GPA', null, 'semester_gpa'],
                            ['Prev GPA', null, 'prev_semester_gpa'],
                            ['Assignments', null, 'assignment_score_avg'],
                            ['Internal', null, 'internal_marks_avg'],
                            ['Study Hrs', null, 'study_hours_per_week'],
                            ['Backlogs', null, 'backlogs'],
                        ].map(([label]) => (
                            <div key={label} className="text-center bg-slate-800/50 rounded-xl p-3">
                                <p className="text-xs text-slate-500 mb-1">{label}</p>
                                <p className="text-lg font-bold text-slate-200">—</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-slate-600 mt-2">Feature values from raw prediction snapshot.</p>
                </div>
            )}

            {/* Prediction History */}
            {student.prediction_history?.length > 0 && (
                <div className="card">
                    <h3 className="section-title">Prediction History</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr>
                                    {['Performance', 'Dropout Risk', 'Model Version', 'Date'].map(h => (
                                        <th key={h} className="table-header text-left">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {student.prediction_history.map(p => (
                                    <tr key={p.id} className="border-b border-slate-800">
                                        <td className="table-cell"><RiskBadge category={p.performance_category} /></td>
                                        <td className="table-cell">{(p.dropout_probability * 100).toFixed(1)}%</td>
                                        <td className="table-cell font-mono text-xs text-slate-500">{p.model_version || '—'}</td>
                                        <td className="table-cell text-xs text-slate-500">{p.predicted_at ? new Date(p.predicted_at).toLocaleString() : '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
