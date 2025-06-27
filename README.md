# HeavyMTL (Hacktivcybers Master TimeLiner)

HeavyMTL is a way to create a single master timeline from the output of the EZTools module in KAPE. It can process the following modules, which should be the complete amount called by EZTools.mkape (with the exception of sqlecmd.mkape):

- amcacheparser.mkape
- appcompatcacheparser.mkape
- evtxecmd.mkape
- jlecmd.mkape
- lecmd.mkape
- mftecmd.mkape
- pecmd.mkape
- rbcmd.mkape
- recentfilecacheparser.mkape
- recmd_DFIRBatch.mkape
- sbecmd.mkape
- srumecmd.mkape
- sumecmd.mkape
- WxTCmd.mkape

You will need to have some Python experience as it uses a fair amount python libraries. It is running under Python 3.12. If you are missing psycopg2, use psycopg2-binary (pip install psycopg2-binary).

## The command line args for CSV and postgres
### CSV
-i "\\diskstation\uploads\USC\ITP 375\Labs\KAPE\Case_1\Modules" -t "csv" -o "\\diskstation\uploads\USC\ITP 375\Labs\KAPE\Case_1"
### PostgreSQL
-i "\\diskstation\uploads\USC\ITP 375\Labs\KAPE\Case_1\Modules" -t postgres -d postgresql://postgres:postgres@localhost:5432/timeline -o "\\diskstation\uploads\USC\ITP 375\Labs\KAPE\Case_1"

Overall it goes fairly quickly. Parsing the results of $MFT & $J can make it take a few minutes (about 7 in testing). Without those it usually finishes in under 30 seconds. **YMMV**.

## Duplicate event artifacts with the same datetimes are grouped into a single master_timeline entry and uniquely coded:
- Jumplists, Linkfiles & RecentFileCache
  - SourceCreated [C]
  - SourceModified [M]
  - SourceAccessed [A]

- $MFT
  - Created0x10 [C1]
  - Created0x30 [C3]
  - LastModified0x10 [M1]
  - LastModified0x30 [M3]
  - LastRecordChange0x10 [R1]
  - LastRecordChange0x30 [R3]
  - LastAccess0x10 [A1]
  - LastAccess0x30 [A3]

- SUMdb
  - InsertDate [I]
  - LastAccess [L]

