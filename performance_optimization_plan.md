# Smriti Performance Optimization Plan

## Critical Issues Found (Impact: HIGH)

### 1. EXCESSIVE LOGGING - 510 log statements
**Problem**: Every repository operation, encryption/decryption, and service call logs DEBUG/INFO messages
**Impact**: Significant I/O overhead, disk writes, string formatting costs
**Solution**: Reduce to ERROR/WARNING only, remove DEBUG logs from hot paths

### 2. REDUNDANT DECRYPTION LOGIC 
**Problem**: Each repository (sessions, nodes, reflections) duplicates decryption + object recreation
**Impact**: Code duplication, maintenance overhead, potential memory waste
**Solution**: Create centralized decryption utility

### 3. MEMORY LEAKS
**Problem**: Temp files from audio transcription, unclosed DB connections in jwt_utils
**Impact**: Memory buildup over time, file system clutter
**Solution**: Guaranteed cleanup with context managers

### 4. N+1 DATABASE QUERIES
**Problem**: Individual decryption calls instead of batch processing
**Impact**: Database round-trip overhead
**Solution**: Batch decryption operations

### 5. TEXT ENTRY ANIMATION BUG
**Problem**: Processing animation not showing for text entries
**Impact**: Poor user experience, confusion about processing status
**Solution**: Fix JavaScript animation flow

## Optimization Strategy

1. **Immediate**: Fix text animation bug (user-facing)
2. **High Impact**: Reduce logging from 510 to ~50 statements
3. **Medium Impact**: Centralize decryption logic
4. **Long-term**: Memory management improvements

## Expected Performance Gains

- **Page Load**: 20-30% faster (reduced logging overhead)
- **Navigation**: 15-25% faster (less I/O operations)
- **Memory Usage**: 10-15% reduction (better cleanup)
- **Database**: 5-10% faster (reduced query overhead)