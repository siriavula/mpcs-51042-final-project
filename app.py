from flask import Flask, request, render_template, send_file, session, redirect, url_for
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'weatherapp'
api_key = '92eae2a76e7041fe86800920250303'
BASE_URL_CURRENT = 'http://api.weatherapi.com/v1/current.json'
BASE_URL_FORECAST = 'http://api.weatherapi.com/v1/forecast.json'
BASE_URL_HISTORICAL = 'https://api.weatherapi.com/v1/history.json'


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
        'condition_img': current_weather['condition']['icon'],
        'wind_speed_kph': current_weather['wind_kph'],
        'wind_speed_mph': current_weather['wind_mph'],
        'feels_like_c': current_weather['feelslike_c'],
        'feels_like_f': current_weather['feelslike_f'],
        'humidity': current_weather['humidity']

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
            'key': api_key, 'q': city, 'days': 3})

        if not err:
            error = data
        else:
            weather, forecast = get_current_and_forecast_data(
                data, weather, forecast)

    return render_template('index.html', weather=weather, forecast=forecast, error=error, active_tab='current_and_forecast')


def get_historical_data(data, weather):
    weather = {
        'temperature_c': data['forecast']['forecastday'][0]['day']['avgtemp_c'],
        'temperature_f': data['forecast']['forecastday'][0]['day']['avgtemp_f'],
        'max_temperature_f': data['forecast']['forecastday'][0]['day']['maxtemp_f'],
        'max_temperature_c': data['forecast']['forecastday'][0]['day']['maxtemp_c'],
        'min_temperature_f': data['forecast']['forecastday'][0]['day']['mintemp_f'],
        'min_temperature_c': data['forecast']['forecastday'][0]['day']['mintemp_c'],
        'humidity': data['forecast']['forecastday'][0]['day']['avghumidity'],
        'condition': data['forecast']['forecastday'][0]['day']['condition']['text'],
        'condition_img': data['forecast']['forecastday'][0]['day']['condition']['icon'],
    }
    return weather


@app.route('/historical', methods=['GET', 'POST'])
def historical():
    weather = None
    data = None
    location = ''
    date = None
    historical_error = None
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
            historical_error = response_data
        else:
            data = get_historical_data(response_data, weather)

    return render_template('index.html', data=data, date_valid=date_valid, historical_error=historical_error, location=location, date=date, active_tab='historical')


@app.route('/multiple_cities_data', methods=['GET', 'POST'])
def multiple_cities_data():
    weather = None
    error = None
    invalid = None
    if 'cities' not in session:
        session['cities'] = []
    if request.method == 'POST':
        city = request.form.get('city')
        err, data = get_response_data(BASE_URL_CURRENT, params={
                                      'key': api_key, 'q': city})

        if not err:
            error = data
            invalid = 'User input city is invalid. Please ensure you enter a valid location.\nShowing previous weather data.'
        else:
            weather = get_current_weather_data(data, weather)
            session['cities'].append(weather)
            session.modified = True
    return render_template('index.html', cities=session['cities'], invalid=invalid, error=error, active_tab='multiple_cities_data')


@app.route('/save_weather_data_file', methods=['GET'])
def save_weather_data_file():
    with open('weather_data.txt', 'w') as output:
        output.write(f'Weather Data for {datetime.today()} Request')
        output.write(
            '\n------------------------------------------------------------------')
        if session['cities']:
            for city in session['cities']:
                output.write(
                    f"\n{city['city']}\nCurrent Temperature - {city['temperature_f']} F / {city['temperature_c']} C, Feels like - {city['feels_like_f']} F / {city['feels_like_c']} C, Condition - {city['condition']}, Wind Speed - {city['wind_speed_kph']} kph / {city['wind_speed_mph']} mph")
        else:
            output.write('\nNo weather data requested.')
    return send_file('weather_data.txt', as_attachment=True, download_name='weather_data.txt', mimetype='text/plain')


@app.route('/clear_weather_data', methods=['GET'])
def clear_weather_data():
    session['cities'] = []
    session.modified = True
    return redirect(url_for('multiple_cities_data'))


if __name__ == '__main__':
    app.run(debug=True)
