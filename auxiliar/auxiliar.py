"""
Auxiliar module for generating synthetic gym member data.
"""

import random
from datetime import datetime, timedelta
from typing import Tuple
import pandas as pd


def generate_data(num_users: int = 100, visits_per_user: tuple = (5, 20)) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic gym member data with realistic patterns.
    
    Args:
        num_users: Number of unique users to generate (default: 100)
        visits_per_user: Tuple of (min, max) visits per user (default: 5-20)
    
    Returns:
        Tuple of (users_df, visits_df):
        - users_df: Static user data (USER_ID, REGISTRATION_DATE, AGE, GENDER, ZUMBA, BODY_PUMP, PILATES, SPINNING)
        - visits_df: Visit records (USER_ID, ENTRY_TIME, EXIT_TIME)
    """
    random.seed(42)  # For reproducibility
    
    # Define time ranges
    gym_open_hour = 9   # 9 AM
    gym_close_hour = 21  # 9 PM
    
    # Peak hours distribution (5pm-8pm = hours 17-20)
    hour_weights = []
    for hour in range(gym_open_hour, gym_close_hour):
        if 17 <= hour < 20:  # Peak hours 5pm-8pm
            hour_weights.append(3.0)  # 3x more likely
        elif 12 <= hour < 14:  # Lunch hours
            hour_weights.append(1.5)
        elif 6 <= hour < 9:  # Early morning
            hour_weights.append(1.2)
        else:
            hour_weights.append(1.0)
    
    available_hours = list(range(gym_open_hour, gym_close_hour))
    
    # Generate 5-digit user IDs
    user_ids = random.sample(range(10000, 99999), num_users)
    
    # Reference date for data generation
    today = datetime.now()
    
    # Lists to store records
    user_records = []
    visit_records = []
    
    for user_id in user_ids:
        # Generate user demographics
        age = random.randint(18, 70)
        gender = random.choice(['M', 'F'])
        
        # Registration date: between 4 years ago (gym opening) and 1 month ago
        days_since_registration = random.randint(30, 1460)  # ~4 years = 1460 days
        registration_date = today - timedelta(days=days_since_registration)
        registration_date = registration_date.replace(
            hour=random.randint(9, 20),
            minute=random.randint(0, 59),
            second=0,
            microsecond=0
        )
        
        # Randomly assign class preferences (~20% chance each, users can have all, some, or none)
        zumba = random.random() < 0.20
        body_pump = random.random() < 0.20
        pilates = random.random() < 0.20
        spinning = random.random() < 0.20
        
        # Add user record (static data)
        user_records.append({
            'USER_ID': user_id,
            'REGISTRATION_DATE': registration_date,
            'AGE': age,
            'GENDER': gender,
            'ZUMBA': zumba,
            'BODY_PUMP': body_pump,
            'PILATES': pilates,
            'SPINNING': spinning
        })
        
        # Generate visits for this user
        num_visits = random.randint(visits_per_user[0], visits_per_user[1])
        
        # Generate visit dates after registration
        days_available = (today - registration_date).days
        if days_available < 1:
            days_available = 1
        
        for _ in range(num_visits):
            # Random day after registration (but before today)
            days_after_reg = random.randint(1, max(1, days_available - 1))
            visit_date = registration_date + timedelta(days=days_after_reg)
            
            # Select entry hour based on weighted distribution
            entry_hour = random.choices(available_hours, weights=hour_weights)[0]
            entry_minute = random.randint(0, 59)
            
            # Create entry time
            entry_time = visit_date.replace(
                hour=entry_hour,
                minute=entry_minute,
                second=0,
                microsecond=0
            )
            
            # Duration with realistic distribution (mean ~55 min, most under 100)
            if random.random() < 0.9:  # 90% of sessions
                duration_minutes = int(random.triangular(30, 100, 45))
            else:  # 10% longer sessions
                duration_minutes = int(random.triangular(90, 180, 110))
            exit_time = entry_time + timedelta(minutes=duration_minutes)
            
            # Ensure exit time doesn't exceed gym closing (9 PM)
            max_exit = entry_time.replace(hour=21, minute=0)
            if exit_time > max_exit:
                exit_time = max_exit
            
            # Add visit record (using datetime objects)
            visit_records.append({
                'USER_ID': user_id,
                'ENTRY_TIME': entry_time,
                'EXIT_TIME': exit_time
            })
    
    # Create DataFrames
    users_df = pd.DataFrame(user_records)
    visits_df = pd.DataFrame(visit_records)
    
    # Sort visits by entry time
    visits_df = visits_df.sort_values('ENTRY_TIME').reset_index(drop=True)
    
    return users_df, visits_df
