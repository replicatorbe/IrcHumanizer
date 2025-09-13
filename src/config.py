import yaml
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class Config:
    """Configuration du bot IRC"""
    
    # Paramètres de connexion IRC
    server: str
    port: int
    ssl: bool
    nickname: str
    username: str
    realname: str
    channels: List[str]
    
    # Paramètres de comportement
    response_probability: float  # Probabilité de répondre (0.0 à 1.0)
    min_response_delay: float   # Délai minimum avant réponse (secondes)
    max_response_delay: float   # Délai maximum avant réponse (secondes)
    
    # API IA (pour future intégration)
    ai_api_key: str
    ai_model: str
    
    # Configuration personnalité (optionnelle)
    personality_config: Optional[Dict[str, Any]]
    
    # Configuration activité (optionnelle)
    activity_config: Optional[Dict[str, Any]]
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """Charge la configuration depuis un fichier YAML"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Fichier de configuration introuvable: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Remplacer les variables d'environnement
        data = cls._replace_env_vars(data)
        
        return cls(
            server=data['irc']['server'],
            port=data['irc']['port'],
            ssl=data['irc'].get('ssl', False),
            nickname=data['irc']['nickname'],
            username=data['irc']['username'],
            realname=data['irc']['realname'],
            channels=data['irc']['channels'],
            response_probability=data['behavior'].get('response_probability', 0.3),
            min_response_delay=data['behavior'].get('min_response_delay', 1.0),
            max_response_delay=data['behavior'].get('max_response_delay', 5.0),
            ai_api_key=data['ai'].get('api_key', ''),
            ai_model=data['ai'].get('model', 'gpt-3.5-turbo'),
            personality_config=data.get('personality'),
            activity_config=data.get('activity')
        )
    
    @staticmethod
    def _replace_env_vars(data):
        """Remplace les variables d'environnement dans la configuration"""
        if isinstance(data, dict):
            return {key: Config._replace_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [Config._replace_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        else:
            return data