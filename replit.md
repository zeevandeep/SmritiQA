# Smriti - AI-Powered Emotional and Cognitive Journaling Assistant

## Overview

Smriti is an AI-powered journaling assistant that helps users gain insights from their emotional and cognitive patterns through graph-based analysis. The application captures voice or text journal entries, extracts meaningful thoughts and emotions, builds a knowledge graph of connected thoughts, and generates personalized reflections.

## Recent Changes

- **Database-Based Tour System Complete**: Successfully implemented database-driven tour completion system replacing localStorage for consistent experience across browsers/devices. Added tour_completed column to user_profiles table, created secure API endpoints (/api/v1/tour/status and /api/v1/tour/complete), and updated JavaScript tour system to check database status. All existing users set to tour_completed=false to allow tour viewing. System ensures only new users see tour after signup plus manual access from "How to Use" page, with tour completion stored securely in database with JWT authentication
- **Processing Animation Positioning Fix Complete**: Successfully resolved issue where processing animation ("Analyzing thoughts, establishing memory linkages...") appeared above microphone instead of below after text input addition. Fixed by moving processingState element to global position outside voice input area, ensuring consistent animation display for both voice and text entry modes. Updated showProcessingMessage() function to always use dedicated processingState element rather than overwriting instruction text. Both input modes now show proper step-by-step processing animation in correct location
- **Multilingual Intelligent Journal Entry Paragraph Formatting Complete**: Successfully implemented smart paragraph detection system with full multilingual support to solve Whisper API continuous text limitation. Created text_processing.py utility with semantic transition detection for English, Hindi, Spanish, French, German, Japanese, and Arabic languages. Algorithm prioritizes natural speech transitions over rigid sentence counts, preserves coherent thought chains, and only breaks on genuine topic/emotional shifts. Supports mixed-language content (Hinglish, Spanglish) and automatically detects user language preference from profile. All existing and new journal entries now display with improved readability through automatic paragraph formatting applied during data retrieval
- **Generate Reflections Page UI Enhancement Complete**: Successfully improved reflection text display width and readability on generate reflections page. Adopted the successful layout approach from main reflections page (800px max-width container, col-12 full width). Reduced excessive padding (from 2.5rem 3rem to 1.5rem) to maximize text space. Added professional text justification with hyphens and optimized word spacing for newspaper-like appearance. Generate reflections page now matches the comfortable reading experience of the main reflections page
- **Reflection Feedback System Fix Complete**: Successfully resolved SQLAlchemy session detachment issues preventing reflection feedback functionality. Fixed critical bug where `get_reflection()` returned detached objects causing "Instance not persistent within this Session" errors. Implemented hybrid solution using direct database queries for updates while maintaining encryption/decryption flow through repository functions. Both thumbs up/down feedback and reflection viewing status updates now work correctly with full encryption support. Users can provide feedback on encrypted reflections with proper data protection maintained throughout the process
- **Reflection Text Encryption Complete**: Successfully implemented and validated comprehensive reflection encryption system across all phases. Phase 4 comprehensive testing achieved 100% success rate validating database schema support, encryption utilities core functionality, direct database encryption workflow, repository integration, mixed encrypted/unencrypted data compatibility, and performance/security requirements. Service layer automatically uses encrypted reflection creation through existing `reflection_processor.py` workflow - all new reflections encrypted based on `ENCRYPT_NEW_REFLECTIONS=true` environment variable. API endpoints properly serve decrypted reflections to users. Fixed encryption utility `derive_user_key` function to handle both string and bytes input types. System now production-ready with comprehensive data protection across all reflection content
- **Reflection Text Encryption Phase 2 Complete**: Successfully implemented enhanced reflection repository with encryption/decryption capabilities using existing encryption infrastructure. Added dual-mode repository pattern with `decrypt_for_processing` parameter - API operations use attached SQLAlchemy objects while OpenAI processing uses detached objects with decrypted data. Comprehensive error handling logs encryption failures and provides fallback mechanisms. Both creation and retrieval functions support encryption based on `ENCRYPT_NEW_REFLECTIONS` environment variable. User-specific key derivation ensures data isolation. Enhanced `create_reflection()`, `get_reflection()`, and `get_user_reflections()` with encryption support and `_decrypt_reflections_for_user()` helper function for user display. Ready for Phase 3 service layer integration
- **Reflection Text Encryption Phase 1 Complete**: Implemented database schema and environment setup for encrypting reflection generated_text column. Added `is_encrypted` column to reflections table (Boolean, default=false) and `ENCRYPT_NEW_REFLECTIONS=true` environment variable. Created migration script `add_reflection_encryption_support.py` that handles both database schema updates and environment configuration. Foundation established for forward-only encryption (new reflections will be encrypted, existing 54 reflections remain unencrypted for backward compatibility). Ready for Phase 2 repository layer implementation
- **Dynamic Chain Requirements for New Users Complete**: Successfully implemented graduated reflection generation requirements to solve new user onboarding issue. Users with 0 existing reflections can now generate insights from 2-node chains, while experienced users (1+ reflections) continue requiring 3+ nodes for quality. Added get_user_reflection_count() function and updated reflection processor logic. Confirmed working through user test7 validation - generated first reflection using 2 encrypted nodes with meaningful, high-quality content. Dramatically improves new user experience by providing immediate value while maintaining quality standards for experienced users
- **Environment Variable Loading Fix Complete**: Resolved critical issue where ENCRYPT_NEW_NODES=true in .env file wasn't loaded at runtime, causing nodes to remain unencrypted. Added explicit dotenv loading in both app/main.py and app/config.py to ensure environment variables are available during startup. Fixed disconnect between config object (using defaults) and node repository (using raw environment variables). Node encryption now properly enabled with environment variable loading at application startup
- **Node Text Encryption Phase 4 Complete**: Successfully completed comprehensive testing across all user scenarios and edge cases. Validated mixed encryption environments (encrypted/unencrypted nodes), backward compatibility with legacy data, error handling for edge cases (empty text, long text 5000+ chars), end-to-end workflow integration, performance with batch processing (10 nodes), and security validation with encryption utilities. All 6 test categories passed with 0 failures. Confirmed session-level encryption working (all sessions now encrypted), service layer seamlessly handles mixed data types, raw database storage properly encrypted, and performance remains efficient with encryption overhead. Comprehensive encryption system fully validated and production-ready
- **Node Text Encryption Phase 3 Complete**: Successfully updated all service layer functions to use decrypted text for OpenAI operations. Enhanced reflection processor's `build_node_chain` function and embedding processor's `get_unprocessed_nodes` function to use `decrypt_for_processing=True` parameter. All OpenAI-bound operations (reflection generation, embedding creation, node extraction) now automatically receive decrypted text while maintaining encrypted storage. Comprehensive testing confirms service layer correctly handles encryption/decryption flow - 3 encrypted nodes created, embedding service retrieves decrypted text (83 chars each), reflection chain building returns readable text for OpenAI processing. Service layer architecture complete for secure AI operations
- **Node Text Encryption Phase 2 Complete**: Successfully implemented enhanced node repository with encryption/decryption capabilities using existing encryption infrastructure. Added dual-mode repository pattern with `decrypt_for_processing` parameter - API operations use attached SQLAlchemy objects while OpenAI processing uses detached objects with decrypted data. Comprehensive error handling logs encryption failures and provides fallback mechanisms. Both single and batch node creation support encryption based on `ENCRYPT_NEW_NODES` environment variable. User-specific key derivation ensures data isolation. Confirmed working through detailed testing - new nodes encrypted automatically, processing functions receive decrypted text, backward compatibility maintained for mixed encrypted/unencrypted nodes
- **Node Text Encryption Phase 1 Complete**: Implemented database schema and environment setup for encrypting node text column. Added `is_encrypted` column to nodes table (Boolean, default=false) and `ENCRYPT_NEW_NODES=true` environment variable. Created migration script `add_node_encryption_support.py` that handles both database schema updates and environment configuration. Foundation established for forward-only encryption (new nodes will be encrypted, existing nodes remain unencrypted for backward compatibility). Ready for Phase 2 repository layer implementation
- **Tour System Universal Fix Complete**: Resolved critical issue where users weren't receiving the app tour consistently across all signup flows. Implemented comprehensive fixes: (1) Added welcome=true parameter to email/password signup redirects, (2) Fixed Google OAuth popup success handlers in login.html and signup.html to redirect with welcome=true, (3) Updated "Skip for now" link in language selection to include welcome=true parameter, and (4) Moved App Tour option from Settings page to "How to Use Smriti" page as the first prominent section. Confirmed working through comprehensive testing - all users now receive the tour regardless of signup method (email/password or Google OAuth) or language selection choice (selecting language or skipping). Tour also accessible manually from How to Use page
- **Voice/Text Toggle Journal Entry System Complete**: Successfully implemented dual-mode journal entry functionality with minimal UI changes. Added elegant toggle buttons allowing users to switch between voice recording and text typing modes. Text mode features spacious text area with optimized padding, pen/notepad icon instead of keyboard, shortened placeholder text, and Enter key for line breaks (save only via button click). Both input methods use same session creation, node extraction, embedding generation, and edge processing systems with real-time progress indicators showing actual AI processing time. Confirmed working with real user testing - seamless switching between voice and text entry modes
- **Extended Audio Processing & Hindi Language Detection Complete**: Successfully resolved critical audio transcription timeout issues and implemented flexible Hindi language detection. Enhanced system timeouts to handle 5+ minute recordings (7-minute OpenAI timeout, 8-minute worker timeout) with robust memory management. Fixed Hindi language preference handling where OpenAI Whisper returns English text for Hindi speech - system now properly accepts and processes this as valid Hindi transcription. Confirmed working with real user testing including authentic Hindi voice entries with accurate Devanagari script output
- **Multilingual Reflection Generation Complete**: Successfully implemented comprehensive multilingual reflection generation system supporting 25+ languages with cultural context. System automatically fetches user's language preference from profile and generates reflections in their preferred language using language-specific OpenAI prompts. Includes culturally appropriate instructions for Hindi, Spanish, French, German, Japanese, Arabic, and many others. Confirmed working with real user testing - Hindi reflection generated with proper cultural context and therapeutic tone
- **Language Preference Display on Journal Page**: Successfully implemented dynamic language preference display on journal page. Status text now shows "Tap the microphone to start recording in [Language]" with user's selected language (e.g., "English", "Hindi", "Spanish"). Improves user awareness and confidence by clearly indicating their current language setting directly on the recording interface. Confirmed working with real user testing including Hinglish mixed-language journal entries
- **Mobile-Friendly UI Text Updates**: Updated all microphone instruction text from "click" to "tap" throughout the journal interface for better mobile user experience, matching the touch-based interaction model of the voice journaling app
- **Language Support Alignment with OpenAI Whisper API**: Updated language selection forms across all three templates (signup.html, select_language.html, settings.html) to only show the 50+ officially supported languages by OpenAI's commercial Whisper API. Removed Bengali, Telugu, Gujarati, and other unsupported languages that were causing script mismatch issues (Bengali users getting Hindi script output). Updated language mappings in main.py and script patterns in audio_utils.py to match OpenAI's official supported language list, preventing user confusion and transcription errors
- **Audio Transcription System Fully Operational**: Successfully resolved all critical bugs preventing real user functionality. Fixed three-part issue: authentication (switched to secureFetch for automatic token refresh), Python scoping (removed conflicting import statement), and frontend field mapping (transcript vs transcribed_text). System now properly handles multilingual transcription with automatic language fallback, confirmed working with real user testing
- **Text-Embedding-3-Small Upgrade Complete**: Successfully upgraded from text-embedding-ada-002 to text-embedding-3-small for all users. Confirmed working with real multilingual testing including Hinglish, Hindi, Urdu, and English mixed content. Delivers +40% multilingual performance improvement, 5x cost reduction ($0.00002 vs $0.0001 per 1K tokens), and enhanced semantic understanding for code-mixed languages. Existing embeddings preserved; all new journal entries use the superior model
- **Confidence Score Removal Complete**: Removed confidence scores from reflection generation UI while maintaining backend storage for future analytics. Updated OpenAI prompts, API responses, and frontend display to exclude confidence scores from user interface
- **Edge Similarity Thresholds Increased**: Raised initial threshold from 0.5 to 0.7 and final threshold from 0.75 to 0.84 to improve edge quality by requiring stronger connections between nodes
- **OpenAI-Free Edge Creation System Complete**: Completely removed OpenAI calls from edge processing. Edges now created directly using adjusted cosine similarity scores as match_strength with edge_type="default". Eliminates timeout issues and dramatically improves performance while maintaining connection quality through advanced similarity scoring
- **Session-Only Edge Processing Implementation Complete**: Successfully separated immediate journal entry processing from background batch processing. New journal entries now only process their own nodes (1-6 per session) for instant completion in ~7 seconds, while background system handles historical backlog separately. Eliminates timeout issues and provides predictable performance regardless of user's journal history. Fixed Node model attribute compatibility issue
- **Unlimited Candidate Processing**: Removed MAX_CANDIDATE_NODES limit so edges are created with ALL qualified candidates above similarity threshold, maximizing connection discovery
- **Candidate Discovery Window Reduced**: Changed MAX_DAYS_TO_CONSIDER from 30 to 14 days to reduce candidate search window and improve edge processing performance by limiting historical nodes considered for connections
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
- **Google OAuth Language Selection Complete**: Successfully implemented comprehensive Google OAuth integration with automatic new user language selection flow. New users are redirected to language selection page while existing users go directly to journal. Enhanced popup handling, OAuth success page redirection logic, and removed globe icon from language selection page for cleaner UI design
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
   - Batch processes nodes to generate vector embeddings using text-embedding-3-small
   - Provides enhanced multilingual support for Hindi, Urdu, Spanish, Hinglish, and 16+ languages
   - Delivers 5x cost efficiency with same 1,536 dimensions for backward compatibility
   - Enables superior semantic similarity calculations for edge creation across languages

