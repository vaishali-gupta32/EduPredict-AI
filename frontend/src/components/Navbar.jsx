import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LayoutDashboard, Upload, Activity, LogOut, GraduationCap } from 'lucide-react'

const links = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Data', icon: Upload },
    { to: '/model-health', label: 'Model Health', icon: Activity },
]

export default function Navbar() {
    const { user, logout } = useAuth()
    const { pathname } = useLocation()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <nav className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center gap-2 text-indigo-400 font-bold text-lg">
                <GraduationCap size={24} />
                <span className="hidden sm:block">EduPredict AI</span>
            </Link>

            {/* Nav Links */}
            <div className="flex items-center gap-1">
                {links.map(({ to, label, icon: Icon }) => (
                    <Link
                        key={to}
                        to={to}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${pathname === to
                                ? 'bg-indigo-600/20 text-indigo-400'
                                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                            }`}
                    >
                        <Icon size={16} />
                        <span className="hidden md:block">{label}</span>
                    </Link>
                ))}
            </div>

            {/* User + Logout */}
            <div className="flex items-center gap-3">
                {user && (
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-slate-200">{user.full_name || user.email}</p>
                        <p className="text-xs text-slate-400 capitalize">{user.role}</p>
                    </div>
                )}
                <button
                    onClick={handleLogout}
                    className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all"
                    title="Logout"
                >
                    <LogOut size={18} />
                </button>
            </div>
        </nav>
    )
}
