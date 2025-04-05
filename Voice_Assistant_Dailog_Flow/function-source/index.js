'use strict';

const functions = require('firebase-functions');
const { WebhookClient } = require('dialogflow-fulfillment');
const axios = require('axios');

process.env.DEBUG = 'dialogflow:debug'; // enables lib debugging statements

const API_KEY = '3128fbf6392f5c77b12e23d23ef80b76';

function callOpenWeatherMapAPI(endpoint, params) {
  const baseUrl = "http://api.openweathermap.org/data/2.5/";
  params.appid = API_KEY;
  if (Array.isArray(params.q)) {
    params.q = params.q[0];
  }
  console.log(`Calling OpenWeatherMap API: ${baseUrl}${endpoint} with params: ${JSON.stringify(params)}`);
  return axios.get(baseUrl + endpoint, { params });
}

function formatDate(dateString) {
  const options = { weekday: 'long', month: 'long', day: 'numeric' };
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', options);
}

function handleCheckWeatherIntent(agent) {
  const city = agent.parameters['geo-city'];
  const queryText = agent.query.toLowerCase();

  if (!city) {
    agent.setContext({ name: 'awaiting_city', lifespan: 1 });
    agent.add("Sure, I can help with that. Which city's weather would you like to know?");
    return;
  }

  return callOpenWeatherMapAPI('weather', { q: city }).then(response => {
    const weatherData = response.data;
    const temperature = (weatherData.main.temp - 273.15).toFixed(2); // Convert from Kelvin to Celsius
    const humidity = weatherData.main.humidity;
    const description = weatherData.weather[0].description;

    // Determine if the user needs an umbrella
    const needsUmbrella = description.includes('rain') || description.includes('drizzle') || description.includes('shower');
    
    // Custom responses based on the query
    let responseMessage;
    if (queryText.includes('sunny')) {
      if (description.includes('clear') || description.includes('sunny')) {
        responseMessage = `Yes, it is currently sunny in ${city}. The temperature is ${temperature}°C.`;
      } else {
        responseMessage = `No, it is not sunny in ${city}. It is ${description} with a temperature of ${temperature}°C.`;
      }
    } else if (queryText.includes('umbrella')) {
      if (needsUmbrella) {
        responseMessage = `Yes, you might want to take an umbrella as it is ${description} in ${city}.`;
      } else {
        responseMessage = `No, you probably don't need an umbrella as it is ${description} in ${city}.`;
      }
    } else if (queryText.includes('temperature') || queryText.includes('warm')) {
      responseMessage = `The current temperature in ${city} is ${temperature}°C.`;
    } else if (queryText.includes('humidity')) {
      responseMessage = `The current humidity in ${city} is ${humidity}%.`;
    } else if (queryText.includes('rain')) {
      if (description.includes('rain')) {
        responseMessage = `Yes, it is currently raining in ${city}. The temperature is ${temperature}°C.`;
      } else {
        responseMessage = `No, it is not raining in ${city}. It is ${description} with a temperature of ${temperature}°C.`;
      }
    } else if (queryText.includes('windy')) {
      responseMessage = `The current wind speed in ${city} is ${weatherData.wind.speed} meters per second.`;
    } else {
      responseMessage = `The current weather in ${city} is ${description} with a temperature of ${temperature}°C and humidity of ${humidity}%.`;
    }

    agent.add(responseMessage);
  }).catch(error => {
    console.error('Error calling weather API:', error.response ? error.response.data : error.message);
    agent.add(`I couldn't get the weather information for ${city}. Please try again later.`);
  });
}

function handleWeatherForecastIntent(agent) {
  const city = agent.parameters['geo-city'];
  const numDays = agent.parameters['number'] || 5; // Default to 5 days if not specified

  if (!city) {
    agent.setContext({ name: 'awaiting_city_forecast', lifespan: 1, parameters: { numDays } });
    agent.add("Sure, I can help with that. Which city's weather forecast would you like to know?");
    return;
  }

  return callOpenWeatherMapAPI('forecast', { q: city }).then(response => {
    const forecastData = response.data.list;
    let dailyForecasts = {};

    forecastData.forEach(entry => {
      const date = entry.dt_txt.split(' ')[0];
      const temp = entry.main.temp - 273.15; // Convert from Kelvin to Celsius
      const desc = entry.weather[0].description;

      if (!dailyForecasts[date]) {
        dailyForecasts[date] = [];
      }
      dailyForecasts[date].push({ temp, desc });
    });

    let summary = `The weather forecast for ${city} on:\n`;
    const dates = Object.keys(dailyForecasts).slice(0, numDays); // Limit the forecast to the specified number of days

    dates.forEach(date => {
      const dayEntries = dailyForecasts[date];
      const averageTemp = (dayEntries.reduce((sum, entry) => sum + entry.temp, 0) / dayEntries.length).toFixed(2);
      const commonDesc = dayEntries.map(entry => entry.desc).sort((a, b) =>
        dayEntries.filter(v => v === a).length - dayEntries.filter(v => v === b).length
      ).pop();
      summary += `${formatDate(date)}: ${commonDesc}, Avg Temp: ${averageTemp}°C\n`;
    });

    agent.add(summary);
  }).catch(error => {
    console.error('Error calling forecast API:', error.response ? error.response.data : error.message);
    agent.add(`I couldn't get the weather forecast for ${city}. Please try again later.`);
  });
}