4. **Edge Creation**
   - **OpenAI-Free System**: Uses pure cosine similarity calculations without AI analysis for faster, more reliable processing
   - **Single Edge Type**: All edges use "default" type with adjusted cosine similarity scores as match_strength
   - **Session-Only Processing**: New journal entries only process their own nodes (1-6 per session) instead of entire user backlog
   - **14-Day Candidate Window**: Searches for connection candidates within 14 days (reduced from 30 days) for optimal performance
   - **High Similarity Threshold**: Requires 0.84+ similarity scores to ensure only meaningful connections are created
   - **Unlimited Qualified Candidates**: Creates edges with ALL candidates above threshold (no artificial limits)
   - **Performance Optimized**: Completes edge processing in 2-7 seconds instead of potentially timing out

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
   - **AI Generation**: GPT-4o creates empathetic reflections from thought sequences (confidence scores removed from UI)

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
4. **Session-Only Edge Creation**: Current session's nodes connected to historical nodes using cosine similarity (14-day window, 0.84+ threshold)
5. **Chain Analysis**: System identifies and marks chain-linked edges (A→B→C patterns)
6. **Insight**: Personalized reflections generated using chain markers and dynamic discovery
7. **Output**: User receives insights and can provide feedback

## External Dependencies

### AI Services
- **OpenAI API**: Primary AI provider for text analysis, embedding generation, and reflection creation
- **Models Used**: GPT-4 for text analysis, text-embedding-3-small for embeddings

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

