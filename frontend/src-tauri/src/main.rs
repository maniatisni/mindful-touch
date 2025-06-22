// Mindful Touch - Tauri Desktop Application
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

// Global state to track the Python backend process
static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn start_python_backend() -> Result<String, String> {
    // Check if backend is already running
    {
        let mut process_guard = PYTHON_PROCESS.lock().unwrap();
        if let Some(ref mut child) = *process_guard {
            match child.try_wait() {
                Ok(Some(_)) => {
                    // Process has exited, remove it
                    *process_guard = None;
                }
                Ok(None) => {
                    // Process is still running
                    return Ok("Python backend is already running".to_string());
                }
                Err(_) => {
                    *process_guard = None;
                }
            }
        }
    }

    // Starting Python backend

    // Try different paths to find the project root
    let possible_paths = vec![
        "../../",           // From frontend/src-tauri/ (dev mode)
        "../../../../",     // From frontend/src-tauri/target/debug/ (built app)
        "../../../",        // Alternative path
        "./",               // Same directory
    ];

    for path in possible_paths {
        let backend_dir = format!("{}backend", path);
        if !std::path::Path::new(&backend_dir).exists() {
            continue;
        }
        
        let child = Command::new("uv")
            .args(&["run", "python", "-m", "backend.detection.main", "--headless"])
            .current_dir(path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();

        match child {
            Ok(child) => {
                // Store the process
                {
                    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
                    *process_guard = Some(child);
                }
                
                // Wait for backend to initialize
                thread::sleep(Duration::from_millis(3000));
                
                return Ok("Python backend started successfully".to_string());
            }
            Err(_) => {
                continue;
            }
        }
    }

    Err("Failed to start Python backend from any path".to_string())
}

#[tauri::command]
async fn stop_python_backend() -> Result<String, String> {
    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
    if let Some(mut child) = process_guard.take() {
        match child.kill() {
            Ok(_) => {
                let _ = child.wait();
                Ok("Python backend stopped successfully".to_string())
            }
            Err(e) => Err(format!("Failed to stop backend: {}", e))
        }
    } else {
        Ok("No Python backend process running".to_string())
    }
}

#[tauri::command]
async fn toggle_region(region: String) -> Result<String, String> {
    Ok(format!("Toggled region: {}", region))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet, start_python_backend, stop_python_backend, toggle_region])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}