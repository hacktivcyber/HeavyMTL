SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    /* Terminal Services / RDP Session Activity */
    '%EventId: 21,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Remote Desktop Services: Session logon succeeded
    '%EventId: 22,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Remote Desktop Services: Shell start notification received
    '%EventId: 23,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Remote Desktop Services: Session logoff succeeded
    '%EventId: 24,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Remote Desktop Services: Session has been disconnected
    '%EventId: 25,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%'  -- Remote Desktop Services: Session reconnection succeeded
	'%EventId: 39,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Session disconnected by session manager (user or timeout)
    '%EventId: 40,%, Channel: Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,%',   -- Session disconnected by local/remote disconnect request
    '%EventId: 1149,%, Channel: Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational,%', -- Remote Desktop Services: User authentication succeeded

    /* RDP Operational / Driver Errors */
    '%EventId: 1024,%, Channel: Microsoft-Windows-TerminalServices-RDPClient/Operational,%', -- RDP Client: Connection error or protocol failure
    '%EventId: 1102,%, Channel: Microsoft-Windows-TerminalServices-RDPClient/Operational,%', --  RDP client has initiated a multi-transport connection to a remote server

    /* Logon / Logoff / Privileges */
    '%EventId: 4624,%, Channel: Security,%', -- An account was successfully logged on
    '%EventId: 4625,%, Channel: Security,%', -- An account failed to log on
    '%EventId: 4634,%, Channel: Security,%', -- An account was logged off
    '%EventId: 4647,%, Channel: Security,%', -- User initiated logoff
    '%EventId: 4648,%, Channel: Security,%', -- A logon was attempted using explicit credentials
    '%EventId: 4672,%, Channel: Security,%', -- Special privileges assigned to new logon (Admin rights)
    
    /* Session Reconnect / Disconnect (TS) */
    '%EventId: 4778,%, Channel: Security,%', -- A session was reconnected to a Window Station
    '%EventId: 4779,%, Channel: Security,%', -- A session was disconnected from a Window Station

    /* System Events */
    '%EventId: 41,%, Channel: System,%'  -- The system shutdown unexpectedly (Power loss/Crash)
])
ORDER BY "time"