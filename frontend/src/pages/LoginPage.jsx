import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'
import { GraduationCap, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPass, setShowPass] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const { data } = await client.post('/auth/login', { email, password })
            // Fetch user profile
            const meRes = await client.get('/auth/me', {
                headers: { Authorization: `Bearer ${data.access_token}` }
            })
            login(data.access_token, meRes.data)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#0a0a14] p-4">
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 via-transparent to-purple-900/20 pointer-events-none" />

            <div className="relative w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-4">
                        <GraduationCap size={32} className="text-indigo-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-100">EduPredict AI</h1>
                    <p className="text-slate-400 text-sm mt-1">Student Performance & Dropout Risk System</p>
                </div>

                {/* Card */}
                <div className="card">
                    <h2 className="text-lg font-semibold text-slate-100 mb-6">Sign in to your account</h2>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm mb-4">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Email Address</label>
                            <input
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                className="input"
                                placeholder="admin@college.edu"
                                required
                                autoFocus
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                            <div className="relative">
                                <input
                                    type={showPass ? 'text' : 'password'}
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    className="input pr-10"
                                    placeholder="••••••••"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPass(v => !v)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                                >
                                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        <button type="submit" disabled={loading} className="btn-primary w-full mt-2 py-3">
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="mt-6 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                        <p className="text-xs text-slate-500 font-medium mb-1">Demo Credentials</p>
                        <p className="text-xs text-slate-400">Admin: <span className="text-slate-300">admin@college.edu</span> / <span className="text-slate-300">Admin@1234</span></p>
                        <p className="text-xs text-slate-400">Viewer: <span className="text-slate-300">viewer@college.edu</span> / <span className="text-slate-300">Viewer@1234</span></p>
                    </div>
                </div>
            </div>
        </div>
    )
}
