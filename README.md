## Configuration

This project uses environment variables for configuration.

1.  Copy the template file `.env.template` to a new file named `.env`:
    ```bash
    cp .env.template .env
    ```
2.  **Edit the `.env` file** and fill in your actual API keys, tokens, URLs, and other settings.
    *   **IMPORTANT:** The `.env` file contains sensitive credentials and **must not** be committed to version control. Ensure `.env` is listed in your `.gitignore` file.

## Development with Cursor AI

This project is optimized for development using [Cursor AI](https://cursor.sh/). Please follow these best practices:

1.  **Provide Context:** Always use `@file`, `@folder`, or `@Codebase` to provide relevant context to Cursor AI. Key configuration files to reference include:
    *   `docs/project_concept_for_cursor.md` (Project goals)
    *   `docs/tech_stack_research_for_cursor.md` (Technical directives)
    *   `docs/project_structure.md` (File organization blueprint)
    *   `.cursorrules` (AI behavior guidelines)
2.  **Use Project Structure:** Adhere to the file structure outlined in `docs/project_structure.md` when creating new files or asking Cursor to modify existing code.
3.  **Follow Rules:** The `.cursorrules` file defines the expected coding style, patterns, and constraints. Ensure Cursor follows these guidelines.
4.  **Iterate and Review:** Break down complex tasks. Review all generated code carefully. Use Cursor's Edit mode (Cmd/Ctrl+K) for quick refinements.
5.  **Version Control:** Commit frequently. Use `@git` context in Cursor chat to help generate commit messages based on changes."# areal-ai-agent" 
