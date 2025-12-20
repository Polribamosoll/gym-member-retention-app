"""
Auxiliar module for generating and processing gym member data.
"""

import random
from datetime import datetime, timedelta
from typing import Tuple
import pandas as pd


def generate_data(num_users: int = 300, visits_per_user: tuple = (5, 20), churn_rate: float = 0.35) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic gym member data with realistic patterns.
    
    Args:
        num_users: Number of unique users to generate (default: 300)
        visits_per_user: Tuple of (min, max) visits per user (default: 5-20)
        churn_rate: Percentage of users who have churned (default: 0.35 = 35%)
    
    Returns:
        Tuple of (users_df, visits_df):
        - users_df: Static user data (USER_ID, REGISTRATION_DATE, AGE, GENDER, ZUMBA, BODY_PUMP, PILATES, SPINNING, MEMBERSHIP_END_DATE)
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
        
        # Determine if user has churned
        has_churned = random.random() < churn_rate
        membership_end_date = None
        
        if has_churned:
            # Generate membership end date (first day of a month, after registration)
            # Churned users should have left at least 1 month ago
            min_membership_months = 1  # At least 1 month of membership
            months_since_registration = (today.year - registration_date.year) * 12 + (today.month - registration_date.month)
            
            if months_since_registration > min_membership_months:
                # Random end month between (registration + 1 month) and (today - 1 month)
                months_of_membership = random.randint(min_membership_months, max(min_membership_months, months_since_registration - 1))
                
                # Calculate end date (first day of the end month)
                end_year = registration_date.year + (registration_date.month + months_of_membership - 1) // 12
                end_month = (registration_date.month + months_of_membership - 1) % 12 + 1
                membership_end_date = datetime(end_year, end_month, 1, 0, 0, 0)
        
        # Randomly assign class preferences (~20% chance each, users can have all, some, or none)
        zumba = random.random() < 0.20
        body_pump = random.random() < 0.20
        pilates = random.random() < 0.20
        spinning = random.random() < 0.20
        
        # Add user record (static data)
        user_records.append({
            'USER_ID': user_id,
            'REGISTRATION_DATE': registration_date,
            'MEMBERSHIP_END_DATE': membership_end_date,
            'AGE': age,
            'GENDER': gender,
            'ZUMBA': zumba,
            'BODY_PUMP': body_pump,
            'PILATES': pilates,
            'SPINNING': spinning
        })
        
        # Generate visits for this user
        num_visits = random.randint(visits_per_user[0], visits_per_user[1])
        
        # Determine the last possible visit date
        if membership_end_date:
            last_visit_date = membership_end_date - timedelta(days=1)  # Last visit before membership ends
        else:
            last_visit_date = today
        
        # Generate visit dates after registration but before membership end (if churned)
        days_available = (last_visit_date - registration_date).days
        if days_available < 1:
            days_available = 1
        
        for _ in range(num_visits):
            # Random day after registration (but before last_visit_date)
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


