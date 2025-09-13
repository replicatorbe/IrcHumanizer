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

### Identité IRC automatique
```yaml
irc:
  nickname: "MonHumain"              # Déclenche génération automatique
  auto_personality_identity: true    # Active génération nick/realname
```

- **nickname: "MonHumain"** → Génère automatiquement un prénom cohérent avec le genre (ex: Pierre_25, Sarah69, Marie_Lyon)
- **nickname personnalisé** → Utilise ce nom s'il correspond au genre de la personnalité
- **auto_personality_identity: false** → Utilise les valeurs fixes de la config

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
- **Identité IRC automatique** : nickname/realname basés sur la personnalité
- **Mémoire contextuelle** : se souvient des conversations par salon/privé
- **Géolocalisation crédible** : répond aux questions "qui du XX"
- **Styles d'écriture variés** : SMS, argot, correct, old-school
- **Analyse de personnalité** des utilisateurs pour adapter les réponses
- **Réponses avec fautes** d'orthographe intentionnelles
- **Actions IRC** (/me) selon l'humeur : "* mange un sandwich"
- **Système d'humeur** : good/bad/tired/excited qui influence les réponses
- **Horaires d'activité** : plus/moins actif selon l'heure et le jour
- **Anti-détection** : évite de répondre trop souvent
- **Absences simulées** : "brb", "va chercher un café"
- **Délais adaptatifs** : plus rapide aux heures de pointe
- **Probabilité de réponse** configurable par humeur/activité
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

### Tester les systèmes du bot
```bash
python personality_test.py          # 3 personnalités aléatoires
python test_config_personality.py   # Test avec config personnalisée
python activity_test.py            # Test horaires et anti-détection
```

## Structure

- `main.py` : Point d'entrée principal
- `src/irc_bot.py` : Client IRC avec gestion des connexions
- `src/config.py` : Système de configuration YAML
- `src/human_generator.py` : IA + génération de réponses humaines
- `src/memory_manager.py` : Mémoire contextuelle par salon/utilisateur
- `src/personality.py` : Système de personnalité + humeur
- `src/activity_manager.py` : Horaires d'activité + anti-détection
- `memory_stats.py` : Outil de visualisation des statistiques
- `personality_test.py` : Test et affichage de la personnalité
- `test_config_personality.py` : Test avec configuration personnalisée
- `activity_test.py` : Test des horaires et anti-détection
- `config.personal.example.yaml` : Exemple de config avec personnalité
