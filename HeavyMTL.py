import os
import csv
import argparse

def process_evtx_ecmd_output(file_path, output_file):
    with open(file_path, 'r', encoding='utf-8-sig') as f, open(output_file, 'a', newline='', encoding='utf-8-sig') as output:
        reader = csv.reader(f)
        header = next(reader)

        # Find column indices
        date_index = header.index('TimeCreated')
        source_index = 'EVTX'
        host_index = header.index('Computer')
        user_index = header.index('UserName')

        writer = csv.writer(output, delimiter='\t')

        # Write header if the file is empty
        if output.tell() == 0:
            writer.writerow(['Date', 'Source', 'Host', 'User', 'Desc'])

        for row in reader:
            desc_fields = [f"{header[i]}: {row[i].replace('\t', '   ')}" for i in range(len(header)) if i not in (date_index, source_index, host_index, user_index)]
            desc_string = '  '.join(desc_fields)

            writer.writerow([row[date_index], source_index, row[host_index], row[user_index], desc_string])

def process_activity_csv(file_path, output_file):
    with open(file_path, 'r', encoding='utf-8-sig') as f, open(output_file, 'a', newline='',
        encoding='utf-8-sig') as output:
        reader = csv.reader(f)
        header = next(reader)

        # Find column indices
        date_index = header.index('StartTime')
        source_index = 'ActivitiesCache'
        host_index = ''
        user_index = ''

        writer = csv.writer(output, delimiter='\t')

        # Write header if the file is empty
        if output.tell() == 0:
            writer.writerow(['Date', 'Source', 'Host', 'User', 'Desc'])

        for row in reader:
            desc_fields = [f"{header[i]}: {row[i].replace('\t', '   ')}" for i in range(len(header)) if
                           i not in (date_index, source_index, host_index, user_index)]
            desc_string = '  '.join(desc_fields)
            desc_string = '[S] ' +desc_string

            writer.writerow([row[date_index], source_index, host_index, user_index, desc_string])

def process_activity_operations_csv(file_path, output_file):
    with open(file_path, 'r', encoding='utf-8-sig') as f, open(output_file, 'a', newline='',
        encoding='utf-8-sig') as output:
        reader = csv.reader(f)
        header = next(reader)

        # Find column indices
        start_date_index = header.index('StartTime')
        created_date_index = header.index('CreatedTime')
        source_index = 'ActivitiesCache'
        host_index = ''
        user_index = ''

        prepend = ''

        writer = csv.writer(output, delimiter='\t')

        # Write header if the file is empty
        if output.tell() == 0:
            writer.writerow(['Date', 'Source', 'Host', 'User', 'Desc'])

        for row in reader:
            if (created_date_index == start_date_index):
                prepend = '[SC]'
                desc_fields = [f"{header[i]}: {row[i].replace('\t', '   ')}" for i in range(len(header)) if
                               i not in (start_date_index, source_index, host_index, user_index)]
                desc_string = '  '.join(desc_fields)
                desc_string = prepend + desc_string
                writer.writerow([row[start_date_index], source_index, host_index, user_index, desc_string])
            else:
                prepend = '[S]'
                desc_fields = [f"{header[i]}: {row[i].replace('\t', '   ')}" for i in range(len(header)) if
                               i not in (start_date_index, source_index, host_index, user_index)]
                desc_string = '  '.join(desc_fields)
                desc_string = prepend + desc_string
                writer.writerow([row[start_date_index], source_index, host_index, user_index, desc_string])

                prepend = '[C]'
                desc_fields = [f"{header[i]}: {row[i].replace('\t', '   ')}" for i in range(len(header)) if
                               i not in (created_date_index, source_index, host_index, user_index)]
                desc_string = '  '.join(desc_fields)
                desc_string = prepend + desc_string
                writer.writerow([row[created_date_index], source_index, host_index, user_index, desc_string])

def process_activity_packageids_csv(file_path, output_file):
    print("process_activity_packageids_csv")

def process_csv(file_path, output_file):
    if file_path.endswith("_EvtxECmd_Output.csv"):
        process_evtx_ecmd_output(file_path, output_file)
    elif file_path.endswith("_Activity.csv"):
        process_activity_csv(file_path, output_file)
    elif file_path.endswith("_ActivityOperations.csv"):
        process_activity_operations_csv(file_path, output_file)
    elif file_path.endswith("_Activity_PackageIDs.csv"):
        process_activity_packageids_csv(file_path, output_file)
    else:
        print("Unsupported file type.")
def main():
    parser = argparse.ArgumentParser(description='Process CSV files recursively.')
    parser.add_argument('-i', '--input_dir', help='Path to the input directory')
    parser.add_argument('-o', '--output_file', help='Path to the output file')
    args = parser.parse_args()

    todo_list = []
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith('.csv'):
                todo_list.append({'FullPath': os.path.join(root, file), 'ProcStatus': False})

    print(todo_list)

    for item in todo_list:
        process_csv(item['FullPath'], args.output_file +'\\HeavyMTL.tsv')
        print("Processing: " +item['FullPath'])
        item['ProcStatus'] = True

    print(todo_list)
if __name__ == '__main__':
    main()