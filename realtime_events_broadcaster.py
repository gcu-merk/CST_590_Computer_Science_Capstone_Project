#!/usr/bin/env python3
"""
Real-time Events Broadcaster Service
Monitors SQLite database for new ServiceLogger entries and broadcasts them via WebSocket

This service:
- Monitors the centralized_logs.db for new entries using database polling
- Filters for relevant business events for the dashboard
- Broadcasts events to connected WebSocket clients via the edge API gateway
- Provides event deduplication and rate limiting
- Maintains connection health with the API gateway

Architecture:
SQLite Database -> Events Broadcaster -> Edge API Gateway -> WebSocket Clients -> Dashboard
"""

import sqlite3
import time
import json
import logging
import os
import sys
import threading
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
import requests
from dataclasses import dataclass

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "edge_processing"))
from shared_logging import ServiceLogger, CorrelationContext

@dataclass
class EventRecord:
    """Represents a database event record"""
    id: int
    timestamp: str
    service_name: str
    level: str
    message: str
    business_event: str
    correlation_id: str
    extra_data: str

class RealTimeEventsBroadcaster:
    """
    Service that monitors the centralized logging database and broadcasts
    relevant events to WebSocket clients through the API gateway
    """
    
    def __init__(self, 
                 db_path: str = None,
                 api_gateway_url: str = None,
                 poll_interval: float = 1.0,
                 batch_size: int = 50):
        """
        Initialize the events broadcaster
        
        Args:
            db_path: Path to SQLite database (default: data/centralized_logs.db)
            api_gateway_url: URL of API gateway for broadcasting (default: http://localhost:5000)
            poll_interval: How often to check for new events (seconds)
            batch_size: Maximum events to process per batch
        """
        
        # Initialize logging
        self.logger = ServiceLogger("realtime_events_broadcaster")
        
        # Configuration
        self.db_path = db_path or os.path.join(current_dir, 'data', 'centralized_logs.db')
        self.api_gateway_url = api_gateway_url or 'http://localhost:5000'
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        
        # State management
        self.last_processed_id = 0
        self.running = False
        self.processed_events: Set[int] = set()  # Deduplication
        self.stats = {
            "events_processed": 0,
            "events_broadcasted": 0,
            "api_errors": 0,
            "database_errors": 0,
            "start_time": None
        }
        
        # Event filtering - only broadcast these business events
        self.relevant_events = {
            'vehicle_detection',
            'vehicle_detected', 
            'radar_alert',
            'system_status',
            'health_check',
            'api_request_success',
            'websocket_connection',
            'websocket_disconnection',
            'detection_processed',
            'consolidation_complete'
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Real-time events broadcaster initialized", extra={
            "business_event": "broadcaster_initialized",
            "db_path": self.db_path,
            "api_gateway_url": self.api_gateway_url,
            "poll_interval": self.poll_interval,
            "relevant_events": list(self.relevant_events)
        })
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Shutdown signal received", extra={
            "business_event": "broadcaster_shutdown_signal",
            "signal": signum
        })
        self.stop()
    
    def start(self):
        """Start the real-time events broadcasting service"""
        if self.running:
            self.logger.warning("Broadcaster already running")
            return
        
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        self.logger.info("Starting real-time events broadcaster", extra={
            "business_event": "broadcaster_start"
        })
        
        try:
            # Initialize database connection and get starting position
            self._initialize_database_position()
            
            # Start the main processing loop
            self._run_processing_loop()
            
        except Exception as e:
            self.logger.error("Fatal error in broadcaster", extra={
                "business_event": "broadcaster_fatal_error",
                "error": str(e)
            })
            self.running = False
            raise
    
    def stop(self):
        """Stop the broadcasting service gracefully"""
        if not self.running:
            return
        
        self.running = False
        
        self.logger.info("Stopping real-time events broadcaster", extra={
            "business_event": "broadcaster_stop",
            "final_stats": self.stats
        })
    
    def _initialize_database_position(self):
        """Initialize the starting position in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the highest ID to start from (avoid replaying old events)
            cursor.execute("SELECT MAX(id) FROM logs WHERE business_event IS NOT NULL")
            result = cursor.fetchone()
            
            if result and result[0]:
                self.last_processed_id = result[0]
                self.logger.info("Initialized database position", extra={
                    "business_event": "database_position_initialized",
                    "starting_id": self.last_processed_id
                })
            else:
                self.logger.info("No existing events found, starting from beginning", extra={
                    "business_event": "database_position_reset"
                })
            
            conn.close()
            
        except Exception as e:
            self.logger.error("Failed to initialize database position", extra={
                "business_event": "database_init_failure",
                "error": str(e)
            })
            self.stats["database_errors"] += 1
    
    def _run_processing_loop(self):
        """Main processing loop - polls database and broadcasts events"""
        
        self.logger.info("Starting event processing loop", extra={
            "business_event": "processing_loop_start"
        })
        
        while self.running:
            try:
                # Get new events from database
                new_events = self._get_new_events()
                
                # Process and broadcast events
                if new_events:
                    self._process_events(new_events)
                
                # Sleep before next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error("Error in processing loop", extra={
                    "business_event": "processing_loop_error",
                    "error": str(e)
                })
                self.stats["database_errors"] += 1
                
                # Back off on errors
                time.sleep(self.poll_interval * 2)
        
        self.logger.info("Processing loop stopped", extra={
            "business_event": "processing_loop_stop"
        })
    
    def _get_new_events(self) -> List[EventRecord]:
        """Get new events from the database since last check"""
        events = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for new events with relevant business_event types
            query = """
                SELECT id, timestamp, service_name, level, message, 
                       business_event, correlation_id, extra_data
                FROM logs 
                WHERE id > ? 
                  AND business_event IS NOT NULL
                  AND business_event IN ({})
                ORDER BY id ASC 
                LIMIT ?
            """.format(','.join('?' * len(self.relevant_events)))
            
            params = [self.last_processed_id] + list(self.relevant_events) + [self.batch_size]
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            for row in rows:
                event = EventRecord(
                    id=row['id'],
                    timestamp=row['timestamp'],
                    service_name=row['service_name'],
                    level=row['level'],
                    message=row['message'],
                    business_event=row['business_event'],
                    correlation_id=row['correlation_id'],
                    extra_data=row['extra_data']
                )
                events.append(event)
                
                # Update last processed ID
                self.last_processed_id = max(self.last_processed_id, event.id)
            
            conn.close()
            
            if events:
                self.logger.debug("Retrieved new events from database", extra={
                    "business_event": "events_retrieved",
                    "event_count": len(events),
                    "last_id": self.last_processed_id
                })
            
        except Exception as e:
            self.logger.error("Failed to retrieve events from database", extra={
                "business_event": "database_query_failure",
                "error": str(e)
            })
            self.stats["database_errors"] += 1
        
        return events
    
    def _process_events(self, events: List[EventRecord]):
        """Process and broadcast a batch of events"""
        
        for event in events:
            try:
                # Skip if already processed (deduplication)
                if event.id in self.processed_events:
                    continue
                
                # Convert to broadcast format
                broadcast_data = self._format_event_for_broadcast(event)
                
                # Broadcast to API gateway
                success = self._broadcast_event(broadcast_data)
                
                if success:
                    self.stats["events_broadcasted"] += 1
                    self.processed_events.add(event.id)
                    
                    # Keep processed_events set reasonable size
                    if len(self.processed_events) > 10000:
                        # Keep only the most recent 5000
                        sorted_ids = sorted(self.processed_events)
                        self.processed_events = set(sorted_ids[-5000:])
                
                self.stats["events_processed"] += 1
                
            except Exception as e:
                self.logger.error("Failed to process event", extra={
                    "business_event": "event_processing_failure",
                    "event_id": event.id,
                    "error": str(e)
                })
    
    def _format_event_for_broadcast(self, event: EventRecord) -> Dict:
        """Format database event for WebSocket broadcast"""
        
        # Parse extra_data JSON if available
        extra_data = {}
        if event.extra_data:
            try:
                extra_data = json.loads(event.extra_data)
            except json.JSONDecodeError:
                pass
        
        # Create broadcast-ready event
        broadcast_event = {
            'timestamp': event.timestamp,
            'service_name': event.service_name,
            'level': event.level,
            'message': event.message,
            'business_event': event.business_event,
            'correlation_id': event.correlation_id,
            'event_id': event.id,
            **extra_data  # Merge extra data fields
        }
        
        return broadcast_event
    
    def _broadcast_event(self, event_data: Dict) -> bool:
        """Broadcast event to API gateway WebSocket clients"""
        
        try:
            # Send to API gateway's broadcast endpoint
            broadcast_url = f"{self.api_gateway_url}/api/events/broadcast"
            
            response = requests.post(
                broadcast_url,
                json=event_data,
                headers={'Content-Type': 'application/json'},
                timeout=5  # 5 second timeout
            )
            
            if response.status_code == 200:
                self.logger.debug("Event broadcasted successfully", extra={
                    "business_event": "event_broadcast_success",
                    "event_id": event_data.get('event_id'),
                    "event_type": event_data.get('business_event')
                })
                return True
            else:
                self.logger.warning("Broadcast failed with HTTP error", extra={
                    "business_event": "event_broadcast_http_error",
                    "status_code": response.status_code,
                    "response_text": response.text[:200]
                })
                self.stats["api_errors"] += 1
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.warning("Network error during broadcast", extra={
                "business_event": "event_broadcast_network_error",
                "error": str(e)
            })
            self.stats["api_errors"] += 1
            return False
        except Exception as e:
            self.logger.error("Unexpected error during broadcast", extra={
                "business_event": "event_broadcast_unexpected_error",
                "error": str(e)
            })
            self.stats["api_errors"] += 1
            return False
    
    def get_stats(self) -> Dict:
        """Get current broadcaster statistics"""
        current_stats = self.stats.copy()
        
        if current_stats["start_time"]:
            start_dt = datetime.fromisoformat(current_stats["start_time"])
            uptime_seconds = (datetime.now() - start_dt).total_seconds()
            current_stats["uptime_seconds"] = uptime_seconds
            
            if uptime_seconds > 0:
                current_stats["events_per_second"] = current_stats["events_processed"] / uptime_seconds
        
        current_stats["running"] = self.running
        current_stats["last_processed_id"] = self.last_processed_id
        current_stats["processed_events_count"] = len(self.processed_events)
        
        return current_stats


def main():
    """Main entry point for the real-time events broadcaster service"""
    
    # Configuration from environment variables
    db_path = os.environ.get('CENTRALIZED_DB_PATH')
    api_gateway_url = os.environ.get('API_GATEWAY_URL', 'http://localhost:5000')
    poll_interval = float(os.environ.get('POLL_INTERVAL', '1.0'))
    batch_size = int(os.environ.get('BATCH_SIZE', '50'))
    
    try:
        # Create and start broadcaster
        broadcaster = RealTimeEventsBroadcaster(
            db_path=db_path,
            api_gateway_url=api_gateway_url,
            poll_interval=poll_interval,
            batch_size=batch_size
        )
        
        broadcaster.start()
        
    except KeyboardInterrupt:
        print("Broadcaster shutdown requested by user")
    except Exception as e:
        print(f"Broadcaster failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()