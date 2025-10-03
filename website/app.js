// Traffic Analytics Dashboard - JavaScript
// GitHub Pages implementation with Tailscale API integration
// Clean logging output without emoji characters

class TrafficDashboard {
    constructor() {
        // Check for old HTTP URL and update to HTTPS
        const storedUrl = localStorage.getItem('api-url');
        if (storedUrl && (storedUrl.includes('http://100.121.231.16:5000') || storedUrl.includes(':8443'))) {
            localStorage.setItem('api-url', 'https://edge-traffic-monitoring.taild46447.ts.net/api');
        }

        this.apiBaseUrl = localStorage.getItem('api-url') || 'https://edge-traffic-monitoring.taild46447.ts.net/api';
        this.isOnline = false;
        this.charts = {};
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupCharts();
        this.showDataUnavailable(); // Show data unavailable until API connects
        this.checkApiConnection();
        
        // Start refresh timer if API is configured
        if (this.apiBaseUrl) {
            this.startRefreshTimer();
        }
    }
    
    degreesToCompass(degrees) {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const targetTab = e.currentTarget.dataset.tab;
                this.switchTab(targetTab);
            });
        });
        
        // Time filter buttons
        document.querySelectorAll('.time-filter').forEach(filter => {
            filter.addEventListener('click', (e) => {
                document.querySelectorAll('.time-filter').forEach(f => f.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                const period = e.currentTarget.dataset.period;
                this.updateTrafficChart(period);
            });
        });
        
        // API configuration
        document.getElementById('connect-btn').addEventListener('click', () => {
            document.getElementById('api-modal').style.display = 'block';
        });
        
        document.querySelector('.close').addEventListener('click', () => {
            document.getElementById('api-modal').style.display = 'none';
        });
        
        document.getElementById('test-connection').addEventListener('click', () => {
            this.testApiConnection();
        });
        
        // Location selector (if exists)
        const locationSelector = document.getElementById('location');
        if (locationSelector) {
            locationSelector.addEventListener('change', (e) => {
                this.filterByLocation(e.target.value);
            });
        }
        
        // Export buttons functionality
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const buttonText = btn.textContent.trim();
                if (buttonText === 'Download HTML') {
                    this.downloadMonthlyReport();
                } else if (buttonText === 'Download CSV') {
                    this.downloadViolationsReport();
                } else {
                    this.showNotImplemented('Export functionality');
                }
            });
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('api-modal');
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    switchTab(tabName) {
        // Stop events manager if switching away from events tab
        if (this.eventsManager && this.currentTab === 'events' && tabName !== 'events') {
            this.eventsManager.stop();
        }
        
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
        // Remember current tab
        this.currentTab = tabName;
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }
    
    setupCharts() {
        // Traffic Volume Chart
        const trafficCtx = document.getElementById('traffic-volume-chart');
        if (trafficCtx) {
            this.charts.traffic = new Chart(trafficCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Vehicle Count',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        }
                    }
                }
            });
        }
        
        // Speed Distribution Chart
        const speedCtx = document.getElementById('speed-distribution-chart');
        if (speedCtx) {
            this.charts.speed = new Chart(speedCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Under Limit', 'Over Limit', 'Significantly Over'],
                    datasets: [{
                        data: [70, 25, 5],
                        backgroundColor: [
                            '#48bb78',
                            '#ed8936',
                            '#f56565'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    }
                }
            });
        }
    }
    
    async checkApiConnection() {
        if (!this.apiBaseUrl) {
            this.updateApiStatus(false, 'No API URL configured');
            return;
        }
        
        try {
            // Try the basic health endpoint first (more reliable)
            let response = await fetch(`${this.apiBaseUrl.replace('/api', '')}/health`, {
                timeout: 5000
            });
            
            if (response.ok) {
                this.updateApiStatus(true);
                this.loadRealData();
                return;
            }
            
            // Fallback to system health endpoint
            response = await fetch(`${this.apiBaseUrl}/health/system`, {
                timeout: 5000
            });
            
            if (response.ok) {
                this.updateApiStatus(true);
                this.loadRealData();
            } else {
                this.updateApiStatus(false, `API returned ${response.status}`);
            }
        } catch (error) {
            console.log('API connection failed:', error);
            
            // Check if this is a mixed content error (HTTPS to HTTP)
            if (error.message.includes('Failed to fetch') && location.protocol === 'https:' && this.apiBaseUrl.startsWith('http:')) {
                this.updateApiStatus(false, 'Mixed Content Error: Cannot connect to HTTP API from HTTPS site. Please visit the API directly at https://edge-traffic-monitoring.taild46447.ts.net/docs/');
            } else {
                this.updateApiStatus(false, `Connection failed: ${error.message}`);
            }
        }
    }
    
    async testApiConnection() {
        const apiUrl = document.getElementById('api-url').value.trim();
        const statusDiv = document.getElementById('connection-status');
        
        if (!apiUrl) {
            statusDiv.textContent = 'Please enter an API URL';
            statusDiv.style.background = '#fed7d7';
            statusDiv.style.color = '#c53030';
            return;
        }
        
        statusDiv.textContent = 'Testing connection...';
        statusDiv.style.background = '#e2e8f0';
        statusDiv.style.color = '#4a5568';
        
        try {
            // Try the basic health endpoint first (more reliable)
            let response = await fetch(`${apiUrl.replace('/api', '')}/health`, {
                timeout: 10000
            });
            
            let data = { status: 'healthy' };
            
            if (response.ok) {
                data = await response.json();
            } else {
                // Fallback to system health endpoint
                response = await fetch(`${apiUrl}/health/system`, {
                    timeout: 10000
                });
                
                if (response.ok) {
                    data = await response.json();
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
            
            this.apiBaseUrl = apiUrl;
            localStorage.setItem('api-url', apiUrl);
            
            statusDiv.textContent = `Connected! System status: ${data.status || 'OK'}`;
            statusDiv.style.background = '#c6f6d5';
            statusDiv.style.color = '#276749';
            
            this.updateApiStatus(true);
            this.loadRealData();
            this.startRefreshTimer();
            
            setTimeout(() => {
                document.getElementById('api-modal').style.display = 'none';
            }, 2000);
        } catch (error) {
            statusDiv.textContent = `Connection failed: ${error.message}`;
            statusDiv.style.background = '#fed7d7';
            statusDiv.style.color = '#c53030';
        }
    }
    
    updateApiStatus(isOnline, errorMessage = null) {
        this.isOnline = isOnline;
        const indicator = document.getElementById('api-indicator');
        const connectBtn = document.getElementById('connect-btn');
        
        if (isOnline) {
            indicator.className = 'status-indicator online';
            indicator.querySelector('.status-text').textContent = 'API Connected';
            connectBtn.textContent = 'Reconfigure';
        } else {
            indicator.className = 'status-indicator offline';
            // Show error message if provided, otherwise default message
            const statusText = errorMessage || 'API Offline';
            indicator.querySelector('.status-text').textContent = statusText;
            connectBtn.textContent = 'Configure API';
        }
    }
    
    async loadRealData() {
        if (!this.isOnline) {
            this.showDataUnavailable();
            return;
        }
        
        console.log('Loading real data from API...');
        
        try {
            // Load recent vehicle detections (last 24 hours using consolidated endpoint)
            try {
                const since24HoursAgo = new Date();
                since24HoursAgo.setHours(since24HoursAgo.getHours() - 24);
                const sinceTimestamp = since24HoursAgo.toISOString();
                
                const detectionsResponse = await fetch(`${this.apiBaseUrl}/vehicles/consolidated?since=${sinceTimestamp}&limit=1000`);
                if (detectionsResponse.ok) {
                    const detectionsData = await detectionsResponse.json();
                    this.updateVehicleCountFrom24Hours(detectionsData);
                    console.log('Vehicle detections (24h) loaded successfully');
                } else {
                    console.error(`Detections API failed: ${detectionsResponse.status}`);
                    document.getElementById('total-vehicles').textContent = `Error ${detectionsResponse.status}`;
                }
            } catch (error) {
                console.error('Detections API error:', error.message);
                document.getElementById('total-vehicles').textContent = 'API Error';
            }
            
            // Load recent speed data (last 24 hours)
            try {
                const speedsResponse = await fetch(`${this.apiBaseUrl}/analytics/speeds?seconds=86400`);
                if (speedsResponse.ok) {
                    const speedsData = await speedsResponse.json();
                    this.updateSpeedMetrics(speedsData);
                    console.log('Speed data loaded successfully');
                } else {
                    console.error(`Speeds API failed: ${speedsResponse.status}`);
                    document.getElementById('avg-speed').textContent = `Error ${speedsResponse.status}`;
                    document.getElementById('speed-violations').textContent = `Error ${speedsResponse.status}`;
                }
            } catch (error) {
                console.error('Speeds API error:', error.message);
                document.getElementById('avg-speed').textContent = 'API Error';
                document.getElementById('speed-violations').textContent = 'API Error';
            }
            
            // Load analytics data
            try {
                const analyticsResponse = await fetch(`${this.apiBaseUrl}/analytics/summary`);
                if (analyticsResponse.ok) {
                    const analyticsData = await analyticsResponse.json();
                    this.updateAnalyticsFromData(analyticsData);
                    console.log('Analytics data loaded successfully');
                } else {
                    console.error(`Analytics API failed: ${analyticsResponse.status}`);
                }
            } catch (error) {
                console.error('Analytics API error:', error.message);
            }
            
            // Load weather data from the consolidated endpoint (latest detection)
            try {
                const weatherResponse = await fetch(`${this.apiBaseUrl}/vehicles/consolidated?limit=1`);

                if (weatherResponse.ok) {
                    const consolidatedData = await weatherResponse.json();
                    let combinedWeatherData = {};
                    let hasValidData = false;

                    // Extract weather data from the most recent vehicle detection
                    if (consolidatedData.events && consolidatedData.events.length > 0) {
                        const latestEvent = consolidatedData.events[0];
                        
                        // Process local weather data (DHT22 sensor)
                        if (latestEvent.weather_data && latestEvent.weather_data.dht22) {
                            const dht22Data = latestEvent.weather_data.dht22;
                            
                            // Handle both new format (temperature_c/temperature_f) and old format (temperature)
                            if (dht22Data.temperature_c !== undefined && dht22Data.temperature_f !== undefined) {
                                // New format - server provides both
                                combinedWeatherData.temperature_c = dht22Data.temperature_c;
                                combinedWeatherData.temperature_f = dht22Data.temperature_f;
                            } else if (dht22Data.temperature !== undefined) {
                                // Old format - temperature is in Celsius, convert to Fahrenheit
                                combinedWeatherData.temperature_c = dht22Data.temperature;
                                combinedWeatherData.temperature_f = (dht22Data.temperature * 9/5) + 32;
                            }
                            
                            combinedWeatherData.humidity = dht22Data.humidity;
                            hasValidData = true;
                            console.log('Local weather data (DHT22) loaded from consolidated endpoint');
                            console.log(`Temperature: ${combinedWeatherData.temperature_c}C (${Math.round(combinedWeatherData.temperature_f)}F)`);
                        }

                        // Process airport weather data (if available in future)
                        if (latestEvent.weather_data && latestEvent.weather_data.airport) {
                            const airportData = latestEvent.weather_data.airport;
                            combinedWeatherData.airport_temperature_f = airportData.temperature_f; // Use correct Fahrenheit field
                            combinedWeatherData.airport_temperature_c = airportData.temperature_c || airportData.temperature; // Celsius fallback
                            combinedWeatherData.weather_description = airportData.textDescription;
                            combinedWeatherData.sky_condition = airportData.cloudLayers;
                            
                            // Add wind data processing
                            if (airportData.windSpeed !== undefined && airportData.windSpeed !== null) {
                                // Convert from km/h to mph
                                combinedWeatherData.wind_speed_mph = Math.round(airportData.windSpeed * 0.621371 * 10) / 10; // Round to 1 decimal
                                combinedWeatherData.wind_speed_kmh = airportData.windSpeed;
                            }
                            if (airportData.windDirection !== undefined && airportData.windDirection !== null) {
                                combinedWeatherData.wind_direction = airportData.windDirection;
                                combinedWeatherData.wind_direction_compass = this.degreesToCompass(airportData.windDirection);
                            }
                            
                            hasValidData = true;
                            console.log('Airport weather data loaded from consolidated endpoint');
                            console.log(`Airport temperature: ${airportData.temperature_c}C (${Math.round(airportData.temperature_f)}F)`);
                            if (combinedWeatherData.wind_speed_mph) {
                                console.log(`Wind: ${combinedWeatherData.wind_speed_mph} mph from ${combinedWeatherData.wind_direction_compass} (${combinedWeatherData.wind_direction})`);
                            }
                        }
                    }

                    if (hasValidData) {
                        this.updateWeatherData(combinedWeatherData);
                        console.log('Weather data processed successfully from consolidated endpoint');
                    } else {
                        console.error('No valid weather data in consolidated endpoint');
                        document.getElementById('airport-temp').textContent = 'No Data';
                        document.getElementById('local-temp').textContent = 'No Data';
                        document.getElementById('local-humidity').textContent = 'No Data';
                    }
                } else {
                    console.error(`Consolidated API failed: ${weatherResponse.status}`);
                    document.getElementById('airport-temp').textContent = 'API Error';
                    document.getElementById('local-temp').textContent = 'API Error';
                    document.getElementById('local-humidity').textContent = 'API Error';
                }
            } catch (error) {
                console.error('Consolidated API error:', error.message);
                document.getElementById('airport-temp').textContent = 'API Error';
                document.getElementById('local-temp').textContent = 'API Error';
                document.getElementById('local-humidity').textContent = 'API Error';
            }
            
            // Load traffic volume chart with default 24h period
            this.updateTrafficChart('24h');
            
            // Update camera snapshot
            this.updateCameraSnapshot();
            
        } catch (error) {
            console.error('Critical error loading real data:', error);
            this.updateApiStatus(false);
            this.showDataUnavailable();
        }
    }
    
    updateMetricsFromData(data) {
        if (!data || data.length === 0) return;
        
        // Calculate metrics from real data
        const totalVehicles = data.reduce((sum, record) => sum + (record.vehicle_count || 0), 0);
        const speeds = data.filter(r => r.radar_speed).map(r => r.radar_speed);
        const avgSpeed = speeds.length > 0 ? (speeds.reduce((a, b) => a + b, 0) / speeds.length).toFixed(1) : 0;
        const violations = data.filter(r => r.radar_speed && r.radar_speed > 25).length;
        const latestTemp = data.find(r => r.air_temperature)?.air_temperature;
        
        // Update UI
        document.getElementById('total-vehicles').textContent = totalVehicles.toLocaleString();
        document.getElementById('avg-speed').textContent = avgSpeed;
        document.getElementById('speed-violations').textContent = violations;
        if (latestTemp) {
            document.getElementById('local-temp').textContent = `${Math.round(latestTemp * 9/5 + 32)} F`;
        }
    }
    
    updateTrafficChartFromData(data) {
        if (!data || data.length === 0 || !this.charts.traffic) return;
        
        // Group data by hour
        const hourlyData = {};
        data.forEach(record => {
            const hour = new Date(record.timestamp).getHours();
            hourlyData[hour] = (hourlyData[hour] || 0) + (record.vehicle_count || 0);
        });
        
        const labels = Object.keys(hourlyData).sort((a, b) => a - b).map(h => `${h}:00`);
        const values = labels.map(label => hourlyData[parseInt(label)]);
        
        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = values;
        this.charts.traffic.update();
    }
    
    updateAnalyticsFromData(data) {
        if (!data || !data.statistics) return;
        
        // Update speed distribution chart
        if (this.charts.speed && data.statistics.total_records > 0) {
            const underLimit = Math.round((data.statistics.total_records - (data.statistics.speed_violations || 0)) / data.statistics.total_records * 100);
            const violations = Math.round((data.statistics.speed_violations || 0) / data.statistics.total_records * 100);
            const severe = Math.max(0, violations - 15); // Estimate severe violations
            
            this.charts.speed.data.datasets[0].data = [underLimit, violations - severe, severe];
            this.charts.speed.update();
        }
    }
    
    updateMetricsFromDetections(detectionsData) {
        if (!detectionsData) {
            console.error('No detections data received');
            document.getElementById('total-vehicles').textContent = 'No Data';
            return;
        }
        
        if (!detectionsData.detections || !Array.isArray(detectionsData.detections)) {
            console.error('Invalid detections data format:', detectionsData);
            document.getElementById('total-vehicles').textContent = 'Invalid Data';
            return;
        }
        
        const detections = detectionsData.detections;
        const totalVehicles = detections.length;
        
        // Update vehicle count
        document.getElementById('total-vehicles').textContent = totalVehicles.toLocaleString();
        console.log(`Updated vehicle count: ${totalVehicles}`);
        
        // Update chart with hourly detection data
        this.updateTrafficChartFromDetections(detections);
    }
    
    updateVehicleCountFrom24Hours(consolidatedData) {
        if (!consolidatedData || !consolidatedData.events) {
            console.error('No consolidated data received for 24h vehicle count');
            document.getElementById('total-vehicles').textContent = 'No Data';
            return;
        }
        
        const events = consolidatedData.events;
        const totalVehicles24h = events.length;
        
        // Update vehicle count for last 24 hours
        document.getElementById('total-vehicles').textContent = totalVehicles24h.toLocaleString();
        console.log(`Updated 24h vehicle count: ${totalVehicles24h}`);
        
        // Calculate average speed for last 24 hours
        const speedEvents = events.filter(event => 
            event.radar_data && 
            event.radar_data.speed !== undefined && 
            event.radar_data.speed !== null && 
            event.radar_data.speed > 0
        );
        
        if (speedEvents.length > 0) {
            const speeds = speedEvents.map(event => event.radar_data.speed);
            const totalSpeed = speeds.reduce((sum, speed) => sum + speed, 0);
            const avgSpeed24h = totalSpeed / speedEvents.length;
            const minSpeed = Math.min(...speeds);
            const maxSpeed = Math.max(...speeds);
            
            document.getElementById('avg-speed').textContent = avgSpeed24h.toFixed(1);
            document.getElementById('min-speed').textContent = minSpeed.toFixed(1);
            document.getElementById('max-speed').textContent = maxSpeed.toFixed(1);
            
            console.log(` Updated 24h speed metrics: avg=${avgSpeed24h.toFixed(1)} mph, min=${minSpeed.toFixed(1)} mph, max=${maxSpeed.toFixed(1)} mph (from ${speedEvents.length} speed readings)`);
            
            // Count speed violations (25+ mph) in last 24 hours
            const violations24h = speedEvents.filter(event => event.radar_data.speed > 25).length;
            document.getElementById('speed-violations').textContent = violations24h;
            
            // Apply high alert styling if violations detected
            const violationsCard = document.getElementById('violations-card');
            if (violations24h > 0) {
                violationsCard.classList.add('high-alert');
            } else {
                violationsCard.classList.remove('high-alert');
            }
            
            console.log(` Updated 24h speed violations: ${violations24h} (out of ${speedEvents.length} readings)`);
        } else {
            document.getElementById('avg-speed').textContent = 'No Data';
            document.getElementById('min-speed').textContent = '0';
            document.getElementById('max-speed').textContent = '0';
            document.getElementById('speed-violations').textContent = '0';
            console.log('No speed data available for 24h average');
        }
        
        // Calculate trend vs previous 24 hours (if we have enough data)
        const now = new Date();
        const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const previous24h = new Date(now.getTime() - 48 * 60 * 60 * 1000);
        
        const currentPeriodEvents = events.filter(event => {
            const eventTime = new Date(event.created_at || event.timestamp);
            return eventTime >= last24h && eventTime <= now;
        });
        
        const previousPeriodEvents = events.filter(event => {
            const eventTime = new Date(event.created_at || event.timestamp);
            return eventTime >= previous24h && eventTime < last24h;
        });
        
        const currentCount = currentPeriodEvents.length;
        const previousCount = previousPeriodEvents.length;
        
        // Update trend indicator
        const trendElement = document.getElementById('vehicles-trend');
        if (trendElement && previousCount > 0) {
            const changePercent = Math.round(((currentCount - previousCount) / previousCount) * 100);
            if (changePercent > 0) {
                trendElement.textContent = `${changePercent}% vs yesterday`;
                trendElement.className = 'metric-trend positive';
            } else if (changePercent < 0) {
                trendElement.textContent = `${Math.abs(changePercent)}% vs yesterday`;
                trendElement.className = 'metric-trend negative';
            } else {
                trendElement.textContent = 'Same as yesterday';
                trendElement.className = 'metric-trend neutral';
            }
        } else if (trendElement) {
            trendElement.textContent = 'No comparison data';
            trendElement.className = 'metric-trend neutral';
        }
        
        // Calculate speed trend between periods
        if (currentPeriodEvents.length > 0 && previousPeriodEvents.length > 0) {
            const currentSpeedEvents = currentPeriodEvents.filter(event => 
                event.radar_data && 
                event.radar_data.speed !== undefined && 
                event.radar_data.speed !== null && 
                event.radar_data.speed > 0
            );
            
            const previousSpeedEvents = previousPeriodEvents.filter(event => 
                event.radar_data && 
                event.radar_data.speed !== undefined && 
                event.radar_data.speed !== null && 
                event.radar_data.speed > 0
            );
            
            const speedTrendElement = document.getElementById('speed-trend');
            
            if (speedTrendElement && currentSpeedEvents.length > 0 && previousSpeedEvents.length > 0) {
                const currentAvgSpeed = currentSpeedEvents.reduce((sum, event) => sum + event.radar_data.speed, 0) / currentSpeedEvents.length;
                const previousAvgSpeed = previousSpeedEvents.reduce((sum, event) => sum + event.radar_data.speed, 0) / previousSpeedEvents.length;
                
                const speedChangePercent = Math.round(((currentAvgSpeed - previousAvgSpeed) / previousAvgSpeed) * 100);
                
                if (speedChangePercent > 0) {
                    speedTrendElement.textContent = `${speedChangePercent}% vs yesterday`;
                    speedTrendElement.className = 'metric-trend positive';
                } else if (speedChangePercent < 0) {
                    speedTrendElement.textContent = `${Math.abs(speedChangePercent)}% vs yesterday`;
                    speedTrendElement.className = 'metric-trend negative';
                } else {
                    speedTrendElement.textContent = 'Same as yesterday';
                    speedTrendElement.className = 'metric-trend neutral';
                }
                console.log(`Speed trend: ${speedChangePercent}% (current: ${currentAvgSpeed.toFixed(1)}, previous: ${previousAvgSpeed.toFixed(1)})`);
            } else if (speedTrendElement) {
                speedTrendElement.textContent = 'No comparison data';
                speedTrendElement.className = 'metric-trend neutral';
            }
        } else {
            const speedTrendElement = document.getElementById('speed-trend');
            if (speedTrendElement) {
                speedTrendElement.textContent = 'No comparison data';
                speedTrendElement.className = 'metric-trend neutral';
            }
        }
        
        // Calculate violations trend between periods
        if (currentPeriodEvents.length > 0 && previousPeriodEvents.length > 0) {
            const currentViolationEvents = currentPeriodEvents.filter(event => 
                event.radar_data && 
                event.radar_data.speed !== undefined && 
                event.radar_data.speed !== null && 
                event.radar_data.speed > 25
            );
            
            const previousViolationEvents = previousPeriodEvents.filter(event => 
                event.radar_data && 
                event.radar_data.speed !== undefined && 
                event.radar_data.speed !== null && 
                event.radar_data.speed > 25
            );
            
            const violationsTrendElement = document.getElementById('violations-trend');
            
            if (violationsTrendElement) {
                const currentViolations = currentViolationEvents.length;
                const previousViolations = previousViolationEvents.length;
                
                if (previousViolations > 0) {
                    const violationsChangePercent = Math.round(((currentViolations - previousViolations) / previousViolations) * 100);
                    
                    if (violationsChangePercent > 0) {
                        violationsTrendElement.textContent = `${violationsChangePercent}% vs yesterday`;
                        violationsTrendElement.className = 'metric-trend negative'; // More violations is negative
                    } else if (violationsChangePercent < 0) {
                        violationsTrendElement.textContent = `${Math.abs(violationsChangePercent)}% vs yesterday`;
                        violationsTrendElement.className = 'metric-trend positive'; // Fewer violations is positive
                    } else {
                        violationsTrendElement.textContent = 'Same as yesterday';
                        violationsTrendElement.className = 'metric-trend neutral';
                    }
                    console.log(`Violations trend: ${violationsChangePercent}% (current: ${currentViolations}, previous: ${previousViolations})`);
                } else if (currentViolations > 0) {
                    violationsTrendElement.textContent = 'New violations detected';
                    violationsTrendElement.className = 'metric-trend negative';
                } else {
                    violationsTrendElement.textContent = 'No violations';
                    violationsTrendElement.className = 'metric-trend positive';
                }
            }
        } else {
            const violationsTrendElement = document.getElementById('violations-trend');
            if (violationsTrendElement) {
                violationsTrendElement.textContent = 'No comparison data';
                violationsTrendElement.className = 'metric-trend neutral';
            }
        }
        
        // Update chart with hourly detection data from last 24 hours
        this.updateTrafficChartFromDetections(currentPeriodEvents);
    }
    
    updateSpeedMetrics(speedsData) {
        if (!speedsData) {
            console.error('No speeds data received');
            document.getElementById('avg-speed').textContent = 'No Data';
            document.getElementById('speed-violations').textContent = 'No Data';
            return;
        }
        
        // Use analytics data directly if available, otherwise calculate from speeds array
        if (speedsData.avg_speed !== undefined && speedsData.violations !== undefined) {
            // Use pre-calculated analytics data
            document.getElementById('avg-speed').textContent = speedsData.avg_speed.toFixed(1);
            document.getElementById('speed-violations').textContent = speedsData.violations;
            
            // Update speed distribution chart with individual speed values if available
            if (speedsData.speeds && Array.isArray(speedsData.speeds)) {
                this.updateSpeedDistributionChart(speedsData.speeds);
                this.updateViolationsList(speedsData.speeds);
            }
            
            console.log(`Updated speeds from analytics - Avg: ${speedsData.avg_speed.toFixed(1)} mph, Violations: ${speedsData.violations}, Total: ${speedsData.total_measurements || 0}`);
            return;
        }
        
        if (!speedsData.speeds || !Array.isArray(speedsData.speeds)) {
            console.error('Invalid speeds data format:', speedsData);
            document.getElementById('avg-speed').textContent = 'Invalid Data';
            document.getElementById('speed-violations').textContent = 'Invalid Data';
            return;
        }
        
        const speeds = speedsData.speeds;
        if (speeds.length === 0) {
            document.getElementById('avg-speed').textContent = '0';
            document.getElementById('speed-violations').textContent = '0';
            console.log('No speed measurements available');
            return;
        }
        
        // Calculate average speed
        const avgSpeed = speeds.reduce((sum, record) => sum + (record.speed || 0), 0) / speeds.length;
        document.getElementById('avg-speed').textContent = avgSpeed.toFixed(1);
        
        // Count speed violations (assuming 25 mph speed limit)
        const violations = speeds.filter(record => record.speed && record.speed > 25).length;
        document.getElementById('speed-violations').textContent = violations;
        
        // Update violations list
        this.updateViolationsList(speeds);
        
        // Update Speed Distribution chart
        this.updateSpeedDistributionChart(speeds);
        
        console.log(`Updated speeds - Avg: ${avgSpeed.toFixed(1)} mph, Violations: ${violations}`);
    }

    updateSpeedDistributionChart(speeds) {
        if (!this.charts.speed) {
            console.error('Speed distribution chart not initialized');
            return;
        }

        if (!speeds || speeds.length === 0) {
            // Show "No Data" state
            this.charts.speed.data.labels = ['No Data'];
            this.charts.speed.data.datasets[0].data = [1];
            this.charts.speed.data.datasets[0].backgroundColor = ['#e2e8f0'];
            this.charts.speed.update();
            return;
        }

        // Extract speed values
        const speedValues = speeds.map(record => record.speed || 0).filter(speed => speed > 0);
        
        if (speedValues.length === 0) {
            // Show "No Data" state
            this.charts.speed.data.labels = ['No Data'];
            this.charts.speed.data.datasets[0].data = [1];
            this.charts.speed.data.datasets[0].backgroundColor = ['#e2e8f0'];
            this.charts.speed.update();
            return;
        }

        // Create speed distribution bins
        const speedLimit = 25; // mph
        const low = speedValues.filter(speed => speed <= 15).length;
        const normal = speedValues.filter(speed => speed > 15 && speed <= speedLimit).length;
        const overLimit = speedValues.filter(speed => speed > speedLimit && speed <= 35).length;
        const excessive = speedValues.filter(speed => speed > 35).length;

        // Calculate percentages
        const total = speedValues.length;
        const lowPercent = total > 0 ? Math.round((low / total) * 100) : 0;
        const normalPercent = total > 0 ? Math.round((normal / total) * 100) : 0;
        const overLimitPercent = total > 0 ? Math.round((overLimit / total) * 100) : 0;
        const excessivePercent = total > 0 ? Math.round((excessive / total) * 100) : 0;

        // Update chart data with percentage labels
        this.charts.speed.data.labels = [
            `0-15 mph (${lowPercent}%)`,
            `16-25 mph (${normalPercent}%)`, 
            `26-35 mph (${overLimitPercent}%)`,
            `36+ mph (${excessivePercent}%)`
        ];
        this.charts.speed.data.datasets[0].data = [low, normal, overLimit, excessive];
        this.charts.speed.data.datasets[0].backgroundColor = [
            '#22c55e', // Green for low speeds
            '#3b82f6', // Blue for normal speeds  
            '#f59e0b', // Orange for over limit
            '#ef4444'  // Red for excessive speeds
        ];
        this.charts.speed.update();

        console.log(`Updated speed distribution: ${low} low (${lowPercent}%), ${normal} normal (${normalPercent}%), ${overLimit} over limit (${overLimitPercent}%), ${excessive} excessive (${excessivePercent}%)`);
    }

    updateViolationsList(speeds) {
        const violationsList = document.getElementById('violations-list');
        if (!violationsList) {
            console.error('Violations list element not found');
            return;
        }

        if (!speeds || speeds.length === 0) {
            violationsList.innerHTML = '<div class="no-violations">No speed data available</div>';
            return;
        }

        // Calculate 24-hour cutoff time
        const now = new Date();
        const cutoffTime = new Date();
        cutoffTime.setHours(now.getHours() - 24);

        // Filter violations (speeds > 25 mph) within last 24 hours and sort by timestamp (newest first)
        const violations = speeds
            .filter(record => {
                if (!record.speed || record.speed <= 25) return false;
                
                // Filter by 24-hour time period
                if (record.timestamp) {
                    const recordTime = new Date(record.timestamp);
                    if (!isNaN(recordTime.getTime()) && recordTime < cutoffTime) {
                        return false;
                    }
                }
                
                return true;
            })
            .sort((a, b) => {
                // Sort by timestamp - handle both ISO strings and objects with timestamp property
                const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
                const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
                return timeB - timeA; // Newest first
            });

        if (violations.length === 0) {
            violationsList.innerHTML = '<div class="no-violations">No violations recorded</div>';
            return;
        }

        // Create HTML for violations list
        const violationsHTML = violations.map(violation => {
            const speed = violation.speed.toFixed(1);
            let timeStr = 'Unknown time';
            let dateStr = '';
            
            if (violation.timestamp) {
                try {
                    const date = new Date(violation.timestamp);
                    if (!isNaN(date.getTime())) {
                        // Format time in Central Time
                        timeStr = date.toLocaleTimeString('en-US', { 
                            hour: '2-digit', 
                            minute: '2-digit',
                            hour12: true,
                            timeZone: 'America/Chicago'
                        });
                        
                        // Get current time in Central Time for proper date comparison
                        const now = new Date();
                        const centralNow = new Date(now.toLocaleString('en-US', { timeZone: 'America/Chicago' }));
                        const centralViolationTime = new Date(date.toLocaleString('en-US', { timeZone: 'America/Chicago' }));
                        
                        // Create date-only objects for comparison (all in Central Time)
                        const violationDateOnly = new Date(centralViolationTime.getFullYear(), centralViolationTime.getMonth(), centralViolationTime.getDate());
                        const todayDateOnly = new Date(centralNow.getFullYear(), centralNow.getMonth(), centralNow.getDate());
                        const yesterdayDateOnly = new Date(todayDateOnly);
                        yesterdayDateOnly.setDate(yesterdayDateOnly.getDate() - 1);
                        
                        if (violationDateOnly.getTime() === todayDateOnly.getTime()) {
                            dateStr = 'Today';
                        } else if (violationDateOnly.getTime() === yesterdayDateOnly.getTime()) {
                            dateStr = 'Yesterday';
                        } else {
                            dateStr = centralViolationTime.toLocaleDateString('en-US', { 
                                month: 'short',
                                day: 'numeric'
                            });
                        }
                    }
                } catch (e) {
                    console.warn('Invalid timestamp:', violation.timestamp);
                }
            }
            
            return `
                <div class="violation-item">
                    <span class="violation-time">
                        <span class="violation-date">${dateStr}</span>
                        <span class="violation-time-only">${timeStr}</span>
                    </span>
                    <span class="violation-speed">${speed} mph</span>
                </div>
            `;
        }).join('');

        violationsList.innerHTML = violationsHTML;
        
        console.log(` Updated violations list with ${violations.length} violations (24h filter)`);
    }
    
    updateWeatherData(weatherData) {
        if (!weatherData) {
            console.error('No weather data received');
            document.getElementById('airport-temp').textContent = 'No Data';
            document.getElementById('local-temp').textContent = 'No Data';
            document.getElementById('local-humidity').textContent = 'No Data';
            return;
        }
        
        // Update airport temperature
        const airportTempElement = document.getElementById('airport-temp');
        if (weatherData.airport_temperature_f) {
            airportTempElement.textContent = `${Math.round(weatherData.airport_temperature_f)} F`;
            console.log(`Updated airport temperature: ${Math.round(weatherData.airport_temperature_f)} F`);
        } else if (weatherData.airport_temperature_c) {
            const tempF = Math.round(weatherData.airport_temperature_c * 9/5 + 32);
            airportTempElement.textContent = `${tempF} F`;
            console.log(`Updated airport temperature: ${tempF} F`);
        } else {
            airportTempElement.textContent = '-- F';
            console.log('No airport temperature data available');
        }
        
        // Update local DHT22 temperature
        const localTempElement = document.getElementById('local-temp');
        if (weatherData.temperature_f) {
            localTempElement.textContent = `${Math.round(weatherData.temperature_f)} F`;
            console.log(`Updated local temperature: ${Math.round(weatherData.temperature_f)} F`);
        } else if (weatherData.temperature_c) {
            const tempF = Math.round(weatherData.temperature_c * 9/5 + 32);
            localTempElement.textContent = `${tempF} F`;
            console.log(`Updated local temperature: ${tempF} F`);
        } else {
            localTempElement.textContent = '-- F';
            console.log('No local temperature data available');
        }
        
        // Update local DHT22 humidity
        const humidityElement = document.getElementById('local-humidity');
        if (weatherData.humidity !== undefined && weatherData.humidity !== null) {
            humidityElement.textContent = `${Math.round(weatherData.humidity)}%`;
            console.log(`Updated humidity: ${Math.round(weatherData.humidity)}%`);
        } else {
            humidityElement.textContent = '--%';
            console.log('No humidity data available');
        }
        
        // Update weather condition display if element exists
        const weatherElement = document.getElementById('weather-condition');
        if (weatherElement) {
            if (weatherData.weather_description) {
                weatherElement.textContent = weatherData.weather_description;
            } else if (weatherData.sky_condition && weatherData.sky_condition.condition) {
                weatherElement.textContent = weatherData.sky_condition.condition;
            } else {
                weatherElement.textContent = 'Unknown';
            }
        }
        
        // Update wind speed
        const windSpeedElement = document.getElementById('wind-speed');
        if (weatherData.wind_speed_mph !== undefined && weatherData.wind_speed_mph !== null) {
            windSpeedElement.textContent = `${weatherData.wind_speed_mph} mph`;
            console.log(`Updated wind speed: ${weatherData.wind_speed_mph} mph`);
        } else {
            windSpeedElement.textContent = 'No Data';
            console.log('No wind speed data available');
        }
        
        // Update wind direction
        const windDirectionElement = document.getElementById('wind-direction');
        if (weatherData.wind_direction !== undefined && weatherData.wind_direction !== null) {
            const compass = weatherData.wind_direction_compass || this.degreesToCompass(weatherData.wind_direction);
            windDirectionElement.textContent = `${compass} (${weatherData.wind_direction} )`;
            console.log(`Updated wind direction: ${compass} (${weatherData.wind_direction} )`);
        } else {
            windDirectionElement.textContent = 'No Data';
            console.log('No wind direction data available');
        }

        // Update additional weather info in the metric trend if available
        const weatherTrend = document.querySelector('.metric-card.weather .metric-trend');
        if (weatherTrend) {
            let trendText = 'Clear conditions';  // default
            
            if (weatherData.weather_description) {
                trendText = weatherData.weather_description;
            } else if (weatherData.wind_speed_mph && weatherData.wind_direction_compass) {
                trendText = `Wind: ${weatherData.wind_speed_mph} mph ${weatherData.wind_direction_compass}`;
            } else if (weatherData.humidity) {
                trendText = `Humidity: ${Math.round(weatherData.humidity)}%`;
            }
            
            weatherTrend.textContent = trendText;
        }
    }

    updateCameraSnapshot() {
        const cameraImage = document.getElementById('camera-snapshot');
        const cameraStatus = document.getElementById('camera-status');
        
        if (!cameraImage || !cameraStatus) {
            console.error(' Camera elements not found');
            return;
        }

        // Set loading state
        cameraImage.classList.add('loading');
        cameraStatus.textContent = 'Loading...';
        cameraStatus.className = 'camera-status';

        // Fetch latest camera snapshot
        const cameraUrl = `${this.apiBaseUrl}/camera/latest?t=${Date.now()}`;
        
        fetch(cameraUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                const imageUrl = URL.createObjectURL(blob);
                cameraImage.src = imageUrl;
                cameraImage.onload = () => {
                    cameraImage.classList.remove('loading');
                    cameraStatus.textContent = 'Last Detected';
                    cameraStatus.className = 'camera-status connected';
                    console.log(' Camera snapshot updated successfully');
                };
                cameraImage.onerror = () => {
                    cameraImage.classList.remove('loading');
                    cameraStatus.textContent = 'Image Error';
                    cameraStatus.className = 'camera-status error';
                    console.error(' Failed to load camera image');
                };
            })
            .catch(error => {
                console.error(' Camera snapshot error:', error);
                cameraImage.classList.remove('loading');
                cameraStatus.textContent = 'Unavailable';
                cameraStatus.className = 'camera-status error';
                cameraImage.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmYWZjIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk0YTNiOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkNhbWVyYSBVbmF2YWlsYWJsZTwvdGV4dD48L3N2Zz4=';
            });

        // Also update the last vehicle speed
        this.updateLastVehicleSpeed();
    }

    async updateLastVehicleSpeed() {
        const speedValueElement = document.getElementById('speed-value');
        const vehicleTypeElement = document.getElementById('vehicle-type');
        
        if (!speedValueElement || !vehicleTypeElement) {
            console.error(' Speed or vehicle type element not found');
            return;
        }

        try {
            // Fetch the most recent vehicle detection with speed data
            const response = await fetch(`${this.apiBaseUrl}/vehicles/consolidated?limit=1`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Debug: Log the raw API response to see structure
            console.log(' Raw consolidated API response:', JSON.stringify(data, null, 2));
            
            if (data.events && data.events.length > 0) {
                const latestEvent = data.events[0];
                
                // Debug: Log the latest event structure
                console.log(' Latest event:', JSON.stringify(latestEvent, null, 2));
                
                // Get vehicle type from camera_data.vehicle_types (nested structure)
                let vehicleType = 'Unknown';
                const vehicleTypes = latestEvent.camera_data?.vehicle_types;
                
                if (vehicleTypes) {
                    if (Array.isArray(vehicleTypes) && vehicleTypes.length > 0) {
                        vehicleType = vehicleTypes[0];
                    } else if (typeof vehicleTypes === 'string') {
                        try {
                            const types = JSON.parse(vehicleTypes);
                            vehicleType = Array.isArray(types) && types.length > 0 ? types[0] : vehicleTypes;
                        } catch (e) {
                            vehicleType = vehicleTypes;
                        }
                    }
                }
                
                // Update vehicle type
                vehicleTypeElement.textContent = vehicleType;
                
                // Get speed from radar_data.speed (nested structure)
                const speedMph = latestEvent.radar_data?.speed;
                
                // Check if we have speed data from radar
                if (speedMph !== null && speedMph !== undefined) {
                    speedValueElement.textContent = `${speedMph.toFixed(1)} mph`;
                    console.log(` Last vehicle: ${vehicleType} at ${speedMph} mph`);
                } else {
                    // No speed data - show vehicle type only without the @ separator
                    speedValueElement.textContent = '(No Speed)';
                    console.log(' Latest detection has no speed data');
                }
            } else {
                vehicleTypeElement.textContent = '--';
                speedValueElement.textContent = 'No Data';
                console.log('No vehicle detections available');
            }
        } catch (error) {
            console.error(' Error fetching last vehicle speed:', error);
            vehicleTypeElement.textContent = '--';
            speedValueElement.textContent = 'Error';
        }
    }
    
    updateTrafficChartFromDetections(detections) {
        if (!detections || detections.length === 0) {
            console.log('No detections data for chart');
            if (this.charts.traffic) {
                this.charts.traffic.data.labels = ['No Data Available'];
                this.charts.traffic.data.datasets[0].data = [0];
                this.charts.traffic.update();
            }
            return;
        }
        
        if (!this.charts.traffic) {
            console.error('Traffic chart not initialized');
            return;
        }
        
        // Group detections by hour
        const hourlyData = {};
        let validDetections = 0;
        
        detections.forEach(detection => {
            if (detection.timestamp) {
                const hour = new Date(detection.timestamp).getHours();
                if (!isNaN(hour) && hour >= 0 && hour <= 23) {
                    hourlyData[hour] = (hourlyData[hour] || 0) + 1;
                    validDetections++;
                }
            }
        });
        
        if (validDetections === 0) {
            console.log('No valid timestamps in detections data');
            this.charts.traffic.data.labels = ['Invalid Data'];
            this.charts.traffic.data.datasets[0].data = [0];
            this.charts.traffic.update();
            return;
        }
        
        const labels = [];
        const values = [];
        for (let hour = 0; hour < 24; hour++) {
            labels.push(`${hour}:00`);
            values.push(hourlyData[hour] || 0);
        }
        
        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = values;
        this.charts.traffic.update();
        
        console.log(`Updated traffic chart with ${validDetections} valid detections`);
    }
    
    updateReportsSummary(summaryData) {
        if (!summaryData) {
            console.log('No summary data received');
            return;
        }
        
        // Update summary statistics
        const summaryElement = document.getElementById('reports-summary');
        if (summaryElement) {
            const vehicleStats = summaryData.vehicle_statistics || {};
            const speedStats = summaryData.speed_statistics || {};
            const safetyMetrics = summaryData.safety_metrics || {};
            
            summaryElement.innerHTML = `
                <div class="summary-section">
                    <h4>Vehicle Statistics (${summaryData.report_period || '24 Hours'})</h4>
                    <p><strong>Total Detections:</strong> ${vehicleStats.total_detections || 0}</p>
                    <p><strong>Hourly Average:</strong> ${Math.round(vehicleStats.hourly_average || 0)}</p>
                    <p><strong>Peak Hour:</strong> ${vehicleStats.peak_hour || 'N/A'}:00</p>
                </div>
                <div class="summary-section">
                    <h4>Speed Analysis</h4>
                    <p><strong>Total Measurements:</strong> ${speedStats.total_measurements || 0}</p>
                    <p><strong>Average Speed:</strong> ${speedStats.average_speed || 0} mph</p>
                    <p><strong>Max Speed:</strong> ${speedStats.max_speed || 0} mph</p>
                    <p><strong>Violations:</strong> ${speedStats.violations || 0}</p>
                    <p><strong>Compliance Rate:</strong> ${speedStats.compliance_rate || 0}%</p>
                </div>
                <div class="summary-section">
                    <h4>Safety Overview</h4>
                    <p><strong>Overall Score:</strong> ${safetyMetrics.overall_score || 0}/100</p>
                    <p><strong>Risk Level:</strong> ${safetyMetrics.risk_level || 'Unknown'}</p>
                    <p><strong>Incidents:</strong> ${safetyMetrics.incidents || 0}</p>
                </div>
            `;
        }
        
        console.log('Updated reports summary with real data');
    }
    
    updateViolationsReport(violationsData) {
        if (!violationsData) {
            console.log('No violations data received');
            return;
        }
        
        // Update violations summary
        const violationsElement = document.getElementById('violations-report');
        if (violationsElement) {
            const categories = violationsData.violation_categories || {};
            
            violationsElement.innerHTML = `
                <div class="violations-summary">
                    <h4>Speed Violations Report</h4>
                    <p><strong>Total Violations:</strong> ${violationsData.total_violations || 0}</p>
                    <p><strong>Speed Limit:</strong> ${violationsData.speed_limit || 25} mph</p>
                </div>
                <div class="violation-categories">
                    <h5>Violation Categories</h5>
                    <p><strong>Minor (${categories.minor?.range || '26-30 mph'}):</strong> ${categories.minor?.count || 0} (${categories.minor?.percentage || 0}%)</p>
                    <p><strong>Moderate (${categories.moderate?.range || '31-35 mph'}):</strong> ${categories.moderate?.count || 0} (${categories.moderate?.percentage || 0}%)</p>
                    <p><strong>Severe (${categories.severe?.range || '36+ mph'}):</strong> ${categories.severe?.count || 0} (${categories.severe?.percentage || 0}%)</p>
                </div>
            `;
            
            // Add recommendations if available
            if (violationsData.recommendations && violationsData.recommendations.length > 0) {
                const recommendationsList = violationsData.recommendations.map(rec => `<li>${rec}</li>`).join('');
                violationsElement.innerHTML += `
                    <div class="violation-recommendations">
                        <h5>Recommendations</h5>
                        <ul>${recommendationsList}</ul>
                    </div>
                `;
            }
        }
        
        console.log('Updated violations report with real data');
    }
    
    updateMonthlyReport(monthlyData) {
        if (!monthlyData) {
            console.log('No monthly data received');
            return;
        }
        
        // Update monthly report display
        const monthlyElement = document.getElementById('monthly-report');
        if (monthlyElement) {
            const summary = monthlyData.summary_statistics || {};
            const performance = monthlyData.performance_trends || {};
            const comparison = monthlyData.comparative_analysis?.vs_previous_month || {};
            
            monthlyElement.innerHTML = `
                <div class="monthly-overview">
                    <h4>Monthly Report - ${monthlyData.month || 'Current Month'}</h4>
                    <p><strong>Total Detections:</strong> ${summary.total_detections || 0}</p>
                    <p><strong>Daily Average:</strong> ${Math.round(summary.daily_average || 0)}</p>
                    <p><strong>Peak Day:</strong> ${summary.peak_day || 'N/A'}</p>
                    <p><strong>Average Compliance:</strong> ${summary.average_compliance_rate || 0}%</p>
                </div>
                <div class="performance-metrics">
                    <h5>System Performance</h5>
                    <p><strong>Detection Accuracy:</strong> ${performance.detection_accuracy || 0}%</p>
                    <p><strong>System Uptime:</strong> ${performance.system_uptime || 0}%</p>
                    <p><strong>Data Quality:</strong> ${performance.data_quality_score || 0}%</p>
                </div>
                <div class="comparative-analysis">
                    <h5>Compared to Previous Month</h5>
                    <p><strong>Traffic Change:</strong> ${comparison.traffic_change || 'N/A'}</p>
                    <p><strong>Violations Change:</strong> ${comparison.violations_change || 'N/A'}</p>
                    <p><strong>Safety Improvement:</strong> ${comparison.safety_improvement || 'N/A'}</p>
                </div>
            `;
            
            // Add insights if available
            if (monthlyData.insights && monthlyData.insights.length > 0) {
                const insightsList = monthlyData.insights.map(insight => `<li>${insight}</li>`).join('');
                monthlyElement.innerHTML += `
                    <div class="monthly-insights">
                        <h5>Key Insights</h5>
                        <ul>${insightsList}</ul>
                    </div>
                `;
            }
        }
        
        console.log('Updated monthly report with real data');
    }
    
    showDataUnavailable() {
        // Show clear indicators that data is unavailable
        document.getElementById('total-vehicles').textContent = 'No Data';
        document.getElementById('avg-speed').textContent = 'No Data';
        document.getElementById('speed-violations').textContent = 'No Data';
        document.getElementById('airport-temp').textContent = 'No Data';
        document.getElementById('local-temp').textContent = 'No Data';
        document.getElementById('local-humidity').textContent = 'No Data';
        
        // Clear charts and show "No Data" message
        this.showChartsUnavailable();
    }
    
    showChartsUnavailable() {
        // Clear traffic chart and show no data message
        if (this.charts.traffic) {
            this.charts.traffic.data.labels = ['No API Connection'];
            this.charts.traffic.data.datasets[0].data = [0];
            this.charts.traffic.update();
        }
        
        // Clear weekly patterns chart
        if (this.charts.weekly) {
            this.charts.weekly.data.labels = ['No Data Available'];
            this.charts.weekly.data.datasets[0].data = [0];
            this.charts.weekly.update();
        }
        
        // Clear speed distribution chart
        if (this.charts.speed) {
            this.charts.speed.data.labels = ['No Data'];
            this.charts.speed.data.datasets[0].data = [0];
            this.charts.speed.update();
        }
    }
    
    updateTrafficChart(period) {
        if (!this.isOnline) {
            console.log('Cannot update traffic chart - API offline');
            return;
        }

        // Calculate the time range based on period
        let seconds;
        switch (period) {
            case '24h':
                seconds = 86400; // 24 hours
                break;
            case '7d':
                seconds = 604800; // 7 days
                break;
            default:
                seconds = 86400; // Default to 24 hours
        }

        // Fetch vehicle detections data for the specified period
        this.loadTrafficVolumeData(seconds, period);
    }

    async loadTrafficVolumeData(seconds, period) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/vehicles/consolidated?limit=1000`);
            if (response.ok) {
                const data = await response.json();
                const events = data.events || [];
                
                // Filter events by time period
                const now = new Date();
                const cutoffTime = new Date(now.getTime() - (seconds * 1000));
                
                const recentEvents = events.filter(event => {
                    // Convert Unix timestamp to Date object
                    const eventTime = new Date(event.timestamp * 1000);
                    return eventTime >= cutoffTime;
                });

                this.updateTrafficChartWithDetections(recentEvents, period);
                console.log(`Updated traffic chart with ${recentEvents.length} events for ${period}`);
            } else {
                console.error(`Traffic volume API failed: ${response.status}`);
                this.showTrafficChartError('API Error');
            }
        } catch (error) {
            console.error('Traffic volume API error:', error.message);
            this.showTrafficChartError('Connection Error');
        }
    }

    updateTrafficChartWithDetections(detections, period) {
        if (!this.charts.traffic) {
            console.error('Traffic chart not initialized');
            return;
        }

        if (detections.length === 0) {
            this.charts.traffic.data.labels = ['No Data Available'];
            this.charts.traffic.data.datasets[0].data = [0];
            this.charts.traffic.update();
            return;
        }

        // Group detections by time intervals
        const timeGroups = {};
        let timeFormat, groupSize;
        
        if (period === '24h') {
            // Group by hours for 24h view
            timeFormat = (date) => date.getHours().toString().padStart(2, '0') + ':00';
            groupSize = 3600000; // 1 hour in milliseconds
        } else {
            // Group by days for 7d view  
            timeFormat = (date) => date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            groupSize = 86400000; // 1 day in milliseconds
        }

        // Initialize time groups
        const now = new Date();
        const numGroups = period === '24h' ? 24 : 7;
        
        for (let i = numGroups - 1; i >= 0; i--) {
            const groupTime = new Date(now.getTime() - (i * groupSize));
            const label = timeFormat(groupTime);
            timeGroups[label] = 0;
        }

        // Count detections in each time group
        detections.forEach(detection => {
            // Convert Unix timestamp to Date object
            const detectionTime = new Date(detection.timestamp * 1000);
            const label = timeFormat(detectionTime);
            if (timeGroups.hasOwnProperty(label)) {
                timeGroups[label]++;
            }
        });

        // Update chart
        const labels = Object.keys(timeGroups);
        const values = Object.values(timeGroups);
        
        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = values;
        this.charts.traffic.update();
    }

    showTrafficChartError(errorMessage) {
        if (!this.charts.traffic) return;
        
        this.charts.traffic.data.labels = [errorMessage];
        this.charts.traffic.data.datasets[0].data = [0];
        this.charts.traffic.update();
    }
    
    loadTabData(tabName) {
        // Load tab-specific data from API only - no mock data
        console.log(`Loading real data for tab: ${tabName}`);
        
        switch (tabName) {
            case 'patterns':
                // Load weekly patterns from analytics API
                if (this.isOnline) {
                    this.loadWeeklyPatterns();
                } else {
                    console.log('Cannot load patterns - API offline');
                }
                break;
            case 'reports':
                // Load reports from API
                if (this.isOnline) {
                    this.loadReportsData();
                } else {
                    console.log('Cannot load reports - API offline');
                }
                break;
            case 'alerts':
                // Load recent alerts from API
                if (this.isOnline) {
                    this.loadRealAlerts();
                } else {
                    console.log('Cannot load alerts - API offline');
                }
                break;
            case 'events':
                // Initialize real-time events dashboard
                if (!this.eventsManager) {
                    this.eventsManager = new VehicleEventsManager(this.apiBaseUrl);
                }
                this.eventsManager.start();
                break;
            case 'logs':
                // Initialize system logs tab
                this.initializeLogsTab();
                break;
            default:
                // Overview tab - data already loaded in loadRealData
                break;
        }
    }
    
    async loadWeeklyPatterns() {
        console.log('Loading weekly patterns from API...');
        
        if (!this.isOnline) {
            console.log('Cannot load weekly patterns - API offline');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/analytics/patterns`);
            if (response.ok) {
                const patternsData = await response.json();
                this.updateWeeklyPatternsDisplay(patternsData);
                console.log('Weekly patterns loaded successfully');
            } else {
                console.error(`Weekly patterns API failed: ${response.status}`);
            }
        } catch (error) {
            console.error('Weekly patterns API error:', error.message);
        }
    }
    
    async loadReportsData() {
        console.log('Loading reports data from API...');
        
        if (!this.isOnline) {
            console.log('Cannot load reports - API offline');
            return;
        }
        
        try {
            // Load summary report
            const summaryResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/summary`);
            if (summaryResponse.ok) {
                const summaryData = await summaryResponse.json();
                this.updateReportsSummary(summaryData);
                console.log('Reports summary loaded successfully');
            } else {
                console.error(`Reports summary API failed: ${summaryResponse.status}`);
            }
            
            // Load violations report
            const violationsResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/violations`);
            if (violationsResponse.ok) {
                const violationsData = await violationsResponse.json();
                this.updateViolationsReport(violationsData);
                console.log('Violations report loaded successfully');
            } else {
                console.error(`Violations report API failed: ${violationsResponse.status}`);
            }
            
            // Load monthly report
            const monthlyResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/monthly`);
            if (monthlyResponse.ok) {
                const monthlyData = await monthlyResponse.json();
                this.updateMonthlyReport(monthlyData);
                console.log('Monthly report loaded successfully');
            } else {
                console.error(`Monthly report API failed: ${monthlyResponse.status}`);
            }
            
        } catch (error) {
            console.error('Reports API error:', error.message);
        }
    }
    
    async loadRealAlerts() {
        console.log('Loading real alerts from API...');
        // Placeholder for future implementation when alerts endpoints are available
    }
    
    filterByLocation(location) {
        // Filter data by location
        console.log('Filtering by location:', location);
        
        if (location === 'oklahoma-city') {
            // Show Oklahoma City data (default and only location)
            console.log('Displaying Oklahoma City traffic data');
        } else {
            // Handle any other location (should not occur with current setup)
            console.log('Unknown location selected');
        }
    }
    
    startRefreshTimer() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.isOnline) {
                this.loadRealData();
            }
        }, 30000);
    }

    downloadMonthlyReport() {
        if (!this.apiBaseUrl) {
            alert('Please configure API connection first');
            return;
        }

        try {
            // Create download link
            const downloadUrl = `${this.apiBaseUrl}/analytics/reports/monthly/download`;
            
            // Create temporary link element and trigger download
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `monthly_traffic_summary_${new Date().toISOString().slice(0, 7)}.html`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            this.showSuccessMessage('Monthly report download started');
            
        } catch (error) {
            console.error('Error downloading monthly report:', error);
            alert('Failed to download monthly report. Please try again.');
        }
    }

    downloadViolationsReport() {
        if (!this.apiBaseUrl) {
            alert('Please configure API connection first');
            return;
        }

        try {
            // Create download link
            const downloadUrl = `${this.apiBaseUrl}/analytics/reports/violations/download`;
            
            // Create temporary link element and trigger download
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `speed_violations_${new Date().toISOString().slice(0, 7)}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            this.showSuccessMessage('Violations report download started');
            
        } catch (error) {
            console.error('Error downloading violations report:', error);
            alert('Failed to download violations report. Please try again.');
        }
    }

    showSuccessMessage(message) {
        // Create temporary success notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 1000;
            font-family: inherit;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    showNotImplemented(feature) {
        alert(`${feature} is not yet implemented.\n\nThis is a demonstration interface. The feature will be added in future development phases.`);
    }
}

