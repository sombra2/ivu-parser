from bs4 import BeautifulSoup
import re  # For replacing invalid filename characters
from datetime import datetime, timedelta  # For timestamp and time difference

# Function to calculate hours between start and end time
def calculate_hours(start_time, end_time):
    # Convert times into datetime objects
    time_format = "%H:%M"
    start = datetime.strptime(start_time, time_format)
    
    # If the shift ends with a '+', add 24 hours to the end time
    if '+' in end_time:
        end_time = end_time.rstrip('+')  # Remove the '+' before processing
        end = datetime.strptime(end_time, time_format) + timedelta(days=1)  # Add 1 day to handle past midnight
    else:
        end = datetime.strptime(end_time, time_format)
    
    # Calculate the difference in hours and minutes
    duration = end - start
    hours = duration.total_seconds() / 3600  # Convert to hours
    return round(hours, 2)  # Round to 2 decimal places

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
    total_hours = 0  # To track the total hours worked across all shifts
    total_non_overnight_hours = 0  # To track total hours for non-overnight shifts (less than 12 hours)
    non_overnight_shifts = 0  # To count shifts that are less than 12 hours
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

        # Calculate and add hours worked for the shift
        if time_start != '----' and time_end != '----':  # Only calculate if valid times exist
            hours = calculate_hours(time_start, time_end)
            total_hours += hours  # Add the calculated hours to the total
            
            # Only count non-overnight shifts with less than 12 hours
            if hours < 12 and '+' not in time_end:  # Exclude overnight shifts and those with more than 12 hours
                total_non_overnight_hours += hours
                non_overnight_shifts += 1

        rows.append({
            'date': date,
            'duty': duty,
            'time_start': time_start,
            'time_end': time_end,
            'hours': round(hours, 2) if time_start != '----' and time_end != '----' else 0  # Add the hours worked for this shift, defaulting to 0 if not available
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
        
        # Adding average hours per shift excluding sleepovers
        if non_overnight_shifts > 0:
            average_hours = total_non_overnight_hours / non_overnight_shifts
            output_file.write(f"\nAverage Hours per Shift (Excl. Sleepovers): {average_hours:.2f} hours\n")
        else:
            output_file.write(f"\nAverage Hours per Shift (Excl. Sleepovers): N/A\n")

        output_file.write(f"\nTotal Rest Days: {total_rest_days}\n")
        output_file.write(f"  D: {rest_day_types['D']}\n")
        output_file.write(f"  I: {rest_day_types['I']}\n")
        output_file.write(f"  V: {rest_day_types['V']}\n")

        # Write schedule table with the new "Hours" column
        output_file.write("\nSchedule:\n")
        output_file.write("{:<12} {:<10} {:<10} {:<10} {:<10}\n".format("Date", "Duty", "Start Time", "End Time", "Hours"))
        output_file.write("-" * 54 + "\n")
        for row in rows:
            output_file.write("{:<12} {:<10} {:<10} {:<10} {:<10}\n".format(row['date'], row['duty'], row['time_start'], row['time_end'], row['hours']))
        
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

    # Print the average hours for non-overnight shifts
    if non_overnight_shifts > 0:
        average_hours = total_non_overnight_hours / non_overnight_shifts
        print(f"\nAverage Hours per Shift (Excl. Sleepovers): {average_hours:.2f} hours")
    else:
        print(f"\nAverage Hours per Shift (Excl. Sleepovers): N/A")

    print(f"Total Rest Days: {total_rest_days}")
    print(f"  D: {rest_day_types['D']}")
    print(f"  I: {rest_day_types['I']}")
    print(f"  V: {rest_day_types['V']}\n")

    # Print the detailed schedule
    print("\nEmployee Schedule:")
    print("{:<12} {:<10} {:<10} {:<10} {:<10}".format("Date", "Duty", "Start Time", "End Time", "Hours"))
    print("-" * 54)
    for row in rows:
        print("{:<12} {:<10} {:<10} {:<10} {:<10}".format(row['date'], row['duty'], row['time_start'], row['time_end'], row['hours']))

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
