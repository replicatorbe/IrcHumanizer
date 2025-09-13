import datetime
import random
import pytz
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ActivitySettings:
    """Configuration des horaires d'activité"""
    
    timezone: str = "Europe/Paris"
    
    # Horaires d'activité (format 24h)
    active_start: str = "08:00"  # Début d'activité
    active_end: str = "23:30"    # Fin d'activité
    
    # Pauses déjeuner et autres
    lunch_start: str = "12:00"
    lunch_end: str = "14:00"
    lunch_probability: float = 0.1  # 10% de chance d'être absent à l'heure de déj
    
    # Horaires de pointe (plus actif)
    peak_hours: list = None  # ["19:00-22:00"] par exemple
    
    # Week-end (moins actif)
    weekend_activity_modifier: float = 0.95  # 95% de l'activité normale
    
    def __post_init__(self):
        if self.peak_hours is None:
            self.peak_hours = ["19:00-22:00", "09:00-10:00"]

class ActivityManager:
    """Gestionnaire d'activité et d'anti-détection"""
    
    def __init__(self, settings: Optional[ActivitySettings] = None, config_data: Optional[Dict] = None):
        if config_data:
            self.settings = self._create_settings_from_config(config_data)
        else:
            self.settings = settings or ActivitySettings()
        self.tz = pytz.timezone(self.settings.timezone)
        
        # Anti-détection
        self.last_response_times = []  # Historique des temps de réponse
        self.daily_message_count = 0
        self.last_message_date = None
        
        # Simulation d'absence
        self.is_simulating_absence = False
        self.absence_end_time = None
        self.absence_reason = None
    
    def _create_settings_from_config(self, config_data: Dict) -> ActivitySettings:
        """Crée des ActivitySettings depuis la config YAML"""
        return ActivitySettings(
            timezone=config_data.get('timezone', 'Europe/Paris'),
            active_start=config_data.get('active_start', '08:00'),
            active_end=config_data.get('active_end', '23:30'),
            lunch_start=config_data.get('lunch_start', '12:00'),
            lunch_end=config_data.get('lunch_end', '14:00'),
            lunch_probability=config_data.get('lunch_probability', 0.3),
            peak_hours=config_data.get('peak_hours', ['19:00-22:00', '09:00-10:00']),
            weekend_activity_modifier=config_data.get('weekend_activity_modifier', 0.7)
        )
    
    def _parse_time(self, time_str: str) -> datetime.time:
        """Parse une heure au format HH:MM"""
        hour, minute = map(int, time_str.split(':'))
        return datetime.time(hour, minute)
    
    def _get_current_time(self) -> datetime.datetime:
        """Retourne l'heure actuelle dans le timezone configuré"""
        return datetime.datetime.now(self.tz)
    
    def is_active_hours(self) -> bool:
        """Vérifie si c'est dans les heures d'activité"""
        now = self._get_current_time()
        current_time = now.time()
        
        # Vérifier les horaires généraux
        start_time = self._parse_time(self.settings.active_start)
        end_time = self._parse_time(self.settings.active_end)
        
        if not (start_time <= current_time <= end_time):
            return False
        
        # Vérifier si c'est l'heure de déjeuner
        if self._is_lunch_time() and random.random() < self.settings.lunch_probability:
            return False
        
        return True
    
    def _is_lunch_time(self) -> bool:
        """Vérifie si c'est l'heure de déjeuner"""
        current_time = self._get_current_time().time()
        lunch_start = self._parse_time(self.settings.lunch_start)
        lunch_end = self._parse_time(self.settings.lunch_end)
        
        return lunch_start <= current_time <= lunch_end
    
    def _is_peak_hours(self) -> bool:
        """Vérifie si c'est les heures de pointe"""
        current_time = self._get_current_time().time()
        
        for peak_range in self.settings.peak_hours:
            start_str, end_str = peak_range.split('-')
            start_time = self._parse_time(start_str)
            end_time = self._parse_time(end_str)
            
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    def _is_weekend(self) -> bool:
        """Vérifie si c'est le weekend"""
        return self._get_current_time().weekday() >= 5  # 5=samedi, 6=dimanche
    
    def get_activity_level(self) -> float:
        """Retourne le niveau d'activité actuel (0.0 à 2.0)"""
        if not self.is_active_hours():
            return 0.3  # Moins actif hors heures mais pas inactif
        
        base_activity = 1.0
        
        # Modifier selon le weekend
        if self._is_weekend():
            base_activity *= self.settings.weekend_activity_modifier
        
        # Modifier selon les heures de pointe
        if self._is_peak_hours():
            base_activity *= 1.5
        
        # Ajouter une variation aléatoire (plus permissive)
        variation = random.uniform(0.9, 1.3)
        
        return base_activity * variation
    
    def should_respond(self, base_probability: float) -> bool:
        """Détermine si le bot devrait répondre selon l'activité"""
        if self.is_simulating_absence:
            return False
        
        activity_level = self.get_activity_level()
        adjusted_probability = base_probability * activity_level
        
        # Anti-détection: ne pas répondre trop souvent
        if self._is_responding_too_much():
            adjusted_probability *= 0.3  # Réduire drastiquement
        
        return random.random() < adjusted_probability
    
    def _is_responding_too_much(self) -> bool:
        """Détecte si on répond trop souvent (anti-détection)"""
        now = self._get_current_time()
        
        # Compter les messages du jour
        if self.last_message_date != now.date():
            self.daily_message_count = 0
            self.last_message_date = now.date()
        
        # Limites anti-détection
        max_daily_messages = 150  # Max messages par jour
        max_hourly_messages = 20  # Max messages par heure
        
        if self.daily_message_count >= max_daily_messages:
            return True
        
        # Vérifier messages de la dernière heure
        one_hour_ago = now - datetime.timedelta(hours=1)
        recent_responses = [
            t for t in self.last_response_times 
            if t > one_hour_ago
        ]
        
        return len(recent_responses) >= max_hourly_messages
    
    def record_response(self):
        """Enregistre qu'une réponse a été envoyée"""
        now = self._get_current_time()
        
        self.last_response_times.append(now)
        self.daily_message_count += 1
        
        # Garder seulement les 100 dernières réponses en mémoire
        if len(self.last_response_times) > 100:
            self.last_response_times = self.last_response_times[-100:]
    
    def simulate_random_absence(self) -> Optional[str]:
        """Simule une absence aléatoire avec raison"""
        if self.is_simulating_absence or random.random() > 0.01:  # 1% de chance (réduit)
            return None
        
        now = self._get_current_time()
        
        # Durées d'absence possibles (en minutes)
        absence_durations = {
            "mange un truc": (5, 15),
            "va aux toilettes": (2, 5), 
            "prend une pause": (10, 30),
            "sort fumer une clope": (5, 10),
            "va chercher un café": (3, 8),
            "répond au téléphone": (5, 15),
            "doit partir 5 min": (5, 20),
            "brb": (5, 25),
        }
        
        reason, (min_duration, max_duration) = random.choice(list(absence_durations.items()))
        duration = random.randint(min_duration, max_duration)
        
        self.is_simulating_absence = True
        self.absence_end_time = now + datetime.timedelta(minutes=duration)
        self.absence_reason = reason
        
        return reason
    
    def check_absence_end(self) -> bool:
        """Vérifie si l'absence simulée est terminée"""
        if not self.is_simulating_absence:
            return False
        
        now = self._get_current_time()
        if now >= self.absence_end_time:
            self.is_simulating_absence = False
            self.absence_end_time = None
            self.absence_reason = None
            return True  # Absence terminée
        
        return False
    
    def get_return_message(self) -> Optional[str]:
        """Génère un message de retour après absence"""
        if not self.check_absence_end():
            return None
        
        return_messages = [
            "re",
            "de retour", 
            "back",
            "c'est reparti",
            "me revoila",
            "ça y est je suis là",
        ]
        
        return random.choice(return_messages)
    
    def get_adaptive_delay(self, base_min: float, base_max: float) -> float:
        """Calcule un délai adaptatif basé sur l'heure et l'activité"""
        activity_level = self.get_activity_level()
        
        # Plus actif = réponse plus rapide
        if activity_level > 1.2:
            # Heures de pointe: plus réactif
            modifier = 0.7
        elif activity_level < 0.5:
            # Heures creuses: plus lent
            modifier = 1.8
        else:
            modifier = 1.0
        
        # Variation selon l'heure de la journée
        hour = self._get_current_time().hour
        if 6 <= hour <= 9:  # Matin: un peu lent
            modifier *= 1.3
        elif 22 <= hour <= 23:  # Soir tard: plus lent
            modifier *= 1.5
        
        adjusted_min = base_min * modifier
        adjusted_max = base_max * modifier
        
        return random.uniform(adjusted_min, adjusted_max)
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques d'activité"""
        now = self._get_current_time()
        
        return {
            "current_time": now.strftime("%H:%M"),
            "is_active_hours": self.is_active_hours(),
            "activity_level": round(self.get_activity_level(), 2),
            "daily_messages": self.daily_message_count,
            "is_absent": self.is_simulating_absence,
            "absence_reason": self.absence_reason,
            "is_peak_hours": self._is_peak_hours(),
            "is_weekend": self._is_weekend()
        }