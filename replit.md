# Smriti - AI-Powered Emotional and Cognitive Journaling Assistant

## Overview

Smriti is an AI-powered journaling assistant that helps users gain insights from their emotional and cognitive patterns through graph-based analysis. The application captures voice or text journal entries, extracts meaningful thoughts and emotions, builds a knowledge graph of connected thoughts, and generates personalized reflections.

## Recent Changes

- **Hamburger Menu Click-Outside Fix Complete**: Resolved UX issue where hamburger menu only closed when clicking the menu button itself. Implemented centralized JavaScript solution using Bootstrap's Collapse API for consistent smooth animations. Menu now closes with same slide-up animation whether clicking hamburger button or outside menu area. Fixed Flask `url_for()` template compatibility issue in FastAPI context. Menu provides intuitive mobile navigation experience across all pages
- **New Brain Network Logo Implementation Complete**: Successfully replaced app logo with updated neural network brain design. Generated PWA-compliant icon sizes (192x192, 512x512, Apple touch icon, favicon) and updated all templates. Confirmed working perfectly on iOS devices - new logo displays correctly when saving app to iPhone home screen through "Add to Home Screen" functionality
- **iOS PWA Installation Fix**: Fixed iOS device detection and unified installation instructions for both Safari and Chrome browsers. Enhanced platform detection to properly identify iPhone, iPad, and iPad Pro devices. Updated installation steps to correctly show "Share" button instructions since both iOS browsers use the same installation method through the Share menu
- **Hamburger Menu Toggle Fix**: Resolved hamburger menu not closing issue on reflections page by removing duplicate Bootstrap JavaScript loading that caused collapse functionality conflicts. Menu now properly toggles open and close as expected
- **Email-Validator Dependency Resolution**: Fixed deployment crashes caused by missing email-validator dependency required for Pydantic EmailStr validation. Issue was triggered when Git integration enabled fresh dependency resolution from pyproject.toml, exposing the implicit dependency. Added email-validator>=2.1.0 to dependencies ensuring consistent deployments across all environments
- **Google OAuth Database Schema Fix Complete**: Resolved critical user creation failure during Google OAuth signup by adding missing `updated_at` field to User model. Successfully executed database migration and updated API schemas. New user Google OAuth signup now works seamlessly in both development and production environments
- **Environment-Aware OAuth System Implemented**: Fixed critical OAuth redirect URI mismatch by implementing smart environment detection system that automatically uses the correct redirect URI based on request domain. System now supports separate GOOGLE_REDIRECT_URI_DEV and GOOGLE_REDIRECT_URI_PROD environment variables with automatic fallback to domain-based detection (localhost, *.replit.dev, --dev patterns for development). Completely resolves oauth_security_failed errors across all environments
- **Google OAuth Integration Complete**: Successfully implemented and tested full Google Sign-In functionality with professional buttons on login/signup pages, secure ID token validation, automatic account linking by email, JWT token generation, popup-based authentication flow, and proper cookie handling for both development and production Replit environments
- **PWA Icon Redesign Complete**: Created professional app icons featuring brain symbol (representing memory/thoughts), microphone (voice journaling), stylized 'S' for Smriti, and decorative dots (emotional connections) on orange gradient background. Generated 192x192, 512x512 PNG icons and favicon.ico for complete PWA branding
- **Google OAuth Cookie Transfer Fix**: Resolved critical issue where JWT cookies weren't transferring from popup to parent window by implementing proper postMessage communication, fixing cookie naming consistency (smriti_access_token), and creating dedicated OAuth success page
- **Google OAuth Route Fix**: Resolved 405 Method Not Allowed error by correcting API router configuration - Google OAuth endpoints now properly accessible at /api/v1/auth/google/login and /api/v1/auth/google/callback
- **JWT Authentication Security Vulnerability Resolved**: Fixed critical authentication issues across all endpoints, standardized JWT token handling with 'sub' field usage, and implemented comprehensive JWT-first authentication with session fallback across all form submissions and API routes
- **Feedback Form Authentication Fix**: Resolved logout issue during feedback submission by updating endpoint to support JWT authentication alongside session-based authentication 
- **Confidence Score UI Removal**: Removed confidence scores from reflections UI display while maintaining backend generation and database storage for future analytics use
- **JWT Authentication System Complete**: Successfully implemented comprehensive JWT-based authentication with access/refresh tokens, secure HTTP-only cookies, and automatic token refresh. All existing users can now log in seamlessly with proper session management
- **Authentication Route Integration**: Fixed critical issue where login generated JWT tokens but protected routes only checked session-based authentication. Updated all protected routes to support JWT authentication with session fallback
- **Cookie Security Configuration**: Properly configured JWT cookies with secure=False for localhost development, HttpOnly protection, and SameSite=lax for optimal security and compatibility
- **User Feedback System Implementation**: Built complete feedback database schema with Feedback model, repository layer, and functional form submission handling for suggestions, bug reports, and compliments
- **FastAPI Error Message Fix**: Resolved flash message display issues by adding proper template handling for FastAPI's flash system in signup and login pages
- **Authentication Enhancements**: Made display name mandatory field and ensured proper password confirmation validation in both frontend and backend
- **UI Text Updates**: Updated navbar "Logout" to "Sign Out" and simplified "How to use Smriti" page description text
- **PWA Install Prompt Implementation**: Created comprehensive install prompt system with orange-themed banner, smart timing (3-second delay), browser detection, and 7-day dismissal cooldown across all key pages
- **Navigation Structure Fix**: Resolved missing bottom navigation on "no patterns found" page by standardizing template structure, CSS variables, and including bottom navigation partial
- **Utility Pages Implementation**: Successfully added How to Use Smriti, Share Feedback, and Settings pages with proper orange theme consistency and fixed header behavior matching journal entries page design
- **Navigation Integration**: Completed routing fixes for utility pages, resolving FastAPI static file reference errors and template compatibility issues
- **Reflections Feedback Fix**: Resolved broken thumbs up/down functionality by removing pagination-related code that contained JavaScript syntax errors, restoring all interactive features
- **Mobile Theme Consistency**: Applied unified orange theme across all utility pages with proper header positioning and scrollable content structure
- **JavaScript Debugging**: Identified and fixed syntax errors in reflections page that were preventing all JavaScript functions from executing properly
- **Bottom Navigation**: Maintained professional bottom tab bar with 4 tabs (Journal, Entries, Reflections, Generate) featuring active state highlighting
- **Menu Cleanup**: Streamlined hamburger menu to contain only utility pages and logout, removing duplicate navigation options
- **Content Structure**: Implemented consistent fixed header + scrollable content pattern across all pages for optimal mobile UX

