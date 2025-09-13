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
            action_delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(action_delay)
            await self.send_action(target, action)
            self.logger.info(f"[{target}] * {self.config.nickname} {action}")
            return  # Action au lieu de réponse
        
        # Décider si on doit répondre (probabilité modifiée par humeur + activité)
        mood_modifier = self.human_generator.personality.get_mood_modifier()
        base_probability = self.config.response_probability * mood_modifier
        activity_level = self.activity_manager.get_activity_level()
        
        if not self.activity_manager.should_respond(base_probability):
            return
        
        # Attendre un délai adaptatif selon l'heure et l'activité
        delay = self.activity_manager.get_adaptive_delay(
            self.config.min_response_delay,
            self.config.max_response_delay
        )
        await asyncio.sleep(delay)
        
        # Générer une réponse humaine
        response = await self.human_generator.generate_response(message, sender, target)
        
        if response:
            await self.send_message(target, response)
            self.activity_manager.record_response()  # Enregistrer pour anti-détection
            self.logger.info(f"[{target}] <{self.config.nickname}> {response}")
    
    def _generate_personality_nickname(self) -> str:
        """Génère un nickname IRC basé sur la personnalité du bot"""
        profile = self.human_generator.personality.profile
        
        # Si un nickname personnalisé est défini, on l'utilise
        if hasattr(self.config, 'nickname') and self.config.nickname != "MonHumain":
            return self.config.nickname
        
        # Sinon on utilise le prénom de la personnalité
        base_name = profile.name
        
        # Variations possibles du prénom pour IRC
        import random
        variations = [
            base_name,                           # Sarah
            f"{base_name}_{profile.age}",       # Sarah_24
            f"{base_name}{profile.location['region']}", # Sarah69
            f"{base_name}_{profile.location['region']}", # Sarah_69
        ]
        
        return random.choice(variations)
    
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
        
        # Format: age sexe ville (ex: "24 F Lyon")
        city_abbrev = city_abbreviations.get(profile.location["city"], profile.location["city"][:4])
        return f"{profile.age} {profile.gender} {city_abbrev}"
    
    async def disconnect(self):
        """Ferme la connexion"""
        # Sauvegarder la mémoire avant de fermer
        self.human_generator.memory.save_memory()
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False