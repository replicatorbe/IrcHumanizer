import random
import re
import openai
import logging
from typing import Optional, List
from .memory_manager import ConversationMemory
from .personality import PersonalityManager

class HumanResponseGenerator:
    """Générateur de réponses humaines avec fautes et imperfections"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialiser la mémoire conversationnelle
        self.memory = ConversationMemory()
        
        # Initialiser la personnalité
        personality_config = config.personality_config if config else None
        self.personality = PersonalityManager(config_data=personality_config)
        self.logger.info(f"Personnalité générée: {self.personality.profile.name}, {self.personality.profile.age} ans, {self.personality.profile.location['city']}")
        
        # Initialiser OpenAI si une clé API est fournie
        if config and config.ai_api_key:
            self.client = openai.AsyncOpenAI(api_key=config.ai_api_key)
            self.use_ai = True
            self.logger.info("API OpenAI configurée")
        else:
            self.client = None
            self.use_ai = False
            self.logger.info("Utilisation des réponses prédéfinies")
        
        # Réponses de base pour la démonstration et fallback
        self.casual_responses = [
            "ah ok je voi",
            "ouai c vrai ça",
            "mdr 😂",
            "jsp trop la",
            "ah bon? intéressant",
            "hmm pas sur",
            "lol",
            "c clair",
            "ptdr",
            "ah ouai d'acc",
            "mouai bof",
            "carrément !",
            "nan mais sérieux ?",
            "ça depend",
            "jpp de ce truc",
            "c'est chiant ça",
            "cool alors",
            "ah merde",
            "jsp quoi dire",
            "ça marche",
            "bon ok",
            "haha",
            "exactement",
            "nan c pas ça",
            "je croi pas",
            "peut etre oui",
        ]
        
        self.question_responses = [
            "bonne question la",
            "aucun idée moi",
            "jsp du tout",
            "faut voir",
            "pourquoi tu demande ça ?",
            "ça depend de quoi tu parle",
            "c compliqué ton truc",
            "j'ai jamais testé",
            "va savoir",
            "bof je sai pas",
        ]
        
        self.greetings = [
            "salut !",
            "hello",
            "coucou",
            "yo",
            "re",
            "bjr",
            "slt",
        ]
        
        # Fautes de frappe courantes
        self.typo_replacements = {
            'que': ['ke', 'qu'],
            'qui': ['ki'],
            'quoi': ['koi'],
            'avec': ['ac', 'av'],
            'beaucoup': ['bcp', 'bocou'],
            'quelque': ['kelke'],
            'pourquoi': ['pk', 'pkoi'],
            'parce que': ['pcq', 'pcke'],
            'c\'est': ['c', 'ces', 'cé'],
            'aussi': ['ossi', 'aussi'],
            'maintenant': ['mtn', 'maintenan'],
            'peut-être': ['ptet', 'ptetre', 'peut etre'],
            'vraiment': ['vrmt', 'vraimen'],
            'quelqu\'un': ['kelkun', 'qqun'],
            'quelque chose': ['kelke choz', 'qqch'],
            'toujours': ['tjrs', 'tjs'],
            'jamais': ['jamé', 'jms'],
            'comment': ['commen', 'comm'],
            'très': ['trè', 'tré'],
            'après': ['apré', 'aprè'],
        }
        
    async def generate_response(self, message: str, sender: str, target: str) -> Optional[str]:
        """Génère une réponse humaine basée sur le message reçu"""
        message_lower = message.lower()
        
        # Ignorer les messages du bot ou les commandes
        if message.startswith('!') or message.startswith('/'):
            return None
        
        # Parfois ne pas répondre du tout (simulation d'inattention)
        if random.random() < 0.2:
            return None
        
        # Déterminer si c'est un message privé
        is_private = not target.startswith('#')
        
        # Ajouter le message à la mémoire
        self.memory.add_message(target, sender, message, is_private)
        
        # Vérifier les questions de géolocalisation (priorité haute)
        location_response = self.personality.should_respond_to_location_question(message)
        if location_response:
            # Adapter selon la personnalité et ajouter à la mémoire
            final_response = self.personality.adapt_response_style(location_response)
            final_response = self._add_human_touches(final_response)
            self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                  final_response, is_private, is_bot=True)
            return final_response
        
        # Vérifier les questions d'âge
        age_response = self.personality.get_age_appropriate_response(message)
        if age_response:
            final_response = self.personality.adapt_response_style(age_response)
            final_response = self._add_human_touches(final_response)
            self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                  final_response, is_private, is_bot=True)
            return final_response
        
        # Utiliser l'IA si disponible, sinon les réponses prédéfinies
        if self.use_ai:
            try:
                ai_response = await self._get_ai_response(message, sender, target, is_private)
                if ai_response:
                    # Adapter selon la personnalité et ajouter à la mémoire
                    human_response = self.personality.adapt_response_style(ai_response)
                    human_response = self._add_human_touches(human_response)
                    self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                          human_response, is_private, is_bot=True)
                    return human_response
            except Exception as e:
                self.logger.error(f"Erreur API IA: {e}")
                # Fallback vers réponses prédéfinies
        
        # Réponses prédéfinies (fallback ou mode par défaut)
        # Détection de salutations
        greetings_keywords = ['salut', 'hello', 'bonjour', 'bonsoir', 'coucou', 'hi', 'hey']
        if any(greeting in message_lower for greeting in greetings_keywords):
            response = random.choice(self.personality.profile.greetings)
            if sender:
                response += f" {sender}"
            # Appliquer personnalité + touches humaines
            response = self.personality.adapt_response_style(response)
            response = self._add_human_touches(response)
            self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                  response, is_private, is_bot=True)
            return response
        
        # Détection de questions
        if '?' in message or any(word in message_lower for word in ['comment', 'pourquoi', 'quand', 'où', 'qui', 'quoi']):
            base_response = random.choice(self.question_responses)
        else:
            base_response = random.choice(self.casual_responses)
        
        # Appliquer personnalité + touches humaines
        response = self.personality.adapt_response_style(base_response)
        response = self._add_human_touches(response)
        
        # Ajouter à la mémoire
        self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                              response, is_private, is_bot=True)
        
        return response
    
    async def _get_ai_response(self, message: str, sender: str, target: str, is_private: bool) -> Optional[str]:
        """Génère une réponse via l'API OpenAI"""
        try:
            # Récupérer l'historique de la conversation
            context_history = self.memory.format_history_for_ai(target, is_private, limit=6)
            
            # Analyser la personnalité de l'utilisateur
            user_personality = self.memory.get_user_personality(sender)
            
            # Construire le prompt avec contexte et personnalité
            context_type = "conversation privée" if is_private else f"salon {target}"
            personality_context = self.personality.get_personality_context()
            
            system_prompt = f"""Tu es un utilisateur IRC réel. Voici ta personnalité:

{personality_context}

Tu participes à une {context_type} et réponds naturellement.
- Utilise un langage simple, familier, avec parfois du langage SMS
- Reste bref (max 1-2 phrases) 
- Sois humain et spontané selon ta personnalité
- Ne sois pas trop poli ou formel
- Tiens compte de l'historique pour répondre de manière cohérente
- Si on te demande ton âge, ta ville, tes goûts, réponds selon ta personnalité
- Adapte ton niveau de langage selon ton score de décontraction"""
            
            # Construire les messages avec historique
            messages = [{"role": "system", "content": system_prompt}]
            
            # Ajouter l'historique si disponible
            if context_history:
                messages.append({
                    "role": "user", 
                    "content": f"Historique récent:\n{context_history}\n\n---\nNouveau message de {sender}: {message}"
                })
            else:
                messages.append({
                    "role": "user", 
                    "content": f"Message de {sender}: {message}"
                })
            
            # Ajouter info sur la personnalité de l'utilisateur si disponible
            if user_personality and user_personality.get("total_messages", 0) > 3:
                casualness = user_personality.get("casualness_score", 0)
                if casualness > 0.3:
                    messages[0]["content"] += f"\n\nNote: {sender} utilise un style décontracté avec des abréviations."
            
            response = await self.client.chat.completions.create(
                model=self.config.ai_model if self.config else "gpt-3.5-turbo",
                messages=messages,
                max_tokens=120,
                temperature=0.9
            )
            
            ai_text = response.choices[0].message.content.strip()
            
            # Limiter la longueur pour rester naturel sur IRC
            if len(ai_text) > 150:
                ai_text = ai_text[:147] + "..."
            
            return ai_text
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
            return None
    
    def _add_human_touches(self, text: str) -> str:
        """Ajoute des imperfections humaines au texte"""
        result = text
        
        # Appliquer des fautes de frappe aléatoires
        if random.random() < 0.4:  # 40% de chance d'avoir des fautes
            result = self._apply_typos(result)
        
        # Parfois oublier une majuscule en début de phrase
        if random.random() < 0.6:
            result = result[0].lower() + result[1:] if len(result) > 1 else result.lower()
        
        # Parfois oublier la ponctuation finale
        if random.random() < 0.3 and result.endswith(('.', '!', '?')):
            result = result[:-1]
        
        # Ajouter parfois des points de suspension
        if random.random() < 0.2:
            result += "..."
        
        # Ajouter parfois des répétitions de lettres
        if random.random() < 0.15:
            result = self._add_letter_repetitions(result)
        
        # Parfois ajouter des hésitations
        if random.random() < 0.1:
            hesitations = ['euh', 'hmm', 'bah', 'ben']
            hesitation = random.choice(hesitations)
            if random.random() < 0.5:
                result = hesitation + " " + result
            else:
                result = result + " " + hesitation
        
        return result
    
    def _apply_typos(self, text: str) -> str:
        """Applique des fautes de frappe courantes"""
        result = text
        
        for correct, typos in self.typo_replacements.items():
            if correct in result.lower():
                # Probabilité d'appliquer la faute
                if random.random() < 0.5:
                    typo = random.choice(typos)
                    # Conserver la casse
                    if correct in result:
                        result = result.replace(correct, typo)
                    elif correct.capitalize() in result:
                        result = result.replace(correct.capitalize(), typo.capitalize())
                    elif correct.upper() in result:
                        result = result.replace(correct.upper(), typo.upper())
        
        return result
    
    def _add_letter_repetitions(self, text: str) -> str:
        """Ajoute des répétitions de lettres (ex: ouaaaai)"""
        # Lettres pouvant être répétées
        repeatable = ['a', 'e', 'i', 'o', 'u', 'h']
        
        for i, char in enumerate(text.lower()):
            if char in repeatable and random.random() < 0.3:
                # Répéter 1 à 3 fois
                repetitions = random.randint(1, 3)
                text = text[:i+1] + char * repetitions + text[i+1:]
                break  # Une seule répétition par message
        
        return text