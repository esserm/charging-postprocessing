import matplotlib
matplotlib.use('TkAgg')
import measurement_merge as mvc
import merge_values_kocos as mvk

vehicle_path = r'\path\to\csv\folder' # exemplary folder path
last_slash_index = vehicle_path.rfind('\\')
measurement = vehicle_path[last_slash_index + 1:]
output_file_path_kocos = '\merged_kocos_' + measurement + '.csv'
output_file_path = '\merged_' + measurement + '.csv'
output_file_path_efficiency = '\Efficiency_analysis\efficiency_' + measurement + '.csv'

#kocos
# data_kocos = mvk.load_data(vehicle_path)
# data_kocos = mvk.merge_voltage_current(data_kocos)
# data_kocos = mvk.timestamp_default(data_kocos)
# data_kocos = mvk.merge_power(data_kocos)
# mvk.save_merged_csv(data_kocos, output_file_path_kocos)

# synchronisation
result_data, efficiency_data = mvc.merge_value_curves(vehicle_path)
#AC Wirelane
#result_data = mvc.merge_value_curves(vehicle_path)


# save
mvc.save_merged_csv(result_data, output_file_path)
mvc.save_merged_csv(efficiency_data, output_file_path_efficiency)