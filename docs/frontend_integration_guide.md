# Rainfall Advisory API - Frontend Integration Guide

## API Endpoint
**POST** `https://rainfall-advisory-api.onrender.com/get-advisory`

## Request Payload
Send this JSON body to get the advisory:
```json
{
    "user_id": "postman_user",
    "gps_lat": 13.3409,
    "gps_long": 74.7421,
    "date": "2026-02-25"
}
```

## Response Structure (Dual-Language)
The API returns a JSON response where all user-facing text fields (messages, titles, actions) are provided in both **English (`en`)** and **Kannada (`kn`)**.

### Example Response
```json
{
	"status": "success",
	"main_status": {
		"title": {
			"en": "DROUGHT",
			"kn": "ಬರಗಾಲ"
		},
		"message": {
			"en": "ALERT: Dry spell continues. No rain in next 7 days. Start irrigation now.",
			"kn": "ಎಚ್ಚರಿಕೆ: ಮಳೆ ಇಲ್ಲ. ಮುಂದಿನ 7 ದಿನ ಒಣ ಹವೆ ಇರುತ್ತದೆ. ಕೂಡಲೇ ನೀರು ಹಾಯಿಸಿ."
		},
		"icon": "🚨",
		"priority": "HIGH",
		"color": "#D32F2F"
	},
	"rainfall": {
		"next_7_days": {
			"amount_mm": 0.0,
			"max_intensity": 0.0,
			"category": "Deficit"
		},
		"monthly_prediction": {
			"category": "Deficit",
			"confidence_percent": 66
		}
	},
	"what_to_do": {
		"title": {
			"en": "Advisory",
			"kn": "ಸಲಹೆ"
		},
		"advisory_summary": {
			"en": "🔴 *IRRIGATION ALERT*\n\nDry spell confirmed. No significant rain forecast for next 7 days.\n\n*Action:*\n- Start irrigation immediately\n- Conserve soil moisture",
			"kn": "🔴 *ನೀರಾವರಿ ಎಚ್ಚರಿಕೆ*\n\nಮುಂದಿನ 7 ದಿನ ಮಳೆ ಇಲ್ಲದಿರುವುದರಿಂದ ಒಣ ಹವೆ ಮುಂದುವರಿಯಲಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- ತಕ್ಷಣ ನೀರು ಹಾಯಿಸಿ\n- ಮಣ್ಣಿನ ತೇವಾಂಶ ಕಾಪಾಡಿಕೊಳ್ಳಿ"
		},
		"actions": {
			"immediate": [
				{
					"en": "💧 Plan irrigation for next 7 days",
					"kn": "💧 ಮುಂದಿನ 7 ದಿನಗಳಿಗೆ ನೀರು ಹಾಯಿಸಲು ಯೋಜಿಸಿ"
				},
				{
					"en": "💧 Mulch around plants to retain moisture",
					"kn": "💧 ತೇವಾಂಶ ಉಳಿಸಲು ಗಿಡಗಳ ಬುಡಕ್ಕೆ ಮಲ್ಚಿಂಗ್ ಮಾಡಿ"
				}
			],
			"this_week": [
				{
					"en": "Irrigate 2-3 times this week",
					"kn": "ಈ ವಾರ 2-3 ಬಾರಿ ನೀರು ಹಾಯಿಸಿ"
				}
			],
			"prepare": []
		},
		"priority_level": "HIGH"
	},
	"technical_details": {
		"ml_prediction": "Deficit",
		"confidence_scores": {
			"Deficit": 0.66,
			"Normal": 0.04,
			"Excess": 0.30
		},
		"model_version": "v2_calibrated",
		"forecast_available": true
	},
	"location": {
		"taluk": "udupi",
		"district": "Udupi",
		"confidence": "high"
	},
	"data_sources": {
		"weather_forecast": "live",
		"location_accuracy": "high",
		"last_updated": "2026-02-08T03:33:08.520672"
	}
}
```

## Flutter Integration (Dart)

### Parsing Logic
Use this helper function to extract the correct language string based on the user's preference.

```dart
String getLocalizedText(Map<String, dynamic> textObj, String languageCode) {
  // languageCode should be 'en' or 'kn'
  if (textObj != null && textObj.containsKey(languageCode)) {
    return textObj[languageCode];
  }
  // Fallback to English if the requested language is missing
  return textObj != null ? (textObj['en'] ?? '') : '';
}
```

### Example Usage
```dart
// Assume 'response' is the parsed JSON map from the API
Map<String, dynamic> mainStatus = response['main_status'];
Map<String, dynamic> messageObj = mainStatus['message']; // This is the {en, kn} map

// User's selected language (e.g., from a Provider or State)
String userLanguage = 'kn'; // or 'en'

// Display in UI
Text(
  getLocalizedText(messageObj, userLanguage),
  style: TextStyle(fontSize: 18),
);

// Displaying Actions List
List<dynamic> immediateActions = response['what_to_do']['actions']['immediate'];

ListView.builder(
  itemCount: immediateActions.length,
  itemBuilder: (context, index) {
    // specific action object {en: "...", kn: "..."}
    var actionObj = immediateActions[index]; 
    return ListTile(
      leading: Icon(Icons.water_drop),
      title: Text(getLocalizedText(actionObj, userLanguage)),
    );
  },
);
```

## Special Fields Checklist
Ensure your UI handles localization for:
- `main_status.title`
- `main_status.message`
- `what_to_do.title`
- `what_to_do.advisory_summary`
- `what_to_do.actions.immediate[]` (iterate and localize each item)
- `what_to_do.actions.this_week[]` (iterate and localize each item)
- `what_to_do.actions.prepare[]` (iterate and localize each item)
