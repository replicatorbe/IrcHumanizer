# IrcHumanizer

Un bot IRC qui imite le comportement d'un utilisateur humain avec des fautes de frappe et un style naturel.

## Installation

1. Clonez le repository
2. Installez les dépendances : `pip install -r requirements.txt`
3. Copiez `config.example.yaml` vers `config.yaml`
4. Éditez la configuration
5. Lancez avec `python main.py`

## Configuration

Le fichier `config.yaml` contient tous les paramètres IRC, comportement et personnalité.

### Configuration de base
```bash
cp config.example.yaml config.yaml
nano config.yaml
```

### Personnalité personnalisée (optionnel)
```yaml
personality:
  name: "Sarah"          # Nom du bot
  gender: "F"            # M, F, ou NB
  age: 24                # 16-45 ans
  city: "Lyon"           # Ville française
  region: "69"           # Code département
  humor_level: 0.7       # 0.0-1.0 (niveau d'humour)
  casualness: 0.8        # 0.0-1.0 (décontraction)
  friendliness: 0.9      # 0.0-1.0 (amabilité)
  geek_level: 0.4        # 0.0-1.0 (côté geek)
  writing_styles: ["sms", "argot"]  # Styles préférés
  interests: ["musique", "cinéma", "gaming"]
```

**Si vide ou absent** → personnalité générée aléatoirement

## Fonctionnalités

- **Connexion IRC automatique** avec support SSL
- **Intégration IA ChatGPT** avec fallback vers réponses prédéfinies
- **Personnalité complète** : nom, âge, genre, localisation, style d'écriture
- **Mémoire contextuelle** : se souvient des conversations par salon/privé
- **Géolocalisation crédible** : répond aux questions "qui du XX"
- **Styles d'écriture variés** : SMS, argot, correct, old-school
- **Analyse de personnalité** des utilisateurs pour adapter les réponses
- **Réponses avec fautes** d'orthographe intentionnelles
- **Délais aléatoires** pour simuler la frappe
- **Probabilité de réponse** configurable
- **Sauvegarde automatique** des conversations

## Utilisation

### Avec IA (recommandé)
```bash
export OPENAI_API_KEY="sk-votre-clé-ici"
python main.py
```

### Sans IA (mode démo)
```bash
python main.py
```

### Voir les statistiques de mémoire
```bash
python memory_stats.py
```

### Tester la personnalité du bot
```bash
python personality_test.py          # 3 personnalités aléatoires
python test_config_personality.py   # Test avec config personnalisée
```

## Structure

- `main.py` : Point d'entrée principal
- `src/irc_bot.py` : Client IRC avec gestion des connexions
- `src/config.py` : Système de configuration YAML
- `src/human_generator.py` : IA + génération de réponses humaines
- `src/memory_manager.py` : Mémoire contextuelle par salon/utilisateur
- `src/personality.py` : Système de personnalité complète
- `memory_stats.py` : Outil de visualisation des statistiques
- `personality_test.py` : Test et affichage de la personnalité
- `test_config_personality.py` : Test avec configuration personnalisée
- `config.personal.example.yaml` : Exemple de config avec personnalité
