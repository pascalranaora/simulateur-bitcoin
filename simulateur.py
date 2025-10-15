import requests
import json
from datetime import date, datetime, timedelta
import time
import random
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import csv

def get_current_block_height():
    """Récupère la hauteur de bloc actuelle du Bitcoin."""
    try:
        response = requests.get("https://blockstream.info/api/blocks/tip/height")
        return int(response.text)
    except Exception as e:
        print(f"Erreur lors de la récupération de la hauteur de bloc : {e}")
        return 916944  # Fallback pour 29/09/2025

def get_btc_price_eur():
    """Récupère le prix actuel du BTC en EUR via CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        print("Prix Bitcoin euro: "+str(response.json()["bitcoin"]["eur"]))
        return response.json()["bitcoin"]["eur"]
    except Exception as e:
        print(f"Erreur lors de la récupération du prix : {e}")
        return 96500  # Updated fallback for Oct 2025

def get_current_hash_rate_ths():
    """Récupère le hash rate actuel en TH/s via Blockchain.info API."""
    try:
        response = requests.get("https://api.blockchain.info/charts/hash-rate?format=json")
        data = response.json()
        hr_ths = data['values'][-1]['y']
        return hr_ths
    except Exception as e:
        print(f"Erreur lors de la récupération du hash rate : {e}")
        return 1020000000  # Updated fallback approx 1020 EH/s = 1.02e9 TH/s

def days_since_genesis(current_date=None):
    """Calcule les jours depuis la genèse (03/01/2009)."""
    genesis = date(2009, 1, 3)
    if current_date is None:
        current_date = date.today()
    return (current_date - genesis).days

def get_historical_prices():
    start_date = datetime(2018, 1, 1)
    end_date = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    # Get Daily Bitcoin Historical Price https://www.tradingview.com/symbols/BTCEUR/ from TradingView and store them on filesystem and a dataframe for re-use later in the code
    
    
    # Get Bitcoin Historical Hashrate https://www.tradingview.com/symbols/HRATE/ from TradingView and store them on filesystem and a dataframe for re-use later in the code
    tv = TvDatafeed("", "")
    # Retry strategy to bypass TvDatafeed errors
    for i in range(10):
        try:
            data = tv.get_hist(symbol="BTCEUR",exchange="COINBASE",interval=Interval.in_daily,n_bars=5000)
            # Resample for complete daily data forward filled
            data = data.resample('1D').ffill()
            data.index = pd.to_datetime(data.index).date
            data = data[data.index >= start_date.date()]
            data['date'] = pd.to_datetime(data.index).date
            data['date_integer'] = data['date'].apply(to_integer)
            print(data['date_integer'])
            data['price'] = data.close
            df = data[['date','price']]
            print(df)
            # Save to a local CSV file
            output_file = 'historical_btcprice.csv'
            df.to_csv(output_file, index=False)
            print("Fichier historical_btcprice.csv généré")
            break
        except Exception as e:
            print("Iteration #"+str(i)+" has failed: "+str(e)+" retrying...")
            continue

def get_power_law_points(current_date, exponent=5.6, years_ahead=7):
    """Génère des points pour la courbe de loi de puissance."""
    current_days = days_since_genesis(current_date)
    price_eur = get_btc_price_eur()
    A = price_eur / (current_days ** exponent)

    points = []
    for i in range(0, (years_ahead * 365) + 1, 30):  # Tous les 30 jours pour lisser
        day = current_days + i
        year = 2009 + (day / 365.25)
        price = A * (day ** exponent)
        points.append({'x': year, 'y': price})
    return points, A, exponent

def calculate_mined_btc(start_block, current_block):
    """Calcule le total de BTC minés depuis le bloc de départ jusqu'au bloc actuel."""
    total_btc = 0.0

    # Période 1 : Blocs ~499500 à 630000 (récompense 12.5 BTC)
    halving1_end = 630000
    blocks1 = max(0, min(halving1_end, current_block) - max(start_block, 499500))
    total_btc += blocks1 * 12.5

    # Période 2 : Blocs 630000 à 840000 (récompense 6.25 BTC)
    halving2_start = 630000
    halving2_end = 840000
    blocks2_start = max(start_block, halving2_start)
    blocks2_end = min(halving2_end, current_block)
    blocks2 = max(0, blocks2_end - blocks2_start)
    total_btc += blocks2 * 6.25

    # Période 3 : Blocs 840000 à maintenant (récompense 3.125 BTC)
    halving3_start = 840000
    blocks3_start = max(start_block, halving3_start)
    blocks3_end = current_block
    blocks3 = max(0, blocks3_end - blocks3_start)
    total_btc += blocks3 * 3.125

    return total_btc

