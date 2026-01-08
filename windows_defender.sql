--- Disabling Windows Defender / Malware Detection
SELECT * FROM master_timeline
WHERE ("time" > '2025-12-01' AND "time" < '2025-12-20') AND
description ILIKE ANY (ARRAY[
    /* Malware Detection Events */
    '%EventId: 1006,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Malware found
    '%EventId: 1007,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Malware action taken
    '%EventId: 1008,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Error taking action
    '%EventId: 1015,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Suspicious behavior detected
    '%EventId: 1116,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Malware detected
    '%EventId: 1117,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Action taken (Success)
    '%EventId: 1118,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Action taken (Failure)
    '%EventId: 1119,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Action taken (Critical Failure)
    
    /* Protection Failures & CFA */
    '%EventId: 1127,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Controlled Folder Access block
    '%EventId: 3002,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Real-time Protection failure
    '%EventId: 3007,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Recovery from failure

    /* Tampering & Disabling (High Priority for Security) */
    '%EventId: 5001,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Real-time Protection Disabled
    '%EventId: 5004,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Configuration change
    '%EventId: 5007,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Platform configuration changed
    '%EventId: 5008,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Engine failed
    '%EventId: 5010,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Scanning disabled
    '%EventId: 5012,%, Channel: Microsoft-Windows-Windows Defender/Operational,%', -- Virus scanning disabled
    '%EventId: 5013,%, Channel: Microsoft-Windows-Windows Defender/Operational,%',  -- Tamper protection block
	
	/* Service Control Manager (System Log) */
	'%EventId: 7036,%, Channel: System,%', -- Service status changed (Look for 'Microsoft Defender Antivirus Service')
	
	/* Registry Auditing (Security Log) */
	'%EventId: 4657,%, Channel: Security,%' -- A registry value was modified (Look for 'DisableAntiSpyware' or 'DisableRealtimeMonitoring')])
])
ORDER BY "time"