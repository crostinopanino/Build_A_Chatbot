from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    activities = relationship('Activity', backref='location')


class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    weather_condition = Column(String, nullable=False)
    activity = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)


class WeatherCache(Base):
    __tablename__ = 'weather_cache'
    id = Column(Integer, primary_key=True)
    location = Column(String, nullable=False)
    forecast_data = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)


class ChatbotTrainingData(Base):
    __tablename__ = 'chatbot_training_data'
    id = Column(Integer, primary_key=True)
    input_text = Column(String, nullable=False)
    response_text = Column(String, nullable=False)


engine = create_engine('sqlite:///go_travel.db')
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()

training_data = [
    {"input_text": "What can you do?",
     "response_text": "I can retrieve weather information for locations in your itinerary!"},
    {"input_text": "How do you work?",
     "response_text": "Just ask where you would like to know the weather forecast and let me do the rest!"},
    {"input_text": "What is the weather",
     "response_text": "Which location would you like the weather forecast?"},
]

for entry in training_data:
    record_exists = session.query(ChatbotTrainingData).filter_by(input_text=entry['input_text']).first()
    if not record_exists:
        new_record = ChatbotTrainingData(**entry)
        session.add(new_record)

session.commit()

# Dictionary of location names with their latitude and longitude
location_coordinates = {
    'Corfe Castle': (50.6395, -2.0566),
    'The Cotswolds': (51.8330, -1.8433),
    'Cambridge': (52.2053, 0.1218),
    'Bristol': (51.4545, -2.5879),
    'Oxford': (51.7520, -1.2577),
    'Norwich': (52.6309, 1.2974),
    'Stonehenge': (51.1789, -1.8262),
    'Watergate Bay': (50.4429, -5.0553),
    'Birmingham': (52.4862, -1.8904)
}

# Insert locations with coordinates if they don't exist yet
for name, (lat, lon) in location_coordinates.items():
    location_exists = session.query(Location.id).filter_by(name=name).scalar()
    if not location_exists:
        new_location = Location(name=name, latitude=lat, longitude=lon)
        session.add(new_location)

session.commit()

location_ids = {location.name: location.id for location in session.query(Location).all()}

