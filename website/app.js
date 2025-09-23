// Traffic Analytics Dashboard - JavaScript
// GitHub Pages implementation with Tailscale API integration

class TrafficDashboard {
    constructor() {
        this.apiBaseUrl = localStorage.getItem('api-url') || 'http://100.121.231.16:5000/api';
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
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
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
            this.updateApiStatus(false);
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/health`, {
                timeout: 5000
            });
            
            if (response.ok) {
                this.updateApiStatus(true);
                this.loadRealData();
            } else {
                this.updateApiStatus(false);
            }
        } catch (error) {
            console.log('API connection failed:', error);
            this.updateApiStatus(false);
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
            const response = await fetch(`${apiUrl}/api/health`, {
                timeout: 10000
            });
            
            if (response.ok) {
                const data = await response.json();
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
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            statusDiv.textContent = `❌ Connection failed: ${error.message}`;
            statusDiv.style.background = '#fed7d7';
            statusDiv.style.color = '#c53030';
        }
    }
    
    updateApiStatus(isOnline) {
        this.isOnline = isOnline;
        const indicator = document.getElementById('api-indicator');
        const connectBtn = document.getElementById('connect-btn');
        
        if (isOnline) {
            indicator.className = 'status-indicator online';
            indicator.querySelector('.status-text').textContent = 'API Connected';
            connectBtn.textContent = 'Reconfigure';
        } else {
            indicator.className = 'status-indicator offline';
            indicator.querySelector('.status-text').textContent = 'API Offline';
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
                const detectionsResponse = await fetch(`${this.apiBaseUrl}/api/detections?seconds=86400`);
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
                const speedsResponse = await fetch(`${this.apiBaseUrl}/api/speeds?seconds=86400`);
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
                const analyticsResponse = await fetch(`${this.apiBaseUrl}/api/analytics`);
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
            
            // Load weather data
            try {
                const weatherResponse = await fetch(`${this.apiBaseUrl}/api/weather`);
                if (weatherResponse.ok) {
                    const weatherData = await weatherResponse.json();
                    this.updateWeatherData(weatherData);
                    console.log('✅ Weather data loaded successfully');
                } else {
                    console.error(`❌ Weather API failed: ${weatherResponse.status}`);
                    document.getElementById('temperature').textContent = `Error ${weatherResponse.status}`;
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
        
        // Update temperature if available
        if (weatherData.data && weatherData.data.temperature) {
            const tempF = Math.round(weatherData.data.temperature * 9/5 + 32);
            document.getElementById('temperature').textContent = `${tempF}°F`;
            console.log(`📊 Updated temperature: ${tempF}°F`);
        } else if (weatherData.temperature) {
            // Handle direct temperature field
            const tempF = Math.round(weatherData.temperature * 9/5 + 32);
            document.getElementById('temperature').textContent = `${tempF}°F`;
            console.log(`📊 Updated temperature: ${tempF}°F`);
        } else {
            document.getElementById('temperature').textContent = 'No Temp Data';
            console.log('📊 No temperature data in weather response');
        }
        
        // Update weather condition display if element exists
        const weatherElement = document.getElementById('weather-condition');
        if (weatherElement && weatherData.sky_condition) {
            weatherElement.textContent = weatherData.sky_condition.condition || 'Unknown';
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
            default:
                // Overview tab - data already loaded in loadRealData
                break;
        }
    }
    
    async loadWeeklyPatterns() {
        console.log('🔄 Loading weekly patterns from API...');
        // Placeholder for future implementation when historical endpoints are available
    }
    
    async loadSafetyData() {
        console.log('🔄 Loading safety data from API...');
        // Placeholder for future implementation when safety endpoints are available
    }
    
    async loadReportsData() {
        console.log('🔄 Loading reports data from API...');
        // Placeholder for future implementation when reports endpoints are available
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