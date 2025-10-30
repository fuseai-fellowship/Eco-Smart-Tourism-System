import json
import re
import spacy
import torch
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class WorkingTravelItineraryGenerator:
    def __init__(self, intent_model_path=None, spacy_model_path=None):
        base_dir = os.path.dirname(__file__)
        self.intent_model_path = intent_model_path or os.path.join(base_dir, "ml_models/intent_model")
        self.spacy_model_path = spacy_model_path or "en_core_web_sm"
        self.load_models()
        self.setup_destinations()
        print("✅ Working model initialized successfully!")

    def load_models(self):
        """Load the pretrained models"""
        if self.intent_model_path and os.path.exists(os.path.join(self.intent_model_path, "pytorch_model.bin")):
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            self.intent_tokenizer = AutoTokenizer.from_pretrained(self.intent_model_path)
            self.intent_model = AutoModelForSequenceClassification.from_pretrained(self.intent_model_path)
            with open(f"{self.intent_model_path}/label_map.json", 'r') as f:
                self.label_map = json.load(f)
            print("✅ Intent model loaded")
        else:
            self.intent_model = None
            self.intent_tokenizer = None
            self.label_map = None
            print("⚠️ Intent model not loaded, skipping.")

        # Load SpaCy model
        import spacy
        self.ner_model = spacy.load(self.spacy_model_path)
        print("✅ NER model loaded")


    def setup_destinations(self):
        """Setup Nepal destinations with guaranteed structure"""
        self.destinations = [
            {'name': 'Kathmandu Durbar Square', 'location': 'Kathmandu', 'description': 'Historical palace complex with ancient temples and courtyards',
             'category': 'cultural', 'activities': 'sightseeing, photography, culture, history', 'best_time': 'September-November',
             'budget_range': 'low', 'duration_recommended': '1 day'},
            {'name': 'Pokhara', 'location': 'Gandaki Province', 'description': 'Lakeside city with stunning mountain views and adventure sports',
             'category': 'adventure', 'activities': 'boating, paragliding, trekking, hiking', 'best_time': 'March-May, September-November',
             'budget_range': 'medium', 'duration_recommended': '2-3 days'},
            {'name': 'Chitwan National Park', 'location': 'Chitwan', 'description': 'UNESCO World Heritage site with rich wildlife and jungle safaris',
             'category': 'wildlife', 'activities': 'jungle safari, bird watching, elephant ride', 'best_time': 'October-February',
             'budget_range': 'medium', 'duration_recommended': '2 days'},
            {'name': 'Swayambhunath Stupa', 'location': 'Kathmandu', 'description': 'Ancient religious stupa atop a hill with panoramic city views',
             'category': 'cultural', 'activities': 'sightseeing, photography, spirituality', 'best_time': 'Year-round',
             'budget_range': 'low', 'duration_recommended': 'Half day'},
            {'name': 'Nagarkot', 'location': 'Bhaktapur', 'description': 'Hill station famous for Himalayan sunrise and sunset views',
             'category': 'nature', 'activities': 'hiking, sunrise views, photography', 'best_time': 'October-March',
             'budget_range': 'medium', 'duration_recommended': '1-2 days'},
            {'name': 'Patan Durbar Square', 'location': 'Lalitpur', 'description': 'Royal palace complex with exquisite wood and stone carvings',
             'category': 'cultural', 'activities': 'culture, photography, history, architecture', 'best_time': 'October-March',
             'budget_range': 'low', 'duration_recommended': '1 day'},
            {'name': 'Lumbini', 'location': 'Rupandehi', 'description': 'Birthplace of Lord Buddha with sacred gardens and monasteries',
             'category': 'spiritual', 'activities': 'meditation, culture, history, photography', 'best_time': 'October-March',
             'budget_range': 'low', 'duration_recommended': '1-2 days'}
        ]
        self.destinations_map = {dest['name'].lower(): dest for dest in self.destinations}

    def extract_entities(self, text):
        """Extract travel entities with Nepal-specific location detection"""
        doc = self.ner_model(text)
        text_lower = text.lower()
        entities = {'locations': [], 'durations': [], 'budgets': [], 'activities': [], 'dates': [], 'people': []}

        nepal_location_keywords = {
            'kathmandu': ['kathmandu', 'ktm'],
            'pokhara': ['pokhara'],
            'chitwan': ['chitwan'],
            'nagarkot': ['nagarkot'],
            'lumbini': ['lumbini'],
            'bhaktapur': ['bhaktapur'],
            'patan': ['patan', 'lalitpur']
        }
        for location, keywords in nepal_location_keywords.items():
            if any(keyword in text_lower for keyword in keywords) and location.title() not in entities['locations']:
                entities['locations'].append(location.title())

        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'FAC'] and ent.text not in entities['locations']:
                entities['locations'].append(ent.text)
            elif ent.label_ in ['DATE', 'TIME']:
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['budgets'].append(ent.text)

        duration_matches = re.findall(r'(\d+)\s*days?', text_lower)
        entities['durations'].extend(duration_matches)

        budget_matches = re.findall(r'\$(\d+)', text_lower)
        entities['budgets'].extend(budget_matches)

        activity_keywords = {
            'adventure': ['adventure', 'trekking', 'hiking', 'paragliding', 'rafting'],
            'culture': ['culture', 'cultural', 'temple', 'historical', 'heritage', 'historical sites'],
            'wildlife': ['wildlife', 'safari', 'jungle', 'animals', 'elephant'],
            'sightseeing': ['sightseeing', 'tour', 'visit', 'explore'],
            'photography': ['photography', 'photos', 'pictures'],
            'spiritual': ['spiritual', 'meditation', 'peace', 'yoga'],
            'food': ['food', 'cuisine', 'eating', 'local food']
        }
        for activity, keywords in activity_keywords.items():
            if any(keyword in text_lower for keyword in keywords) and activity not in entities['activities']:
                entities['activities'].append(activity)

        return entities

    def classify_intent(self, text):
        """Classify user intent"""
        try:
            inputs = self.intent_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
            with torch.no_grad():
                outputs = self.intent_model(**inputs)
            predicted_class_id = outputs.logits.argmax().item()
            return self.label_map.get(str(predicted_class_id), "travel_planning")
        except:
            text_lower = text.lower()
            if any(word in text_lower for word in ['adventure', 'trekking', 'hiking']):
                return "adventure"
            elif any(word in text_lower for word in ['culture', 'temple', 'historical']):
                return "cultural"
            elif any(word in text_lower for word in ['wildlife', 'safari', 'jungle']):
                return "wildlife"
            else:
                return "travel_planning"

    def find_matching_destinations(self, entities):
        matched_destinations = []
        location_hints = [loc.lower() for loc in entities.get('locations', [])]
        activity_hints = entities.get('activities', [])

        for dest_name, destination in self.destinations_map.items():
            score = 0
            for location_hint in location_hints:
                if location_hint in dest_name or location_hint in destination['location'].lower():
                    score += 3
            for activity_hint in activity_hints:
                dest_activities = destination['activities'].lower()
                dest_category = destination['category'].lower()
                if activity_hint in dest_activities:
                    score += 2
                elif activity_hint in dest_category:
                    score += 1
            if score > 0:
                matched_destinations.append((destination, score))
        matched_destinations.sort(key=lambda x: x[1], reverse=True)
        return [dest[0] for dest in matched_destinations[:3]]

    def generate_itinerary(self, user_input):
        entities = self.extract_entities(user_input)
        intent = self.classify_intent(user_input)
        destinations = self.find_matching_destinations(entities)
        return self.build_response(user_input, entities, intent, destinations)

    def build_response(self, user_input, entities, intent, destinations):
        duration = entities.get('durations', ['3'])[0] if entities.get('durations') else '3'
        budget_info = entities.get('budgets', [])
        budget = budget_info[0] if budget_info else 'medium'
        return {
            "success": True,
            "result": {
                "input": user_input,
                "entities": entities,
                "intent": intent,
                "destinations": destinations,
                "itinerary": {
                    "duration": f"{duration} days",
                    "summary": f"Custom {duration}-day Nepal {intent.title()} Experience",
                    "destinations": [dest['name'] for dest in destinations],
                    "daily_plan": self.build_daily_plan(duration, destinations),
                    "budget": self.calculate_budget(budget, duration),
                    "travel_tips": self.get_travel_tips(intent, destinations),
                    "recommendations": self.get_recommendations(intent)
                }
            }
        }

    def build_daily_plan(self, duration, destinations):
        days = int(duration)
        daily_plan = []
        for day in range(1, days + 1):
            if day == 1:
                daily_plan.append({
                    "day": day,
                    "title": "Arrival in Kathmandu",
                    "activities": [
                        "Arrive at Tribhuvan International Airport",
                        "Transfer to your hotel in Thamel",
                        "Explore local markets and streets",
                        "Traditional Nepali welcome dinner",
                        "Briefing about your Nepal adventure"
                    ]
                })
            elif day == 2 and destinations:
                first_dest = destinations[0]
                daily_plan.append({
                    "day": day,
                    "title": f"Explore {first_dest['name']}",
                    "activities": [
                        f"Travel to {first_dest['name']}",
                        f"Guided tour of main attractions",
                        f"Learn about local history and culture",
                        "Enjoy authentic local cuisine"
                    ]
                })
            elif day == days:
                daily_plan.append({
                    "day": day,
                    "title": "Departure & Farewell",
                    "activities": [
                        "Last-minute souvenir shopping",
                        "Visit local craft centers",
                        "Traditional farewell lunch",
                        "Transfer to airport for departure"
                    ]
                })
            else:
                dest_index = min(day - 2, len(destinations) - 1)
                if dest_index >= 0 and destinations:
                    current_dest = destinations[dest_index]
                    daily_plan.append({
                        "day": day,
                        "title": f"Discover {current_dest['name']}",
                        "activities": [
                            f"Morning exploration of {current_dest['name']}",
                            "Local cultural experiences",
                            "Adventure or relaxation activities",
                            "Evening local cuisine tasting"
                        ]
                    })
                else:
                    daily_plan.append({
                        "day": day,
                        "title": f"Day {day} Adventures",
                        "activities": [
                            "Morning sightseeing and exploration",
                            "Local food and culture immersion",
                            "Adventure activities or relaxation",
                            "Evening cultural experiences"
                        ]
                    })
        return daily_plan

    def calculate_budget(self, budget_hint, duration):
        duration = int(duration)
        if isinstance(budget_hint, str) and budget_hint.isdigit():
            total_budget = int(budget_hint)
            per_day = total_budget / duration
            if per_day <= 40:
                level = 'low'
            elif per_day <= 100:
                level = 'medium'
            else:
                level = 'high'
            total = total_budget
        else:
            level = 'medium'
            total = 70 * duration
        return {"total": f"${total} USD", "per_day": f"${total // duration} USD", "level": level, "description": f"{level.title()} budget travel"}

    def get_travel_tips(self, intent, destinations):
        tips = [
            "Carry Nepali rupees for local transactions",
            "Respect local customs and temple etiquette",
            "Dress modestly, especially in religious sites",
            "Stay hydrated and use sunscreen"
        ]
        if intent == 'adventure':
            tips.extend([
                "Book adventure activities with licensed operators",
                "Carry appropriate gear and clothing",
                "Check weather conditions before outdoor activities"
            ])
        elif intent == 'cultural':
            tips.extend([
                "Remove shoes before entering temples",
                "Ask permission before photographing people",
                "Learn basic Nepali greetings"
            ])
        return tips

    def get_recommendations(self, intent):
        if intent == 'adventure':
            return ["Paragliding in Pokhara with mountain views", "Trekking in Annapurna region", "White water rafting in Trishuli River"]
        elif intent == 'cultural':
            return ["Visit UNESCO World Heritage sites in Kathmandu Valley", "Attend traditional Nepali cultural shows", "Try authentic Newari cuisine"]
        elif intent == 'wildlife':
            return ["Jungle safari in Chitwan National Park", "Bird watching in Koshi Tappu", "Elephant bathing experience"]
        else:
            return ["Explore local markets and bazaars", "Try traditional Nepali dishes like momo and dal bhat", "Enjoy mountain views and photography"]