def engineer_features(users_df: pd.DataFrame, visits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create features for churn prediction from user and visit data.
    
    Args:
        users_df: DataFrame with user information (USER_ID, REGISTRATION_DATE, 
                  MEMBERSHIP_END_DATE, AGE, GENDER, class enrollments)
        visits_df: DataFrame with visit records (USER_ID, ENTRY_TIME, EXIT_TIME)
    
    Returns:
        DataFrame with engineered features for each user, including:
        - Visit frequency metrics (total_visits, visits_per_month)
        - Recency metrics (days_since_last_visit)
        - Session patterns (avg_session_duration_min, avg_days_between_visits)
        - Time preferences (pct_peak_hour_visits, pct_weekend_visits)
        - Trend indicators (visit_frequency_trend)
        - Demographics (AGE, GENDER, class enrollments)
    """
    # Reference date (use today for active users, end date for churned)
    reference_date = datetime.now()
    
    # Calculate visit-based features for each user
    visit_features = []
    
    for user_id in users_df['USER_ID']:
        user_visits = visits_df[visits_df['USER_ID'] == user_id].copy()
        user_info = users_df[users_df['USER_ID'] == user_id].iloc[0]
        
        # Determine reference date for this user
        if pd.notna(user_info['MEMBERSHIP_END_DATE']):
            ref_date = user_info['MEMBERSHIP_END_DATE']
            churned = 1
        else:
            ref_date = reference_date
            churned = 0
        
        registration_date = user_info['REGISTRATION_DATE']
        membership_duration_days = (ref_date - registration_date).days
        
        if len(user_visits) == 0:
            visit_features.append({
                'USER_ID': user_id,
                'CHURNED': churned,
                'total_visits': 0,
                'visits_per_month': 0,
                'avg_session_duration_min': 0,
                'days_since_last_visit': membership_duration_days,
                'avg_days_between_visits': 0,
                'std_days_between_visits': 0,
                'visits_last_30_days': 0,
                'visits_last_60_days': 0,
                'visits_last_90_days': 0,
                'pct_peak_hour_visits': 0,
                'pct_weekend_visits': 0,
                'visit_frequency_trend': 0,
                'membership_duration_months': membership_duration_days / 30
            })
            continue
        
        # Sort visits by time
        user_visits = user_visits.sort_values('ENTRY_TIME')
        
        # Total visits
        total_visits = len(user_visits)
        
        # Visits per month
        months_active = max(1, membership_duration_days / 30)
        visits_per_month = total_visits / months_active
        
        # Session duration
        user_visits['duration_min'] = (user_visits['EXIT_TIME'] - user_visits['ENTRY_TIME']).dt.total_seconds() / 60
        avg_session_duration = user_visits['duration_min'].mean()
        
        # Days since last visit (from reference date)
        last_visit = user_visits['ENTRY_TIME'].max()
        days_since_last_visit = (ref_date - last_visit).days
        
        # Days between visits
        if len(user_visits) > 1:
            user_visits['days_since_prev'] = user_visits['ENTRY_TIME'].diff().dt.days
            avg_days_between = user_visits['days_since_prev'].mean()
            std_days_between = user_visits['days_since_prev'].std()
        else:
            avg_days_between = 0
            std_days_between = 0
        
        # Visits in last X days (before reference date)
        visits_last_30 = len(user_visits[user_visits['ENTRY_TIME'] >= ref_date - timedelta(days=30)])
        visits_last_60 = len(user_visits[user_visits['ENTRY_TIME'] >= ref_date - timedelta(days=60)])
        visits_last_90 = len(user_visits[user_visits['ENTRY_TIME'] >= ref_date - timedelta(days=90)])
        
        # Peak hour visits (5pm-8pm)
        user_visits['hour'] = user_visits['ENTRY_TIME'].dt.hour
        peak_visits = len(user_visits[(user_visits['hour'] >= 17) & (user_visits['hour'] < 20)])
        pct_peak_hour = peak_visits / total_visits if total_visits > 0 else 0
        
        # Weekend visits
        user_visits['weekday'] = user_visits['ENTRY_TIME'].dt.weekday
        weekend_visits = len(user_visits[user_visits['weekday'] >= 5])
        pct_weekend = weekend_visits / total_visits if total_visits > 0 else 0
        
        # Visit frequency trend (compare first half vs second half of membership)
        mid_date = registration_date + timedelta(days=membership_duration_days / 2)
        first_half_visits = len(user_visits[user_visits['ENTRY_TIME'] < mid_date])
        second_half_visits = len(user_visits[user_visits['ENTRY_TIME'] >= mid_date])
        
        if first_half_visits > 0:
            visit_frequency_trend = (second_half_visits - first_half_visits) / first_half_visits
        else:
            visit_frequency_trend = 0
        
        visit_features.append({
            'USER_ID': user_id,
            'CHURNED': churned,
            'total_visits': total_visits,
            'visits_per_month': visits_per_month,
            'avg_session_duration_min': avg_session_duration,
            'days_since_last_visit': days_since_last_visit,
            'avg_days_between_visits': avg_days_between if not pd.isna(avg_days_between) else 0,
            'std_days_between_visits': std_days_between if not pd.isna(std_days_between) else 0,
            'visits_last_30_days': visits_last_30,
            'visits_last_60_days': visits_last_60,
            'visits_last_90_days': visits_last_90,
            'pct_peak_hour_visits': pct_peak_hour,
            'pct_weekend_visits': pct_weekend,
            'visit_frequency_trend': visit_frequency_trend,
            'membership_duration_months': membership_duration_days / 30
        })
    
    features_df = pd.DataFrame(visit_features)
    
    # Merge with user demographics
    user_demographics = users_df[['USER_ID', 'AGE', 'GENDER', 'ZUMBA', 'BODY_PUMP', 'PILATES', 'SPINNING']].copy()
    features_df = features_df.merge(user_demographics, on='USER_ID')
    
    # Encode gender
    features_df['GENDER'] = (features_df['GENDER'] == 'M').astype(int)
    
    # Convert boolean columns to int
    for col in ['ZUMBA', 'BODY_PUMP', 'PILATES', 'SPINNING']:
        features_df[col] = features_df[col].astype(int)
    
    # Count total classes enrolled
    features_df['num_classes_enrolled'] = features_df[['ZUMBA', 'BODY_PUMP', 'PILATES', 'SPINNING']].sum(axis=1)
    
    return features_df
