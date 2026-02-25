import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Navbar from './Navbar'

export default function ProtectedRoute() {
    const { isAuthenticated } = useAuth()
    if (!isAuthenticated) return <Navigate to="/login" replace />
    return (
        <div className="min-h-screen flex flex-col bg-[#0a0a14]">
            <Navbar />
            <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
                <Outlet />
            </main>
        </div>
    )
}
