import os
import argparse
import pandas as pd
import psycopg2
from urllib.parse import urlparse
import logging
import time
import sys
import re

# TLN column names
TLN_COLUMNS = ["Time", "Source", "System", "User", "Description"]

# Mapping of EZTools CSV types to specific columns
CSV_MAPPINGS = {
    "*_Activity_PackageIDs.csv": {
        "time": "Expires",
        "source": lambda df: "WIN10_Timeline",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_RBCmd_Output.csv": {
        "time": "DeletedOn",
        "source": lambda df: "RecycleBin",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_NTUSER.csv": {
        "time": "LastWriteTime",
        "source": lambda df: "ShellBags",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_UsrClass.csv": {
        "time": "LastWriteTime",
        "source": lambda df: "ShellBags",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_PECmd_Output.csv": {
        "time": "LastRun",
        "source": lambda df: "PREFETCH",
        "system": "Volume0Name",
        "user": "UserName"
    },
    "*_*Destinations.csv": {
        "time_fields": [
            ("SourceCreated", "C"),
            ("SourceModified", "M"),
            ("SourceAccessed", "A")
        ],  # Multiple timestamps with prefixes
        "source": lambda df: "JumpList",
        "system": lambda df: "Unknown_System",
        "user": None
    },
    "*_LECmd_Output.csv": {
        "time_fields": [
            ("SourceCreated", "C"),
            ("SourceModified", "M"),
            ("SourceAccessed", "A")
        ],  # Multiple timestamps with prefixes
        "source": lambda df: "LinkFile",
        "system": lambda df: "Unknown_System",
        "user": None
    },
    "*_SrumECmd_*.csv": {  # Matches all SRUM-related files
        "time": "Timestamp",
        "source": lambda df: "SRUM",
        "system": lambda df: "Unknown_System",
        "user": lambda df: df.apply(
            lambda row: f"{row.get('UserName')} ({row.get('Sid')})" if pd.notna(row.get('UserName')) and pd.notna(row.get('Sid')) else "Unknown_User",
            axis=1
        )
    },
    "*_MFTECmd_\\$J_Output.csv": {  # Escaped $ for $J artifact files
        "time": "UpdateTimestamp",
        "source": lambda df: "$J",
        "system": lambda df: "Unknown_System",
        "user": lambda df: "Unknown_User"
    },
    "*_MFTECmd_\\$MFT_Output.csv": {  # Escaped $ for $MFT artifact files
        "time_fields": [
            ("Created0x10", "C1"),
            ("Created0x30", "C3"),
            ("LastModified0x10", "M1"),
            ("LastModified0x30", "M3"),
            ("LastRecordChange0x10", "R1"),
            ("LastRecordChange0x30", "R3"),
            ("LastAccess0x10", "A1"),
            ("LastAccess0x30", "A3")
        ],  # Multiple timestamps with prefixes
        "source": lambda df: "$MFT",
        "system": lambda df: "Unknown_System",
        "user": lambda df: "Unknown_User"
    },
    "*_SumECmd_DETAIL_ClientDetailed_Output.csv": {  # SUMdb ClientDetailed files
        "time_fields": [
            ("InsertDate", "I"),
            ("LastAccess", "L")
        ],  # Multiple timestamps with prefixes
        "source": lambda df: "SUMdb",
        "system": lambda df: df.get('IpAddress', "Unknown_System"),
        "user": lambda df: df.get('AuthenticatedUserName', "Unknown_User")
    },
    "*_RecentFileCacheParser_Output.csv": {  # RecentFileCacheParser files
        "time_fields": [
            ("SourceCreated", "C"),
            ("SourceModified", "M"),
            ("SourceAccessed", "A")
        ],  # Multiple timestamps with prefixes
        "source": lambda df: "RecentFileCache",
        "system": lambda df: "Unknown_Host",
        "user": lambda df: "Unknown_User"
    },
    "*_Amcache_*FileEntries.csv": {
        "time": "FileKeyLastWriteTimestamp",
        "source": lambda df: "AMCACHE",
        "system": lambda df: "Unknown_System",
        "user": None
    },
    "*_Windows10Creators_SYSTEM_AppCompatCache.csv": {
        "time": "LastModifiedTimeUTC",
        "source": lambda df: "AppCompatCache",
        "system": lambda df: "Unknown_System",
        "user": None
    },
    "*_Amcache_*.csv": {
        "time": "KeyLastWriteTimestamp",
        "source": lambda df: "AMCACHE",
        "system": lambda df: "Unknown_System",
        "user": None
    },
    "*_EvtxECmd_Output.csv": {
        "time": "TimeCreated",
        "source": lambda df: "EVTX",
        "system": "Computer",
        "user": "UserId"
    },
    "*_RunMRU__*_Users_*_NTUSER.DAT.csv": {
        "time": "OpenedOn",
        "source": lambda df: "RunMRU",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_RECmd_Batch_UserActivity_Output.csv": {
        "time": "LastWriteTimestamp",
        "source": lambda df: "REGISTRY",
        "system": lambda df: "Unknown_System",
        "user": None  # Extracted from HivePath
    },
    "*_UserAssist__*_Users_*_NTUSER.DAT.csv": {
        "time": "LastExecuted",
        "source": lambda df: "UserAssist",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
    "*_BamDam__*_Windows_System32_config_SYSTEM.csv": {
        "time": "ExecutionTime",
        "source": lambda df: "BamDam",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from BatchKeyPath
    },
    "*_RecentDocs__*_Users_*_NTUSER.DAT.csv": {
        "time": "ExtensionLastOpened",
        "source": lambda df: "RecentDocs",
        "system": lambda df: "Unknown_System",
        "user": None  # Parsed from filename
    },
}

def setup_logging(output_dir):
    """Configure logging to write to both a file and the console."""
    log_file = os.path.join(output_dir, "heavymtl.log")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Changed to DEBUG for detailed tracing

    logger.handlers = []

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def find_csv_files(root_dir):
    """Recursively find all EZTools CSVs in the input directory."""
    csv_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv"):
                for key in CSV_MAPPINGS:
                    # Convert pattern to regex, escaping special characters and handling wildcards
                    pattern = re.escape(key).replace(r"\*", ".*").replace(r"\\\$", r"\$")
                    if re.fullmatch(pattern, file, re.IGNORECASE):
                        logging.debug(f"Matched file {file} to pattern {pattern} (key: {key})")
                        csv_files.append(os.path.join(root, file))
                        break
                else:
                    logging.debug(f"No match for file {file}")
    return csv_files

def parse_csv_to_tln(csv_path, files_remaining):
    """Parse a single CSV into TLN format with one column per field and concatenated description."""
    logging.info(f"Processing file: {csv_path} ({files_remaining} files remaining)")
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        filename = os.path.basename(csv_path)
        input_lines = len(df)

        csv_type = next(
            (key for key in CSV_MAPPINGS if
             re.fullmatch(re.escape(key).replace(r"\*", ".*").replace(r"\\\$", r"\$"), filename, re.IGNORECASE)),
            None
        )
        if not csv_type:
            logging.warning(f"Skipping unrecognized CSV: {csv_path} ({files_remaining} files remaining)")
            return None

        logging.debug(f"Selected csv_type: {csv_type} for file: {filename}")
        mapping = CSV_MAPPINGS[csv_type]

        # Common fields for all CSV types
        df["Source"] = mapping["source"](df) if callable(mapping["source"]) else df.get(mapping["source"], "Unknown_Source")

        if callable(mapping["system"]):
            df["System"] = mapping["system"](df)
        else:
            df["System"] = df.get(mapping["system"], "Unknown_System")

        if mapping["user"] is None:
            if ("HivePath" in df.columns) and ("RECmd_Batch_UserActivity_Output.csv" in filename):  # For RECmd_Batch_UserActivity_Output.csv
                df["User"] = df["HivePath"].apply(
                    lambda path: os.path.basename(os.path.dirname(str(path))) if pd.notna(path) else "Unknown_User")
            elif ("SourceName" in df.columns) and ("RBCmd_Output.csv" in filename):  # For RBCmd_Output.csv
                df["User"] = df["SourceName"].apply(
                    lambda path: os.path.basename(os.path.dirname(str(path))) if pd.notna(path) else "Unknown_User")
            elif "_UserAssist__" in filename:  # For UserAssist files
                match = re.search(r"Users_([^_]+)_NTUSER\.DAT\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_RunMRU__" in filename:  # For RunMRU files
                match = re.search(r"Users_([^_]+)_NTUSER\.DAT\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_NTUSER.csv" in filename:  # For ShellBag Artifacts
                match = re.search(r"([^_]+)_NTUSER\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_Activity_PackageIDs.csv" in filename:  # For Win10 Timeline Artifacts
                match = re.search(r"([^_]+)_Activity_PackageIDs\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_UsrClass.csv" in filename:  # For ShellBag Artifacts
                match = re.search(r"([^_]+)_UsrClass\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_BamDam__" in filename:  # For BamDam files
                if "BatchKeyPath" in df.columns:
                    df["User"] = df["BatchKeyPath"].apply(
                        lambda path: path.split("UserSettings\\")[-1] if pd.notna(path) and "UserSettings\\" in path else "Unknown_User"
                    )
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"BatchKeyPath column not found in {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            elif "_RecentDocs__" in filename:  # For RecentDocs files
                match = re.search(r"Users_([^_]+)_NTUSER\.DAT\.csv$", filename, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    df["User"] = username
                else:
                    df["User"] = "Unknown_User"
                    logging.warning(
                        f"Could not parse username from {filename}, defaulting to 'Unknown_User' ({files_remaining} files remaining)")
            else:
                df["User"] = "Unknown_User"
        elif callable(mapping["user"]):
            df["User"] = mapping["user"](df)
        else:
            df["User"] = df.get(mapping["user"], "Unknown_User")

        # Special handling for JumpList, LinkFile, MFT, SUMdb, and RecentFileCache files with multiple timestamps
        if csv_type in ["*_*Destinations.csv", "*_LECmd_Output.csv", "*_MFTECmd_\\$MFT_Output.csv", "*_SumECmd_DETAIL_ClientDetailed_Output.csv", "*_RecentFileCacheParser_Output.csv"]:
            time_fields = mapping.get("time_fields", [])
            # Extract field names and their corresponding prefix letters
            field_names = [field[0] if isinstance(field, tuple) else field for field in time_fields]
            field_prefixes = {field[0]: field[1] for field in time_fields if isinstance(field, tuple)} if any(
                isinstance(field, tuple) for field in time_fields) else {
                "SourceCreated": "C",
                "SourceModified": "M",
                "SourceAccessed": "A"
            }

            if not all(field in df.columns for field in field_names):
                missing = [f for f in field_names if f not in df.columns]
                logging.error(f"Timestamp fields {missing} not found in {csv_path} ({files_remaining} files remaining)")
                return None

            # Generate description for JumpList/LinkFile/MFT/SUMdb/RecentFileCache files (before timestamp processing)
            exclude_cols = field_names.copy()
            if not callable(mapping.get("system")) and mapping.get("system"):
                exclude_cols.append(mapping["system"])
            if not callable(mapping.get("user")) and mapping.get("user"):
                exclude_cols.append(mapping["user"])
            # Exclude specific columns for SUMdb and SRUM to avoid duplication in description
            if csv_type == "*_SumECmd_DETAIL_ClientDetailed_Output.csv":
                exclude_cols.extend(["AuthenticatedUserName", "IpAddress"])
            elif csv_type == "*_SrumECmd_*.csv":
                exclude_cols.extend(["UserName", "Sid"])
            remaining_cols = [col for col in df.columns if col not in exclude_cols and col not in TLN_COLUMNS]
            df["BaseDescription"] = df[remaining_cols].apply(
                lambda row: ", ".join(f"{k}: {v}" for k, v in row.dropna().items() if str(v).strip()), axis=1
            )

            # Convert timestamps to datetime and format
            for field in field_names:
                df[field + "_formatted"] = pd.to_datetime(df[field], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

            # Group by unique timestamps and combine prefix labels
            grouped_times = []
            for index, row in df.iterrows():
                times = [
                    (row[field + "_formatted"], field)
                    for field in field_names
                    if pd.notna(row[field + "_formatted"])
                ]
                # Group by identical timestamps
                time_dict = {}
                for t, field in times:
                    if t not in time_dict:
                        time_dict[t] = []
                    time_dict[t].append(field)

                # Create entries for each unique timestamp
                for t, fields in time_dict.items():
                    prefix = [field_prefixes.get(field, '') for field in fields]
                    prefix_str = f"[{''.join(sorted(prefix))}]"

                    # Create a new row for this timestamp
                    new_row = row.copy()
                    new_row["Time"] = t
                    new_row["Description"] = f"{prefix_str} {row['BaseDescription']}" if row['BaseDescription'] else prefix_str
                    grouped_times.append(new_row)

            # Convert grouped times to DataFrame
            if grouped_times:
                df = pd.DataFrame(grouped_times)
            else:
                logging.warning(f"No valid timestamps found in {csv_path} ({files_remaining} files remaining)")
                return None

        else:
            # Standard handling for other CSV types
            time_col = mapping["time"]
            if time_col not in df.columns:
                logging.error(f"Timestamp field '{time_col}' not found in {csv_path} ({files_remaining} files remaining)")
                return None

            df["Time"] = pd.to_datetime(df[time_col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

            # Generate description for non-JumpList/LinkFile/MFT/SUMdb/RecentFileCache files
            exclude_cols = []
            if "time" in mapping:
                exclude_cols.append(mapping["time"])
            elif "time_fields" in mapping:
                exclude_cols.extend([field[0] if isinstance(field, tuple) else field for field in mapping["time_fields"]])
            if not callable(mapping.get("system")) and mapping.get("system"):
                exclude_cols.append(mapping["system"])
            if not callable(mapping.get("user")) and mapping.get("user"):
                exclude_cols.append(mapping["user"])
            # Exclude Sid and UserName for SRUM files to avoid duplication in description
            if csv_type == "*_SrumECmd_*.csv":
                exclude_cols.extend(["Sid", "UserName"])
            remaining_cols = [col for col in df.columns if col not in exclude_cols and col not in TLN_COLUMNS]
            df["Description"] = df[remaining_cols].apply(
                lambda row: ", ".join(f"{k}: {v}" for k, v in row.dropna().items() if str(v).strip()), axis=1
            )

        tln_df = df[TLN_COLUMNS].dropna(subset=["Time"])
        output_lines = len(tln_df)

        logging.info(
            f"Successfully processed {csv_path}: {input_lines} input lines, {output_lines} lines written to output ({files_remaining} files remaining)")
        return tln_df

    except Exception as e:
        logging.error(f"Failed to process {csv_path}: {e} ({files_remaining} files remaining)")
        return None

def create_postgres_table(conn):
    """Create a TLN table in PostgreSQL with quoted 'User' column."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS master_timeline (
                Time TIMESTAMP,
                Source TEXT,
                System TEXT,
                "User" TEXT,
                Description TEXT
            );
        """)
        conn.commit()

def insert_to_postgres(conn, df):
    """Insert TLN DataFrame into PostgreSQL with quoted 'User' column."""
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO master_timeline (Time, Source, System, "User", Description)
                VALUES (%s, %s, %s, %s, %s);
            """, (row["Time"], row["Source"], row["System"], row["User"], row["Description"]))
        conn.commit()

def parse_db_url(db_url):
    """Parse a PostgreSQL URL into connection parameters."""
    result = urlparse(db_url)
    return {
        "dbname": result.path[1:],
        "user": result.username,
        "password": result.password,
        "host": result.hostname,
        "port": result.port or 5432
    }

def main():
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Parse EZTools KAPE CSVs into a TLN master timeline.")
    parser.add_argument("-i", "--input", required=True, help="Input folder containing KAPE EZTools CSVs")
    parser.add_argument("-t", "--type", choices=["csv", "postgres", "both"], required=True,
                        help="Output type: 'csv', 'postgres', or 'both' (CSV and PostgreSQL)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output folder for CSV file")
    parser.add_argument("-d", "--db-url",
                        help="PostgreSQL URL (e.g., postgresql://user:password@localhost:5432/dbname), required if type is 'postgres' or 'both'")

    args = parser.parse_args()

    # Validate db-url requirement for postgres or both
    if args.type in ["postgres", "both"] and not args.db_url:
        parser.error("--db-url is required when --type is 'postgres' or 'both'")

    if not os.path.isdir(args.input):
        parser.error(f"Input folder '{args.input}' does not exist")

    if not os.path.isdir(args.output):
        os.makedirs(args.output)

    setup_logging(args.output)

    output_csv = os.path.join(args.output, "master_timeline.csv")

    csv_files = find_csv_files(args.input)
    if not csv_files:
        logging.warning("No EZTools CSVs found!")
        print("No EZTools CSVs found!")
        return

    total_files = len(csv_files)
    logging.info(f"Total files to process: {total_files}")

    master_timeline = []
    total_output_lines = 0
    for i, csv_file in enumerate(csv_files, 1):
        files_remaining = total_files - i
        tln_df = parse_csv_to_tln(csv_file, files_remaining)
        if tln_df is not None:
            master_timeline.append(tln_df)
            total_output_lines += len(tln_df)

    if not master_timeline:
        logging.warning("No data parsed successfully!")
        print("No data parsed successfully!")
        return

    master_df = pd.concat(master_timeline, ignore_index=True)
    master_df["Time"] = pd.to_datetime(master_df["Time"])
    master_df = master_df.sort_values(by=["Time", "Source", "System", "User"]).reset_index(drop=True)

    # Track success of each output method
    csv_success = False
    postgres_success = False
    output_messages = []

    # Handle CSV output
    if args.type in ["csv", "both"]:
        try:
            master_df.to_csv(output_csv, index=False)
            logging.info(f"Master timeline written to {output_csv}: {total_output_lines} total lines written")
            output_messages.append(f"Master timeline written to {output_csv}")
            csv_success = True
        except Exception as e:
            logging.error(f"Failed to write CSV to {output_csv}: {e}")
            output_messages.append(f"Failed to write CSV: {e}")

    # Handle PostgreSQL output
    if args.type in ["postgres", "both"]:
        try:
            db_config = parse_db_url(args.db_url)
            conn = psycopg2.connect(**db_config)
            create_postgres_table(conn)
            insert_to_postgres(conn, master_df)
            logging.info(f"Data successfully inserted into PostgreSQL: {total_output_lines} total lines written")
            output_messages.append("Data successfully inserted into PostgreSQL")
            postgres_success = True
            conn.close()
        except Exception as e:
            logging.error(f"PostgreSQL error: {e}")
            output_messages.append(f"PostgreSQL error: {e}")

    # Print summary of output results
    for message in output_messages:
        print(message)

    # Determine overall success
    if args.type == "both":
        if csv_success and postgres_success:
            print("All outputs completed successfully.")
        else:
            print("One or more outputs failed. Check logs for details.")
            sys.exit(1)
    elif args.type == "csv" and csv_success:
        print("CSV output completed successfully.")
    elif args.type == "postgres" and postgres_success:
        print("PostgreSQL output completed successfully.")
    else:
        print("Output failed. Check logs for details.")
        sys.exit(1)

    end_time = time.time()
    runtime = end_time - start_time
    logging.info(f"Total runtime: {runtime:.2f} seconds")

if __name__ == "__main__":
    main()