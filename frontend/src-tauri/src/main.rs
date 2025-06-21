// Mindful Touch - Tauri Desktop Application
// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Stdio};

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn start_python_backend() -> Result<String, String> {
    // Start the Python detection backend
    println!("Starting Python backend...");
    
    let output = Command::new("uv")
        .args(&["run", "python", "-m", "backend.detection.main", "--headless"])
        .current_dir("../../") // Go up two levels to find the Python project
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn();
    
    match output {
        Ok(_child) => {
            println!("Python process spawned successfully");
            // Don't wait for the process, let it run in background
            Ok("Python backend started successfully".to_string())
        },
        Err(e) => {
            println!("Failed to start Python backend: {}", e);
            Err(format!("Failed to start Python backend: {}", e))
        }
    }
}

#[tauri::command]
async fn toggle_region(region: String) -> Result<String, String> {
    // This will communicate with the Python backend to toggle regions
    // For now, just return success
    Ok(format!("Toggled region: {}", region))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet, start_python_backend, toggle_region])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}