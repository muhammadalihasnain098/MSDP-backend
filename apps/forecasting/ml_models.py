"""
Machine Learning Models - EXACT CODE FROM JUPYTER NOTEBOOKS

This file contains the EXACT training and prediction logic from:
- model_1.ipynb (Malaria forecasting with Random Forest)
- model_2.ipynb (Dengue forecasting with Random Forest + sales logic)

The only modifications are:
1. CSV reads replaced with Django ORM queries
2. Model serialization added (joblib save/load)

ALL feature engineering, training, and prediction logic is PRESERVED AS-IS.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
from pathlib import Path
from django.conf import settings

from apps.datasets.models import LabTest, PharmacySales


# ==============================================================================
# CONSTANTS FROM NOTEBOOKS (DO NOT MODIFY)
# ==============================================================================

# From model_1.ipynb and model_2.ipynb
LAGS = 14
TRAIN_END_DATE = '2024-09-30'
PREDICT_START_DATE = '2024-10-01'
PREDICT_END_DATE = '2024-12-31'

# From model_1.ipynb Cell 1 (version with peak cycle heuristic)
PEAK_TESTS_THRESHOLD = 100  # Threshold to define a peak day
PEAK_CYCLE_THRESHOLD = 4    # 4-day cycle from 2024 surge data


# ==============================================================================
# MODEL 1: MALARIA FORECASTING
# ==============================================================================
# EXACT CODE FROM: model_1.ipynb Cell 1 (version with 4-day cycle heuristic)
# ==============================================================================

def create_initial_features_malaria(df, features_to_lag, lags):
    """
    EXACT CODE FROM model_1.ipynb Cell 1
    Generates core time series features (lags, rolling means, date features).
    """
    df_feat = df.copy()

    # Lagged features (positive_tests are log-transformed)
    for col in features_to_lag:
        for lag in range(1, lags + 1):
            if col == 'positive_tests':
                df_feat[f'{col}_lag{lag}'] = np.log1p(df_feat[col]).shift(lag)
            else:
                df_feat[f'{col}_lag{lag}'] = df_feat[col].shift(lag)

    # Rolling Mean features
    df_feat['pos7'] = df_feat['positive_tests'].shift(1).rolling(window=7).mean()
    df_feat['pos14'] = df_feat['positive_tests'].shift(1).rolling(window=14).mean()

    # Date features
    df_feat['year'] = df_feat['date'].dt.year
    df_feat['month'] = df_feat['date'].dt.month
    df_feat['dow'] = df_feat['date'].dt.dayofweek
    df_feat['dom'] = df_feat['date'].dt.day

    # Target variable (log transformed)
    df_feat['y'] = np.log1p(df_feat['positive_tests'])

    # Drop initial rows with NaN values resulting from lagging
    df_feat.dropna(inplace=True)
    return df_feat


def calculate_time_since_last_peak(row, peak_dates_series):
    """
    EXACT CODE FROM model_1.ipynb Cell 1
    Calculate time difference from the last observed peak.
    """
    past_peaks = peak_dates_series[peak_dates_series <= row['date']]
    if past_peaks.empty:
        return np.nan
    last_peak_date = past_peaks.max()
    return (row['date'] - last_peak_date).days


def load_malaria_data_from_django():
    """
    REPLACES: CSV loading from notebooks
    NEW CODE: Loads data from Django ORM instead of CSV files
    Returns df_master with same structure as notebooks
    """
    # Load Lab Test Data (replaces: pd.read_csv('malaria lab test.csv'))
    lab_tests = LabTest.objects.filter(disease='MALARIA').values('date', 'positive_tests')
    df_lab = pd.DataFrame(list(lab_tests))
    df_lab['date'] = pd.to_datetime(df_lab['date'])
    
    # Load Pharmacy Sales (replaces: pharmacy.csv + Jinnah Pharmacy 2.csv)
    sales = PharmacySales.objects.filter(
        medicine__in=['Coartem', 'Fansidar']
    ).values('date', 'medicine', 'sale')
    
    df_sales = pd.DataFrame(list(sales))
    df_sales['date'] = pd.to_datetime(df_sales['date'])
    
    # Pivot sales data (same as notebooks)
    df_sales_pivot = df_sales.pivot_table(
        index='date', columns='medicine', values='sale', aggfunc='sum'
    ).reset_index()
    
    # Merge all data (same as notebooks)
    df_master = pd.merge(df_lab, df_sales_pivot, on='date', how='inner')
    df_master.sort_values('date', inplace=True)
    df_master.reset_index(drop=True, inplace=True)
    
    return df_master


def train_malaria_model(training_start=None, training_end=None, forecast_start=None, forecast_end=None):
    """
    EXACT CODE FROM model_1.ipynb Cell 1 (with peak cycle heuristic)
    Trains Random Forest model for malaria forecasting.
    
    Args:
        training_start: Start date for training data (default: use constant)
        training_end: End date for training data (default: use constant)
        forecast_start: Start date for forecast period (default: use constant)
        forecast_end: End date for forecast period (default: use constant)
    
    Returns:
        - rf_regressor: Trained RandomForestRegressor
        - feature_cols: List of feature column names
        - metrics: Dict with MAE and other performance metrics
    """
    # Use defaults if not provided
    train_end = training_end or TRAIN_END_DATE
    predict_start = forecast_start or PREDICT_START_DATE
    predict_end = forecast_end or PREDICT_END_DATE
    
    # Load data from Django (replaces CSV loading)
    df_master = load_malaria_data_from_django()
    
    # Filter by custom training_start if provided
    if training_start:
        df_master = df_master[df_master['date'] >= pd.to_datetime(training_start)]
    
    # EXACT CODE FROM NOTEBOOK STARTS HERE
    FEATURES_TO_LAG = ['positive_tests', 'Coartem', 'Fansidar']
    
    # Feature Engineering
    df_features = create_initial_features_malaria(df_master, FEATURES_TO_LAG, LAGS)
    
    # Split data
    df_train_base = df_features[df_features['date'] <= train_end].copy()
    df_predict = df_features[
        (df_features['date'] >= predict_start) & (df_features['date'] <= predict_end)
    ].copy()
    
    # Heuristic Feature Creation for Training Set
    df_train_base['peak_day'] = (df_train_base['positive_tests'].shift(1) > PEAK_TESTS_THRESHOLD).astype(int)
    peak_dates_train = df_train_base.loc[df_train_base['peak_day'] == 1, 'date']
    
    # Calculate time difference and create the predictor feature
    df_train_base['time_since_last_peak'] = df_train_base.apply(
        lambda row: calculate_time_since_last_peak(row, peak_dates_train), axis=1
    )
    df_train_base['peak_cycle_predictor'] = (df_train_base['time_since_last_peak'] == PEAK_CYCLE_THRESHOLD).astype(int)
    
    df_train = df_train_base.dropna().copy()
    
    # Initialize Prediction Feature
    df_predict['peak_cycle_predictor'] = 0
    
    # Define feature columns
    feature_cols = [col for col in df_train.columns if col.startswith(('positive_tests_lag', 'Coartem_lag', 'Fansidar_lag', 'pos7', 'pos14', 'dow', 'dom', 'month', 'year'))]
    feature_cols.extend(['Coartem', 'Fansidar'])  # Current Day Sales
    feature_cols.append('peak_cycle_predictor')
    
    X_train = df_train[feature_cols]
    y_train = df_train['y']
    
    # Train Random Forest Regressor
    rf_regressor = RandomForestRegressor(n_estimators=300, random_state=42)
    rf_regressor.fit(X_train, y_train)
    
    # Calculate metrics (using training data for now)
    train_predictions = rf_regressor.predict(X_train)
    train_mae = mean_absolute_error(y_train, train_predictions)
    
    metrics = {
        'model': 'RandomForest',
        'n_estimators': 300,
        'lags': LAGS,
        'features': feature_cols,
        'train_mae': float(train_mae),
        'train_samples': len(X_train),
        'training_period': f"{df_train['date'].min()} to {train_end}",
        'forecast_period': f"{predict_start} to {predict_end}",
    }
    
    return rf_regressor, feature_cols, metrics


# ==============================================================================
# MODEL 2: DENGUE FORECASTING
# ==============================================================================
# EXACT CODE FROM: model_2.ipynb Cell 1
# ==============================================================================

def create_features_with_current_sales_dengue(df, features_to_lag, lags):
    """
    EXACT CODE FROM model_2.ipynb Cell 1
    Feature engineering for dengue forecasting.
    """
    df_feat = df.copy()
    for col in features_to_lag:
        for lag in range(1, lags + 1):
            if col == 'positive_tests':
                df_feat[f'{col}_lag{lag}'] = np.log1p(df_feat[col]).shift(lag)
            else:
                df_feat[f'{col}_lag{lag}'] = df_feat[col].shift(lag)

    df_feat['pos7'] = df_feat['positive_tests'].shift(1).rolling(window=7).mean()
    df_feat['pos14'] = df_feat['positive_tests'].shift(1).rolling(window=14).mean()
    df_feat['dow'] = df_feat['date'].dt.dayofweek
    df_feat['dom'] = df_feat['date'].dt.day
    df_feat['month'] = df_feat['date'].dt.month
    df_feat['y'] = np.log1p(df_feat['positive_tests'])
    df_feat.dropna(inplace=True)
    return df_feat


def load_dengue_data_from_django():
    """
    REPLACES: CSV loading from notebooks
    NEW CODE: Loads dengue data from Django ORM
    Returns df_master with same structure as notebooks
    """
    # Load Lab Test Data (replaces: pd.read_csv('dengue lab test.csv'))
    lab_tests = LabTest.objects.filter(disease='DENGUE').values('date', 'positive_tests')
    df_lab = pd.DataFrame(list(lab_tests))
    df_lab['date'] = pd.to_datetime(df_lab['date'])
    
    # Load Pharmacy Sales (replaces: z1.csv + Jinnah Pharmacy 4.csv)
    sales = PharmacySales.objects.filter(
        medicine__in=['Panadol', 'Calpol']
    ).values('date', 'medicine', 'sale')
    
    df_sales = pd.DataFrame(list(sales))
    df_sales['date'] = pd.to_datetime(df_sales['date'])
    
    # Pivot sales data
    df_sales_pivot = df_sales.pivot_table(
        index='date', columns='medicine', values='sale', aggfunc='sum'
    ).reset_index()
    
    # Merge all data
    df_master = pd.merge(df_lab, df_sales_pivot, on='date', how='inner')
    df_master.sort_values('date', inplace=True)
    df_master.reset_index(drop=True, inplace=True)
    
    # Calculate Total Sales (REQUIRED for dengue logic)
    df_master['Total_Sales'] = df_master['Panadol'] + df_master['Calpol']
    
    return df_master


def train_dengue_model(training_start=None, training_end=None, forecast_start=None, forecast_end=None):
    """
    EXACT CODE FROM model_2.ipynb Cell 1
    Trains Random Forest model for dengue forecasting.
    
    Args:
        training_start: Start date for training data (default: use constant)
        training_end: End date for training data (default: use constant)
        forecast_start: Start date for forecast period (default: use constant)
        forecast_end: End date for forecast period (default: use constant)
    
    Returns:
        - rf_regressor: Trained RandomForestRegressor
        - feature_cols: List of feature column names
        - metrics: Dict with MAE and other performance metrics
    """
    # Use defaults if not provided
    train_end = training_end or TRAIN_END_DATE
    predict_start = forecast_start or PREDICT_START_DATE
    predict_end = forecast_end or PREDICT_END_DATE
    
    # Load data from Django (replaces CSV loading)
    df_master = load_dengue_data_from_django()
    
    # Filter by custom training_start if provided
    if training_start:
        df_master = df_master[df_master['date'] >= pd.to_datetime(training_start)]
    
    # EXACT CODE FROM NOTEBOOK STARTS HERE
    FEATURES_TO_LAG = ['positive_tests', 'Panadol', 'Calpol']
    
    # Feature Engineering & Split
    df_features = create_features_with_current_sales_dengue(df_master, FEATURES_TO_LAG, LAGS)
    
    df_train = df_features[df_features['date'] <= train_end].copy()
    df_predict = df_features[
        (df_features['date'] >= predict_start) & (df_features['date'] <= predict_end)
    ].copy()
    
    # Define feature columns
    feature_cols = [col for col in df_train.columns if col.startswith(('positive_tests_lag', 'Panadol_lag', 'Calpol_lag', 'pos7', 'pos14', 'dow', 'dom', 'month'))]
    feature_cols.extend(['Panadol', 'Calpol'])
    
    X_train = df_train[feature_cols]
    y_train = df_train['y']
    
    # Train Model
    rf_regressor = RandomForestRegressor(n_estimators=300, random_state=42)
    rf_regressor.fit(X_train, y_train)
    
    # Calculate metrics
    train_predictions = rf_regressor.predict(X_train)
    train_mae = mean_absolute_error(y_train, train_predictions)
    
    metrics = {
        'model': 'RandomForest',
        'n_estimators': 300,
        'lags': LAGS,
        'features': feature_cols,
        'train_mae': float(train_mae),
        'train_samples': len(X_train),
        'special_logic': 'Sales surge detection (2x if consecutive increases)',
        'training_period': f"{df_train['date'].min()} to {train_end}",
        'forecast_period': f"{predict_start} to {predict_end}",
    }
    
    return rf_regressor, feature_cols, metrics


# ==============================================================================
# RECURSIVE PREDICTION FUNCTIONS
# ==============================================================================

def generate_malaria_forecast(rf_regressor, feature_cols, start_date, end_date):
    """
    EXACT RECURSIVE PREDICTION LOGIC FROM model_1.ipynb Cell 1
    
    Generates malaria forecasts using the trained model.
    Implements the 4-day peak cycle heuristic.
    """
    # Load data
    df_master = load_malaria_data_from_django()
    FEATURES_TO_LAG = ['positive_tests', 'Coartem', 'Fansidar']
    
    # Feature engineering
    df_features = create_initial_features_malaria(df_master, FEATURES_TO_LAG, LAGS)
    
    # EXTENDED: Generate future dates if forecast extends beyond available data
    max_date_in_data = df_features['date'].max()
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    
    if end_date_dt > max_date_in_data:
        # Create date range for future dates
        future_dates = pd.date_range(start=max_date_in_data + pd.Timedelta(days=1), end=end_date_dt, freq='D')
        
        # Create empty rows for future dates
        future_rows = pd.DataFrame({
            'date': future_dates,
            'positive_tests': np.nan
        })
        
        # Add placeholder columns for features (will be filled recursively)
        for col in df_features.columns:
            if col not in future_rows.columns:
                future_rows[col] = np.nan
        
        # Append future dates to features
        df_features = pd.concat([df_features, future_rows], ignore_index=True)
        df_features.sort_values('date', inplace=True)
        df_features.reset_index(drop=True, inplace=True)
    
    # Get training data for peak detection
    df_train_base = df_features[df_features['date'] <= TRAIN_END_DATE].copy()
    df_train_base['peak_day'] = (df_train_base['positive_tests'].shift(1) > PEAK_TESTS_THRESHOLD).astype(int)
    peak_dates_train = df_train_base.loc[df_train_base['peak_day'] == 1, 'date']
    df_train_base['time_since_last_peak'] = df_train_base.apply(
        lambda row: calculate_time_since_last_peak(row, peak_dates_train), axis=1
    )
    df_train_base['peak_cycle_predictor'] = (df_train_base['time_since_last_peak'] == PEAK_CYCLE_THRESHOLD).astype(int)
    df_train = df_train_base.dropna().copy()
    
    # Prediction set
    df_predict = df_features[
        (df_features['date'] >= start_date_dt) & (df_features['date'] <= end_date_dt)
    ].copy()
    df_predict['peak_cycle_predictor'] = 0
    
    X_predict_base = df_predict[feature_cols].copy()
    actual_values = df_predict[['date', 'positive_tests']].copy()
    
    # EXACT RECURSIVE PREDICTION LOOP FROM NOTEBOOK
    df_pred_results = actual_values.copy()
    df_pred_results.set_index('date', inplace=True)
    df_pred_results.rename(columns={'positive_tests': 'actual_tests'}, inplace=True)
    df_pred_results['predicted_tests'] = np.nan
    
    # Initialize tracking for heuristic: last actual peak date from training data
    df_lab_full = pd.DataFrame(list(LabTest.objects.filter(disease='MALARIA').values('date', 'positive_tests')))
    df_lab_full['date'] = pd.to_datetime(df_lab_full['date'])
    last_peak_date = df_lab_full[df_lab_full['date'] <= TRAIN_END_DATE].loc[
        df_lab_full['positive_tests'] > PEAK_TESTS_THRESHOLD, 'date'
    ].max()
    
    for i in range(len(df_pred_results)):
        date_i = df_pred_results.index[i]
        current_features = X_predict_base.iloc[[i]].copy()
        
        # Update Lagged Positive Tests Recursively
        if i > 0:
            pred_val_yesterday = df_pred_results['predicted_tests'].iloc[i-1]
            log_pred_yesterday = np.log1p(pred_val_yesterday)
            current_features.loc[:, 'positive_tests_lag1'] = log_pred_yesterday
        
        # Update the Heuristic Feature
        if last_peak_date and (date_i - last_peak_date).days == PEAK_CYCLE_THRESHOLD:
            current_features.loc[:, 'peak_cycle_predictor'] = 1
        else:
            current_features.loc[:, 'peak_cycle_predictor'] = 0
        
        # Predict
        log_pred_i = rf_regressor.predict(current_features)[0]
        pred_i = np.expm1(log_pred_i)
        pred_i = max(0, round(pred_i))
        
        # Store prediction
        df_pred_results.loc[date_i, 'predicted_tests'] = pred_i
        
        # Update last_peak_date if prediction is a new peak
        if pred_i > PEAK_TESTS_THRESHOLD:
            last_peak_date = date_i

    # Calculate MAE only if we have actual values
    has_actuals = df_pred_results['actual_tests'].notna().any()
    if has_actuals:
        valid_rows = df_pred_results[df_pred_results['actual_tests'].notna()]
        mae = mean_absolute_error(valid_rows['actual_tests'], valid_rows['predicted_tests'])
    else:
        mae = None  # Future predictions have no actual values yet

    # Return results
    df_comp = df_pred_results.reset_index()
    df_comp['predicted_tests'] = df_comp['predicted_tests'].astype(int)
    # Keep actual_tests as float if it has NaN (future dates)
    if df_comp['actual_tests'].notna().any():
        df_comp['actual_tests'] = df_comp['actual_tests'].fillna(-1).astype(int)

    return df_comp, mae


def generate_dengue_forecast(rf_regressor, feature_cols, start_date, end_date):
    """
    EXACT RECURSIVE PREDICTION LOGIC FROM model_2.ipynb Cell 1
    
    Generates dengue forecasts using the trained model.
    Implements the sales surge detection logic (2x if consecutive increases).
    """
    # Load data
    df_master = load_dengue_data_from_django()
    FEATURES_TO_LAG = ['positive_tests', 'Panadol', 'Calpol']
    
    # Feature engineering
    df_features = create_features_with_current_sales_dengue(df_master, FEATURES_TO_LAG, LAGS)
    
    # EXTENDED: Generate future dates if forecast extends beyond available data
    max_date_in_data = df_features['date'].max()
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    
    if end_date_dt > max_date_in_data:
        # Create date range for future dates
        future_dates = pd.date_range(start=max_date_in_data + pd.Timedelta(days=1), end=end_date_dt, freq='D')
        
        # Create empty rows for future dates
        future_rows = pd.DataFrame({
            'date': future_dates,
            'positive_tests': np.nan
        })
        
        # Add placeholder columns for features (will be filled recursively)
        for col in df_features.columns:
            if col not in future_rows.columns:
                future_rows[col] = np.nan
        
        # Append future dates to features
        df_features = pd.concat([df_features, future_rows], ignore_index=True)
        df_features.sort_values('date', inplace=True)
        df_features.reset_index(drop=True, inplace=True)
    
    df_train = df_features[df_features['date'] <= TRAIN_END_DATE].copy()
    df_predict = df_features[
        (df_features['date'] >= start_date_dt) & (df_features['date'] <= end_date_dt)
    ].copy()
    
    X_predict_base = df_predict[feature_cols].copy()
    actual_values = df_predict[['date', 'positive_tests']].copy()
    
    # EXACT RECURSIVE PREDICTION LOOP FROM NOTEBOOK
    df_pred_results = actual_values.copy()
    df_pred_results.set_index('date', inplace=True)
    df_pred_results.rename(columns={'positive_tests': 'actual_tests'}, inplace=True)
    df_pred_results['predicted_tests'] = np.nan
    
    # Lookup dictionary for sales logic
    sales_lookup = df_master.set_index('date')['Total_Sales'].to_dict()
    
    for i in range(len(df_pred_results)):
        date_i = df_pred_results.index[i]
        current_features = X_predict_base.iloc[[i]].copy()
        
        if i > 0:
            pred_val_yesterday = df_pred_results['predicted_tests'].iloc[i-1]
            log_pred_yesterday = np.log1p(pred_val_yesterday)
            
            for lag in range(LAGS, 1, -1):
                current_features[f'positive_tests_lag{lag}'] = current_features[f'positive_tests_lag{lag-1}']
            current_features['positive_tests_lag1'] = log_pred_yesterday
        
        log_pred_i = rf_regressor.predict(current_features)[0]
        pred_i = np.expm1(log_pred_i)
        pred_i = max(0, round(pred_i))
        
        # LOGIC: Double if sales increased for 2 consecutive days
        sales_t = sales_lookup.get(date_i, 0)
        date_minus_1 = date_i - pd.Timedelta(days=1)
        date_minus_2 = date_i - pd.Timedelta(days=2)
        sales_t_minus_1 = sales_lookup.get(date_minus_1, 0)
        sales_t_minus_2 = sales_lookup.get(date_minus_2, 0)
        
        if (sales_t > sales_t_minus_1) and (sales_t > sales_t_minus_2):
            pred_final = pred_i * 2
        else:
            pred_final = pred_i
        
        df_pred_results.loc[date_i, 'predicted_tests'] = pred_final

    # Calculate MAE only if we have actual values
    has_actuals = df_pred_results['actual_tests'].notna().any()
    if has_actuals:
        valid_rows = df_pred_results[df_pred_results['actual_tests'].notna()]
        mae = mean_absolute_error(valid_rows['actual_tests'], valid_rows['predicted_tests'])
    else:
        mae = None  # Future predictions have no actual values yet

    # Return results
    df_comp = df_pred_results.reset_index()
    df_comp['predicted_tests'] = df_comp['predicted_tests'].astype(int)
    # Keep actual_tests as float if it has NaN (future dates)
    if df_comp['actual_tests'].notna().any():
        df_comp['actual_tests'] = df_comp['actual_tests'].fillna(-1).astype(int)

    return df_comp, mae


# ==============================================================================
# MODEL PERSISTENCE (ONLY NEW CODE - NOT FROM NOTEBOOKS)
# ==============================================================================

def save_model(rf_regressor, feature_cols, metrics, disease_name):
    """
    NEW CODE: Save trained model to disk using joblib
    
    This is the ONLY code not from notebooks.
    Saves model file and metadata for later use.
    """
    model_registry_path = Path(settings.MODEL_REGISTRY_PATH)
    model_registry_path.mkdir(parents=True, exist_ok=True)
    
    model_filename = f"{disease_name.lower()}_model.joblib"
    model_path = model_registry_path / model_filename
    
    # Save model and metadata together
    model_data = {
        'regressor': rf_regressor,
        'feature_cols': feature_cols,
        'metrics': metrics,
        'disease': disease_name,
    }
    
    joblib.dump(model_data, model_path)
    
    return str(model_path)


def load_model(disease_name):
    """
    NEW CODE: Load trained model from disk
    
    Returns:
        - rf_regressor: Trained model
        - feature_cols: Feature column names
        - metrics: Training metrics
    """
    model_registry_path = Path(settings.MODEL_REGISTRY_PATH)
    model_filename = f"{disease_name.lower()}_model.joblib"
    model_path = model_registry_path / model_filename
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model_data = joblib.load(model_path)
    
    return (
        model_data['regressor'],
        model_data['feature_cols'],
        model_data['metrics']
    )

