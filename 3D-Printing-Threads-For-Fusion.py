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

# Define the linear adjustment function with a ceiling
def calculate_adjustment(pitch_mm):
    adjustment = pitch_mm * 0.16  # Coefficient for linear scaling
    return min(adjustment, 0.3)  # Apply a ceiling of 0.3 mm

def adjust_diameter(diameter, adjustment, unit):
    try:
        diameter_value = float(diameter)
        if unit == 'in':
            adjustment /= 25.4  # Convert mm adjustment to inches
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

def process_designation(designation, unit):
    pitch = None
    tpi = designation.find('TPI')
    if tpi is not None:
        pitch = float(tpi.text)
    else:
        pitch = float(designation.find('Pitch').text)
    
    for thread in designation.findall('Thread'):
        gender = thread.find('Gender').text
        is_internal = gender == 'internal'
        process_thread(thread, pitch, unit, is_internal)

def process_thread_size(thread_size, unit):
    for designation in thread_size.findall('Designation'):
        process_designation(designation, unit)

def process_thread_type(thread_type):
    unit = thread_type.find('Unit').text  # Determine the unit of measurement
    
    name = thread_type.find('Name')
    if name is not None:
        name.text += " for 3D printing"
    
    custom_name = thread_type.find('CustomName')
    if custom_name is not None:
        custom_name.text += " for 3D printing"

    for thread_size in thread_type.findall('ThreadSize'):
        process_thread_size(thread_size, unit)

def adjust_thread_definitions(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    for thread_type in root.findall('./ThreadSize/..'):
        process_thread_type(thread_type)

    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

def find_latest_thread_data_directory():
    base_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', 'webdeploy', 'production')
    latest_subdir = None
    latest_time = None
    for subdir in os.listdir(base_dir):
        candidate = os.path.join(base_dir, subdir, 'Fusion', 'Server', 'Fusion', 'Configuration', 'ThreadData')
        if os.path.isdir(candidate):
            creation_time = os.path.getctime(candidate)
            if latest_time is None or creation_time > latest_time:
                latest_time = creation_time
                latest_subdir = candidate
    return latest_subdir

def copy_custom_files(target_dir):
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        script_dir = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        script_dir = os.path.dirname(os.path.abspath(__file__))

    for file in glob.glob(os.path.join(script_dir, "*.xml")):
        shutil.copy(file, target_dir)

def main():
    thread_data_dir = find_latest_thread_data_directory()
    if thread_data_dir is None:
        print("ThreadData directory not found.")
        return

    # Copy any custom XML files to the target directory
    copy_custom_files(thread_data_dir)
    
    # Delete any existing -3Dprinting.xml files
    for file in glob.glob(os.path.join(thread_data_dir, "*-3Dprinting.xml")):
        os.remove(file)

    # Process each XML file and write the adjusted content to a new file
    for file in glob.glob(os.path.join(thread_data_dir, "*.xml")):
        if "-3Dprinting" not in file:
            base_name = os.path.basename(file)
            base_name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(thread_data_dir, base_name_without_ext + "-3Dprinting.xml")
            adjust_thread_definitions(file, output_file)

if __name__ == "__main__":
    main()
