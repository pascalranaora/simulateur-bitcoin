# Simulateur de Minage Bitcoin

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Licence](https://img.shields.io/badge/Licence-MIT-green)](LICENSE)

## Description

Ce repository contient un simulateur simple de minage Bitcoin écrit en Python. Il permet de modéliser les revenus potentiels d'un site de minage en tenant compte des données historiques (backtesting depuis 2018) et des projections futures basées sur une loi de puissance pour le prix du Bitcoin, les halvings et la croissance du hashrate global.

### Fonctionnalités Principales
- **Mode Simulation (Backtesting)** : Charge les données historiques d'un site de minage (puissance en MW, hashrate global, prix BTC) depuis 2018 pour évaluer les revenus passés et cumulés.
- **Mode Projection** : Utilise la puissance moyenne du site pour projeter les revenus futurs sur un nombre d'années défini (par défaut 7 ans, ajustable via sliders dans l'interface HTML générée). Intègre une courbe de loi de puissance pour le prix BTC, avec halvings (2028) et croissance du hashrate.
- Génération d'un fichier HTML interactif (`index.html`) avec sliders pour ajuster les paramètres en temps réel (part de marché, puissance, etc.).
- Données historiques récupérées via TradingView (prix BTC et hashrate) et APIs (CoinGecko pour prix actuel, Blockchain.info pour hashrate actuel).
- Fichiers CSV générés pour les données historiques et exemples de puissance de site.

Le simulateur est conçu pour être éducatif et analytique, en modélisant un scénario hypothétique (ex. : 3% de part de marché pour la France).

## Prérequis

- Python 3.8 ou supérieur.
- Bibliothèques requises : `requests`, `pandas`, `tvDatafeed` (pour les données TradingView).

## Installation

1. Clonez le repository :
   ```
   git clone https://github.com/pascalranaora/simulateur-bitcoin.git
   cd simulateur-bitcoin
   ```

2. Installez les dépendances :
   ```
   pip install requests pandas tvdatafeed
   ```

3. Exécutez le script principal pour générer les fichiers :
   ```
   python simulateur.py
   ```

Cela générera :
- `historical_btcprice.csv` : Prix historiques BTC en EUR (depuis 2018).
- `historical_data_hashrate.csv` : Hashrate historique en EH/s.
- `sample_power.csv` : Exemple de données de puissance d'un site (80-120 MW).
- `Tricastin-1.csv` : Exemple spécifique pour le site Tricastin-1 (20-60 MW).
- `index.html` : Interface web interactive pour le simulateur.

Ouvrez `index.html` dans un navigateur pour interagir avec les sliders et visualiser les graphiques.

## Utilisation

- **Lancement** : Exécutez `python simulateur.py` pour régénérer les données et l'HTML.
- **Modes** :
  - **Simulation (case "projection" non cochée)** : Backtesting sur données historiques chargées depuis 2018. Utilise les CSV générés pour calculer les revenus passés basés sur la puissance réelle/variable du site.
  - **Projection (case "projection" cochée)** : Projection future sur X années (slider par défaut à 7 ans). Calcule les revenus en utilisant la puissance moyenne du site, une loi de puissance pour le prix BTC (exposant par défaut 5.6), et intègre les halvings futurs.
