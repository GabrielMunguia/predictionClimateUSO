(
    ()=>{
        function getIconForRainProbability(probabilidad) {
            const icons = {
                0: '☀️',
                1: '🌧️',
                2: '⛅',
                3: '🌩️',
                4: '❄️'
            }
        
           
            const probabilidadValue = parseFloat(probabilidad.replace('%', ''));
            
            if (probabilidadValue === 0) {
                return icons[0]; // Clear
            } else if (probabilidadValue > 0 && probabilidadValue <= 20) {
                return icons[2]; // Cloudy
            } else if (probabilidadValue > 20 && probabilidadValue <= 50) {
                return icons[1]; // Rain
            } else if (probabilidadValue > 50 && probabilidadValue <= 80) {
                return icons[3]; // Thunderstorm
            } else {
                return icons[4]; // Snow
            }
        }
        document.addEventListener('DOMContentLoaded', function () {
            const apiUrl = 'http://127.0.0.1:8000/api/predict/';
       
            
            // Crear el contenedor principal con estilo moderno
            const weatherApp = document.createElement('div');
            weatherApp.style.cssText = `
                background: linear-gradient(135deg, #4284DB, #3475C5);
                max-width: 400px;
                margin: 20px auto;
                border-radius: 25px;
                padding: 20px;
                color: white;
                font-family: Arial, sans-serif;
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            `;
        
            // Sección principal del clima
            const mainWeather = document.createElement('div');
            mainWeather.style.cssText = `
                text-align: center;
                padding: 20px 0;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            `;
        
            // Temperatura actual
            const tempDisplay = document.createElement('h1');
            tempDisplay.style.cssText = `
                font-size: 72px;
                margin: 0;
                font-weight: 300;
            `;
            tempDisplay.innerHTML = '28<span style="font-size: 40px;">°</span>';
        
            // Detalles del clima
            const weatherDetails = document.createElement('div');
            weatherDetails.style.cssText = `
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 20px 0;
                padding: 10px;
            `;
        
            const details = [
                { icon: '💧', value: '', label: 'Humedad' },
                { icon: '🌪️', value: '', label: 'Radiacion solar' },
                { icon: '🌡️', value: '', label: 'Presión' }
            ];
        
            details.forEach(detail => {
                const detailBox = document.createElement('div');
                detailBox.style.cssText = `
                    text-align: center;
                    padding: 10px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                `;
                detailBox.innerHTML = `
                    <div style="font-size: 20px;">${detail.icon}</div>
                    <div style="font-size: 16px; font-weight: bold;">${detail.value}</div>
                    <div style="font-size: 12px; opacity: 0.8;">${detail.label}</div>
                `;
                weatherDetails.appendChild(detailBox);
            });
        
            // Pronóstico de días
            const forecast = document.createElement('div');
            forecast.style.cssText = `
            overflow-x: scroll;
            white-space: nowrap;
            padding: 20px 0;
            scrollbar-width: thin;
           
            scrollbar-color:rgb(3, 20, 43)  transparent; /* Esto cambia el color del scrollbar */
            cursor: grab;
            -ms-overflow-style: none;
            margin: 0 -20px;
            padding: 20px;
        
            /* Estilo para navegadores basados en Webkit (Chrome, Safari) */
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-thumb {
                background-color: blue; /* Color del thumb (parte que se mueve) */
                border-radius: 4px;
            }
            ::-webkit-scrollbar-track {
                background: transparent; /* Fondo del track */
            }
        `;
            forecast.addEventListener('wheel', (e) => {
                e.preventDefault();
                forecast.scrollLeft += e.deltaY;
            });
        
            
   
        
        
            // Ensamblar todo
            mainWeather.appendChild(tempDisplay);
            weatherApp.appendChild(mainWeather);
            weatherApp.appendChild(weatherDetails);
            weatherApp.appendChild(forecast);
        
            // Agregar al DOM
            document.body.appendChild(weatherApp);
        
            // Fetch data from API
            fetch(apiUrl, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
              
            })
            .then(response => response.json())
            .then(data => {
                if (data.predicciones && data.predicciones.length > 0) {
                    // Actualizar la temperatura actual
                    tempDisplay.innerHTML = `${data.predicciones[0].temperatura_predicha}<span style="font-size: 40px;">°</span>`;
                    // "humedad": 79,
                    // "presion_atmosferica": 1014.1,
                    //"radiacion_solar": 133.5
        
                    // Actualizar los detalles del Humedad, Viento y Presión
                    details[0].value = `${data.predicciones[0].humedad}%`;
                    details[1].value = `${data.predicciones[0].radiacion_solar} W/m²`;
                    details[2].value = `${data.predicciones[0].presion_atmosferica} hPa`;
        
                    details.forEach((detail, index) => {
                        weatherDetails.children[index].children[1].innerHTML = detail.value;
                    });
                  
                    
                    
                    // Actualizar el pronóstico
                    forecast.innerHTML = '';
                    data.predicciones.forEach(prediction => {
                        const dayForecast = document.createElement('div');
                        dayForecast.style.cssText = `
                            display: inline-block;
                            text-align: center;
                            margin-right: 25px;
                            background: rgba(255,255,255,0.1);
                            padding: 15px 25px;
                            border-radius: 15px;
                            min-width: 60px;
                        `;
                        
                        //"2025-01-03"
                        const date = new Date(prediction.fecha + 'T00:00:00'); // Añadimos una hora para asegurar la correcta interpretación de la fecha
                       
                        const dayName = date.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase();
                        console.log({dayName,date ,prediction});
                       
                        
                        dayForecast.innerHTML = `
                            <div style="font-size: 14px; margin-bottom: 8px;">${dayName}</div>
                            <div style="font-size: 24px; margin-bottom: 8px;">${getIconForRainProbability(prediction.probabilidad_lluvia)}</div>
                            <div style="font-size: 16px;">${prediction.temperatura_predicha}°</div>
                            <div style="font-size: 12px; opacity: 0.8;">${prediction.probabilidad_lluvia} lluvia</div>
                        `;
                        forecast.appendChild(dayForecast);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                weatherApp.innerHTML = '<p style="color: white; text-align: center;">Error al cargar los datos del clima</p>';
            });
        });
    }
)()