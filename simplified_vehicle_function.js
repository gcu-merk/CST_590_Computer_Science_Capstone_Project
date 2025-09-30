    updateVehicleCountFrom24Hours(consolidatedData) {
        if (!consolidatedData || !consolidatedData.events) {
            console.error('❌ No consolidated data received for 24h vehicle count');
            document.getElementById('total-vehicles').textContent = 'No Data';
            return;
        }

        const events = consolidatedData.events;
        
        // Calculate metrics from last 24 hours
        const now = new Date();
        const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        
        const last24hEvents = events.filter(event => {
            const eventTime = new Date(event.created_at || event.timestamp);
            return eventTime >= last24h && eventTime <= now;
        });
        
        // Update vehicle count
        document.getElementById('total-vehicles').textContent = last24hEvents.length.toLocaleString();
        console.log(`📊 Updated 24h vehicle count: ${last24hEvents.length}`);
        
        // Calculate speed metrics if we have radar data
        const speedEvents = last24hEvents.filter(event => 
            event.radar_data && 
            event.radar_data.speed !== undefined && 
            event.radar_data.speed !== null && 
            event.radar_data.speed > 0
        );
        
        if (speedEvents.length > 0) {
            const avgSpeed24h = speedEvents.reduce((sum, event) => sum + event.radar_data.speed, 0) / speedEvents.length;
            document.getElementById('avg-speed').textContent = avgSpeed24h.toFixed(1);
            
            // Count speed violations (> 25 mph)
            const violations24h = speedEvents.filter(event => event.radar_data.speed > 25).length;
            document.getElementById('speed-violations').textContent = violations24h;
            
            // Update violations card appearance based on severity
            const violationsCard = document.getElementById('violations-card');
            if (violationsCard) {
                if (violations24h > 10) {
                    violationsCard.classList.add('high-alert');
                } else {
                    violationsCard.classList.remove('high-alert');
                }
            }
            
            console.log(`📊 Updated 24h speeds - Avg: ${avgSpeed24h.toFixed(1)} mph, Violations: ${violations24h} (out of ${speedEvents.length} readings)`);
        } else {
            document.getElementById('avg-speed').textContent = 'No Data';
            document.getElementById('speed-violations').textContent = '0';
            console.log('📊 No speed data available for 24h average');
        }
        
        // Update chart with hourly detection data from last 24 hours
        this.updateTrafficChartFromDetections(last24hEvents);
    }