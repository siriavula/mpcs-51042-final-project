
from turtle import down
from flask import Flask, request, render_template, send_file
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

api_key = '92eae2a76e7041fe86800920250303'
BASE_URL_CURRENT = 'http://api.weatherapi.com/v1/current.json'
BASE_URL_FORECAST = 'http://api.weatherapi.com/v1/forecast.json'
BASE_URL_HISTORICAL = 'https://api.weatherapi.com/v1/history.json'

cities = []


@app.route('/')
def index():
    return render_template('index.html')


def get_response_data(url, params):
    response = requests.get(url, params=params)
    response_data = response.json()

    if response.status_code == 200:
        return True, response_data
    else:
        return None, response_data.get('error', {}).get(
            'message', 'Unknown error')


def get_current_weather_data(data, weather):
    current_weather = data['current']
    weather = {
        'city': data['location']['name'],
        'local_time': data['location']['localtime'],
        'temperature_f': current_weather['temp_f'],
        'temperature_c': current_weather['temp_c'],
        'condition': current_weather['condition']['text'],
        'wind_speed_kph': current_weather['wind_kph'],
        'wind_speed_mph': current_weather['wind_mph'],
        'feels_like_c': current_weather['feelslike_c'],
        'feels_like_f': current_weather['feelslike_f'],
    }
    return weather


def get_current_and_forecast_data(data, weather, forecast):
    weather = get_current_weather_data(data, weather)
    weather_forecast_day = data['forecast']['forecastday']
    forecast = [{
        "date": day["date"],
        "max_temp": day["day"]["maxtemp_c"],
        "min_temp": day["day"]["mintemp_c"],
        "avg_temp": day["day"]["avgtemp_c"],
        "condition_text": day["day"]["condition"]["text"],
        "condition_icon": day["day"]["condition"]["icon"],
        "wind_speed": day["day"]["maxwind_kph"],
        "humidity": day["day"]["avghumidity"],
    }
        for day in weather_forecast_day
    ]
    return weather, forecast


@app.route('/current_and_forecast', methods=['GET', 'POST'])
def current_and_forecast():
    weather = None
    forecast = []
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        err, data = get_response_data(BASE_URL_FORECAST, params={
            'key': api_key, 'q': city, 'days': 7})

        if not err:
            error = data
        else:
            weather, forecast = get_current_and_forecast_data(
                data, weather, forecast)

    return render_template('index.html', weather=weather, forecast=forecast, error=error, active_tab='current_and_forecast')


@app.route('/historical', methods=['GET', 'POST'])
def historical():
    data = None
    location = ''
    date = None
    error = None
    date_valid = None
    if request.method == 'POST':
        location = request.form.get('location')
        date_str = request.form.get('date')

        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.today()
            one_week_ago = today - timedelta(days=7)

            if date > datetime.today() or date < one_week_ago:
                date_valid = 'User input date is an invalid input. Please ensure the date you enter is within the past 7 days.\nShowing weather data for today.'
                date = datetime.today()
        else:
            date = datetime.today()

        err, response_data = get_response_data(BASE_URL_HISTORICAL, params={
            'key': api_key, 'q': location, 'dt': date.strftime('%Y-%m-%d')})
        if not err:
            error = response_data
        else:
            data = response_data

    return render_template('index.html', data=data, date_valid=date_valid, error=error, location=location, date=date, active_tab='historical')


@app.route('/multiple_cities_data', methods=['GET', 'POST'])
def multiple_cities_data():
    weather = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        err, data = get_response_data(BASE_URL_CURRENT, params={
                                      'key': api_key, 'q': city})

        if not err:
            error = data
        else:
            weather = get_current_weather_data(data, weather)
            cities.append(weather)
    return render_template('index.html', cities=cities, error=error, active_tab='multiple_cities_data')


@app.route('/save_weather_data_file', methods=['GET'])
def save_weather_data_file():
    with open('weather_data.txt', 'w') as output:
        output.write(f'Weather Data for {datetime.today()} Request')
        output.write(
            '\n------------------------------------------------------------------')
        if cities:
            for city in cities:
                pass
                output.write(
                    f"\n{city['city']}\nCurrent Temperature - {city['temperature_f']} F / {city['temperature_c']} C, Feels like - {city['feels_like_f']} F / {city['feels_like_c']} C, Condition - {city['condition']}, Wind Speed - {city['wind_speed_kph']} kph / {city['wind_speed_mph']} mph")

    return send_file('weather_data.txt', as_attachment=True, download_name='weather_data.txt', mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True)