def calculate_opportunity_cost(share=0.03):  # 3% de part hypothétique
    """Calcule le coût d'opportunité, plus données pour graphique."""
    start_block = 499500  # Hauteur approximative au 1er janvier 2018
    current_block = get_current_block_height()
    price_eur = get_btc_price_eur()
    current_date = date.today()

    total_mined_btc = calculate_mined_btc(start_block, current_block)
    france_btc_past = total_mined_btc * share
    value_eur_past = france_btc_past * price_eur
    total_euros_past = int(value_eur_past)  # En euros complets

    # Données historiques pour le graphique
    hist_points = get_historical_prices()

    initial_blocks = current_block - start_block

    # Calcul initial MW/jour total réseau (puissance moyenne)
    hr_ths = get_current_hash_rate_ths()
    eff = 30  # J/TH moyenne
    total_power_w = hr_ths * eff
    total_mw = total_power_w / 1_000_000

    # Points pour loi de puissance
    power_points, A, exponent = get_power_law_points(current_date)

    return {
        'france_btc_past': france_btc_past,
        'total_euros_past': total_euros_past,
        'price_eur': price_eur,
        'share': share,
        'hist_points': hist_points,
        'initial_blocks': initial_blocks,
        'start_block': start_block,
        'initial_current_block': current_block,
        'total_mined_btc': total_mined_btc,
        'initial_total_mw': total_mw,
        'power_points': power_points,
        'A': A,
        'exponent': exponent
    }

def to_integer(dt_time):
    return 10000*dt_time.year + 100*dt_time.month + dt_time.day

def generate_sample_hash_csv():
    """Génère un fichier CSV pour le hashrate historique."""
    start_date = datetime(2018, 1, 1)
    end_date = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    
    # Get Bitcoin Historical Hashrate https://www.tradingview.com/symbols/HRATE/ from TradingView and store them on filesystem and a dataframe for re-use later in the code
    tv = TvDatafeed("", "")
    # Retry strategy to bypass TvDatafeed errors
    for i in range(10):
        try:
            data = tv.get_hist(symbol="HRATE",exchange="BCHAIN",interval=Interval.in_daily,n_bars=5000)
            # Resample for complete daily data forward filled
            data = data.resample('1D').ffill()
            data.index = pd.to_datetime(data.index).date
            data = data[data.index >= start_date.date()]
            data['date'] = pd.to_datetime(data.index).date
            data['date_integer'] = data['date'].apply(to_integer)
            print(data['date_integer'])
            data['EH/s'] = data.close / 1_000_000
            df = data[['date','EH/s']]
            print(df)
            # Save to a local CSV file
            output_file = 'sample_hashrate.csv'
            df.to_csv(output_file, index=False)
            print("Fichier sample_hashrate.csv généré")
            break
        except Exception as e:
            print("Iteration #"+str(i)+" has failed: "+str(e)+" retrying...")
            continue
    
    

