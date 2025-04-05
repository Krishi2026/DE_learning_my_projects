# Anya – Voice-Based Weather Assistant 🌤️🗣️

Anya is a conversational voice assistant designed using Google Dialogflow and powered by the OpenWeatherMap API. She provides real-time weather updates, multi-day forecasts, and severe weather alerts through natural voice interactions. Built as a part of the CS 466/566 course project, Anya aims to offer a friendly, reliable, and informative experience to users seeking weather insights.

---

## 🔧 Features

- **Current Weather**: Get real-time weather info (temperature, humidity, wind speed, and conditions).
- **Weather Forecast**: 3 to 7-day forecasts with temperature trends and precipitation.
- **Severe Weather Alerts**: Immediate warnings for storms, floods, or other alerts.
- **Morning & Night Updates**: Special intents for checking weather conditions during morning or night.
- **Tomorrow's Forecast**: Simple weather summaries for planning the next day.
- **Natural Language Support**: Understands a wide range of ways users ask about the weather.

---

## 🧠 Assistant Persona – "Anya"

- **Voice & Style**: Neutral American English with a friendly and calm demeanor.
- **Traits**: Informative, engaging, reassuring, and responsive.
- **Designed for**: Daily use, from checking if you need an umbrella to planning your weekend.

---

## 🛠️ Tech Stack

- **Dialogflow**: For natural language understanding and intent handling.
- **OpenWeatherMap API**: Provides current, forecast, and alert data.
- **Google Cloud Functions**: Used for webhook fulfillment.
- **Node.js**: Backend logic to process intent parameters and fetch weather data.
- **JSON**: Handles parameter extraction and API response parsing.

---

## 💬 Intents Implemented

1. **CheckWeatherIntent** – Real-time weather updates.
2. **WeatherForecastIntent** – Forecasts for upcoming days.
3. **WeatherAlertsIntent** – Reports on severe weather.
4. **GoodMorningIntent** – Tailored weather for mornings.
5. **GoodNightIntent** – Nighttime forecasts.
6. **WeatherTomorrowIntent** – Forecast for tomorrow.

Each intent is modular and fetches data using Dialogflow parameters and webhook fulfillment.

---

## 🔍 Sample Queries

- "What's the weather like in Portland?"
- "Give me the weather forecast for the next 3 days in Seattle."
- "Are there any weather alerts for Chicago?"
- "Good morning!"
- "Tell me the night forecast in New York."
- "Will it rain tomorrow in Austin?"

---

## 🧪 Usability Testing

Two testers evaluated Anya for:
- Accuracy
- Timeliness
- Ease of use

**Feedback**:
- ✅ Easy to use and effective
- ✅ Timely and informative responses
- 💡 Suggestions: Add variety to responses and include recommendations like clothing suggestions

---

## 🚀 Future Enhancements

- Personalized advice (e.g., “Take a raincoat!”)
- Visual interface and weather charts
- Push notifications or daily updates

---

## 🔗 Live Demo

Try it out on Dialogflow: [Launch Anya](https://bot.dialogflow.com/e1a72402-ae97-4b73-8349-1d115c327cca)

---

## 👤 Author

**Krishna Karthik Chava**  
Graduate Student | Oregon State University  
Course: CS 466/566 – Voice Assistants  
Project: Final Submission

---

## 📄 License

This project is for academic and demonstration purposes only.
