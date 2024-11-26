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
    shift_destinations = {'BC': 0, 'VL': 0, 'AG': 0, 'SV': 0, 'AL': 0}
    total_rest_days = 0
    rest_day_types = {'D': 0, 'I': 0, 'V': 0}
    total_overnight_shifts = 0
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

        # Counting rest days and types
        if duty in ['D', 'I', 'DT', 'LD', 'V']:  # Rest days
            total_rest_days += 1
            if duty == 'D':
                rest_day_types['D'] += 1
            elif duty == 'I':
                rest_day_types['I'] += 1
            elif duty == 'V':
                rest_day_types['V'] += 1

        # Counting overnight shifts
        if '+' in time_end:  # Overnight shifts
            total_overnight_shifts += 1

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
        output_file.write(f"  BC (Barcelona): {shift_destinations['BC']}\n")
        output_file.write(f"  VL (Valencia): {shift_destinations['VL']}\n")
        output_file.write(f"  AG (Malaga): {shift_destinations['AG']}\n")
        output_file.write(f"  SV (Sevilla): {shift_destinations['SV']}\n")
        output_file.write(f"  AL (Alicante): {shift_destinations['AL']}\n")
        output_file.write(f"Total Rest Days: {total_rest_days}\n")
        output_file.write(f"  D: {rest_day_types['D']}\n")
        output_file.write(f"  I: {rest_day_types['I']}\n")
        output_file.write(f"  V: {rest_day_types['V']}\n")
        output_file.write(f"Total Overnight Shifts: {total_overnight_shifts}\n")

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
    print(f"  BC (Barcelona): {shift_destinations['BC']}")
    print(f"  VL (Valencia): {shift_destinations['VL']}")
    print(f"  AG (Malaga): {shift_destinations['AG']}")
    print(f"  SV (Sevilla): {shift_destinations['SV']}")
    print(f"  AL (Alicante): {shift_destinations['AL']}")
    print(f"Total Rest Days: {total_rest_days}")
    print(f"  D: {rest_day_types['D']}")
    print(f"  I: {rest_day_types['I']}")
    print(f"  V: {rest_day_types['V']}")
    print(f"Total Overnight Shifts: {total_overnight_shifts}\n")

    # Print the detailed schedule
    print("\nEmployee Schedule:")
    print("{:<12} {:<10} {:<10} {:<10}".format("Date", "Duty", "Start Time", "End Time"))
    print("-" * 44)
    for row in rows:
        print("{:<12} {:<10} {:<10} {:<10}".format(row['date'], row['duty'], row['time_start'], row['time_end']))

# Parse 'untitled.html'
file_path = 'untitled.html'
parse_schedule(file_path)