// Vehicle Events Manager for Real-time Dashboard
class VehicleEventsManager {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
        this.logContent = document.getElementById('events-feed');
        this.lineNumber = 5;
        this.autoScroll = true;
        this.isPaused = false;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.stats = {
            total: 0,
            cars: 0,
            trucks: 0,
            motorcycles: 0,
            totalConfidence: 0
        };
        
        // Health monitoring properties
        this.connectionHealth = {
            isConnected: false,
            connectionType: 'none', // 'socket.io', 'polling', 'none'
            lastPing: null,
            latency: null,
            reconnectCount: 0,
            uptime: 0,
            startTime: Date.now()
        };
        
        // Event deduplication properties
        this.eventCache = new Map(); // eventId -> timestamp
        this.lastEventSequence = 0;
        this.cacheCleanupInterval = 60000; // Clean old events every minute

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const clearEventsBtn = document.getElementById('clear-events');
        const pauseBtn = document.getElementById('pause-events');
        const filterSelect = document.getElementById('event-level-filter');

        if (clearEventsBtn) {
            clearEventsBtn.addEventListener('click', () => {
                this.clearLog();
            });
        }

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.isPaused = !this.isPaused;
                pauseBtn.innerHTML = this.isPaused ? 'Resume' : 'Pause';
                pauseBtn.classList.toggle('active', this.isPaused);
                
