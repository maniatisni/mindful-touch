#!/usr/bin/env python3
"""
Integration tests for WebSocket communication between detection backend and frontend
"""
import asyncio
import json
import time
import subprocess
import signal
import sys
import os
from pathlib import Path
import threading
import websockets
import pytest
import pytest_asyncio
import logging

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.server.websocket_server import DetectionWebSocketServer

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWebSocketServer:
    """Test suite for standalone WebSocket server functionality"""
    
    @pytest_asyncio.fixture
    async def websocket_server(self):
        """Create and start a WebSocket server for testing"""
        import random
        port = random.randint(8800, 8900)  # Use random port to avoid conflicts
        server = DetectionWebSocketServer(host="localhost", port=port)
        
        # Start server in background thread
        thread = server.run_in_thread()
        await asyncio.sleep(2)  # Give more time for server startup
        
        # Store port for tests to use
        server.test_port = port
        yield server
        
        # Improved cleanup
        try:
            server.running = False
            if hasattr(server, 'server') and server.server:
                # Just close, don't wait in fixture
                server.server.close()
        except Exception as e:
            logger.warning(f"Error during server cleanup: {e}")
        
        # Give time for cleanup
        await asyncio.sleep(0.5)
    
    @pytest.mark.asyncio
    async def test_server_startup_and_connection(self, websocket_server):
        """Test that WebSocket server starts and accepts connections"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        async with websockets.connect(uri) as websocket:
            # Just test that we can connect and close
            logger.info("✅ WebSocket server accepts connections")
    
    @pytest.mark.asyncio
    async def test_ping_pong_communication(self, websocket_server):
        """Test basic ping-pong communication"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        async with websockets.connect(uri) as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Receive pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            assert data["type"] == "pong"
            logger.info("✅ Ping-pong communication works")
    
    @pytest.mark.asyncio
    async def test_region_toggle_functionality(self, websocket_server):
        """Test region toggle message handling"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        async with websockets.connect(uri) as websocket:
            # Test different regions
            regions_to_test = ["scalp", "eyebrows", "eyes", "mouth", "beard"]
            
            for region in regions_to_test:
                for enabled in [True, False]:
                    toggle_message = {
                        "type": "toggle_region",
                        "region": region,
                        "enabled": enabled
                    }
                    await websocket.send(json.dumps(toggle_message))
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    assert data["type"] == "region_toggle_response"
                    assert data["region"] == region
                    assert data["enabled"] == enabled
                    assert data["status"] == "success"
            
            logger.info("✅ Region toggle functionality works for all regions")
    
    @pytest.mark.asyncio
    async def test_detection_data_broadcasting(self, websocket_server):
        """Test detection data broadcasting to clients"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        mock_detection_data = {
            "timestamp": time.time(),
            "hands_detected": True,
            "face_detected": True,
            "contact_points": 2,
            "alerts_active": ["scalp", "eyebrows"],
            "active_regions": ["scalp", "eyebrows", "eyes"]
        }
        
        async with websockets.connect(uri) as websocket:
            # Trigger detection data update
            websocket_server.update_detection_data(mock_detection_data)
            
            # Wait for broadcast message
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            assert data["type"] == "detection_data"
            assert data["data"]["hands_detected"] is True
            assert data["data"]["face_detected"] is True
            assert data["data"]["contact_points"] == 2
            assert "scalp" in data["data"]["alerts_active"]
            assert "eyebrows" in data["data"]["alerts_active"]
            
            logger.info("✅ Detection data broadcasting works")
    
    @pytest.mark.asyncio
    async def test_multiple_client_connections(self, websocket_server):
        """Test multiple clients can connect and receive data simultaneously"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        # Connect multiple clients
        async with websockets.connect(uri) as client1, \
                   websockets.connect(uri) as client2, \
                   websockets.connect(uri) as client3:
            
            # Send detection data
            mock_data = {
                "timestamp": time.time(),
                "hands_detected": False,
                "face_detected": True,
                "contact_points": 0,
                "alerts_active": [],
                "active_regions": ["eyes"]
            }
            
            websocket_server.update_detection_data(mock_data)
            
            # All clients should receive the data
            clients = [client1, client2, client3]
            responses = []
            
            for client in clients:
                response = await asyncio.wait_for(client.recv(), timeout=5.0)
                data = json.loads(response)
                responses.append(data)
            
            # Verify all clients received the same data
            for response in responses:
                assert response["type"] == "detection_data"
                assert response["data"]["hands_detected"] is False
                assert response["data"]["face_detected"] is True
                assert response["data"]["contact_points"] == 0
            
            logger.info("✅ Multiple client connections work correctly")
    
    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, websocket_server):
        """Test server handles invalid messages gracefully"""
        uri = f"ws://localhost:{websocket_server.test_port}"
        
        async with websockets.connect(uri) as websocket:
            # Send invalid JSON
            await websocket.send("invalid json")
            
            # Server should still be responsive
            await asyncio.sleep(0.5)
            
            # Test with valid message to ensure server is still working
            await websocket.send(json.dumps({"type": "ping"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            assert data["type"] == "pong"
            logger.info("✅ Server handles invalid messages gracefully")


class TestEndToEndIntegration:
    """End-to-end integration tests with actual backend process"""
    
    @pytest.fixture
    def backend_process(self):
        """Start the actual detection backend process"""
        logger.info("🚀 Starting detection backend process...")
        
        process = subprocess.Popen(
            [sys.executable, "-m", "backend.detection.main", "--headless"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give backend more time to start (MediaPipe models take time to load)
        logger.info("Waiting for backend to initialize...")
        time.sleep(8)
        
        # Verify process is running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"Backend failed to start. Stdout: {stdout}, Stderr: {stderr}")
        
        # Additional check: try to connect to WebSocket port
        logger.info("Checking if WebSocket server is ready...")
        import socket
        for attempt in range(10):  # Try for 10 seconds
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 8765))
                sock.close()
                if result == 0:
                    logger.info("✅ WebSocket server is ready!")
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            pytest.fail("WebSocket server did not start within timeout")
        
        yield process
        
        # Cleanup
        logger.info("🧹 Cleaning up backend process...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    @pytest.mark.asyncio
    async def test_backend_websocket_connection(self, backend_process):
        """Test connection to the actual backend WebSocket server"""
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Just test that connection succeeds (no .open attribute needed)
            logger.info("✅ Successfully connected to backend WebSocket")
    
    @pytest.mark.asyncio
    async def test_backend_ping_pong(self, backend_process):
        """Test ping-pong with actual backend"""
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Backend may send detection_data messages, so we need to look for pong
            pong_received = False
            for attempt in range(10):  # Try up to 10 messages
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                if data["type"] == "pong":
                    pong_received = True
                    break
                elif data["type"] == "detection_data":
                    # This is expected - backend streams detection data
                    logger.debug("Received detection data (expected)")
                    continue
            
            assert pong_received, "Did not receive pong response"
            logger.info("✅ Backend ping-pong communication works")
    
    @pytest.mark.asyncio
    async def test_backend_region_toggles(self, backend_process):
        """Test region toggle functionality with actual backend"""
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Test toggling a region
            toggle_message = {
                "type": "toggle_region",
                "region": "scalp",
                "enabled": True
            }
            await websocket.send(json.dumps(toggle_message))
            
            # Look for region toggle response among multiple messages
            toggle_response_received = False
            for attempt in range(10):
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                if data["type"] == "region_toggle_response":
                    assert data["region"] == "scalp"
                    assert data["enabled"] is True
                    assert data["status"] == "success"
                    toggle_response_received = True
                    break
                elif data["type"] == "detection_data":
                    continue  # Skip detection data messages
            
            assert toggle_response_received, "Did not receive region toggle response"
            logger.info("✅ Backend region toggle functionality works")
    
    @pytest.mark.asyncio
    async def test_backend_detection_data_stream(self, backend_process):
        """Test that backend streams detection data"""
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Wait for detection data (backend should be sending automatically)
            detection_data_received = False
            
            for attempt in range(20):  # Try for up to 20 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data["type"] == "detection_data":
                        # Verify required fields exist
                        required_fields = ["hands_detected", "face_detected", "contact_points", "alerts_active"]
                        assert all(field in data["data"] for field in required_fields)
                        
                        detection_data_received = True
                        logger.info("✅ Backend detection data streaming works")
                        break
                        
                except asyncio.TimeoutError:
                    continue
            
            assert detection_data_received, "No detection data received from backend"
    
    @pytest.mark.asyncio
    async def test_backend_multiple_clients(self, backend_process):
        """Test multiple clients can connect to backend simultaneously"""
        uri = "ws://localhost:8765"
        
        # Connect multiple clients
        async with websockets.connect(uri) as client1, \
                   websockets.connect(uri) as client2:
            
            # Both clients should be able to ping and receive responses
            for i, client in enumerate([client1, client2], 1):
                await client.send(json.dumps({"type": "ping"}))
                
                # Look for pong response among multiple messages
                pong_received = False
                for attempt in range(10):
                    response = await asyncio.wait_for(client.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if data["type"] == "pong":
                        pong_received = True
                        break
                    elif data["type"] == "detection_data":
                        continue  # Skip detection data messages
                
                assert pong_received, f"Client {i} did not receive pong response"
            
            logger.info("✅ Backend supports multiple simultaneous clients")


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_connection_to_nonexistent_server(self):
        """Test handling of connection failures"""
        with pytest.raises(Exception):  # Should raise connection error
            await websockets.connect("ws://localhost:9999")
        
        logger.info("✅ Correctly handles connection to non-existent server")
    
    @pytest.mark.asyncio
    async def test_malformed_json_resilience(self):
        """Test that invalid JSON doesn't crash the connection"""
        # This test requires a running server, so we'll create a minimal one
        import random
        port = random.randint(8900, 8950)
        server = DetectionWebSocketServer(host="localhost", port=port)
        thread = server.run_in_thread()
        await asyncio.sleep(2)
        
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri) as websocket:
                # Send malformed JSON
                await websocket.send("{ invalid json")
                
                # Server should still be responsive
                await asyncio.sleep(0.5)
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                assert data["type"] == "pong"
                logger.info("✅ Server resilient to malformed JSON")
        
        finally:
            # Improved cleanup
            try:
                server.running = False
                if hasattr(server, 'server') and server.server:
                    server.server.close()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
            await asyncio.sleep(0.5)


# Pytest configuration and markers
def test_backend_startup_command():
    """Test that the backend command can be invoked (non-async test)"""
    result = subprocess.run(
        [sys.executable, "-m", "backend.detection.main", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Mindful Touch" in result.stdout
    assert "--headless" in result.stdout
    logger.info("✅ Backend command line interface works correctly")