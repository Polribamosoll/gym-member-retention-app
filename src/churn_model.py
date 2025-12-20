"""
Churn prediction model for gym members.

This module provides model training functionality to predict which gym members 
are at risk of cancelling their membership.
"""

import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib

# Import engineer_features from auxiliar module
from auxiliar.auxiliar import engineer_features


# Feature columns used by the model
FEATURE_COLUMNS = [
    'total_visits', 'visits_per_month', 'avg_session_duration_min',
    'days_since_last_visit', 'avg_days_between_visits', 'std_days_between_visits',
    'visits_last_30_days', 'visits_last_60_days', 'visits_last_90_days',
    'pct_peak_hour_visits', 'pct_weekend_visits', 'visit_frequency_trend',
    'membership_duration_months', 'AGE', 'GENDER',
    'ZUMBA', 'BODY_PUMP', 'PILATES', 'SPINNING', 'num_classes_enrolled'
]


def train_churn_model(
    features_df: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, pd.DataFrame, pd.DataFrame]:
    """
    Train a Random Forest model to predict churn.
    
    Args:
        features_df: DataFrame with engineered features (output of engineer_features)
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (trained model, X_test, y_test) for evaluation
    """
    X = features_df[FEATURE_COLUMNS]
    y = features_df['CHURNED']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Train Random Forest model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=random_state,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    return model, X_test, y_test


def evaluate_model(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> dict:
    """
    Evaluate the churn prediction model.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
    
    Returns:
        Dictionary with evaluation metrics
    """
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    return {
        'classification_report': classification_report(y_test, y_pred, target_names=['Active', 'Churned']),
        'roc_auc_score': roc_auc_score(y_test, y_pred_proba),
        'predictions': y_pred,
        'probabilities': y_pred_proba
    }


def get_feature_importance(model: RandomForestClassifier) -> pd.DataFrame:
    """
    Get feature importance from the trained model.
    
    Args:
        model: Trained model
    
    Returns:
        DataFrame with features sorted by importance
    """
    return pd.DataFrame({
        'feature': FEATURE_COLUMNS,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)


def predict_churn_risk(
    model: RandomForestClassifier,
    features_df: pd.DataFrame,
    active_only: bool = True
) -> pd.DataFrame:
    """
    Predict churn risk for users.
    
    Args:
        model: Trained model
        features_df: DataFrame with engineered features
        active_only: If True, only predict for active users
    
    Returns:
        DataFrame with USER_ID, churn_risk, and risk_level
    """
    if active_only:
        users = features_df[features_df['CHURNED'] == 0].copy()
    else:
        users = features_df.copy()
    
    users['churn_risk'] = model.predict_proba(users[FEATURE_COLUMNS])[:, 1]
    
    # Categorize risk levels
    users['risk_level'] = pd.cut(
        users['churn_risk'],
        bins=[0, 0.3, 0.6, 1.0],
        labels=['Low', 'Medium', 'High']
    )
    
    return users[['USER_ID', 'churn_risk', 'risk_level']].sort_values('churn_risk', ascending=False)


def save_model(model: RandomForestClassifier, filepath: str) -> None:
    """Save the trained model to a file."""
    joblib.dump(model, filepath)
    print(f"Model saved to: {filepath}")


def load_model(filepath: str) -> RandomForestClassifier:
    """Load a trained model from a file."""
    return joblib.load(filepath)
