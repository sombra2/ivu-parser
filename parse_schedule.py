from bs4 import BeautifulSoup
import re  # For replacing invalid filename characters
from datetime import datetime  # For timestamp

# Function to parse the HTML file and extract required data
def parse_schedule(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Extract header information
    user_name = soup.find('span', class_='user-name').text.strip()
    personnel_number = soup.find('span', class_='personnel-number').text.strip()

    # Extract table data
    rows = []
    total_shifts = 0
    shift_destinations = {'BC': 0, 'VL': 0, 'AG': 0, 'SV': 0, 'AL': 0, 'MA': 0}
    total_rest_days = 0
    rest_day_types = {'D': 0, 'I': 0, 'V': 0}
    total_overnight_shifts = 0
    overnight_shifts_by_dest = {'BC': 0, 'VL': 0, 'AG': 0, 'SV': 0, 'AL': 0}
    overnight_shifts_details = []  # List to store details of overnight shifts
    parsed_dates = set()  # Set to track already parsed dates

    duty_days = soup.find_all('td', class_='day')
    for day in duty_days:
        date_elem = day.find('div', class_='date')
        date = date_elem.text.strip() if date_elem else ''

        # Skip the date if it's already been processed
        if date in parsed_dates:
            continue
        parsed_dates.add(date)  # Add the date to the set

        # Look for the duty denomination
        allocation_name_elem = day.find('div', class_='allocation-name')
        duty_nr_elem = day.find('div', class_='duty-nr')
        duty = None

        if duty_nr_elem:
            duty = duty_nr_elem.text.strip()  # Take the "duty-nr" field if available
        elif allocation_name_elem:
            duty = allocation_name_elem.text.strip()  # Fallback to "allocation-name"

        duty = duty or '----'  # Default to '----' if no duty found

        # Look for times
        start_time_elem = day.find('span', class_='time begin')
        end_time_elem = day.find('span', class_='time end')
        time_start = start_time_elem.text.strip() if start_time_elem else '----'
        time_end = end_time_elem.text.strip() if end_time_elem else '----'

        # Temporarily remove '+' from end time to make time comparisons easier
        time_end_no_plus = time_end.rstrip('+')  # Remove '+' sign if it exists

        # Counting total shifts and destinations
        if duty not in ['D', 'I', 'DT', 'LD', 'V', '----']:  # Not a rest day or empty
            total_shifts += 1
            if duty.startswith('BC'):
                shift_destinations['BC'] += 1
            elif duty.startswith('VL'):
                shift_destinations['VL'] += 1
            elif duty.startswith('AG'):
                shift_destinations['AG'] += 1
            elif duty.startswith('SV'):
                shift_destinations['SV'] += 1
            elif duty.startswith('AL'):
                shift_destinations['AL'] += 1
            elif duty.startswith('MA'):
                shift_destinations['MA'] += 1

        # Counting rest days and types
        if duty in ['D', 'I', 'DT', 'LD', 'V']:  # Rest days
            total_rest_days += 1
            if duty == 'D':
                rest_day_types['D'] += 1
            elif duty == 'I':
                rest_day_types['I'] += 1
            elif duty == 'V':
                rest_day_types['V'] += 1

        # Check if this shift is an overnight shift
        if '+' in time_end:  # Overnight shifts
            # Check if the shift ends after 06:00 AM (but still ends with a "+")
            hours, minutes = map(int, time_end_no_plus.split(':')[:2])  # Split time and convert to int
            if hours >= 6:  # If the shift ends after 06:00 AM
                total_overnight_shifts += 1
                if duty.startswith('BC'):
                    overnight_shifts_by_dest['BC'] += 1
                elif duty.startswith('VL'):
                    overnight_shifts_by_dest['VL'] += 1
                elif duty.startswith('AG'):
                    overnight_shifts_by_dest['AG'] += 1
                elif duty.startswith('SV'):
                    overnight_shifts_by_dest['SV'] += 1
                elif duty.startswith('AL'):
                    overnight_shifts_by_dest['AL'] += 1
                overnight_shifts_details.append({
                    'date': date,
                    'duty': duty,
                    'time_start': time_start,
                    'time_end': time_end  # Keep the '+' sign in the output
                })

        rows.append({
            'date': date,
            'duty': duty,
            'time_start': time_start,
            'time_end': time_end,
        })

    # Determine the filename based on the employee and dates
    first_date = rows[0]['date'] if rows else 'unknown'
    last_date = rows[-1]['date'] if rows else 'unknown'

    # Replace invalid characters in the filename
    sanitized_first_date = re.sub(r'[^\w-]', '_', first_date)
    sanitized_last_date = re.sub(r'[^\w-]', '_', last_date)
    sanitized_user_name = re.sub(r'[^\w\s]', '', user_name).replace(' ', '_')
    filename = f"{sanitized_user_name}_{personnel_number}_duties_from_{sanitized_first_date}_to_{sanitized_last_date}.txt"

    # Write results to a text file
    with open(filename, 'w', encoding='utf-8') as output_file:
        # Write header
        output_file.write(f"Employee: {user_name}\n")
        output_file.write(f"Personnel Number: {personnel_number}\n")
        output_file.write(f"Parsing dates from {first_date} to {last_date}\n")  # Parsing range
        output_file.write("\nStatistics:\n")
        output_file.write(f"Total Days Parsed: {len(rows)}\n")
        output_file.write(f"Total Shifts: {total_shifts}\n")
        
        # Adding the percentage next to each shift destination
        for destination, count in shift_destinations.items():
            percentage = (count / total_shifts) * 100 if total_shifts > 0 else 0
            output_file.write(f"  {destination} ({destination_name(destination)}): {count} ({percentage:.2f}%)\n")
        
        # Adding the percentage for total overnight shifts
        overnight_percentage = (total_overnight_shifts / total_shifts) * 100 if total_shifts > 0 else 0
        output_file.write(f"Total Overnight Shifts: {total_overnight_shifts} ({overnight_percentage:.2f}%)\n")

        # Detailing overnight shifts for BC, VL, AG, SV, AL
        output_file.write("\nOvernight Shifts by Destination:\n")
        for destination in ['BC', 'VL', 'AG', 'SV', 'AL']:
            if overnight_shifts_by_dest[destination] > 0:
                percentage = (overnight_shifts_by_dest[destination] / total_overnight_shifts) * 100 if total_overnight_shifts > 0 else 0
                output_file.write(f"  {destination} ({destination_name(destination)}): {overnight_shifts_by_dest[destination]} ({percentage:.2f}%)\n")
        
        output_file.write(f"\nTotal Rest Days: {total_rest_days}\n")
        output_file.write(f"  D: {rest_day_types['D']}\n")
        output_file.write(f"  I: {rest_day_types['I']}\n")
        output_file.write(f"  V: {rest_day_types['V']}\n")

        # Write schedule table
        output_file.write("\nSchedule:\n")
        output_file.write("{:<12} {:<10} {:<10} {:<10}\n".format("Date", "Duty", "Start Time", "End Time"))
        output_file.write("-" * 44 + "\n")
        for row in rows:
            output_file.write("{:<12} {:<10} {:<10} {:<10}\n".format(row['date'], row['duty'], row['time_start'], row['time_end']))
        
        # Add the timestamp at the bottom
        timestamp = datetime.now().strftime("%d/%m/%y %H:%M:%S")
        output_file.write(f"\nThis report has been generated at: {timestamp}\n")

    # Print to console
    print(f"Output written to {filename}")
    print("\nStatistics:")
    print(f"Total Days Parsed: {len(rows)}")
    print(f"Total Shifts: {total_shifts}")
    
    # Print shift destination breakdown with percentages
    for destination, count in shift_destinations.items():
        percentage = (count / total_shifts) * 100 if total_shifts > 0 else 0
        print(f"  {destination} ({destination_name(destination)}): {count} ({percentage:.2f}%)")
    
    # Print the overnight shift percentage
    overnight_percentage = (total_overnight_shifts / total_shifts) * 100 if total_shifts > 0 else 0
    print(f"Total Overnight Shifts: {total_overnight_shifts} ({overnight_percentage:.2f}%)")

    # Print overnight shifts breakdown by destination
    print("\nOvernight Shifts by Destination:")
    for destination in ['BC', 'VL', 'AG', 'SV', 'AL']:
        if overnight_shifts_by_dest[destination] > 0:
            percentage = (overnight_shifts_by_dest[destination] / total_overnight_shifts) * 100 if total_overnight_shifts > 0 else 0
            print(f"  {destination} ({destination_name(destination)}): {overnight_shifts_by_dest[destination]} ({percentage:.2f}%)")

    print(f"Total Rest Days: {total_rest_days}")
    print(f"  D: {rest_day_types['D']}")
    print(f"  I: {rest_day_types['I']}")
    print(f"  V: {rest_day_types['V']}\n")

    # Print the detailed schedule
    print("\nEmployee Schedule:")
    print("{:<12} {:<10} {:<10} {:<10}".format("Date", "Duty", "Start Time", "End Time"))
    print("-" * 44)
    for row in rows:
        print("{:<12} {:<10} {:<10} {:<10}".format(row['date'], row['duty'], row['time_start'], row['time_end']))

# Helper function to map destination codes to their full names
def destination_name(code):
    mapping = {
        'BC': 'Barcelona',
        'VL': 'Valencia',
        'AG': 'Malaga',
        'SV': 'Sevilla',
        'AL': 'Alicante',
        'MA': 'Madrid'
    }
    return mapping.get(code, 'Unknown')

# Parse 'untitled.html'
file_path = 'untitled.html'
parse_schedule(file_path)
