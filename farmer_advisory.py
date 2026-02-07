#!/usr/bin/env python3
"""
Enhanced Farmer Advisory System
Provides actionable recommendations, not just predictions
"""

from datetime import datetime, timedelta
import requests

class FarmerAdvisory:
    """Generate farmer-friendly actionable advice"""
    
    # Crop water requirements (mm/month)
    CROP_WATER_NEEDS = {
        'paddy': {'low': 150, 'high': 200, 'critical_stage': 'flowering'},
        'coconut': {'low': 80, 'high': 120, 'critical_stage': 'summer'},
        'vegetables': {'low': 100, 'high': 150, 'critical_stage': 'fruiting'},
        'areca': {'low': 100, 'high': 140, 'critical_stage': 'summer'},
        'cashew': {'low': 60, 'high': 100, 'critical_stage': 'flowering'},
        'mango': {'low': 75, 'high': 110, 'critical_stage': 'flowering'}
    }
    
    def get_7day_forecast(self, lat, lon):
        """Get 7-day weather forecast from Open-Meteo"""
        try:
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'precipitation_sum,temperature_2m_max,temperature_2m_min',
                'timezone': 'Asia/Kolkata',
                'forecast_days': 7
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            forecast = []
            for i in range(7):
                forecast.append({
                    'date': data['daily']['time'][i],
                    'rain_mm': data['daily']['precipitation_sum'][i],
                    'temp_max': data['daily']['temperature_2m_max'][i],
                    'temp_min': data['daily']['temperature_2m_min'][i]
                })
            
            return forecast
        except Exception as e:
            print(f"Forecast error: {e}")
            return None
    
    def get_risk_level(self, category, confidence):
        """Convert prediction to simple risk level"""
        
        if category == 'Excess':
            if confidence >= 70:
                return 'HIGH', '🔴', 'Heavy rain very likely'
            elif confidence >= 50:
                return 'MEDIUM', '🟡', 'Heavy rain possible'
            else:
                return 'LOW', '🟢', 'Heavy rain unlikely'
        
        elif category == 'Deficit':
            if confidence >= 70:
                return 'HIGH', '🔴', 'Drought conditions very likely'
            elif confidence >= 50:
                return 'MEDIUM', '🟡', 'Dry conditions possible'
            else:
                return 'LOW', '🟢', 'Normal conditions likely'
        
        else:  # Normal
            return 'LOW', '🟢', 'Normal conditions expected'
    
    def get_actions_for_excess(self, confidence):
        """Actionable recommendations for excess rainfall"""
        actions = {
            'immediate': [],
            'this_week': [],
            'prepare': []
        }
        
        if confidence >= 60:
            actions['immediate'] = [
                '⚠️ Postpone fertilizer application',
                '⚠️ Harvest ready crops within 2-3 days',
                '⚠️ Prepare drainage channels',
                '⚠️ Store harvested grain indoors'
            ]
            actions['this_week'] = [
                'Check field drainage daily',
                'Monitor crops for waterlogging',
                'Apply fungicide if moisture persists'
            ]
        else:
            actions['prepare'] = [
                'Monitor weather updates daily',
                'Keep drainage tools ready',
                'Plan to harvest ripe crops if rain increases'
            ]
        
        return actions
    
    def get_actions_for_deficit(self, confidence):
        """Actionable recommendations for deficit rainfall"""
        actions = {
            'immediate': [],
            'this_week': [],
            'prepare': []
        }
        
        if confidence >= 60:
            actions['immediate'] = [
                '💧 Plan irrigation for next 7 days',
                '💧 Mulch around plants to retain moisture',
                '💧 Reduce water-intensive activities',
                '💧 Check irrigation equipment'
            ]
            actions['this_week'] = [
                'Irrigate 2-3 times this week',
                'Monitor soil moisture daily',
                'Avoid planting water-intensive crops'
            ]
        else:
            actions['prepare'] = [
                'Prepare irrigation backup plan',
                'Monitor soil moisture',
                'Wait before adding new crops'
            ]
        
        return actions
    
    def get_actions_for_normal(self):
        """Recommendations for normal conditions"""
        return {
            'this_week': [
                '✅ Proceed with normal farming activities',
                '✅ Good time for fertilizer application',
                '✅ Can plant new crops',
                '✅ Regular irrigation schedule'
            ]
        }
    
    def get_crop_specific_advice(self, category, monthly_rain_mm, crops=None):
        """Crop-specific recommendations"""
        if crops is None:
            crops = ['paddy', 'coconut', 'vegetables']  # Default Udupi crops
        
        advice = {}
        
        for crop in crops:
            if crop not in self.CROP_WATER_NEEDS:
                continue
            
            needs = self.CROP_WATER_NEEDS[crop]
            crop_advice = {
                'name': crop.title(),
                'water_need': 'HIGH' if monthly_rain_mm < needs['low'] else 'ADEQUATE',
                'actions': []
            }
            
            if category == 'Excess':
                if crop == 'paddy':
                    crop_advice['actions'] = [
                        'Ensure proper drainage',
                        'Monitor for pest diseases',
                        'Avoid fertilizer application'
                    ]
                elif crop == 'vegetables':
                    crop_advice['actions'] = [
                        'Cover with plastic during heavy rain',
                        'Apply fungicide preventively',
                        'Harvest ripe vegetables immediately'
                    ]
                elif crop == 'coconut':
                    crop_advice['actions'] = [
                        'No special action needed',
                        'Natural drainage sufficient'
                    ]
            
            elif category == 'Deficit':
                if crop == 'paddy':
                    crop_advice['actions'] = [
                        f'Irrigate 2-3 times per week',
                        'Especially important during flowering',
                        'Monitor for water stress'
                    ]
                elif crop == 'vegetables':
                    crop_advice['actions'] = [
                        'Daily irrigation required',
                        'Mulch to retain moisture',
                        'Consider drip irrigation'
                    ]
                elif crop == 'coconut':
                    crop_advice['actions'] = [
                        'Weekly watering if no rain',
                        'Focus on young palms',
                        'Mature trees can tolerate dry spell'
                    ]
            
            else:  # Normal
                crop_advice['actions'] = [
                    f'Normal watering schedule',
                    f'Good conditions for {crop}'
                ]
            
            advice[crop] = crop_advice
        
        return advice
    
    def generate_complete_advisory(self, prediction_result, lat, lon, crops=None):
        """Generate complete farmer advisory with all features"""
        
        if prediction_result['status'] != 'success':
            return {'error': 'Prediction failed'}
        
        # Extract prediction
        pred = prediction_result['rainfall']['monthly_prediction']
        category = pred['category']
        confidence = pred['confidence_percent']
        
        # Get 7-day forecast
        forecast_7day = self.get_7day_forecast(lat, lon)
        
        # Get risk level
        risk_level, risk_icon, risk_desc = self.get_risk_level(category, confidence)
        
        # Get general actions
        if category == 'Excess':
            actions = self.get_actions_for_excess(confidence)
        elif category == 'Deficit':
            actions = self.get_actions_for_deficit(confidence)
        else:
            actions = self.get_actions_for_normal()
        
        # Estimate monthly rainfall from prediction
        # This is approximate - would need actual prediction values
        estimated_rain = {
            'Excess': 150,
            'Normal': 80,
            'Deficit': 30
        }.get(category, 80)
        
        # Get crop-specific advice
        crop_advice = self.get_crop_specific_advice(category, estimated_rain, crops)
        
        # Build complete advisory
        advisory = {
            'prediction': {
                'category': category,
                'confidence': confidence,
                'risk_level': risk_level,
                'risk_icon': risk_icon,
                'risk_description': risk_desc
            },
            'forecast_7day': forecast_7day,
            'actions': actions,
            'crop_advice': crop_advice,
            'generated_at': datetime.now().isoformat()
        }
        
        return advisory
    
    def format_for_farmer(self, advisory, farmer_name='Farmer', language='en'):
        """Format advisory in farmer-friendly way"""
        
        pred = advisory['prediction']
        
        output = f"""
{'='*70}
🌾 FARMING ADVISORY - {datetime.now().strftime('%d %B %Y')}
{'='*70}

Namaste {farmer_name}!

📊 THIS MONTH'S FORECAST:
   {pred['risk_icon']} {pred['category'].upper()} rainfall predicted
   Confidence: {pred['confidence']}%
   Risk Level: {pred['risk_level']} - {pred['risk_description']}

"""
        
        # 7-day forecast
        if advisory.get('forecast_7day'):
            output += "📅 7-DAY WEATHER FORECAST:\n"
            for day in advisory['forecast_7day'][:7]:
                date_obj = datetime.fromisoformat(day['date'])
                day_name = date_obj.strftime('%a')
                rain_icon = '🌧️' if day['rain_mm'] > 10 else '🌦️' if day['rain_mm'] > 2 else '☀️'
                output += f"   {day_name} {date_obj.strftime('%d/%m')}: {rain_icon} {day['rain_mm']:.0f}mm, {day['temp_min']:.0f}-{day['temp_max']:.0f}°C\n"
            output += "\n"
        
        # Actions
        if 'immediate' in advisory['actions'] and advisory['actions']['immediate']:
            output += "🚨 IMMEDIATE ACTIONS:\n"
            for action in advisory['actions']['immediate']:
                output += f"   {action}\n"
            output += "\n"
        
        if 'this_week' in advisory['actions'] and advisory['actions']['this_week']:
            output += "📋 THIS WEEK:\n"
            for action in advisory['actions']['this_week']:
                output += f"   • {action}\n"
            output += "\n"
        
        if 'prepare' in advisory['actions'] and advisory['actions']['prepare']:
            output += "⚙️ PREPARE:\n"
            for action in advisory['actions']['prepare']:
                output += f"   • {action}\n"
            output += "\n"
        
        # Crop-specific
        if advisory.get('crop_advice'):
            output += "🌱 CROP-SPECIFIC ADVICE:\n\n"
            for crop, advice in advisory['crop_advice'].items():
                output += f"   {advice['name'].upper()}:\n"
                output += f"   Water need: {advice['water_need']}\n"
                for action in advice['actions']:
                    output += f"   • {action}\n"
                output += "\n"
        
        output += "="*70 + "\n"
        output += "💡 TIP: Check forecast again in 3-4 days\n"
        output += "📱 Questions? Contact agricultural officer\n"
        output += "="*70
        
        return output


if __name__ == '__main__':
    # Demo
    from production_backend import process_advisory_request
    
    print("Testing Enhanced Farmer Advisory System...")
    print()
    
    # Get prediction
    result = process_advisory_request('demo', 13.3409, 74.7421, '2026-02-07')
    
    # Generate advisory
    advisor = FarmerAdvisory()
    advisory = advisor.generate_complete_advisory(
        result, 
        lat=13.3409, 
        lon=74.7421,
        crops=['paddy', 'coconut', 'vegetables']
    )
    
    # Format for farmer
    formatted = advisor.format_for_farmer(advisory, farmer_name='Ravi Kumar')
    print(formatted)
