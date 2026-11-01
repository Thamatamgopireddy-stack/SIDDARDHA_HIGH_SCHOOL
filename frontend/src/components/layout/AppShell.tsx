import {
  BookOpenCheck,
  ChevronDown,
  ClipboardCheck,
  GraduationCap,
  LayoutDashboard,
  Menu,
  School,
  ShieldCheck,
  UserRound,
  UsersRound,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { getData } from '../../lib/api'
import { appConfig } from '../../lib/env'
import type { Profile } from '../../lib/types'
import { useAuth } from '../../features/auth/useAuth'
import { usePermissions } from '../../hooks/usePermissions'

const navigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/students', label: 'Students', icon: GraduationCap, permission: 'students:read' },
  { to: '/teachers', label: 'Teachers', icon: UsersRound, permission: 'teachers:read' },
  { to: '/admissions', label: 'Admissions', icon: BookOpenCheck, permission: 'admissions:read' },
  { to: '/attendance', label: 'Attendance', icon: ClipboardCheck, permission: 'attendance:read' },
  { to: '/profile', label: 'My profile', icon: UserRound },
]

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [signOutError, setSignOutError] = useState('')
  const location = useLocation()
  const { signOut, accountStatus } = useAuth()
  const profileQuery = useQuery({
    queryKey: ['profile'],
    queryFn: () => getData<Profile>('/auth/me'),
  })
  const permissionsQuery = usePermissions()
  const profile = profileQuery.data
  const pageTitle = navigation.find((item) => location.pathname.startsWith(item.to))?.label ?? 'EduCore'
  const visibleNavigation = navigation.filter(
    (item) => !item.permission || permissionsQuery.data?.includes(item.permission),
  )
  const navigationItems = accountStatus?.portal === 'super_admin'
    ? [...visibleNavigation, { to: '/super-admin', label: 'Access approvals', icon: ShieldCheck }]
    : visibleNavigation

  const leave = async () => {
    setSignOutError('')
    try {
      await signOut()
    } catch (error) {
      setSignOutError(error instanceof Error ? error.message : 'Could not sign out')
    }
  }

  return (
    <div className="app-shell">
      {sidebarOpen && <button aria-label="Close navigation" className="sidebar-scrim" onClick={() => setSidebarOpen(false)} type="button" />}
      <aside className={`sidebar${sidebarOpen ? ' sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><School size={21} /></div>
          <div><div className="brand-name">{appConfig.appName}</div><div className="brand-subtitle">School management</div></div>
          <button aria-label="Close navigation" className="icon-button mobile-menu" onClick={() => setSidebarOpen(false)} type="button"><X size={18} /></button>
        </div>
        <div className="nav-caption">Workspace</div>
        <nav aria-label="Main navigation" className="nav-list">
          {navigationItems.map(({ to, label, icon: Icon }) => (
            <NavLink className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} key={to} onClick={() => setSidebarOpen(false)} to={to}>
              <Icon size={17} strokeWidth={1.9} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="side-bottom">
          <div className="school-card"><div className="school-label">School</div><div className="school-value">{appConfig.schoolName}</div></div>
          {signOutError && <div className="field-error" role="alert">{signOutError}</div>}
          <button className="nav-link" onClick={() => void leave()} type="button"><X size={17} /> Sign out</button>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button aria-label="Open navigation" className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} type="button"><Menu size={19} /></button>
            <div><div className="topbar-kicker">{appConfig.schoolName}</div><div className="topbar-title">{pageTitle}</div></div>
          </div>
          <div className="topbar-actions">
            <NavLink aria-label="My profile" className="icon-button" to="/profile"><UserRound size={17} /></NavLink>
            <NavLink className="user-chip" to="/profile">
              <div className="avatar">{initials(profile?.display_name || profile?.email || 'User')}</div>
              <div><div className="user-name">{profile?.display_name || profile?.email || 'My account'}</div><div className="user-role">School account</div></div>
              <ChevronDown size={14} color="#98a2b3" />
            </NavLink>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  )
}

function initials(value: string) {
  return value.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('')
}
