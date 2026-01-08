SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    '%EventId: 104,%, Channel: System,%', -- The System audit log was cleared (Critical System Event)
    '%EventId: 104,%, Channel: Setup,%', -- The Setup audit log was cleared
    '%EventId: 1102,%, Channel: Security,%', -- The Security audit log was cleared (Critical Security Event)
    '%EventId: 4715,%, Channel: Security,%' -- The audit policy was changed
])
ORDER BY "time"