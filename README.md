# Tactical Assets Allocation (TAA) — Deep Learning Model
### *Institutional-Grade Portfolio Optimization & Regime Detection*

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.20-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📌 Project Overview
This repository contains a sophisticated **Tactical Asset Allocation (TAA)** framework that leverages **Deep Learning** to generate risk-adjusted investment signals. Moving beyond traditional static allocation, this model dynamically adjusts weights across diverse asset classes (Equities, Commodities, and Fixed Income) based on detected market regimes and non-linear data patterns.

The system is designed for institutional analysis, providing a real-time interactive dashboard to visualize allocation shifts, risk metrics, and backtested performance.

## 🧠 Core Features
* **Deep Learning Engine**: Built with **TensorFlow 2.20**, the model identifies complex relationships between macroeconomic indicators and asset returns.
* **Regime Detection**: Utilizes advanced statistical transforms to categorize market states (e.g., Bull, Bear, or Neutral) and adjust exposure accordingly.
* **Multi-Asset Coverage**: Integrated tracking for the S&P 500 (`^GSPC`), Gold (`GC=F`), Brent Crude Oil (`BZ=F`), and the 10-Year Treasury Yield.
* **Interactive Data Grid**: A responsive web-based dashboard featuring:
    * Real-time risk matrix and volatility tracking.
    * Dynamic Chart.js visualizations of asset trends.
    * Institutional Excel export capabilities via SheetJS.
* **Automated Pipeline**: End-to-end data fetching via **FRED API** and **Yahoo Finance** with built-in fallback mechanisms.

## 🛠️ Technical Stack
* **Backend**: Python 3.12, Flask
* **Machine Learning**: TensorFlow, Scikit-learn, Statsmodels
* **Data Science**: Pandas, NumPy, SciPy
* **APIs**: Federal Reserve Economic Data (FRED), Yahoo Finance
* **Frontend**: HTML5, CSS3 (Modern Dark Theme), Chart.js, SheetJS

## 📂 Repository Structure
```text
Tactical-Assets-Allocation/
├── DeepTAA_Interactive.py   # Main Flask application & ML Inference
├── config.py                # API keys and indicator thresholds
├── requirements.txt         # Project dependencies
├── Documentations/          # Technical guides & Research papers
│   ├── Complete_Guide.md    # Internal framework documentation
│   └── TAA_Deep_Learning.pdf # Academic research background
├── models/                  # Saved model weights and configurations
│   ├── BestModel20260316/   
│   └── GoodModel20260317/
└── data/                    # Local cache for market data
```

## 🚀 Getting Started

### Prerequisites
* Python 3.12+
* A FRED API Key (Update in `config.py`)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/david-haindongo/Tactical-Assets-Allocation---DeepLearning-Model.git
   cd "Tactical Assets Allocation - DeepLearning Model"
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python3 -m venv DeepLTAA-env
   source DeepLTAA-env/bin/activate  # On Windows use: DeepLTAA-env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch the Dashboard:**
   ```bash
   python DeepTAA_Interactive.py
   ```
   *The dashboard will be available at `http://127.0.0.1:5000`.*

## 📈 Methodology
The model evaluates asset classes using a **Threshold-Based Risk Model**. Key indicators like the **Death Cross (50/200 SMA)**, **VIX Volatility Spikes**, and **Yield Curve Inversions** act as primary features for the Deep Learning architecture. The model outputs a probability-weighted allocation intended to minimize drawdowns during high-risk regimes while capturing upside during recovery phases.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
