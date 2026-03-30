"""
Deep Learning based Global Tactical Asset Allocation Model
PRODUCTION READY VERSION
============================================================
Author: Quantitative Research Team
Version: 3.2.0
Last Updated: 2026-03-16

FIXES:
- Save models in native Keras format (.keras) instead of legacy .h5
- Add compatibility for loading models across TensorFlow versions
- Custom load function with error handling
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings
warnings.filterwarnings('ignore')
import time
import os
import re
import json
import pickle
import hashlib
import random
from pathlib import Path
from dataclasses import dataclass, field, asdict
import logging
from logging.handlers import RotatingFileHandler

# Deep Learning
import tensorflow as tf
from tensorflow.keras import layers, regularizers, Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import metrics  # Explicitly import metrics

# Data Processing
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

# FRED API
from fredapi import Fred

# Visualization
import matplotlib.pyplot as plt

# Utilities
from tqdm import tqdm
import joblib

# =============================================================================
# CONFIGURATION
# =============================================================================

ROOT_DIR = Path(__file__).parent.absolute()
CACHE_DIR = ROOT_DIR / "cache"
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
LOGS_DIR = ROOT_DIR / "logs"

for dir_path in [CACHE_DIR, DATA_DIR, MODEL_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# FRED API Key
FRED_API_KEY = "115663e81b13055630e24787b7ef5ca2"

# Logging Configuration
def setup_logging(name: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging("DeepTAA")

# =============================================================================
# TICKER CONFIGURATION (Based on dashboards_engine.py)
# =============================================================================

MARKET_INDICES_TICKERS = {
    "VIX": "^VIX",
    "US Dollar Index": "DX-Y.NYB",
    "Nasdaq": "^IXIC",
    "IBOVESPA": "^BVSP",
    "S&P 500": "^GSPC",
    "S&P/TSX Composite": "^GSPTSE",
    "Dow 30": "^DJI",
    "Russell 2000": "^RUT",
    "British Pound / USD": "GBPUSD=X",
    "FTSE 100": "^FTSE",
    "Euro Index": "EURUSD=X",
    "CAC 40": "^FCHI",
    "DAX PERFORMANCE-INDEX": "^GDAXI",
    "Euronext 100 Index": "^N100",
    "EURO STOXX 50": "^STOXX50E",
    "MSCI Europe Index": "IEUR",
    "Hang Seng Index": "^HSI",
    "Nikkei 225": "^N225",
    "SSE Composite Index": "000001.SS",
    "KOSPI Composite Index": "^KS11",
    "Japanese Yen / USD": "JPY=X",
    "Australian Dollar / USD": "AUDUSD=X",
    "S&P/ASX 200": "^AXJO",
    "S&P BSE SENSEX": "^BSESN"
}

ASSETS_TICKERS = {
    "Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Gold": "GC=F",
    "Copper": "HG=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "USD/MXN": "MXN=X",
    "USD/JPY": "JPY=X",
    "USD/AUD": "AUDUSD=X",
    "USD/GBP": "GBPUSD=X",
    "USD/CAD": "CAD=X",
    "EUR/USD": "EURUSD=X",
    "5-Yr Bond": "^FVX",
    "10-Yr Bond": "^TNX",
    "30-Yr Bond": "^TYX",
    "2 Yr T-Note": "SHY",
    "10 Yr T-Note": "IEF",
    "13-Wk Bill": "BIL"
}

STOCKS_TICKERS = {
    "NVIDIA Corporation": "NVDA",
    "Ondas Inc.": "ONDS",
    "American Airlines Group Inc.": "AAL",
    "Marvell Technology, Inc.": "MRVL",
    "Banco Bradesco S.A.": "BBD",
    "Day One Biopharmaceuticals": "DAWN",
    "SoFi Technologies, Inc.": "SOFI",
    "Plug Power Inc.": "PLUG",
    "Chevron Corporation": "CVX"
}

COMMODITIES_TICKERS = {
    "Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Copper": "HG=F",
    "Platinum": "PL=F"
}

NAME_TO_SYMBOL = {}
for d in [MARKET_INDICES_TICKERS, ASSETS_TICKERS, STOCKS_TICKERS, COMMODITIES_TICKERS]:
    NAME_TO_SYMBOL.update(d)


@dataclass
class TAAConfig:
    """Configuration for Tactical Asset Allocation model"""
    
    etf_tickers: List[str] = field(default_factory=lambda: [
        'SPY', 'EFA', 'EEM', 'TLT', 'IEF', 'SHY', 'LQD', 'GLD', 'USO', 'RWX'
    ])
    
    fred_series: Dict[str, str] = field(default_factory=lambda: {
        'T10Y2Y': '10-Year Treasury Constant Maturity Minus 2-Year',
        'T10Y3M': '10-Year Treasury Constant Maturity Minus 3-Month',
        'DGS10': '10-Year Treasury Constant Maturity Rate',
        'DGS2': '2-Year Treasury Constant Maturity Rate',
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
        'PAYEMS': 'All Employees, Total Nonfarm',
        'GDPC1': 'Real Gross Domestic Product',
        'UNRATE': 'Unemployment Rate',
        'FEDFUNDS': 'Federal Funds Effective Rate',
        'INDPRO': 'Industrial Production Index',
        'M2SL': 'M2 Money Stock',
        'SP500': 'S&P 500 Index',
        'DJIA': 'Dow Jones Industrial Average',
        'VIXCLS': 'CBOE Volatility Index'
    })
    
    prediction_horizon: int = 63
    initial_training_days: int = 252
    update_frequency: int = 21
    initial_epochs: int = 50
    walkforward_epochs: int = 10
    batch_size: int = 32
    validation_split: float = 0.2      # kept for compatibility, not used in walk-forward
    
    layer_sizes: List[int] = field(default_factory=lambda: [128, 64, 32])
    dropout_rate: float = 0.3
    l2_reg: float = 0.001
    learning_rate: float = 0.001
    min_learning_rate: float = 1e-6
    
    mc_simulations: int = 50
    
    max_allocation_change: float = 0.2
    cash_threshold: float = 0.05
    transaction_costs: float = 0.001
    
    risk_free_rate: float = 0.02
    
    random_seed: int = 42
    
    # Delay between requests (exactly as dashboards_engine)
    request_delay: float = 0.5
    
    # No retries – simple fetch or fail
    use_cache: bool = True
    cache_ttl_days: int = 1
    
    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'TAAConfig':
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)


# =============================================================================
# CACHE MANAGER (simplified)
# =============================================================================

class CacheManager:
    def __init__(self, cache_dir: Path = CACHE_DIR, ttl_days: int = 1):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_days = ttl_days
        self.logger = logging.getLogger(f"{__name__}.CacheManager")
    
    def _get_key_hash(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, key: str) -> Path:
        key_hash = self._get_key_hash(key)
        return self.cache_dir / f"{key_hash}.pkl"
    
    def _is_expired(self, path: Path) -> bool:
        if not path.exists():
            return True
        mod_time = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - mod_time
        return age.days > self.ttl_days
    
    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if cache_path.exists() and not self._is_expired(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
        return None
    
    def set(self, key: str, data: Any) -> None:
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            self.logger.warning(f"Failed to cache: {e}")
    
    def clear(self) -> None:
        for f in self.cache_dir.glob("*.pkl"):
            f.unlink()
        self.logger.info("Cache cleared")


# =============================================================================
# DATA FETCHER – EXACT METHOD FROM DASHBOARDS_ENGINE.PY
# =============================================================================

class DataFetcher:
    def __init__(self, config: TAAConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DataFetcher")
        self.fred = Fred(api_key=FRED_API_KEY)
        self.cache = CacheManager(ttl_days=config.cache_ttl_days) if config.use_cache else None
    
    def fetch_yahoo_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Exact copy of fetch_yahoo_data from dashboards_engine.py
        """
        cache_key = f"yf_{symbol}_max"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return cached
        
        try:
            self.logger.debug(f"Fetching {symbol}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="max", interval="1d")
            
            if df is None or df.empty:
                self.logger.warning(f"No data for {symbol}")
                return None
            
            df = df.reset_index()
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            
            if self.cache:
                self.cache.set(cache_key, df)
            
            self.logger.info(f"Fetched {symbol}: {len(df)} days")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def fetch_etf_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch ETF data with simple delay between requests (like dashboards_engine)
        """
        self.logger.info("=" * 70)
        self.logger.info("FETCHING ETF DATA")
        self.logger.info("=" * 70)
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        results = {}
        # Wrap loop with tqdm for progress bar
        for i, ticker in enumerate(tqdm(self.config.etf_tickers, desc="Fetching ETFs", unit="ticker")):
            if i > 0:
                time.sleep(self.config.request_delay)  # 0.5s delay as in dashboards_engine
            
            df = self.fetch_yahoo_data(ticker)
            if df is not None:
                # Filter to date range
                df = df.set_index('Date')
                df = df.loc[start_dt.date():end_dt.date()]
                if not df.empty:
                    results[ticker] = df['Close'].rename(ticker)
        
        if not results:
            self.logger.warning("No ETF data fetched. Using synthetic data.")
            return self._generate_synthetic_etf_data(start_date, end_date)
        
        prices_df = pd.concat(results.values(), axis=1)
        prices_df = prices_df.dropna()
        
        self.logger.info(f"Successfully fetched {len(prices_df.columns)} ETFs")
        return prices_df
    
    def _generate_synthetic_etf_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate synthetic ETF data as fallback"""
        self.logger.info("Generating synthetic ETF data")
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        np.random.seed(self.config.random_seed)
        
        n_assets = len(self.config.etf_tickers)
        n_days = len(dates)
        
        # Simple random walk
        returns = np.random.normal(0.0005, 0.01, (n_days, n_assets))
        prices = 100 * np.exp(np.cumsum(returns, axis=0))
        
        return pd.DataFrame(prices, index=dates, columns=self.config.etf_tickers)
    
    def fetch_fred_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch FRED data with caching"""
        self.logger.info("=" * 70)
        self.logger.info("FETCHING FRED DATA")
        self.logger.info("=" * 70)
        
        all_series = []
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # Wrap loop with tqdm for progress bar
        series_items = list(self.config.fred_series.items())
        for series_id, description in tqdm(series_items, desc="Fetching FRED series", unit="series"):
            time.sleep(self.config.request_delay)
            
            cache_key = f"fred_{series_id}_{start_date}_{end_date}"
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    all_series.append(cached.rename(series_id))
                    continue
            
            try:
                data = self.fred.get_series(
                    series_id,
                    observation_start=start_date,
                    observation_end=end_date
                )
                
                if not data.empty:
                    data = data.reindex(dates, method='ffill').fillna(method='bfill')
                    if self.cache:
                        self.cache.set(cache_key, data)
                    all_series.append(data.rename(series_id))
                else:
                    self.logger.warning(f"  ✗ {series_id}: No data")
                    
            except Exception as e:
                self.logger.warning(f"  ✗ Failed to fetch {series_id}: {e}")
        
        if all_series:
            return pd.concat(all_series, axis=1)
        else:
            self.logger.warning("No FRED data, using synthetic")
            return self._generate_synthetic_fred_data(start_date, end_date, dates)
    
    def _generate_synthetic_fred_data(self, start_date: str, end_date: str, dates) -> pd.DataFrame:
        np.random.seed(self.config.random_seed)
        n_points = len(dates)
        data = {
            'T10Y2Y': 1.5 + 0.5*np.sin(np.arange(n_points)/252) + np.random.normal(0,0.1,n_points),
            'T10Y3M': 1.2 + 0.4*np.sin(np.arange(n_points)/252) + np.random.normal(0,0.1,n_points),
            'DGS10': 3.0 + 0.2*np.sin(np.arange(n_points)/252) + np.random.normal(0,0.2,n_points),
            'DGS2': 2.0 + 0.3*np.sin(np.arange(n_points)/252) + np.random.normal(0,0.2,n_points),
            'CPIAUCSL': 100 + np.cumsum(np.random.normal(0.2,0.1,n_points)),
            'PAYEMS': 150000 + np.cumsum(np.random.normal(50,100,n_points)),
            'GDPC1': 20000 + np.cumsum(np.random.normal(50,20,n_points)),
            'UNRATE': 5.0 - 0.001*np.arange(n_points) + np.random.normal(0,0.2,n_points),
            'FEDFUNDS': 2.0 + 0.5*np.sin(np.arange(n_points)/252),
            'INDPRO': 100 + np.cumsum(np.random.normal(0.1,0.3,n_points)),
            'M2SL': 15000 + np.cumsum(np.random.normal(10,5,n_points)),
            'SP500': 3000 + np.cumsum(np.random.normal(1,10,n_points)),
            'DJIA': 30000 + np.cumsum(np.random.normal(10,100,n_points)),
            'VIXCLS': 20 + 5*np.abs(np.random.normal(0,1,n_points))
        }
        return pd.DataFrame(data, index=dates)


# =============================================================================
# FEATURE ENGINEERING
# =============================================================================

class FeatureEngineer:
    def __init__(self, config: TAAConfig):
        self.config = config
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.logger = logging.getLogger(f"{__name__}.FeatureEngineer")
    
    def create_technical_features(self, prices: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame(index=prices.index)
        
        for h in [1,5,21,63,126,252]:
            ret = prices.pct_change(h)
            ret.columns = [f'{col}_ret_{h}d' for col in prices.columns]
            features = features.join(ret)
        
        for w in [21,63]:
            vol = prices.pct_change().rolling(w).std() * np.sqrt(252)
            vol.columns = [f'{col}_vol_{w}d' for col in prices.columns]
            features = features.join(vol)
        
        for col in prices.columns:
            ma50 = prices[col].rolling(50).mean()
            ma200 = prices[col].rolling(200).mean()
            features[f'{col}_ma_cross'] = (ma50/ma200 - 1)
            features[f'{col}_roc_10'] = prices[col].pct_change(10)
            features[f'{col}_roc_30'] = prices[col].pct_change(30)
            
            delta = prices[col].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / (loss + 1e-8)
            features[f'{col}_rsi_14'] = 100 - (100/(1+rs))
        
        return features
    
    def create_macro_features(self, fred_data: pd.DataFrame) -> pd.DataFrame:
        features = fred_data.copy()
        for col in fred_data.columns:
            if any(x in col for x in ['CPI','GDP','PAYEMS','M2']):
                features[f'{col}_yoy'] = fred_data[col].pct_change(252)
            if any(x in col for x in ['UNRATE','FEDFUNDS']):
                features[f'{col}_mom'] = fred_data[col].diff(21)
            if any(x in col for x in ['T10Y2Y','T10Y3M']):
                features[f'{col}_change_5d'] = fred_data[col].diff(5)
                features[f'{col}_change_20d'] = fred_data[col].diff(20)
            if 'DGS' in col:
                features[f'{col}_change_1d'] = fred_data[col].diff(1)
                features[f'{col}_change_5d'] = fred_data[col].diff(5)
        return features
    
    def prepare_features(self, prices: pd.DataFrame, fred_data: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Creating technical features...")
        tech = self.create_technical_features(prices)
        self.logger.info("Creating macro features...")
        macro = self.create_macro_features(fred_data)
        
        # Ensure both DataFrames have the same index type (timezone-naive Timestamp)
        tech.index = pd.to_datetime(tech.index).tz_localize(None)
        macro.index = pd.to_datetime(macro.index).tz_localize(None)
        
        common = tech.index.intersection(macro.index)
        if len(common) == 0:
            self.logger.error("No overlapping dates between technical and macro features!")
            self.logger.error(f"Technical index range: {tech.index.min()} to {tech.index.max()}")
            self.logger.error(f"Macro index range: {macro.index.min()} to {macro.index.max()}")
            raise ValueError("No overlapping dates between technical and macro features. Data may be insufficient.")
        
        all_features = pd.concat([tech.loc[common], macro.loc[common]], axis=1).dropna()
        self.feature_columns = all_features.columns.tolist()
        self.logger.info(f"Created {len(self.feature_columns)} features")
        return all_features
    
    def normalize_features(self, features: pd.DataFrame, fit: bool = False) -> np.ndarray:
        if fit:
            return self.scaler.fit_transform(features)
        else:
            return self.scaler.transform(features)


# =============================================================================
# DEEP LEARNING MODEL
# =============================================================================

class DeepTAAModel:
    def __init__(self, config: TAAConfig, input_dim: int, num_assets: int):
        self.config = config
        self.input_dim = input_dim
        self.num_assets = num_assets
        self.model = None
        self.logger = logging.getLogger(f"{__name__}.DeepTAAModel")
        
        tf.random.set_seed(config.random_seed)
        np.random.seed(config.random_seed)
    
    def build_model(self) -> tf.keras.Model:
        inputs = layers.Input(shape=(self.input_dim,))
        x = inputs
        for units in self.config.layer_sizes:
            x = layers.Dense(units, kernel_regularizer=regularizers.l2(self.config.l2_reg),
                             kernel_initializer='he_normal')(x)
            x = layers.BatchNormalization()(x)
            x = layers.Activation('relu')(x)
            x = layers.Dropout(self.config.dropout_rate)(x)
        outputs = layers.Dense(self.num_assets,
                               kernel_regularizer=regularizers.l2(self.config.l2_reg),
                               kernel_initializer='he_normal')(x)
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=Adam(self.config.learning_rate), 
                     loss='mse', 
                     metrics=['mae', tf.keras.metrics.MeanSquaredError(name='mse')])
        self.logger.info(f"Model built with {model.count_params():,} parameters")
        return model
    
    def monte_carlo_dropout_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        preds = []
        for _ in range(self.config.mc_simulations):
            preds.append(self.model(X, training=True).numpy())
        preds = np.array(preds)
        return np.mean(preds, axis=0), np.std(preds, axis=0)
    
    def save(self, path: Union[str, Path]) -> None:
        """Save model in native Keras format (.keras)"""
        model_path = Path(path) / "model.keras"
        self.model.save(model_path)
        self.logger.info(f"Model saved to {model_path}")
    
    def load(self, path: Union[str, Path]) -> None:
        """Load model with compatibility handling"""
        model_path = Path(path) / "model.keras"
        h5_path = Path(path) / "model.h5"
        
        # Try loading the native Keras format first
        if model_path.exists():
            try:
                self.model = tf.keras.models.load_model(model_path, compile=False)
                # Recompile with our metrics
                self.model.compile(optimizer=Adam(self.config.learning_rate),
                                 loss='mse',
                                 metrics=['mae', tf.keras.metrics.MeanSquaredError(name='mse')])
                self.logger.info(f"Model loaded from {model_path}")
                return
            except Exception as e:
                self.logger.warning(f"Failed to load .keras format: {e}")
        
        # Fallback to legacy .h5 format
        if h5_path.exists():
            try:
                # Try loading with custom objects to handle metrics
                custom_objects = {
                    'mse': tf.keras.metrics.MeanSquaredError(),
                    'mean_squared_error': tf.keras.metrics.MeanSquaredError()
                }
                self.model = tf.keras.models.load_model(h5_path, custom_objects=custom_objects, compile=False)
                # Recompile
                self.model.compile(optimizer=Adam(self.config.learning_rate),
                                 loss='mse',
                                 metrics=['mae', tf.keras.metrics.MeanSquaredError(name='mse')])
                self.logger.info(f"Model loaded from {h5_path} (legacy format)")
                return
            except Exception as e:
                self.logger.error(f"Failed to load .h5 format: {e}")
                raise
        
        raise FileNotFoundError(f"No model file found in {path}")


# =============================================================================
# PORTFOLIO OPTIMIZATION
# =============================================================================

class PortfolioOptimizer:
    def __init__(self, config: TAAConfig):
        self.config = config
    
    def kelly_allocation(self, expected_returns: np.ndarray, uncertainty: np.ndarray) -> np.ndarray:
        kelly = expected_returns / (uncertainty**2 + 1e-8)
        kelly = np.clip(kelly, -1, 1)
        weights = np.abs(kelly) / (np.sum(np.abs(kelly)) + 1e-8)
        return weights
    
    def equal_weights(self, n_assets: int) -> np.ndarray:
        return np.ones(n_assets) / n_assets


# =============================================================================
# BACKTEST ENGINE
# =============================================================================

class BacktestEngine:
    def __init__(self, config: TAAConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.BacktestEngine")
    
    def calculate_metrics(self, returns: np.ndarray) -> Dict:
        returns = np.array(returns)
        if len(returns) == 0:
            return self._empty_metrics()
        
        cum_ret = np.cumprod(1 + returns) - 1
        total_return = cum_ret[-1]
        n_years = len(returns) / 252
        ann_return = (1 + total_return) ** (1/n_years) - 1 if n_years>0 else 0
        vol = np.std(returns) * np.sqrt(252)
        sharpe = (ann_return - self.config.risk_free_rate) / vol if vol>0 else 0
        
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown)
        
        downside = returns[returns<0]
        downside_vol = np.std(downside) * np.sqrt(252) if len(downside)>0 else 0
        sortino = ann_return / downside_vol if downside_vol>0 else 0
        
        calmar = ann_return / abs(max_dd) if max_dd!=0 else 0
        win_rate = np.sum(returns>0)/len(returns) if len(returns)>0 else 0
        var95 = np.percentile(returns, 5)
        cvar95 = returns[returns<=var95].mean() if len(returns[returns<=var95])>0 else var95
        
        return {
            'total_return': total_return,
            'annualized_return': ann_return,
            'volatility': vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'win_rate': win_rate,
            'var_95': var95,
            'cvar_95': cvar95,
            'cumulative_returns': cum_ret,
            'drawdown': drawdown
        }
    
    def _empty_metrics(self) -> Dict:
        return {k:0.0 for k in ['total_return','annualized_return','volatility','sharpe_ratio',
                                 'max_drawdown','sortino_ratio','calmar_ratio','win_rate',
                                 'var_95','cvar_95']}
    
    def print_results(self, results: Dict, title: str = "Backtest Results") -> None:
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}")
        print(f"Total Return:      {results['total_return']*100:>10.2f}%")
        print(f"Annualized Return: {results['annualized_return']*100:>10.2f}%")
        print(f"Volatility:        {results['volatility']*100:>10.2f}%")
        print(f"Sharpe Ratio:      {results['sharpe_ratio']:>10.4f}")
        print(f"Max Drawdown:      {results['max_drawdown']*100:>10.2f}%")
        print(f"Sortino Ratio:     {results['sortino_ratio']:>10.4f}")
        print(f"Calmar Ratio:      {results['calmar_ratio']:>10.4f}")
        print(f"Win Rate:          {results['win_rate']*100:>10.2f}%")
        print(f"VaR (95%):         {results['var_95']*100:>10.2f}%")
        print(f"CVaR (95%):        {results['cvar_95']*100:>10.2f}%")
        print(f"{'='*70}")
    
    def plot_results(self, results: Dict, title: str = "Strategy Performance") -> None:
        fig, (ax1, ax2) = plt.subplots(2,1,figsize=(14,8))
        ax1.plot(results['cumulative_returns']*100, linewidth=2, color='#1f77b4')
        ax1.fill_between(range(len(results['cumulative_returns'])), 0,
                         results['cumulative_returns']*100, alpha=0.2, color='#1f77b4')
        ax1.set_title(f'{title} - Cumulative Returns', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Return (%)')
        ax1.grid(True, alpha=0.3)
        
        ax2.fill_between(range(len(results['drawdown'])), results['drawdown']*100, 0,
                         color='red', alpha=0.3)
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Trading Days')
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


# =============================================================================
# MAIN DEEP TAA CLASS
# =============================================================================

class DeepTAA:
    def __init__(self, config: Optional[TAAConfig] = None):
        self.config = config or TAAConfig()
        self.logger = logging.getLogger(f"{__name__}.DeepTAA")
        
        self.data_fetcher = DataFetcher(self.config)
        self.feature_engineer = FeatureEngineer(self.config)
        self.model = None
        self.portfolio_optimizer = PortfolioOptimizer(self.config)
        self.backtest_engine = BacktestEngine(self.config)
        
        self.features = None
        self.prices = None
        self.fred_data = None
        self.training_history = None
        
        self.logger.info("DeepTAA initialized")
    
    def prepare_data(self, start_date: str = '2000-01-01', end_date: Optional[str] = None,
                     save_csv: bool = True, save_excel: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info("="*70)
        self.logger.info("DATA PREPARATION PHASE")
        self.logger.info("="*70)
        self.logger.info(f"Period: {start_date} to {end_date}")
        
        self.prices = self.data_fetcher.fetch_etf_data(start_date, end_date)
        if not self.prices.empty:
            # Convert the index from date objects to timezone-naive Timestamps
            self.prices.index = pd.to_datetime(self.prices.index).tz_localize(None)
        
        self.fred_data = self.data_fetcher.fetch_fred_data(start_date, end_date)
        if self.fred_data is not None and not self.fred_data.empty:
            # Ensure FRED data index is also timezone-naive Timestamp
            self.fred_data.index = pd.to_datetime(self.fred_data.index).tz_localize(None)
        
        # Validate data
        if self.prices.empty:
            raise ValueError("No price data available after fetching. Cannot proceed.")
        if self.fred_data.empty:
            raise ValueError("No macroeconomic data available after fetching. Cannot proceed.")
        
        self.logger.info("="*70)
        self.logger.info("FEATURE ENGINEERING")
        self.logger.info("="*70)
        self.features = self.feature_engineer.prepare_features(self.prices, self.fred_data)
        
        if self.features.empty:
            raise ValueError("Feature engineering resulted in empty dataset. Cannot proceed.")
        
        common = self.features.index.intersection(self.prices.index)
        if len(common) == 0:
            # Detailed debug output
            self.logger.error(f"Features index range: {self.features.index.min()} to {self.features.index.max()}")
            self.logger.error(f"Prices index range: {self.prices.index.min()} to {self.prices.index.max()}")
            self.logger.error(f"Features index type: {type(self.features.index)}")
            self.logger.error(f"Prices index type: {type(self.prices.index)}")
            raise ValueError("No overlapping dates between features and prices. Cannot proceed.")
        
        self.features = self.features.loc[common]
        self.prices = self.prices.loc[common]
        
        # Save data to files
        if save_csv:
            prices_file = DATA_DIR / f"prices_{start_date}_to_{end_date}.csv"
            features_file = DATA_DIR / f"features_{start_date}_to_{end_date}.csv"
            self.prices.to_csv(prices_file)
            self.features.to_csv(features_file)
            self.logger.info(f"Prices saved to {prices_file}")
            self.logger.info(f"Features saved to {features_file}")
        
        if save_excel:
            try:
                excel_file = DATA_DIR / f"data_{start_date}_to_{end_date}.xlsx"
                # Use xlsxwriter engine (comes with pandas)
                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                    self.prices.to_excel(writer, sheet_name='Prices')
                    self.features.to_excel(writer, sheet_name='Features')
                    if self.fred_data is not None:
                        self.fred_data.to_excel(writer, sheet_name='FRED')
                self.logger.info(f"Data saved to Excel: {excel_file}")
            except Exception as e:
                self.logger.warning(f"Excel export failed: {e}. Saving CSV only.")
                save_excel = False
        
        self.logger.info("="*70)
        self.logger.info("DATA PREPARATION COMPLETE")
        self.logger.info("="*70)
        self.logger.info(f"Features shape: {self.features.shape}")
        self.logger.info(f"Prices shape: {self.prices.shape}")
        self.logger.info(f"Date range: {self.features.index[0]} to {self.features.index[-1]}")
        
        return self.features, self.prices, self.fred_data
    
    def _train_on_window(self, features: pd.DataFrame, targets: pd.DataFrame, epochs: int) -> None:
        """
        Train the model on a specific window of data.
        Features and targets are already aligned and have no NaNs.
        """
        # Normalise features (fit scaler)
        X_scaled = self.feature_engineer.normalize_features(features, fit=True)
        y = targets.values
        
        # Build model if not already built (first time)
        if self.model is None:
            self.model = DeepTAAModel(self.config, features.shape[1], self.prices.shape[1])
            self.model.model = self.model.build_model()
        
        # Train for the given number of epochs, show progress with verbose=1
        history = self.model.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=self.config.batch_size,
            verbose=1  # <-- Show epoch progress
        )
        self.training_history = history.history
        self.logger.info(f"Trained on window: {len(features)} samples, {epochs} epochs, final loss: {history.history['loss'][-1]:.6f}")
    
    def train(self) -> Dict:
        """
        Initial training on all available data (for the interactive 'Train Model' option).
        This is not used in the walk-forward backtest, but kept for convenience.
        """
        if self.features is None:
            raise ValueError("No data. Run prepare_data() first.")
        
        self.logger.info("="*70)
        self.logger.info("INITIAL MODEL TRAINING (ALL DATA)")
        self.logger.info("="*70)
        
        # Prepare targets: future returns over prediction_horizon, then drop NaNs
        future_returns = self.prices.pct_change(self.config.prediction_horizon).shift(-self.config.prediction_horizon)
        common = self.features.index.intersection(future_returns.index)
        X = self.features.loc[common].dropna()
        y = future_returns.loc[common].loc[X.index]
        
        # Drop any remaining rows where y is NaN (should be none after intersection, but safe)
        mask = y.notna().all(axis=1)
        X = X[mask]
        y = y[mask]
        
        if len(X) == 0:
            raise ValueError("No training data after removing NaNs")
        
        self.logger.info(f"Training samples: {len(X):,}")
        self._train_on_window(X, y, self.config.initial_epochs)
        
        self.logger.info("INITIAL TRAINING COMPLETE")
        return self.training_history
    
    def backtest(self) -> Dict:
        """
        Walk-forward backtest as described in the paper.
        - Expands training window over time.
        - Retrains every `update_frequency` days for `walkforward_epochs`.
        - Uses the model to predict for the following `update_frequency` days.
        - Records daily portfolio returns using Kelly allocation.
        """
        if self.features is None or self.prices is None:
            raise ValueError("No data. Run prepare_data() first.")
        
        self.logger.info("="*70)
        self.logger.info("WALK-FORWARD BACKTEST")
        self.logger.info("="*70)
        
        # Prepare daily returns (t to t+1)
        daily_returns = self.prices.pct_change().shift(-1).dropna()
        
        # Prepare features and targets (future returns over prediction_horizon)
        future_returns = self.prices.pct_change(self.config.prediction_horizon).shift(-self.config.prediction_horizon)
        common = self.features.index.intersection(future_returns.index).intersection(daily_returns.index)
        features = self.features.loc[common].copy()
        targets = future_returns.loc[common].copy()
        daily_ret = daily_returns.loc[common].copy()
        
        # Sort by date
        features = features.sort_index()
        targets = targets.sort_index()
        daily_ret = daily_ret.sort_index()
        
        # Drop rows where targets contain NaN (last `prediction_horizon` days)
        mask = targets.notna().all(axis=1)
        features = features[mask]
        targets = targets[mask]
        daily_ret = daily_ret.loc[features.index]  # align again
        
        dates = features.index.tolist()
        n = len(dates)
        
        # Determine walk-forward split points
        # We need at least initial_training_days for the first training
        if n < self.config.initial_training_days:
            raise ValueError(f"Not enough data: need at least {self.config.initial_training_days} days, got {n}")
        
        train_end_indices = list(range(self.config.initial_training_days, n, self.config.update_frequency))
        if train_end_indices[-1] != n:
            train_end_indices.append(n)  # ensure last segment covers to the end
        
        # Storage for portfolio returns
        portfolio_returns = []
        prediction_dates = []
        
        # Reset model and scaler for walk-forward
        self.model = None
        self.feature_engineer.scaler = StandardScaler()  # fresh scaler
        
        current_model = None
        current_scaler = None
        
        # Progress bar for training windows
        pbar = tqdm(total=len(train_end_indices), desc="Walk-forward windows", unit="window")
        for i, train_end_idx in enumerate(train_end_indices):
            # Training window: from start to train_end_idx (exclusive)
            train_start = 0
            train_end = train_end_idx
            
            X_train = features.iloc[train_start:train_end]
            y_train = targets.iloc[train_start:train_end]
            
            if len(X_train) == 0:
                self.logger.warning(f"No training data at split {i}, skipping")
                pbar.update(1)
                continue
            
            # Fit scaler on training features and transform
            X_scaled = self.feature_engineer.normalize_features(X_train, fit=True)
            y_values = y_train.values
            
            # Build or continue training model
            if self.model is None:
                self.model = DeepTAAModel(self.config, X_train.shape[1], self.prices.shape[1])
                self.model.model = self.model.build_model()
            else:
                # Continue training from previous weights
                pass
            
            # Train for walkforward_epochs (silent - we already have progress bar)
            self.model.model.fit(
                X_scaled, y_values,
                epochs=self.config.walkforward_epochs,
                batch_size=self.config.batch_size,
                verbose=0
            )
            
            # Store the current scaler (already updated in feature_engineer)
            current_scaler = self.feature_engineer.scaler
            
            # Determine prediction range
            if i < len(train_end_indices) - 1:
                pred_end_idx = train_end_indices[i+1]
            else:
                pred_end_idx = n
            
            X_pred = features.iloc[train_end:pred_end_idx]
            if len(X_pred) == 0:
                pbar.update(1)
                continue
            
            # Transform prediction features using the same scaler
            X_pred_scaled = current_scaler.transform(X_pred)
            
            # Predict expected returns and uncertainty
            exp_ret, unc = self.model.monte_carlo_dropout_predict(X_pred_scaled)
            
            # For each prediction day, compute allocation and portfolio return
            for j, idx in enumerate(X_pred.index):
                w = self.portfolio_optimizer.kelly_allocation(exp_ret[j], unc[j])
                # Daily return for that day (return from idx to next day)
                r = daily_ret.loc[idx].values  # shape (n_assets,)
                port_ret = np.sum(w * r)
                portfolio_returns.append(port_ret)
                prediction_dates.append(idx)
            
            pbar.update(1)
        pbar.close()
        
        # Convert to array and compute metrics
        portfolio_returns = np.array(portfolio_returns)
        results = self.backtest_engine.calculate_metrics(portfolio_returns)
        
        # Compute equal-weight benchmark on the same dates
        ew_weights = self.portfolio_optimizer.equal_weights(self.prices.shape[1])
        ew_returns = daily_ret.loc[prediction_dates].values @ ew_weights
        results['benchmark_equal'] = self.backtest_engine.calculate_metrics(ew_returns)
        
        self.logger.info("Walk-forward backtest complete")
        return results
    
    def predict_allocation(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.model is None:
            raise ValueError("Model not trained.")
        
        latest = self.features.iloc[-1:].values
        latest_scaled = self.feature_engineer.normalize_features(latest, fit=False)
        exp_ret, unc = self.model.monte_carlo_dropout_predict(latest_scaled)
        w = self.portfolio_optimizer.kelly_allocation(exp_ret[0], unc[0])
        return w, exp_ret[0], unc[0]
    
    def save(self, name: str) -> None:
        save_dir = MODEL_DIR / name
        save_dir.mkdir(exist_ok=True)
        self.config.save(save_dir / 'config.json')
        if self.model:
            self.model.save(save_dir)
        joblib.dump(self.feature_engineer.scaler, save_dir / 'scaler.pkl')
        joblib.dump(self.feature_engineer.feature_columns, save_dir / 'feature_columns.pkl')
        if self.training_history:
            joblib.dump(self.training_history, save_dir / 'history.pkl')
        self.logger.info(f"Model saved to {save_dir}")
    
    def load(self, name: str) -> None:
        load_dir = MODEL_DIR / name
        if not load_dir.exists():
            raise FileNotFoundError(f"Model directory {load_dir} not found")
        
        self.config = TAAConfig.load(load_dir / 'config.json')
        self.feature_engineer.scaler = joblib.load(load_dir / 'scaler.pkl')
        self.feature_engineer.feature_columns = joblib.load(load_dir / 'feature_columns.pkl')
        
        # Load model with compatibility handling
        input_dim = len(self.feature_engineer.feature_columns)
        num_assets = len(self.config.etf_tickers)
        self.model = DeepTAAModel(self.config, input_dim, num_assets)
        self.model.load(load_dir)
        
        hist_path = load_dir / 'history.pkl'
        if hist_path.exists():
            self.training_history = joblib.load(hist_path)
        self.logger.info(f"Model loaded from {load_dir}")
    
    def get_model_info(self) -> Dict:
        info = {'config': asdict(self.config),
                'data_available': self.features is not None,
                'model_trained': self.model is not None}
        if self.features is not None:
            info['data_info'] = {
                'date_range': f"{self.features.index[0]} to {self.features.index[-1]}",
                'n_days': len(self.features),
                'n_features': self.features.shape[1],
                'n_assets': self.prices.shape[1]
            }
        if self.training_history:
            info['training_info'] = {
                'final_loss': self.training_history['loss'][-1],
                'epochs': len(self.training_history['loss'])
            }
        return info


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def interactive_session() -> None:
    print("\n" + "="*80)
    print(" " * 20 + "DEEP LEARNING TACTICAL ASSET ALLOCATION")
    print(" " * 15 + "PRODUCTION READY VERSION v3.2.0")
    print("="*80)
    
    config = TAAConfig()
    taa = DeepTAA(config)
    
    while True:
        print("\n" + "─"*50)
        print("MAIN MENU")
        print("─"*50)
        print("1. Prepare/Update Data")
        print("2. Train Model (on all data, for interactive use)")
        print("3. Run Walk-Forward Backtest")
        print("4. Predict Future Allocation (using latest model)")
        print("5. Analyze Specific Asset")
        print("6. Save Model")
        print("7. Load Model")
        print("8. Model Information")
        print("9. Clear Cache")
        print("10. Exit")
        print("─"*50)
        
        choice = input("\nEnter your choice (1-10): ").strip()
        
        if choice == '1':
            print("\n" + "─"*50)
            print("DATA PREPARATION")
            print("─"*50)
            start = input("Enter start date (YYYY-MM-DD) [default: 2000-01-01]: ").strip()
            end = input("Enter end date (YYYY-MM-DD) [default: today]: ").strip()
            start = start or '2000-01-01'
            end = end or datetime.now().strftime('%Y-%m-%d')
            try:
                f, p, _ = taa.prepare_data(start, end, save_csv=True, save_excel=True)
                print(f"\nData prepared successfully:")
                print(f"  Date range: {f.index[0]} to {f.index[-1]}")
                print(f"  Trading days: {len(f):,}")
                print(f"  Features: {f.shape[1]:,}")
                print(f"  Assets: {p.shape[1]}")
            except Exception as e:
                print(f"\nError preparing data: {e}")
        
        elif choice == '2':
            if taa.features is None:
                print("\nPlease prepare data first (Option 1)")
                continue
            try:
                hist = taa.train()
                print(f"\nTraining complete.")
                print(f"Final loss: {hist['loss'][-1]:.6f}")
            except Exception as e:
                print(f"\nError training model: {e}")
        
        elif choice == '3':
            if taa.features is None:
                print("\nPlease prepare data first (Option 1)")
                continue
            try:
                res = taa.backtest()
                taa.backtest_engine.print_results(res, "WALK-FORWARD TAA STRATEGY")
                print("\n" + "─"*30)
                taa.backtest_engine.print_results(res['benchmark_equal'], "EQUAL WEIGHT (on same dates)")
                if input("\nShow plots? (y/n): ").strip().lower() == 'y':
                    taa.backtest_engine.plot_results(res, "Walk-Forward TAA")
            except Exception as e:
                print(f"\nError in backtest: {e}")
        
        elif choice == '4':
            if taa.model is None:
                print("\nPlease train a model first (Option 2 or 3)")
                continue
            try:
                w, er, unc = taa.predict_allocation()
                print("\n" + "="*70)
                print("FUTURE ALLOCATION PREDICTION")
                print("="*70)
                print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                print(f"Horizon: {taa.config.prediction_horizon} days")
                print("─"*70)
                print(f"{'Asset':<10} {'Weight':<12} {'Exp Return':<18} {'Uncertainty':<15}")
                print("─"*70)
                for i, ticker in enumerate(taa.config.etf_tickers):
                    print(f"{ticker:<10} {w[i]*100:>6.2f}%   "
                          f"{er[i]*100:>8.2f}% ± {unc[i]*100:>5.2f}%")
                print("="*70)
            except Exception as e:
                print(f"\nError in prediction: {e}")
        
        elif choice == '5':
            if taa.model is None:
                print("\nPlease train a model first (Option 2 or 3)")
                continue
            ticker = input("Enter ticker: ").strip().upper()
            try:
                w, er, unc = taa.predict_allocation()
                if ticker in taa.config.etf_tickers:
                    idx = taa.config.etf_tickers.index(ticker)
                    print(f"\nAnalysis for {ticker}")
                    print(f"  Weight: {w[idx]*100:.2f}%")
                    print(f"  Expected Return: {er[idx]*100:.2f}% ± {unc[idx]*100:.2f}%")
                    rank = np.sum(w > w[idx]) + 1
                    print(f"  Rank: {rank}/{len(w)}")
                else:
                    print(f"{ticker} not in asset list. Available: {', '.join(taa.config.etf_tickers)}")
            except Exception as e:
                print(f"\nError analyzing asset: {e}")
        
        elif choice == '6':
            if taa.model is None:
                print("\nNo model to save")
                continue
            name = input("Model name: ").strip()
            if name:
                taa.save(name)
                print(f"Model saved as '{name}'")
        
        elif choice == '7':
            name = input("Model name: ").strip()
            try:
                taa.load(name)
                print(f"Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")
        
        elif choice == '8':
            info = taa.get_model_info()
            print("\n" + "="*50)
            print("MODEL INFORMATION")
            print("="*50)
            print(f"Data Available: {info['data_available']}")
            print(f"Model Trained: {info['model_trained']}")
            if 'data_info' in info:
                for k,v in info['data_info'].items():
                    print(f"  {k}: {v}")
            if 'training_info' in info:
                for k,v in info['training_info'].items():
                    print(f"  {k}: {v}")
        
        elif choice == '9':
            if input("Clear cache? (y/n): ").lower() == 'y':
                CacheManager().clear()
        
        elif choice == '10':
            print("\nExiting. Goodbye.")
            break
        else:
            print("\nInvalid choice.")


def main() -> int:
    try:
        interactive_session()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        logger.exception("Fatal error")
        print(f"\nFatal error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())