## System Architecture

### Backend Architecture
- **Framework**: FastAPI with Flask proxy wrapper for WSGI compatibility
- **API Design**: RESTful API with versioned endpoints (/api/v1/)
- **Authentication**: Basic user management with potential for OAuth integration
- **Deployment**: Gunicorn WSGI server with auto-scaling capability

### Frontend Architecture
- **Templates**: Jinja2 templating system for web interface
- **Proxy Layer**: Flask application acts as reverse proxy to FastAPI
- **Static Assets**: Served through Flask for web interface components

## Key Components

### Data Processing Pipeline

1. **Session Management**
   - Captures raw transcripts from voice or text input
   - Tracks session metadata (duration, timestamps)
   - Maintains processing status flags

2. **Node Extraction** 
   - Uses OpenAI GPT-4 to analyze journal transcripts
   - Extracts atomic thought units with emotional and cognitive context
   - Categorizes by theme, cognition type, and emotion
   - Implements deduplication to ensure one node per theme per session

3. **Embedding Generation**
   - Batch processes nodes to generate vector embeddings
   - Uses OpenAI embedding models for semantic similarity
   - Enables efficient similarity calculations for edge creation

4. **Edge Creation**
   - Identifies psychological connections between thoughts
   - Supports 7 edge types: thought_progression, emotion_shift, theme_repetition, identity_drift, emotional_contradiction, belief_contradiction, unresolved_loop
   - Uses cosine similarity and AI analysis for relationship classification
   - Processes both intra-session and cross-session connections

