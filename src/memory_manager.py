import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import logging

class ConversationMemory:
    """Gestionnaire de mémoire conversationnelle par contexte"""
    
    def __init__(self, max_messages_per_context: int = 50, memory_file: str = "bot_memory.json"):
        self.logger = logging.getLogger(__name__)
        self.max_messages = max_messages_per_context
        self.memory_file = memory_file
        
        # Structure: {context_id: deque([message_dict, ...])}
        # context_id = "channel:#francophonie" ou "private:username"
        self.conversations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.max_messages))
        
        # Mémoire des utilisateurs: {username: {infos personnelles}}
        self.users_info: Dict[str, Dict] = defaultdict(dict)
        
        # Charger la mémoire existante
        self.load_memory()
    
    def _get_context_id(self, target: str, is_private: bool = False) -> str:
        """Génère un ID de contexte unique"""
        if is_private:
            return f"private:{target}"
        else:
            return f"channel:{target}"
    
    def add_message(self, target: str, sender: str, message: str, is_private: bool = False, is_bot: bool = False):
        """Ajoute un message à la mémoire du contexte"""
        context_id = self._get_context_id(target, is_private)
        
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "message": message,
            "is_bot": is_bot
        }
        
        self.conversations[context_id].append(message_data)
        
        # Extraire infos personnelles si ce n'est pas le bot
        if not is_bot and sender != "System":
            self._extract_user_info(sender, message)
        
        # Sauvegarder périodiquement
        if len(self.conversations[context_id]) % 10 == 0:
            self.save_memory()
    
    def get_context_history(self, target: str, is_private: bool = False, limit: int = 10) -> List[Dict]:
        """Récupère l'historique d'un contexte"""
        context_id = self._get_context_id(target, is_private)
        messages = list(self.conversations[context_id])
        
        # Retourner les derniers messages
        return messages[-limit:] if messages else []
    
    def get_conversation_with_user(self, username: str, limit: int = 10) -> List[Dict]:
        """Récupère l'historique privé avec un utilisateur spécifique"""
        return self.get_context_history(username, is_private=True, limit=limit)
    
    def format_history_for_ai(self, target: str, is_private: bool = False, limit: int = 8) -> str:
        """Formate l'historique pour l'envoyer à l'IA"""
        history = self.get_context_history(target, is_private, limit)
        
        if not history:
            return ""
        
        formatted_lines = []
        context_type = "conversation privée" if is_private else f"salon {target}"
        formatted_lines.append(f"[Contexte: {context_type}]")
        
        for msg in history:
            sender = msg["sender"]
            content = msg["message"]
            timestamp = datetime.fromisoformat(msg["timestamp"])
            
            # Afficher seulement l'heure pour plus de concision
            time_str = timestamp.strftime("%H:%M")
            formatted_lines.append(f"{time_str} <{sender}> {content}")
        
        return "\n".join(formatted_lines)
    
    def get_user_personality(self, username: str) -> Dict[str, any]:
        """Analyse la personnalité d'un utilisateur basée sur ses messages"""
        # Récupérer tous les messages de cet utilisateur dans tous les contextes
        user_messages = []
        
        for context_id, messages in self.conversations.items():
            for msg in messages:
                if msg["sender"] == username and not msg["is_bot"]:
                    user_messages.append(msg["message"])
        
        if not user_messages:
            return {}
        
        # Analyse basique
        total_messages = len(user_messages)
        avg_length = sum(len(msg) for msg in user_messages) / total_messages
        
        # Détection de style
        casual_indicators = ["mdr", "lol", "ptdr", "xD", "^^", ":)", ":(", "jsp", "bcp"]
        casual_count = sum(1 for msg in user_messages 
                          for indicator in casual_indicators 
                          if indicator in msg.lower())
        
        questions_count = sum(1 for msg in user_messages if "?" in msg)
        
        return {
            "total_messages": total_messages,
            "avg_message_length": avg_length,
            "casualness_score": casual_count / total_messages if total_messages > 0 else 0,
            "question_ratio": questions_count / total_messages if total_messages > 0 else 0,
            "sample_messages": user_messages[-3:] if user_messages else []
        }
    
    def _extract_user_info(self, username: str, message: str):
        """Extrait automatiquement des infos personnelles des messages"""
        message_lower = message.lower()
        
        # Extraction de prénom
        if not self.users_info[username].get("first_name"):
            # Patterns: "je m'appelle X", "mon nom c'est X", "je suis X"
            import re
            name_patterns = [
                r"je m'appelle (\w+)",
                r"mon nom c'est (\w+)",  
                r"je suis (\w+)",
                r"moi c'est (\w+)",
                r"appelez-moi (\w+)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    name = match.group(1).capitalize()
                    # Éviter les mots communs
                    common_words = {"bien", "là", "ici", "pas", "très", "super", "content", "triste"}
                    if name.lower() not in common_words and len(name) > 2:
                        self.users_info[username]["first_name"] = name
                        self.users_info[username]["name_mentioned_at"] = datetime.now().isoformat()
                        break
        
        # Extraction d'âge
        if not self.users_info[username].get("age"):
            age_patterns = [
                r"j'ai (\d{1,2}) ans",
                r"(\d{1,2}) ans",
                r"j'ai (\d{1,2})a",  # j'ai 25a
            ]
            
            for pattern in age_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    age = int(match.group(1))
                    if 13 <= age <= 99:  # Age raisonnable
                        self.users_info[username]["age"] = age
                        self.users_info[username]["age_mentioned_at"] = datetime.now().isoformat()
                        break
        
        # Extraction de ville/région
        if not self.users_info[username].get("location"):
            # Villes françaises communes
            french_cities = [
                "paris", "lyon", "marseille", "toulouse", "nice", "nantes", 
                "strasbourg", "montpellier", "bordeaux", "lille", "rennes",
                "reims", "toulon", "grenoble", "dijon", "angers", "nîmes",
                "clermont", "aix", "brest", "tours", "limoges", "besançon",
                "metz", "perpignan", "orléans", "mulhouse", "caen", "boulogne",
                "rouen", "nancy", "saint-étienne", "le havre", "avignon"
            ]
            
            location_patterns = [
                r"je suis de (\w+)",
                r"j'habite à (\w+)", 
                r"je vis à (\w+)",
                r"j'viens de (\w+)",
                r"de (\w+)",
                r"à (\w+)"
            ]
            
            for city in french_cities:
                if city in message_lower:
                    # Vérifier le contexte avec patterns
                    for pattern in location_patterns:
                        if re.search(pattern.replace(r"(\w+)", city), message_lower):
                            self.users_info[username]["location"] = city.capitalize()
                            self.users_info[username]["location_mentioned_at"] = datetime.now().isoformat()
                            return
        
        # Extraction d'intérêts/hobbies
        interests_keywords = {
            "gaming": ["jeu", "game", "gaming", "console", "pc", "ps5", "xbox", "steam", "valorant", "lol", "cs"],
            "music": ["musique", "music", "écoute", "concert", "groupe", "album", "chanson", "spotify"],
            "movies": ["film", "movie", "cinéma", "netflix", "serie", "série", "regarder"],
            "sport": ["sport", "foot", "football", "tennis", "basket", "gym", "course", "vélo"],
            "tech": ["tech", "code", "dev", "programmation", "ordi", "pc", "smartphone"],
            "travel": ["voyage", "trip", "vacances", "pays", "avion", "hotel"],
            "food": ["bouffe", "restaurant", "cuisine", "manger", "plat", "recette"]
        }
        
        if "interests" not in self.users_info[username]:
            self.users_info[username]["interests"] = []
            
        for interest, keywords in interests_keywords.items():
            if interest not in self.users_info[username]["interests"]:
                for keyword in keywords:
                    if keyword in message_lower:
                        self.users_info[username]["interests"].append(interest)
                        break
    
    def get_user_info(self, username: str) -> Dict[str, any]:
        """Récupère les infos connues sur un utilisateur"""
        return dict(self.users_info.get(username, {}))
    
    def get_friendly_greeting(self, username: str) -> Optional[str]:
        """Génère un salut personnalisé selon les infos de l'utilisateur"""
        info = self.users_info.get(username, {})
        
        if not info:
            return None
            
        greetings = []
        
        # Salut avec prénom
        if info.get("first_name"):
            name = info["first_name"]
            greetings.extend([
                f"Salut {name} !",
                f"Hey {name} !",
                f"Hello {name}",
                f"Coucou {name}",
                f"Yo {name} !"
            ])
        
        # Référence aux intérêts
        if info.get("interests"):
            interests = info["interests"]
            if "gaming" in interests:
                greetings.extend([
                    "Salut ! Tu joues à quoi en ce moment ?",
                    "Hey gamer ! Quoi de neuf ?",
                    "Yo ! Des bonnes parties récemment ?"
                ])
            if "music" in interests:
                greetings.extend([
                    "Salut ! Tu écoutes quoi comme musique ?",
                    "Hey ! Des nouveaux sons à recommander ?",
                    "Yo ! Spotify tourne bien ?"
                ])
        
        # Référence à la localisation
        if info.get("location"):
            location = info["location"]
            greetings.extend([
                f"Salut ! Comment ça va à {location} ?",
                f"Hey ! Il fait beau à {location} ?",
                f"Yo de {location} !"
            ])
        
        import random
        return random.choice(greetings) if greetings else None
    
    def clean_old_messages(self, days_old: int = 7):
        """Nettoie les messages anciens"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for context_id in list(self.conversations.keys()):
            messages = self.conversations[context_id]
            # Filtrer les messages récents
            recent_messages = deque([
                msg for msg in messages 
                if datetime.fromisoformat(msg["timestamp"]) > cutoff_date
            ], maxlen=self.max_messages)
            
            if recent_messages:
                self.conversations[context_id] = recent_messages
            else:
                # Supprimer le contexte s'il n'y a plus de messages
                del self.conversations[context_id]
    
    def save_memory(self):
        """Sauvegarde la mémoire sur disque"""
        try:
            # Convertir les deques en listes pour la sérialisation JSON
            serializable_data = {
                "conversations": {
                    context_id: list(messages) 
                    for context_id, messages in self.conversations.items()
                },
                "users_info": dict(self.users_info)
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Mémoire sauvegardée dans {self.memory_file}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def load_memory(self):
        """Charge la mémoire depuis le disque"""
        if not os.path.exists(self.memory_file):
            self.logger.info("Aucun fichier de mémoire trouvé, démarrage avec mémoire vide")
            return
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support ancien format (sans structure)
            if "conversations" in data:
                conversations_data = data["conversations"]
                self.users_info = defaultdict(dict, data.get("users_info", {}))
            else:
                # Ancien format - tout est conversations
                conversations_data = data
                self.users_info = defaultdict(dict)
            
            # Convertir les listes en deques
            for context_id, messages in conversations_data.items():
                self.conversations[context_id] = deque(messages, maxlen=self.max_messages)
            
            total_contexts = len(self.conversations)
            total_messages = sum(len(messages) for messages in self.conversations.values())
            total_users = len(self.users_info)
            
            self.logger.info(f"Mémoire chargée: {total_contexts} contextes, {total_messages} messages, {total_users} utilisateurs")
            
            # Nettoyer les vieux messages au démarrage
            self.clean_old_messages()
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la mémoire: {e}")
            self.conversations = defaultdict(lambda: deque(maxlen=self.max_messages))
    
    def get_stats(self) -> Dict[str, any]:
        """Retourne des statistiques sur la mémoire"""
        total_contexts = len(self.conversations)
        total_messages = sum(len(messages) for messages in self.conversations.values())
        
        channel_contexts = sum(1 for cid in self.conversations.keys() if cid.startswith("channel:"))
        private_contexts = sum(1 for cid in self.conversations.keys() if cid.startswith("private:"))
        
        return {
            "total_contexts": total_contexts,
            "total_messages": total_messages,
            "channel_contexts": channel_contexts,
            "private_contexts": private_contexts,
            "memory_file_size": os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0
        }