#!/usr/bin/env python3
"""
Test de génération d'identité IRC basée sur la personnalité
"""

from src.personality import PersonalityManager
from src.config import Config

class MockConfig:
    def __init__(self):
        self.nickname = "MonHumain"
        self.auto_personality_identity = True

def test_identity_generation():
    print("=== Test de génération d'identité IRC ===\n")
    
    for i in range(5):
        print(f"🎭 Test #{i+1}")
        print("-" * 40)
        
        # Générer une personnalité
        personality_manager = PersonalityManager()
        profile = personality_manager.profile
        
        # Simuler la génération d'identité
        config = MockConfig()
        
        # Générer nickname
        base_name = profile.name
        variations = [
            base_name,
            f"{base_name}_{profile.age}",
            f"{base_name}{profile.location['region']}",
            f"{base_name}_{profile.location['region']}",
        ]
        import random
        nickname = random.choice(variations)
        
        # Générer realname
        city_abbreviations = {
            "Paris": "Paris", "Lyon": "Lyon", "Marseille": "Mars",
            "Toulouse": "Toul", "Nice": "Nice", "Nantes": "Nant",
            "Strasbourg": "Stras", "Montpellier": "Montp", "Bordeaux": "Bdx",
            "Lille": "Lille", "Rennes": "Renn", "Reims": "Reims",
            "Toulon": "Toulon", "Grenoble": "Gren", "Dijon": "Dijon",
            "Angers": "Angers", "Nîmes": "Nimes", "Villeurbanne": "Villeurb",
            "Clermont-Ferrand": "Clermont", "Le Havre": "LH",
            "Bruxelles": "Bxl", "Brussels": "Bxl", "Brüssel": "Bxl",
            "Genève": "Gen", "Geneva": "Gen", "Genf": "Gen",
            "Montréal": "Mtl", "Montreal": "Mtl",
            "Lausanne": "Laus", "Zurich": "Zur", "Bern": "Bern", "Berne": "Bern"
        }
        
        city_abbrev = city_abbreviations.get(profile.location["city"], profile.location["city"][:4])
        realname = f"{profile.age} {profile.gender} {city_abbrev}"
        
        print(f"👤 Personnalité: {profile.name}, {profile.age} ans, {profile.gender}")
        print(f"📍 Lieu: {profile.location['city']} ({profile.location['region']})")
        print(f"🏷️ Nickname IRC: {nickname}")
        print(f"📝 Realname IRC: {realname}")
        print()

def test_config_variations():
    print("=== Test avec différentes configs ===\n")
    
    # Test avec auto_personality_identity = False
    print("🔧 Avec auto_personality_identity = False:")
    print("   Nickname: MonHumain (config)")
    print("   Realname: Un utilisateur normal (config)")
    print()
    
    # Test avec nickname personnalisé
    print("🔧 Avec nickname personnalisé 'Sarah24':")
    print("   Nickname: Sarah24 (gardé de la config)")
    print("   Realname: 24 F Lyon (généré selon personnalité)")
    print()

if __name__ == "__main__":
    test_identity_generation()
    test_config_variations()