def generate_sample_power_csv():
    """Génère un fichier CSV d'exemple pour la puissance du site."""
    start_date = datetime(2018, 1, 1)
    end_date = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    current_date = start_date
    power_data = []

    while current_date <= end_date:
        mw = 80 + 40 * random.random()  # 80-120 MW
        power_data.append(f"{current_date.date().isoformat()},{mw:.0f}")
        current_date += timedelta(days=1)

    csv_content = "date,MW\n" + "\n".join(power_data)

    with open('sample_power.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print("Fichier sample_power.csv généré")

def load_sample_csv(filename):
    """Charge les données d'un fichier CSV d'exemple."""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row and len(row) >= 2:
                date_str = row[0].strip()
                try:
                    val = float(row[1].strip())
                    if filename.endswith('hashrate.csv'):
                        data.append({'date': date_str, 'ehs': val})
                    elif filename.endswith('btcprice.csv'):
                        data.append({'date': date_str, 'pr': val}) 
                    else:
                        data.append({'date': date_str, 'mw': val})
                except ValueError:
                    pass
    return data

def generate_html():
    """Génère le fichier HTML avec mises à jour en temps réel via API."""
    result = calculate_opportunity_cost()
    
    # Load sample data
    generate_sample_power_csv()
    generate_sample_hash_csv()
    get_historical_prices()
    hash_sample = load_sample_csv('sample_hashrate.csv')
    power_sample = load_sample_csv('sample_power.csv')
    price_sample = load_sample_csv('historical_btcprice.csv')

    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compteur Bitcoin France</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Arial:wght@400;700&display=swap');
        
        img {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: #000;
            color: #fff;
            margin: 0;
            padding: 0;
            overflow: auto;
        }}
        .container {{ display: flex; min-height: 100vh; }}
        .left {{
            flex: 1;
            padding: 40px;
            display: flex;
            flex-direction: column;
            background: #000;
        }}
        .right {{
            flex: 1;
            padding: 40px;
            background: #111;
        }}
        h1 {{
            font-size: 2.5em;
            color: #F7931A;
            margin-bottom: 20px;
            text-align: center;
        }}
        p {{ color: #ccc; text-align: center; margin-bottom: 40px; }}
        .label {{
            font-size: 1.2em;
            color: #F7931A;
            margin-bottom: 10px;
            text-align: center;
        }}
        h2 {{ color: #F7931A; text-align: center; margin-bottom: 20px; }}
        a:link {{
        color: orange;
        background-color: transparent;
        text-decoration: none;
        }}

        a:visited {{
        color: orange;
        background-color: transparent;
        text-decoration: none;
        }}

        a:hover {{
        color: red;
        background-color: transparent;
        text-decoration: underline;
        }}

        a:active {{
        color: orange;
        background-color: transparent;
        text-decoration: underline;
        }}

        table {{ border-collapse: collapse; width: 100%; color: #FFF;}}
        th, td {{ border: 1px solid #FF9900; padding: 8px; text-align: right; }}
        th {{ background-color: #000; text-align: left; }}
        .slider-container {{ margin: 10px 0; display: flex; align-items: center; color: #FF9900;}}
        .slider-container label {{ width: 200px; margin-right: 10px; }}
        .slider-container input {{ flex: 1; }}
        .slider-container span {{ width: 60px; margin-left: 10px; text-align: right; }}
        .wrapper {{
            text-align: center;
        }}
        button {{ padding: 10px; background: #FF9900; color: white; border: none; cursor: pointer; }}

        .updating {{ color: #ccc; font-size: 0.9em; text-align: center; margin-top: 20px; }}
        /* Tooltip Styles - Updated for ? icon */
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 350px;
            background-color: #111;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            top: 125%;
            left: 50%;
            margin-left: -45px;
            margin-bottom: -45px;
            opacity: 0;
            transition: opacity 0.3s;
            border: 1px solid #F7931A;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        .tooltip .tooltiptext::after {{
            content: "";
            position: absolute;
            bottom: 100%;
            right: 80%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #F7931A transparent transparent transparent;
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}

        .tooltip .tooltip-icon {{
            color: #0066cc;
            font-weight: bold;
            font-size: 0.7em;
            margin-left: 2px;
            vertical-align: super;
        }}

        :root {{
        --track-height: 6px;
        --thumb-height: 18px;
        --thumb-width: 18px;
        }}

        input[type="range"] {{
        appearance: none;
        background: transparent;
        width: 15rem;
        cursor: pointer;
        border-radius: 3px;
        }}

        /* Inpiut Track */

        /* Chrome, Safari, Edge (Chromium) */
        input[type="range"]::-webkit-slider-runnable-track {{
        background: linear-gradient(to right, #fff 0%, #ff9900 100%);
        height: var(--track-height);
        border-radius: 3px;
        }}

        /* Firefox */
        input[type="range"]::-moz-range-track {{
        background: linear-gradient(to right, #fff 0%, #ff9900 100%);
        height: var(--track-height);
        border-radius: 3px;
        }}

        /* Inpiut Thumb */

        /* Chrome, Safari, Edge (Chromium) */
        input[type="range"]::-webkit-slider-thumb {{
        appearance: none;
        background: #fff;
        border-radius: 50%;
        width: var(--thumb-width);
        height: var(--thumb-height);
        margin-top: calc((var(--track-height) / 2) - (var(--thumb-height) / 2));
        border: 3px solid #ff9900;
        }}

        /* Firefox */
        input[type="range"]::-moz-range-thumb {{
        appearance: none;
        background: #fff;
        border-radius: 0;
        border-radius: 50%;
        border: 3px solid #ff9900;
        }}

        .file-upload {{ margin: 10px 0; color: #FF9900; }}
        .file-upload label {{ display: block; margin-bottom: 5px; }}
        .file-upload input[type="file"] {{ margin-bottom: 10px; }}
        .mode-container {{ margin: 10px 0; color: #FF9900; display: flex; align-items: center; }}
        .mode-container label {{ margin-right: 10px; }}


    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <img src="https://res.cloudinary.com/daabdiwnt/image/upload/v1760479746/INBI/LOGO-INBI_aezky1.webp" alt="Logo INBI"> 
            <h1>Simulateur site de minage</h1>
            <p style="color: #FF9900;">Cette simulation modélise un déploiement variable sur site de minage Bitcoin (2026-2032), avec loi de puissance pour le prix BTC (en EUR, convertis en EUR), halving 2028, et croissance du hash global. Glissez les sliders pour ajuster les paramètres et voir les mises à jour en temps réel.
            Un mode "projection" est aussi proposé. En prenant des données du taux de hachage historique
            </p>

            <div class="file-upload">
                <label>CSV Profil de Puissance Minable du Site   (format: date,MW) :</label>
                <input type="file" id="powerCsv" accept=".csv">
            </div>

            <!-- <div class="file-upload">
                 <label>CSV Hashrate historique (format: date,EH/s) :</label>
                 <input type="file" id="hashCsv" accept=".csv">
            </div> -->

            <div class="mode-container">
                <label>Mode projection :</label>
                <input type="checkbox" id="projectionMode" checked>
            </div>

            <div id="dateRangeContainer" style="display: none;">
                <div class="slider-container">
                    <label>Date de début :</label>
                    <input type="range" id="startDateSlider" min="0" max="0" step="1" value="0">
                    <span id="startDateValue"></span>
                </div>
                <div class="slider-container">
                    <label>Date de fin :</label>
                    <input type="range" id="endDateSlider" min="0" max="0" step="1" value="0">
                    <span id="endDateValue"></span>
                </div>
            </div>

            <div class="slider-container" id="efficiencySliderContainer">
                <label>Efficacité Minage (J/TH) :<span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Efficacité énergétique des ASICs (Joules par Terahash). Plus bas = plus efficace.</span></span></label>
                <input type="range" id="efficiencySlider" min="1" max="50" step="1" value="18">
                <span id="efficiencyValue">18</span>
            </div>

            <div class="slider-container" id="feesSliderContainer">
                <label>Frais par bloc (BTC) :<span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Frais moyens par bloc (en BTC). Actuel ~0.022, peut varier avec adoption.</span></span></label>
                <input type="range" id="feesSlider" min="0.010" max="0.2" step="0.002" value="0.022">
                <span id="feesValue">0.022</span>
            </div>

            <div class="slider-container" id="exponentSliderContainer">
                <label>Exposant loi de puissance :<span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Exposant dans P(t) = a * t^exposant. 5.6 est calibré historique ; plus haut = croissance plus agressive.</span></span></label>
                <input type="range" id="exponentSlider" min="4" max="7" step="0.1" value="5.6">
                <span id="exponentValue">5.6</span>
            </div>

            <div class="slider-container" id="growthSliderContainer">
                <label>Croissance hash/an (%):<span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Croissance annuelle estimée du hash global (~50%/an historique). Dilue le % français sans upgrade hardware.</span></span></label>
                <input type="range" id="growthSlider" min="0" max="100" step="5" value="30">
                <span id="growthValue">30</span>
            </div>

            
        </div>

        <div class="right">
            
            <div id="results-table"></div>
            <h2>Puissance du Site (MW)</h2>
            <canvas id="powerChart" width="800" height="400"></canvas>

            <h2>Hashrate Historique (EH/s)</h2>
            <canvas id="hashChart" width="800" height="400"></canvas>

            <h2>Évolution Projetée du Prix du Bitcoin (EUR)</h2>
            <canvas id="priceChart" width="800" height="400"></canvas>

            <h2>Revenus Annuels Projetés (M EUR)</h2>
            <canvas id="revenueChart" width="800" height="400"></canvas>

            <h2>Revenus Cumulés Projetés (M EUR)</h2>
            <canvas id="cumulativeChart" width="800" height="400"></canvas>

            

            
        </div>
        </div>
    </div>


    <script>

        // Paramètres de simulation
        const GENESIS_DATE = new Date(2009, 0, 3);  // 3 janv 2009
        const CURRENT_HASH_EH_S = 1020;  // Hash global actuel (EH/s) updated for 2025
        const BLOCKS_PER_DAY = 144;
        const DAYS_PER_YEAR = 365.25;
        let FEES_PER_BLOCK = 0.022;
        let A_POWER_LAW = 6.013753970346012e-17;  // Calibré initialement
        let ANNUAL_GROWTH_RATE = 1.3;  // 30% initial
        let SITE_HASH_EH_S = 55.6;  // Initial
        let powerAverage = 1000;  // Default MW exploitable du site
        let historicalHash = {{}};  // year: avg EH/s
        let powerData = []; // {{date: string, mw: number}}
        let hashData = []; // {{date: string, ehs: number}}
        let EFFICIENCY = 18;
        let minPowerDate, maxPowerDate;

        let priceChart, revenueChart, cumulativeChart, hashChart, powerChart;

        const hashSample = {json.dumps(hash_sample)};
        const powerSample = {json.dumps(power_sample)};
        const btcHistoricalPrice = {json.dumps(price_sample)};
        
        function parseHashData(dataArray) {{
            let tempHash = {{}};
            dataArray.forEach(d => {{
                const date = new Date(d.date);
                if (!isNaN(date.getTime())) {{
                    const year = date.getFullYear();
                    if (!tempHash[year]) {{
                        tempHash[year] = {{sum: 0, count: 0}};
                    }}
                    tempHash[year].sum += d.ehs;
                    tempHash[year].count++;
                }}
            }});
            historicalHash = {{}};
            for (let y in tempHash) {{
                historicalHash[y] = tempHash[y].sum / tempHash[y].count;
            }}
            hashData = hashSample;
            console.log('Historical hash yearly:', historicalHash);
            console.log('Historical hash daily:', hashData);
        }}

        function parsePowerData(dataArray) {{
            let sum = 0, count = 0;
            dataArray.forEach(d => {{
                sum += d.mw;
                count++;
            }});
            powerAverage = count > 0 ? sum / count : 1000;
            powerData = dataArray.sort((a, b) => new Date(a.date) - new Date(b.date));
            if (powerData.length > 0) {{
                minPowerDate = new Date(powerData[0].date);
                maxPowerDate = new Date(powerData[powerData.length - 1].date);
            }}
            console.log('MW minage journalier moyen du site:', powerAverage);
        }}

        function initializeDateSliders() {{
            if (powerData.length > 0) {{
                const diffTime = maxPowerDate - minPowerDate;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                const startSlider = document.getElementById('startDateSlider');
                const endSlider = document.getElementById('endDateSlider');
                startSlider.max = diffDays - 1;
                endSlider.max = diffDays - 1;
                startSlider.min = 0;
                endSlider.min = 0;
                startSlider.value = 0;
                endSlider.value = diffDays - 1;
                updateStartDateValue();
                updateEndDateValue();
            }}
        }}
        
        // Load samples automatically
        parseHashData(hashSample);
        parsePowerData(powerSample);
        initializeDateSliders();

        // Create lookup for historical prices
        const btcHist = {{}};
        btcHistoricalPrice.forEach(item => {{
            btcHist[item.date] = item.pr;
        }});

        function updateStartDateValue() {{
            const sliderVal = parseInt(document.getElementById('startDateSlider').value);
            const date = new Date(minPowerDate);
            date.setDate(date.getDate() + sliderVal);
            document.getElementById('startDateValue').textContent = date.toISOString().split('T')[0];
        }}

        function updateEndDateValue() {{
            const sliderVal = parseInt(document.getElementById('endDateSlider').value);
            const date = new Date(minPowerDate);
            date.setDate(date.getDate() + sliderVal);
            document.getElementById('endDateValue').textContent = date.toISOString().split('T')[0];
        }}

        // Halving approx mid year
        function getAverageReward(year) {{
            let baseReward;
            if (year < 2012) baseReward = 50;
            else if (year < 2016) baseReward = 25;
            else if (year < 2020) baseReward = 12.5;
            else if (year < 2024) baseReward = 6.25;
            else if (year < 2028) baseReward = 3.125;
            else if (year < 2032) baseReward = 1.5625;
            else baseReward = 0.78125;

            // For halving years, approximate mid-year average
            const halvingYears = [2012, 2016, 2020, 2024, 2028, 2032];
            if (halvingYears.includes(year)) {{
                let oldReward;
                if (year === 2012) oldReward = 50;
                else if (year === 2016) oldReward = 25;
                else if (year === 2020) oldReward = 12.5;
                else if (year === 2024) oldReward = 6.25;
                else if (year === 2028) oldReward = 3.125;
                else if (year === 2032) oldReward = 1.5625;
                baseReward = (oldReward + baseReward) / 2;
            }}
            return baseReward + FEES_PER_BLOCK;
        }}

        function getDaysFromGenesis(inputDate) {{
            const diffTime = inputDate - GENESIS_DATE;
            return Math.floor(diffTime / (1000 * 60 * 60 * 24));
        }}

        function getBTCPrice(days, exponent) {{
            return A_POWER_LAW * Math.pow(days, exponent);
        }}

        function handlePowerCsv(e) {{
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(ev) {{
                const text = ev.target.result;
                const lines = text.split(/\\r?\\n/);
                powerData = [];
                let sum = 0, count = 0;
                for (let i = 1; i < lines.length; i++) {{
                    if (lines[i].trim() === '') continue;
                    const parts = lines[i].split(',');
                    if (parts.length >= 2) {{
                        const dateStr = parts[0].trim();
                        const mw = parseFloat(parts[1]);
                        if (!isNaN(mw)) {{
                            powerData.push({{date: dateStr, mw: mw}});
                            sum += mw;
                            count++;
                        }}
                    }}
                }}
                parsePowerData(powerData);
                if (count > 0) {{
                    powerAverage = sum / count;
                    console.log('MW journalier moyen site:', powerAverage);
                }}
                initializeDateSliders();
                const dateCont = document.getElementById('dateRangeContainer');
                if (!document.getElementById('projectionMode').checked) {{
                    dateCont.style.display = powerData.length > 0 ? 'block' : 'none';
                }}
                updateSimulation();
            }};
            reader.readAsText(file);
        }}

        // Mise à jour des sliders avec appel dynamique à updateSimulation
        document.getElementById('efficiencySlider').oninput = function() {{
            document.getElementById('efficiencyValue').textContent = this.value;
            updateSimulation();
        }};
        document.getElementById('feesSlider').oninput = function() {{
            document.getElementById('feesValue').textContent = this.value;
            updateSimulation();
        }};
        document.getElementById('startDateSlider').oninput = function() {{
            updateStartDateValue();
            updateSimulation();
        }};
        document.getElementById('endDateSlider').oninput = function() {{
            updateEndDateValue();
            updateSimulation();
        }};

        document.getElementById('projectionMode').onchange = function() {{
            const checked = this.checked;
            document.getElementById('exponentSliderContainer').style.display = !checked ? 'none' : 'flex';
            document.getElementById('growthSliderContainer').style.display = !checked ? 'none' : 'flex';
            const dateCont = document.getElementById('dateRangeContainer');
            dateCont.style.display = !checked && powerData.length > 0 ? 'block' : 'none';
            updateSimulation();
        }};

        document.getElementById('exponentSlider').oninput = function() {{
            document.getElementById('exponentValue').textContent = this.value;
            updateSimulation();
        }};
        document.getElementById('growthSlider').oninput = function() {{
            document.getElementById('growthValue').textContent = this.value;
            updateSimulation();
        }};

        document.getElementById('powerCsv').addEventListener('change', handlePowerCsv);
        // document.getElementById('hashCsv').addEventListener('change', handleHashCsv);

        function updateSimulation() {{
            const efficiency = parseInt(document.getElementById('efficiencySlider').value);
            const exponent = parseFloat(document.getElementById('exponentSlider').value);
            ANNUAL_GROWTH_RATE = 1 + (parseFloat(document.getElementById('growthSlider').value) / 100);
            FEES_PER_BLOCK = parseFloat(document.getElementById('feesSlider').value);
            const projection = document.getElementById('projectionMode').checked;

            const effective_MW = powerAverage;
            const effective_GW = effective_MW / 1000;
            SITE_HASH_EH_S = (1000 / efficiency) * effective_GW;
            EFFICIENCY = efficiency;

            // Recalculer A si exposant change (calibré sur prix actuel)
            const currentDate = new Date(2025, 6, 1);
            const currentDays = getDaysFromGenesis(currentDate);
            // Pass the price_eur value as a string literal to the JavaScript
            const currentPrice = 95335;
            A_POWER_LAW = currentPrice / Math.pow(currentDays, exponent);

            // Generate sorted dates
            let sortedDates = [];
            if (!projection) {{
                if (powerData.length === 0 && hashData.length === 0) return;
                let start, end;
                if (powerData.length > 0) {{
                    const startOffset = parseInt(document.getElementById('startDateSlider').value);
                    const endOffset = parseInt(document.getElementById('endDateSlider').value);
                    start = new Date(minPowerDate.getTime() + startOffset * 86400000);
                    end = new Date(minPowerDate.getTime() + endOffset * 86400000);
                }} else {{
                    const hashDates = hashData.map(d => new Date(d.date)).sort((a, b) => a - b);
                    start = hashDates[0];
                    end = hashDates[hashDates.length - 1];
                }}
                let current = new Date(start);
                while (current <= end) {{
                    sortedDates.push(current.toISOString().split('T')[0]);
                    current.setDate(current.getDate() + 1);
                }}
            }} else {{
                let startDate = new Date(2026, 0, 1);
                let endDate = new Date(2032, 11, 31);
                let current = new Date(startDate);
                while (current <= endDate) {{
                    sortedDates.push(current.toISOString().split('T')[0]);
                    current.setDate(current.getDate() + 1);
                }}
            }}

            let yearSums = {{}};
            let cumulativeRevenueEur = 0;
            let dailySimulation = []; // For projection daily results

            sortedDates.forEach(dateStr => {{
                const date = new Date(dateStr);
                const year = date.getFullYear();
                const days = getDaysFromGenesis(date);

                // Price
                let priceEur;
                if (!projection && btcHist[dateStr]) {{
                    priceEur = btcHist[dateStr];
                }} else {{
                    priceEur = getBTCPrice(days, exponent);
                }}

                // Daily site MW and hash
                const dailyMw = !projection ? (powerData.find(p => p.date === dateStr)?.mw || powerAverage) : powerAverage;
                const dailySiteHashEh = (1000 / EFFICIENCY) * (dailyMw / 1000);

                // Daily global hash
                let dailyGlobalHash;
                if (!projection) {{
                    dailyGlobalHash = hashData.find(h => h.date === dateStr)?.ehs || (historicalHash[year] || CURRENT_HASH_EH_S);
                }} else {{
                    dailyGlobalHash = CURRENT_HASH_EH_S * Math.pow(ANNUAL_GROWTH_RATE, year - 2025);
                }}

                const hashPct = (dailySiteHashEh / dailyGlobalHash) * 100;
                const avgReward = getAverageReward(year);
                const totalBtcDay = avgReward * BLOCKS_PER_DAY;
                const btcMinedDay = (hashPct / 100) * totalBtcDay;
                const revenueDayEur = btcMinedDay * priceEur;
                cumulativeRevenueEur += revenueDayEur;

                if (!yearSums[year]) {{
                    yearSums[year] = {{btc: 0, revenue: 0, days: 0, prices: [], hashPcts: []}};
                }}
                yearSums[year].btc += btcMinedDay;
                yearSums[year].revenue += revenueDayEur;
                yearSums[year].days++;
                yearSums[year].prices.push(priceEur);
                yearSums[year].hashPcts.push(hashPct);

                if (!projection) {{
                    dailySimulation.push({{
                        date: dateStr,
                        priceEur: priceEur,
                        hashPct: hashPct,
                        btcMined: btcMinedDay,
                        revenueEur: revenueDayEur,
                        siteHash: dailySiteHashEh,
                        globalHash: dailyGlobalHash,
                        cumulativeEur: cumulativeRevenueEur
                    }});
                }}
            }});

            // Build yearly simulation data
            let sortedYears = Object.keys(yearSums).sort((a, b) => parseInt(a) - parseInt(b));
            let simulationData = [];
            let runningCum = 0;
            sortedYears.forEach(y => {{
                const ys = yearSums[y];
                const avgPrice = ys.prices.reduce((a, b) => a + b, 0) / ys.prices.length;
                const avgHashPct = ys.hashPcts.reduce((a, b) => a + b, 0) / ys.hashPcts.length;
                runningCum += ys.revenue;
                simulationData.push({{
                    year: parseInt(y),
                    priceEur: avgPrice,
                    hashPct: avgHashPct,
                    btcMined: ys.btc,
                    revenueEur: ys.revenue,
                    cumulativeEur: runningCum
                }});
            }});

            // Génération du tableau annuel
            let tableHTML = `
                <h2>Synthèse Performance (annualisée)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Année</th>
                            <th>Prix BTC (EUR)</th>
                            <th>% Hash Site</th>
                            <th>BTC Minés</th>
                            <th>Revenus Annuels (M EUR)</th>
                            <th>Revenus Cumulés (M EUR)</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            simulationData.forEach(row => {{
                tableHTML += `
                    <tr>
                        <td>${{row.year}}</td>
                        <td>${{Math.round(row.priceEur).toLocaleString()}}</td>
                        <td>${{row.hashPct.toFixed(3)}} %</td>
                        <td>${{Math.round(row.btcMined).toLocaleString()}}</td>
                        <td>${{Math.round(row.revenueEur).toLocaleString()}}</td>
                        <td>${{Math.round(row.cumulativeEur).toLocaleString()}}</td>
                    </tr>
                `;
            }});
            tableHTML += `
                    </tbody>
                    <tfoot>
                        <tr style="font-weight: bold;">
                            <td>Total</td>
                            <td colspan="2"></td>
                            <td>${{Math.round(simulationData.reduce((sum, r) => sum + r.btcMined, 0)).toLocaleString()}} BTC</td>
                            <td colspan="2">${{Math.round(simulationData[simulationData.length - 1]?.cumulativeEur || 0).toLocaleString()}} M EUR</td>
                        </tr>
                    </tfoot>
                </table>
            `;

            let fullHTML = tableHTML;

            // Add daily table if projection
            if (!projection && dailySimulation.length > 0) {{
                let dailyTableHTML = `
                    <h2>Résultats de Simulation Quotidienne</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Prix BTC (EUR)</th>
                                <th>% Hash Site</th>
                                <th>Hash rate du site (EH/s)</th>
                                <th>Hash rate du reseau bitcoin (EH/s)</th>
                                <th>BTC Minés</th>
                                <th>Revenus Quotidiens (EUR)</th>
                                <th>Revenus Quotidiens cumules (EUR)</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                dailySimulation.forEach(d => {{
                    dailyTableHTML += `
                        <tr>
                            <td>${{d.date}}</td>
                            <td>${{Math.round(d.priceEur).toLocaleString()}}</td>
                            <td>${{d.hashPct.toFixed(3)}} %</td>
                            <td>${{d.siteHash.toFixed(2)}}</td>
                            <td>${{d.globalHash.toFixed(2)}}</td>
                            <td>${{(d.btcMined).toFixed(6)}}</td>
                            <td>${{Math.round(d.revenueEur).toLocaleString()}}</td>
                            <td>${{Math.round(d.cumulativeEur).toLocaleString()}}</td>
                        </tr>
                    `;
                }});
                const totalDailyBtc = dailySimulation.reduce((sum, d) => sum + d.btcMined, 0);
                const totalDailyRev = dailySimulation.reduce((sum, d) => sum + d.revenueEur, 0);
                const avgSiteHash = dailySimulation.reduce((sum, d) => sum + d.siteHash, 0) / dailySimulation.length;
                const avgGlobalHash = dailySimulation.reduce((sum, d) => sum + d.globalHash, 0) / dailySimulation.length;
                const finalCum = dailySimulation[dailySimulation.length - 1].cumulativeEur;
                dailyTableHTML += `
                        </tbody>
                        <tfoot>
                            <tr style="font-weight: bold;">
                                <td>Total</td>
                                <td colspan="2"></td>
                                <td>${{avgSiteHash.toFixed(2)}}</td>
                                <td>${{avgGlobalHash.toFixed(2)}}</td>
                                <td>${{totalDailyBtc.toFixed(6)}} BTC</td>
                                <td>${{Math.round(totalDailyRev).toLocaleString()}} EUR</td>
                                <td>${{Math.round(finalCum).toLocaleString()}} EUR</td>
                            </tr>
                        </tfoot>
                    </table>
                `;
                fullHTML += dailyTableHTML;
            }}

            document.getElementById('results-table').innerHTML = fullHTML;

            // Mise à jour des graphiques
            if (priceChart) priceChart.destroy();
            if (revenueChart) revenueChart.destroy();
            if (cumulativeChart) cumulativeChart.destroy();

            // Graphique 1: Prix BTC (EUR)
            const priceCtx = document.getElementById('priceChart').getContext('2d');
            priceChart = new Chart(priceCtx, {{
                type: 'line',
                data: {{
                    labels: simulationData.map(d => d.year.toString()),
                    datasets: [{{
                        label: 'Prix BTC (EUR)',
                        data: simulationData.map(d => d.priceEur),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: false, title: {{ display: true, text: 'Prix (EUR)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Projection du Prix du Bitcoin (Loi de Puissance)' }} }}
                }}
            }});

            // Graphique 2: Revenus Annuels (M EUR)
            const revenueCtx = document.getElementById('revenueChart').getContext('2d');
            revenueChart = new Chart(revenueCtx, {{
                type: 'bar',
                data: {{
                    labels: simulationData.map(d => d.year.toString()),
                    datasets: [{{
                        label: 'Revenus (M EUR)',
                        data: simulationData.map(d => d.revenueEur),
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Revenus (M EUR)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Revenus Annuels Projetés' }} }}
                }}
            }});

            // Graphique 3: Revenus Cumulés (M EUR)
            const cumulativeCtx = document.getElementById('cumulativeChart').getContext('2d');
            cumulativeChart = new Chart(cumulativeCtx, {{
                type: 'line',
                data: {{
                    labels: simulationData.map(d => d.year.toString()),
                    datasets: [{{
                        label: 'Revenus Cumulés (M EUR)',
                        data: simulationData.map(d => d.cumulativeEur),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Revenus Cumulés (M EUR)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Projection des Revenus Cumulés' }} }}
                }}
            }});

            // Graphique Hashrate Historique
            if (hashData.length > 0) {{
                if (hashChart) hashChart.destroy();
                const hashCtx = document.getElementById('hashChart').getContext('2d');
                hashChart = new Chart(hashCtx, {{
                    type: 'line',
                    data: {{
                        labels: hashData.map(d => d.date),
                        datasets: [{{
                            label: 'Hashrate (EH/s)',
                            data: hashData.map(d => d.ehs),
                            borderColor: '#ff6384',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            fill: true,
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            x: {{
                                type: 'time',
                                time: {{
                                    parser: 'yyyy-MM-dd',
                                    unit: 'month'
                                }},
                                title: {{ display: true, text: 'Date' }}
                            }},
                            y: {{ title: {{ display: true, text: 'EH/s' }} }}
                        }},
                        plugins: {{ title: {{ display: true, text: 'Hashrate Historique (Backtest)' }} }}
                    }}
                }});
            }}

            // Graphique Puissance du Site
            if (powerData.length > 0) {{
                if (powerChart) powerChart.destroy();
                const powerCtx = document.getElementById('powerChart').getContext('2d');
                powerChart = new Chart(powerCtx, {{
                    type: 'line',
                    data: {{
                        labels: powerData.map(d => d.date),
                        datasets: [{{
                            label: 'Puissance (MW)',
                            data: powerData.map(d => d.mw),
                            borderColor: '#36a2eb',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: true,
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            x: {{
                                type: 'time',
                                time: {{
                                    parser: 'yyyy-MM-dd',
                                    unit: 'month'
                                }},
                                title: {{ display: true, text: 'Date' }}
                            }},
                            y: {{ title: {{ display: true, text: 'MW' }} }}
                        }},
                        plugins: {{ title: {{ display: true, text: 'Puissance Minable du Site (MW)' }} }}
                    }}
                }});
            }}
        }}

        // Initialisation
        updateSimulation();

    </script>
</body>
</html>
    """

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("Fichier index.html généré")

if __name__ == "__main__":
    generate_html()
    