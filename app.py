
from flask import Flask, request, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

BASE_URL_CURRENT = 'http://api.weatherapi.com/v1/current.json'
BASE_URL_FORECAST = 'http://api.weatherapi.com/v1/forecast.json'
BASE_URL_HISTORICAL = 'https://api.weatherapi.com/v1/history.json'

api_key = '92eae2a76e7041fe86800920250303'
cities = []


def get_weather_data(location, date):
    formatted_date = date.strftime('%Y-%m-%d')

    params = {
        'key': api_key,
        'q': location,
        'dt': formatted_date
    }
    response = requests.get(BASE_URL_HISTORICAL, params=params)

    # Return data as a dictionary
    return response.json()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tab1', methods=['GET', 'POST'])
def tab1():
    # current weather and forecast
    # need to include hourly data for that day
    # improve the UI
    weather = None
    forecast = []
    error = None

    if request.method == 'POST':
        city = request.form.get('city')

        params_current = {
            'key': api_key,
            'q': city,
            'days': 7,
            'aqi': 'no'
        }

        response = requests.get(BASE_URL_FORECAST, params=params_current)
        response_data = response.json()

        if response.status_code == 200:
            current_weather = response_data['current']

            weather = {
                'city': response_data['location']['name'],
                'local_time': response_data['location']['localtime'],
                'temperature_f': current_weather['temp_f'],
                'temperature_c': current_weather['temp_c'],
                'condition': current_weather['condition']['text'],
                'wind_speed_kph': current_weather['wind_kph'],
                'wind_speed_mph': current_weather['wind_mph'],
                'feels_like_c': current_weather['feelslike_c'],
                'feels_like_f': current_weather['feelslike_f'],
            }

            # CHANGE
            weather_forecast_day = response_data['forecast']['forecastday']
            for day in weather_forecast_day:
                date = day["date"]
                max_temp = day["day"]["maxtemp_c"]
                min_temp = day["day"]["mintemp_c"]
                avg_temp = day["day"]["avgtemp_c"]
                condition_text = day["day"]["condition"]["text"]
                condition_icon = day["day"]["condition"]["icon"]
                wind_speed = day["day"]["maxwind_kph"]
                humidity = day["day"]["avghumidity"]

                forecast.append({
                    "date": date,
                    "max_temp": max_temp,
                    "min_temp": min_temp,
                    "avg_temp": avg_temp,
                    "condition_text": condition_text,
                    "condition_icon": condition_icon,
                    "wind_speed": wind_speed,
                    "humidity": humidity,
                })
        else:
            error = response_data.get('error', {}).get(
                'message', 'Unknown error')

    return render_template('index.html', weather=weather, forecast=forecast, error=error, active_tab='Tab1')


@app.route('/tab2', methods=['GET', 'POST'])
def tab2():
    weather_data = None
    location = ''
    date = None

    if request.method == 'POST':
        # Get the location and date from the form
        location = request.form.get('location')
        date_str = request.form.get('date')

        # Convert the date string to a datetime object
        try:
            date = datetime.strptime(
                date_str, '%Y-%m-%d') if date_str else datetime.today()
        except ValueError:
            date = datetime.today()  # If invalid date, use today's date

        # Get the historical weather data
        weather_data = get_weather_data(location, date)

    return render_template('index.html', weather_data=weather_data, location=location, date=date, active_tab='Tab2')


@app.route('/tab3', methods=['GET', 'POST'])
def tab3():
    weather = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')

        params_current = {
            'key': api_key,
            'q': city,
        }

        response = requests.get(BASE_URL_FORECAST, params=params_current)
        response_data = response.json()

        if response.status_code == 200:
            current_weather = response_data['current']

            weather = {
                'city': response_data['location']['name'],
                'local_time': response_data['location']['localtime'],
                'temperature_f': current_weather['temp_f'],
                'temperature_c': current_weather['temp_c'],
                'condition': current_weather['condition']['text'],
                'wind_speed_kph': current_weather['wind_kph'],
                'wind_speed_mph': current_weather['wind_mph'],
                'feels_like_c': current_weather['feelslike_c'],
                'feels_like_f': current_weather['feelslike_f'],
            }

            cities.append(weather)

        else:
            error = response_data.get('error', {}).get(
                'message', 'Unknown error')

    return render_template('index.html', cities=cities, error=error, active_tab='Tab3', clear=clear)


if __name__ == '__main__':
    app.run(debug=True)
