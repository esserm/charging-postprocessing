import csv
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import datetime
vehicle_path = r'\path\to\csv'

def merge_value_curves(vehicle_path):
    last_slash_index = vehicle_path.rfind('\\')
    measurement = vehicle_path[last_slash_index + 1:]
    input_file_path_node_red = vehicle_path + '/' + measurement + '.csv'
    input_file_path_merged_kocos = '\Kocos_adjustments\merged_kocos_' + measurement + '.csv'
    input_file_path_ev_monitor = vehicle_path + '/' + measurement + '_EV-Monitor' + '.csv'
    output_file_path = '\Merge_data\Mitsubishi Eclipse Cross\merged_' + measurement + '.csv'
    output_file_path_efficiency = '\Efficiency_analysis\efficiency_' + measurement + '.csv'

    # load data
    data_node_red = np.loadtxt(input_file_path_node_red, delimiter=',', dtype=str)
    try:
        data_kocos = np.loadtxt(input_file_path_merged_kocos, delimiter=';', dtype=str)
        print('Kocos data available')
    except Exception as e:
        print('No Kocos data',e)

    # definition meas type
    meas_type = 0 # empty charging / discharging
    if 'individual' in vehicle_path: # time series
        meas_type = 2
        print('meas type 2: individual')
    elif '5kW' in vehicle_path:
        meas_type = 1
        print('meas type 1: 5 kW - full charge / complete discharge ')
    else:
        print('meas type 0: 10 kW / 22 kW - full charge / complete discharge ')

    # formatting
    header = np.vstack([data_node_red[0], [''] * data_node_red.shape[1]])
    values_node_red = data_node_red[1:, :].astype(float)
    if 'data_kocos' in locals():
        data_kocos = np.char.replace(data_kocos, ',', '.')
        header_kocos = data_kocos[:2]
        header = np.hstack([header, header_kocos])

        values_kocos = []
        for row in data_kocos[2:]:
            converted_row = []
            for val in row[1:]:
                if val != '':
                    converted_row.append(float(val))
                else:
                    converted_row.append(np.nan)
            values_kocos.append(converted_row)
        values_kocos = np.array(values_kocos)

        # stepsize adjustment (node_red: 0.5s // kocos: 3s)
        kocos_val_time = data_kocos[2:,:]
        rows, cols = kocos_val_time.shape # kocos timestamp missing


    # stepsize adjustments
    ##create array based on node-red timestamp
    stepsize_node_red = data_node_red[1:,data_node_red.shape[1]-1]
    #stepsize = data_node_red[1:, 41]
    timestamp = stepsize_node_red.astype(float)/1000
    converted_timestamp_array = []
    for i in range(len(timestamp)):
        converted_timestamp = datetime.datetime.fromtimestamp(timestamp[i])
        converted_timestamp_array.append(converted_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"))

    measurement_duration = (datetime.datetime.fromtimestamp(timestamp[len(timestamp)-1]) - datetime.datetime.fromtimestamp(timestamp[0])).total_seconds()
    target_number_meas_values = measurement_duration * 2
    average_real_stepsize = (len(values_node_red) / target_number_meas_values) * 0.5
    real_number_meas_values = measurement_duration / average_real_stepsize

    indices = []
    for i in range(1,len(converted_timestamp_array)-5):
        current_row = converted_timestamp_array[i]
        previous_row = converted_timestamp_array[i-1]
        next_row = converted_timestamp_array[i+1]
        if current_row[18] != previous_row[18] and current_row[18] != next_row[18]:
            indices.append(i)

    null_row = np.zeros((1,values_node_red.shape[1]), dtype=values_node_red.dtype)
    #values_node_red = values_node_red
    # for pos in indices:
    #     values_node_red = np.insert(values_node_red, pos+1, null_row, axis = 0)

    if 'data_kocos' in locals():
        # comparative value: grid power
        grid_power_kocos = np.sum(values_kocos[:,[7,265,523]], axis=1)/1000.0
        #grid_power_kocos = np.sum(values_kocos[:, [6, 264, 520]], axis=1) / 1000.0
        #grid_power_kocos = np.sum(values_kocos[:, [7, 203, 399]], axis=1) / 1000.0 # corsa
        grid_power_node_red = values_node_red[:,8] #or values_node_red with zeros
        grid_power_node_red.reshape((-1, 1))

        # create a new array with six times the number of rows (stepsize differences)
        step = 'variable' #fixed
        step_in_sec = 3
        stepsize = 2 * step_in_sec
        number_values_kocos = average_real_stepsize * stepsize
        adjusted_stepsize_kocos = number_values_kocos/0.5
        #adjusted_stepsize_kocos = 6

        stepsize_adj_kocos = np.zeros((round(kocos_val_time.shape[0] * adjusted_stepsize_kocos)-1, kocos_val_time.shape[1]), dtype=object)

        sum_rest = 0
        reste = []
        counter = 0
        counter_2 = 0

        for i in range(kocos_val_time.shape[0]):
            rest = step_in_sec - number_values_kocos
            sum_rest = sum_rest + rest
            if sum_rest > 0.5:
                reste.append(i)
                counter_2 += 1
                sum_rest = 0

        for i in range(kocos_val_time.shape[0]-6-counter_2):
            if i in reste:
                stepsize_adj_kocos[i * stepsize - 1 - counter] = kocos_val_time[i]
                counter += 1
                sum_rest = 0
            else:
                stepsize_adj_kocos[i * stepsize - counter] = kocos_val_time[i]

        # elif step == 'fixed':
        #     stepsize_adj_kocos = np.zeros((kocos_val_time.shape[0] * stepsize - 1, kocos_val_time.shape[1]), dtype=object)
        #
        #     # for i in range(kocos_val_time.shape[0]-6):
        #     #     stepsize_adj_kocos[round(i * adjusted_stepsize_kocos)] = kocos_val_time[i]
        #     #
        #     #stepsize_adj_kocos = stepsize_adj_kocos[:round(kocos_val_time.shape[0] * adjusted_stepsize_kocos)]
        #
        #     # if i < kocos_val_time.shape[0] - 1:
        #     #    stepsize_adj_kocos[i * 6 + 1] = np.empty(kocos_val_time.shape[1], dtype=object)
        #
        #     #option fixed stepsize
        #     #fill resulting array with the values from the original array and zero rows
        #     stepsize_adj_kocos[::6] = kocos_val_time
        #     stepsize_adj_kocos[1::6] = [0] * cols  # insert empty character strings as zero lines
        #     stepsize_adj_kocos[2::6] = [0] * cols
        #     stepsize_adj_kocos[3::6] = [0] * cols
        #     stepsize_adj_kocos[4::6] = [0] * cols
        #     stepsize_adj_kocos[5::6] = [0] * cols


        # compare values by using tolerance
        # parameters for tolerance and number of values are defined here
        #tolerance = 0.05 # 0.001
        if meas_type == 0: # 10 kW charging / discharging
            tolerance = 0.5
            tolerance_step_size = 0.5 #0.1
            number_value_check = 2 #2000 10
        elif meas_type == 1: # 5 kW charging / discharging
            tolerance = 0.5
            tolerance_step_size = 0.5  # 0.03 0.015
            number_value_check = 2  # 2000 200
        else: # time series
            tolerance = 0.2 # 0.1
            tolerance_step_size = 0.5 # 0.2
            number_value_check = 2 # 2

            # Iterate through the columns to find
        #for col in range(round(grid_power_node_red.shape[0] - 1)):  # Iterate until the second-to-last column
        #for col in range(round(grid_power_node_red.shape[0] / 12),round(grid_power_node_red.shape[0] - 1)):  # Iterate until the second-to-last column
        for col in range(600, round(grid_power_node_red.shape[0] - 1)):
            current_column = grid_power_node_red[col]
            next_column = grid_power_node_red[col + 1]

            diff = np.abs(next_column - current_column)

            if diff > 0.5:
                start_index_node_red = col #+ round(number_value_check * adjusted_stepsize_kocos) # - round(adjusted_stepsize_kocos * (grid_power_kocos.shape[0]/4))
                print(start_index_node_red)
                break

        #for col in range(round(grid_power_kocos.shape[0] - 1)):  # Iterate until the second-to-last column
        #for col in range(round(grid_power_kocos.shape[0] / 12), round(grid_power_kocos.shape[0] - 1)):  # Iterate until the second-to-last column
        for col in range(100, round(grid_power_kocos.shape[0] - 1)): # 52 133
            current_column = grid_power_kocos[col]
            next_column = grid_power_kocos[col + 1]

            diff = np.abs(next_column - current_column)

            if diff > 0.5:
                start_index_kocos = col #+ number_value_check # - round(grid_power_kocos.shape[0]/4)
                print(start_index_kocos)
                break

        num_values = min(len(grid_power_node_red), len(grid_power_kocos)*6)
        for i in range(start_index_kocos,round(len(grid_power_kocos)/10*10)): #8.5
            for j in range(start_index_node_red,round(len(grid_power_node_red)/10*10)): #round(number_value_check * adjusted_stepsize_kocos)
                if abs(grid_power_node_red[j] - grid_power_kocos[i]) < tolerance: # compare values
                    #l = j - (number_value_check * stepsize)  # option fixed stepsize
                    l = j - round(number_value_check * adjusted_stepsize_kocos) # variable step size
                    success_count = 0
                    for k in range(i - number_value_check, i):
                        if abs(grid_power_node_red[l] - grid_power_kocos[k]) < tolerance_step_size:
                            success_count += 1
                        #l += stepsize  # option fixed stepsize
                        l = round((i+1) * adjusted_stepsize_kocos)

                        if success_count == round((number_value_check/10) * 8.0): # 95% of values match
                            print(i,j)
                            if round(i * adjusted_stepsize_kocos) - j < 0:
                            #if i * stepsize - j < 0: # option fixed stepsize
                                missing_values = abs(round(i * adjusted_stepsize_kocos) - j)
                                #missing_values = abs(i * 6 - j) # option fixed stepsize
                                filling_array = np.empty((missing_values, stepsize_adj_kocos.shape[1]), dtype= object)
                                stepsize_adj_kocos = np.vstack((filling_array, stepsize_adj_kocos))
                                r = stepsize_adj_kocos[0:len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j + missing_values]
                                r = stepsize_adj_kocos[round(i * adjusted_stepsize_kocos) - j:len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j]
                                #r = stepsize_adj_kocos[missing_values:len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j + missing_values]
                                #r = stepsize_adj_kocos[0:len(grid_power_node_red) + i * stepsize - j + missing_values] # option fixed stepsize
                                #r = r[:len(grid_power_node_red) + i * stepsize - j + missing_values]
                                print('1')
                            elif round(i * adjusted_stepsize_kocos) + (len(grid_power_node_red)-j) > stepsize_adj_kocos.shape[0]:
                            #elif len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j >stepsize_adj_kocos.shape[0]:
                                missing_values = len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j - stepsize_adj_kocos.shape[0]
                                filling_array = np.empty((missing_values, stepsize_adj_kocos.shape[1]), dtype=object)
                                stepsize_adj_kocos = np.vstack((stepsize_adj_kocos, filling_array))
                                #r = stepsize_adj_kocos[missing_values:(len(grid_power_node_red) + missing_values)]
                                r = stepsize_adj_kocos[round(i * adjusted_stepsize_kocos) - j:len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j]
                                #r = stepsize_adj_kocos[0:len(grid_power_node_red)]
                                print('2')
                            else:
                                r = stepsize_adj_kocos[round(i * adjusted_stepsize_kocos) - j:len(grid_power_node_red) + round(i * adjusted_stepsize_kocos) - j]
                                #r = stepsize_adj_kocos[i * stepsize - j:len(grid_power_node_red) + i * stepsize - j] # option fixed stepsize
                                #r = r[:len(grid_power_node_red) + i * stepsize - j]
                                print('3')
                            num_values = 0
                            break
                    if num_values == 0:
                        break
            if num_values == 0:
                break

    # data ev-monitor
    try:
        data_ev_monitor = np.loadtxt(input_file_path_ev_monitor, delimiter=',', dtype=str)
    except Exception as e:
        print('EV-Monitor data not available',e)

    if 'data_ev_monitor' in locals():
        header_ev_monitor = np.vstack([data_ev_monitor[0],['']* len(data_ev_monitor[0])])
        values_ev_monitor = data_ev_monitor[1:,:]
        header_2 = np.hstack([header, header_ev_monitor])

        sum_rest = 0
        reste = []
        counter = 0
        number_values_ev_monitor = average_real_stepsize * 2
        adjusted_stepsize_ev_monitor = number_values_ev_monitor/0.5

        # stepsize adjustment (node red: 0,5s // ev-monitor: 1s)
        stepsize_adj_ev_monitor = np.zeros((values_ev_monitor.shape[0] * 2 - 1, values_ev_monitor.shape[1]),dtype=object)
        #stepsize_adj_ev_monitor = np.zeros((round(values_ev_monitor.shape[0] * adjusted_stepsize_ev_monitor) - 1, values_ev_monitor.shape[1]), dtype=object)

### approach 1

        # # option fixed stepsize
        # for i in range(values_ev_monitor.shape[0]):
        #     stepsize_adj_ev_monitor[i * 2] = values_ev_monitor[i]
        # if i < values_ev_monitor.shape[0] - 1:
        #     stepsize_adj_ev_monitor[i * 2 + 1] = np.empty(values_ev_monitor.shape[1], dtype=object)

        # stepsize_adj_ev_monitor[stepsize_adj_ev_monitor == None] = 0

### approach 2
        # sum_rest = 0
        # reste = []
        # counter = 0
        #
        # for i in range(values_ev_monitor.shape[0]):
        #     rest = 1 - number_values_ev_monitor
        #     sum_rest = sum_rest + rest
        #     if sum_rest > 0.5:
        #         reste.append(i)
        #         sum_rest = 0
        #
        # for i in range(values_ev_monitor.shape[0] - 2):
        #     if i in reste:
        #         stepsize_adj_ev_monitor[i * 2 - 1 - counter] = values_ev_monitor[i]
        #         counter += 1
        #         sum_rest = 0
        #     else:
        #         stepsize_adj_ev_monitor[i * 2 - counter] = values_ev_monitor[i]

### approach 3
        for i in range(values_ev_monitor.shape[0]):
            rest = 1 - number_values_ev_monitor
            sum_rest = sum_rest + rest
            if sum_rest > 0.5:
                reste.append(i)
                sum_rest = 0

        for i in range(values_ev_monitor.shape[0]):
            if i in reste:
                stepsize_adj_ev_monitor[i * 2 - 1 - counter] = values_ev_monitor[i]
                counter += 1
                sum_rest = 0
            else:
                stepsize_adj_ev_monitor[i * 2 - counter] = values_ev_monitor[i]


    ## values_node_red[32] = chademo output power // stepsize_adj_ev_monitor[37] = chademo output power - add automatic check for plug type
    #node_red_output_power = values_node_red[:, 32]
    if values_node_red.shape[1] < 40:
        output = 'Meas type: Wirelane AC'
        z = 0
    else:
        if values_node_red[0, 27] != 0:
            node_red_output_voltage = values_node_red[:, 30]
            node_red_output_current = values_node_red[:, 31]
            z = 32
            output = 'Plug type: CHAdeMo'
        elif values_node_red[0, 36] != 0:
            node_red_output_voltage = values_node_red[:, 37]
            node_red_output_current = values_node_red[:, 38]
            z = 39
            output = 'Plug type: AC'
        elif values_node_red[0,18] != 0:
            node_red_output_voltage = values_node_red[:, 21]
            node_red_output_current = values_node_red[:, 22]
            output = 'Plug type: CCS'
            z = 23
        else:
            output = 'Error: Plug type'
    print(output)

    if 'data_ev_monitor' in locals():
        if values_node_red[0,25] != 0: #chademo
            #ev_monitor_output_power = values_ev_monitor[:, 38].astype(float) / 1000
            ev_monitor_output_voltage = values_ev_monitor[:, 36].astype(float)
            ev_monitor_output_current = values_ev_monitor[:, 37].astype(float)
            #print('Plug type: CHAdeMo')
        elif values_node_red[0,18] != 0: #ccs
            # ev_monitor_output_power = values_ev_monitor[:, 38].astype(float) / 1000
            ev_monitor_output_voltage = values_ev_monitor[:, 33].astype(float)
            ev_monitor_output_current = values_ev_monitor[:, 34].astype(float)
            #print('Plug type: CCS')
        # elif values_node_red[0,36] != 0:
        #     #print('Plug type AC')
        else:
            print('Error: Plug type')

        # adjustments based on an examination of the flanks
        i = 0
        j = 0
        k = 0
        l = 0
        tolerance_output_power = 0.5
        tolerance_output_current_initial = 1 # 0.3
        tolerance_output_voltage_initial = 1 # 0.3
        if meas_type == 0: # 10 kW charging / discharging
            tolerance_output_current = 2 #0.8
            tolerance_output_voltage = 4 #2.5 # decimal places ev-monitor: max. 2
            number_value_check = 20 #3500 200
        elif meas_type == 1: # 5 kW charging / discharging
            tolerance_output_current_initial = 1
            tolerance_output_current = 1
            tolerance_output_voltage = 1
            number_value_check = 50 # 200
        else: # time series
            tolerance_output_current_initial = 1.5 # 1.5
            tolerance_output_voltage_initial = 1.5 # 1.5
            tolerance_output_current = 4.0 # 0.2
            tolerance_output_voltage = 0.5 # 0.5
            number_value_check = 10 # 100


        # Iterate through the columns
        for col in range(node_red_output_current.shape[0] - 1):
        #for col in range(round(node_red_output_current.shape[0]/2), node_red_output_current.shape[0] - 1):  # Iterate until the second-to-last column
            current_column = node_red_output_current[col]
            next_column = node_red_output_current[col + 1]

            diff = np.abs(next_column - current_column)

            if diff > 0.2:
                #start_index_node_red_2 = col + round(number_value_check * adjusted_stepsize_ev_monitor) # - round(adjusted_stepsize_ev_monitor * (ev_monitor_output_voltage.shape[0]/4))
                start_index_node_red_2 = col + round(number_value_check * 2)
                break

        for col in range(400,ev_monitor_output_current.shape[0] - 1):  # Iterate until the second-to-last column
        #for col in range(round(ev_monitor_output_current.shape[0]/2), ev_monitor_output_current.shape[0] - 1):  # Iterate until the second-to-last column
            current_column = ev_monitor_output_current[col]
            next_column = ev_monitor_output_current[col + 1]

            diff = np.abs(next_column - current_column)

            if diff > 0.2:
                start_index_ev_monitor = col + number_value_check # - round(ev_monitor_output_voltage.shape[0]/4)
                break

        num_values_2 = min(len(node_red_output_voltage), len(ev_monitor_output_voltage))

        for i in range(start_index_ev_monitor, round(len(ev_monitor_output_voltage)/10*8.5)):
        #for i in range(number_value_check, len(ev_monitor_output_voltage)): # round(len(ev_monitor_output_voltage)/10*7)
            for j in range(start_index_node_red_2, round((len(node_red_output_voltage)/10*8.5))):
            #for j in range(round(adjusted_stepsize_ev_monitor * number_value_check), len(node_red_output_voltage)):
                #if abs(node_red_output_voltage[j] - ev_monitor_output_voltage  [i]) < tolerance_output_voltage_initial and abs(node_red_output_current[j] - ev_monitor_output_current[i]) < tolerance_output_current_initial: # compare values
                if abs(node_red_output_current[j] - ev_monitor_output_current[i]) < tolerance_output_current_initial:  # compare values
                    l = j - round(adjusted_stepsize_ev_monitor * number_value_check)
                    #l = j - (number_value_check * 2) # option fixed stepsize
                    success_count = 0
                    for k in range(i - number_value_check ,i):
                        #if abs(node_red_output_voltage[l] - ev_monitor_output_voltage[k]) < tolerance_output_voltage and abs(node_red_output_current[l] - ev_monitor_output_current[k]) < tolerance_output_current:
                        if abs(node_red_output_current[l] - ev_monitor_output_current[k]) < tolerance_output_current:

                            success_count +=1
                            #print(success_count)

                        #l += 2 # option fixed stepsize
                        l = round((i + 1) * adjusted_stepsize_ev_monitor)

                        if success_count == round((number_value_check / 10) * 10.0): # 95%
                            print(i, j)
                            if round(i * adjusted_stepsize_ev_monitor) - j < 0:
                            #if i * 2 - j < 0:
                                missing_values = abs(i * 2 - j)
                                #missing_values = abs(round(i * adjusted_stepsize_ev_monitor) - j)
                                filling_array = np.empty((missing_values, stepsize_adj_ev_monitor.shape[1]), dtype=object)
                                stepsize_adj_ev_monitor = np.vstack((filling_array, stepsize_adj_ev_monitor))
                                #s = stepsize_adj_ev_monitor[0:len(node_red_output_voltage) + round(i * adjusted_stepsize_ev_monitor) - j + missing_values]
                                s = stepsize_adj_ev_monitor[0:len(node_red_output_voltage) + (i * 2) - j + missing_values]
                                print('1')
                            #elif round(i * 2) + (len(node_red_output_voltage) - j) >stepsize_adj_ev_monitor.shape[0]:
                            elif round(i * adjusted_stepsize_ev_monitor) + (len(node_red_output_current) - j) > stepsize_adj_ev_monitor.shape[0]:
                            #elif len(node_red_output_voltage) + round(i * adjusted_stepsize_ev_monitor) - j >stepsize_adj_ev_monitor.shape[0]:
                                #missing_values = len(node_red_output_current) + round(i * 2) - j - - stepsize_adj_ev_monitor.shape[0]
                                missing_values = len(node_red_output_current) + round(i * adjusted_stepsize_ev_monitor) - j - stepsize_adj_ev_monitor.shape[0]
                                filling_array = np.empty((missing_values, stepsize_adj_ev_monitor.shape[1]), dtype=object)
                                stepsize_adj_ev_monitor = np.vstack((stepsize_adj_ev_monitor, filling_array))
                                s = stepsize_adj_ev_monitor[round(i * adjusted_stepsize_ev_monitor) - j:len(node_red_output_voltage) + round(i * adjusted_stepsize_ev_monitor) - j+ missing_values]
                                # s = stepsize_adj_ev_monitor[missing_values:len(node_red_output_voltage) + missing_values]
                                # #s = stepsize_adj_ev_monitor[0:len(node_red_output_voltage)]
                                # print('2')
                            else:
                                s = stepsize_adj_ev_monitor[round(i * adjusted_stepsize_ev_monitor) - j:len(node_red_output_voltage) + round(i * adjusted_stepsize_ev_monitor) - j]
                                #s = stepsize_adj_ev_monitor[i * 2 - j:len(node_red_output_voltage) + i * 2 - j]  # option fixed stepsize
                                print('3')

                            num_values_2 = 0
                            break

                if num_values_2 == 0:
                    break
            if num_values_2 == 0:
                break



    # results
    if 'data_kocos' in locals() and 'data_ev_monitor' in locals():
        merged_data = np.hstack([values_node_red, r, s])
    elif 'data_kocos' in locals() and 'data_ev_monitor' not in locals():
        merged_data = np.hstack([values_node_red, r])
    elif 'data_ev_monitor' in locals() and 'data_kocos' not in locals():
        merged_data = np.hstack([values_node_red, s])
    else:
        print('Error: no data to merge')

    result_data = merged_data
    result_data = np.where(result_data == None, 0, result_data)
    count=0
    list_ind= []
    for pos in range(len(merged_data)-len(indices)):
        if result_data[pos,data_node_red.shape[1]-1] < 1.0:
            list_ind.append(pos)
            result_data = np.delete(result_data, pos, axis = 0)
            count += 1

    if 'data_ev_monitor' in locals():
        header = np.hstack([header, header_ev_monitor])
    result_data = np.vstack([header, result_data])


    if z != 0:
        efficiency_node_red = np.empty(result_data.shape[0]-2)

        # efficiency calculation
        for i in range(2, result_data.shape[0]-2):
            if result_data[i,z] < 0:
                efficiency_node_red[i] = abs(result_data[i, 8] / result_data[i, z])
            elif result_data[i,z] > 0 and result_data[i,8] == 0:
                efficiency_node_red[i] = 0
            else:
                efficiency_node_red[i] = abs(result_data[i,z] / result_data[i,8]) # output/input

        if 'data_kocos' in locals():
            x = 861
        else:
            x = 80

        if 'data_ev_monitor' in locals() and z != 0:
            efficiency_node_red_ev_monitor = np.empty(result_data.shape[0]-2)
            u = result_data[2:, 8].astype(float)
            t = (result_data[2:, x]).astype(float)
            for i in range(u.shape[0]-2):
                if t[i] < 0:
                    efficiency_node_red_ev_monitor[i] = abs(u[i] / (t[i] / 1000))
                else:
                    efficiency_node_red_ev_monitor[i] = abs((t[i] / 1000)/ u[i])

        # compress without zero
            efficiency_comp = np.empty(result_data.shape[0]-2)
            efficiency_node_red_ev_monitor_comp = []
            for i in range(2,result_data.shape[0]-2):
                if (float(result_data[i,x])/ 1000) < 0:
                    efficiency_comp[i] = abs(result_data[i, 8] / (float(result_data[i, x]) / 1000))
                else:
                    efficiency_comp[i] = abs((float(result_data[i,x])/ 1000) / result_data[i,8])

                if efficiency_comp[i] != 0:
                    efficiency_node_red_ev_monitor_comp.append(efficiency_comp[i])


            efficiency_data = np.vstack((efficiency_node_red, efficiency_node_red_ev_monitor))
            efficiency_header = np.array((['Efficiency Node-red', 'Efficiency Node-red_EV-Monitor'], ['%', '%']))
            efficiency_data = np.transpose(efficiency_data)

        else:
            efficiency_data = efficiency_node_red
            efficiency_header = np.array((['Efficiency Node-red'], ['%']))
            efficiency_data = efficiency_data.reshape((-1, 1))


        efficiency_data = np.vstack((efficiency_header, efficiency_data))
        efficiency_data = np.hstack((result_data, efficiency_data))

    else:
        print('Efficiency calculation not possible')



    ## check if value assignment is valid
    if 'data_kocos' in locals():
        pl1 = np.array(result_data[2:,26], dtype=float) # AC Wirelane
        pl2 = np.array(result_data[2:,283], dtype=float)
        pl3 = np.array(result_data[2:,540], dtype=float)
        # pl1 = np.array(result_data[2:, 50], dtype=float)
        # pl2 = np.array(result_data[2:, 308], dtype=float)
        # pl3 = np.array(result_data[2:, 566], dtype=float)
        # pl1 = np.array(result_data[2:, 50], dtype=float) # corsa
        # pl2 = np.array(result_data[2:, 246], dtype=float) # corsa
        # pl3 = np.array(result_data[2:, 442], dtype=float) # corsa
        # #pl1_floats = [float(element) for element in merged_data[2:,50]]
        # #pl2 = float(merged_data[2:,308])
        # #pl3 = float(merged_data[2:,566])
        grid_power = (pl1 + pl2 + pl3)/1000.0
        grid_power = grid_power[:]
    node_red_power = result_data[2:,8]
    node_red_charging_station = result_data[2:,32]
    node_red_voltage = result_data[2:,30]
    node_red_current = result_data[2:,31]

    if 'data_ev_monitor' in locals():
        ev_monitor_power = result_data[2:,x].astype(float)/1000
        ev_monitor_voltage = result_data[2:,x-2].astype(float)
        ev_monitor_current = result_data[2:,x-1].astype(float)


    if 'data_kocos' in locals():
        plt.figure(1)
        plt.plot(grid_power, label='kocos')
        plt.plot(node_red_power, label = 'node_red')
        plt.xlabel('time')
        plt.ylabel('grid_power')
        plt.title('comparison of grid power')
        plt.legend()

        # efficiency consideration
        if z!=0:
            plt.figure(2)
            plt.plot(efficiency_node_red, label='node_red')
            plt.xlabel('time')
            plt.ylabel('efficiency')
            plt.title('efficiency consideration')
            plt.legend()
            plt.show()

    if 'data_ev_monitor' in locals():
        plt.figure(3)
        plt.plot(ev_monitor_power, label='ev_monitor')
        plt.plot(node_red_charging_station, label = 'node_red')
        plt.xlabel('time')
        plt.ylabel('charging power')
        plt.title('comparison of charging power')
        plt.legend()
        plt.show()

        plt.figure(4)
        plt.plot(ev_monitor_voltage, label='ev_monitor_voltage')
        plt.plot(node_red_voltage, label = 'node_red_voltage')
        plt.xlabel('time')
        plt.ylabel('charging voltage')
        plt.title('comparison of voltage')
        plt.legend()
        plt.show()

        plt.figure(5)
        plt.plot(ev_monitor_current, label='ev_monitor_current')
        plt.plot(node_red_current, label = 'node_red_current')
        plt.xlabel('time')
        plt.ylabel('charging current')
        plt.title('comparison of current')
        plt.legend()
        plt.show()


        plt.figure(6)
        plt.plot(efficiency_node_red_ev_monitor, label = 'ev_monitor')
        plt.xlabel('time')
        plt.ylabel('efficiency')
        plt.title('efficiency consideration')
        plt.legend()
        plt.show()

    if 'efficiency_data' in locals():
        return result_data, efficiency_data
    else:
        return result_data

def save_merged_csv(data, path):
    try:
        np.savetxt(path, data, delimiter=';', fmt='%s')
        print('File successfully saved')
    except Exception as e:
        print('Error while saving', e)



