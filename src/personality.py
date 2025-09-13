import random
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PersonalityProfile:
    """Profil de personnalité complet du bot"""
    
    # Identité de base
    name: str
    gender: str  # "M", "F", "NB"
    age: int
    location: Dict[str, str]  # {"city": "Lyon", "region": "69", "country": "France"}
    
    # Traits de personnalité
    humor_level: float  # 0.0 à 1.0
    casualness: float   # 0.0 à 1.0
    friendliness: float # 0.0 à 1.0
    geek_level: float   # 0.0 à 1.0
    
    # Styles d'écriture
    writing_styles: List[str]  # ["sms", "correct", "argot", "old_school"]
    preferred_emojis: List[str]
    
    # Intérêts et hobbies
    interests: List[str]
    dislikes: List[str]
    
    # Expressions favorites
    expressions: List[str]
    greetings: List[str]

class PersonalityManager:
    """Gestionnaire de personnalité du bot"""
    
    def __init__(self, custom_profile: Optional[PersonalityProfile] = None, config_data: Optional[Dict] = None):
        if custom_profile:
            self.profile = custom_profile
        elif config_data:
            self.profile = self._generate_from_config(config_data)
        else:
            self.profile = self._generate_random_profile()
        
        # Styles d'écriture par niveau
        self.writing_patterns = {
            "sms": {
                "replacements": {
                    "salut": ["slt", "coucou", "yo"],
                    "comment": ["comm", "cmt"],
                    "beaucoup": ["bcp", "bocou"],
                    "quelqu'un": ["qqun", "kelkun"],
                    "quelque chose": ["qqch", "kelke choz"],
                    "pourquoi": ["pk", "pkoi"],
                    "parce que": ["pcq", "pcke"],
                    "aujourd'hui": ["ajd", "aujourd8"],
                    "c'est": ["c", "cé"],
                    "aussi": ["ossi"],
                    "avec": ["ac", "av"],
                    "vraiment": ["vrmt"],
                    "toujours": ["tjrs", "tjs"],
                    "jamais": ["jamé", "jms"],
                    "maintenant": ["mtn"],
                    "peut-être": ["ptet", "ptetre"]
                },
                "shortcuts": ["mdr", "lol", "ptdr", "jsp", "jpp", "brf", "oklm"]
            },
            
            "argot": {
                "replacements": {
                    "bien": ["grave", "ouf"],
                    "cool": ["stylé", "chanmé", "ouf"],
                    "nul": ["pourri", "naze", "bidon"],
                    "super": ["grave", "de ouf", "mortel"],
                    "bizarre": ["chelou", "zarb"],
                    "cher": ["salé"],
                    "fatigué": ["crevé", "naze"],
                    "énervé": ["vénère", "chaud"],
                    "fille": ["meuf", "go"],
                    "garçon": ["mec", "gars"],
                    "ami": ["pote", "reuf"],
                    "maison": ["baraque", "tiek-k"]
                },
                "expressions": ["wesh", "tranquille", "grave", "de ouf", "ça passe"]
            },
            
            "old_school": {
                "replacements": {
                    "lol": ["héhé", "hihi", "ah ah"],
                    "cool": ["chouette", "sympa"],
                    "super": ["génial", "formidable"],
                    "nul": ["pas terrible", "bof bof"],
                    "bizarre": ["étrange", "curieux"]
                },
                "expressions": ["ma foi", "en effet", "tout à fait", "certes"]
            }
        }
    
    def _generate_from_config(self, config_data: Dict) -> PersonalityProfile:
        """Génère une personnalité depuis la configuration YAML"""
        
        # Locations par défaut
        french_locations = [
            {"city": "Paris", "region": "75", "country": "France"},
            {"city": "Lyon", "region": "69", "country": "France"},
            {"city": "Marseille", "region": "13", "country": "France"},
            {"city": "Toulouse", "region": "31", "country": "France"},
            {"city": "Nice", "region": "06", "country": "France"},
            {"city": "Nantes", "region": "44", "country": "France"},
            {"city": "Strasbourg", "region": "67", "country": "France"},
            {"city": "Montpellier", "region": "34", "country": "France"},
            {"city": "Bordeaux", "region": "33", "country": "France"},
            {"city": "Lille", "region": "59", "country": "France"},
            {"city": "Rennes", "region": "35", "country": "France"},
            {"city": "Reims", "region": "51", "country": "France"},
            {"city": "Toulon", "region": "83", "country": "France"},
            {"city": "Grenoble", "region": "38", "country": "France"},
            {"city": "Dijon", "region": "21", "country": "France"},
            {"city": "Angers", "region": "49", "country": "France"},
            {"city": "Nîmes", "region": "30", "country": "France"},
            {"city": "Villeurbanne", "region": "69", "country": "France"},
            {"city": "Clermont-Ferrand", "region": "63", "country": "France"},
            {"city": "Le Havre", "region": "76", "country": "France"}
        ]
        
        # Extraction des valeurs de config avec fallbacks
        gender = config_data.get('gender', '').upper()
        if gender not in ['M', 'F', 'NB']:
            gender = random.choice(['M', 'F', 'NB'])
        
        age = config_data.get('age', 0)
        if age <= 0:
            age = random.randint(16, 45)
        
        # Gestion de la localisation
        config_city = config_data.get('city', '').strip()
        config_region = config_data.get('region', '').strip()
        
        if config_city and config_region:
            location = {"city": config_city, "region": config_region, "country": "France"}
        else:
            location = random.choice(french_locations)
        
        # Noms selon le genre
        if gender == "M":
            names = ["Alex", "Thomas", "Nicolas", "Julien", "Maxime", "Antoine", "Pierre", "Paul", "Louis", "Hugo", "Lucas", "Nathan", "Enzo", "Léo", "Gabriel", "Arthur", "Jules", "Ethan", "Noah", "Tom"]
        elif gender == "F":
            names = ["Emma", "Jade", "Louise", "Alice", "Chloé", "Lina", "Léa", "Manon", "Julia", "Zoé", "Camille", "Sarah", "Eva", "Inès", "Jeanne", "Margot", "Adèle", "Anna", "Rose", "Clara"]
        else:  # NB
            names = ["Alex", "Sam", "Charlie", "Jordan", "Casey", "Morgan", "Taylor", "River", "Sage", "Quinn"]
        
        name = config_data.get('name', '').strip()
        if not name:
            name = random.choice(names)
        
        # Traits de personnalité
        humor_level = float(config_data.get('humor_level', 0))
        if humor_level <= 0:
            humor_level = random.uniform(0.3, 0.9)
        
        casualness = float(config_data.get('casualness', 0))
        if casualness <= 0:
            casualness = random.uniform(0.4, 1.0)
        
        friendliness = float(config_data.get('friendliness', 0))
        if friendliness <= 0:
            friendliness = random.uniform(0.5, 0.9)
        
        geek_level = float(config_data.get('geek_level', 0))
        if geek_level <= 0:
            geek_level = random.uniform(0.2, 0.8)
        
        # Styles d'écriture
        writing_styles = config_data.get('writing_styles', [])
        if not writing_styles:
            writing_styles = random.sample(["sms", "correct", "argot", "old_school"], k=random.randint(1, 3))
        
        # Intérêts
        interests = config_data.get('interests', [])
        if not interests:
            interests_pool = [
                "jeux vidéo", "cinéma", "musique", "sport", "lecture", "cuisine", "voyages", 
                "photo", "programmation", "manga", "anime", "séries", "bd", "dessin",
                "guitare", "piano", "foot", "basket", "tennis", "natation", "randonnée",
                "politique", "sciences", "histoire", "philo", "art", "mode", "déco"
            ]
            interests = random.sample(interests_pool, k=random.randint(3, 8))
        
        return PersonalityProfile(
            name=name,
            gender=gender,
            age=age,
            location=location,
            
            humor_level=humor_level,
            casualness=casualness,
            friendliness=friendliness,
            geek_level=geek_level,
            
            writing_styles=writing_styles,
            preferred_emojis=["😂", "😊", "🙄", "👍", "🤔", "😅", "🥰", "😎", "🔥", "💯"],
            
            interests=interests,
            dislikes=["spam", "drama", "politique extrême", "trolls"],
            
            expressions=[
                "ah ouais", "c'est clair", "grave", "tout à fait", "exactement",
                "bah écoute", "en même temps", "du coup", "après bon", "n'empêche que"
            ],
            greetings=[
                "salut", "coucou", "yo", "hello", "re", "slt", "bonsoir", "bjr"
            ]
        )
    
    def _generate_random_profile(self) -> PersonalityProfile:
        """Génère une personnalité aléatoire crédible"""
        
        # Villes françaises avec codes départements
        french_locations = [
            {"city": "Paris", "region": "75", "country": "France"},
            {"city": "Lyon", "region": "69", "country": "France"},
            {"city": "Marseille", "region": "13", "country": "France"},
            {"city": "Toulouse", "region": "31", "country": "France"},
            {"city": "Nice", "region": "06", "country": "France"},
            {"city": "Nantes", "region": "44", "country": "France"},
            {"city": "Strasbourg", "region": "67", "country": "France"},
            {"city": "Montpellier", "region": "34", "country": "France"},
            {"city": "Bordeaux", "region": "33", "country": "France"},
            {"city": "Lille", "region": "59", "country": "France"},
            {"city": "Rennes", "region": "35", "country": "France"},
            {"city": "Reims", "region": "51", "country": "France"},
            {"city": "Toulon", "region": "83", "country": "France"},
            {"city": "Grenoble", "region": "38", "country": "France"},
            {"city": "Dijon", "region": "21", "country": "France"},
            {"city": "Angers", "region": "49", "country": "France"},
            {"city": "Nîmes", "region": "30", "country": "France"},
            {"city": "Villeurbanne", "region": "69", "country": "France"},
            {"city": "Clermont-Ferrand", "region": "63", "country": "France"},
            {"city": "Le Havre", "region": "76", "country": "France"}
        ]
        
        gender = random.choice(["M", "F", "NB"])
        
        # Noms selon le genre
        if gender == "M":
            names = ["Alex", "Thomas", "Nicolas", "Julien", "Maxime", "Antoine", "Pierre", "Paul", "Louis", "Hugo", "Lucas", "Nathan", "Enzo", "Léo", "Gabriel", "Arthur", "Jules", "Ethan", "Noah", "Tom"]
        elif gender == "F":
            names = ["Emma", "Jade", "Louise", "Alice", "Chloé", "Lina", "Léa", "Manon", "Julia", "Zoé", "Camille", "Sarah", "Eva", "Inès", "Jeanne", "Margot", "Adèle", "Anna", "Rose", "Clara"]
        else:  # NB
            names = ["Alex", "Sam", "Charlie", "Jordan", "Casey", "Morgan", "Taylor", "River", "Sage", "Quinn"]
        
        interests_pool = [
            "jeux vidéo", "cinéma", "musique", "sport", "lecture", "cuisine", "voyages", 
            "photo", "programmation", "manga", "anime", "séries", "bd", "dessin",
            "guitare", "piano", "foot", "basket", "tennis", "natation", "randonnée",
            "politique", "sciences", "histoire", "philo", "art", "mode", "déco"
        ]
        
        return PersonalityProfile(
            name=random.choice(names),
            gender=gender,
            age=random.randint(16, 45),
            location=random.choice(french_locations),
            
            humor_level=random.uniform(0.3, 0.9),
            casualness=random.uniform(0.4, 1.0),
            friendliness=random.uniform(0.5, 0.9),
            geek_level=random.uniform(0.2, 0.8),
            
            writing_styles=random.sample(["sms", "correct", "argot", "old_school"], k=random.randint(1, 3)),
            preferred_emojis=["😂", "😊", "🙄", "👍", "🤔", "😅", "🥰", "😎", "🔥", "💯"],
            
            interests=random.sample(interests_pool, k=random.randint(3, 8)),
            dislikes=["spam", "drama", "politique extrême", "trolls"],
            
            expressions=[
                "ah ouais", "c'est clair", "grave", "tout à fait", "exactement",
                "bah écoute", "en même temps", "du coup", "après bon", "n'empêche que"
            ],
            greetings=[
                "salut", "coucou", "yo", "hello", "re", "slt", "bonsoir", "bjr"
            ]
        )
    
    def get_personality_context(self) -> str:
        """Génère le contexte de personnalité pour l'IA"""
        p = self.profile
        
        gender_text = {
            "M": "Tu es un homme",
            "F": "Tu es une femme", 
            "NB": "Tu es non-binaire"
        }[p.gender]
        
        context = f"""{gender_text} de {p.age} ans qui s'appelle {p.name}.
Tu habites à {p.location['city']} ({p.location['region']}).

Traits de personnalité:
- Niveau d'humour: {int(p.humor_level * 10)}/10
- Décontraction: {int(p.casualness * 10)}/10
- Amabilité: {int(p.friendliness * 10)}/10
- Côté geek: {int(p.geek_level * 10)}/10

Tes centres d'intérêt: {', '.join(p.interests[:5])}
Tu n'aimes pas: {', '.join(p.dislikes)}

Style d'écriture préféré: {', '.join(p.writing_styles)}
"""
        return context
    
    def adapt_response_style(self, text: str) -> str:
        """Adapte le texte selon le style de personnalité"""
        result = text
        
        # Appliquer les styles dans l'ordre de préférence
        for style in self.profile.writing_styles:
            if random.random() < 0.4:  # 40% de chance d'appliquer le style
                result = self._apply_writing_style(result, style)
        
        # Ajouter parfois un emoji selon la personnalité
        if random.random() < (self.profile.humor_level * 0.3):
            emoji = random.choice(self.profile.preferred_emojis)
            if random.random() < 0.5:
                result = f"{result} {emoji}"
            else:
                result = f"{emoji} {result}"
        
        return result
    
    def _apply_writing_style(self, text: str, style: str) -> str:
        """Applique un style d'écriture spécifique"""
        if style not in self.writing_patterns:
            return text
        
        pattern = self.writing_patterns[style]
        result = text.lower()
        
        # Remplacements de mots
        if "replacements" in pattern:
            for original, alternatives in pattern["replacements"].items():
                if original in result:
                    if random.random() < 0.6:  # 60% de chance de remplacer
                        replacement = random.choice(alternatives)
                        result = result.replace(original, replacement)
        
        # Ajouter des expressions du style
        if "expressions" in pattern and random.random() < 0.2:
            expression = random.choice(pattern["expressions"])
            if random.random() < 0.5:
                result = f"{expression} {result}"
            else:
                result = f"{result} {expression}"
        
        # Ajouter des raccourcis SMS
        if style == "sms" and "shortcuts" in pattern and random.random() < 0.3:
            shortcut = random.choice(pattern["shortcuts"])
            result = f"{result} {shortcut}"
        
        return result
    
    def should_respond_to_location_question(self, message: str) -> Optional[str]:
        """Répond aux questions de géolocalisation"""
        message_lower = message.lower()
        location_keywords = [
            "qui du", "quelqu'un du", "qui de", "qui est du", "qui habite",
            "d'où tu viens", "tu es d'où", "région", "département", "ville"
        ]
        
        if any(keyword in message_lower for keyword in location_keywords):
            p = self.profile
            
            # Extraire le code de département si mentionné
            region_mentioned = None
            words = message_lower.split()
            for word in words:
                if word.isdigit() and len(word) in [2, 3]:
                    region_mentioned = word.zfill(2)  # Normaliser sur 2 chiffres
                    break
            
            # Répondre si c'est notre région ou question générale
            if region_mentioned == p.location["region"] or not region_mentioned:
                responses = [
                    f"moi je suis de {p.location['city']}",
                    f"par ici, {p.location['city']} represent !",
                    f"{p.location['city']} dans le {p.location['region']}",
                    f"yo {p.location['city']} ici",
                    f"présent, {p.location['city']} ftw"
                ]
                return random.choice(responses)
        
        return None
    
    def get_age_appropriate_response(self, message: str) -> Optional[str]:
        """Génère des réponses appropriées à l'âge"""
        if "âge" in message.lower() or "age" in message.lower():
            age = self.profile.age
            if age < 20:
                return f"j'ai {age} ans jsp pk"
            elif age < 30:
                return f"{age} ans, dans la force de l'age mdr"
            else:
                return f"j'ai {age} ans, ça passe encore"
        return None