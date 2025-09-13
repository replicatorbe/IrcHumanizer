#!/usr/bin/env python3
"""
Outil pour visualiser les statistiques de mémoire du bot
"""

import json
from src.memory_manager import ConversationMemory

def main():
    print("=== Statistiques de mémoire IrcHumanizer ===\n")
    
    memory = ConversationMemory()
    stats = memory.get_stats()
    
    print(f"📊 Résumé général:")
    print(f"  - Total contextes: {stats['total_contexts']}")
    print(f"  - Total messages: {stats['total_messages']}")
    print(f"  - Salons: {stats['channel_contexts']}")
    print(f"  - Conversations privées: {stats['private_contexts']}")
    print(f"  - Taille fichier: {stats['memory_file_size']} bytes\n")
    
    print("📋 Détail des contextes:")
    
    for context_id, messages in memory.conversations.items():
        message_count = len(messages)
        if message_count == 0:
            continue
            
        context_type = "💬 Privé" if context_id.startswith("private:") else "📢 Salon"
        context_name = context_id.split(":", 1)[1]
        
        print(f"  {context_type} '{context_name}': {message_count} messages")
        
        # Afficher les derniers messages pour aperçu
        if message_count > 0:
            last_msg = list(messages)[-1]
            timestamp = last_msg["timestamp"][:16].replace("T", " ")
            sender = last_msg["sender"]
            content = last_msg["message"][:50] + "..." if len(last_msg["message"]) > 50 else last_msg["message"]
            print(f"    Dernier: {timestamp} <{sender}> {content}")
        
        print()
    
    # Analyse des utilisateurs les plus actifs
    print("👥 Utilisateurs les plus actifs:")
    user_counts = {}
    
    for context_id, messages in memory.conversations.items():
        for msg in messages:
            sender = msg["sender"]
            if not msg.get("is_bot", False):  # Ignorer les messages du bot
                user_counts[sender] = user_counts.get(sender, 0) + 1
    
    # Trier par nombre de messages
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for i, (user, count) in enumerate(sorted_users, 1):
        personality = memory.get_user_personality(user)
        casualness = personality.get("casualness_score", 0)
        casual_indicator = "😎" if casualness > 0.3 else "🤓"
        
        print(f"  {i:2d}. {casual_indicator} {user}: {count} messages")
    
    print("\n=== Fin des statistiques ===")

if __name__ == "__main__":
    main()