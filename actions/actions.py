import pandas as pd
import random
import re
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import os
import logging

logger = logging.getLogger(__name__)

# -----------------------------
# Helper: Convert duration to numeric
# -----------------------------
def parse_duration(duration_str):
    duration_str = str(duration_str).lower()
    numbers = re.findall(r'\d+\.?\d*', duration_str)

    if "half" in duration_str:
        return [0.5]
    elif "few hour" in duration_str:
        return [0.25]
    elif "day" in duration_str:
        return [float(numbers[0]) if numbers else 1.0]
    elif "-" in duration_str and len(numbers) == 2:
        return [float(n) for n in numbers]
    elif numbers:
        return [float(n) for n in numbers]
    else:
        return []

# -----------------------------
# ACTION: Suggest Itinerary
# -----------------------------
class ActionSuggestItinerary(Action):
    def name(self):
        return "action_suggest_itinerary"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        # --- Get slots ---
        slots = {
            "location": tracker.get_slot("location"),
            "province": tracker.get_slot("province"),
            "activity_type": tracker.get_slot("activity_type"),
            "category": tracker.get_slot("category"),
            "duration": tracker.get_slot("duration"),
            "best_time": tracker.get_slot("best_time"),
            "popularity_preference": tracker.get_slot("popularity_preference")
        }

        # --- Ask popularity preference if not provided ---
        if not slots["popularity_preference"]:
            dispatcher.utter_message(
                text="Do you prefer **popular destinations**, **off-beat**, or **both**?"
            )
            return [SlotSet("popularity_preference", None)]

        # --- Load dataset ---
        data_path = os.path.join("data", "Unified_Itinerary_Data.csv")
        if not os.path.exists(data_path):
            dispatcher.utter_message(text="⚠️ Itinerary data file not found.")
            return []

        try:
            df = pd.read_csv(data_path)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error loading itinerary data: {e}")
            return []

        # --- Normalize column names ---
        df.columns = df.columns.str.strip().str.lower()
        required_cols = ["destination", "province", "location", "category", "duration", "best_time", "tags", "popularity"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            dispatcher.utter_message(text=f"⚠️ Missing column(s) in dataset: {', '.join(missing_cols)}")
            return []

        for col in required_cols:
            df[col] = df[col].astype(str).str.strip().str.lower()

        filtered_df = df.copy()

        # --- Handle user input: multiple locations ---
        locations = []
        if slots["location"]:
            loc_text = str(slots["location"]).lower().strip()
            # Split by comma, 'and', '&'
            locations = [l.strip() for l in re.split(r",| and | & ", loc_text) if l.strip()]

        # --- Filter by location(s) or province ---
        if locations:
            mask = pd.Series(False, index=filtered_df.index)
            for loc in locations:
                mask = mask | filtered_df["location"].str.contains(re.escape(loc), na=False)
            filtered_df = filtered_df[mask]
        elif slots["province"]:
            province_str = str(slots["province"]).lower().strip()
            filtered_df = filtered_df[filtered_df["province"] == province_str]

        # --- Filter by category ---
        if slots["category"]:
            filtered_df = filtered_df[
                filtered_df["category"].str.contains(str(slots["category"]).lower(), na=False)
            ]

        # --- Filter by activity type ---
        if slots["activity_type"]:
            filtered_df = filtered_df[
                filtered_df["tags"].str.contains(str(slots["activity_type"]).lower(), na=False)
            ]

        # --- Filter by best time ---
        if slots["best_time"]:
            filtered_df = filtered_df[
                filtered_df["best_time"].str.contains(str(slots["best_time"]).lower(), na=False)
            ]

        # --- Filter by popularity preference ---
        pop_pref = str(slots["popularity_preference"]).lower()
        if pop_pref in ["popular", "off-beat"]:
            filtered_df = filtered_df[
                filtered_df["popularity"].str.contains(pop_pref, na=False)
            ]
        # if 'both', do not filter by popularity

        # --- Smart duration filtering ---
        if slots["duration"]:
            user_durations = parse_duration(slots["duration"])
            if user_durations:
                def match_duration(row_dur):
                    row_durs = parse_duration(row_dur)
                    for ud in user_durations:
                        if any(abs(ud - rd) < 0.25 or (ud >= rd and "-" in str(row_dur)) for rd in row_durs):
                            return True
                    return False
                filtered_df = filtered_df[filtered_df["duration"].apply(match_duration)]

        logger.info(f"Filtered dataframe shape: {filtered_df.shape}")

        # --- Prepare response ---
        if not filtered_df.empty:
            top_suggestions = filtered_df.sample(min(3, len(filtered_df)))
            messages = []
            for idx, row in top_suggestions.iterrows():
                response_slots = {
                    "destination": row.get("destination", "unknown"),
                    "province": row.get("province", "unknown"),
                    "location": slots["location"] if slots["location"] else row.get("location", "unknown"),
                    "category": row.get("category", "not specified"),
                    "duration": row.get("duration", "not specified"),
                    "best_time": row.get("best_time", "not available"),
                    "tags": ", ".join([t.strip() for t in str(row.get("tags", "not specified")).split(",") if t.strip()])
                }
                msg = (
                    f"✨ Suggested destination: **{response_slots['destination'].title()}** 🏞️\n"
                    f"📍 Province: {response_slots['province'].title()}\n"
                    f"📍 Location: {response_slots['location'].title()}\n"
                    f"🏕️ Category: {response_slots['category'].title()}\n"
                    f"🕒 Duration: {response_slots['duration']}\n"
                    f"🌤️ Best Time: {response_slots['best_time'].title()}\n"
                    f"🎯 Activities: {response_slots['tags'].title() if response_slots['tags'] else 'Not specified'}\n"
                )
                messages.append(msg)

            full_msg = "\n---\n".join(messages)
            full_msg += "\n\nWould you like me to include nearby attractions too?"
            dispatcher.utter_message(text=full_msg)

            first_row = top_suggestions.iloc[0]
            return [
                SlotSet("location", slots["location"].lower() if slots["location"] else ""),
                SlotSet("province", slots["province"].lower() if slots["province"] else first_row.get("province", "").lower()),
                SlotSet("destination", first_row.get("destination", "").lower()),
                SlotSet("category", first_row.get("category", "").lower()),
                SlotSet("duration", first_row.get("duration", "").lower()),
                SlotSet("best_time", first_row.get("best_time", "").lower()),
                SlotSet("tags", first_row.get("tags", "").lower()),
            ]
        else:
            dispatcher.utter_message(
                text=f"😕 Sorry, I couldn’t find itinerary info for "
                     f"{', '.join(locations) if locations else (slots['province'] or 'that place')}.\n"
                     f"Try adjusting the duration, category, activity type, or popularity preference!"
            )
            return []

class ActionRecommendDestinations(Action):
    def name(self) -> str:
        return "action_recommend_destinations"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        # A simple static response
        destinations = ["Kathmandu 🏙️", "Pokhara 🌄", "Chitwan 🐘", "Lumbini 🕊️"]
        dispatcher.utter_message(text=f"Here are some popular destinations: {', '.join(destinations)}")
        return []
