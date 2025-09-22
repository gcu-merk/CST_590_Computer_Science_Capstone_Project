// Traffic Analytics Dashboard - JavaScript
// GitHub Pages implementation with Tailscale API integration

class TrafficDashboard {
    constructor() {
        this.apiBaseUrl = localStorage.getItem('api-url') || '';
        this.isOnline = false;
        this.charts = {};
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupCharts();
        this.checkApiConnection();
        this.loadMockData();
        
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
            const response = await fetch(`${this.apiBaseUrl}/health/database`, {
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
            const response = await fetch(`${apiUrl}/health/database`, {
                timeout: 10000
            });
            
            if (response.ok) {
                const data = await response.json();
                this.apiBaseUrl = apiUrl;
                localStorage.setItem('api-url', apiUrl);
                
                statusDiv.textContent = `✅ Connected! Found ${data.database?.record_count || 0} records`;
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
        if (!this.isOnline) return;
        
        try {
            // Load recent traffic data
            const recentResponse = await fetch(`${this.apiBaseUrl}/traffic/recent?hours=24`);
            if (recentResponse.ok) {
                const recentData = await recentResponse.json();
                this.updateMetricsFromData(recentData.data);
                this.updateTrafficChartFromData(recentData.data);
            }
            
            // Load analytics data
            const analyticsResponse = await fetch(`${this.apiBaseUrl}/traffic/analytics?period=week`);
            if (analyticsResponse.ok) {
                const analyticsData = await analyticsResponse.json();
                this.updateAnalyticsFromData(analyticsData.data);
            }
            
        } catch (error) {
            console.error('Failed to load real data:', error);
            this.updateApiStatus(false);
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
    
    loadMockData() {
        // Load mock data for demonstration
        this.updateTrafficChart('24h');
    }
    
    updateTrafficChart(period) {
        if (!this.charts.traffic) return;
        
        let labels, data;
        
        switch (period) {
            case '24h':
                labels = Array.from({length: 24}, (_, i) => `${i}:00`);
                data = [120, 95, 80, 75, 85, 110, 180, 250, 220, 190, 200, 210, 
                       230, 220, 200, 190, 210, 280, 320, 280, 240, 200, 170, 140];
                break;
            case '7d':
                labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                data = [4230, 3950, 4100, 4200, 4350, 2800, 2600];
                break;
            case '30d':
                labels = Array.from({length: 30}, (_, i) => `${i + 1}`);
                data = Array.from({length: 30}, () => Math.floor(Math.random() * 1000) + 3000);
                break;
        }
        
        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = data;
        this.charts.traffic.update();
    }
    
    loadTabData(tabName) {
        // Load tab-specific data
        switch (tabName) {
            case 'patterns':
                // Update weekly patterns chart if needed
                break;
            case 'safety':
                // Load safety-specific data
                break;
            case 'reports':
                // Update available reports
                break;
            case 'alerts':
                // Load recent alerts
                this.loadAlerts();
                break;
        }
    }
    
    loadAlerts() {
        // Mock alert loading
        const alertsList = document.querySelector('.alerts-section .alert-list');
        if (alertsList) {
            // Alerts are already in HTML, could be updated from API here
        }
    }
    
    filterByLocation(location) {
        // Filter data by location
        console.log('Filtering by location:', location);
        
        if (location === 'all') {
            // Show all data
        } else {
            // Filter data for specific location
            this.showNotImplemented('Location filtering');
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