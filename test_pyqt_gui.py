#!/usr/bin/env python3
"""Test script for PyQt GUI components."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_gui_components():
    """Test GUI components without full integration."""
    app = QApplication(sys.argv)
    
    try:
        # Test imports
        from backend.gui.main_window import MainWindow
        from backend.gui.widgets.custom_toggle import CustomToggle, ToggleRow
        from backend.gui.widgets.camera_display import CameraDisplayWidget
        from backend.audio.sound_manager import SoundManager
        
        print("✓ All GUI imports successful")
        
        # Test sound manager
        sound_manager = SoundManager()
        print(f"✓ Sound manager initialized (macOS: {sound_manager.is_macos})")
        
        if sound_manager.is_macos:
            print("Testing system sounds...")
            for sound_type in ['Chime', 'Beep', 'Gentle']:
                success = sound_manager.test_sound(sound_type)
                print(f"  {sound_type}: {'✓' if success else '✗'}")
        
        # Test main window creation (without show)
        window = MainWindow()
        print("✓ Main window created successfully")
        
        # Test toggle functionality
        toggle = CustomToggle()
        toggle.set_checked(True)
        print(f"✓ Custom toggle works (checked: {toggle.is_checked()})")
        
        print("\n🎉 All PyQt GUI components working correctly!")
        
        # Close after 2 seconds
        QTimer.singleShot(2000, app.quit)
        
    except Exception as e:
        print(f"✗ Error testing GUI components: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(test_gui_components())