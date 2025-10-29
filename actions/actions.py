from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from nepal_travel_generator import NepalTravelItineraryGenerator  # your main class

class ActionGenerateItinerary(Action):

    def name(self) -> str:
        return "action_generate_itinerary"

    def __init__(self):
        self.generator = NepalTravelItineraryGenerator()

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        user_input = tracker.latest_message.get("text")
        dispatcher.utter_message(text=f"🧳 Planning your itinerary for: '{user_input}'...")

        try:
            result = self.generator.generate_itinerary(user_input)
            itinerary = result['result']['itinerary']
            destinations = [d['name'] for d in result['result']['destinations']]
            budget = itinerary['budget']['total']
            duration = itinerary['duration']

            response = f"✅ Here’s your {duration} itinerary!\n"
            response += f"📍 Destinations: {', '.join(destinations)}\n"
            response += f"💰 Budget: {budget}\n\n"
            response += "🗓️ Sample Plan:\n"

            for day in itinerary['daily_plan'][:2]:  # just preview
                response += f"  Day {day['day']}: {day['title']}\n"
                for activity in day['activities'][:2]:
                    response += f"   • {activity}\n"

            dispatcher.utter_message(text=response)

        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Sorry, I couldn’t generate your itinerary right now: {e}")

        return []
