import { createContext, useContext, useReducer, useEffect } from 'react'

const AuthContext = createContext(null)

const initialState = {
    user: null,
    token: null,
    isAuthenticated: false,
}

function authReducer(state, action) {
    switch (action.type) {
        case 'LOGIN':
            return {
                user: action.payload.user,
                token: action.payload.token,
                isAuthenticated: true,
            }
        case 'LOGOUT':
            return initialState
        default:
            return state
    }
}

export function AuthProvider({ children }) {
    const [state, dispatch] = useReducer(authReducer, initialState)

    // Restore session from localStorage on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token')
        const user = localStorage.getItem('user')
        if (token && user) {
            dispatch({ type: 'LOGIN', payload: { token, user: JSON.parse(user) } })
        }
    }, [])

    const login = (token, user) => {
        localStorage.setItem('access_token', token)
        localStorage.setItem('user', JSON.stringify(user))
        dispatch({ type: 'LOGIN', payload: { token, user } })
    }

    const logout = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        dispatch({ type: 'LOGOUT' })
    }

    return (
        <AuthContext.Provider value={{ ...state, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
    return ctx
}
