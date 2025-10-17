# Simulateur Bitcoin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description

Ce dépôt contient un simulateur de minage Bitcoin écrit en Python et JavaScript. Il permet de modéliser les revenus potentiels d'un site de minage en utilisant des données historiques (depuis 2018) pour des backtests, ou en projetant des revenus futurs basés sur une loi de puissance pour le prix du Bitcoin, les halvings, et la croissance du hashrate global.

Le simulateur s'apparente à de l'optimisation sous contraintes de réseaux électriques. Il génère un fichier HTML interactif (`index.html`) avec des sliders pour ajuster les paramètres (comme la puissance en MW, l'efficacité en J/TH, etc.) et visualiser les résultats en temps réel via des graphiques.

### Modes de fonctionnement
- **Mode simulation (projection non cochée)** : Charge les données d'un site de minage (fichier CSV pour la puissance journalière en MW, hashrate historique et prix BTC) pour backtester les performances depuis 2018. Cela utilise des données réelles pour calculer les revenus cumulés passés.
- **Mode projection (case "projection" cochée)** : Analyse la puissance moyenne du site et projette les revenus futurs sur un nombre d'années défini (par défaut 7 ans). Les projections intègrent une croissance du hashrate, les halvings Bitcoin, et une courbe de loi de puissance pour l'évolution du prix du BTC.

Le script principal `simulateur.py` récupère des données via des API (Blockstream, CoinGecko, Blockchain.info, TradingView), génère des fichiers CSV pour les données historiques et exemples, et produit un fichier HTML embarquant du JavaScript pour l'interactivité.

## Installation

1. Clonez le dépôt :
   ```
   git clone https://github.com/pascalranaora/simulateur-bitcoin.git
   cd simulateur-bitcoin
   ```

2. Installez les dépendances Python (utilisez un environnement virtuel recommandé) :
   ```
   pip install requests pandas tvDatafeed matplotlib
   ```
   Note : Le script utilise des bibliothèques comme `requests`, `pandas`, `tvDatafeed` pour récupérer et traiter les données. Assurez-vous d'avoir une connexion internet pour les API.

3. Exécutez le script pour générer l'interface :
   ```
   python simulateur.py
   ```
   Cela produira `index.html`, des fichiers CSV historiques (`historical_btcprice.csv`, `historical_data_hashrate.csv`), et des exemples (`sample_power.csv`, `Tricastin-1.csv`).

## Utilisation

1. Lancez le script Python :
   ```
   python simulateur.py
   ```

2. Ouvrez `index.html` dans un navigateur web. Vous verrez :
   - Des sliders pour ajuster les paramètres (puissance MW, efficacité J/TH, coût €/MWh, etc.).
   - Des graphiques pour les données historiques (prix BTC, hashrate) et projections (loi de puissance, revenus cumulés).
   - Une section pour charger un fichier CSV personnalisé pour la puissance du site.

3. Activez/désactivez la case "Projection" pour basculer entre les modes.
   - En mode simulation : Utilise les données historiques pour calculer les BTC minés et revenus passés.
   - En mode projection : Projette les revenus futurs basés sur la puissance moyenne et des modèles prédictifs.

Exemple de fichier CSV pour la puissance du site (format : `date,MW`) :
```
date,MW
2018-01-01,40
2018-01-02,45
...
```

## Détails du code : simulateur.py

Le script `simulateur.py` est structuré en fonctions modulaires pour la récupération de données, les calculs, et la génération de l'interface HTML. Voici une explication détaillée du code, section par section.

### Imports et dépendances
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
- **Utilité** : Importe les modules nécessaires pour les requêtes API (`requests`), la manipulation de dates (`datetime`), la génération aléatoire (`random`), le traitement de données (`pandas`), la récupération de données historiques (`tvDatafeed`), et la lecture/écriture CSV (`csv`).

### Fonctions pour récupérer des données en temps réel
1. `get_current_block_height()` :
   - Récupère la hauteur de bloc actuelle via l'API Blockstream.
   - Fallback : 916944 (pour le 29/09/2025).
   - **Détail** : Utilise une requête GET et convertit la réponse en entier. Gère les erreurs avec un print et un fallback.

2. `get_btc_price_eur()` :
   - Récupère le prix BTC en EUR via CoinGecko.
   - Fallback : 96500 EUR (mis à jour pour octobre 2025).
   - **Détail** : Parse le JSON de la réponse et extrait le prix. Affiche le prix en console pour debugging.

3. `get_current_hash_rate_ths()` :
   - Récupère le hashrate actuel en TH/s via Blockchain.info.
   - Fallback : 1.02e9 TH/s (environ 1020 EH/s).
   - **Détail** : Accède au dernier point de données dans le JSON des valeurs.

### Fonctions utilitaires
1. `days_since_genesis(current_date=None)` :
   - Calcule les jours depuis le bloc genesis (03/01/2009).
   - **Détail** : Utilise `date` pour soustraire les dates et retourne un entier.

2. `get_historical_prices()` :
   - Récupère les prix historiques BTC/EUR depuis 2018 via TradingView (`tvDatafeed`).
   - **Détail** : Utilise une boucle de retry (jusqu'à 10 tentatives) pour gérer les erreurs. Resample les données journalières, forward-fill, et sauvegarde en CSV (`historical_btcprice.csv`). Ajoute une colonne `date_integer` pour un format numérique (YYYYMMDD).

3. `get_power_law_points(current_date, exponent=5.6, years_ahead=7)` :
   - Génère des points pour une courbe de loi de puissance (prix BTC ~ jours^exposant).
   - **Détail** : Calcule le coefficient A basé sur le prix actuel, puis génère des points tous les 30 jours pour les années futures. Retourne une liste de points {x: année, y: prix}.

4. `calculate_mined_btc(start_block, current_block)` :
   - Calcule les BTC minés entre deux blocs, en tenant compte des halvings (récompenses : 12.5, 6.25, 3.125 BTC).
   - **Détail** : Divise en périodes de halving et additionne les BTC par bloc pour chaque période.

5. `calculate_opportunity_cost(share=0.03)` :
   - Calcule le coût d'opportunité (BTC minés passés, valeur en EUR) pour une part de marché hypothétique.
   - **Détail** : Utilise `calculate_mined_btc` pour les BTC totaux, applique la part, multiplie par le prix actuel. Récupère aussi des données historiques et points de loi de puissance. Retourne un dictionnaire avec tous les résultats pour l'HTML.

6. `to_integer(dt_time)` :
   - Convertit une date en entier YYYYMMDD.
   - **Détail** : Utilisé pour les dataframes historiques.

7. `get_hash_historical_data_csv()` :
   - Similaire à `get_historical_prices`, mais pour le hashrate (symbole "HRATE").
   - **Détail** : Sauvegarde en `historical_data_hashrate.csv` avec colonne EH/s.

### Fonctions pour générer des données exemples
1. `generate_sample_power_csv()` :
   - Génère un CSV exemple de puissance journalière (80-120 MW aléatoire) de 2018 à 2020.
   - **Détail** : Boucle sur les jours, ajoute du bruit aléatoire, écrit en CSV.

2. `generate_demo_tricastin_mining_power_csv()` :
   - Génère un CSV exemple pour un site "Tricastin-1" (20-60 MW aléatoire) depuis 2018 jusqu'à aujourd'hui.
   - **Détail** : Similaire à ci-dessus, mais avec des bornes différentes.

3. `load_sample_csv(filename)` :
   - Charge un CSV et parse les dates/valeurs en liste de dictionnaires.
   - **Détail** : Gère différents types (ehs pour hashrate, pr pour prix, mw pour puissance). Skippe l'en-tête et gère les erreurs de parsing.

### Fonction principale
`generate_html()` :
- Calcule les résultats via `calculate_opportunity_cost`.
- Génère/charge les CSV exemples et historiques.
- Construit le contenu HTML avec :
  - Sliders (puissance, efficacité, coût énergie, etc.).
  - Sections pour données démo et revenus projetés.
  - **Détail** : Utilise des f-strings pour insérer les données JSONifiées dans l'HTML. Écrit le fichier `index.html`.

### Exécution principale
```python
if __name__ == "__main__":
    generate_html()
```
- Lance la génération de l'HTML lors de l'exécution du script.

## Contributions
Développé par Pascal Ranaora.

## Licence
MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

## Avertissement
Ce simulateur est à des fins éducatives et de modélisation. Les projections sont basées sur des modèles hypothétiques et ne constituent pas un conseil financier. 