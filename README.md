# IrcHumanizer

Un bot IRC qui imite le comportement d'un utilisateur humain avec des fautes de frappe et un style naturel.

## Installation

1. Clonez le repository
2. Installez les dépendances : `pip install -r requirements.txt`
3. Copiez `config.example.yaml` vers `config.yaml`
4. Éditez la configuration
5. Lancez avec `python main.py`

## Configuration

Le fichier `config.yaml` contient tous les paramètres IRC et de comportement.

## Fonctionnalités

- Connexion IRC automatique
- Réponses avec fautes d'orthographe intentionnelles
- Délais aléatoires pour simuler la frappe
- Probabilité de réponse configurable

## Structure

- `main.py` : Point d'entrée
- `src/irc_bot.py` : Client IRC
- `src/config.py` : Configuration
- `src/human_generator.py` : Génération de réponses humaines