5. **Chain-Linked Edge Processing (Phase 3.25)**
   - Identifies edges that form potential chains (A→B, B→C patterns)
   - Marks qualifying edges as processed to optimize reflection generation
   - Runs automatically after each journal submission

6. **Reflection Generation**
   - **Manual process only** - triggered when user clicks "Generate Reflection" button
   - Uses both dynamic chain discovery and pre-identified chain markers
   - Generates personalized insights from connected thought sequences
   - Provides empathetic, supportive reflections with confidence scores

### Database Schema

**Core Tables:**
- `users`: Basic user authentication and metadata
- `user_profile`: Extended user information (display name, language, demographics)
- `sessions`: Journal entry sessions with raw transcripts
- `nodes`: Atomic thought units with emotional/cognitive attributes
- `edges`: Relationships between nodes with strength and type classification
- `reflections`: AI-generated insights based on connected thoughts

## Data Flow

1. **Input**: User creates journal session via voice/text
2. **Processing**: Raw transcript processed through OpenAI to extract nodes
3. **Embedding**: Nodes converted to vector embeddings for similarity analysis
4. **Connection**: Edges created between semantically and emotionally related nodes
5. **Chain Analysis**: System identifies and marks chain-linked edges (A→B→C patterns)
6. **Insight**: Personalized reflections generated using chain markers and dynamic discovery
7. **Output**: User receives insights and can provide feedback

## External Dependencies

### AI Services
- **OpenAI API**: Primary AI provider for text analysis, embedding generation, and reflection creation
- **Models Used**: GPT-4 for text analysis, text-embedding-ada-002 for embeddings

### Database Systems
- **PostgreSQL**: Primary relational database for structured data
- **Neo4j**: Graph database for advanced relationship analysis (configured but not yet implemented)

### Infrastructure
- **Replit**: Primary hosting and development environment
- **Environment Variables**: Secure configuration management for API keys and database connections

## Deployment Strategy

### Development Environment
- **Local Development**: Uvicorn server on port 8000 for FastAPI
- **Proxy Setup**: Flask application on port 5000 routing to FastAPI
- **Hot Reload**: Automatic code reloading in development mode

### Production Deployment
- **WSGI Server**: Gunicorn with auto-scaling capabilities
- **Port Configuration**: External port 80 mapping to internal port 5000
- **Process Management**: Workflow automation through Replit deployment system

### Configuration Management
- **Environment Files**: `.env` file for database and API configuration
- **Security**: API keys managed through Replit secrets
- **Database**: PostgreSQL connection via environment variables

## Processing Pipeline Status

**Current Implementation:**
- **Phase 1**: Session Management ✓ Implemented
- **Phase 2**: Node Extraction ✓ Implemented  
- **Phase 3**: Edge Creation ✓ Implemented
- **Phase 3.25**: Chain-Linked Edge Processing ✓ Implemented & Auto-triggered
- **Phase 5**: Reflection Generation ✓ Implemented (with dynamic chain discovery)

**Note**: Phase 3.25 automatically identifies and marks edges that form potential chains (where edge A→B connects to edge B→C) during journal submission. Reflection generation then uses both dynamic chain discovery and these pre-identified chain markers to create meaningful insights.

## Changelog

- June 25, 2025: Corrected documentation - Phase 3.25 chain-linked edge processing is fully implemented and auto-triggered during journal submissions
- June 25, 2025: Implemented nuclear scroll fix solution - comprehensive event blocking, 500ms monitoring with exponential backoff, multiple reset methods, transitioning class management
- June 25, 2025: Fixed reflections page sticky header by identifying correct template file (clean_reflections.html) and implementing proper sticky positioning
- June 24, 2025: Fixed schema issues and identified implementation gaps  
- June 23, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.