import numpy as np

#input data
vehicle_path = '\path\to\csv\folder' # exemplary folder path


def load_data(vehicle_path):
    last_slash_index = vehicle_path.rfind('\\')
    measurement = vehicle_path[last_slash_index + 1:]
    input_file_path = vehicle_path + '/' + measurement + '_Kocos' + '.csv'
    output_file_path = '\merged_kocos_' + measurement + '.csv'
    data = np.loadtxt(input_file_path, delimiter=';', dtype=str)
    return data


### faster approach
def merge_voltage_current(data):
    grouped_rows = {}
    for row in data[1:]:
        timestamp = row[0]
        if timestamp in grouped_rows:
            grouped_rows[timestamp].append(row)
        else:
            grouped_rows[timestamp] = [row]

    # merge rows with the same timestamp
    merged_data = []
    for timestamp, rows in grouped_rows.items():
        if len(rows) >= 1:  # If there is at least one row with the same timestamp
            combined_row = rows[0]  # Start with the first row
            for i in range(1, len(rows)):
                for j in range(len(rows[i])):
                    # If the combined row has empty cells, fill them from the current row
                    if combined_row[j] == '' and rows[i][j] != '':
                        combined_row[j] = rows[i][j]
            merged_data.append(combined_row)

    merged_data = np.array(merged_data)
    return merged_data

def timestamp_default(data):
    i = 2
    merged_data = [data[0], data[1]]
    while i < len(data)-1:
            voltage_column_value = data[i][1]
            current_column_value = data[i][4]
            power_column_value = data[i][8]
            current_row = data[i]
            next_row = data[i + 1]
            if (voltage_column_value == '' or current_column_value == '') and power_column_value =='':
                merged_row = [current_row[0]]  # adopt timestamp of the first line
                for j in range(1,len(current_row)):
                    if current_row[j] =='':
                        merged_row.append(next_row[j])
                    else:
                        merged_row.append(current_row[j])
                merged_data.append(merged_row)
                i+=2
            else:
                merged_data.append(current_row)
                i +=1

    merged_data = np.array(merged_data)
    return merged_data


def has_empty_cells(row):
    return '' in row

def merge_power(data):
    # merge rows when a complete row is created together
    merged_data = [data[0], data[1]]
    i = 3
    while i < len(data) - 1:
        current_row = data[i]
        next_row = data[i + 1]
        if has_empty_cells(current_row) or has_empty_cells(next_row):
            combined_row = [current_row[0]]  # adopt timestamp of the first line
            for j in range(1, len(current_row)):
                if current_row[j] != '':
                    combined_row.append(current_row[j])
                else:
                    combined_row.append(next_row[j])
            merged_data.append(combined_row)
            i += 2  # skip to the next group of lines
        else:
            merged_data.append(current_row)
            i += 1  # jump to next row

    # add the last line when the loop is finished and it has no more pairs
    if i == len(data) - 1:
        merged_data.append(data[i])

    merged_data = np.array(merged_data)
    return merged_data

def save_merged_csv(data,path):
    try:
        np.savetxt(path, data,delimiter=';', fmt='%s')
        print('File successfully saved')
    except Exception as e:
        print('Error while saving',e)


# data = merge_voltage_current(data)
# data = timestamp_default(data)
# data = merge_power(data)
#save_merged_csv(data, output_file_path)