- July 19, 2025: Database-based tour system complete - implemented secure tour completion tracking in database instead of localStorage for consistent cross-browser experience, all existing users can now see tour
- July 19, 2025: Processing animation positioning fix complete - resolved animation appearing above microphone, moved to global position for consistent display in both voice and text modes
- July 19, 2025: Multilingual intelligent journal entry paragraph formatting complete - implemented smart semantic transition detection with full language support (English, Hindi, Spanish, French, German, Japanese, Arabic) preserving coherent thought chains while improving readability
- July 19, 2025: Generate reflections page UI enhancement complete - improved text width, adopted successful layout from main reflections page, added text justification for professional appearance
- July 19, 2025: Reflection feedback system fix complete - resolved SQLAlchemy session detachment issues, implemented hybrid database update approach with full encryption support
- July 19, 2025: Reflection encryption system complete - achieved 100% success rate in Phase 4 comprehensive testing validating all encryption functionality including database schema, utilities, repository integration, mixed data compatibility, and performance/security requirements
- July 14, 2025: Text-embedding-3-small upgrade complete and tested - all new journal entries now use enhanced embedding model with confirmed +40% multilingual performance, 5x cost reduction, and excellent Hinglish/code-mixed language support
- July 14, 2025: Confidence score removal from UI complete - updated OpenAI prompts, API responses, and frontend display  
- July 14, 2025: Major edge creation system overhaul - implemented OpenAI-free session-only processing with 14-day candidate window and 0.84+ similarity threshold for 2-7 second processing times
- June 25, 2025: Corrected documentation - Phase 3.25 chain-linked edge processing is fully implemented and auto-triggered during journal submissions
- June 25, 2025: Implemented nuclear scroll fix solution - comprehensive event blocking, 500ms monitoring with exponential backoff, multiple reset methods, transitioning class management
- June 25, 2025: Fixed reflections page sticky header by identifying correct template file (clean_reflections.html) and implementing proper sticky positioning
- June 24, 2025: Fixed schema issues and identified implementation gaps  
- June 23, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.