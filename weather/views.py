from django.shortcuts import render, redirect, get_object_or_404
import requests
from django.conf import settings
from datetime import datetime
import pytz
from datetime import timezone, timedelta
import json
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FavoriteCity

def get_weather_data(city):
    """Fetch weather data from OpenWeatherMap API"""
    api_key = settings.OPENWEATHER_API_KEY
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'  
    }
    
    try:
        response = requests.get(base_url, params=params)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_country_name(country_code):
    """Convert country code to full country name"""
    countries = {
        'US': 'United States', 'GB': 'United Kingdom', 'UK': 'United Kingdom', 'FR': 'France', 'DE': 'Germany',
        'IT': 'Italy', 'ES': 'Spain', 'CN': 'China', 'JP': 'Japan', 'KR': 'South Korea', 'IN': 'India',
        'RU': 'Russia', 'BR': 'Brazil', 'CA': 'Canada', 'AU': 'Australia', 'NZ': 'New Zealand',
        'AE': 'United Arab Emirates', 'SA': 'Saudi Arabia', 'ZA': 'South Africa', 'MX': 'Mexico',
        'AR': 'Argentina', 'TH': 'Thailand', 'VN': 'Vietnam', 'MY': 'Malaysia', 'SG': 'Singapore',
        'ID': 'Indonesia', 'PH': 'Philippines', 'PK': 'Pakistan', 'TR': 'Turkey', 'IR': 'Iran',
        'EG': 'Egypt', 'NG': 'Nigeria', 'KE': 'Kenya', 'IL': 'Israel', 'SE': 'Sweden',
        'NO': 'Norway', 'FI': 'Finland', 'DK': 'Denmark', 'PL': 'Poland', 'UA': 'Ukraine',
        'GR': 'Greece', 'PT': 'Portugal', 'NL': 'Netherlands', 'BE': 'Belgium', 'CH': 'Switzerland',
        'AT': 'Austria', 'IE': 'Ireland'
    }
    return countries.get(country_code, country_code)

def get_default_country_for_city(city_name):
    """Map common European cities to their default country codes"""
    city_country_map = {
        'london': 'GB',
        'paris': 'FR',
        'rome': 'IT',
        'madrid': 'ES',
        'berlin': 'DE',
        'dublin': 'IE',
        'vienna': 'AT',
        'amsterdam': 'NL',
        'brussels': 'BE',
        'lisbon': 'PT',
        'athens': 'GR',
        'stockholm': 'SE',
        'oslo': 'NO',
        'copenhagen': 'DK',
        'helsinki': 'FI',
        'prague': 'CZ',
        'warsaw': 'PL',
        'budapest': 'HU',
        'milan': 'IT',
        'barcelona': 'ES',
        'munich': 'DE',
        'venice': 'IT',
        'florence': 'IT',
        'naples': 'IT',
    }
    return city_country_map.get(city_name.lower())

