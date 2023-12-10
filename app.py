from flask import Flask, render_template, request, jsonify
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
import requests
import logging
from setup_database import Location, Activity, ChatbotTrainingData


app = Flask(__name__)

# SQLAlchemy setup to connect to the same database as used by setup_database.py and chatterbot
engine = create_engine('sqlite:///go_travel.db', connect_args={'check_same_thread': False})
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# ChatterBot setup
chatbot = ChatBot(
    'GoTravelBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///go_travel.db',
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': 'Which location would you like the weather forecast?',
            'maximum_similarity_threshold': 0.65
        }
    ]
)

# Create a new trainer for the chatbot
trainer = ChatterBotCorpusTrainer(chatbot)

logging.basicConfig(level=logging.INFO)


def train_chatbot_from_database(chatbot):
    trainer = ListTrainer(chatbot)
    session = Session()
    training_data = session.query(ChatbotTrainingData).all()
    for entry in training_data:
        trainer.train([entry.input_text, entry.response_text])
    session.close()
    logging.info("Training from database completed.")


trainer.train("chatterbot.corpus.english")
train_chatbot_from_database(chatbot)


# Function to read API key from given file path (with error/debug)
def get_api_key(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.readline().strip()
    except FileNotFoundError:
        print("The OPENWEATHER_API_KEY.txt file was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# API key management
file_path = '/Users/ciaria/PycharmProjects/Build_A_Chatbot/OPENWEATHER_API_KEY.txt'
API_KEY = get_api_key(file_path)


# Functions for handling weather requests
def get_weather(lat, lon):
    api_url = "https://api.openweathermap.org/data/3.0/onecall"
    parameters = {
        'lat': lat,
        'lon': lon,
        'units': 'metric',
        'exclude': 'minutely,hourly,alerts',
        'appid': API_KEY
    }
    response = requests.get(api_url, params=parameters)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Could not retrieve weather for {lat}, {lon}, HTTP {response.status_code}")
        return None


# Format the 7-day forecast data into a readable string
def format_7day_forecast(forecast_data):
    if forecast_data and 'daily' in forecast_data:
        forecast_days = forecast_data['daily'][1:8]
        forecast_message = ''
        for day in forecast_days:
            main_weather = day['weather'][0]['main']
            temp = day['temp']['min']

            forecast_message += f"{main_weather}. Temperature: {temp}°C\n"
        return forecast_message
    else:
        return "Couldn't get the forecast data."


def format_html_response(message):
    return message.replace("\n", "<br>")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        user_input = request.form.get('message', '').lower()  # Get the user input from the form
        if not user_input.strip():
            return jsonify({'response': 'Please enter a location for weather information.'})

        # Query the database for all locations
        session = Session()
        all_locations = session.query(Location).all()
        session.close()

        # Create a list of location names from the database
        location_names = [location.name.lower() for location in all_locations]

        # Check if the user message mentions any of the locations
        mentioned_locations = [location for location in location_names if location in user_input]

        if not mentioned_locations:
            # If no locations are mentioned, let the chatbot handle the message
            bot_response = str(chatbot.get_response(user_input))
            return jsonify({'response': bot_response})

        bot_responses = []
        for location_name in mentioned_locations:
            # Find the location object with the matching name
            location = next((loc for loc in all_locations if loc.name.lower() == location_name), None)
            if location:
                weather_data = get_weather(location.latitude, location.longitude)
                if weather_data:
                    # Create and format current weather condition response
                    current_weather = weather_data['current']
                    current_main = current_weather['weather'][0]['main']
                    temp = current_weather['temp']
                    current_weather_response = (
                        f"The current weather in {location.name.title()} is {current_main} "
                        f"with a temperature of {temp}°C."
                    )

                    # Process 7-day weather forecast
                    forecast_message = format_7day_forecast(weather_data)

                    # Fetch activity suggestions based on the current weather condition
                    activity_suggestion = get_activity_suggestion(location.id, current_main.lower())
                    if not activity_suggestion:
                        activity_suggestion = "No specific activity suggestion available for this weather condition."
                    else:
                        # If there is an activity suggestion, format the message
                        activity_suggestion = activity_suggestion

                    full_message = (
                        f"{current_weather_response}\n\n"
                        f"7-day Forecast:\n"
                        f"{forecast_message}\n\n"
                        f"Activity Suggestion:\n"
                        f"{activity_suggestion}"
                    )

                    # Append the current weather and forecast to the response list
                    bot_responses.append(full_message)

        # Join all responses for the mentioned locations into one string
        full_response = " ".join(bot_responses)
        return jsonify({'response': full_response})

    # This line should never be reached, but it's included as a fallback
    return jsonify({'response': 'Something went wrong with your request.'})


# Function to fetch activity suggestions from the database
def get_activity_suggestion(location_id, weather_condition):
    session = Session()
    suggestion = session.query(Activity).filter(
        Activity.location_id == location_id,
        func.lower(Activity.weather_condition) == func.lower(weather_condition)
    ).first()
    session.close()

    if suggestion:
        return suggestion.recommendation
    else:
        return "No activity suggestion available for this weather condition."


# Run the Flask app
if __name__ == '__main__':
    train_chatbot_from_database(chatbot)
    app.run(debug=True)
