--- Powershell & Remote Execution Artifacts
SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    /* PowerShell Engine & Scripting */
    '%EventId: 400,%, Channel: Windows PowerShell,%',
    '%EventId: 4104,%, Channel: Microsoft-Windows-PowerShell/Operational,%',
    '%EventId: 4103,%, Channel: Microsoft-Windows-PowerShell/Operational,%',
    '%EventId: 4688,%, Channel: Security,%',

    /* WinRM: Connection & Authentication */
    '%EventId: 161,%, Channel: Microsoft-Windows-WinRM/Operational,%', -- WinRM: Connection received from client
    '%EventId: 6,%, Channel: Microsoft-Windows-WinRM/Operational,%',   -- WinRM: Client authentication succeeded
    '%EventId: 142,%, Channel: Microsoft-Windows-WinRM/Operational,%', -- WinRM: WSMan Shell created (Remote session started)

    /* WinRM: Service & Listener Activity */
    '%EventId: 10148,%, Channel: System,%', -- WinRM service is listening for HTTP requests
    '%EventId: 10149,%, Channel: System,%'  -- WinRM service is listening for HTTPS requests
])
ORDER BY "time"