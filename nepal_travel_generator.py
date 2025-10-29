# nepal_travel_generator.py
import re
from actions.custom_nlp import CustomNLPPipeline

class NepalTravelItineraryGenerator:
    """
    Nepal Travel Itinerary Generator for Rasa
    Uses CustomNLPPipeline (BERT intent + spaCy NER) to parse user input
    and generate a structured itinerary.
    """

    def __init__(self):
        print("🚀 Initializing Nepal Travel Itinerary Generator...")
        self.nlp_pipeline = CustomNLPPipeline()

        # Knowledge base: example destinations
        self.knowledge_base = {
            "Kathmandu": [
                {"name": "Kathmandu Durbar Square", "description": "Historical palace complex with ancient temples and courtyards", "location": "Kathmandu"},
                {"name": "Swayambhunath Stupa", "description": "Ancient religious stupa atop a hill with panoramic city views", "location": "Kathmandu"}
            ],
            "Pokhara": [
                {"name": "Pokhara", "description": "Lakeside city with stunning mountain views and adventure sports", "location": "Gandaki Province"}
            ],
            "Chitwan": [
                {"name": "Chitwan National Park", "description": "UNESCO World Heritage site with rich wildlife and jungle safaris", "location": "Chitwan"}
            ]
        }

    def generate_itinerary(self, text: str):
        """
        Analyze user text, extract entities and intent, and return a structured itinerary.
        """
        # Run NLU pipeline
        result = self.nlp_pipeline.analyze(text)

        # Extract entities
        entities = {ent['entity']: ent['value'] for ent in result['entities']}
        locations = [ent['value'] for ent in result['entities'] if ent['entity'].lower() in ['location', 'locations', 'geo']]
        durations = [int(ent['value']) for ent in result['entities'] if ent['entity'].lower() in ['duration', 'durations', 'days']]
        budgets = [ent['value'] for ent in result['entities'] if ent['entity'].lower() in ['budget', 'amount', 'money']]

        # Default values
        duration = f"{durations[0]} days" if durations else "3 days"
        budget = f"${budgets[0]} USD" if budgets else "$150 USD"

        # Determine recommended destinations
        recommended_destinations = []
        for loc in locations:
            if loc in self.knowledge_base:
                recommended_destinations.extend(self.knowledge_base[loc])

        # If no location matched, default to Kathmandu
        if not recommended_destinations:
            recommended_destinations = self.knowledge_base["Kathmandu"]

        # Create daily plan (simple example)
        daily_plan = []
        for i, dest in enumerate(recommended_destinations, start=1):
            daily_plan.append({
                "day": i,
                "title": f"Visit {dest['name']}",
                "activities": [
                    f"Travel to {dest['name']}",
                    f"Explore main attractions of {dest['name']}"
                ]
            })

        # Build itinerary
        itinerary = {
            "duration": duration,
            "budget": {"total": budget},
            "daily_plan": daily_plan
        }

        return {
            "result": {
                "destinations": recommended_destinations,
                "itinerary": itinerary
            }
        }


# 🔹 Test standalone
if __name__ == "__main__":
    generator = NepalTravelItineraryGenerator()
    test_texts = [
        "3 days in Kathmandu with budget $200",
        "Adventure trip to Pokhara for 5 days",
        "Wildlife safari in Chitwan for 3 days",
    ]

    for text in test_texts:
        result = generator.generate_itinerary(text)
        print(f"\nInput: {text}")
        print("Generated Itinerary:", result)
