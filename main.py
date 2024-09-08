import os
import time
import psutil
import tkinter as tk
from tkinter import messagebox, ttk
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import platform
import wmi
from io import StringIO
import sys

# Disk Test Functions
def list_disks():
    """Returns a list of all mounted disks on the system."""
    partitions = psutil.disk_partitions()
    return partitions

def measure_write_speed(file_path, size_in_mb):
    """Measures write speed."""
    data = os.urandom(size_in_mb * 1024 * 1024)
    start_time = time.time()
    try:
        with open(file_path, 'wb') as f:
            f.write(data)
    except IOError as e:
        raise RuntimeError(f"Error writing to disk: {e}")
    end_time = time.time()
    write_speed = size_in_mb / (end_time - start_time)
    return write_speed, data

def measure_read_speed(file_path, size_in_mb):
    """Measures read speed."""
    start_time = time.time()
    try:
        with open(file_path, 'rb') as f:
            f.read(size_in_mb * 1024 * 1024)
    except IOError as e:
        raise RuntimeError(f"Error reading from disk: {e}")
    end_time = time.time()
    read_speed = size_in_mb / (end_time - start_time)
    return read_speed

def verify_data(file_path, original_data, size_in_mb):
    """Verifies if the read data matches the originally written data."""
    try:
        with open(file_path, 'rb') as f:
            read_data = f.read(size_in_mb * 1024 * 1024)
        return read_data == original_data
    except IOError as e:
        raise RuntimeError(f"Error reading data for verification: {e}")

def get_disk_usage(disk):
    """Returns total and free disk space."""
    usage = psutil.disk_usage(disk.mountpoint)
    return usage.total, usage.free

def get_filesystem_type(disk):
    """Returns the filesystem type of the disk."""
    return disk.fstype

def run_test(disk, size_in_mb):
    """Runs read/write test on the selected disk."""
    try:
        test_dir = os.path.join(tempfile.gettempdir(), 'disk_speed_test')
        os.makedirs(test_dir, exist_ok=True)
        file_path = os.path.join(test_dir, 'test_speed.tmp')
        
        write_speed, original_data = measure_write_speed(file_path, size_in_mb)
        if not verify_data(file_path, original_data, size_in_mb):
            raise RuntimeError("Verified data does not match the written data.")
        
        progress_bar['value'] = 50
        root.update_idletasks()
        
        read_speed = measure_read_speed(file_path, size_in_mb)
        os.remove(file_path)
        if not os.listdir(test_dir):
            os.rmdir(test_dir)
        
        total, free = get_disk_usage(disk)
        fs_type = get_filesystem_type(disk)
        
        return {
            'write_speed': write_speed,
            'read_speed': read_speed,
            'total_space': total / (1024 * 1024 * 1024),  # GB
            'free_space': free / (1024 * 1024 * 1024),   # GB
            'fs_type': fs_type
        }
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while testing the disk: {e}")
        return None

def plot_results(results):
    """Creates charts of disk test results."""
    fig, ax = plt.subplots()
    ax.bar(['Read', 'Write'], [results['read_speed'], results['write_speed']])
    ax.set_ylabel('Speed (MB/s)')
    ax.set_title('Disk Test Results')
    plt.show()

def start_test():
    """Starts the disk test after the user selects a disk and a file size."""
    selected_index = disk_listbox.curselection()
    
    if not selected_index:
        messagebox.showwarning("Warning", "Please select a disk to test.")
        return

    size_str = size_entry.get()
    try:
        size_in_mb = int(size_str)
        if size_in_mb <= 0:
            raise ValueError("File size must be a positive number.")
    except ValueError as e:
        messagebox.showwarning("Warning", f"Invalid file size value: {e}")
        return
    
    selected_disk = disks[selected_index[0]]
    
    progress_bar['value'] = 0
    root.update_idletasks()
    
    results = run_test(selected_disk, size_in_mb)
    
    progress_bar['value'] = 100
    root.update_idletasks()
    
    if results:
        result_label.config(text=(
            f"Write Speed: {results['write_speed']:.2f} MB/s\n"
            f"Read Speed: {results['read_speed']:.2f} MB/s\n"
            f"Total Space: {results['total_space']:.2f} GB\n"
            f"Free Space: {results['free_space']:.2f} GB\n"
            f"Filesystem Type: {results['fs_type']}"
        ))
        plot_results(results)
    else:
        result_label.config(text="Test not completed. Please try again.")

# Memory Test Functions
def get_ram_info():
    """Returns information about the RAM installed on the system."""
    if platform.system() == "Windows":
        c = wmi.WMI()
        ram_info = []
        for mem in c.Win32_PhysicalMemory():
            ram_info.append({
                "Manufacturer": mem.Manufacturer,
                "Size (GB)": int(mem.Capacity) / (1024 ** 3),
                "Clock (MHz)": mem.ConfiguredClockSpeed
            })
        return ram_info
    elif platform.system() == "Linux":
        mem_info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key, value = parts
                    mem_info[key.strip()] = value.strip()
        total_memory_kb = int(mem_info.get('MemTotal', '0').split()[0])
        return [{
            "Manufacturer": "Unknown",
            "Size (GB)": total_memory_kb / (1024 ** 2),
            "Clock (MHz)": "Unknown"
        }]
    else:
        # For other systems, you may use other methods or libraries
        return [{"Manufacturer": "Unknown", "Size (GB)": "Unknown", "Clock (MHz)": "Unknown"}]

def get_available_memory():
    """Returns the available memory on the system in GB."""
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)

