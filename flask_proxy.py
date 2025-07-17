"""
Simple Flask application that serves as a wrapper for our FastAPI app.
"""
from flask import Flask, request, Response, render_template_string, render_template, redirect, url_for, flash, session, send_from_directory
import os
import subprocess
import threading
import requests
import time
import sys
import uuid
import json
from datetime import datetime

# Create the Flask application
app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(24)

# Port for the uvicorn server
FASTAPI_PORT = 8000
uvicorn_process = None
uvicorn_lock = threading.Lock()

def get_or_create_default_user():
    """
    Get a default user or create one for testing purposes.
    
    Returns:
        str: User ID
    """
    try:
        # Try to get existing users
        response = requests.get(f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/")
        
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                # Return the first user's ID
                return users[0]["id"]
        
        # If no users exist, create a new one
        user_data = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com"
        }
        
        response = requests.post(
            f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/",
            json=user_data
        )
        
        if response.status_code == 201:
            return response.json()["id"]
        
    except Exception as e:
        print(f"Error getting/creating user: {e}")
    
    # Return None if both approaches fail
    return None

def start_uvicorn_server():
    """Start uvicorn server in a subprocess."""
    global uvicorn_process
    
    # Use a lock to prevent multiple threads from starting multiple servers
    with uvicorn_lock:
        if uvicorn_process is not None and uvicorn_process.poll() is None:
            # Process is still running
            return True
            
        print("Starting uvicorn server...")
        try:
            # Start the uvicorn process
            process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "127.0.0.1", 
                    "--port", str(FASTAPI_PORT),
                    "--reload"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            uvicorn_process = process
            
            # Create threads to capture and log output
            def log_output(stream, prefix):
                for line in stream:
                    print(f"{prefix}: {line.strip()}")
            
            threading.Thread(
                target=log_output, 
                args=(process.stdout, "UVICORN STDOUT"), 
                daemon=True
            ).start()
            threading.Thread(
                target=log_output, 
                args=(process.stderr, "UVICORN STDERR"), 
                daemon=True
            ).start()
            
            # Wait for server to start
            time.sleep(3)
            
            if process.poll() is not None:
                print(f"Uvicorn process failed with code {process.returncode}")
                return False
                
            print(f"Uvicorn server started on port {FASTAPI_PORT}")
            return True
            
        except Exception as e:
            print(f"Error starting uvicorn: {e}")
            return False

