#!/usr/bin/env python3
"""
Test de la personnalité avec configuration personnalisée
"""

from src.config import Config
from src.personality import PersonalityManager

def test_custom_personality():
    print("=== Test personnalité depuis configuration ===\n")
    
    # Test avec config personnalisée
    custom_config = {
        "name": "Alex",
        "gender": "M",
        "age": 28,
        "city": "Paris",
        "region": "75",
        "humor_level": 0.8,
        "casualness": 0.9,
        "friendliness": 0.7,
        "geek_level": 0.6,
        "writing_styles": ["sms", "argot"],
        "interests": ["gaming", "musique", "prog", "cinema"]
    }
    
    print("🎭 Configuration personnalisée:")
    for key, value in custom_config.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*50)
    
    personality = PersonalityManager(config_data=custom_config)
    profile = personality.profile
    
    print(f"🎯 Personnalité générée:")
    print(f"   👤 {profile.name}, {profile.gender}, {profile.age} ans")
    print(f"   📍 {profile.location['city']} ({profile.location['region']})")
    print(f"   🎨 Humour: {int(profile.humor_level * 10)}/10")
    print(f"   🎨 Décontraction: {int(profile.casualness * 10)}/10")
    print(f"   🎨 Amabilité: {int(profile.friendliness * 10)}/10")
    print(f"   🎨 Geek: {int(profile.geek_level * 10)}/10")
    print(f"   ✍️ Styles: {profile.writing_styles}")
    print(f"   🎯 Intérêts: {profile.interests}")
    
    # Test réponses
    print(f"\n💬 Tests de réponses:")
    geo_response = personality.should_respond_to_location_question("qui du 75")
    if geo_response:
        print(f"   'qui du 75' → '{geo_response}'")
    
    age_response = personality.get_age_appropriate_response("quel âge tu as ?")
    if age_response:
        print(f"   'quel âge tu as ?' → '{age_response}'")
    
    # Test adaptation de style
    test_message = "salut comment ça va aujourd'hui ?"
    adapted = personality.adapt_response_style(test_message)
    print(f"   Style adapté: '{test_message}' → '{adapted}'")

def test_partial_config():
    print(f"\n\n=== Test configuration partielle ===\n")
    
    # Config partielle - le reste sera aléatoire
    partial_config = {
        "name": "Julie",
        "city": "Marseille",
        "region": "13",
        "casualness": 0.9
    }
    
    print("🔧 Configuration partielle:")
    for key, value in partial_config.items():
        print(f"   {key}: {value}")
    
    personality = PersonalityManager(config_data=partial_config)
    profile = personality.profile
    
    print(f"\n✨ Personnalité complétée automatiquement:")
    print(f"   👤 {profile.name}, {profile.gender}, {profile.age} ans")
    print(f"   📍 {profile.location['city']} ({profile.location['region']})")
    print(f"   🎨 Casualness configurée: {int(profile.casualness * 10)}/10")
    print(f"   🎨 Autres traits aléatoires: H{int(profile.humor_level * 10)} A{int(profile.friendliness * 10)} G{int(profile.geek_level * 10)}")
    print(f"   ✍️ Styles aléatoires: {profile.writing_styles}")

if __name__ == "__main__":
    test_custom_personality()
    test_partial_config()