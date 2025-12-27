# VS Code Extension Server

This service provides APIs for VS Code extension integration, enabling real-time AI features in the IDE.

## Endpoints

### Code Completion
- `POST /api/completion` - Get code completion suggestions

### Code Explanation
- `POST /api/explain` - Explain code in detail
- `POST /api/explain-error` - Explain error messages

### Code Editing
- `POST /api/inline-edit` - Inline code editing

### Test Generation
- `POST /api/generate-tests` - Generate unit tests

### Documentation
- `POST /api/generate-docs` - Generate documentation

## WebSocket

Real-time features available via WebSocket on port 3004:
- Streaming code completion
- Real-time chat
- Live error explanations

## Integration

Connect your VS Code extension to this server to enable:
- Real-time code completion
- Inline code editing
- Chat panel
- Error explanations
- And more!

See ENTERPRISE_FEATURES.md for extension implementation guide.

