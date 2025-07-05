// Mindful Touch - Tauri Desktop Application
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::{process::CommandChild, ShellExt};

// Global state to track the Python backend process
static PYTHON_PROCESS: Mutex<Option<CommandChild>> = Mutex::new(None);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {name}! You've been greeted from Rust!")
}

#[tauri::command]
async fn start_python_backend(app: tauri::AppHandle) -> Result<(), String> {
    let (_rx, child) = app
        .shell()
        .sidecar("mindful-touch-backend")
        .unwrap()
        .args(["--headless", "--verbose"])
        .spawn()
        .map_err(|e| e.to_string())?;
    *PYTHON_PROCESS.lock().unwrap() = Some(child);
    Ok(())
}

#[tauri::command]
async fn stop_python_backend() -> Result<String, String> {
    cleanup_python_process()
}

fn cleanup_python_process() -> Result<String, String> {
    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
    if let Some(child) = process_guard.take() {
        // First try to terminate gracefully
        let pid = child.pid() as i32; // Get pid before child is moved by kill()
        match child.kill() {
            Ok(_) => {
                // On Unix systems, also kill the process group to ensure all child processes are terminated
                #[cfg(unix)]
                {
                    unsafe {
                        // Kill the entire process group
                        libc::killpg(pid, libc::SIGTERM);
                        std::thread::sleep(Duration::from_millis(100));
                        libc::killpg(pid, libc::SIGKILL);
                    }
                }
                Ok("Python backend stopped successfully".to_string())
            }
            Err(e) => Err(format!("Failed to stop backend: {e}")),
        }
    } else {
        Ok("No Python backend process running".to_string())
    }
}

#[tauri::command]
async fn toggle_region(region: String) -> Result<String, String> {
    Ok(format!("Toggled region: {region}"))
}

fn main() {
    // Setup cleanup on process termination
    #[cfg(unix)]
    {
        extern "C" fn handle_sigterm(_: i32) {
            let _ = cleanup_python_process();
            std::process::exit(0);
        }

        unsafe {
            libc::signal(libc::SIGTERM, handle_sigterm as usize);
            libc::signal(libc::SIGINT, handle_sigterm as usize);
        }
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            start_python_backend,
            stop_python_backend,
            toggle_region
        ])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            window.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { .. } = event {
                    // Clean up Python backend process when window is closing
                    let _ = cleanup_python_process();
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
