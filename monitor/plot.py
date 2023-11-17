from monitor.parser import parse_log
import numpy as np


def plot_cpu(plt, file_path:str, from_zero, linestyle='dashed', marker='o', **plt_kargs):
    header_info, feild_names, data = parse_log(file_path)
    for device, df in data.items():
        x = np.arange(len(df)) + 1 if from_zero else df['Time']
        # plt.xticks(x)
        plt.plot(x, df['%user'] + df['%system'], label=f'CPU {device}',linestyle=linestyle, marker=marker, **plt_kargs)
        plt.xlabel('Time (s)')
        plt.ylabel('CPU Usage (%)')
        plt.title(f'CPU Usage Over Time for Each CPU, {header_info[-2] + header_info[-1]}')
        plt.legend()
    return header_info, feild_names, data

def plot_net(plt, file_path:str, from_zero, linestyle='dashed', marker='o', **plt_kargs):
    header_info, feild_names, data = parse_log(file_path)
    for device, df in data.items():
        x = np.arange(len(df)) + 1 if from_zero else df['Time']
        # plt.xticks(x)
        plt.plot(x, df['rxkB/s'] / 1024, label=f'{device} received',linestyle=linestyle, marker=marker, **plt_kargs)
        plt.plot(x, df['txkB/s'] / 1024, label=f'{device} transmitted',linestyle=linestyle, marker=marker, **plt_kargs)
        plt.xlabel('Time (s)')
        plt.ylabel('Speed (MB/s)')
        plt.title(f'Network bandwidth Over Time for Each Interface, {header_info[-2] + header_info[-1]}')
        plt.legend()
    return header_info, feild_names, data

def plot_io(plt, file_path:str, from_zero, linestyle='dashed', marker='o', **plt_kargs):
    header_info, feild_names, data = parse_log(file_path)
    for device, df in data.items():
        x = np.arange(len(df)) + 1 if from_zero else df['Time']
        plt.plot(x, df['rkB/s'], label=f'{device} read',linestyle=linestyle, marker=marker, **plt_kargs)
        plt.plot(x, df['wkB/s'], label=f'{device} write',linestyle=linestyle, marker=marker, **plt_kargs)
        plt.xlabel('Time (s)')
        plt.ylabel('Speed (KB/s)')
        plt.title(f'I/O bandwidth Over Time for Each Device, {header_info[-2] + header_info[-1]}')
        plt.legend()
    return header_info, feild_names, data

def plot_state_log(plt, file_path:str, type:str, from_zero=False, linestyle='dashed', marker='o', **plt_kargs):
    if type == 'cpu':
        return plot_cpu(plt, file_path, from_zero, linestyle, marker, **plt_kargs)
    elif type == 'net':
        return plot_net(plt, file_path, from_zero, linestyle, marker, **plt_kargs)
    elif type == 'io':
        return plot_io(plt, file_path, from_zero, linestyle, marker, **plt_kargs)