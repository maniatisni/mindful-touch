// Mindful Touch - Tauri Desktop Application
// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

// Global state to track the Python backend process
static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
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
                    // Error checking process, assume it's dead
                    *process_guard = None;
                }
            }
        }
    }

    println!("Starting Python backend...");
    
    // Try different paths to find the project root
    let possible_paths = vec![
        "../../",           // From frontend/src-tauri/ (dev mode)
        "../../../../",     // From frontend/src-tauri/target/debug/ (built app)
        "../../../",        // Alternative path
        "./",               // Same directory
    ];
    
    for path in possible_paths {
        println!("Trying path: {}", path);
        
        let child = Command::new("uv")
            .args(&["run", "python", "-m", "backend.detection.main", "--headless"])
            .current_dir(path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();
        
        match child {
            Ok(mut child) => {
                println!("Python process spawned successfully from path: {}", path);
                
                // Give the process time to start
                thread::sleep(Duration::from_millis(2000));
                
                match child.try_wait() {
                    Ok(Some(status)) => {
                        println!("Process exited early with status: {}", status);
                        // Read stderr to see what went wrong
                        if let Ok(output) = child.wait_with_output() {
                            let stderr = String::from_utf8_lossy(&output.stderr);
                            let stdout = String::from_utf8_lossy(&output.stdout);
                            println!("Process stderr: {}", stderr);
                            println!("Process stdout: {}", stdout);
                            return Err(format!("Backend failed to start: {}", stderr));
                        }
                        continue; // Try next path
                    },
                    Ok(None) => {
                        println!("Process is running successfully");
                        
                        // Store the process in global state
                        {
                            let mut process_guard = PYTHON_PROCESS.lock().unwrap();
                            *process_guard = Some(child);
                        }
                        
                        // Give WebSocket server additional time to start
                        thread::sleep(Duration::from_millis(3000));
                        
                        return Ok("Python backend started successfully".to_string());
                    },
                    Err(e) => {
                        println!("Error checking process status: {}", e);
                        continue; // Try next path
                    }
                }
            },
            Err(e) => {
                println!("Failed to start from path {}: {}", path, e);
                continue; // Try next path
            }
        }
    }
    
    Err("Failed to start Python backend from any path. Make sure 'uv' is installed and the project structure is correct.".to_string())
}

#[tauri::command]
async fn stop_python_backend() -> Result<String, String> {
    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        match child.kill() {
            Ok(_) => {
                println!("Python backend process terminated");
                // Wait for the process to actually exit
                let _ = child.wait();
                Ok("Python backend stopped successfully".to_string())
            }
            Err(e) => {
                println!("Failed to kill Python backend process: {}", e);
                Err(format!("Failed to stop backend: {}", e))
            }
        }
    } else {
        Ok("No Python backend process running".to_string())
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
        .invoke_handler(tauri::generate_handler![greet, start_python_backend, stop_python_backend, toggle_region])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}