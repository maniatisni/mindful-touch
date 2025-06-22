"""
WebSocket server for real-time communication between detection engine and frontend
"""
import asyncio
import json
import logging
import websockets
from typing import Set, Dict, Any
import threading

logger = logging.getLogger(__name__)


class DetectionWebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        self.loop = None  # Store the event loop
        
        # Shared state between detection thread and WebSocket server
        self.latest_detection_data = {}
        self.region_toggles = asyncio.Queue()
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send current state to new client
        if self.latest_detection_data:
            await self.send_to_client(websocket, {
                "type": "detection_data",
                "data": self.latest_detection_data
            })

    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_to_client(self, websocket, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        # Create a copy of clients to avoid modification during iteration
        clients_copy = self.clients.copy()
        
        # Send to all clients concurrently
        await asyncio.gather(
            *[self.send_to_client(client, message) for client in clients_copy],
            return_exceptions=True
        )

    async def handle_client_message(self, websocket, message_str: str):
        """Handle incoming messages from clients"""
        try:
            message = json.loads(message_str)
            message_type = message.get("type")
            
            if message_type == "toggle_region":
                region = message.get("region")
                enabled = message.get("enabled", True)
                
                logger.info(f"Region toggle request: {region} -> {enabled}")
                
                # Add to queue for detection thread to process
                await self.region_toggles.put({
                    "region": region,
                    "enabled": enabled
                })
                
                # Confirm back to client
                await self.send_to_client(websocket, {
                    "type": "region_toggle_response",
                    "region": region,
                    "enabled": enabled,
                    "status": "success"
                })
                
            elif message_type == "ping":
                await self.send_to_client(websocket, {"type": "pong"})
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message_str}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def client_handler(self, websocket):
        """Handle individual client connections"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Store the event loop
        self.loop = asyncio.get_running_loop()
        
        self.server = await websockets.serve(
            self.client_handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        self.running = True
        logger.info("WebSocket server started successfully")

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    def update_detection_data(self, detection_data: Dict[str, Any]):
        """Update detection data (called from detection thread)"""
        self.latest_detection_data = detection_data
        
        # Schedule broadcast in the event loop (thread-safe)
        if self.clients and self.running and self.loop:
            try:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.broadcast_to_all({
                        "type": "detection_data",
                        "data": detection_data,
                        "timestamp": detection_data.get("timestamp")
                    }))
                )
            except Exception as e:
                logger.debug(f"Could not schedule broadcast: {e}")

    async def get_region_toggle(self):
        """Get region toggle request (for detection thread)"""
        try:
            return await asyncio.wait_for(self.region_toggles.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    def run_in_thread(self):
        """Run the WebSocket server in a separate thread"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.start_server())
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("WebSocket server interrupted")
            finally:
                loop.run_until_complete(self.stop_server())
                loop.close()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread