# This file is part of 3D-Printing-Threads-For-Fusion.
#
# 3D-Printing-Threads-For-Fusion is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 3D-Printing-Threads-For-Fusion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 3D-Printing-Threads-For-Fusion.  If not, see <https://www.gnu.org/licenses/>.

import xml.etree.ElementTree as ET
import os
import glob
import shutil
import sys
import platform
import argparse
import types

Fore = types.SimpleNamespace(**{
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'RESET': '\033[39m',
})

# Define the linear adjustment function with a ceiling
def calculate_adjustment(pitch_mm):
    adjustment = pitch_mm * 0.16  # Coefficient for linear scaling
    return min(adjustment, 0.3)  # Apply a ceiling of 0.3 mm

def adjust_diameter(diameter, adjustment, unit):
    try:
        diameter_value = float(diameter)
        if unit == 'in':
            adjustment /= 25.4  # Convert inches to mm 
        return diameter_value + adjustment
    except ValueError:
        return diameter

def process_thread(thread, pitch, unit, is_internal):
    pitch_mm = pitch if unit == 'mm' else 25.4 / pitch
    adjustment = calculate_adjustment(pitch_mm)
    if is_internal:
        adjustment = abs(adjustment)  # Increase for internal threads
    else:
        adjustment = -abs(adjustment)  # Decrease for external threads

    major_dia = thread.find('MajorDia')
    if major_dia is not None:
        major_dia.text = f"{adjust_diameter(major_dia.text, adjustment, unit):.4f}"

    pitch_dia = thread.find('PitchDia')
    if pitch_dia is not None:
        pitch_dia.text = f"{adjust_diameter(pitch_dia.text, adjustment, unit):.4f}"

    minor_dia = thread.find('MinorDia')
    if minor_dia is not None:
        minor_dia.text = f"{adjust_diameter(minor_dia.text, adjustment, unit):.4f}"

    if is_internal:
        tap_drill = thread.find('TapDrill')
        if tap_drill is not None and tap_drill.text:
            try:
                tap_drill.text = f"{adjust_diameter(tap_drill.text, adjustment, unit):.4f}"
            except ValueError:
                pass

def process_designation(designation, unit, verbose=False, counters=None, type_name='<unknown-thread>'):
    pitch = None
    threadDesignation = designation.find('ThreadDesignation')
    threadName =  'Unknown-Thread' if threadDesignation is None else threadDesignation.text
    tpi = designation.find('TPI')
    classes = []

    if tpi is not None:
        pitch = float(tpi.text)
        pitch_type = 'TPI'
        pitch_val = tpi.text
    else:
        pitch_elem = designation.find('Pitch')
        pitch = float(pitch_elem.text)
        pitch_type = 'Pitch'
        pitch_val = pitch_elem.text

    if counters is not None:
        counters['designations'] += 1
        counters['file_designations'] += 1

    internal_count = 0
    external_count = 0

    for thread in designation.findall('Thread'):
        if counters is not None:
            counters['threads'] += 1
            counters['file_threads'] += 1

        threadClass = thread.find('Class')
        if threadClass is not None:
            classes.append(threadClass.text)

        gender = thread.find('Gender').text
        is_internal = gender == 'internal'
        if is_internal:
            internal_count += 1
        else:
            external_count += 1

        process_thread(thread, pitch, unit, is_internal)

    if verbose>=3:
        print(f"    Processing size {Fore.GREEN}{type_name}{Fore.RESET}:{Fore.CYAN}{threadName}{Fore.RESET}" + 
                f" {pitch_type} = {Fore.BLUE}{pitch_val}{Fore.RESET}" + 
                f" internal={Fore.BLUE}{internal_count}{Fore.RESET} external={Fore.BLUE}{external_count}{Fore.RESET}" + 
                (f" classes={Fore.BLUE}{','.join(classes)}{Fore.RESET}" if len(classes) else ""))


def process_thread_size(thread_size, unit, verbose=False, counters=None, type_name='<unknown-thread>'):
    if counters is not None:
        counters['file_sizes'] += 1
    for designation in thread_size.findall('Designation'):
        process_designation(designation, unit, verbose, counters, type_name)

def process_thread_type(thread_type, verbose=False, counters=None):
    unit = thread_type.find('Unit').text  # Determine the unit of measurement
    
    name = thread_type.find('Name')
    custom_name = thread_type.find('CustomName')

    type_name = ('<unknown-thread>' if custom_name in None else custom_name.text) if name is None else f"{name.text}" 

    if counters is not None:
        counters['file_type_name'] = type_name

    if name is not None:
        name.text += " for 3D printing"
    
    if custom_name is not None:
        custom_name.text += " for 3D printing"

    for thread_size in thread_type.findall('ThreadSize'):
        process_thread_size(thread_size, unit, verbose, counters, type_name)

def adjust_thread_definitions(input_file, output_file, verbose=False, counters=None):
    tree = ET.parse(input_file)
    root = tree.getroot()

    for thread_type in root.findall('./ThreadSize/..'):
        if counters is not None:
            counters['thread_types'] += 1

        process_thread_type(thread_type, verbose, counters)

    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

def find_latest_thread_data_directory():
    system = platform.system()
    
    if system == 'Windows':
        production_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', 'webdeploy', 'production')
    elif system == 'Darwin':  # macOS
        production_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Autodesk', 'webdeploy', 'production')
    else:
        raise OSError("Unsupported OS: Only Windows and macOS are supported.")
    
    if not os.path.exists(production_path):
        raise FileNotFoundError(f"Production path not found: {production_path}. Ensure Fusion 360 is installed.")
    
    # Get all subdirectories in production (these are version folders, typically hex-named)
    version_folders = [
        os.path.join(production_path, d) for d in os.listdir(production_path)
        if os.path.isdir(os.path.join(production_path, d))
    ]
    
    if not version_folders:
        raise FileNotFoundError("No version folders found in production path.")
    
    # Find the latest version folder by modification time
    latest_version = max(version_folders, key=os.path.getmtime)
    
    # Construct the ThreadData path (differs slightly by OS)
    if system == 'Windows':
        thread_data_path = os.path.join(latest_version, 'Fusion', 'Fusion', 'Server', 'Fusion', 'Configuration', 'ThreadData')
    else:  # macOS
        thread_data_path = os.path.join(
            latest_version, 'Autodesk Fusion.app', 'Contents', 'Libraries', 'Applications',
            'Fusion', 'Fusion', 'Server', 'Fusion', 'Configuration', 'ThreadData'
        )
    
    if not os.path.exists(thread_data_path):
        raise FileNotFoundError(f"ThreadData path not found: {thread_data_path}. Try checking if Fusion 360 is up to date.")
    
    return thread_data_path

def copy_custom_files(target_dir, verbose=False, counters=None):
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        script_dir = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        script_dir = os.path.dirname(os.path.abspath(__file__))

    for file in glob.glob(os.path.join(script_dir, "*.xml")):
        shutil.copy(file, target_dir)
        if counters is not None:
            counters['custom_copied'] += 1
        if verbose:
            print(f"Copied custom file: {os.path.basename(file)} to {target_dir}")

def main():
    parser = argparse.ArgumentParser(description='Adjust thread definitions for 3D printing in Fusion 360.')
    parser.add_argument('-v', '--verbose', action='count', help='Enable verbose output that lists files and each thread as they are processed and total counts at the end.')
    args = parser.parse_args()
    verbose = args.verbose

    if verbose>=3:
        print(f"Executing {os.path.basename(__file__)}")
        print(f"  Options:")
        for arg_name, arg_value in args.__dict__.items():
            print(f"    {arg_name}: {arg_value}")

    if verbose:
        counters = {
            'custom_copied': 0,
            'deleted': 0,
            'input_files': 0,
            'output_files': 0,
            'thread_types': 0,
            'designations': 0,
            'threads': 0,
            'file_sizes' : 0,
            'file_designations' : 0,
            'file_threads' : 0,
            'file_type_name' : None,
        }
    else:
        counters = None

    thread_data_dir = find_latest_thread_data_directory()
    if verbose>=2:
        print(f"Found ThreadData directory: {Fore.CYAN}{thread_data_dir}{Fore.RESET}")

    # Copy any custom XML files to the target directory
    copy_custom_files(thread_data_dir, verbose, counters)
    
    # Delete any existing -3Dprinting.xml files
    for file in glob.glob(os.path.join(thread_data_dir, "*-3Dprinting.xml")):
        os.remove(file)
        if counters is not None:
            counters['deleted'] += 1
        if verbose>=2:
            print(f"Deleted existing file: {Fore.RED}{os.path.basename(file)}{Fore.RESET}")

    # Process each XML file and write the adjusted content to a new file
    for file in glob.glob(os.path.join(thread_data_dir, "*.xml")):
        if "-3Dprinting" not in file:
            if counters is not None:
                counters['input_files'] += 1
            base_name = os.path.basename(file)
            base_name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(thread_data_dir, base_name_without_ext + "-3Dprinting.xml")
            if verbose>=3:
                print(f"Adjusting file: {Fore.CYAN}{base_name}{Fore.RESET} to: {Fore.CYAN}{os.path.basename(output_file)}{Fore.RESET}")
            if verbose:
                counters['file_sizes'] = 0
                counters['file_designations'] = 0
                counters['file_threads'] = 0
                counters['file_type_name'] = None
            adjust_thread_definitions(file, output_file, verbose, counters)
            if counters is not None:
                counters['output_files'] += 1
            if verbose>=2:
                name = base_name if counters['file_type_name'] is None else counters['file_type_name']
                print(f"Processed threads {Fore.GREEN}{name}{Fore.RESET} -" + 
                      f" sizes={Fore.BLUE}{counters['file_sizes']}{Fore.RESET}" + 
                      f" designations={Fore.BLUE}{counters['file_designations']}{Fore.RESET}" + 
                      f" threads={Fore.BLUE}{counters['file_threads']}{Fore.RESET}")

    if verbose:
        print("\nProcessing completed:")
        print(f"    Input files processed: {Fore.BLUE}{counters['input_files']}{Fore.RESET}")
        print(f"    Output files created: {Fore.BLUE}{counters['output_files']}{Fore.RESET}")
        if counters['custom_copied']:
            print(f"    Custom files copied: {Fore.BLUE}{counters['custom_copied']}{Fore.RESET}")
        if counters['deleted']:
            print(f"    Existing files deleted: {Fore.BLUE}{counters['deleted']}{Fore.RESET}")
        print(f"    Thread types processed: {Fore.BLUE}{counters['thread_types']}{Fore.RESET}")
        print(f"    Thread designations processed: processed: {Fore.BLUE}{counters['designations']}{Fore.RESET}")
        print(f"    Total threads processed: {Fore.BLUE}{counters['threads']}{Fore.RESET}")

if __name__ == "__main__":
    main()
