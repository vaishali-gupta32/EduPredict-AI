import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Users, AlertTriangle, TrendingUp, BookOpen, AlertCircle } from 'lucide-react'
import client from '../api/client'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const RISK_COLORS = { 'High': '#22c55e', 'Medium': '#f59e0b', 'At Risk': '#ef4444' }

export default function DashboardPage() {
    const navigate = useNavigate()
    const [filters, setFilters] = useState({ risk: '', department: '', semester: '' })
    const [page, setPage] = useState(1)

    const { data, isLoading, error } = useQuery({
        queryKey: ['students', filters, page],
        queryFn: async () => {
            const params = { page, limit: 20, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
            const { data } = await client.get('/students', { params })
            return data
        },
    })

    const { data: metricsData } = useQuery({
        queryKey: ['model-metrics'],
        queryFn: async () => { const { data } = await client.get('/model/metrics'); return data },
    })

    // Cohort stats from current page data (for quick counts)
    const students = data?.data || []
    const total = data?.total || 0
    const atRiskCount = students.filter(s => s.performance_category === 'At Risk').length
    const highCount = students.filter(s => s.performance_category === 'High').length
    const mediumCount = students.filter(s => s.performance_category === 'Medium').length

    // Pie chart data
    const pieData = [
        { name: 'High', value: highCount },
        { name: 'Medium', value: mediumCount },
        { name: 'At Risk', value: atRiskCount },
    ].filter(d => d.value > 0)

    // Bar chart: group by department
    const deptMap = {}
    students.forEach(s => {
        if (!s.department) return
        if (!deptMap[s.department]) deptMap[s.department] = { dept: s.department, at_risk: 0 }
        if (s.performance_category === 'At Risk') deptMap[s.department].at_risk++
    })
    const barData = Object.values(deptMap).sort((a, b) => b.at_risk - a.at_risk)

    if (isLoading) return <LoadingSpinner message="Loading dashboard..." />
    if (error) return <p className="text-red-400 text-center py-10">Failed to load data.</p>

    return (
        <div className="space-y-6">
            {/* Drift Warning */}
            {metricsData?.model_drift_warning && (
                <div className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl px-4 py-3">
                    <AlertCircle size={18} />
                    <span className="text-sm font-medium">Model drift detected. Consider retraining the model.</span>
                </div>
            )}

            <div>
                <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
                <p className="text-slate-400 text-sm mt-1">Cohort performance overview and student risk tracking</p>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { label: 'Total Students (Page)', value: students.length, icon: Users, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
                    { label: 'At Risk', value: atRiskCount, icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10' },
                    { label: 'Medium Performers', value: mediumCount, icon: TrendingUp, color: 'text-amber-400', bg: 'bg-amber-500/10' },
                    { label: 'High Performers', value: highCount, icon: BookOpen, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                ].map(({ label, value, icon: Icon, color, bg }) => (
                    <div key={label} className="stat-card">
                        <div className={`inline-flex p-2 rounded-lg ${bg} w-fit mb-2`}>
                            <Icon size={20} className={color} />
                        </div>
                        <p className={`text-2xl font-bold ${color}`}>{value}</p>
                        <p className="text-xs text-slate-500">{label}</p>
                    </div>
                ))}
            </div>

            {/* Charts */}
            {students.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6">
                    <div className="card">
                        <h3 className="section-title">Performance Distribution</h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                                    {pieData.map(entry => (
                                        <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="card">
                        <h3 className="section-title">At-Risk by Department</h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={barData}>
                                <XAxis dataKey="dept" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0' }} />
                                <Bar dataKey="at_risk" fill="#ef4444" radius={[4, 4, 0, 0]} name="At Risk" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Filters + Table */}
            <div className="card">
                <div className="flex flex-wrap gap-3 mb-4">
                    <select className="input !w-auto text-sm py-2" value={filters.risk} onChange={e => { setFilters(f => ({ ...f, risk: e.target.value })); setPage(1) }}>
                        <option value="">All Risk Levels</option>
                        <option>High</option>
                        <option>Medium</option>
                        <option value="At Risk">At Risk</option>
                    </select>
                    <input className="input !w-auto text-sm py-2" placeholder="Department" value={filters.department} onChange={e => { setFilters(f => ({ ...f, department: e.target.value })); setPage(1) }} />
                    <select className="input !w-auto text-sm py-2" value={filters.semester} onChange={e => { setFilters(f => ({ ...f, semester: e.target.value })); setPage(1) }}>
                        <option value="">All Semesters</option>
                        {[1, 2, 3, 4, 5, 6, 7, 8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>
                    {(filters.risk || filters.department || filters.semester) && (
                        <button className="btn-secondary text-sm py-2" onClick={() => { setFilters({ risk: '', department: '', semester: '' }); setPage(1) }}>Clear</button>
                    )}
                    <span className="ml-auto text-sm text-slate-400 self-center">Total: {total}</span>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full">
                        <thead>
                            <tr>
                                {['Student ID', 'Dept', 'Sem', 'Risk Level', 'Dropout Prob.', 'Last Prediction'].map(h => (
                                    <th key={h} className="table-header text-left">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {students.length === 0 && (
                                <tr><td colSpan={6} className="text-center text-slate-500 py-10 text-sm">No students found. Upload a CSV to get started.</td></tr>
                            )}
                            {students.map(s => (
                                <tr key={s.student_id} className="table-row" onClick={() => navigate(`/students/${s.student_id}`)}>
                                    <td className="table-cell font-mono text-indigo-400">{s.student_id}</td>
                                    <td className="table-cell">{s.department || '—'}</td>
                                    <td className="table-cell">{s.semester || '—'}</td>
                                    <td className="table-cell"><RiskBadge category={s.performance_category} /></td>
                                    <td className="table-cell">
                                        {s.dropout_probability != null ? (
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 bg-slate-800 rounded-full h-1.5 max-w-[80px]">
                                                    <div className="bg-gradient-to-r from-amber-500 to-red-500 h-1.5 rounded-full" style={{ width: `${Math.round(s.dropout_probability * 100)}%` }} />
                                                </div>
                                                <span>{(s.dropout_probability * 100).toFixed(0)}%</span>
                                            </div>
                                        ) : '—'}
                                    </td>
                                    <td className="table-cell text-slate-500 text-xs">
                                        {s.predicted_at ? new Date(s.predicted_at).toLocaleDateString() : '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {total > 20 && (
                    <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-800">
                        <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Previous</button>
                        <span className="text-sm text-slate-400">Page {page} of {Math.ceil(total / 20)}</span>
                        <button className="btn-secondary text-sm" disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(p => p + 1)}>Next →</button>
                    </div>
                )}
            </div>
        </div>
    )
}
