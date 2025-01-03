import csv
import os

class DataLogger:
    """Handles logging of measurement data to CSV files."""
    
    def __init__(self, base_path="data"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
    def log_mpp_data(self, channel_id, timestamp, measured_voltage, measured_current, 
                     dac_value, adc_gain_v, adc_gain_c):
        """Log MPP tracking data to CSV file."""
        file_name = os.path.join(self.base_path, f'{channel_id}_data.csv')
        
        # Create file with header if it doesn't exist
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                f.write('timestamp,measured_voltage,measured_current,dac_value,adc_gain_v,adc_gain_c\n')
        
        # Append data
        with open(file_name, 'a') as f:
            f.write(f'{timestamp},{measured_voltage},{measured_current},{dac_value},{adc_gain_v},{adc_gain_c}\n')

    def log_iv_sweep(self, channel_id, data):
        """Log IV sweep data to CSV file."""
        file_name = os.path.join(self.base_path, 'IV', f'{channel_id}_data.csv')
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        
        with open(file_name, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'measured_voltage', 'measured_current', 
                           'dac_value', 'adc_gain_v', 'adc_gain_c'])
            writer.writerows(data)