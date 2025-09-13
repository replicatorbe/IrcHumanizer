#!/usr/bin/env python3
"""
IrcHumanizer - Un bot IRC qui imite un utilisateur humain
"""

import asyncio
import logging
import signal
from src.irc_bot import IrcHumanizerBot
from src.config import Config

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('irchumanizer.log'),
            logging.StreamHandler()
        ]
    )

async def main():
    """Point d'entrée principal du bot"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    bot = None
    
    def signal_handler(signum, frame):
        logger.info("Signal d'arrêt reçu, sauvegarde en cours...")
        if bot:
            asyncio.create_task(bot.disconnect())
    
    # Gérer les signaux d'arrêt proprement
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Charger la configuration
        config = Config.load_from_file('config.yaml')
        logger.info("Configuration chargée avec succès")
        
        # Créer et démarrer le bot
        bot = IrcHumanizerBot(config)
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Arrêt du bot demandé par l'utilisateur")
        if bot:
            await bot.disconnect()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise
    finally:
        if bot:
            await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())