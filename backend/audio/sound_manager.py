"""Sound manager for playing system sounds on macOS."""

import os
import subprocess
import platform
from typing import Optional


class SoundManager:
    """Manager for playing notification sounds."""
    
    # Sound type mappings
    SOUND_MAPPINGS = {
        'Chime': 'Ping',
        'Beep': 'Pop', 
        'Gentle': 'Purr'
    }
    
    # Fallback system sound paths for macOS
    FALLBACK_PATHS = {
        'Ping': '/System/Library/Sounds/Ping.aiff',
        'Pop': '/System/Library/Sounds/Pop.aiff', 
        'Purr': '/System/Library/Sounds/Purr.aiff',
        'Glass': '/System/Library/Sounds/Glass.aiff',
        'Tink': '/System/Library/Sounds/Tink.aiff'
    }
    
    def __init__(self):
        self.is_macos = platform.system() == 'Darwin'
        self.sound_enabled = True
        
    def play_sound(self, sound_type: str) -> bool:
        """Play a system sound by type.
        
        Args:
            sound_type: Sound type ('Chime', 'Beep', 'Gentle')
            
        Returns:
            True if sound was played successfully, False otherwise
        """
        if not self.sound_enabled:
            return False
            
        if not self.is_macos:
            print(f"Sound playback not implemented for {platform.system()}")
            return False
            
        # Map UI sound type to system sound name
        system_sound_name = self.SOUND_MAPPINGS.get(sound_type, 'Ping')
        
        # Try playing via NSSound (preferred method)
        if self._play_via_nssound(system_sound_name):
            return True
            
        # Fallback to afplay with system sound file
        if self._play_via_afplay(system_sound_name):
            return True
            
        print(f"Failed to play sound: {sound_type}")
        return False
        
    def _play_via_nssound(self, sound_name: str) -> bool:
        """Play sound using NSSound via osascript.
        
        This is the preferred method as it uses the system's native sound API.
        """
        try:
            applescript = f'''
            tell application "System Events"
                set soundName to "{sound_name}"
                do shell script "afplay /System/Library/Sounds/" & soundName & ".aiff"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"NSSound playback failed: {e}")
            return False
            
    def _play_via_afplay(self, sound_name: str) -> bool:
        """Play sound using afplay directly.
        
        Fallback method using macOS built-in audio player.
        """
        try:
            sound_path = self.FALLBACK_PATHS.get(sound_name)
            if not sound_path or not os.path.exists(sound_path):
                print(f"Sound file not found: {sound_path}")
                return False
                
            # Use non-blocking mode for faster playback
            result = subprocess.Popen(
                ['afplay', sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Don't wait for completion, just start playing
            return True
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"afplay failed: {e}")
            return False
            
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable sound playback."""
        self.sound_enabled = enabled
        
    def test_sound(self, sound_type: str = 'Chime') -> bool:
        """Test sound playback."""
        print(f"Testing sound: {sound_type}")
        return self.play_sound(sound_type)
        
    def is_sound_available(self) -> bool:
        """Check if sound playback is available on this system."""
        if not self.is_macos:
            return False
            
        # Test if we can play a simple sound
        try:
            # Try a shorter, simpler sound test
            result = subprocess.run(
                ['afplay', '/System/Library/Sounds/Purr.aiff'],
                capture_output=True,
                timeout=0.5
            )
            return result.returncode == 0
        except:
            return False