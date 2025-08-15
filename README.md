# NEXUS-RSI - Hyperfast Iteration System

## Vue d'ensemble

NEXUS-RSI est un système d'accélération et d'auto-amélioration continue utilisant des frameworks multi-agents (CrewAI, AutoGen, LangChain, AgencySwarm) pour maximiser la vitesse d'itération et l'optimisation automatique.

## Caractéristiques principales

### 1. Automatisation complète
- Frameworks multi-agents intégrés
- Pipeline CI/CD automatisé
- Déploiement et patch automatiques

### 2. Parallélisme maximal
- Jusqu'à 10 agents actifs simultanément
- Traitement par batch
- Analyse distribuée

### 3. Auto-amélioration continue
- Agents critics et meta pour benchmark
- Patch automatique toutes les 15 minutes
- Kill/Keep automatique des modules

### 4. Veille technologique H24
- Scrapers multi-sources (GitHub, ArXiv, Reddit, HackerNews)
- Ingestion et intégration automatiques
- Analyse et catégorisation des découvertes

### 5. Monitoring temps réel
- Dashboard Streamlit interactif
- Métriques de performance
- Alertes automatiques

## Installation rapide

```bash
# 1. Cloner ou créer le dossier
cd C:\Users\%USERNAME%
mkdir NEXUS-RSI
cd NEXUS-RSI

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer le système
python launch_nexus.py
# ou
start.bat
```

## Structure du projet

```
NEXUS-RSI/
├── nexus_core.py           # Système central
├── nexus_dashboard.py       # Dashboard Streamlit
├── launch_nexus.py          # Launcher principal
├── start.bat               # Script de démarrage Windows
├── requirements.txt        # Dépendances Python
├── config/
│   └── nexus_config.json   # Configuration système
├── agents/                 # Agents spécialisés
├── workflows/              # Workflows automatisés
├── scrapers/               # Scrapers multi-sources
│   └── multi_source_scraper.py
├── scripts/
│   └── auto_patcher.py     # Auto-patch intelligent
├── monitoring/             # Monitoring et logs
├── proofs/                 # Logs et preuves
└── .github/
    └── workflows/
        └── nexus_cicd.yml  # Pipeline CI/CD

```

## Configuration

Éditez `config/nexus_config.json` pour personnaliser :

- **Intervalles** : patch (15min), benchmark (60min)
- **Parallélisme** : nombre d'agents actifs
- **Seuils** : kill (0.3), patch (0.7), scale (0.9)
- **Sources** : GitHub, ArXiv, Reddit, HackerNews, Twitter, Discord

## Dashboard

Accédez au dashboard : http://localhost:8501

### Onglets disponibles :
- **Overview** : Vue d'ensemble du système
- **Agents** : État des agents actifs
- **Performance** : Métriques et graphiques
- **Analytics** : Insights et opportunités
- **Logs** : Historique et actions

## Commandes principales

### Lancement
```bash
# Lancement complet
python launch_nexus.py

# Dashboard seul
streamlit run nexus_dashboard.py

# Core seul
python nexus_core.py

# Scraper seul
python scrapers/multi_source_scraper.py
```

### Auto-patch manuel
```bash
python scripts/auto_patcher.py --threshold 0.8
```

## Pipeline CI/CD

Le système inclut un pipeline GitHub Actions pour :
- Tests et benchmarks automatiques
- Auto-patch des modules lents
- Déploiement parallèle
- Monitoring et alertes
- Apprentissage continu

## Métriques de performance

- **Vitesse d'itération** : mesurée en ops/sec
- **Précision** : score de 0 à 1
- **Utilisation mémoire** : en MB
- **Temps de réponse** : en ms

## Routine d'audit

Le système effectue automatiquement :
- Benchmark toutes les heures
- Patch des modules lents
- Kill des modules inactifs
- Archivage des logs dans `/proofs/`

## Résultats attendus

- Vitesse d'itération **explosive**
- Absorption et test de **chaque nouveauté**
- Auto-amélioration **continue**
- Pivots **sans friction**
- Contrôle **total** via dashboard

## Support

Pour toute question ou problème :
- Consultez les logs dans `/proofs/`
- Vérifiez le dashboard de monitoring
- Ajustez la configuration dans `config/nexus_config.json`

---

**Version** : 1.0.0
**Statut** : Production Ready
**Mode** : Auto-amélioration 24/7