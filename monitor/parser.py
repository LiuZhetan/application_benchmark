import pandas as pd

def get_block_size(lines:[str]) -> int:
    for i in range(2, len(lines)):
        if lines[i] == '\n':
            return i - 2

def parse_log(file_path:str) -> ([str], [str], {}):
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()

    if len(lines) < 4:
        raise Exception("Empty log file")
    
    # Parse header, usually 3 fields
    header_info = lines[0].removesuffix('\n').split('\t')

    # Parse DataFrame header
    df_header = lines[2].split()

    # If lost time informaton throw a Exception
    try:
        pd.to_datetime(df_header[0])
    except:
        raise Exception('lost time informaton')
    df_header[0] = 'Time'

    # Initialize a dictionary to store time and CPU usage for each CPU
    data = {}

    # get block size of log file
    block_size = get_block_size(lines)

    # Process each line
    for i, line in enumerate(lines[2:]): 
        # Check if the line contains CPU usage data
        if i % (block_size + 1) != block_size and i % (block_size + 1) != 0:
            # Split the line into fields
            fields = line.split()

            time = pd.to_datetime(fields[0])
            try:
                device = int(fields[1])
            except:
                device = fields[1]

            fields = fields[2:]
            
            if device not in data:
                data[device] = {'Time': []}
                for field_name in  df_header[2:]:
                    data[device][field_name] = []
            
            # Append all fields to dict
            data[device]['Time'].append(time)
            for i, field_name in enumerate(df_header[2:]):
                    data[device][field_name].append(float(fields[i]))

    result = {}
    for device, data in data.items():
        # Create a DataFrame from the lists
        df = pd.DataFrame(data)
        result[device] = df
    return header_info, df_header, result

if __name__=='__main__':
    parse_log('redis/results/monitor/cpu/iter8_cpu.log')