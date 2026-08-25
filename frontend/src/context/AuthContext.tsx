import React, { createContext, useContext, useState, useEffect } from 'react'
import { setAuthToken } from '../api'

type AuthContextType = {
  token: string | null
  user: any | null
  login: (token: string, user?: any) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('ns_token'))
  const [user, setUser] = useState<any | null>(null)

  useEffect(() => {
    setAuthToken(token)
    if (token) {
      localStorage.setItem('ns_token', token)
    } else {
      localStorage.removeItem('ns_token')
    }
  }, [token])

  const login = (t: string, u?: any) => {
    setToken(t)
    if (u) setUser(u)
  }
  const logout = () => {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
