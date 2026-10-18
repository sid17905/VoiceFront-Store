# ChatGPT Interface Integration Plan for VoiceFront-Store

## 1. ChatGPT Layout Anatomy
ChatGPT's interface is structured around three core pillars:
1. **Sidebar / Drawer (Hidden in Settings / Secondary Layer)**: Chat history, saved storefronts, configuration, and app settings.
2. **Main Conversation Canvas**: Center-aligned scrollable stream of user messages (bubbles right/distinguished) and AI assistant responses (left/clean).
3. **Bottom Sticky Input Bar**: Multi-modal input container holding:
   - Text input box (auto-expanding)
   - Attachment / Voice button (for ASR audio upload or prompt injection)
   - Send / Stop generation button

---

## 2. Integration with VoiceFront-Store V2

To fit this exactly into our current app structure while keeping advanced controls tucked away:

### What Moves to the Chat Layer (Primary UI)
- **The Entire User Interaction Loop**: Users open the app to a clean chat screen ("What kind of store would you like to build today?").
- **Streaming Responses**: As Tony extracts store details via `nlp-service`, intermediate responses appear in the chat ("Got it! Adding *Tony's Pizza* with Margherita for ₹299. What are your opening hours?").
- **Embedded Preview Cards**: When a storefront is successfully compiled by `layout-service`, a rich preview card renders directly inside the chat stream with a [Preview] and [Publish] button.

### What Gets Hidden in Settings / Secondary Layers
- **Raw JSON Schemas & Entity Edits**: Moved from the old `ReviewEditScreen` into an advanced "Edit Store JSON / Metadata" drawer or settings menu.
- **Detailed QA Violation Reports**: Instead of cluttering the main flow, QA check results are summarized with a badge ("✓ WCAG 2.2 AA Compliant") in the preview card, with full violation logs tucked behind a "Details" tap.
- **Design Reference & Scraping Tools**: Completely hidden behind developer/admin settings.

---

## 3. Recommended Implementation Steps

1. **Flutter Frontend Refactor (`voicefront/lib/screens/chat_screen.dart`)**:
   - Replace the multi-tab navigation shell with a primary ChatGPT-style chat interface.
   - Wire the text input and voice record button to hit `/v1/nlp/extract` and `/v1/layout/generate`.
2. **State Management**:
   - Maintain the accumulated `StorefrontSpec` state locally in the chat session.
3. **Hidden Drawer (`voicefront/lib/widgets/settings_drawer.dart`)**:
   - Store saved storefront history, API endpoints, and advanced JSON inspection.
