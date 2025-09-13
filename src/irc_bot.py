import asyncio
import logging
import random
import socket
import ssl
from typing import Optional
from .config import Config
from .human_generator import HumanResponseGenerator

class IrcHumanizerBot:
    """Bot IRC principal qui imite un utilisateur humain"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.human_generator = HumanResponseGenerator(config)
        
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
            
            # Envoyer les informations d'authentification
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
        
        # Décider si on doit répondre (probabilité configurable)
        if random.random() > self.config.response_probability:
            return
        
        # Attendre un délai aléatoire pour simuler le temps de frappe
        delay = random.uniform(
            self.config.min_response_delay,
            self.config.max_response_delay
        )
        await asyncio.sleep(delay)
        
        # Générer une réponse humaine
        response = await self.human_generator.generate_response(message, sender, target)
        
        if response:
            await self.send_message(target, response)
            self.logger.info(f"[{target}] <{self.config.nickname}> {response}")
    
    async def disconnect(self):
        """Ferme la connexion"""
        # Sauvegarder la mémoire avant de fermer
        self.human_generator.memory.save_memory()
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False