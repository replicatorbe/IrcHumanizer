#!/usr/bin/env python3
"""
Test du système d'activité et d'anti-détection
"""

import datetime
from src.activity_manager import ActivityManager, ActivitySettings

def test_activity_manager():
    print("=== Test du gestionnaire d'activité ===\n")
    
    # Test avec settings par défaut
    activity_manager = ActivityManager()
    stats = activity_manager.get_stats()
    
    print("📊 Statistiques actuelles:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n⏰ Niveau d'activité actuel: {activity_manager.get_activity_level():.2f}")
    print(f"🎯 Devrait répondre (prob 0.3): {activity_manager.should_respond(0.3)}")
    
    # Test des délais adaptatifs
    print(f"\n⏱️ Tests de délais adaptatifs:")
    for i in range(5):
        delay = activity_manager.get_adaptive_delay(1.0, 5.0)
        print(f"   Délai #{i+1}: {delay:.1f}s")
    
    # Simuler plusieurs réponses pour tester l'anti-détection
    print(f"\n🛡️ Test anti-détection:")
    print(f"Messages aujourd'hui: {activity_manager.daily_message_count}")
    
    for i in range(10):
        activity_manager.record_response()
        if i % 3 == 0:
            responding_too_much = activity_manager._is_responding_too_much()
            print(f"   Après {i+1} réponses: {'⚠️ TROP' if responding_too_much else '✅ OK'}")
    
    # Test simulation d'absence
    print(f"\n😴 Test simulation d'absence:")
    for i in range(20):
        absence = activity_manager.simulate_random_absence()
        if absence:
            print(f"   Absence simulée: '{absence}'")
            break
    else:
        print("   Aucune absence simulée dans ce test")
    
    # Test des différents moments de la journée
    print(f"\n🕐 Test activité selon l'heure:")
    test_hours = ["08:00", "12:30", "19:30", "02:00"]
    
    for hour_str in test_hours:
        hour, minute = map(int, hour_str.split(':'))
        # Simuler différents moments (approximatif)
        test_time = datetime.datetime.now().replace(hour=hour, minute=minute)
        
        print(f"   {hour_str}: ", end="")
        
        # Test approximatif des horaires
        if 8 <= hour <= 23:
            if 12 <= hour <= 14:
                print("🍽️ Pause déj (activité réduite)")
            elif 19 <= hour <= 22:
                print("🔥 Heure de pointe (très actif)")
            else:
                print("✅ Horaires normaux")
        else:
            print("😴 Hors horaires (inactif)")

def test_custom_settings():
    print(f"\n\n=== Test avec settings personnalisées ===\n")
    
    # Settings personnalisées
    custom_settings = ActivitySettings(
        active_start="09:30",
        active_end="22:00", 
        lunch_probability=0.8,  # 80% de chance d'être absent au déj
        weekend_activity_modifier=0.5,  # 50% d'activité le weekend
        peak_hours=["20:00-21:30"]
    )
    
    activity_manager = ActivityManager(custom_settings)
    stats = activity_manager.get_stats()
    
    print("⚙️ Avec settings personnalisées:")
    print(f"   Horaires: 09:30-22:00")
    print(f"   Absence déj: 80% de chance")
    print(f"   Weekend: 50% d'activité")
    print(f"   Peak hours: 20:00-21:30")
    
    print(f"\n📈 Résultats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_activity_manager()
    test_custom_settings()