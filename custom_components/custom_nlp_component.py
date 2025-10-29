# custom_components/custom_nlp_component.py

from typing import Any, Dict, Text, List
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.constants import INTENT, ENTITIES
from actions.custom_nlp import CustomNLPPipeline
import logging

logger = logging.getLogger(__name__)


@DefaultV1Recipe.register(
    DefaultV1Recipe.ComponentType.MESSAGE_FEATURIZER,
    is_trainable=False
)
class CustomNLPComponent(GraphComponent):
    """
    Custom Rasa NLU component integrating:
    - BERT for intent classification
    - spaCy for NER entity extraction
    """

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> "CustomNLPComponent":
        return cls(config, model_storage, resource)

    def __init__(
        self,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
    ) -> None:
        super().__init__()
        try:
            logger.info("🚀 Loading spaCy NER + BERT Intent Classifier on CPU...")
            self.pipeline = CustomNLPPipeline()
            logger.info("✅ CustomNLPPipeline loaded successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CustomNLPPipeline: {e}")
            raise e

    def process(self, messages: List[Message], **kwargs) -> List[Message]:
        """
        Apply NLP pipeline to user messages.
        Extracts intent and entities and stores them in Rasa Message objects.
        """
        for message in messages:
            text = message.get("text", "").strip()

            if not text:
                message.set(INTENT, {"name": "unknown", "confidence": 0.0})
                message.set(ENTITIES, [])
                continue

            try:
                result = self.pipeline.analyze(text)
                intent = result.get("intent", "unknown")
                confidence = float(result.get("confidence", 0.9))

                # --- Normalize spaCy NER entities ---
                entities = []
                for ent in result.get("entities", []):
                    ent_label = ent.get("label", "").upper()

                    # Map common location tags to Rasa DESTINATION
                    if ent_label in ["LOC", "GPE", "PLACE", "LOCATION", "CITY"]:
                        entities.append({
                            "entity": "DESTINATION",
                            "value": ent.get("text"),
                            "confidence": ent.get("confidence", 0.85),
                            "extractor": "spacy",
                        })
                    else:
                        entities.append(ent)

                # --- Set results into the message ---
                message.set(INTENT, {"name": intent, "confidence": confidence})
                message.set(ENTITIES, entities)

                logger.debug(f"[NLP] Text: {text}")
                logger.debug(f" → Intent: {intent} ({confidence:.2f})")
                logger.debug(f" → Entities: {entities}")

            except Exception as e:
                logger.error(f"Error processing '{text}': {e}")
                message.set(INTENT, {"name": "unknown", "confidence": 0.0})
                message.set(ENTITIES, [])

        return messages

    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        """No training — component is inference-only."""
        return training_data