def test_memory(size_gb):
    """
    Tests memory allocation and usage.
    
    Args:
        size_gb (int): The size of the memory to allocate in gigabytes.
        
    Returns:
        time (float): The time required to complete the test in seconds.
    """
    size_bytes = size_gb * 1024 * 1024 * 1024
    size_elements = size_bytes // np.dtype(np.float64).itemsize

    start_time = time.time()

    # Allocate a large array of floats
    try:
        array = np.random.rand(size_elements)
    except MemoryError:
        return float('inf')  # Returns infinity if unable to allocate memory

    end_time = time.time()

    time_taken = end_time - start_time
    return time_taken

def start_memory_test():
    """Starts the memory test and displays results and chart."""
    progress_bar['value'] = 0
    root.update_idletasks()

    try:
        # Get RAM information
        ram_info = get_ram_info()
        ram_details = "\n".join(
            [f"Manufacturer: {info['Manufacturer']}\nSize: {info['Size (GB)']:.2f} GB\nClock: {info['Clock (MHz)']} MHz"
             for info in ram_info]
        )
        ram_info_label.config(text=f"RAM Information:\n{ram_details}\n")
        
        # Get maximum available RAM capacity
        available_memory_gb = get_available_memory()
        max_ram_gb = int(available_memory_gb * 0.90)  # Test up to 90% of available memory
        
        results = []
        sizes_gb = range(1, max_ram_gb + 1)  # Test from 1GB up to the maximum capacity
        
        for size_gb in sizes_gb:
            time_taken = test_memory(size_gb)
            results.append((size_gb, time_taken))
            progress_bar['value'] = (size_gb / max_ram_gb) * 100
            root.update_idletasks()

        progress_bar['value'] = 100
        root.update_idletasks()
        
        # Display results in the label
        memory_result_label.config(text="\n".join(
            [f"Size: {gb} GB - Time: {time:.2f} seconds" for gb, time in results]
        ))
        
        # Plot chart
        plot_memory_results(results)
        
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while testing memory: {e}")

def plot_memory_results(results):
    """Creates charts of memory test results."""
    sizes_gb, times = zip(*results)
    
    fig, ax = plt.subplots()
    ax.plot(sizes_gb, times, marker='o')
    ax.set_xlabel('Memory Size (GB)')
    ax.set_ylabel('Time (seconds)')
    ax.set_title('RAM Performance')
    plt.grid(True)
    plt.show()

def show_memory_test_frame():
    """Displays the memory test interface."""
    memory_test_frame.pack(fill=tk.BOTH, expand=True)
    disk_test_frame.pack_forget()

def show_disk_test_frame():
    """Displays the disk test interface."""
    disk_test_frame.pack(fill=tk.BOTH, expand=True)
    memory_test_frame.pack_forget()

def setup_redirects():
    """Redirects standard output and errors to Tkinter."""
    sys.stdout = StringIO()
    sys.stderr = StringIO()

def get_redirects_output():
    """Gets redirected output."""
    output = sys.stdout.getvalue()
    error = sys.stderr.getvalue()
    return output, error

def update_output_label():
    """Updates the label with redirected output."""
    output, error = get_redirects_output()
    output_label.config(text=f"Output:\n{output}\nErrors:\n{error}")

# Setup GUI
root = tk.Tk()
root.title("System Test")

setup_redirects()

# Frame for selecting test type
select_test_frame = tk.Frame(root)
select_test_frame.pack(padx=10, pady=10)

tk.Label(select_test_frame, text="Select test type:").pack(pady=10)

tk.Button(select_test_frame, text="Memory Test", command=show_memory_test_frame).pack(pady=5)
tk.Button(select_test_frame, text="Disk Test", command=show_disk_test_frame).pack(pady=5)

# Warning label
warning_label = tk.Label(select_test_frame, text="Warning: Do not run other programs or perform actions that require RAM or disk I/O during the test.", font=("Arial", 12), fg="red")
warning_label.pack(pady=10)

# Frame for memory test
memory_test_frame = tk.Frame(root)

# Button to start memory test
start_memory_button = tk.Button(memory_test_frame, text="Start Memory Test", command=start_memory_test)
start_memory_button.pack(pady=10)

# Progress bar
progress_bar = ttk.Progressbar(memory_test_frame, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

# Label to show results
memory_result_label = tk.Label(memory_test_frame, text="", font=("Arial", 12), fg="blue")
memory_result_label.pack(pady=10)

# Label to show RAM info
ram_info_label = tk.Label(memory_test_frame, text="", font=("Arial", 12), fg="green")
ram_info_label.pack(pady=10)

# Frame for disk test
disk_test_frame = tk.Frame(root)

# Label to select disk
disk_label = tk.Label(disk_test_frame, text="Select disk:")
disk_label.pack(pady=10)

# Listbox to show disks
disks = list_disks()
disk_listbox = tk.Listbox(disk_test_frame)
for disk in disks:
    disk_listbox.insert(tk.END, disk.device)
disk_listbox.pack(pady=10)

# Entry for file size
size_label = tk.Label(disk_test_frame, text="File size (MB):")
size_label.pack(pady=5)
size_entry = tk.Entry(disk_test_frame)
size_entry.pack(pady=5)

# Button to start disk test
start_disk_button = tk.Button(disk_test_frame, text="Start Disk Test", command=start_test)
start_disk_button.pack(pady=10)

# Label to show disk test results
result_label = tk.Label(disk_test_frame, text="", font=("Arial", 12), fg="blue")
result_label.pack(pady=10)

# Label to show output
output_label = tk.Label(root, text="", font=("Arial", 10), fg="red")
output_label.pack(pady=10)

# Display initial selection frame
select_test_frame.pack(fill=tk.BOTH, expand=True)
memory_test_frame.pack_forget()
disk_test_frame.pack_forget()

# Update label with redirected output
update_output_label()

# Start GUI
root.mainloop()
