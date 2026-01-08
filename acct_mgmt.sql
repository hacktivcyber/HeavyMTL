SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    /* User Account Management (Security Channel) */
    '%EventId: 4720,%, Channel: Security,%', -- User created
    '%EventId: 4722,%, Channel: Security,%', -- User enabled
    '%EventId: 4723,%, Channel: Security,%', -- User changed password
    '%EventId: 4724,%, Channel: Security,%', -- User reset password
    '%EventId: 4725,%, Channel: Security,%', -- User disabled
    '%EventId: 4726,%, Channel: Security,%', -- User deleted
    '%EventId: 4738,%, Channel: Security,%', -- User changed (general)
    '%EventId: 4740,%, Channel: Security,%', -- User locked out
    '%EventId: 4767,%, Channel: Security,%', -- User unlocked
    '%EventId: 4781,%, Channel: Security,%', -- Account name changed

    /* Group Management (Security Channel) */
    '%EventId: 4727,%, Channel: Security,%', -- Security group created
    '%EventId: 4728,%, Channel: Security,%', -- Member added to security group
    '%EventId: 4729,%, Channel: Security,%', -- Member removed from security group
    '%EventId: 4730,%, Channel: Security,%', -- Security group deleted
    '%EventId: 4731,%, Channel: Security,%', -- Local group created
    '%EventId: 4732,%, Channel: Security,%', -- Member added to local group
    '%EventId: 4733,%, Channel: Security,%', -- Member removed from local group
    '%EventId: 4734,%, Channel: Security,%', -- Local group deleted
    '%EventId: 4735,%, Channel: Security,%', -- Local group changed
    '%EventId: 4737,%, Channel: Security,%', -- Security group changed
    '%EventId: 4754,%, Channel: Security,%', -- Universal group created
    '%EventId: 4755,%, Channel: Security,%', -- Universal group changed
    '%EventId: 4756,%, Channel: Security,%', -- Member added to universal group
    '%EventId: 4757,%, Channel: Security,%', -- Member removed from universal group
    '%EventId: 4758,%, Channel: Security,%', -- Universal group deleted
    '%EventId: 4764,%, Channel: Security,%'  -- Group type changed
])
ORDER BY "time"