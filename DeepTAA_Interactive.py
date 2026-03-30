<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>recession forecaster · institutional data grid</title>
    <!-- Fonts & minimal icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <!-- Chart.js 4 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <!-- SheetJS for Excel export -->
    <script src="https://cdn.sheetjs.com/xlsx-0.20.2/package/dist/xlsx.full.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }

        body {
            background: #111111;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1mm;
            overflow: hidden;
            transition: background 0.1s;
        }
        body.light-theme {
            background: #e6e9ef;
        }
        body.light-theme .dashboard {
            background: #ffffff;
            border-color: #b0c0d0;
        }
        body.light-theme .top-bar {
            background: #f2f5f9;
            border-bottom: 1px solid #b8c8dc;
        }
        body.light-theme .institution h1,
        body.light-theme .fetch-log,
        body.light-theme .matrix-header,
        body.light-theme .name-criteria,
        body.light-theme .live-value,
        body.light-theme .risk-percent,
        body.light-theme .hedge-tag,
        body.light-theme .chart-title { color: #1e2a36; }
        body.light-theme .indicator-card { background: #f0f4fc; border-color: #a8bcd0; }
        body.light-theme .progress-bar-bg { background: #d0dcee; }
        body.light-theme .assumption-box input { background: #ffffff; border-color: #a0b8d0; color: #111; }
        body.light-theme .risk-panel { background: #f2f7ff; border-color: #a8b8d0; }
        body.light-theme .chart-card { background: #f0f6ff; border-color: #b0c4dc; }
        body.light-theme .refresh-btn { background: #dde5f0; border-color: #90a8c0; color: #111; }
        body.light-theme .refresh-btn i { color: #2b4f6e; }
        body.light-theme .download-progress { background: #e0e8f2; border-color: #90a8c0; }
        body.light-theme .fetch-log { color: #2a4055; }

        .dashboard {
            width: 100%;
            height: 100%;
            background: #121212;
            border: 1px solid #2c3a4a;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 10px 30px -10px #000000;
            border-radius: 0;
        }

        .top-bar {
            background: #1a1a1a;
            border-bottom: 1px solid #2a3a4a;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }
        .institution {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .institution i {
            font-size: 1.8rem;
            color: #b0c8e6;
            background: #1f2f3f;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #3a5068;
        }
        .institution h1 {
            font-weight: 600;
            font-size: 1.4rem;
            color: #e6f0ff;
            letter-spacing: -0.2px;
        }
        .badge {
            background: #1e2f40;
            padding: 4px 18px;
            font-size: 0.7rem;
            font-weight: 500;
            color: #b0d0f0;
            border: 1px solid #3c5778;
            margin-left: 12px;
        }

        .refresh-area {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        .download-progress {
            background: #1a2635;
            border: 1px solid #314e6e;
            padding: 4px 14px 4px 20px;
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .progress-ring {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: conic-gradient(#3ba080 0deg, #2a4058 0deg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 700;
            color: #d0f0e0;
            border: 2px solid #3a6080;
        }
        .fetch-log {
            font-size: 0.75rem;
            color: #b0cce0;
            font-weight: 500;
            max-width: 200px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .refresh-btn {
            background: #1e2f40;
            border: 1px solid #3a5778;
            padding: 8px 24px;
            font-weight: 500;
            font-size: 0.85rem;
            color: #e6f0ff;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: 0.1s;
            border-radius: 0;
        }
        .refresh-btn i { color: #6bb8d0; }
        .refresh-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .theme-toggle {
            background: #1e2c3c;
            border: 1px solid #3a5770;
            padding: 5px 16px;
            cursor: pointer;
            font-size: 0.75rem;
            color: #c0d8f0;
        }

        .main-grid {
            display: flex;
            flex: 1;
            min-height: 0;
            gap: 16px;
            padding: 16px 20px 14px 20px;
        }

        .left-col {
            width: 36%;
            background: #151515;
            border: 1px solid #2c3e54;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .matrix-header {
            padding: 14px 20px 6px 20px;
            color: #b0d0f0;
            font-weight: 600;
            font-size: 0.75rem;
            border-bottom: 1px solid #2a4058;
        }
        .matrix-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 12px 14px 14px 14px;
            scrollbar-width: thin;
            scrollbar-color: #3a6080 #1e2630;
        }

        .indicator-card {
            background: #1a1f2a;
            border: 1px solid #2f455e;
            padding: 16px 16px 14px 16px;
            margin-bottom: 12px;
        }
        .row-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .name-criteria {
            font-weight: 600;
            color: #e0ecff;
            font-size: 0.85rem;
        }
        .name-criteria small {
            color: #90b0d0;
            font-weight: 400;
            font-size: 0.6rem;
            display: block;
            margin-top: 2px;
        }
        .status-badge {
            width: 28px;
            height: 28px;
            background: #25374a;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #3f6080;
        }
        .status-badge.active { background: #1e6b40; border-color: #70cc90; }
        .status-badge i { color: #ffffff; font-size: 1rem; display: none; }
        .status-badge.active i { display: block; }

        .live-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 12px 0 8px;
        }
        .live-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #f0f8ff;
        }
        .threshold {
            background: #1e3145;
            padding: 4px 16px;
            font-size: 0.65rem;
            border: 1px solid #3b6080;
            color: #b0d0f0;
        }
        .progress-bar-bg {
            background: #222f40;
            height: 8px;
            margin: 8px 0 12px;
            width: 100%;
        }
        .progress-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #e8b04b, #dd6040);
        }
        .assumption-box {
            display: flex;
            align-items: center;
            gap: 6px;
            border-top: 1px solid #2e445e;
            padding-top: 12px;
            margin-top: 6px;
        }
        .assumption-box i { color: #80b0d0; font-size: 0.7rem; }
        .assumption-box input {
            background: #131f30;
            border: 1px solid #2d4a6a;
            padding: 6px 14px;
            width: 100%;
            color: #d0e8ff;
            font-size: 0.7rem;
            outline: none;
        }

        .right-col {
            width: 64%;
            display: flex;
            flex-direction: column;
            gap: 16px;
            min-width: 0;
        }

        .risk-panel {
            background: #151515;
            border: 1px solid #2f445c;
            padding: 18px 24px;
        }
        .risk-header {
            display: flex;
            justify-content: space-between;
            color: #c0d8f5;
            font-size: 0.75rem;
            margin-bottom: 10px;
        }
        .battery-container {
            background: #1f3145;
            height: 40px;
            border: 2px solid #304e70;
            margin-bottom: 10px;
        }
        .battery-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #2fa87a, #e8b450, #db5a4a);
        }
        .risk-stats {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .risk-percent {
            font-size: 2rem;
            font-weight: 700;
            color: #ecf8ff;
        }
        .hedge-tag {
            background: #1f334a;
            border: 1px solid #3b6388;
            padding: 6px 24px;
            font-size: 0.8rem;
            color: #cce0ff;
        }

        .chart-grid-container {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding-right: 4px;
            scrollbar-width: thin;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            padding-bottom: 4px;
        }
        .chart-card {
            background: #151515;
            border: 1px solid #2f4864;
            padding: 8px 6px 4px 6px;
            display: flex;
            flex-direction: column;
            height: 160px;
            position: relative;
            cursor: pointer;
            transition: all 0.2s;
        }
        .chart-card:hover {
            border-color: #5a8bb0;
            transform: scale(1.02);
            z-index: 10;
        }
        .chart-card.fullscreen {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80vw;
            height: 80vh;
            z-index: 1000;
            background: #1a1f2a;
            border: 2px solid #5a8bb0;
            padding: 20px;
            cursor: default;
        }
        .chart-card.fullscreen .chart-title {
            font-size: 1rem;
            margin-bottom: 10px;
        }
        .chart-card.fullscreen:hover {
            transform: translate(-50%, -50%);
        }
        .chart-title {
            color: #b0d0f0;
            font-size: 0.6rem;
            font-weight: 600;
            margin-left: 2px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fullscreen-btn {
            background: transparent;
            border: 1px solid #3a6080;
            color: #b0d0f0;
            padding: 2px 8px;
            font-size: 0.6rem;
            cursor: pointer;
            border-radius: 0;
        }
        .fullscreen-btn:hover {
            background: #2a4058;
        }
        .canvas-container {
            flex: 1;
            width: 100%;
            min-height: 0;
        }
        canvas { display: block; width: 100% !important; height: 100% !important; }

        .export-row {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            flex-shrink: 0;
            margin-top: 4px;
        }
        .export-btn {
            background: #1d2b3c;
            border: 1px solid #325577;
            padding: 6px 18px;
            color: #cce0ff;
            font-size: 0.7rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .fullscreen-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 999;
            display: none;
        }
        .fullscreen-overlay.active {
            display: block;
        }

        .error-message {
            color: #ff6b6b;
            font-size: 0.7rem;
            padding: 4px 8px;
            background: #2a1f1f;
            border: 1px solid #ff6b6b;
            margin-top: 4px;
        }
    </style>
</head>
<body>
<div class="dashboard">
    <div class="top-bar">
        <div class="institution">
            <i class="fas fa-chart-line"></i>
            <h1>RECESSION FORECAST · INSTITUTIONAL</h1>
            <span class="badge">FRED API + YAHOO FINANCE</span>
        </div>
        <div class="refresh-area">
            <div class="download-progress" id="progressContainer">
                <div class="progress-ring" id="progressRing">
                    <span id="progressText">0%</span>
                </div>
                <span class="fetch-log" id="fetchLog">initializing...</span>
            </div>
            <div class="refresh-btn" id="refreshBtn">
                <i class="fas fa-sync-alt"></i> refresh data
            </div>
            <div class="theme-toggle" id="themeToggle">🌓 DARK</div>
        </div>
    </div>

    <div class="main-grid">
        <div class="left-col">
            <div class="matrix-header">RECESSION INDICATOR MATRIX</div>
            <div class="matrix-scroll" id="matrixContainer"></div>
        </div>

        <div class="right-col">
            <div class="risk-panel">
                <div class="risk-header">
                    <span>RECESSION PROBABILITY (equal weight)</span>
                    <span id="triggerCount">0/12</span>
                </div>
                <div class="battery-container">
                    <div class="battery-fill" id="batteryFill" style="width:0%"></div>
                </div>
                <div class="risk-stats">
                    <span class="risk-percent" id="riskPercent">0.0%</span>
                    <span class="hedge-tag" id="hedgeText">hedge 0%</span>
                </div>
            </div>

            <div class="chart-grid-container" id="chartGridContainer">
                <div class="chart-grid" id="chartGrid"></div>
            </div>

            <div class="export-row">
                <div class="export-btn" id="exportCsv"><i class="fas fa-file-csv"></i> CSV</div>
                <div class="export-btn" id="exportExcel"><i class="fas fa-file-excel"></i> EXCEL</div>
            </div>
        </div>
    </div>
</div>

<div class="fullscreen-overlay" id="fullscreenOverlay"></div>

<script>
    (function() {
        // FRED API Key
        const FRED_API_KEY = "115663e81b13055630e24787b7ef5ca2";
        
        // Comprehensive indicator mappings with correct FRED series IDs and Yahoo symbols
        const INDICATORS = [
            { 
                name: 'Brent Crude Oil', 
                yahoo: 'BZ=F', 
                fred: 'DCOILBRENTEU',
                source: 'yahoo', // Prefer Yahoo for this
                trigger: 80,
                condition: '>',
                decimals: 2, 
                color: '#f2a65a',
                description: 'Brent Crude > $80 (energy price shock)',
                frequency: 'daily'
            },
            { 
                name: 'CPI YoY', 
                yahoo: null,
                fred: 'CPIAUCSL',
                source: 'fred',
                trigger: 3.0,
                condition: '>',
                transform: 'pct_yoy',
                decimals: 2, 
                color: '#f2846c',
                description: 'CPI YoY > 3% (inflation)',
                frequency: 'monthly'
            },
            { 
                name: 'Fed Funds Rate', 
                yahoo: null,
                fred: 'FEDFUNDS',
                source: 'fred',
                trigger: 0.25,
                condition: '>',
                decimals: 2, 
                color: '#b28aff',
                description: 'Fed Funds Rate > 0.25% (tightening)',
                frequency: 'monthly'
            },
            { 
                name: '10Y-2Y Treasury', 
                yahoo: null,
                fred: 'T10Y2Y',
                source: 'fred',
                trigger: 0,
                condition: '<',
                decimals: 2, 
                color: '#f0bc60',
                description: '10Y-2Y < 0 (inverted curve)',
                frequency: 'daily'
            },
            { 
                name: 'Unemployment Rate', 
                yahoo: null,
                fred: 'UNRATE',
                source: 'fred',
                trigger: 4.2,
                condition: '>',
                decimals: 2, 
                color: '#6abfdc',
                description: 'Unemployment > 4.2% (Sahm rule)',
                frequency: 'monthly'
            },
            { 
                name: 'S&P 500', 
                yahoo: '^GSPC',
                fred: 'SP500',
                source: 'yahoo',
                trigger: 5100,
                condition: '<',
                decimals: 0, 
                color: '#bda0e0',
                description: 'S&P 500 < 5100 (death cross)',
                frequency: 'daily'
            },
            { 
                name: 'MSCI World', 
                yahoo: 'URTH',
                fred: null,
                source: 'yahoo',
                trigger: 135,
                condition: '<',
                decimals: 2, 
                color: '#e69aab',
                description: 'MSCI World < 135 (global equities)',
                frequency: 'daily'
            },
            { 
                name: 'ISM Manufacturing PMI', 
                yahoo: null,
                fred: 'NAPM',
                source: 'fred',
                trigger: 50,
                condition: '<',
                decimals: 1, 
                color: '#9acfaf',
                description: 'PMI < 50 (contraction)',
                frequency: 'monthly'
            },
            { 
                name: 'BAA-10Y Spread', 
                yahoo: null,
                fred: 'BAA10Y',
                source: 'fred',
                trigger: 2.5,
                condition: '>',
                decimals: 2, 
                color: '#dd9f9f',
                description: 'BAA-10Y > 2.5% (credit stress)',
                frequency: 'daily'
            },
            { 
                name: 'Gold Price', 
                yahoo: 'GC=F',
                fred: 'GOLDPMGBD228NLBM',
                source: 'yahoo',
                trigger: 2000,
                condition: '>',
                decimals: 0, 
                color: '#ecd87c',
                description: 'Gold > $2000 (safe haven)',
                frequency: 'daily'
            },
            { 
                name: 'VIX', 
                yahoo: '^VIX',
                fred: 'VIXCLS',
                source: 'yahoo',
                trigger: 30,
                condition: '>',
                decimals: 1, 
                color: '#d29ab0',
                description: 'VIX > 30 (fear)',
                frequency: 'daily'
            },
            { 
                name: 'Retail Sales MoM', 
                yahoo: null,
                fred: 'RSAFS',
                source: 'fred',
                trigger: -0.5,
                condition: '<',
                transform: 'pct_mom',
                decimals: 2, 
                color: '#a5b2e5',
                description: 'Retail Sales MoM < -0.5% (consumer weakness)',
                frequency: 'monthly'
            }
        ];

        // State management
        let latestValues = {};
        let historicalData = {};
        let triggersActive = new Array(INDICATORS.length).fill(false);
        let analystNotes = new Array(INDICATORS.length).fill('');
        let chartInstances = [];
        let fullscreenChart = null;
        let fetchErrors = [];

        // Cache keys
        const CACHE_KEY = 'recession_dashboard_cache_v2';
        const CACHE_TIMESTAMP_KEY = 'recession_dashboard_timestamp_v2';

        // UI elements
        const matrixDiv = document.getElementById('matrixContainer');
        const triggerCountSpan = document.getElementById('triggerCount');
        const batteryFill = document.getElementById('batteryFill');
        const riskPercentSpan = document.getElementById('riskPercent');
        const hedgeSpan = document.getElementById('hedgeText');
        const progressRing = document.getElementById('progressRing');
        const progressText = document.getElementById('progressText');
        const fetchLog = document.getElementById('fetchLog');
        const refreshBtn = document.getElementById('refreshBtn');
        const fullscreenOverlay = document.getElementById('fullscreenOverlay');

        // Utility: Calculate percentage change
        function pctChange(current, previous) {
            if (!previous || previous === 0) return 0;
            return ((current - previous) / previous) * 100;
        }

        // Utility: Format date for FRED
        function formatDateForFRED(date) {
            return date.toISOString().split('T')[0];
        }

        // Load cached data
        function loadCachedData() {
            try {
                const cached = localStorage.getItem(CACHE_KEY);
                const timestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY);
                
                if (cached && timestamp) {
                    const data = JSON.parse(cached);
                    const cacheAge = Date.now() - parseInt(timestamp);
                    const cacheValid = cacheAge < 12 * 60 * 60 * 1000; // 12 hours
                    
                    if (cacheValid) {
                        latestValues = data.latestValues || {};
                        historicalData = data.historicalData || {};
                        analystNotes = data.analystNotes || new Array(INDICATORS.length).fill('');
                        
                        fetchLog.innerText = `cached data · ${Object.keys(latestValues).length} series`;
                        return true;
                    }
                }
            } catch (e) {
                console.warn('Cache load failed:', e);
            }
            return false;
        }

        // Save data to cache
        function saveToCache() {
            try {
                const cacheData = {
                    latestValues,
                    historicalData,
                    analystNotes,
                    timestamp: Date.now()
                };
                localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
                localStorage.setItem(CACHE_TIMESTAMP_KEY, Date.now().toString());
            } catch (e) {
                console.warn('Cache save failed:', e);
            }
        }

        // FRED API fetch using official API
        async function fetchFredSeries(seriesId, maxPoints = 100) {
            try {
                // Construct FRED API URL
                const endDate = new Date();
                const startDate = new Date();
                startDate.setFullYear(startDate.getFullYear() - 2); // Get 2 years of data
                
                const url = `https://api.stlouisfed.org/fred/series/observations?` +
                    `series_id=${seriesId}` +
                    `&api_key=${FRED_API_KEY}` +
                    `&file_type=json` +
                    `&observation_start=${formatDateForFRED(startDate)}` +
                    `&observation_end=${formatDateForFRED(endDate)}` +
                    `&sort_order=desc` +
                    `&limit=${maxPoints}`;
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error(`FRED API error: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (!data.observations || data.observations.length === 0) {
                    throw new Error('No data from FRED');
                }
                
                // Parse observations
                const values = data.observations
                    .filter(obs => obs.value !== '.' && !isNaN(parseFloat(obs.value)))
                    .map(obs => ({
                        date: obs.date,
                        value: parseFloat(obs.value)
                    }))
                    .reverse(); // Oldest first
                
                return values;
            } catch (e) {
                console.warn(`FRED fetch failed for ${seriesId}:`, e);
                fetchErrors.push(`FRED ${seriesId}: ${e.message}`);
                return null;
            }
        }

        // Yahoo Finance fetch
        async function fetchYahooSeries(symbol, maxPoints = 100) {
            try {
                // Calculate date range
                const endDate = Math.floor(Date.now() / 1000);
                const startDate = endDate - (180 * 24 * 60 * 60); // 180 days
                
                const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?` +
                    `period1=${startDate}&period2=${endDate}&interval=1d`;
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error(`Yahoo API error: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (!data.chart || !data.chart.result || !data.chart.result[0]) {
                    throw new Error('No data from Yahoo');
                }
                
                const result = data.chart.result[0];
                const timestamps = result.timestamp;
                const quotes = result.indicators.quote[0];
                const closes = quotes.close;
                
                const values = [];
                for (let i = 0; i < timestamps.length; i++) {
                    if (closes[i] !== null && !isNaN(closes[i]) && closes[i] > 0) {
                        const date = new Date(timestamps[i] * 1000).toISOString().split('T')[0];
                        values.push({ date, value: closes[i] });
                    }
                }
                
                return values;
            } catch (e) {
                console.warn(`Yahoo fetch failed for ${symbol}:`, e);
                fetchErrors.push(`Yahoo ${symbol}: ${e.message}`);
                return null;
            }
        }

        // Calculate transformed values (YoY%, MoM%)
        function calculateTransformedValue(hist, transform) {
            if (!hist || hist.length === 0) return null;
            
            const current = hist[hist.length - 1].value;
            
            if (transform === 'pct_yoy') {
                // Find value from 12 months ago
                const currentDate = new Date(hist[hist.length - 1].date);
                for (let i = hist.length - 2; i >= 0; i--) {
                    const histDate = new Date(hist[i].date);
                    const monthDiff = (currentDate.getFullYear() - histDate.getFullYear()) * 12 + 
                                    (currentDate.getMonth() - histDate.getMonth());
                    
                    if (monthDiff >= 12) {
                        return pctChange(current, hist[i].value);
                    }
                }
                // Fallback to most recent available
                return hist.length > 1 ? pctChange(current, hist[0].value) : null;
            }
            
            if (transform === 'pct_mom') {
                if (hist.length >= 2) {
                    return pctChange(current, hist[hist.length - 2].value);
                }
            }
            
            return current;
        }

        // Check if indicator is triggered
        function isTriggered(ind, val) {
            if (val === null || val === undefined || isNaN(val)) return false;
            
            switch (ind.condition) {
                case '>': return val > ind.trigger;
                case '<': return val < ind.trigger;
                case '>=': return val >= ind.trigger;
                case '<=': return val <= ind.trigger;
                default: return false;
            }
        }

        // Main data fetching function
        async function fetchAllData(forceRefresh = false) {
            const total = INDICATORS.length;
            let fetched = 0;
            fetchErrors = [];
            
            // Try to load from cache first unless forcing refresh
            if (!forceRefresh && loadCachedData()) {
                return true;
            }
            
            // Clear existing data
            latestValues = {};
            historicalData = {};
            
            for (let i = 0; i < total; i++) {
                const ind = INDICATORS[i];
                const percent = Math.round((i / total) * 100);
                progressRing.style.background = `conic-gradient(#3ba080 ${percent * 3.6}deg, #2a4058 0deg)`;
                progressText.innerText = percent + '%';
                
                try {
                    let currentValue = null;
                    let history = [];
                    let primarySource = ind.source || (ind.yahoo ? 'yahoo' : 'fred');
                    
                    // Try primary source first
                    if (primarySource === 'yahoo' && ind.yahoo) {
                        fetchLog.innerText = `Yahoo: ${ind.yahoo}... (${i + 1}/${total})`;
                        const ydata = await fetchYahooSeries(ind.yahoo);
                        
                        if (ydata && ydata.length > 0) {
                            history = ydata;
                            currentValue = ydata[ydata.length - 1].value;
                            latestValues[ind.yahoo] = currentValue;
                            historicalData[ind.yahoo] = ydata;
                        }
                    }
                    
                    // If primary failed and has FRED fallback, try FRED
                    if ((!currentValue || history.length === 0) && ind.fred) {
                        fetchLog.innerText = `FRED: ${ind.fred}... (${i + 1}/${total})`;
                        const fredHist = await fetchFredSeries(ind.fred);
                        
                        if (fredHist && fredHist.length > 0) {
                            history = fredHist;
                            
                            if (ind.transform) {
                                currentValue = calculateTransformedValue(fredHist, ind.transform);
                            } else {
                                currentValue = fredHist[fredHist.length - 1].value;
                            }
                            
                            latestValues[ind.fred] = currentValue;
                            historicalData[ind.fred] = fredHist;
                        }
                    }
                    
                    // If still no data, try alternative source
                    if ((!currentValue || history.length === 0) && ind.yahoo && primarySource !== 'yahoo') {
                        fetchLog.innerText = `Yahoo (alt): ${ind.yahoo}... (${i + 1}/${total})`;
                        const ydata = await fetchYahooSeries(ind.yahoo);
                        
                        if (ydata && ydata.length > 0) {
                            history = ydata;
                            currentValue = ydata[ydata.length - 1].value;
                            latestValues[ind.yahoo] = currentValue;
                            historicalData[ind.yahoo] = ydata;
                        }
                    }
                    
                    // Log warning if still no data
                    if (!currentValue || history.length === 0) {
                        console.warn(`No data for ${ind.name}`);
                        fetchErrors.push(`${ind.name}: No data available`);
                    } else {
                        fetched++;
                    }
                    
                } catch (e) {
                    console.error(`Error fetching ${ind.name}:`, e);
                    fetchErrors.push(`${ind.name}: ${e.message}`);
                }
                
                // Rate limiting
                await new Promise(r => setTimeout(r, 250));
            }
            
            // Save to cache
            saveToCache();
            
            progressRing.style.background = `conic-gradient(#3ba080 360deg, #2a4058 0deg)`;
            progressText.innerText = '100%';
            
            if (fetchErrors.length > 0) {
                fetchLog.innerText = `loaded ${fetched}/${total} · ${fetchErrors.length} errors`;
            } else {
                fetchLog.innerText = `live data · ${fetched}/${total} series`;
            }
            
            return true;
        }

        // Render the indicator matrix
        function renderMatrix() {
            let html = '';
            
            INDICATORS.forEach((ind, idx) => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                const val = latestValues[key] ?? null;
                const active = isTriggered(ind, val);
                triggersActive[idx] = active;
                
                // Calculate fill percentage for progress bar
                let fill = 0;
                if (val !== null) {
                    if (ind.condition === '>') {
                        fill = Math.min(100, (val / ind.trigger) * 100);
                    } else {
                        fill = Math.min(100, (ind.trigger / Math.max(val, 0.01)) * 100);
                    }
                }
                
                html += `<div class="indicator-card">
                    <div class="row-header">
                        <div class="name-criteria">${ind.name} <small>${ind.condition} ${ind.trigger}</small></div>
                        <div class="status-badge ${active ? 'active' : ''}"><i class="fas fa-check"></i></div>
                    </div>
                    <div class="live-row">
                        <span class="live-value">${val !== null ? val.toFixed(ind.decimals) : 'N/A'}</span>
                        <span class="threshold">${ind.trigger}</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-fill" style="width:${fill}%;"></div></div>
                    <div class="assumption-box">
                        <i class="fas fa-pencil-alt"></i>
                        <input placeholder="analyst note" value="${analystNotes[idx] || ''}" data-idx="${idx}" class="note-input">
                    </div>
                </div>`;
            });
            
            matrixDiv.innerHTML = html;
            
            document.querySelectorAll('.note-input').forEach(inp => {
                inp.addEventListener('input', e => {
                    analystNotes[e.target.dataset.idx] = e.target.value;
                    saveToCache();
                });
            });
        }

        // Update risk panel
        function updateRisk() {
            const total = INDICATORS.length;
            const cnt = triggersActive.filter(v => v).length;
            const pct = (cnt / total) * 100;
            
            triggerCountSpan.innerText = `${cnt}/${total}`;
            batteryFill.style.width = pct + '%';
            riskPercentSpan.innerText = pct.toFixed(1) + '%';
            
            let hedge = 'hedge 0%';
            if (pct > 60) hedge = 'execute downside · hedge 25%';
            else if (pct > 40) hedge = 'hedge 15% portfolio';
            else if (pct > 20) hedge = 'hedge 5%';
            
            hedgeSpan.innerText = hedge;
        }

        // Render single chart
        function renderSingleChart(chartId, ind, hist) {
            const canvas = document.getElementById(`chart-${chartId}`);
            if (!canvas || !hist || hist.length === 0) return;
            
            const ctx = canvas.getContext('2d');
            const data = hist.map(h => h.value);
            
            // Create labels based on frequency
            const labels = hist.map(h => {
                const date = new Date(h.date);
                if (ind.frequency === 'monthly') {
                    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                }
                return `${date.getMonth() + 1}/${date.getDate()}`;
            });
            
            // Destroy existing chart if any
            const existingChart = chartInstances.find(c => c.canvas && c.canvas.id === `chart-${chartId}`);
            if (existingChart) {
                existingChart.destroy();
                chartInstances = chartInstances.filter(c => c.canvas && c.canvas.id !== `chart-${chartId}`);
            }
            
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        { 
                            label: ind.name, 
                            data, 
                            borderColor: ind.color, 
                            pointRadius: 0.5, 
                            borderWidth: 1.5, 
                            tension: 0.1,
                            fill: false
                        },
                        { 
                            label: 'threshold', 
                            data: Array(data.length).fill(ind.trigger), 
                            borderColor: '#dc5f5f', 
                            borderDash: [4, 4], 
                            pointRadius: 0,
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true, 
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { display: false },
                        tooltip: { 
                            mode: 'index', 
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.raw.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    scales: { 
                        x: { 
                            ticks: { 
                                maxTicksLimit: 5, 
                                color: document.body.classList.contains('light-theme') ? '#333' : '#90b0c0',
                                maxRotation: 0
                            }, 
                            grid: { color: document.body.classList.contains('light-theme') ? '#ccc' : '#2c4058' } 
                        },
                        y: { 
                            ticks: { color: document.body.classList.contains('light-theme') ? '#333' : '#b0c8e0' }, 
                            grid: { color: document.body.classList.contains('light-theme') ? '#ccc' : '#263a50' } 
                        }
                    }
                }
            });
            
            chartInstances.push(chart);
        }

        // Render all charts
        function renderCharts() {
            const grid = document.getElementById('chartGrid');
            
            grid.innerHTML = INDICATORS.map((ind, i) => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                const hist = historicalData[key] || [];
                const chartId = `chart-${i}`;
                
                return `<div class="chart-card" id="chart-card-${i}">
                    <div class="chart-title">
                        ${ind.name}
                        <button class="fullscreen-btn" onclick="window.toggleFullscreen(${i}, '${ind.name}', '${key}')">
                            <i class="fas fa-expand"></i>
                        </button>
                    </div>
                    <div class="canvas-container">
                        <canvas id="${chartId}"></canvas>
                    </div>
                </div>`;
            }).join('');
            
            // Destroy existing chart instances
            if (chartInstances.length) {
                chartInstances.forEach(c => {
                    if (c && c.destroy) c.destroy();
                });
                chartInstances = [];
            }
            
            // Create new charts
            INDICATORS.forEach((ind, i) => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                const hist = historicalData[key] || [];
                if (hist.length > 0) {
                    setTimeout(() => renderSingleChart(i, ind, hist), 50);
                }
            });
        }

        // Full refresh
        async function fullRefresh() {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> fetching...';
            
            await fetchAllData(true);
            
            renderMatrix();
            updateRisk();
            renderCharts();
            
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> refresh data';
            refreshBtn.disabled = false;
        }

        // Export functions
        document.getElementById('exportCsv').addEventListener('click', () => {
            const rows = [['Indicator', 'Current Value', 'Trigger', 'Condition', 'Active', 'Analyst Note', 'Description']];
            
            INDICATORS.forEach((ind, i) => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                rows.push([
                    ind.name,
                    latestValues[key] || 'N/A',
                    ind.trigger,
                    ind.condition,
                    triggersActive[i] ? 'Yes' : 'No',
                    analystNotes[i] || '',
                    ind.description
                ]);
            });
            
            let csv = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
            
            const a = document.createElement('a');
            a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
            a.download = `recession_dashboard_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        });

        document.getElementById('exportExcel').addEventListener('click', () => {
            // Current state sheet
            const currentRows = [['Indicator', 'Current Value', 'Trigger', 'Condition', 'Active', 'Analyst Note', 'Description', 'Frequency']];
            INDICATORS.forEach((ind, i) => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                currentRows.push([
                    ind.name,
                    latestValues[key] || 'N/A',
                    ind.trigger,
                    ind.condition,
                    triggersActive[i] ? 'Yes' : 'No',
                    analystNotes[i] || '',
                    ind.description,
                    ind.frequency
                ]);
            });
            
            // Historical data sheet
            const historicalRows = [['Indicator', 'Date', 'Value', 'Trigger', 'Condition']];
            INDICATORS.forEach(ind => {
                const key = ind.source === 'yahoo' ? ind.yahoo : ind.fred;
                const hist = historicalData[key] || [];
                hist.slice(-30).forEach(point => {
                    historicalRows.push([
                        ind.name,
                        point.date,
                        point.value,
                        ind.trigger,
                        ind.condition
                    ]);
                });
            });
            
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(currentRows), 'Current State');
            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(historicalRows), 'Historical Data');
            
            XLSX.writeFile(wb, `recession_forecast_${new Date().toISOString().split('T')[0]}.xlsx`);
        });

        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', (e) => {
            document.body.classList.toggle('light-theme');
            e.target.innerText = document.body.classList.contains('light-theme') ? '🌞 LIGHT' : '🌓 DARK';
            
            // Re-render charts with new theme colors
            renderCharts();
        });

        // Fullscreen toggle
        window.toggleFullscreen = function(chartId, chartName, dataKey) {
            const chartCard = document.getElementById(`chart-card-${chartId}`);
            const overlay = fullscreenOverlay;
            
            if (chartCard.classList.contains('fullscreen')) {
                chartCard.classList.remove('fullscreen');
                overlay.classList.remove('active');
            } else {
                document.querySelectorAll('.chart-card.fullscreen').forEach(c => {
                    c.classList.remove('fullscreen');
                });
                
                chartCard.classList.add('fullscreen');
                overlay.classList.add('active');
            }
            
            // Re-render chart
            const ind = INDICATORS[chartId];
            const hist = historicalData[dataKey] || [];
            setTimeout(() => renderSingleChart(chartId, ind, hist), 50);
        };

        // Close fullscreen on overlay click
        fullscreenOverlay.addEventListener('click', () => {
            document.querySelectorAll('.chart-card.fullscreen').forEach(c => {
                c.classList.remove('fullscreen');
            });
            fullscreenOverlay.classList.remove('active');
            setTimeout(() => renderCharts(), 50);
        });

        // Initialize
        (async function init() {
            fetchLog.innerText = 'loading data...';
            await fetchAllData(false);
            renderMatrix();
            updateRisk();
            renderCharts();
        })();
    })();
</script>
</body>
</html>