function handleWeatherAlertsIntent(agent) {
  const city = agent.parameters['geo-city'];
  const alertType = agent.parameters.AlertType || 'emergencies'; // Default to 'emergencies' if not specified

  if (!city) {
    agent.setContext({ name: 'awaiting_city_alert', lifespan: 1, parameters: { alertType } });
    agent.add("Sure, I can help with that. Which city's weather alerts would you like to know?");
    return;
  }

  return callOpenWeatherMapAPI('forecast', { q: city }).then(response => {
    const forecastData = response.data.list;
    let relevantAlerts = forecastData.filter(entry => {
      const description = entry.weather[0].description.toLowerCase();
      return description.includes(alertType.toLowerCase()) || description.includes('storm') || description.includes('rain') || description.includes('snow');
    });

    if (relevantAlerts.length > 0) {
      let responseText = `There are ${relevantAlerts.length} weather alerts for ${city}:\n\n`;
      relevantAlerts.forEach(alert => {
        const date = new Date(alert.dt_txt).toLocaleString();
        responseText += `- ${alert.weather[0].description} expected on ${date}\n`;
      });
      agent.add(responseText);
    } else {
      agent.add(`There are no ${alertType} alerts for ${city} at the moment.`);
    }
  }).catch(error => {
    console.error('Error calling forecast API:', error.response ? error.response.data : error.message);
    agent.add(`I couldn't get the weather alerts for ${city}. Please try again later.`);
  });
}

function handleGoodMorningIntent(agent) {
  const city = agent.parameters['geo-city'];
  const dateTime = agent.parameters['date-time'];
  const timePeriod = agent.parameters['time-period'];

  if (!city) {
    agent.setContext({ name: 'awaiting_city_good_morning', lifespan: 1 });
    agent.add("Good morning! Which city's weather would you like to know?");
    return;
  }

  let dateDescription = "today";
  let targetDate = new Date();

  if (dateTime) {
    targetDate = new Date(dateTime);
    const now = new Date();
    if (targetDate.toDateString() === now.toDateString()) {
      dateDescription = "today";
    } else if (targetDate.toDateString() === new Date(now.setDate(now.getDate() + 1)).toDateString()) {
      dateDescription = "tomorrow";
    } else {
      dateDescription = targetDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    }
  }

  return callOpenWeatherMapAPI('forecast', { q: city }).then(response => {
    const forecastData = response.data.list;
    let morningWeather;

    for (let entry of forecastData) {
      const entryDate = entry.dt_txt.split(' ')[0];
      const entryTime = entry.dt_txt.split(' ')[1];

      if (new Date(entryDate).toDateString() === targetDate.toDateString() && entryTime.startsWith("06:00:00")) {
        morningWeather = entry;
        break;
      }
    }

    if (morningWeather) {
      const temperature = (morningWeather.main.temp - 273.15).toFixed(2);
      const description = morningWeather.weather[0].description;
      agent.add(`Good morning! The weather on ${dateDescription} morning in ${city} is ${description} with a temperature of ${temperature}°C. Have a great day!`);
    } else {
      agent.add(`Good morning! I couldn't get the weather information for ${city} on ${dateDescription} morning. Please try again later.`);
    }
  }).catch(error => {
    console.error('Error calling forecast API for morning weather:', error.response ? error.response.data : error.message);
    agent.add(`Good morning! I couldn't get the weather information for ${city}. Please try again later.`);
  });
}

