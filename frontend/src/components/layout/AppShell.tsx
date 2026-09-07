import type { ReactNode } from 'react'

import type {
  ActiveConnection,
} from '../database/ConnectDatabaseDialog'

import Sidebar from './Sidebar'
import TopBar from './TopBar'

type AppShellProps = {
  children: ReactNode
  onConnectDatabase: () => void
  connection: ActiveConnection | null
}

function AppShell({
  children,
  onConnectDatabase,
  connection,
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
        connection={connection}
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