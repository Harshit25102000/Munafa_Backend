from datetime import datetime, timedelta
import random


def generate_date_and_value_lists():
    # Generate a list of dates from the last 30 days
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]

    # Generate a list of fluctuating values
    initial_value = 189
    value_list = [initial_value]
    for _ in range(29):  # 29 more values to match the length of date_list
        fluctuation = random.choice([-3, -2, -1, 1, 2, 3])  # Fluctuate by -3, -2, -1, 1, 2, or 3
        new_value = value_list[-1] + fluctuation
        value_list.append(new_value)

    return date_list, value_list


# Example usage
dates, values = generate_date_and_value_lists()
print("Dates:", dates)
print("Values:", values)