def home(request):
    context = {'weather': None, 'error': None}
    API_KEY = 'c7d91ccfcd3c32e8fb6ed4e7ed912852'
    
    
    if request.user.is_authenticated:
        context['favorite_cities'] = FavoriteCity.objects.filter(user=request.user).order_by('-created_at')
    
    if city := request.GET.get('city'):
        
        if not city.strip():
            context['error'] = "Please enter a city name."
        elif len(city) > 100:
            context['error'] = "City name is too long. Please enter a shorter name."
        else:
            try:
                # Clean up the city input
                city_parts = [part.strip() for part in city.split(',')]
                city_name = city_parts[0]
                
                # Validate city name
                if not city_name:
                    context['error'] = "Please enter a valid city name."
                elif not city_name.replace(' ', '').isalnum():
                    context['error'] = "City name contains invalid characters. Please use only letters, numbers, and spaces."
                else:
                    # Try with country code if provided, otherwise check default mapping
                    if len(city_parts) > 1:
                        country_code = city_parts[1].upper()
                        # Validate country code
                        if not country_code.isalpha() or len(country_code) > 3:
                            context['error'] = "Invalid country code. Please use a valid 2-3 letter country code."
                    else:
                        country_code = get_default_country_for_city(city_name)
                    
                    # Only proceed with API call if validation passed
                    if not context.get('error'):
                        # Build the query string
                        if country_code:
                            url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name},{country_code}&appid={API_KEY}&units=metric'
                        else:
                            url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric'
                        
                        response = requests.get(url)
                        data = response.json()
                        
                        if response.status_code == 200:
                            # Get timezone offset in seconds from API
                            timezone_offset = data['timezone']
                            
                            # Convert Unix timestamps to local time
                            sunrise_utc = datetime.fromtimestamp(data['sys']['sunrise'], timezone.utc)
                            sunset_utc = datetime.fromtimestamp(data['sys']['sunset'], timezone.utc)
                            
                            # Apply timezone offset
                            local_tz = timezone(timedelta(seconds=timezone_offset))
                            sunrise_local = sunrise_utc.astimezone(local_tz)
                            sunset_local = sunset_utc.astimezone(local_tz)
                            
                            # Format times for display
                            data['sys']['sunrise_formatted'] = sunrise_local.strftime('%I:%M %p')
                            data['sys']['sunset_formatted'] = sunset_local.strftime('%I:%M %p')
                            
                            # Convert wind speed from m/s to km/h and add wind direction
                            wind_speed_kmh = data['wind']['speed'] * 3.6
                            wind_deg = data.get('wind', {}).get('deg', 0)
                            
                            # Get wind direction
                            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                                        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                            index = round(wind_deg / (360 / len(directions))) % len(directions)
                            wind_direction = directions[index]
                            
                            # Add formatted wind data to the context
                            data['wind']['speed_kmh'] = round(wind_speed_kmh)
                            data['wind']['direction'] = wind_direction
                            
                            # Add timezone name for display
                            hours_offset = timezone_offset // 3600
                            minutes_offset = (abs(timezone_offset) % 3600) // 60
                            sign = '+' if timezone_offset >= 0 else '-'
                            data['timezone_name'] = f"UTC{sign}{abs(hours_offset):02d}:{minutes_offset:02d}"
                            
                            # Add full country name
                            data['sys']['country_name'] = get_country_name(data['sys']['country'])
                            
                            # Round the temperature to whole number
                            data['main']['temp'] = round(data['main']['temp'])
                            data['main']['feels_like'] = round(data['main']['feels_like'])
                            
                            # Check if this city is in user's favorites
                            if request.user.is_authenticated:
                                data['is_favorite'] = FavoriteCity.objects.filter(
                                    user=request.user,
                                    city_name=city_name,
                                    country_code=country_code
                                ).exists()
                            
                            context['weather'] = data
                        else:
                            error_message = data.get('message', '')
                            if 'city not found' in error_message.lower():
                                suggestions = [
                                    "Try adding a country code (e.g., Dublin,IE or Rome,IT)",
                                    "Check the spelling of the city name",
                                    "Use English names for cities",
                                    "For US cities, add ',US' (e.g., Dublin,US for Dublin, Ohio)"
                                ]
                                context['error'] = f"City not found. Suggestions:\n• " + "\n• ".join(suggestions)
                            else:
                                context['error'] = f"Error: {error_message.capitalize()}"
            except requests.RequestException:
                context['error'] = 'Unable to fetch weather data. Please try again later.'
            except Exception as e:
                context['error'] = 'An error occurred. Please try again.'
    
    return render(request, 'weather/home.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember')
        
        # Validate inputs
        errors = []
        
        # Username validation
        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        elif len(username) > 150:
            errors.append('Username is too long')
        
        # Password validation
        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        # If there are validation errors, return them
        if errors:
            return render(request, 'weather/login.html', {
                'error_message': 'Please correct the following errors:',
                'errors': errors,
                'username': username  # Return the username to preserve it
            })
        
        # Try to authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if the user is active
            if not user.is_active:
                return render(request, 'weather/login.html', {
                    'error_message': 'Your account is inactive. Please contact support.',
                    'username': username
                })
            
            # Log the user in
            login(request, user)
            
            # Set session expiry based on remember me checkbox
            if remember:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            # Redirect to the home page
            return redirect('weather:home')
        else:
            # Check if the username exists
            if User.objects.filter(username=username).exists():
                return render(request, 'weather/login.html', {
                    'error_message': 'Invalid password',
                    'username': username
                })
            else:
                return render(request, 'weather/login.html', {
                    'error_message': 'Username not found',
                    'username': username
                })
    
    return render(request, 'weather/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            return render(request, 'weather/register.html', {'error_message': 'Passwords do not match'})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'weather/register.html', {'error_message': 'Username already exists'})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'weather/register.html', {'error_message': 'Email already exists'})
        
        # Create new user
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        
        return redirect('weather:home')
    
    return render(request, 'weather/register.html')

def logout_view(request):
    logout(request)
    return redirect('weather:home')

@login_required
def add_favorite(request):
    if request.method == 'POST':
        city_name = request.POST.get('city_name', '').strip()
        country_code = request.POST.get('country_code', '').strip()
        
        # Validate inputs
        if not city_name:
            return JsonResponse({'status': 'error', 'message': 'City name is required'})
        
        if len(city_name) > 100:
            return JsonResponse({'status': 'error', 'message': 'City name is too long'})
        
        if not city_name.replace(' ', '').isalnum():
            return JsonResponse({'status': 'error', 'message': 'City name contains invalid characters'})
        
        if country_code and (not country_code.isalpha() or len(country_code) > 3):
            return JsonResponse({'status': 'error', 'message': 'Invalid country code'})
        
        # Check if already in favorites
        if FavoriteCity.objects.filter(user=request.user, city_name=city_name, country_code=country_code).exists():
            return JsonResponse({'status': 'error', 'message': 'City already in favorites'})
        
        # Add to favorites
        try:
            FavoriteCity.objects.create(
                user=request.user,
                city_name=city_name,
                country_code=country_code
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error adding to favorites: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def remove_favorite(request, favorite_id):
    try:
        favorite = get_object_or_404(FavoriteCity, id=favorite_id, user=request.user)
        favorite.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error removing favorite: {str(e)}'})

@login_required
def favorites(request):
    favorites = FavoriteCity.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'weather/favorites.html', {'favorites': favorites}) 