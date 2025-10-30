from django.urls import path
#from .views import travel_predict, intent_predict, ner_extract
from .views import travel_predict

urlpatterns = [
    path('predict/', travel_predict, name="travel_predict"),
    #path('intent/', intent_predict, name="intent_predict"),
    #path('ner/', ner_extract, name="ner_extract"),
]
