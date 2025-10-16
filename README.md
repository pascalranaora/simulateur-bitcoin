# Simulateur de Minage Bitcoin

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description

Ce repository contient un simulateur simple de minage Bitcoin écrit en Python. Il permet d'analyser les revenus potentiels d'un site de minage en deux modes principaux :

- **Mode Simulation (projection non cochée)** : Charge les données historiques d'un site de minage (puissance en MW journalière) pour effectuer un backtest depuis 2018. Il utilise des données de prix du Bitcoin et de hashrate global pour calculer les revenus rétroactifs.
  
- **Mode Projection (case "projection" cochée)** : Calcule la puissance moyenne du site à partir des données historiques et projette les revenus futurs sur un nombre d'années défini (par défaut 7 ans). Les projections intègrent une loi de puissance pour l'évolution du prix du Bitcoin, les halvings (réductions de récompenses) et la croissance du hashrate global.

Le script génère des fichiers CSV pour les données historiques et un fichier HTML interactif avec des sliders pour ajuster les paramètres (part de marché, puissance, exposant de la loi de puissance, etc.) et visualiser les graphiques en temps réel.

**Note** : Ce simulateur est éducatif et hypothétique. Il ne modélise pas les coûts réels (électricité, maintenance) et utilise des approximations (ex. : efficacité de 30 J/TH).

## Prérequis

- Python 3.8 ou supérieur
- Bibliothèques : `requests`, `pandas`, `tvDatafeed` (pour les données TradingView)

## Installation

1. Clonez le repository :
   ```
   git clone https://github.com/pascalranaora/simulateur-bitcoin.git
   cd simulateur-bitcoin
   ```

2. Installez les dépendances :
   ```
   pip install requests pandas tvDatafeed
   ```

3. Exécutez le script :
   ```
   python simulateur.py
   ```

Cela générera :
- `historical_btcprice.csv` : Prix historiques du Bitcoin en EUR depuis 2018.
- `historical_data_hashrate.csv` : Hashrate historique en EH/s.
- `sample_power.csv` : Exemple de profil de puissance (80-120 MW).
- `Tricastin-1.csv` : Exemple spécifique pour un site (20-60 MW).
- `index.html` : Interface web interactive.

Ouvrez `index.html` dans un navigateur pour interagir avec le simulateur.

## Utilisation

1. **Lancement** : Exécutez `python simulateur.py` pour générer les fichiers.

2. **Interface HTML** :
   - Ouvrez `index.html`.
   - Ajustez les sliders.
   - Cochez/décochez **Projection** pour basculer entre modes.
   - Visualisez les graphiques : Revenus cumulés, prix projeté, etc.

3. **Modes détaillés** :
   - **Simulation (backtest)** : Charge les CSV de puissance du site, prix BTC et hashrate. Calcule les BTC minés et revenus depuis 2018 en fonction de la part de marché.
   - **Projection** : Utilise la puissance moyenne historique pour extrapoler. Applique la loi de puissance au prix BTC, ajuste pour les halvings futurs et la croissance du hashrate.

Exemple de sortie : Revenus cumulés projetés en M€, graphiques de prix et puissance.

## Détails Techniques : Analyse du Code `simulateur.py`

Le script `simulateur.py` est structuré autour de fonctions utilitaires pour la récupération de données, les calculs et la génération d'interface. Voici une explication détaillée, section par section.

### Imports et Dépendances
```python
import requests
import json
from datetime import date, datetime, timedelta
import time
import random
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import csv
```
- `requests` et `json` : Pour les appels API (Blockstream, CoinGecko, Blockchain.info).
- `datetime` et `timedelta` : Gestion des dates pour les historiques et projections.
- `random` : Génération de données d'exemple randomisées.
- `pandas` et `tvDatafeed` : Traitement des données TradingView (prix BTC, hashrate).
- `csv` : Lecture/écriture des fichiers CSV.

### Fonctions Utilitaires pour Données Actuelles
Ces fonctions récupèrent les données en temps réel avec fallbacks.

```python
def get_current_block_height():
    """Récupère la hauteur de bloc actuelle du Bitcoin."""
    try:
        response = requests.get("https://blockstream.info/api/blocks/tip/height")
        return int(response.text)
    except Exception as e:
        print(f"Erreur lors de la récupération de la hauteur de bloc : {e}")
        return 916944  # Fallback pour 29/09/2025
```
- Calcule les blocs minés pour les halvings.

```python
def get_btc_price_eur():
    """Récupère le prix actuel du BTC en EUR via CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        print("Prix Bitcoin euro: "+str(response.json()["bitcoin"]["eur"]))
        return response.json()["bitcoin"]["eur"]
    except Exception as e:
        print(f"Erreur lors de la récupération du prix : {e}")
        return 96500  # Updated fallback for Oct 2025
```
- Prix actuel en EUR, utilisé pour les projections.

```python
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
```
- Hashrate global actuel, converti en TH/s.

```python
def days_since_genesis(current_date=None):
    """Calcule les jours depuis la genèse (03/01/2009)."""
    genesis = date(2009, 1, 3)
    if current_date is None:
        current_date = date.today()
    return (current_date - genesis).days
```
- Base pour la loi de puissance (jours depuis la genèse).

### Chargement des Données Historiques (Mode Simulation)
Ces fonctions récupèrent et stockent les données depuis 2018 pour le backtest.

