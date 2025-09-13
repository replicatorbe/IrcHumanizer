#!/usr/bin/env python3
"""
Test et affichage de la personnalité du bot
"""

from src.personality import PersonalityManager, PersonalityProfile

def main():
    print("=== Test du système de personnalité IrcHumanizer ===\n")
    
    # Générer 3 personnalités aléatoires
    for i in range(3):
        print(f"🎭 Personnalité #{i+1}")
        print("=" * 50)
        
        personality = PersonalityManager()
        profile = personality.profile
        
        print(f"👤 Identité: {profile.name}, {profile.gender}, {profile.age} ans")
        print(f"📍 Localisation: {profile.location['city']} ({profile.location['region']})")
        print(f"🎨 Traits:")
        print(f"   - Humour: {int(profile.humor_level * 10)}/10")
        print(f"   - Décontraction: {int(profile.casualness * 10)}/10") 
        print(f"   - Amabilité: {int(profile.friendliness * 10)}/10")
        print(f"   - Côté geek: {int(profile.geek_level * 10)}/10")
        print(f"✍️ Styles: {', '.join(profile.writing_styles)}")
        print(f"🎯 Intérêts: {', '.join(profile.interests[:5])}...")
        print(f"😊 Emojis préférés: {' '.join(profile.preferred_emojis[:5])}")
        
        # Test d'adaptation de style
        test_messages = [
            "salut comment ça va ?",
            "tu es d'où toi ?",
            "qu'est-ce que tu penses de ça ?",
            "mdr c'est trop drôle"
        ]
        
        print(f"\n💬 Exemples de style d'écriture:")
        for msg in test_messages:
            adapted = personality.adapt_response_style(msg)
            print(f"   '{msg}' → '{adapted}'")
        
        # Test réponses géolocalisation
        geo_tests = [
            "qui du 69",
            f"quelqu'un du {profile.location['region']}",
            "qui est de Lyon"
        ]
        
        print(f"\n🗺️ Réponses géolocalisées:")
        for test in geo_tests:
            response = personality.should_respond_to_location_question(test)
            if response:
                print(f"   '{test}' → '{response}'")
        
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()