function handleGoodNightIntent(agent) {
  const city = agent.parameters['geo-city'];
  const dateTime = agent.parameters['date-time'];

  if (!city) {
    agent.setContext({ name: 'awaiting_city_good_night', lifespan: 1 });
    agent.add("Good night! Which city's weather would you like to know?");
    return;
  }

  let dateDescription = "tonight";
  let targetDate = new Date();

  if (dateTime) {
    targetDate = new Date(dateTime);
    const now = new Date();
    if (targetDate.toDateString() === now.toDateString()) {
      dateDescription = "tonight";
    } else {
      dateDescription = targetDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    }
  }

  return callOpenWeatherMapAPI('forecast', { q: city }).then(response => {
    const forecastData = response.data.list;
    let nightWeather;

    for (let entry of forecastData) {
      const entryDate = new Date(entry.dt_txt);
      const entryTime = entry.dt_txt.split(' ')[1];

      if (entryDate.toDateString() === targetDate.toDateString() && (entryTime.startsWith("18:00:00") || entryTime.startsWith("21:00:00") || entryTime.startsWith("00:00:00") || entryTime.startsWith("03:00:00"))) {
        nightWeather = entry;
        break;
      }
    }

    if (nightWeather) {
      const temperature = (nightWeather.main.temp - 273.15).toFixed(2); // Convert from Kelvin to Celsius
      const description = nightWeather.weather[0].description;
      agent.add(`Good night! The weather ${dateDescription} in ${city} is expected to be ${description} with a temperature of ${temperature}°C. Sleep well!`);
    } else {
      agent.add(`Good night! I couldn't get the night weather information for ${city} ${dateDescription}. Please try again later.`);
    }
  }).catch(error => {
    console.error('Error calling forecast API for night weather:', error.response ? error.response.data : error.message);
    agent.add(`Good night! I couldn't get the weather information for ${city}. Please try again later.`);
  });
}

function handleWeatherTomorrowIntent(agent) {
  const city = agent.parameters['geo-city'];
  return callOpenWeatherMapAPI('forecast', { q: city }).then(response => {
    const forecastData = response.data.list;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowDate = tomorrow.toISOString().split('T')[0];
    let tomorrowForecast = forecastData.filter(entry => entry.dt_txt.split(' ')[0] === tomorrowDate);
    if (tomorrowForecast.length > 0) {
      const averageTemp = (tomorrowForecast.reduce((sum, entry) => sum + (entry.main.temp - 273.15), 0) / tomorrowForecast.length).toFixed(2);
      const commonDesc = tomorrowForecast.map(entry => entry.weather[0].description).sort((a, b) =>
        tomorrowForecast.filter(v => v === a).length - tomorrowForecast.filter(v => v === b).length
      ).pop();
      agent.add(`The weather in ${city} tomorrow is expected to be ${commonDesc} with an average temperature of ${averageTemp}°C.`);
    } else {
      agent.add(`I couldn't get the weather forecast for ${city} for tomorrow. Please try again later.`);
    }
  }).catch(error => {
    console.error('Error calling forecast API for tomorrow weather:', error.response ? error.response.data : error.message);
    agent.add(`I couldn't get the weather forecast for ${city} for tomorrow. Please try again later.`);
  });
}

function handleFallback(agent) {
  const context = agent.getContext('awaiting_city') || agent.getContext('awaiting_city_forecast') || agent.getContext('awaiting_city_alert') || agent.getContext('awaiting_city_good_morning') || agent.getContext('awaiting_city_good_night');
  
  if (context) {
    const city = agent.query;
    agent.parameters['geo-city'] = city;
    
    if (context.name === 'awaiting_city') {
      return handleCheckWeatherIntent(agent);
    } else if (context.name === 'awaiting_city_forecast') {
      agent.parameters['number'] = context.parameters.numDays;
      return handleWeatherForecastIntent(agent);
    } else if (context.name === 'awaiting_city_alert') {
      agent.parameters['AlertType'] = context.parameters.alertType;
      return handleWeatherAlertsIntent(agent);
    } else if (context.name === 'awaiting_city_good_morning') {
      return handleGoodMorningIntent(agent);
    } else if (context.name === 'awaiting_city_good_night') {
      return handleGoodNightIntent(agent);
    }
  }

  agent.add(`I'm sorry, I didn't understand that. Can you please specify the city you want the weather information for?`);
}

exports.dialogflowFirebaseFulfillment = functions.https.onRequest((request, response) => {
  const agent = new WebhookClient({ request, response });
  console.log('Dialogflow Request headers: ' + JSON.stringify(request.headers));
  console.log('Dialogflow Request body: ' + JSON.stringify(request.body));
 
  function welcome(agent) {
    agent.add(`Welcome to my agent!`);
  }
 
  function fallback(agent) {
    return handleFallback(agent);
  }

  let intentMap = new Map();
  intentMap.set('Default Welcome Intent', welcome);
  intentMap.set('Default Fallback Intent', fallback);
  intentMap.set('CheckWeatherIntent', handleCheckWeatherIntent);
  intentMap.set('WeatherForecastIntent', handleWeatherForecastIntent);
  intentMap.set('WeatherAlertsIntent', handleWeatherAlertsIntent);
  intentMap.set('GoodMorningIntent', handleGoodMorningIntent);
  intentMap.set('GoodNightIntent', handleGoodNightIntent);
  intentMap.set('WeatherTomorrowIntent', handleWeatherTomorrowIntent);
  
  agent.handleRequest(intentMap);
});
