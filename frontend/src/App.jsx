import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import StudentDetailPage from './pages/StudentDetailPage'
import UploadPage from './pages/UploadPage'
import ModelHealthPage from './pages/ModelHealthPage'

export default function App() {
    return (
        <AuthProvider>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route element={<ProtectedRoute />}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/students/:id" element={<StudentDetailPage />} />
                    <Route path="/upload" element={<UploadPage />} />
                    <Route path="/model-health" element={<ModelHealthPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </AuthProvider>
    )
}
