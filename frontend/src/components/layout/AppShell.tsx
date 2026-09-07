import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

type AppShellProps = {
  children: ReactNode
  onConnectDatabase: () => void
}

function AppShell({
  children,
  onConnectDatabase,
}: AppShellProps) {
  return (
    <div
      className="
        flex
        h-screen
        overflow-hidden
        bg-[var(--background)]
        text-[var(--text-primary)]
      "
    >
      <Sidebar
        onConnectDatabase={
          onConnectDatabase
        }
      />

      <div
        className="
          flex
          min-w-0
          flex-1
          flex-col
        "
      >
        <TopBar />
        {children}
      </div>
    </div>
  )
}

export default AppShell