```python
def get_historical_prices():
    start_date = datetime(2018, 1, 1)
    end_date = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    # ... (code pour TradingView)
    tv = TvDatafeed("", "")
    for i in range(10):  # Retry loop
        try:
            data = tv.get_hist(symbol="BTCEUR", exchange="COINBASE", interval=Interval.in_daily, n_bars=5000)
            data = data.resample('1D').ffill()
            # ... (traitement et sauvegarde en CSV)
            df.to_csv('historical_btcprice.csv', index=False)
            break
        except Exception as e:
            print("Iteration #"+str(i)+" has failed: "+str(e)+" retrying...")
            continue
```
- Récupère prix BTC en EUR via TradingView, resample quotidien, sauvegarde en `historical_btcprice.csv`.
- Similaire pour `get_hash_historical_data_csv()` avec symbole "HRATE" pour le hashrate en EH/s.

```python
def to_integer(dt_time):
    return 10000*dt_time.year + 100*dt_time.month + dt_time.day
```
- Convertit les dates en entier pour les index.

### Génération de Données d'Exemple pour Puissance du Site
Pour tester sans données réelles.

```python
def generate_sample_power_csv():
    """Génère un fichier CSV d'exemple pour la puissance du site."""
    # ... (boucle pour dates depuis 2018, MW random 80-120)
    with open('sample_power.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
```
- Génère profil journalier randomisé. Variante pour `generate_demo_tricastin_mining_power_csv()` (20-60 MW).

```python
def load_sample_csv(filename):
    """Charge les données d'un fichier CSV d'exemple."""
    # ... (lecture CSV, parsing en dicts {date, mw/ehs/pr})
```
- Charge les CSV pour utilisation dans les calculs.

### Projections Futures (Mode Projection)
```python
def get_power_law_points(current_date, exponent=5.6, years_ahead=7):
    """Génère des points pour la courbe de loi de puissance."""
    current_days = days_since_genesis(current_date)
    price_eur = get_btc_price_eur()
    A = price_eur / (current_days ** exponent)
    points = []
    for i in range(0, (years_ahead * 365) + 1, 30):  # Tous les 30 jours
        day = current_days + i
        year = 2009 + (day / 365.25)
        price = A * (day ** exponent)
        points.append({'x': year, 'y': price})
    return points, A, exponent
```
- Modélise le prix futur : `price = A * days^exponent`. Points tous les 30 jours sur `years_ahead` ans.

### Calculs des Revenus et BTC Minés
```python
def calculate_mined_btc(start_block, current_block):
    """Calcule le total de BTC minés depuis le bloc de départ jusqu'au bloc actuel."""
    total_btc = 0.0
    # Période 1 : Blocs ~499500 à 630000 (récompense 12.5 BTC)
    halving1_end = 630000
    blocks1 = max(0, min(halving1_end, current_block) - max(start_block, 499500))
    total_btc += blocks1 * 12.5
    # Période 2 : 630000 à 840000 (6.25 BTC)
    # Période 3 : 840000+ (3.125 BTC)
    # ... (similaire pour autres périodes)
    return total_btc
```
- Calcule BTC minés en tenant compte des halvings (récompenses : 12.5 → 6.25 → 3.125 BTC/bloc).

```python
def calculate_opportunity_cost(share=0.03):
    """Calcule le coût d'opportunité, plus données pour graphique."""
    start_block = 499500  # ~1er jan 2018
    current_block = get_current_block_height()
    price_eur = get_btc_price_eur()
    current_date = date.today()
    total_mined_btc = calculate_mined_btc(start_block, current_block)
    france_btc_past = total_mined_btc * share
    value_eur_past = france_btc_past * price_eur
    total_euros_past = int(value_eur_past)
    # ... (chargement historiques, calcul puissance totale réseau avec eff=30 J/TH)
    hr_ths = get_current_hash_rate_ths()
    eff = 30  # J/TH
    total_power_w = hr_ths * eff
    total_mw = total_power_w / 1_000_000
    power_points, A, exponent = get_power_law_points(current_date)
    return { ... }  # Dict avec tous les résultats pour HTML
```
- Cœur des calculs : BTC minés * part de marché * prix = revenus passés.
- Pour projection : Intègre puissance site / hashrate global pour part effective, applique loi de puissance et halvings futurs.

### Génération de l'Interface HTML
```python
def generate_html():
    """Génère le fichier HTML avec mises à jour en temps réel via API."""
    result = calculate_opportunity_cost()
    # Charge samples
    generate_sample_power_csv()
    get_hash_historical_data_csv()
    get_historical_prices()
    # ... (load CSV)
    html_content = f"""<!DOCTYPE html>
    <html><head><title>Simulateur Site de Minage Bitcoin</title></head>
    <body>
    <h1>Simulateur site de minage</h1>
    <p>Simulateur de minage Bitcoin écrit en Python+Javascript...</p>
    <!-- Sliders pour part, puissance, etc. -->
    <input type="checkbox" id="projection"> Projection
    <!-- Graphiques avec Chart.js ou similaire -->
    <div id="revenus">Revenus Cumulés Projetés (M€): {result['total_euros_past']/1e6:.2f}</div>
    </body></html>"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
```
- Génère HTML statique avec placeholders pour JS (mises à jour via API pour interactivité).
- Intègre résultats des calculs pour affichage initial.

### Exécution Principale
```python
if __name__ == "__main__":
    generate_html()
```
- Lance tout : calculs, CSV, HTML.

### Limites et Améliorations
- **Limites** : Pas de modélisation des coûts.
- **Améliorations** : Ajouter coûts énergétiques ; support pour halvings futurs ; interface JS plus avancée ; tests unitaires.

## Contribution

Forkez le repo et soumettez une Pull Request pour des améliorations. Merci !

## Licence

Ce projet est sous licence [MIT](LICENSE).