                if (this.isPaused) {
                    this.disconnect();
                } else {
                    this.connect();
                }
            });
        }

        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.filterEvents(e.target.value);
            });
        }
        
        // Start health monitoring and event cleanup
        this.startHealthMonitoring();
        this.startEventCacheCleanup();
    }

    // Health Monitoring Methods
    startHealthMonitoring() {
        // Update connection uptime every second
        setInterval(() => {
            if (this.connectionHealth.isConnected) {
                this.connectionHealth.uptime = Date.now() - this.connectionHealth.startTime;
            }
            this.updateConnectionStatus();
        }, 1000);

        // Ping health check every 30 seconds for Socket.IO connections
        setInterval(() => {
            if (this.socket && this.connectionHealth.connectionType === 'socket.io') {
                this.pingHealthCheck();
            }
        }, 30000);
    }

    pingHealthCheck() {
        const pingStart = Date.now();
        this.socket.emit('ping', pingStart, (ack) => {
            const latency = Date.now() - pingStart;
            this.connectionHealth.latency = latency;
            this.connectionHealth.lastPing = new Date().toISOString();
            console.log(`Socket.IO ping: ${latency}ms`);
        });
    }

    updateConnectionHealth(connectionType, isConnected = false) {
        this.connectionHealth.isConnected = isConnected;
        this.connectionHealth.connectionType = connectionType;
        
        if (isConnected) {
            this.connectionHealth.startTime = Date.now();
            this.connectionHealth.uptime = 0;
        } else {
            this.connectionHealth.uptime = 0;
            this.connectionHealth.latency = null;
            this.connectionHealth.lastPing = null;
        }
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('last-detection');
        if (!statusElement) return;

        const health = this.connectionHealth;
        let statusText = '';
        
        if (health.isConnected) {
            const uptimeSeconds = Math.floor(health.uptime / 1000);
            statusText = `Connected via ${health.connectionType} (${uptimeSeconds}s)`;
            
            if (health.latency !== null) {
                statusText += ` - Latency: ${health.latency}ms`;
            }
        } else {
            statusText = `Disconnected (${health.reconnectCount} reconnects)`;
        }
        
        // Only update if text has changed to prevent flashing
        if (statusElement.textContent !== statusText) {
            statusElement.textContent = statusText;
        }
    }

    // Event Deduplication Methods
    startEventCacheCleanup() {
        setInterval(() => {
            this.cleanupEventCache();
        }, this.cacheCleanupInterval);
    }

    cleanupEventCache() {
        const now = Date.now();
        const maxAge = 300000; // 5 minutes
        
        for (const [eventId, timestamp] of this.eventCache.entries()) {
            if (now - timestamp > maxAge) {
                this.eventCache.delete(eventId);
            }
        }
        
        console.log(`Event cache cleaned: ${this.eventCache.size} events remaining`);
    }

    generateEventId(eventData) {
        // Generate a unique ID based on event content and timestamp
        const content = JSON.stringify({
            timestamp: eventData.timestamp,
            type: eventData.type,
            detection_type: eventData.detection_type,
            confidence: eventData.confidence,
            speed: eventData.speed
        });
        
        // Simple hash function for event ID
        let hash = 0;
        for (let i = 0; i < content.length; i++) {
            const char = content.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        return `evt_${Math.abs(hash)}_${Date.now()}`;
    }

    isDuplicateEvent(eventData) {
        // Generate or extract event ID
        let eventId = eventData.id || eventData.event_id;
        
        if (!eventId) {
            eventId = this.generateEventId(eventData);
        }
        
        // Check if we've seen this event recently
        if (this.eventCache.has(eventId)) {
            console.log(`Duplicate event detected and skipped: ${eventId}`);
            return true;
        }
        
        // Add to cache
        this.eventCache.set(eventId, Date.now());
        
        // Check sequence number if available
        if (eventData.sequence) {
            if (eventData.sequence <= this.lastEventSequence) {
                console.log(`Out-of-order event detected and skipped: seq ${eventData.sequence}`);
                return true;
            }
            this.lastEventSequence = eventData.sequence;
        }
        
        return false;
    }

    start() {
        this.addSystemMessage('Connecting to real-time event stream...');
        this.connect();
    }

    connect() {
        if (this.isPaused || this.socket) return;

        try {
            this.addSystemMessage('Connecting to real-time event stream...');
            
            // Initialize Socket.IO connection with proper configuration
            this.socket = io(this.apiBaseUrl.replace('/api', ''), {
                transports: ['websocket', 'polling'],
                timeout: 5000,
                forceNew: true,
                reconnection: false // We'll handle reconnection manually
            });

            // Connection successful
            this.socket.on('connect', () => {
                this.reconnectAttempts = 0;
                this.connectionHealth.reconnectCount = this.reconnectAttempts;
                this.updateConnectionHealth('socket.io', true);
                
                this.addSystemMessage('Connected to real-time event stream');
                this.addSystemMessage('Subscribing to vehicle detection events...');
                
                // Subscribe to events
                this.socket.emit('subscribe_events');
            });

            // Handle real-time events from Socket.IO
            this.socket.on('real_time_event', (data) => {
                try {
                    // Check for duplicate events
                    if (this.isDuplicateEvent(data)) {
                        return; // Skip duplicate
                    }
                    
                    this.handleRealtimeEvent(data);
                } catch (error) {
                    console.error('Error processing Socket.IO event:', error);
                }
            });

            // Handle connection status updates
            this.socket.on('events_status', (status) => {
                console.log('Events subscription status:', status);
                if (status.status === 'subscribed') {
                    this.addSystemMessage('Successfully subscribed to vehicle detection events');
                }
            });

            // Handle disconnection
            this.socket.on('disconnect', (reason) => {
                console.log('Socket.IO disconnected:', reason);
                this.socket = null;
                this.updateConnectionHealth('none', false);
                this.handleDisconnect();
            });

            // Handle connection errors
            this.socket.on('connect_error', (error) => {
                console.error('Socket.IO connection error:', error);
                this.addSystemMessage('Socket.IO connection error');
                this.handleDisconnect();
            });

            // Handle system logs
            this.socket.on('system_log', (logData) => {
                // Debug: Log the incoming timestamp format
                console.log('Received log timestamp:', logData.timestamp, 'Type:', typeof logData.timestamp);
                this.addLogEntry(logData);
            });

        } catch (error) {
            console.error('Failed to create Socket.IO connection:', error);
            this.addSystemMessage('Failed to establish Socket.IO connection. Using fallback...');
            this.startPolling();
        }
    }

    handleDisconnect() {
        if (!this.isPaused && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.connectionHealth.reconnectCount = this.reconnectAttempts;
            this.addSystemMessage(`Connection lost. Reconnecting... (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
        } else {
            this.addSystemMessage('Socket.IO connection failed. Using fallback polling...');
            this.updateConnectionHealth('polling', true);
            this.startPolling();
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    startPolling() {
        // Fallback to polling the API for events
        this.pollInterval = setInterval(async () => {
            if (this.isPaused) return;

            try {
                const response = await fetch(`${this.apiBaseUrl}/events/realtime?limit=10`);
                if (response.ok) {
                    const data = await response.json();
                    const events = data.events || [];
                    events.forEach(event => {
                        // Check for duplicate events in polling mode too
                        if (!this.isDuplicateEvent(event)) {
                            this.handleRealtimeEvent(event);
                        }
                    });
                }
            } catch (error) {
                console.error('Polling failed:', error);
            }
        }, 3000);
    }

    handleRealtimeEvent(data) {
        if (this.isPaused) return;

        // Format timestamp in Central Time
        const timestamp = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });

        // Handle different event types
        switch (data.event_type || data.business_event) {
            case 'vehicle_detection':
            case 'vehicle_detected':
                this.addVehicleDetection(
                    data.vehicle_type || data.detected_class,
                    data.confidence || Math.floor(Math.random() * 40) + 60,
                    data.location || data.zone || 'Camera Zone',
                    data.additional_info || `Speed: ${data.speed || 'unknown'}`
                );
                break;

            case 'system_status':
            case 'health_check':
                this.addSystemMessage(`${data.message || 'System health check completed'}`);
                break;

            case 'api_request_success':
                // Only log significant API events to avoid spam
                if (data.endpoint && data.endpoint.includes('detection')) {
                    this.addSystemMessage(`Detection API request processed (${data.duration_ms}ms)`);
                }
                break;

            case 'radar_alert':
                this.addSystemMessage(`Radar alert: ${data.message || 'Motion detected'}`);
                break;

            default:
                // Generic event handling
                if (data.message) {
                    this.addSystemMessage(` ${data.message}`);
                }
                break;
        }

        // Update last detection time
        document.getElementById('last-detection').textContent = `Last detection: ${timestamp}`;
    }

    addVehicleDetection(vehicleType, confidence, location, additionalInfo = '') {
        if (this.isPaused || !this.logContent) return;

        // Format timestamp in Central Time
        const timestamp = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry info new-detection';
        
        const confidenceColor = confidence > 80 ? '#38b2ac' : confidence > 60 ? '#ed8936' : '#e53e3e';
        
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level">DETECT</span>
            <span class="log-service">vehicle</span>
            <span class="log-message">
                Detected <span style="color: ${confidenceColor}">${vehicleType}</span> 
                with ${confidence}% confidence
                ${location ? ` at ${location}` : ''}
                ${additionalInfo ? ` - ${additionalInfo}` : ''}
            </span>
        `;

        this.logContent.appendChild(logEntry);
        this.lineNumber++;

        // Update stats
        this.updateStats(vehicleType, confidence);

        // Auto scroll
        if (this.autoScroll) {
            this.logContent.scrollTop = this.logContent.scrollHeight;
        }

        // Remove highlight after animation
        setTimeout(() => {
            logEntry.classList.remove('new-detection');
        }, 1000);
    }

    updateStats(vehicleType, confidence) {
        this.stats.total++;
        this.stats.totalConfidence += confidence;

        const vehicleTypeLower = vehicleType.toLowerCase();
        if (vehicleTypeLower.includes('car') || vehicleTypeLower.includes('sedan') || vehicleTypeLower.includes('suv')) {
            this.stats.cars++;
        } else if (vehicleTypeLower.includes('truck') || vehicleTypeLower.includes('van')) {
            this.stats.trucks++;
        } else if (vehicleTypeLower.includes('motorcycle') || vehicleTypeLower.includes('bike')) {
            this.stats.motorcycles++;
        }

        // Stats display removed from simplified events UI
        // Vehicle detection counts are now visible in the unified log format
    }

    clearLog() {
        if (this.logContent) {
            this.logContent.innerHTML = '';
            this.lineNumber = 1;
            this.stats = { total: 0, cars: 0, trucks: 0, motorcycles: 0, totalConfidence: 0 };
            this.updateStatsDisplay();
            this.addSystemMessage('Log cleared');
        }
    }

    filterEvents(eventType) {
        if (!this.logContent) return;

        const entries = this.logContent.querySelectorAll('.log-entry');
        entries.forEach(entry => {
            const service = entry.querySelector('.log-service')?.textContent || '';
            const message = entry.querySelector('.log-message')?.textContent || '';
            
            if (eventType === 'all') {
                entry.style.display = 'flex';
            } else if (eventType === 'vehicle' && (service.includes('vehicle') || message.includes('vehicle') || message.includes('detection'))) {
                entry.style.display = 'flex';
            } else if (eventType === 'speed' && (service.includes('radar') || message.includes('speed'))) {
                entry.style.display = 'flex';
            } else if (eventType === 'system' && (service.includes('system') || service.includes('api'))) {
                entry.style.display = 'flex';
            } else {
                entry.style.display = 'none';
            }
        });
    }

    updateStatsDisplay() {
        // Stats display removed from simplified events UI
        // Events are now displayed in unified log format
    }

    addSystemMessage(message) {
        if (!this.logContent) return;

        // Format timestamp in Central Time
        const timestamp = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry info';
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level">INFO</span>
            <span class="log-service">system</span>
            <span class="log-message">${message}</span>
        `;
        this.logContent.appendChild(logEntry);
        this.lineNumber++;

        if (this.autoScroll) {
            this.logContent.scrollTop = this.logContent.scrollHeight;
        }
    }

    filterLog(searchTerm) {
        if (!this.logContent) return;

        const lines = this.logContent.querySelectorAll('.events-log-line');
        lines.forEach(line => {
            const text = line.textContent.toLowerCase();
            if (searchTerm === '' || text.includes(searchTerm.toLowerCase())) {
                line.style.display = 'flex';
            } else {
                line.style.display = 'none';
            }
        });
    }

    // System Logs functionality
    addLogEntry(logData) {
        if (this.logsPaused) return;

        const logsFeed = document.getElementById('logs-feed');
        if (!logsFeed) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${logData.level.toLowerCase()}`;
        
        // Format timestamp in Central Time
        let timestamp;
        try {
            // Parse the timestamp - handle both ISO strings and already-formatted strings
            const date = new Date(logData.timestamp);
            if (!isNaN(date.getTime())) {
                timestamp = date.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true,
                    timeZone: 'America/Chicago'
                });
            } else {
                // If parsing fails, use current time in Central Time
                timestamp = new Date().toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true,
                    timeZone: 'America/Chicago'
                });
            }
        } catch (e) {
            // Fallback to current time if timestamp parsing fails
            timestamp = new Date().toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
                timeZone: 'America/Chicago'
            });
        }
        
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level">${logData.level}</span>
            <span class="log-service">${logData.service}</span>
            <span class="log-message">${logData.message}</span>
        `;
        
        // Add to top of feed
        logsFeed.insertBefore(logEntry, logsFeed.firstChild);
        
        // Keep only last 200 logs for performance
        while (logsFeed.children.length > 200) {
            logsFeed.removeChild(logsFeed.lastChild);
        }

        // Filter based on current level setting
        this.applyLogFilter();
    }

    applyLogFilter() {
        const filter = document.getElementById('log-level-filter')?.value || 'all';
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            let show = true;
            
            if (filter === 'error') {
                show = entry.classList.contains('error');
            } else if (filter === 'warn') {
                show = entry.classList.contains('error') || entry.classList.contains('warn');
            } else if (filter === 'info') {
                show = !entry.classList.contains('debug');
            }
            
            entry.style.display = show ? 'grid' : 'none';
        });
    }

    initializeLogsTab() {
        // Subscribe to logs when tab is activated
        if (this.socket) {
            this.socket.emit('subscribe_logs');
        }

        // Initialize log controls
        this.logsPaused = false;
        
        document.getElementById('clear-logs')?.addEventListener('click', () => {
            const logsFeed = document.getElementById('logs-feed');
            if (logsFeed) {
                logsFeed.innerHTML = '';
                this.addLogEntry({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    service: 'system',
                    message: 'Logs cleared'
                });
            }
        });

        document.getElementById('pause-logs')?.addEventListener('click', (e) => {
            this.logsPaused = !this.logsPaused;
            const btn = e.target;
            btn.textContent = this.logsPaused ? 'Resume' : 'Pause';
            btn.classList.toggle('paused', this.logsPaused);
        });

        document.getElementById('log-level-filter')?.addEventListener('change', () => {
            this.applyLogFilter();
        });
    }

    // Cleanup when switching tabs
    stop() {
        this.disconnect();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TrafficDashboard();
});

// Add some helper functions for backwards compatibility
function switchTab(tabName) {
    if (window.dashboard) {
        window.dashboard.switchTab(tabName);
    }
}
