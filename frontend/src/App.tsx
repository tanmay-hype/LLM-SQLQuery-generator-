import { useState } from 'react'

import AppShell from './components/layout/AppShell'
import ConnectDatabaseDialog, {
  type ActiveConnection,
} from './components/database/ConnectDatabaseDialog'
import QueryWorkspace from './components/query/QueryWorkspace'

function App() {
  const [
    isConnectDialogOpen,
    setIsConnectDialogOpen,
  ] = useState(false)

  const [
    connection,
    setConnection,
  ] = useState<ActiveConnection | null>(
    null,
  )

  return (
    <>
      <AppShell
        connection={connection}
        onConnectDatabase={() =>
          setIsConnectDialogOpen(true)
        }
      >
        <QueryWorkspace />
      </AppShell>

      <ConnectDatabaseDialog
        open={isConnectDialogOpen}
        onClose={() =>
          setIsConnectDialogOpen(false)
        }
        onConnected={
          setConnection
        }
      />
    </>
  )
}

export default App