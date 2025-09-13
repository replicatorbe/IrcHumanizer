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
        
    async def generate_response(self, message: str, sender: str, target: str, is_mentioned: bool = False) -> Optional[str]:
        """Génère une réponse humaine basée sur le message reçu"""
        message_lower = message.lower()
        
        # Ignorer les messages du bot, les commandes, et les réactions IRC
        if message.startswith('!') or message.startswith('/') or 'REACT' in message:
            return None
        
        # Parfois ne pas répondre du tout (simulation d'inattention) - mais pas si mentionné
        if not is_mentioned and random.random() < 0.2:
            return None
        
        # Déterminer si c'est un message privé
        is_private = not target.startswith('#')
        
        # Ajouter le message à la mémoire
        self.memory.add_message(target, sender, message, is_private)
        
        # Chance de salut personnalisé (5% si pas mentionné, 20% si mentionné)  
        greeting_chance = 0.2 if is_mentioned else 0.05
        if random.random() < greeting_chance:
            friendly_greeting = self.memory.get_friendly_greeting(sender)
            if friendly_greeting:
                final_greeting = self.personality.adapt_response_style(friendly_greeting)
                final_greeting = self.personality.adapt_response_with_mood(final_greeting)
                final_greeting = self._add_human_touches(final_greeting)
                self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                      final_greeting, is_private, is_bot=True)
                return final_greeting
        
        # Réponse spéciale si mentionné (priorité)
        if is_mentioned:
            mention_response = self._get_mention_response(message, sender)
            if mention_response:
                final_response = self.personality.adapt_response_style(mention_response)
                final_response = self.personality.adapt_response_with_mood(final_response)
                final_response = self._add_human_touches(final_response)
                self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                      final_response, is_private, is_bot=True)
                return final_response
        
        # Traitement spécial des messages privés
        if is_private:
            private_response = self._handle_private_message(message, sender)
            if private_response:
                final_response = self.personality.adapt_response_style(private_response)
                final_response = self.personality.adapt_response_with_mood(final_response)
                final_response = self._add_human_touches(final_response)
                self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                      final_response, is_private, is_bot=True)
                return final_response
        
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
                    # Adapter selon la personnalité, humeur et ajouter à la mémoire
                    human_response = self.personality.adapt_response_style(ai_response)
                    human_response = self.personality.adapt_response_with_mood(human_response)
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
            # Appliquer personnalité + humeur + touches humaines
            response = self.personality.adapt_response_style(response)
            response = self.personality.adapt_response_with_mood(response)
            response = self._add_human_touches(response)
            self.memory.add_message(target, self.config.nickname if self.config else "Bot", 
                                  response, is_private, is_bot=True)
            return response
        
        # Détection de questions
        if '?' in message or any(word in message_lower for word in ['comment', 'pourquoi', 'quand', 'où', 'qui', 'quoi']):
            base_response = random.choice(self.question_responses)
        else:
            base_response = random.choice(self.casual_responses)
        
        # Appliquer personnalité + humeur + touches humaines
        response = self.personality.adapt_response_style(base_response)
        response = self.personality.adapt_response_with_mood(response)
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
    
    def _get_mention_response(self, message: str, sender: str) -> Optional[str]:
        """Génère une réponse spéciale quand le bot est mentionné"""
        message_lower = message.lower()
        
        # Réponses selon le contexte de la mention
        direct_responses = [
            "Oui ?", "Tu m'as appelé ?", "Qu'est-ce qu'il y a ?",
            "Je t'écoute", "Salut !", "Oui oui ?", "Dites-moi tout !",
            "Présent !", "Me voilà !", "Yo !", "Hey !",
            "Qu'est-ce qui se passe ?", "Tu voulais me parler ?",
            "Je suis là", "Alors ?", "Quoi de neuf ?"
        ]
        
        # Réponses selon l'humeur
        mood = self.personality.profile.current_mood if self.personality else "neutral"
        
        if mood == "good":
            mood_responses = [
                "Salut ! Ça va bien !", "Hey ! Je suis de bonne humeur !",
                "Oui ! Tout va bien ici !", "Salut ! Ça roule !",
                "Hello ! Super journée !", "Yo ! Ça baigne !"
            ]
        elif mood == "tired":
            mood_responses = [
                "Hmm ? Oui ?", "...oui ?", "Je t'écoute",
                "Qu'est-ce qu'il y a ?", "Mmmh ?", "J'écoute..."
            ]
        elif mood == "bad":
            mood_responses = [
                "Quoi ?", "Oui bon...", "Qu'est-ce que tu veux ?",
                "Pas le moment...", "Bof", "Mmm ?"
            ]
        elif mood == "excited":
            mood_responses = [
                "Ouiiii ! Qu'est-ce qu'il y a ?", "Hey ! Alors ?!",
                "Salut ! Tu voulais quoi ?!", "Yoooo !", 
                "Dis-moi tout !", "Qu'est-ce qui t'amène ?!"
            ]
        else:  # neutral
            mood_responses = direct_responses.copy()
        
        # Utiliser les réponses selon l'humeur 70% du temps, sinon réponses directes
        if random.random() < 0.7 and mood != "neutral":
            responses = mood_responses
        else:
            responses = direct_responses
        
        # Parfois ajouter le nom de l'expéditeur (30% du temps)
        response = random.choice(responses)
        if random.random() < 0.3 and sender:
            # Variations avec le nom
            name_variations = [
                f"{response} {sender}",
                f"Salut {sender} ! {response.lower()}",
                f"{sender} ? {response.lower()}",
                f"Hey {sender}, {response.lower()}"
            ]
            response = random.choice(name_variations)
        
        return response
    
    def get_spontaneous_question(self, target: str) -> Optional[str]:
        """Génère une question spontanée pour relancer la conversation"""
        # Ne pas faire de questions en privé, seulement dans les channels
        if not target.startswith('#'):
            return None
            
        # Très faible probabilité (2%) pour éviter le spam
        if random.random() > 0.02:
            return None
            
        profile = self.personality.profile if self.personality else None
        
        # Questions générales par catégorie
        general_questions = [
            "Quelqu'un regarde quoi ce soir ?",
            "Vous faites quoi ce weekend ?",
            "Il y a du monde qui dort pas ?",
            "Alors, quoi de neuf par ici ?",
            "Une recommandation de film quelqu'un ?",
            "Vous écoutez quoi comme musique ?",
            "C'est mort ici non ?",
            "Personne pour papoter ?",
            "On fait quoi pour s'occuper ?",
            "Des nouvelles fraîches ?",
            "Comment ça se passe votre journée ?",
            "Y'a quelqu'un d'éveillé ?",
            "Une série à recommander ?"
        ]
        
        # Questions selon les intérêts de la personnalité
        interest_questions = {}
        
        if profile and profile.interests:
            if "gaming" in profile.interests:
                interest_questions["gaming"] = [
                    "Quelqu'un joue à quoi en ce moment ?",
                    "Des bonnes parties récemment ?",
                    "Y'a quoi comme bon jeu qui sort ?",
                    "Steam Summer Sales, quelqu'un craque ?",
                    "Des recos de jeux indé ?",
                    "Qui rage sur un jeu là ?",
                    "Console ou PC team ?"
                ]
            
            if "musique" in profile.interests:
                interest_questions["music"] = [
                    "Des découvertes musicales récentes ?",
                    "Qui connaît de bons artistes français ?",
                    "Spotify ou Deezer team ?",
                    "Un concert prévu prochainement ?",
                    "Vous écoutez quoi pour bosser ?",
                    "Des playlists à partager ?",
                    "Un groupe qui vous fait vibrer ?"
                ]
            
            if "sport" in profile.interests:
                interest_questions["sport"] = [
                    "Quelqu'un suit le foot ?",
                    "Des sportifs motivés ici ?",
                    "Vous faites du sport vous ?",
                    "Les JO quelqu'un suit ?",
                    "Une salle de sport à recommander ?",
                    "Course à pied, des adeptes ?",
                    "Le vélo c'est la vie non ?"
                ]
        
        # Questions selon l'humeur
        mood = self.personality.profile.current_mood if self.personality else "neutral"
        mood_questions = []
        
        if mood == "good":
            mood_questions = [
                "Tout le monde va bien ?",
                "Une bonne nouvelle à partager ?",
                "Quelqu'un de bonne humeur aussi ?",
                "On fait la fête ce soir ?",
                "Des projets sympa en vue ?",
                "Qui a le smile aujourd'hui ?"
            ]
        elif mood == "tired":
            mood_questions = [
                "Quelqu'un d'autre est crevé ?",
                "Dur dur la journée hein ?",
                "On tient le coup ?",
                "Café ou thé pour tenir ?",
                "Quelqu'un pour me tenir éveillé ?",
                "Sieste autorisée au bureau ?"
            ]
        elif mood == "excited":
            mood_questions = [
                "Y'a quelqu'un d'excité aussi ?!",
                "On fait quoi pour se défouler ?!",
                "Des plans fous ce weekend ?!",
                "Qui est chaud pour sortir ?!",
                "Une aventure quelqu'un ?!",
                "On organise quelque chose ?!"
            ]
        
        # Questions selon l'heure
        from datetime import datetime
        now = datetime.now()
        time_questions = []
        
        if 6 <= now.hour <= 10:
            time_questions = [
                "Bien dormi tout le monde ?",
                "Café ou petit déj au lit ?",
                "Motivés pour cette journée ?",
                "Quelqu'un debout de bonne heure ?",
                "Programme du jour ?"
            ]
        elif 12 <= now.hour <= 14:
            time_questions = [
                "Bon appétit à tous !",
                "Qu'est-ce qu'on mange ?",
                "Pause déj bien méritée ?",
                "Restaurant ou fait maison ?",
                "Des gourmands dans le coin ?"
            ]
        elif 17 <= now.hour <= 19:
            time_questions = [
                "Fin de journée comment ça va ?",
                "Apéro quelqu'un ?",
                "Programme de soirée ?",
                "Qui est libéré du taff ?",
                "On se détend enfin ?"
            ]
        elif 20 <= now.hour <= 23:
            time_questions = [
                "Soirée télé ou sortie ?",
                "Des couche-tard par ici ?",
                "Qui traîne encore ?",
                "Une série en cours ?",
                "Nuit blanche prévue ?"
            ]
        
        # Rassembler toutes les questions possibles
        all_questions = general_questions[:]
        
        # Ajouter questions selon intérêts (30% de chance)
        if interest_questions and random.random() < 0.3:
            for questions_list in interest_questions.values():
                all_questions.extend(questions_list)
        
        # Ajouter questions selon humeur (40% de chance)  
        if mood_questions and random.random() < 0.4:
            all_questions.extend(mood_questions)
        
        # Ajouter questions selon heure (50% de chance)
        if time_questions and random.random() < 0.5:
            all_questions.extend(time_questions)
        
        return random.choice(all_questions) if all_questions else None
    
    def _handle_private_message(self, message: str, sender: str) -> Optional[str]:
        """Traite spécialement les messages privés avec un ton plus personnel"""
        message_lower = message.lower()
        
        # Première fois en privé - accueil chaleureux
        user_history = self.memory.get_conversation_with_user(sender)
        is_first_private = len(user_history) <= 1
        
        if is_first_private:
            welcomes = [
                "Salut ! Tu voulais me parler en privé ?",
                "Hello ! Qu'est-ce qui t'amène ?",
                "Coucou ! Tu voulais discuter ?",
                "Yo ! Qu'est-ce qu'il y a ?",
                "Salut ! Je t'écoute",
                "Hey ! Comment ça va ?",
                "Hello ! Besoin de parler ?",
                "Coucou ! Tu vas bien ?"
            ]
            return random.choice(welcomes)
        
        # Questions fréquentes en privé
        if any(word in message_lower for word in ["aide", "help", "problème", "souci", "bug"]):
            help_responses = [
                "Dis-moi ce qui ne va pas, je vais essayer d'aider !",
                "Quel problème tu rencontres ?",
                "Raconte-moi, qu'est-ce qui coince ?",
                "Je t'écoute, qu'est-ce qu'il y a ?",
                "Explique-moi ton souci",
                "Allez, dis-moi tout !",
                "Je suis là pour ça, raconte !"
            ]
            return random.choice(help_responses)
        
        # Confidences/secrets
        if any(word in message_lower for word in ["secret", "confier", "dire à personne", "entre nous", "confidentiel"]):
            confidence_responses = [
                "Tu peux me faire confiance, promis !",
                "Ça reste entre nous bien sûr",
                "Secret professionnel, je dis rien !",
                "Motus et bouche cousue !",
                "Tu peux y aller, je garde tout pour moi",
                "Entre nous, pas de souci",
                "Confiance totale, je t'écoute"
            ]
            return random.choice(confidence_responses)
        
        # Questions personnelles sur le bot
        if any(word in message_lower for word in ["tu es qui", "comment tu t'appelles", "ton nom", "qui es-tu"]):
            if self.personality and self.personality.profile:
                profile = self.personality.profile
                identity_responses = [
                    f"Moi c'est {profile.name}, j'ai {profile.age} ans !",
                    f"Je suis {profile.name}, de {profile.location['city']}",
                    f"{profile.name}, {profile.age} ans, et toi ?",
                    f"Tu peux m'appeler {profile.name} !",
                    f"C'est {profile.name}, ravi de te rencontrer !",
                    f"Moi ? {profile.name}, et toi comment tu t'appelles ?"
                ]
                return random.choice(identity_responses)
        
        # Demandes d'informations personnelles
        if any(word in message_lower for word in ["d'où tu viens", "tu habites où", "ta ville", "tu viens d'où"]):
            if self.personality and self.personality.profile:
                city = self.personality.profile.location['city']
                location_responses = [
                    f"Je suis de {city} ! Et toi ?",
                    f"Moi je viens de {city}, ça te dit quelque chose ?",
                    f"{city} born and raised ! Tu connais ?",
                    f"J'habite à {city}, pas loin peut-être ?",
                    f"Native de {city} ! Tu viens d'où toi ?",
                    f"Petite {city.lower()}aise ! Et toi tu es d'où ?"
                ]
                return random.choice(location_responses)
        
        # Salutations privées plus chaleureuses
        if any(word in message_lower for word in ["salut", "hello", "coucou", "hey", "yo", "bonjour", "bonsoir"]):
            # Utiliser les infos de l'utilisateur si disponibles
            user_info = self.memory.get_user_info(sender)
            if user_info.get("first_name"):
                name = user_info["first_name"]
                personal_greetings = [
                    f"Coucou {name} ! Ça va ?",
                    f"Salut {name} ! Comment tu vas ?",
                    f"Hey {name} ! Quoi de neuf ?",
                    f"Hello {name} ! Ça roule ?",
                    f"Yo {name} ! Tu fais quoi ?",
                    f"Salut {name} ! Content de te revoir !",
                    f"Coucou {name} ! Ça fait plaisir !"
                ]
                return random.choice(personal_greetings)
            else:
                warm_greetings = [
                    "Salut ! Ça me fait plaisir de te revoir !",
                    "Coucou ! Tu vas bien ?",
                    "Hello ! Comment ça se passe ?",
                    "Hey ! Ravi de te reparler !",
                    "Yo ! Qu'est-ce que tu deviens ?",
                    "Salut ! Tu fais quoi de beau ?",
                    "Coucou ! Des nouvelles ?"
                ]
                return random.choice(warm_greetings)
        
        # Au revoir en privé
        if any(word in message_lower for word in ["au revoir", "bye", "ciao", "à plus", "salut", "bonne nuit", "bonne soirée"]):
            farewell_responses = [
                "À plus ! Ça m'a fait plaisir de discuter !",
                "Bye ! Prends soin de toi !",
                "Ciao ! À bientôt !",
                "Salut ! N'hésite pas à revenir !",
                "À plus tard ! Bonne continuation !",
                "Bye bye ! Passe une bonne soirée !",
                "Ciao ! À la prochaine !",
                "Au revoir ! Ça m'a fait plaisir !"
            ]
            return random.choice(farewell_responses)
        
        # Réponses générales plus personnelles pour le privé
        personal_responses = [
            "Dis-moi en plus !",
            "Ah intéressant ! Continue",
            "Je t'écoute attentivement",
            "Raconte-moi ça !",
            "Oui oui, je suis avec toi",
            "Tu peux tout me dire !",
            "Ça me passionne !",
            "Je suis tout ouïe",
            "Vas-y, explique-moi",
            "Je t'écoute vraiment"
        ]
        
        # 70% de chance de répondre avec une réponse personnelle
        if random.random() < 0.7:
            return random.choice(personal_responses)
            
        return None  # Laisser l'IA ou les réponses normales prendre le relais