// Mindful Touch - Tauri Desktop Application
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;

// Global state to track the Python backend process
static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {name}! You've been greeted from Rust!")
}

#[tauri::command]
async fn start_python_backend(app: tauri::AppHandle) -> Result<String, String> {
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

    // Try to find the backend executable in different locations
    let mut possible_executables = vec![];
    
    // In production, try the app's resource directory first
    if let Ok(resource_dir) = app.path().resource_dir() {
        let resource_path = resource_dir.to_string_lossy().to_string();
        #[cfg(windows)]
        possible_executables.push(format!("{resource_path}/mindful-touch-backend.exe"));
        #[cfg(not(windows))]
        possible_executables.push(format!("{resource_path}/mindful-touch-backend"));
    }
    
    // Development fallback paths (for dev mode with source code)
    let dev_paths = vec![
        "../../".to_string(),       // From frontend/src-tauri/ (dev mode)
        "../../../../".to_string(), // From frontend/src-tauri/target/debug/ (built app)
        "../../../".to_string(),    // Alternative path
        "./".to_string(),           // Same directory
    ];

    // First, try to run the standalone executable
    for executable_path in possible_executables {
        if std::path::Path::new(&executable_path).exists() {
            let mut cmd = Command::new(&executable_path);
            cmd.args(["--headless"])
                .stdout(Stdio::piped())
                .stderr(Stdio::piped());

            // On Unix systems, create a new process group so we can kill all child processes
            #[cfg(unix)]
            {
                use std::os::unix::process::CommandExt;
                cmd.process_group(0);
            }

            let child = cmd.spawn();

            match child {
                Ok(child) => {
                    // Store the process
                    {
                        let mut process_guard = PYTHON_PROCESS.lock().unwrap();
                        *process_guard = Some(child);
                    }

                    // Wait for backend to initialize
                    thread::sleep(Duration::from_millis(3000));

                    return Ok(format!("Standalone backend started successfully from: {executable_path}"));
                }
                Err(e) => {
                    eprintln!("Failed to start standalone backend from {executable_path}: {e}");
                    continue;
                }
            }
        }
    }

    // Fallback: try development mode with source code (if standalone executable not found)
    for path in dev_paths {
        let backend_dir = format!("{path}/backend");
        let pyproject_file = format!("{path}/pyproject.toml");
        
        // Check if both backend directory and pyproject.toml exist
        if !std::path::Path::new(&backend_dir).exists() || !std::path::Path::new(&pyproject_file).exists() {
            continue;
        }

        let mut cmd = Command::new("uv");
        cmd.args([
            "run",
            "python",
            "-m",
            "backend.detection.main",
            "--headless",
        ])
        .current_dir(&path)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

        // On Unix systems, create a new process group so we can kill all child processes
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            cmd.process_group(0);
        }

        let child = cmd.spawn();

        match child {
            Ok(child) => {
                // Store the process
                {
                    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
                    *process_guard = Some(child);
                }

                // Wait for backend to initialize
                thread::sleep(Duration::from_millis(3000));

                return Ok(format!("Development backend started successfully from path: {path}"));
            }
            Err(e) => {
                // Log the error for debugging but continue trying other paths
                eprintln!("Failed to start development backend from {path}: {e}");
                continue;
            }
        }
    }

    Err("Failed to start backend. Standalone executable not found and development environment not available.".to_string())
}

#[tauri::command]
async fn stop_python_backend() -> Result<String, String> {
    cleanup_python_process()
}

fn cleanup_python_process() -> Result<String, String> {
    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
    if let Some(mut child) = process_guard.take() {
        // First try to terminate gracefully
        match child.kill() {
            Ok(_) => {
                // Wait for process to actually exit
                let _ = child.wait();

                // On Unix systems, also kill the process group to ensure all child processes are terminated
                #[cfg(unix)]
                {
                    let pid = child.id() as i32;
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
