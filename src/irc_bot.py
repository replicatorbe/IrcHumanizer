import asyncio
import logging
import random
import socket
import ssl
from typing import Optional
from .config import Config
from .human_generator import HumanResponseGenerator
from .activity_manager import ActivityManager

class IrcHumanizerBot:
    """Bot IRC principal qui imite un utilisateur humain"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.human_generator = HumanResponseGenerator(config)
        self.activity_manager = ActivityManager(config_data=config.activity_config)
        
    async def start(self):
        """Démarre le bot et maintient la connexion"""
        while True:
            try:
                await self.connect()
                await self.run()
            except Exception as e:
                self.logger.error(f"Erreur de connexion: {e}")
                self.logger.info("Reconnexion dans 30 secondes...")
                await asyncio.sleep(30)
    
    async def connect(self):
        """Établit la connexion au serveur IRC"""
        self.logger.info(f"Connexion à {self.config.server}:{self.config.port}")
        
        try:
            if self.config.ssl:
                context = ssl.create_default_context()
                self.reader, self.writer = await asyncio.open_connection(
                    self.config.server, self.config.port, ssl=context
                )
            else:
                self.reader, self.writer = await asyncio.open_connection(
                    self.config.server, self.config.port
                )
            
            # Utiliser l'identité de la personnalité si configuré
            if self.config.auto_personality_identity:
                personality_nickname = self._generate_personality_nickname()
                personality_realname = self._generate_personality_realname()
                
                # Envoyer les informations d'authentification
                await self.send_raw(f"NICK {personality_nickname}")
                await self.send_raw(f"USER {self.config.username} 0 * :{personality_realname}")
                
                # Mettre à jour le nickname dans la config pour les logs
                self.config.nickname = personality_nickname
                
                self.logger.info(f"Identité personnalisée: {personality_nickname} ({personality_realname})")
            else:
                # Utiliser l'identité de la config
                await self.send_raw(f"NICK {self.config.nickname}")
                await self.send_raw(f"USER {self.config.username} 0 * :{self.config.realname}")
            
            self.connected = True
            self.logger.info("Connexion établie")
            
        except Exception as e:
            self.logger.error(f"Échec de la connexion: {e}")
            raise
    
    async def send_raw(self, message: str):
        """Envoie un message brut au serveur IRC"""
        if not self.writer:
            return
            
        encoded_msg = f"{message}\r\n".encode('utf-8')
        self.writer.write(encoded_msg)
        await self.writer.drain()
        self.logger.debug(f">>> {message}")
    
    async def send_message(self, target: str, message: str):
        """Envoie un message à un salon ou utilisateur"""
        await self.send_raw(f"PRIVMSG {target} :{message}")
    
    async def send_action(self, target: str, action: str):
        """Envoie une action IRC (/me) à un salon ou utilisateur"""
        await self.send_raw(f"PRIVMSG {target} :\x01ACTION {action}\x01")
    
    async def join_channel(self, channel: str):
        """Rejoint un salon"""
        await self.send_raw(f"JOIN {channel}")
        self.logger.info(f"Rejoint le salon {channel}")
    
    async def run(self):
        """Boucle principale d'écoute des messages"""
        if not self.reader:
            return
            
        while self.connected:
            try:
                line = await self.reader.readline()
                if not line:
                    break
                    
                message = line.decode('utf-8', errors='ignore').strip()
                if not message:
                    continue
                    
                self.logger.debug(f"<<< {message}")
                await self.handle_message(message)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la lecture: {e}")
                break
    
    async def handle_message(self, raw_message: str):
        """Traite un message reçu du serveur"""
        parts = raw_message.split(' ', 3)
        
        if len(parts) < 2:
            return
            
        # Gérer PING pour maintenir la connexion
        if parts[0] == 'PING':
            await self.send_raw(f"PONG {parts[1]}")
            return
        
        # Message de bienvenue - rejoindre les salons
        if len(parts) >= 2 and parts[1] == '001':
            for channel in self.config.channels:
                await self.join_channel(channel)
            return
        
        # Messages de salon/privé
        if len(parts) >= 4 and parts[1] == 'PRIVMSG':
            await self.handle_privmsg(raw_message)
    
    async def handle_privmsg(self, raw_message: str):
        """Traite les messages privés et de salon"""
        # Parser le message IRC
        # Format: :nickname!user@host PRIVMSG #channel :message
        parts = raw_message.split(' ', 3)
        
        if len(parts) < 4:
            return
            
        sender_info = parts[0][1:]  # Enlever le ':' initial
        sender = sender_info.split('!')[0] if '!' in sender_info else sender_info
        target = parts[2]
        message = parts[3][1:]  # Enlever le ':' initial
        
        # Ignorer ses propres messages
        if sender == self.config.nickname:
            return
        
        self.logger.info(f"[{target}] <{sender}> {message}")
        
        # Vérifier si on simule une absence
        absence_reason = self.activity_manager.simulate_random_absence()
        if absence_reason:
            await self.send_action(target, absence_reason)
            self.logger.info(f"[{target}] * {self.config.nickname} {absence_reason}")
            return
        
        # Vérifier si on revient d'absence
        return_message = self.activity_manager.get_return_message()
        if return_message:
            await self.send_message(target, return_message)
            self.logger.info(f"[{target}] <{self.config.nickname}> {return_message}")
            return
        
        # Mettre à jour l'humeur du bot
        self.human_generator.personality.update_mood()
        
        # Vérifier si le bot fait une action spontanée
        action = self.human_generator.personality.get_irc_action()
        if action:
            action_delay = random.uniform(1.0, 6.0)
            await asyncio.sleep(action_delay)
            await self.send_action(target, action)
            self.logger.info(f"[{target}] * {self.config.nickname} {action}")
            return  # Action au lieu de réponse
        
        # Vérifier si le bot fait une interruption spontanée
        interruption = self.human_generator.get_spontaneous_interruption()
        if interruption:
            interruption_delay = random.uniform(2.0, 8.0)
            await asyncio.sleep(interruption_delay)
            adapted_interruption = self.human_generator.personality.adapt_response_style(interruption)
            adapted_interruption = self.human_generator._add_human_touches(adapted_interruption)
            await self.send_message(target, adapted_interruption)
            self.logger.info(f"[{target}] <{self.config.nickname}> [INTERRUPTION] {adapted_interruption}")
            return

        # Vérifier si le bot pose une question spontanée (très rare, channels seulement)
        if target.startswith('#'):
            spontaneous_question = self.human_generator.get_spontaneous_question(target)
            if spontaneous_question:
                # Délai plus long pour les questions spontanées (paraître naturel)
                question_delay = random.uniform(5.0, 18.0)
                await asyncio.sleep(question_delay)
                
                # Adapter la question selon la personnalité
                adapted_question = self.human_generator.personality.adapt_response_style(spontaneous_question)
                adapted_question = self.human_generator.personality.adapt_response_with_mood(adapted_question)
                adapted_question = self.human_generator._add_human_touches(adapted_question)
                
                await self.send_message(target, adapted_question)
                self.activity_manager.record_response()  # Compter comme une réponse
                self.logger.info(f"[{target}] <{self.config.nickname}> [QUESTION] {adapted_question}")
                return  # Question au lieu de réponse normale
        
        # Vérifier si le bot poste un status spontané (très rare, channels seulement)
        if target.startswith('#'):
            spontaneous_status = self.activity_manager.get_spontaneous_status()
            if spontaneous_status:
                # Délai moyen pour les status (paraître naturel)
                status_delay = random.uniform(3.0, 12.0)
                await asyncio.sleep(status_delay)
                
                # Adapter le status selon la personnalité
                adapted_status = self.human_generator.personality.adapt_response_style(spontaneous_status)
                adapted_status = self.human_generator.personality.adapt_response_with_mood(adapted_status) 
                adapted_status = self.human_generator._add_human_touches(adapted_status)
                
                await self.send_message(target, adapted_status)
                self.activity_manager.record_response()  # Compter comme une réponse
                self.logger.info(f"[{target}] <{self.config.nickname}> [STATUS] {adapted_status}")
                return  # Status au lieu de réponse normale
        
        # Vérifier si le bot est mentionné (réaction prioritaire)
        is_mentioned = self._is_bot_mentioned(message)
        
        # Décider si on doit répondre (probabilité modifiée par humeur + activité)
        mood_modifier = self.human_generator.personality.get_mood_modifier()
        base_probability = self.config.response_probability * mood_modifier
        
        # Si mentionné, probabilité beaucoup plus élevée (80%)
        if is_mentioned:
            base_probability = 0.8 * mood_modifier
        
        activity_level = self.activity_manager.get_activity_level()
        
        if not self.activity_manager.should_respond(base_probability):
            return
        
        # Générer une réponse humaine d'abord (avec contexte mention si applicable)
        response = await self.human_generator.generate_response(message, sender, target, is_mentioned)
        
        if response:
            # Calculer le délai de lecture du message reçu
            reading_delay = self.human_generator.calculate_reading_delay(message)
            
            # Calculer le délai de frappe réaliste basé sur la longueur de la réponse
            typing_delay = self.human_generator.calculate_typing_delay(response)
            
            # Combiner avec le délai d'activité (mais donner la priorité à la simulation de frappe)
            activity_delay = self.activity_manager.get_adaptive_delay(
                self.config.min_response_delay,
                self.config.max_response_delay
            )
            
            # Combiner délai de lecture + frappe + activité
            final_delay = reading_delay + max(typing_delay, activity_delay * 0.3)
            await asyncio.sleep(final_delay)
            await self.send_message(target, response)
            self.activity_manager.record_response()  # Enregistrer pour anti-détection
            self.logger.info(f"[{target}] <{self.config.nickname}> {response}")
    
    def _is_bot_mentioned(self, message: str) -> bool:
        """Vérifie si le bot est mentionné dans le message"""
        if not hasattr(self.config, 'nickname') or not self.config.nickname:
            return False
            
        message_lower = message.lower()
        nickname_lower = self.config.nickname.lower()
        
        # Détection de mentions directes
        mentions = [
            nickname_lower,                    # "Pierre"
            f"{nickname_lower}:",             # "Pierre:"  
            f"{nickname_lower},",             # "Pierre,"
            f"@{nickname_lower}",             # "@Pierre"
            f"{nickname_lower}?",             # "Pierre?"
            f"{nickname_lower}!",             # "Pierre!"
        ]
        
        # Vérifier si une mention est présente
        for mention in mentions:
            if mention in message_lower:
                return True
                
        # Détection contextuelle (salutations + nom)
        greetings = ["salut", "hello", "hi", "hey", "bonjour", "bonsoir"]
        for greeting in greetings:
            if greeting in message_lower and nickname_lower in message_lower:
                return True
                
        return False
    
    def _generate_personality_nickname(self) -> str:
        """Génère un nickname IRC basé sur la personnalité du bot"""
        profile = self.human_generator.personality.profile
        
        # Si un nickname personnalisé est défini ET qu'il correspond au genre, on l'utilise
        if hasattr(self.config, 'nickname') and self.config.nickname != "MonHumain":
            # Vérifier si le nickname correspond au genre de la personnalité
            if self._nickname_matches_gender(self.config.nickname, profile.gender):
                return self.config.nickname
        
        # Sinon générer un nickname approprié au genre
        base_name = self._get_gender_appropriate_name(profile.gender)
        
        # Variations possibles du prénom pour IRC
        import random
        variations = [
            base_name,                           # Sarah
            f"{base_name}_{profile.age}",       # Sarah_24
            f"{base_name}{profile.location['region']}", # Sarah69
            f"{base_name}_{profile.location['region']}", # Sarah_69
        ]
        
        return random.choice(variations)
    
    def _nickname_matches_gender(self, nickname: str, gender: str) -> bool:
        """Vérifie si un nickname correspond au genre"""
        # Listes de prénoms pour vérification
        male_names = [
            "Alex", "Alexandre", "Pierre", "Paul", "Jean", "Michel", "Nicolas", 
            "David", "Thomas", "Julien", "Antoine", "Laurent", "Sebastien",
            "Christophe", "Stephane", "Vincent", "Pascal", "Olivier", "Bruno",
            "Philippe", "Fabrice", "Thierry", "Patrice", "Romain", "Maxime",
            "Kevin", "Jeremy", "Florian", "Damien", "Cedric", "Gregory",
            "Mathieu", "Benjamin", "Lucas", "Hugo", "Leo", "Nathan", "Noah",
            "Arthur", "Louis", "Gabriel", "Raphael", "Adam", "Victor", "Jules",
            "Theo", "Ethan", "Nolan", "Clement", "Oscar", "Aaron", "Diego"
        ]
        
        female_names = [
            "Marie", "Sophie", "Anne", "Catherine", "Isabelle", "Nathalie",
            "Sylvie", "Stephanie", "Christine", "Sandrine", "Valerie", "Patricia",
            "Celine", "Aurelie", "Laetitia", "Carole", "Emilie", "Julie",
            "Laurence", "Veronique", "Virginie", "Corinne", "Delphine", "Martine",
            "Emma", "Jade", "Louise", "Alice", "Chloe", "Lina", "Lea", "Manon",
            "Clara", "Camille", "Sarah", "Ines", "Zoe", "Lily", "Elena", "Mia",
            "Nina", "Rose", "Anna", "Lola", "Eva", "Noa", "Romy", "Mila", "Lou"
        ]
        
        # Nettoyer le nickname (enlever chiffres et underscores)
        clean_nickname = nickname.split('_')[0].rstrip('0123456789')
        
        if gender == "M":
            return clean_nickname in male_names
        else:  # "F"
            return clean_nickname in female_names
    
    def _get_gender_appropriate_name(self, gender: str) -> str:
        """Retourne un prénom approprié au genre"""
        import random
        
        male_names = [
            "Alexandre", "Pierre", "Paul", "Jean", "Michel", "Nicolas", 
            "David", "Thomas", "Julien", "Antoine", "Laurent", "Sebastien",
            "Christophe", "Stephane", "Vincent", "Pascal", "Olivier", "Bruno",
            "Philippe", "Fabrice", "Thierry", "Patrice", "Romain", "Maxime",
            "Kevin", "Jeremy", "Florian", "Damien", "Cedric", "Gregory",
            "Mathieu", "Benjamin", "Lucas", "Hugo", "Leo", "Nathan", "Noah",
            "Arthur", "Louis", "Gabriel", "Raphael", "Adam", "Victor", "Jules",
            "Theo", "Ethan", "Nolan", "Clement", "Oscar", "Aaron", "Diego"
        ]
        
        female_names = [
            "Marie", "Sophie", "Anne", "Catherine", "Isabelle", "Nathalie",
            "Sylvie", "Stephanie", "Christine", "Sandrine", "Valerie", "Patricia",
            "Celine", "Aurelie", "Laetitia", "Carole", "Emilie", "Julie",
            "Laurence", "Veronique", "Virginie", "Corinne", "Delphine", "Martine",
            "Emma", "Jade", "Louise", "Alice", "Chloe", "Lina", "Lea", "Manon",
            "Clara", "Camille", "Sarah", "Ines", "Zoe", "Lily", "Elena", "Mia",
            "Nina", "Rose", "Anna", "Lola", "Eva", "Noa", "Romy", "Mila", "Lou"
        ]
        
        if gender == "M":
            return random.choice(male_names)
        else:  # "F"
            return random.choice(female_names)
    
    def _generate_personality_realname(self) -> str:
        """Génère un realname IRC basé sur la personnalité du bot"""
        profile = self.human_generator.personality.profile
        
        # Abréviations de villes courantes
        city_abbreviations = {
            "Paris": "Paris", "Lyon": "Lyon", "Marseille": "Mars",
            "Toulouse": "Toul", "Nice": "Nice", "Nantes": "Nant",
            "Strasbourg": "Stras", "Montpellier": "Montp", "Bordeaux": "Bdx",
            "Lille": "Lille", "Rennes": "Renn", "Reims": "Reims",
            "Toulon": "Toulon", "Grenoble": "Gren", "Dijon": "Dijon",
            "Angers": "Angers", "Nîmes": "Nimes", "Villeurbanne": "Villeurb",
            "Clermont-Ferrand": "Clermont", "Le Havre": "LH",
            # Ajouts internationaux
            "Bruxelles": "Bxl", "Brussels": "Bxl", "Brüssel": "Bxl",
            "Genève": "Gen", "Geneva": "Gen", "Genf": "Gen",
            "Montréal": "Mtl", "Montreal": "Mtl",
            "Lausanne": "Laus", "Zurich": "Zur", "Bern": "Bern", "Berne": "Bern"
        }
        
        # Format: age sexe ville (ex: "24 H Lyon", "24 F Lyon")
        city_abbrev = city_abbreviations.get(profile.location["city"], profile.location["city"][:4])
        
        # Conversion M -> H pour plus naturel
        gender_display = "H" if profile.gender == "M" else profile.gender
        
        return f"{profile.age} {gender_display} {city_abbrev}"
    
    async def disconnect(self):
        """Ferme la connexion"""
        # Sauvegarder la mémoire avant de fermer
        self.human_generator.memory.save_memory()
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False