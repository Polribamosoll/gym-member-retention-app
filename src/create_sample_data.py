"""
Script to generate sample gym member data.
"""
import pandas as pd
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from auxiliar.auxiliar import generate_data


def main():
    """Generate and save sample gym data."""
    print("Generating gym member data...")
    
    # Generate data (returns two tables)
    users_df, visits_df = generate_data(num_users=300, visits_per_user=(5, 20))
    
    print(f"Generated {len(users_df)} users and {len(visits_df)} visit records")
    
    # Show users sample
    print("\n=== USERS TABLE (sample) ===")
    print(users_df.head(10))
    
    # Show visits sample
    print("\n=== VISITS TABLE (sample) ===")
    print(visits_df.head(10))
    
    # Show churn statistics
    print("\n=== CHURN STATISTICS ===")
    churned_users = users_df['MEMBERSHIP_END_DATE'].notna().sum()
    active_users = users_df['MEMBERSHIP_END_DATE'].isna().sum()
    print(f"Churned users: {churned_users} ({churned_users/len(users_df)*100:.1f}%)")
    print(f"Active users:  {active_users} ({active_users/len(users_df)*100:.1f}%)")
    
    # Show class enrollment stats
    print("\n=== CLASS ENROLLMENT ===")
    print(f"ZUMBA:     {users_df['ZUMBA'].sum()} users ({users_df['ZUMBA'].mean()*100:.1f}%)")
    print(f"BODY_PUMP: {users_df['BODY_PUMP'].sum()} users ({users_df['BODY_PUMP'].mean()*100:.1f}%)")
    print(f"PILATES:   {users_df['PILATES'].sum()} users ({users_df['PILATES'].mean()*100:.1f}%)")
    print(f"SPINNING:  {users_df['SPINNING'].sum()} users ({users_df['SPINNING'].mean()*100:.1f}%)")
    
    # Show registration date range
    print("\nRegistration date range:")
    print(f"  Earliest: {users_df['REGISTRATION_DATE'].min()}")
    print(f"  Latest: {users_df['REGISTRATION_DATE'].max()}")
    
    # Save to data folder
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Save users table
    users_path = data_dir / 'user_information.csv'
    users_df.to_csv(users_path, index=False)
    print(f"\nUsers data saved to: {users_path}")
    
    # Save visits table
    visits_path = data_dir / 'user_visits.csv'
    visits_df.to_csv(visits_path, index=False)
    print(f"Visits data saved to: {visits_path}")


if __name__ == '__main__':
    main()
