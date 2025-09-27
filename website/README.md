# 🚗 CST 590 Traffic Monitoring System - Web Dashboard

This is the web dashboard for the CST 590 Computer Science Capstone Project, a real-time traffic monitoring system using AI cameras and radar sensors for Grand Canyon University.

## 🌐 Live Demo

**Website**: https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/

The dashboard provides real-time visualization of:
- Traffic flow analytics
- Vehicle detection and counting
- Speed monitoring
- Weather impact analysis
- Safety metrics and alerts
- System performance monitoring

## 📁 Project Structure

```
website/
├── index.html          # Main dashboard page
├── app.js             # JavaScript application logic
├── styles.css         # Responsive CSS styling
├── api-test.html      # API connectivity testing page
├── .nojekyll         # GitHub Pages configuration
└── README.md         # This documentation
```

## 🚀 Features

### Real-Time Dashboard
- **Live Traffic Metrics**: Current vehicle counts, speeds, and flow rates
- **Interactive Charts**: Traffic patterns over time with customizable time ranges
- **Weather Integration**: Real-time weather data and its impact on traffic
- **Alert System**: Real-time notifications for traffic incidents and anomalies

### Safety Analysis
- **Speed Monitoring**: Average speeds and violation detection
- **Traffic Violations**: Stop sign violations and unsafe behaviors
- **Risk Assessment**: Safety recommendations based on traffic patterns
- **Historical Analysis**: Trend analysis for safety improvements

### System Monitoring
- **API Status**: Real-time connection status to the Raspberry Pi system
- **Data Quality**: Monitoring of sensor health and data accuracy
- **Performance Metrics**: System uptime and processing statistics

### Responsive Design
- **Mobile-Friendly**: Optimized for phones, tablets, and desktop
- **Cross-Browser**: Compatible with modern browsers
- **Accessibility**: WCAG 2.1 compliant design patterns

## 🛠️ Technical Implementation

### Frontend Technologies
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **Vanilla JavaScript**: ES6+ with modular architecture
- **Chart.js**: Interactive charts and data visualization
- **Socket.IO**: Real-time WebSocket communication

### API Integration
- **RESTful API**: Connection to Raspberry Pi backend services
- **Real-time Updates**: WebSocket integration for live data
- **Offline Support**: Graceful degradation when API is unavailable
- **Error Handling**: Comprehensive error states and user feedback

### Performance Optimizations
- **Lazy Loading**: Charts and images loaded on demand
- **Caching**: Local storage for API endpoints and user preferences
- **Debounced Updates**: Efficient data refresh strategies
- **Responsive Images**: Optimized for different screen sizes

## 🔧 Local Development

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (optional, for CORS compliance)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
   cd CST_590_Computer_Science_Capstone_Project/website
   ```

2. **Serve locally** (optional):
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js
   npx http-server
   
   # Using PHP
   php -S localhost:8000
   ```

3. **Open in browser**:
   ```
   http://localhost:8000
   ```

### Development Tips
- **API Configuration**: Use the "Configure API" button to set your Raspberry Pi endpoint
- **Debug Mode**: Open browser DevTools to see console logs and network requests  
- **Mobile Testing**: Use browser DevTools device simulation for responsive testing

## 📡 API Configuration

The dashboard connects to a Raspberry Pi running the traffic monitoring system:

### Default Endpoints
- **Production**: `https://edge-traffic-monitoring.taild46447.ts.net/api`
- **Local Development**: `http://[PI-IP]:5000/api`

### API Test Page
Visit `/api-test.html` to verify connectivity and test API responses.

### Supported API Endpoints
- `GET /health` - System health check
- `GET /traffic/current` - Current traffic metrics
- `GET /traffic/history` - Historical data
- `GET /weather/current` - Weather conditions
- `WebSocket /events` - Real-time event stream

## 🚀 GitHub Pages Deployment

This website is automatically deployed to GitHub Pages from the `main` branch.

### Deployment Process
1. **Push changes** to the main branch
2. **GitHub Actions** automatically builds and deploys
3. **Live site** updates within minutes at the GitHub Pages URL

### Custom Domain (Optional)
To use a custom domain:
1. Add `CNAME` file with your domain name
2. Configure DNS settings
3. Update GitHub Pages settings

## 📱 Mobile Support

The dashboard is fully responsive and optimized for mobile devices:

### Mobile Features
- **Touch-Friendly**: Large touch targets and gestures
- **Responsive Layout**: Adapts to all screen sizes
- **Offline Indicators**: Clear status when API is unavailable
- **Fast Loading**: Optimized for mobile networks

### Testing on Mobile
- Use browser DevTools device simulation
- Test on actual devices when possible
- Verify touch interactions and scrolling

## 🔍 Troubleshooting

### Common Issues

**API Connection Failed**:
- Verify Raspberry Pi is running and accessible
- Check network connectivity and firewall settings
- Ensure correct API endpoint URL
- Test with `/api-test.html` page

**Charts Not Loading**:
- Check browser console for JavaScript errors
- Verify Chart.js CDN is accessible
- Clear browser cache and reload

**Mobile Display Issues**:
- Test in browser DevTools mobile simulation
- Check CSS media queries are working
- Verify viewport meta tag is present

### Debug Information
- Browser console shows detailed connection logs
- Network tab shows API request/response details
- Local storage shows saved API configurations

## 📚 Project Documentation

### Related Documentation
- **[Main Repository](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)**: Complete project overview
- **[Technical Documentation](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/tree/main/documentation/docs)**: Implementation details
- **[User Guide](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/blob/main/documentation/docs/User_Guide.md)**: End-user documentation
- **[API Documentation](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/blob/main/API_ENDPOINTS_WITH_LINKS.html)**: Complete API reference

### Academic Context
- **Course**: CST 590 Computer Science Capstone
- **Institution**: Grand Canyon University
- **Semester**: Fall 2025
- **Focus**: Real-time AI traffic monitoring and analytics

## 🤝 Contributing

This is an academic capstone project. For questions or collaboration:

1. **Create Issues**: Use GitHub Issues for bug reports or feature requests
2. **Fork & PR**: Submit pull requests for improvements
3. **Documentation**: Help improve documentation and user guides
4. **Testing**: Report compatibility issues across different devices/browsers

## 📄 License

This project is part of an academic capstone and is available for educational purposes. See the [LICENSE](../LICENSE) file for details.

## 🎓 Academic Information

**Grand Canyon University - CST 590 Computer Science Capstone**

This web dashboard demonstrates:
- Modern web development practices
- Real-time data visualization
- Responsive design principles
- API integration and error handling
- Performance optimization techniques
- Accessibility considerations

**Technologies Demonstrated**:
- Frontend: HTML5, CSS3, JavaScript ES6+
- Visualization: Chart.js, real-time updates
- Communication: REST APIs, WebSocket integration
- Deployment: GitHub Pages, CI/CD workflows
- Hardware Integration: Raspberry Pi, AI cameras, sensors

---

*Built with ❤️ for traffic safety and smart city solutions*