- **Paramètres ajustables** (via sliders dans l'HTML) :
  - Part de marché (ex. : 0.03 pour 3%).
  - Puissance du site (MW).
  - Nombre d'années de projection.
  - Exposant de la loi de puissance.
- **Sorties** : Graphiques de revenus cumulés (M€), courbes de prix BTC historiques et projetés, et métriques comme le total BTC miné depuis 2018.

**Note** : Les données sont mises à jour en temps réel via APIs (prix actuel, hashrate). En cas d'erreur réseau, des valeurs de fallback sont utilisées (ex. : prix BTC à 96 500 €, hashrate à 1 020 EH/s).

## Détails Techniques : Analyse du Code `simulateur.py`

Le fichier `simulateur.py` est le cœur du simulateur. Il s'agit d'un script Python qui récupère des données en temps réel/historiques, effectue des calculs mathématiques (loi de puissance, halvings), génère des fichiers CSV pour persistance, et produit une interface HTML statique mais interactive (via JavaScript embarqué pour les sliders).

### Structure Générale
- **Imports** : 
  - `requests` et `json` : Pour les appels API (CoinGecko, Blockchain.info).
  - `datetime`, `time`, `random` : Gestion des dates, délais, et génération de données aléatoires.
  - `pandas` et `tvDatafeed` : Récupération et traitement des données historiques de TradingView.
  - `csv` : Génération/lecture de fichiers CSV.

- **Fonctions Utilitaires** :
  - `get_current_block_height()` : Récupère la hauteur de bloc actuelle via Blockstream API. Fallback : 916 944 (29/09/2025). Utilisé pour calculer les BTC minés.
  - `get_btc_price_eur()` : Prix BTC actuel en EUR via CoinGecko. Affiche le prix et utilise un fallback à 96 500 €. Appelée en temps réel pour les projections.
  - `get_current_hash_rate_ths()` : Hashrate actuel en TH/s via Blockchain.info. Fallback : 1 020 000 000 TH/s (≈1 020 EH/s). Essentiel pour normaliser la part de puissance du site.
  - `days_since_genesis(current_date=None)` : Calcule les jours écoulés depuis le bloc genesis (03/01/2009). Utilisé comme base temporelle pour la loi de puissance.
  - `to_integer(dt_time)` : Convertit une date en entier (AAAAMMJJ) pour les CSV.

### Chargement des Données Historiques (Mode Simulation)
- `get_historical_prices()` : 
  - Récupère les prix quotidiens BTC/EUR depuis 2018 via TradingView (`TvDatafeed` avec symbole "BTCEUR" sur COINBASE, intervalle daily, 5000 barres).
  - Resample pour combler les trous (forward fill), filtre depuis 01/01/2018.
  - Sauvegarde en `historical_btcprice.csv` (colonnes : `date`, `price`).
  - Gestion d'erreurs : Retry jusqu'à 10 fois en cas d'échec TvDatafeed.
  
- `get_hash_historical_data_csv()` : 
  - Similaire, mais pour le hashrate (`HRATE` sur BCHAIN).
  - Sauvegarde en `historical_data_hashrate.csv` (colonnes : `date`, `EH/s` = close / 1e6).
  - Utilisé pour backtester la part de puissance du site vs. réseau global depuis 2018.

- `load_sample_csv(filename)` : Lit un CSV et retourne une liste de dicts (ex. : `{'date': 'YYYY-MM-DD', 'mw': 80.0}` pour puissance, ou `ehs`/`pr` pour hashrate/prix).

- Génération d'exemples :
  - `generate_sample_power_csv()` : Crée `sample_power.csv` avec puissance aléatoire 80-120 MW/jour depuis 2018.
  - `generate_demo_tricastin_mining_power_csv()` : Spécifique pour Tricastin-1, puissance 20-60 MW/jour (moyenne 40 MW).

Ces fonctions chargent les données pour le backtesting : en mode simulation, les revenus sont calculés en itérant sur les dates historiques, en utilisant la puissance du site ce jour-là multipliée par la part de hashrate, le prix BTC, et les récompenses de bloc (ajustées pour halvings).

### Projections Futures (Mode Projection)
- `get_power_law_points(current_date, exponent=5.6, years_ahead=7)` :
  - Calcule des points pour la courbe de prix BTC future : `price = A * (days_since_genesis ** exponent)`.
  - `A` est calibré sur le prix actuel pour ancrer la courbe.
  - Génère des points tous les 30 jours sur `years_ahead` années (ex. : 2026-2032).
  - Retourne liste de dicts `{'x': year, 'y': price}` pour le graphique.

- `calculate_mined_btc(start_block, current_block)` :
  - Calcule le total BTC minés entre `start_block` (≈499 500 pour 2018) et `current_block`.
  - Segmente par ères de halving :
    - Période 1 (blocs 499 500-630 000) : 12.5 BTC/bloc.
    - Période 2 (630 000-840 000) : 6.25 BTC/bloc.
    - Période 3 (840 000+) : 3.125 BTC/bloc.
  - Pour projections : Extrapole les blocs futurs en assumant un rythme constant, ajusté pour halving 2028 (récompense à 1.5625 BTC).

- `calculate_opportunity_cost(share=0.03)` : Fonction centrale.
  - Calcule les métriques passées : BTC minés depuis 2018 * part * prix actuel = valeur en €.
  - Charge les historiques via les CSV.
  - Calcule puissance totale réseau (hashrate * efficacité 30 J/TH).
  - Génère points de projection via `get_power_law_points`.
  - Retourne un dict avec toutes les données pour l'HTML (revenus cumulés, graphiques, etc.).

### Génération de l'Interface (HTML)
- `generate_html()` :
  - Appelle `calculate_opportunity_cost()` pour les données de base.
  - Charge les samples CSV.
  - Génère un HTML avec :
    - Titre et logo (INBI).
    - Sliders JavaScript pour paramètres (part, puissance, années, exposant).
    - Case à cocher "projection" pour basculer les modes.
    - Graphiques (revenus cumulés en M€, courbe prix BTC historique/projetée).
    - Mises à jour en temps réel via appels aux fonctions (prix/hashrate actuels).
  - Sauvegarde en `index.html`.

### Exécution Principale
- `if __name__ == "__main__": generate_html()` : Lance tout au démarrage.

### Limites et Améliorations
- **Dépendances Externes** : APIs et TradingView peuvent échouer ; fallbacks fournis mais à updater.
- **Hypothèses** : Efficacité fixe (30 J/TH), pas de frais d'électricité, part de marché fixe. Ajoutez des sliders pour plus de réalisme.
- **Améliorations** : Intégrez Streamlit pour une UI Python native, ou ajoutez des scénarios personnalisés via CSV upload.
- **Données Sensibles** : Le simulateur utilise des estimations ; pas pour investissement réel.

## Contribution

Les contributions sont les bienvenues ! Forkez le repo, créez une branche, et soumettez une Pull Request.

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteurs

- [Pascal Ranaora](https://github.com/pascalranaora)

---

*Ce README est un exemple générique basé sur la structure du code. Adaptez-le selon vos besoins spécifiques.*