activities_data = [
    # Activities for Bristol
    {"location_id": location_ids['Bristol'], "weather_condition": "Rain", "activity": "SS Great Britain Visit",
     "recommendation": "Step aboard the SS Great Britain and discover Bristol's maritime history on a rainy day."},
    {"location_id": location_ids['Bristol'], "weather_condition": "Clear", "activity": "Bristol Balloon Fiesta",
     "recommendation": "Take to the skies and enjoy a hot air balloon ride over Bristol."},
    {"location_id": location_ids['Bristol'], "weather_condition": "Clouds", "activity": "Bristol Shopping Experience",
     "recommendation": "Rug up and enjoy shopping at the Cabot Circus, it's the perfect day to be indoors."},

    # Activities for Oxford
    {"location_id": location_ids['Oxford'], "weather_condition": "Rain", "activity": "Ashmolean Museum Exploration",
     "recommendation": "Discover treasures from around the world in the dry comfort of Oxford's Ashmolean Museum."},
    {"location_id": location_ids['Oxford'], "weather_condition": "Clear", "activity": "Punting on the Isis",
     "recommendation": "Take a traditional punt along the river on a clear Oxford day."},
    {"location_id": location_ids['Oxford'], "weather_condition": "Clouds", "activity": "Indoor Climbing Adventure",
     "recommendation": "Test your climbing skills at the indoor wall, a perfect cloudy day activity."},

    # Activities for Cambridge
    {"location_id": location_ids['Cambridge'], "weather_condition": "Rain", "activity": "Fitzwilliam Museum Tour",
     "recommendation": "Enjoy an educational visit to the Fitzwilliam Museum, avoiding the rain."},
    {"location_id": location_ids['Cambridge'], "weather_condition": "Clear",
     "activity": "Cambridge University Botanic Garden",
     "recommendation": "Explore the beautiful plant collections at the Botanic Gardens on a clear day."},
    {"location_id": location_ids['Cambridge'], "weather_condition": "Clouds", "activity": "Hot Chocolate in Fitzbillies",
     "recommendation": "Savor a famous Fitzbillies hot chocolate to warm up on a cloudy day in Cambridge."},

    # Activities for Corfe Castle
    {"location_id": location_ids['Corfe Castle'], "weather_condition": "Rain", "activity": "Corfe Castle Model Village",
     "recommendation": "Step back in time and enjoy the Corfe Castle Model Village indoors when it's raining."},
    {"location_id": location_ids['Corfe Castle'], "weather_condition": "Clear", "activity": "Hike around Corfe Castle",
     "recommendation": "Take a scenic hike around Corfe Castle and enjoy the stunning views on a clear day."},
    {"location_id": location_ids['Corfe Castle'], "weather_condition": "Clouds", "activity": "Pub Lunch by the Fireplace",
     "recommendation": "Cozy up with a warm pub lunch by the fire in one of Corfe's historic taverns."},

    # Activities for The Cotswolds
    {"location_id": location_ids['The Cotswolds'], "weather_condition": "Rain", "activity": "Cotswold Motoring Museum",
     "recommendation": "Stay dry while journeying through automotive history at the Cotswold Motoring Museum."},
    {"location_id": location_ids['The Cotswolds'], "weather_condition": "Clear",
     "activity": "Walk through Bourton-on-the-Water",
     "recommendation": "Stroll through the 'Venice of the Cotswolds' and visit the charming boutiques."},
    {"location_id": location_ids['The Cotswolds'], "weather_condition": "Clouds", "activity": "Spa Day in the Cotswolds",
     "recommendation": "Treat yourself to a relaxing spa day in the tranquil setting of the Cotswolds."},

    # Activities for Norwich
    {"location_id": location_ids['Norwich'], "weather_condition": "Rain",
     "activity": "Norwich Castle Museum & Art Gallery",
     "recommendation": "Explore Norwich's history and culture indoors at the castle museum."},
    {"location_id": location_ids['Norwich'], "weather_condition": "Clear", "activity": "Norwich Market",
     "recommendation": "Enjoy local food and shopping at Norwich Market on a clear day."},
    {"location_id": location_ids['Norwich'], "weather_condition": "Clouds", "activity": "Theatre Royal Norwich",
     "recommendation": "Catch a show at the Theatre Royal for a memorable night out in Norwich."},

    # Activities for Stonehenge
    {"location_id": location_ids['Stonehenge'], "weather_condition": "Rain", "activity": "Stonehenge Visitor Center",
     "recommendation": "Learn about the mysteries of Stonehenge in the comfort of the visitor center."},
    {"location_id": location_ids['Stonehenge'], "weather_condition": "Clear", "activity": "Stonehenge Walk",
     "recommendation": "Take a walk around the historic Stonehenge site with clear skies above."},
    {"location_id": location_ids['Stonehenge'], "weather_condition": "Clouds", "activity": "Stonehenge Photo Opportunity",
     "recommendation": "Capture the beauty of Stonehenge in a moody, cloudy setting."},

    # Activities for Watergate Bay
    {"location_id": location_ids['Watergate Bay'], "weather_condition": "Rain",
     "activity": "Indoor Swim and Spa",
     "recommendation": "Relax in the warmth of an indoor pool and spa while watching the rain outside."},
    {"location_id": location_ids['Watergate Bay'], "weather_condition": "Clear", "activity": "Watergate Bay Surfing",
     "recommendation": "Catch some waves and soak up the sun with a surfing lesson at Watergate Bay."},
    {"location_id": location_ids['Watergate Bay'], "weather_condition": "Clouds", "activity": "Jamie Oliver's Fifteen Cornwall",
     "recommendation": "Enjoy seaside dining at Jamie Oliver's restaurant, overlooking the cloudy bay."},

    # Activities for Birmingham
    {"location_id": location_ids['Birmingham'], "weather_condition": "Rain",
     "activity": "Birmingham Museum and Art Gallery",
     "recommendation": "Stay out of the rain while discovering art and history in Birmingham."},
    {"location_id": location_ids['Birmingham'], "weather_condition": "Clear",
     "activity": "Birmingham Botanical Gardens",
     "recommendation": "Take a leisurely walk in the Birmingham Botanical Gardens under the clear sky."},
    {"location_id": location_ids['Birmingham'], "weather_condition": "Clouds",
     "activity": "Birmingham's Frankfurt Christmas Market",
     "recommendation": "Experience the magic of Birmingham's Christmas market."}
]

# Insert activities into the table
for activity in activities_data:
    new_activity = Activity(**activity)
    session.merge(new_activity)


session.commit()
session.close()
