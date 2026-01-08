SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    /* Process Tracking (Security Channel) */
    '%EventId: 4688,%, Channel: Security,%', -- A new process has been created (Program execution)
    '%EventId: 4689,%, Channel: Security,%', -- A process has exited
    '%EventId: 4696,%, Channel: Security,%', -- A primary token was assigned to a process
    '%EventId: 4698,%, Channel: Security,%', -- A scheduled task was created
    '%EventId: 4700,%, Channel: Security,%', -- A scheduled task was enabled

    /* Service & System Control (System Channel) */
    '%EventId: 7036,%, Channel: System,%',   -- A service status was changed (Started/Stopped)
    '%EventId: 7040,%, Channel: System,%',   -- Service start type changed
    '%EventId: 7045,%, Channel: System,%'    -- A new service was installed
])
ORDER BY "time"