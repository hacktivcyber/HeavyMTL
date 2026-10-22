select * from master_timeline
WHERE ("time" > '2026-01-05' AND "time" < '2026-01-06') and
description ILIKE ANY (ARRAY[
	'%TrackView%',
	'%AnyDesk%',
	'%Atera%',
	'%AsyncRAT%',
	'%BlackSuit%',
	'%Chisel%',
	'%ConnectWise%',
	'%ScreenConnect%',
	'%Chrome Remote Desktop%',
	'%DCRat%',
	'%FRP%',
	'%Fast Reverse Proxy%',
	'%Localtonet%',
	'%MeshCentral%',
	'%NetSupport Manager%',
	'%Ngrok%',
	'%QuasarRAT%',
	'%Quick Assist%',
	'%Remcos RAT%',
	'%RemotePC%',
	'%RustDesk%',
	'%Splashtop%',
	'%Tactical RMM%',
	'%Tailscale%',
	'%TeamViewer%',
	'%ZeroTier%'
])
ORDER BY "time"
