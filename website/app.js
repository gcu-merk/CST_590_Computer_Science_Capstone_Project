// Traffic Analytics Dashboard - JavaScript
// GitHub Pages implementation with Tailscale API integration

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
        
        // Location selector
        document.getElementById('location').addEventListener('change', (e) => {
            this.filterByLocation(e.target.value);
        });
        
        // Export buttons (mock functionality)
        document.querySelectorAll('.download-btn, .export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showNotImplemented('Export functionality');
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
        
        // Weekly Patterns Chart
        const weeklyCtx = document.getElementById('weekly-patterns-chart');
        if (weeklyCtx) {
            this.charts.weekly = new Chart(weeklyCtx, {
                type: 'bar',
                data: {
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    datasets: [{
                        label: 'Vehicle Count',
                        data: [18500, 19200, 18800, 20100],
                        backgroundColor: '#667eea',
                        borderRadius: 8
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
                                display: false
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
            
            statusDiv.textContent = `✅ Connected! System status: ${data.status || 'OK'}`;
            statusDiv.style.background = '#c6f6d5';
            statusDiv.style.color = '#276749';
            
            this.updateApiStatus(true);
            this.loadRealData();
            this.startRefreshTimer();
            
            setTimeout(() => {
                document.getElementById('api-modal').style.display = 'none';
            }, 2000);
        } catch (error) {
            statusDiv.textContent = `❌ Connection failed: ${error.message}`;
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
            // Load recent vehicle detections (last 24 hours = 86400 seconds)
            try {
                const detectionsResponse = await fetch(`${this.apiBaseUrl}/vehicles/detections?seconds=86400`);
                if (detectionsResponse.ok) {
                    const detectionsData = await detectionsResponse.json();
                    this.updateMetricsFromDetections(detectionsData);
                    console.log('✅ Vehicle detections loaded successfully');
                } else {
                    console.error(`❌ Detections API failed: ${detectionsResponse.status}`);
                    document.getElementById('total-vehicles').textContent = `Error ${detectionsResponse.status}`;
                }
            } catch (error) {
                console.error('❌ Detections API error:', error.message);
                document.getElementById('total-vehicles').textContent = 'API Error';
            }
            
            // Load recent speed data (last 24 hours)
            try {
                const speedsResponse = await fetch(`${this.apiBaseUrl}/analytics/speeds?seconds=86400`);
                if (speedsResponse.ok) {
                    const speedsData = await speedsResponse.json();
                    this.updateSpeedMetrics(speedsData);
                    console.log('✅ Speed data loaded successfully');
                } else {
                    console.error(`❌ Speeds API failed: ${speedsResponse.status}`);
                    document.getElementById('avg-speed').textContent = `Error ${speedsResponse.status}`;
                    document.getElementById('speed-violations').textContent = `Error ${speedsResponse.status}`;
                }
            } catch (error) {
                console.error('❌ Speeds API error:', error.message);
                document.getElementById('avg-speed').textContent = 'API Error';
                document.getElementById('speed-violations').textContent = 'API Error';
            }
            
            // Load analytics data
            try {
                const analyticsResponse = await fetch(`${this.apiBaseUrl}/analytics/summary`);
                if (analyticsResponse.ok) {
                    const analyticsData = await analyticsResponse.json();
                    this.updateAnalyticsFromData(analyticsData);
                    console.log('✅ Analytics data loaded successfully');
                } else {
                    console.error(`❌ Analytics API failed: ${analyticsResponse.status}`);
                }
            } catch (error) {
                console.error('❌ Analytics API error:', error.message);
            }
            
            // Load weather data from individual endpoints
            try {
                const [dht22Response, airportResponse] = await Promise.all([
                    fetch(`${this.apiBaseUrl}/weather/current`),
                    fetch(`${this.apiBaseUrl}/weather/current`)
                ]);

                let combinedWeatherData = {};
                let hasValidData = false;

                // Process DHT22 sensor data
                if (dht22Response.ok) {
                    const dht22Data = await dht22Response.json();
                    if (dht22Data.data) {
                        combinedWeatherData.temperature_f = dht22Data.data.temperature_f;
                        combinedWeatherData.temperature_c = dht22Data.data.temperature_c;
                        combinedWeatherData.humidity = dht22Data.data.humidity;
                        hasValidData = true;
                        console.log('✅ DHT22 weather data loaded successfully');
                    }
                } else {
                    console.error(`❌ DHT22 Weather API failed: ${dht22Response.status}`);
                }

                // Process airport weather data
                if (airportResponse.ok) {
                    const airportData = await airportResponse.json();
                    if (airportData.data) {
                        combinedWeatherData.weather_description = airportData.data.textDescription;
                        combinedWeatherData.sky_condition = airportData.data.cloudLayers;
                        hasValidData = true;
                        console.log('✅ Airport weather data loaded successfully');
                    }
                } else {
                    console.error(`❌ Airport Weather API failed: ${airportResponse.status}`);
                }

                if (hasValidData) {
                    this.updateWeatherData(combinedWeatherData);
                    console.log('✅ Combined weather data processed successfully');
                } else {
                    console.error('❌ No valid weather data from either endpoint');
                    document.getElementById('temperature').textContent = 'No Data';
                }
            } catch (error) {
                console.error('❌ Weather API error:', error.message);
                document.getElementById('temperature').textContent = 'API Error';
            }
            
        } catch (error) {
            console.error('❌ Critical error loading real data:', error);
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
            document.getElementById('temperature').textContent = `${Math.round(latestTemp * 9/5 + 32)}°F`;
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
            console.error('❌ No detections data received');
            document.getElementById('total-vehicles').textContent = 'No Data';
            return;
        }
        
        if (!detectionsData.detections || !Array.isArray(detectionsData.detections)) {
            console.error('❌ Invalid detections data format:', detectionsData);
            document.getElementById('total-vehicles').textContent = 'Invalid Data';
            return;
        }
        
        const detections = detectionsData.detections;
        const totalVehicles = detections.length;
        
        // Update vehicle count
        document.getElementById('total-vehicles').textContent = totalVehicles.toLocaleString();
        console.log(`📊 Updated vehicle count: ${totalVehicles}`);
        
        // Update chart with hourly detection data
        this.updateTrafficChartFromDetections(detections);
    }
    
    updateSpeedMetrics(speedsData) {
        if (!speedsData) {
            console.error('❌ No speeds data received');
            document.getElementById('avg-speed').textContent = 'No Data';
            document.getElementById('speed-violations').textContent = 'No Data';
            return;
        }
        
        if (!speedsData.speeds || !Array.isArray(speedsData.speeds)) {
            console.error('❌ Invalid speeds data format:', speedsData);
            document.getElementById('avg-speed').textContent = 'Invalid Data';
            document.getElementById('speed-violations').textContent = 'Invalid Data';
            return;
        }
        
        const speeds = speedsData.speeds;
        if (speeds.length === 0) {
            document.getElementById('avg-speed').textContent = '0';
            document.getElementById('speed-violations').textContent = '0';
            console.log('📊 No speed measurements available');
            return;
        }
        
        // Calculate average speed
        const avgSpeed = speeds.reduce((sum, record) => sum + (record.speed || 0), 0) / speeds.length;
        document.getElementById('avg-speed').textContent = avgSpeed.toFixed(1);
        
        // Count speed violations (assuming 25 mph speed limit)
        const violations = speeds.filter(record => record.speed && record.speed > 25).length;
        document.getElementById('speed-violations').textContent = violations;
        
        console.log(`📊 Updated speeds - Avg: ${avgSpeed.toFixed(1)} mph, Violations: ${violations}`);
    }
    
    updateWeatherData(weatherData) {
        if (!weatherData) {
            console.error('❌ No weather data received');
            document.getElementById('temperature').textContent = 'No Data';
            return;
        }
        
        // Update temperature if available - handle multiple API formats
        let temperature = null;
        let tempDisplay = 'No Temp Data';
        
        if (weatherData.temperature_f) {
            // New API format - temperature_f directly available
            temperature = weatherData.temperature_f;
            tempDisplay = `${Math.round(temperature)}°F`;
        } else if (weatherData.temperature_c) {
            // New API format - convert from Celsius
            const tempF = Math.round(weatherData.temperature_c * 9/5 + 32);
            tempDisplay = `${tempF}°F`;
            temperature = tempF;
        } else if (weatherData.data && weatherData.data.temperature) {
            // Legacy API format - nested temperature
            const tempF = Math.round(weatherData.data.temperature * 9/5 + 32);
            tempDisplay = `${tempF}°F`;
            temperature = tempF;
        } else if (weatherData.temperature) {
            // Legacy API format - direct temperature field
            const tempF = Math.round(weatherData.temperature * 9/5 + 32);
            tempDisplay = `${tempF}°F`;
            temperature = tempF;
        }
        
        document.getElementById('temperature').textContent = tempDisplay;
        
        if (temperature) {
            console.log(`📊 Updated temperature: ${tempDisplay}`);
        } else {
            console.log('📊 No temperature data in weather response');
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
        
        // Update additional weather info in the metric trend if available
        const weatherTrend = document.querySelector('.metric-card.weather .metric-trend');
        if (weatherTrend) {
            let trendText = 'Clear conditions';  // default
            
            if (weatherData.weather_description) {
                trendText = weatherData.weather_description;
            } else if (weatherData.humidity) {
                trendText = `Humidity: ${Math.round(weatherData.humidity)}%`;
            }
            
            weatherTrend.textContent = trendText;
        }
    }
    
    updateTrafficChartFromDetections(detections) {
        if (!detections || detections.length === 0) {
            console.log('📊 No detections data for chart');
            if (this.charts.traffic) {
                this.charts.traffic.data.labels = ['No Data Available'];
                this.charts.traffic.data.datasets[0].data = [0];
                this.charts.traffic.update();
            }
            return;
        }
        
        if (!this.charts.traffic) {
            console.error('❌ Traffic chart not initialized');
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
            console.log('📊 No valid timestamps in detections data');
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
        
        console.log(`📊 Updated traffic chart with ${validDetections} valid detections`);
    }
    
    updateWeeklyPatternsDisplay(patternsData) {
        if (!patternsData) {
            console.log('❌ No patterns data received');
            return;
        }
        
        // Update weekly patterns chart with real data
        if (this.charts.weekly && patternsData.daily_patterns) {
            const days = Object.keys(patternsData.daily_patterns);
            const values = days.map(day => patternsData.daily_patterns[day].total || 0);
            
            this.charts.weekly.data.labels = days;
            this.charts.weekly.data.datasets[0].data = values;
            this.charts.weekly.update();
            
            console.log('📊 Updated weekly patterns chart with real data');
        }
        
        // Update patterns summary text elements if they exist
        const summaryElement = document.getElementById('patterns-summary');
        if (summaryElement && patternsData.weekly_summary) {
            summaryElement.innerHTML = `
                <p><strong>Total Weekly Detections:</strong> ${patternsData.weekly_summary.total_detections || 0}</p>
                <p><strong>Average Daily Traffic:</strong> ${Math.round(patternsData.weekly_summary.avg_daily_traffic || 0)}</p>
                <p><strong>Peak Day:</strong> ${patternsData.weekly_summary.peak_day || 'N/A'}</p>
                <p><strong>Lowest Day:</strong> ${patternsData.weekly_summary.lowest_day || 'N/A'}</p>
            `;
        }
    }
    
    updateSafetyDisplay(safetyData) {
        if (!safetyData) {
            console.log('❌ No safety data received');
            return;
        }
        
        // Update overall safety score
        const safetyScoreElement = document.getElementById('safety-score');
        if (safetyScoreElement) {
            safetyScoreElement.textContent = `${safetyData.overall_safety_score || 0}/100`;
        }
        
        // Update safety metrics
        const complianceElement = document.getElementById('speed-compliance-rate');
        if (complianceElement && safetyData.speed_compliance) {
            complianceElement.textContent = `${safetyData.speed_compliance.compliance_rate || 0}%`;
        }
        
        const violationsElement = document.getElementById('total-violations');
        if (violationsElement && safetyData.speed_compliance) {
            violationsElement.textContent = safetyData.speed_compliance.violations || 0;
        }
        
        // Update safety summary if element exists
        const safetySummaryElement = document.getElementById('safety-summary');
        if (safetySummaryElement) {
            const riskFactors = safetyData.risk_factors || {};
            const incidents = safetyData.incidents || {};
            
            safetySummaryElement.innerHTML = `
                <div class="safety-metrics">
                    <h4>Risk Assessment</h4>
                    <p><strong>Excessive Speed:</strong> ${riskFactors.excessive_speed || 'Unknown'}</p>
                    <p><strong>Traffic Volume:</strong> ${riskFactors.traffic_volume || 'Unknown'}</p>
                    <p><strong>Weather Impact:</strong> ${riskFactors.weather_impact || 'Unknown'}</p>
                    <p><strong>Visibility:</strong> ${riskFactors.visibility || 'Unknown'}</p>
                </div>
                <div class="incident-summary">
                    <h4>Recent Incidents</h4>
                    <p><strong>Last 7 Days:</strong> ${incidents.last_7_days || 0}</p>
                    <p><strong>Last 30 Days:</strong> ${incidents.last_30_days || 0}</p>
                </div>
            `;
        }
        
        // Update recommendations if element exists
        const recommendationsElement = document.getElementById('safety-recommendations');
        if (recommendationsElement && safetyData.recommendations) {
            const recommendationsList = safetyData.recommendations.map(rec => `<li>${rec}</li>`).join('');
            recommendationsElement.innerHTML = `<ul>${recommendationsList}</ul>`;
        }
        
        console.log('📊 Updated safety display with real data');
    }
    
    updateReportsSummary(summaryData) {
        if (!summaryData) {
            console.log('❌ No summary data received');
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
        
        console.log('📊 Updated reports summary with real data');
    }
    
    updateViolationsReport(violationsData) {
        if (!violationsData) {
            console.log('❌ No violations data received');
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
        
        console.log('📊 Updated violations report with real data');
    }
    
    updateMonthlyReport(monthlyData) {
        if (!monthlyData) {
            console.log('❌ No monthly data received');
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
        
        console.log('📊 Updated monthly report with real data');
    }
    
    showDataUnavailable() {
        // Show clear indicators that data is unavailable
        document.getElementById('total-vehicles').textContent = 'No Data';
        document.getElementById('avg-speed').textContent = 'No Data';
        document.getElementById('speed-violations').textContent = 'No Data';
        document.getElementById('temperature').textContent = 'No Data';
        
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
        // Only update chart if we have real data - no mock data fallback
        console.log(`Chart update requested for period: ${period} - Use real API data only`);
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
                    console.log('❌ Cannot load patterns - API offline');
                }
                break;
            case 'safety':
                // Load safety-specific data from API
                if (this.isOnline) {
                    this.loadSafetyData();
                } else {
                    console.log('❌ Cannot load safety data - API offline');
                }
                break;
            case 'reports':
                // Load reports from API
                if (this.isOnline) {
                    this.loadReportsData();
                } else {
                    console.log('❌ Cannot load reports - API offline');
                }
                break;
            case 'alerts':
                // Load recent alerts from API
                if (this.isOnline) {
                    this.loadRealAlerts();
                } else {
                    console.log('❌ Cannot load alerts - API offline');
                }
                break;
            case 'events':
                // Initialize real-time events dashboard
                if (!this.eventsManager) {
                    this.eventsManager = new VehicleEventsManager(this.apiBaseUrl);
                }
                this.eventsManager.start();
                break;
            default:
                // Overview tab - data already loaded in loadRealData
                break;
        }
    }
    
    async loadWeeklyPatterns() {
        console.log('🔄 Loading weekly patterns from API...');
        
        if (!this.isOnline) {
            console.log('❌ Cannot load weekly patterns - API offline');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/analytics/patterns`);
            if (response.ok) {
                const patternsData = await response.json();
                this.updateWeeklyPatternsDisplay(patternsData);
                console.log('✅ Weekly patterns loaded successfully');
            } else {
                console.error(`❌ Weekly patterns API failed: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Weekly patterns API error:', error.message);
        }
    }
    
    async loadSafetyData() {
        console.log('🔄 Loading safety data from API...');
        
        if (!this.isOnline) {
            console.log('❌ Cannot load safety data - API offline');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/analytics/safety`);
            if (response.ok) {
                const safetyData = await response.json();
                this.updateSafetyDisplay(safetyData);
                console.log('✅ Safety data loaded successfully');
            } else {
                console.error(`❌ Safety analysis API failed: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Safety analysis API error:', error.message);
        }
    }
    
    async loadReportsData() {
        console.log('🔄 Loading reports data from API...');
        
        if (!this.isOnline) {
            console.log('❌ Cannot load reports - API offline');
            return;
        }
        
        try {
            // Load summary report
            const summaryResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/summary`);
            if (summaryResponse.ok) {
                const summaryData = await summaryResponse.json();
                this.updateReportsSummary(summaryData);
                console.log('✅ Reports summary loaded successfully');
            } else {
                console.error(`❌ Reports summary API failed: ${summaryResponse.status}`);
            }
            
            // Load violations report
            const violationsResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/violations`);
            if (violationsResponse.ok) {
                const violationsData = await violationsResponse.json();
                this.updateViolationsReport(violationsData);
                console.log('✅ Violations report loaded successfully');
            } else {
                console.error(`❌ Violations report API failed: ${violationsResponse.status}`);
            }
            
            // Load monthly report
            const monthlyResponse = await fetch(`${this.apiBaseUrl}/analytics/reports/monthly`);
            if (monthlyResponse.ok) {
                const monthlyData = await monthlyResponse.json();
                this.updateMonthlyReport(monthlyData);
                console.log('✅ Monthly report loaded successfully');
            } else {
                console.error(`❌ Monthly report API failed: ${monthlyResponse.status}`);
            }
            
        } catch (error) {
            console.error('❌ Reports API error:', error.message);
        }
    }
    
    async loadRealAlerts() {
        console.log('🔄 Loading real alerts from API...');
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
    
    showNotImplemented(feature) {
        alert(`⚠️ ${feature} is not yet implemented.\n\nThis is a demonstration interface. The feature will be added in future development phases.`);
    }
}

// Vehicle Events Manager for Real-time Dashboard
class VehicleEventsManager {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
        this.logContent = document.getElementById('events-log-content');
        this.lineNumber = 5;
        this.autoScroll = true;
        this.isPaused = false;
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.stats = {
            total: 0,
            cars: 0,
            trucks: 0,
            motorcycles: 0,
            totalConfidence: 0
        };

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const autoScrollBtn = document.getElementById('auto-scroll');
        const clearLogBtn = document.getElementById('clear-log');
        const pauseBtn = document.getElementById('pause-detection');
        const searchInput = document.getElementById('search');

        if (autoScrollBtn) {
            autoScrollBtn.addEventListener('click', () => {
                this.autoScroll = !this.autoScroll;
                autoScrollBtn.classList.toggle('active', this.autoScroll);
                autoScrollBtn.innerHTML = this.autoScroll ? '📜 Auto Scroll' : '📜 Manual';
            });
        }

        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => {
                this.clearLog();
            });
        }

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.isPaused = !this.isPaused;
                pauseBtn.innerHTML = this.isPaused ? '▶️ Resume' : '⏸️ Pause';
                pauseBtn.classList.toggle('active', this.isPaused);
                
                if (this.isPaused) {
                    this.disconnect();
                } else {
                    this.connect();
                }
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterLog(e.target.value);
            });
        }
    }

    start() {
        this.addSystemMessage('🔄 Connecting to real-time event stream...');
        this.connect();
    }

    connect() {
        if (this.isPaused || this.websocket) return;

        // Skip WebSocket connection for now and use REST polling
        this.addSystemMessage('🔄 Using REST API polling for real-time events...');
        this.startPolling();
        return;

        try {
            // Convert HTTP API URL to WebSocket URL
            let wsUrl = this.apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
            wsUrl = wsUrl + '/events';  // WebSocket endpoint for events
            
            this.addSystemMessage(`🔗 Attempting connection to ${wsUrl}`);
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                this.reconnectAttempts = 0;
                this.addSystemMessage('✅ Connected to real-time event stream');
                document.getElementById('last-detection').textContent = 'Last detection: Connected, waiting for events...';
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleRealtimeEvent(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                this.websocket = null;
                if (!this.isPaused && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    this.addSystemMessage(`🔄 Connection lost. Reconnecting... (attempt ${this.reconnectAttempts})`);
                    setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
                } else {
                    this.addSystemMessage('❌ WebSocket connection failed. Using fallback polling...');
                    this.startPolling();
                }
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addSystemMessage('⚠️ WebSocket connection error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.addSystemMessage('❌ Failed to establish WebSocket connection. Using fallback...');
            this.startPolling();
        }
    }

    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
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
                    events.forEach(event => this.handleRealtimeEvent(event));
                }
            } catch (error) {
                console.error('Polling failed:', error);
            }
        }, 3000);
    }

    handleRealtimeEvent(data) {
        if (this.isPaused) return;

        const timestamp = new Date().toLocaleTimeString();

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
                this.addSystemMessage(`🔧 ${data.message || 'System health check completed'}`);
                break;

            case 'api_request_success':
                // Only log significant API events to avoid spam
                if (data.endpoint && data.endpoint.includes('detection')) {
                    this.addSystemMessage(`📡 Detection API request processed (${data.duration_ms}ms)`);
                }
                break;

            case 'radar_alert':
                this.addSystemMessage(`📡 Radar alert: ${data.message || 'Motion detected'}`);
                break;

            default:
                // Generic event handling
                if (data.message) {
                    this.addSystemMessage(`ℹ️ ${data.message}`);
                }
                break;
        }

        // Update last detection time
        document.getElementById('last-detection').textContent = `Last detection: ${timestamp}`;
    }

    addVehicleDetection(vehicleType, confidence, location, additionalInfo = '') {
        if (this.isPaused) return;

        const timestamp = new Date().toLocaleTimeString();
        const logLine = document.createElement('div');
        logLine.className = 'events-log-line new-detection';
        
        const confidenceColor = confidence > 80 ? '#38b2ac' : confidence > 60 ? '#ed8936' : '#e53e3e';
        
        logLine.innerHTML = `
            <div class="events-line-number">${this.lineNumber}</div>
            <div class="events-log-text">
                <span class="events-timestamp">[${timestamp}]</span> 
                🚗 Detected <span class="events-vehicle-type">${vehicleType}</span> 
                with <span class="events-confidence" style="color: ${confidenceColor}">${confidence}% confidence</span>
                ${location ? ` at <span class="events-location">${location}</span>` : ''}
                ${additionalInfo ? ` - ${additionalInfo}` : ''}
            </div>
        `;

        this.logContent.appendChild(logLine);
        this.lineNumber++;

        // Update stats
        this.updateStats(vehicleType, confidence);

        // Auto scroll
        if (this.autoScroll) {
            this.logContent.scrollTop = this.logContent.scrollHeight;
        }

        // Remove highlight after animation
        setTimeout(() => {
            logLine.classList.remove('new-detection');
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

        document.getElementById('total-detections').textContent = this.stats.total;
        document.getElementById('cars-count').textContent = this.stats.cars;
        document.getElementById('trucks-count').textContent = this.stats.trucks;
        document.getElementById('motorcycles-count').textContent = this.stats.motorcycles;
        
        const avgConfidence = this.stats.total > 0 ? Math.round(this.stats.totalConfidence / this.stats.total) : 0;
        document.getElementById('avg-confidence').textContent = avgConfidence + '%';
    }

    clearLog() {
        if (this.logContent) {
            this.logContent.innerHTML = '';
            this.lineNumber = 1;
            this.stats = { total: 0, cars: 0, trucks: 0, motorcycles: 0, totalConfidence: 0 };
            this.updateStatsDisplay();
            this.addSystemMessage('📝 Log cleared');
        }
    }

    updateStatsDisplay() {
        document.getElementById('total-detections').textContent = '0';
        document.getElementById('cars-count').textContent = '0';
        document.getElementById('trucks-count').textContent = '0';
        document.getElementById('motorcycles-count').textContent = '0';
        document.getElementById('avg-confidence').textContent = '0%';
    }

    addSystemMessage(message) {
        if (!this.logContent) return;

        const logLine = document.createElement('div');
        logLine.className = 'events-log-line';
        logLine.innerHTML = `
            <div class="events-line-number">${this.lineNumber}</div>
            <div class="events-log-text">${message}</div>
        `;
        this.logContent.appendChild(logLine);
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