@app.route('/')
def index():
    """Render landing page with just a welcome message and login/signup options."""
    # Check if user is logged in
    user_id = session.get('user_id')
    
    # If the user is logged in, redirect to journal page directly
    if user_id:
        return redirect(url_for('journal'))
    
    # Start the FastAPI server
    start_uvicorn_server()
            
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Smriti - AI Journaling Assistant</title>
                
                <!-- PWA Meta Tags -->
                <meta name="description" content="AI-powered emotional intelligence voice journaling app">
                <meta name="theme-color" content="#f39c12">
                <meta name="apple-mobile-web-app-capable" content="yes">
                <meta name="apple-mobile-web-app-status-bar-style" content="default">
                <meta name="apple-mobile-web-app-title" content="Smriti">
                <meta name="mobile-web-app-capable" content="yes">
                
                <!-- PWA Manifest -->
                <link rel="manifest" href="/static/manifest.json">
                
                <!-- PWA Icons -->
                <link rel="apple-touch-icon" href="/static/icon-192.png">
                <link rel="icon" type="image/png" sizes="192x192" href="/static/icon-192.png">
                <link rel="icon" type="image/png" sizes="512x512" href="/static/icon-512.png">
                <link rel="shortcut icon" href="/static/favicon.ico">
                
                <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
                <style>
                    body { 
                        font-family: Arial, sans-serif;
                        height: 100vh;
                        margin: 0;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container {
                        max-width: 800px;
                        text-align: center;
                        padding: 20px;
                    }
                    .welcome-content {
                        margin-bottom: 3rem;
                    }
                    .auth-buttons {
                        display: flex;
                        gap: 1rem;
                        justify-content: center;
                    }
                    .alert {
                        position: fixed;
                        top: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        min-width: 300px;
                        z-index: 9999;
                    }
                </style>
            </head>
            <body>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category if category != 'message' else 'info' }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="container">
                    <div class="welcome-content">
                        <h1 class="display-4">Welcome to Smriti</h1>
                        <p class="lead mb-5">An AI-powered emotional and cognitive journaling assistant</p>
                    </div>
                    
                    <div class="auth-buttons">
                        <a href="/login" class="btn btn-primary btn-lg">Log In</a>
                        <a href="/signup" class="btn btn-outline-primary btn-lg">Sign Up</a>
                    </div>
                </div>
                
                <!-- Bootstrap JS for alert dismissal -->
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
                
                <!-- PWA Service Worker Registration -->
                <script>
                    // Register Service Worker for PWA functionality
                    if ('serviceWorker' in navigator) {
                        window.addEventListener('load', function() {
                            navigator.serviceWorker.register('/static/sw.js')
                                .then(function(registration) {
                                    console.log('ServiceWorker registration successful');
                                })
                                .catch(function(err) {
                                    console.log('ServiceWorker registration failed: ', err);
                                });
                        });
                    }
                </script>
            </body>
        </html>
    ''')

@app.route('/journal')
def journal():
    """Render the voice journal interface."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # First check if there's a user ID in the session
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to access your journal', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info (if available)
    display_name = None
    is_returning_user = False
    try:
        # Try to get the user profile from API
        print(f"Fetching profile for user ID: {user_id}")
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        print(f"Profile API response status: {response.status_code}")
        
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
            print(f"Got user display name: {display_name}")
        else:
            print(f"Failed to get profile: {response.text}")
            
        # Check if user has any previous sessions to determine if they're returning
        sessions_response = requests.get(f"http://localhost:8000/api/v1/sessions/user/{user_id}")
        if sessions_response.status_code == 200:
            sessions = sessions_response.json()
            is_returning_user = len(sessions) > 0
            print(f"User has {len(sessions)} sessions, is_returning_user: {is_returning_user}")
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Render the journal template with the user ID and display name
    # Create a special parameter for mobile-friendly display name
    # This prevents it from showing in the mobile menu
    print(f"Rendering template with display_name: {display_name}")
    return render_template('journal.html', 
                          user_id=user_id, 
                          display_name=display_name,
                          desktop_name=display_name,  # New parameter only for desktop view
                          is_mobile_menu=False,
                          is_returning_user=is_returning_user)

@app.route('/entries')
def entries():
    """Render the journal entries page."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # First check if there's a user ID in the session
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to view your journal entries', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info (if available)
    display_name = None
    try:
        # Try to get the user profile from API
        print(f"Fetching profile for user ID: {user_id}")
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        print(f"Profile API response status: {response.status_code}")
        
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
            print(f"Got user display name: {display_name}")
        else:
            print(f"Failed to get profile: {response.text}")
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Render the entries template with the user ID and display name
    return render_template('entries.html', user_id=user_id, display_name=display_name)


@app.route('/reflections')
def reflections():
    """Render the clean reflections page."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # Get the user ID from the session (the logged-in user)
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to view your reflections', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info (if available)
    display_name = None
    
    try:
        # Try to get the user profile from API
        print(f"Fetching profile for user ID: {user_id}")
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        print(f"Profile API response status: {response.status_code}")
        
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
            print(f"Got user display name: {display_name}")
        else:
            print(f"Failed to get profile: {response.text}")
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Directly fetch reflections from the API
    reflections = []
    try:
        print(f"Fetching reflections for user ID: {user_id}")
        response = requests.get(f"http://localhost:8000/api/v1/reflections/user/{user_id}")
        print(f"Reflections API response status: {response.status_code}")
        
        if response.status_code == 200:
            reflections = response.json()
            print(f"Found {len(reflections)} reflections")
            # Safely convert generated_at to datetime for template
            for r in reflections:
                generated_at = r.get('generated_at')
                if generated_at and isinstance(generated_at, str):
                    try:
                        # Handle different datetime string formats
                        if generated_at.endswith('Z'):
                            r['generated_at'] = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                        elif '+' in generated_at or generated_at.endswith('00:00'):
                            r['generated_at'] = datetime.fromisoformat(generated_at)
                        else:
                            # Fallback: parse as is
                            r['generated_at'] = datetime.fromisoformat(generated_at)
                    except (ValueError, TypeError) as e:
                        # If parsing fails, keep as string and let template handle it gracefully
                        print(f"Warning: Could not parse datetime string: {generated_at} - {e}")
                elif isinstance(generated_at, datetime):
                    # Already a datetime object, keep as is
                    pass
    except Exception as e:
        print(f"Error fetching reflections: {e}")
    
    # Render the clean reflections template with the user ID, display name, and reflections data
    return render_template('clean_reflections.html', 
                           user_id=user_id, 
                           display_name=display_name,
                           reflections=reflections,
                           enable_pagination=False)
    
@app.route('/generate-reflection')
def generate_reflection():
    """Show the manual reflection generation page."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # Get the user ID from the session
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to generate reflections', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info
    display_name = None
    try:
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Check if user has unprocessed edges available for reflection generation
    has_unprocessed_edges = False
    try:
        # Get edges for the user and check if any are unprocessed
        response = requests.get(f"http://localhost:8000/api/v1/edges/user/{user_id}")
        if response.status_code == 200:
            edges = response.json()
            has_unprocessed_edges = any(not edge.get('is_processed', True) for edge in edges)
    except Exception as e:
        print(f"Error checking unprocessed edges: {e}")
    
    # Render the generate reflection page with button
    return render_template('generate_reflection_page.html', 
                           user_id=user_id, 
                           display_name=display_name,
                           has_unprocessed_edges=has_unprocessed_edges)

@app.route('/generate-reflection/process', methods=['POST'])
def process_reflection_generation():
    """Process manual reflection generation when button is clicked."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # Get the user ID from the session
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to generate reflections', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info
    display_name = None
    try:
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Trigger reflection generation (Phase 5)
    new_reflection = None
    error_message = None
    
    try:
        print(f"Triggering reflection generation for user: {user_id}")
        # Add a small delay to ensure FastAPI server is ready
        import time
        time.sleep(2)
        response = requests.post(f"http://localhost:8000/api/v1/reflections/user/{user_id}/generate")
        print(f"Reflection generation API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Reflection generation result: {result}")
            
            if result.get('reflections_created', 0) > 0:
                # Fetch the latest reflection
                try:
                    reflections_response = requests.get(f"http://localhost:8000/api/v1/reflections/user/{user_id}")
                    if reflections_response.status_code == 200:
                        reflections = reflections_response.json()
                        if reflections:
                            new_reflection = reflections[0]  # Most recent reflection
                            # Convert datetime for template
                            generated_at = new_reflection.get('generated_at')
                            if generated_at and isinstance(generated_at, str):
                                try:
                                    if generated_at.endswith('Z'):
                                        new_reflection['generated_at'] = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                                    elif '+' in generated_at or generated_at.endswith('00:00'):
                                        new_reflection['generated_at'] = datetime.fromisoformat(generated_at)
                                    else:
                                        new_reflection['generated_at'] = datetime.fromisoformat(generated_at)
                                except (ValueError, TypeError) as e:
                                    print(f"Warning: Could not parse datetime string: {generated_at} - {e}")
                except Exception as e:
                    print(f"Error fetching latest reflection: {e}")
            else:
                error_message = "No new patterns found, try journaling more"
                print("No new reflection was generated")
        else:
            error_message = "There is some issue, please try again later"
            print(f"Failed to generate reflection: {response.text}")
            
    except Exception as e:
        error_message = "There is some issue, please try again later"
        print(f"Error generating reflection: {e}")
    
    # Render the generate reflection result page
    return render_template('generate_reflection_result.html', 
                           user_id=user_id, 
                           display_name=display_name,
                           new_reflection=new_reflection,
                           error_message=error_message)

@app.route('/simple-reflections')
def simple_reflections():
    """Render a simplified reflections page with direct database access."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    # Get the user ID from the session
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to view your reflections', 'warning')
        return redirect(url_for('login'))
    
    # Get user profile info (if available)
    display_name = None
    try:
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        if response.status_code == 200:
            user_profile = response.json()
            display_name = user_profile.get('display_name')
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    # Directly fetch reflections from the API
    reflections = []
    try:
        print(f"Fetching reflections for user ID: {user_id}")
        response = requests.get(f"http://localhost:8000/api/v1/reflections/user/{user_id}")
        print(f"Reflections API response status: {response.status_code}")
        
        if response.status_code == 200:
            reflections = response.json()
            print(f"Found {len(reflections)} reflections")
            # Convert generated_at string to datetime for template
            for r in reflections:
                r['generated_at'] = datetime.fromisoformat(r['generated_at'].replace('Z', '+00:00'))
    except Exception as e:
        print(f"Error fetching reflections: {e}")
    
    return render_template('simple_reflections.html', 
                          reflections=reflections, 
                          user_id=user_id, 
                          display_name=display_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    error = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            error = "Email and password are required."
            return render_template('login.html', error=error)
        
        try:
            # Check if the user exists
            response = requests.get(
                f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/",
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u.get("email") == email), None)
                
                if not user:
                    error = "Invalid email or password."
                    return render_template('login.html', error=error)
                
                # Create the authentication request
                auth_data = {
                    "email": email,
                    "password": password
                }
                
                # Send the authentication request to a new endpoint we'll create
                response = requests.post(
                    f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/authenticate",
                    json=auth_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Authentication successful, store user ID in session
                    user_id = response.json().get("id")
                    session['user_id'] = user_id
                    return redirect(url_for('journal'))
                else:
                    error = "Invalid email or password."
            else:
                error = "An error occurred. Please try again."
        
        except Exception as e:
            error = f"An error occurred: {str(e)}"
    
    return render_template('login.html', error=error)


@app.route('/how-to-use')
def how_to_use():
    """Render the how to use page."""
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    return render_template('how_to_use.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Handle the feedback page and form submission."""
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle feedback form submission
        feedback_type = request.form.get('feedback_type')
        subject = request.form.get('subject')
        message = request.form.get('message')
        rating = request.form.get('rating')
        email = request.form.get('email')
        
        # Here you would typically save the feedback to a database
        # For now, just show a success message
        flash('Thank you for your feedback! We appreciate your input.', 'success')
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Handle the settings page."""
    user_id = session.get('user_id')
    
    # If no user is logged in, redirect to login page
    if not user_id:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle settings form submission
        # Here you would typically update user preferences in the database
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    
    # Get user info for the settings page
    user = None
    try:
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}/profile")
        if response.status_code == 200:
            user = response.json()
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    """Log the user out."""
    # Clear the user ID from the session
    if 'user_id' in session:
        session.pop('user_id')
    
    # Add flash message for feedback
    flash('You have been successfully logged out!', 'success')
    
    # Redirect to the login page
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup."""
    # Start the FastAPI server
    start_uvicorn_server()
    
    error = None
    success = None
    
    if request.method == 'POST':
        # Extract data from the form
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        display_name = request.form.get('display_name')
        birthdate_str = request.form.get('birthdate')
        gender = request.form.get('gender')
        language = request.form.get('language', 'en')
        
        # Validate passwords
        if not password:
            error = "Password is required."
            return render_template('signup.html', error=error)
        
        if password != confirm_password:
            error = "Passwords do not match."
            return render_template('signup.html', error=error)
        
        if len(password) < 8:
            error = "Password must be at least 8 characters long."
            return render_template('signup.html', error=error)
        
        try:
            # Convert birthdate string to date object if present
            birthdate = None
            if birthdate_str:
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date().isoformat()
            
            # First, check if the user already exists
            response = requests.get(
                f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/",
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                existing_user = next((user for user in users if user.get("email") == email), None)
                
                if existing_user:
                    error = "Email is already registered. Please use a different email address."
                    return render_template('signup.html', error=error)
            
            # Create the user first
            user_data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(
                f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/",
                json=user_data,
                timeout=10
            )
            
            if response.status_code != 201:
                error = f"Failed to create user: {response.text}"
                return render_template('signup.html', error=error)
            
            # Get the user ID from the response
            user_id = response.json().get("id")
            
            # Now create the user profile
            profile_data = {
                "display_name": display_name if display_name else None,
                "birthdate": birthdate,
                "gender": gender if gender else None,
                "language": language
            }
            
            # Remove None values from the profile data
            profile_data = {k: v for k, v in profile_data.items() if v is not None}
            
            response = requests.post(
                f"http://127.0.0.1:{FASTAPI_PORT}/api/v1/users/{user_id}/profile",
                json=profile_data,
                timeout=10
            )
            
            if response.status_code != 201:
                error = f"Failed to create user profile: {response.text}"
                return render_template('signup.html', error=error)
            
            # Store user ID in session
            session['user_id'] = user_id
            
            # Redirect to journal with tour parameter for new users
            return redirect(url_for('journal') + '?welcome=true')
        
        except Exception as e:
            error = f"An error occurred during signup: {str(e)}"
    
    return render_template('signup.html', error=error, success=success)

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """Proxy requests to the FastAPI app."""
    # Exclude frontend-only routes from proxying
    frontend_routes = ['how-to-use', 'feedback', 'settings']
    if path in frontend_routes:
        # This should not happen since we have specific routes above, but just in case
        return Response("Route handled by Flask", status=404)
    
    # Make sure the FastAPI server is running
    if not start_uvicorn_server():
        return Response("Failed to start the API server", status=500)
    
    try:
        # Forward the request to FastAPI
        resp = requests.request(
            method=request.method,
            url=f"http://127.0.0.1:{FASTAPI_PORT}/{path}",
            headers={k: v for k, v in request.headers.items() if k != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )
        
        # Create response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded_headers]
        
        return Response(resp.content, resp.status_code, headers)
        
    except requests.exceptions.ConnectionError:
        # Try to restart the server if connection fails
        print("Connection error, attempting to restart uvicorn server...")
        
        global uvicorn_process
        if uvicorn_process:
            uvicorn_process.terminate()
            uvicorn_process = None
            
        if start_uvicorn_server():
            return Response("API server restarted, please try again", status=503)
        else:
            return Response("Failed to restart API server", status=500)
            
    except Exception as e:
        print(f"Proxy error: {e}")
        return Response(f"Proxy error: {str(e)}", status=500)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve PWA static files."""
    return send_from_directory('app/static', filename)

if __name__ == '__main__':
    # Start the FastAPI server
    start_uvicorn_server()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000)
    
    # Clean up when the Flask app exits
    if uvicorn_process:
        uvicorn_process.terminate()
        uvicorn_process.wait()