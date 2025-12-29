import json

def name_entrances(entrances_file, output_file=None):
    """
    Add names and room numbers to entrances in the JSON file.
    Only entrances with data in the dictionary will have attributes added.
    """
    
    # Define entrance details - add name, room_no, and/or available for each entrance
    entrance_details = {
        # Format: entrance_id: {"name": "...", "room_no": "...", "available": True/False/None}
        # You can include any combination, or use None for null values
        3: {"name": "Gents Toilet", "room_no": "114", "available": True},
        6: {"name": "Software Computing Lab", "room_no": "115", "available": True},
        8: {"name": "Software Computing Lab", "room_no": "115", "available": True},
        2: {"name": "Gents Waiting Room", "room_no": "113", "available": True},
        5: {"name": "Staff Room", "room_no": "112", "available": True},
        7: {"name": "HOD Office", "room_no": "111", "available": True},
        25: {"name": "Lecture Hall", "room_no": "105", "available": True},
        26: {"name": "Lecture Hall", "room_no": "105", "available": True},
        27: {"name": "HO Office", "room_no": "110", "available": True},
        28: {"name": "Staff Room", "room_no": "109", "available": True},
        29: {"name": "Lecture Hall", "room_no": "106", "available": True},
        31: {"name": "Lecture Hall", "room_no": "106", "available": True},
        30: {"name": "Ladies Toilet", "room_no": "108", "available": True},
        32: {"name": "Ladies Waiting Room", "room_no": "107", "available": True},
        4: {"name": None, "room_no": None, "available": True},
        1: {"name": "Lift", "room_no": None, "available": True},
        9: {"name": None, "room_no": None, "available": True},
        10: {"name": None, "room_no": None, "available": True},
        11: {"name": None, "room_no": None, "available": True},
        19: {"name": None, "room_no": None, "available": True},
        17: {"name": None, "room_no": None, "available": True},
        15: {"name": None, "room_no": None, "available": True},
        13: {"name": None, "room_no": None, "available": True},
        20: {"name": None, "room_no": None, "available": True},
        18: {"name": None, "room_no": None, "available": True},
        16: {"name": None, "room_no": None, "available": True},
        14: {"name": None, "room_no": None, "available": True},
        35: {"name": None, "room_no": None, "available": True},
        34: {"name": None, "room_no": None, "available": True},
        12: {"name": None, "room_no": None, "available": True},
        21: {"name": None, "room_no": None, "available": True},
        24: {"name": None, "room_no": None, "available": True},
        23: {"name": None, "room_no": None, "available": True},
        22: {"name": None, "room_no": None, "available": True},
        33: {"name": None, "room_no": None, "available": True},
    }
    
    if output_file is None:
        output_file = entrances_file
    
    # Load current entrances
    with open(entrances_file, 'r') as f:
        data = json.load(f)
    
    # Add details to entrances that have them defined
    for entrance in data['entrances']:
        entrance_id = entrance['id']
        if entrance_id in entrance_details:
            details = entrance_details[entrance_id]
            if 'name' in details:
                entrance['name'] = details['name']
            if 'room_no' in details:
                entrance['room_no'] = details['room_no']
            if 'available' in details:
                entrance['available'] = details['available']
    
    # Save updated data
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Print summary
    named_count = sum(1 for e in data['entrances'] if 'name' in e)
    room_count = sum(1 for e in data['entrances'] if 'room_no' in e)
    available_count = sum(1 for e in data['entrances'] if 'available' in e)
    print(f"Updated entrances: {named_count} have names, {room_count} have room numbers, {available_count} have availability")
    print(f"Saved to {output_file}")

if __name__ == '__main__':
    name_entrances('json/first_floor_entrances.json')
