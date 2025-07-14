# Smriti - AI-Powered Emotional and Cognitive Journaling Assistant

## Overview

Smriti is an AI-powered journaling assistant that helps users gain insights from their emotional and cognitive patterns through graph-based analysis. The application captures voice or text journal entries, extracts meaningful thoughts and emotions, builds a knowledge graph of connected thoughts, and generates personalized reflections.

## Recent Changes

- **Edge Similarity Thresholds Increased**: Raised initial threshold from 0.5 to 0.7 and final threshold from 0.75 to 0.84 to improve edge quality by requiring stronger connections between nodes
- **OpenAI-Free Edge Creation System**: Completely removed OpenAI calls from edge processing. Edges now created directly using adjusted cosine similarity scores as match_strength with edge_type="default". Eliminates timeout issues and dramatically improves performance while maintaining connection quality through advanced similarity scoring
- **Session-Only Edge Processing Implementation**: Separated immediate journal entry processing from background batch processing. New journal entries now only process their own nodes (1-3 per session) for instant completion, while background system handles historical backlog separately. Eliminates timeout issues and provides predictable performance regardless of user's journal history
- **Unlimited Candidate Processing**: Removed MAX_CANDIDATE_NODES limit so edges are created with ALL qualified candidates above similarity threshold, maximizing connection discovery
- **Candidate Discovery Window Reduced**: Changed MAX_DAYS_TO_CONSIDER from 45 to 30 days to reduce candidate search window and improve edge processing performance by limiting historical nodes considered for connections
- **Edge Processing Batch Size Fix**: Fixed critical issue where edge processor only processed 1 node per journal entry instead of all unprocessed nodes. Root cause: frontend called edge API with default batch_size=1, causing SQL LIMIT 1 to fetch only oldest unprocessed node. Updated frontend to use batch_size=10 ensuring all user's unprocessed nodes get processed together, eliminating mixed is_processed states
- **Database-Level Encryption Implementation Complete**: Successfully implemented dual-mode session repository with decrypt_for_processing parameter to resolve SQLAlchemy detached object issues. System now returns attached objects for API operations and detached objects with decrypted data for OpenAI processing, maintaining full encryption while preserving processing functionality
- **Admin/Debug Script Security Cleanup Complete**: Removed all debug and administrative scripts that could bypass API security and access user data directly. Deleted scripts including debug_auth_issue.py, reset_jd_password.py, batch_process_nodes.py, and all test scripts. Secured unprotected user endpoints (/api/v1/users/) with proper JWT authentication and user access verification. Enhanced privacy protection ensuring only authenticated users can access their own data through official API endpoints
- **Phase 1 Privacy Security Implementation Complete**: Resolved critical privacy vulnerability where developers could access any user's journal entries through unprotected API endpoints. Implemented comprehensive JWT authentication and user access verification across all session, node, edge, and reflection endpoints. Added verify_user_access() function to ensure users can only access their own data. All journal content is now protected from unauthorized internal access while maintaining full functionality for legitimate users
- **Iterative Reflection Generation Implemented**: Enhanced reflection generation algorithm to try multiple edges until finding a valid chain (≥3 nodes). Previously, if the strongest edge couldn't form a sufficient chain, no reflection was generated. Now the system iteratively tries up to 10 edges in order of strength, dramatically improving success rate for new users with limited data
- **Reflection Generation Algorithm Documentation Updated**: Corrected technical documentation to accurately reflect the unidirectional edge system and backward-only chain building algorithm. Reflection generation uses strongest edge selection, random backward traversal through incoming edges, and requires minimum 3-node chains for meaningful insights
- **JWT Token Refresh System Complete**: Implemented comprehensive automatic token refresh system to resolve "Error saving journal entry" when access tokens expire. Added centralized AUTH_CONFIG in config.py, environment-aware cookie security settings, secureFetch.js utility with race condition prevention, and security headers middleware. System now automatically refreshes expired access tokens and retries failed requests transparently to users. Extended secureFetch implementation across all frontend templates (journal.html, entries.html, clean_reflections.html, generate_reflection_page.html, reflections.html) ensuring consistent token refresh behavior throughout the entire application
- **Timezone Display Fix Complete**: Successfully resolved journal entries displaying in GMT/UTC instead of user's local timezone (IST). Implemented Pydantic field serializers for proper UTC timezone indicators with 'Z' suffix in API responses. Updated frontend JavaScript to use browser locale settings and automatically convert UTC timestamps to local timezone with AM/PM format. Journal entries now display correctly in user's local time zone - confirmed working by user testing
- **Extended Session Duration**: Increased refresh token expiration from 14 days to 90 days across all authentication flows (email/password login, signup, Google OAuth). Users now stay logged in for 3 months instead of 2 weeks, significantly reducing login friction for regular users while maintaining reasonable security
- **New User Journal Entry Fix Complete**: Resolved critical authentication issue preventing new users from saving journal entries immediately after signup. Implemented JWT token generation and secure cookie setting during email/password signup to match Google OAuth flow. New users now get instant access to journal creation without needing to log in again
- **Notification Settings Disabled**: Disabled daily journal reminders and new reflection alerts toggles in settings page since these features aren't implemented yet. Set both to off by default and added "(Coming Soon)" labels to prevent user confusion about unimplemented features
- **Settings Page Language Selector Disabled**: Disabled language dropdown in settings page to prevent users from changing languages since only English is currently supported. Added "Coming Soon" labels to non-English options and made selector read-only, consistent with signup page restrictions
- **Display Name Update Feature Complete**: Successfully implemented full display name editing functionality in settings page. Users can now update their display name through a proper form submission that saves to the user_profile database table with success/error feedback messages. Form includes proper validation and database error handling
- **Language Selector Update**: Disabled non-English language options in signup form with "Coming Soon" labels since app currently only supports English. Prevents user confusion and accidental selection of unsupported languages during account creation
- **Reflection Generation Age Limit Fix**: Resolved critical issue preventing reflection generation by updating MAX_NODE_AGE_DAYS from 30 to 90 days. Root cause: all unprocessed edges connected nodes older than 30 days (42-48 days old), causing automatic rejection during chain building. This created permanent backlog of unprocessable edges. Users can now generate reflections from historical journal connections spanning up to 3 months
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
   - **Iterative Edge Selection**: Tries multiple edges in strength order until finding valid chain (≥3 nodes)
   - **Edge Scoring**: Combined score = match_strength + (0.3 × decay_factor) prioritizes recent, strong connections
   - **Backward Chain Building**: Traces thought progression by following edges backward from selected edge
   - **Unidirectional Edges**: All edges are one-way relationships (from_node → to_node)
   - **Random Backward Traversal**: Randomly selects from available incoming edges to build causal history
   - **Chain Requirements**: Minimum 3 nodes, maximum 20 nodes, nodes must be ≤90 days old
   - **Attempt Limits**: Maximum 10 edge attempts (configurable via MAX_REFLECTION_ATTEMPTS env var)
   - **AI Generation**: GPT-4o creates empathetic reflections from thought sequences with confidence scores

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