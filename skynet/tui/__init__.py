"""Textual TUI front end for Skynet Hunter.

The engine is headless and already takes an injected `ui` object, so this
package is purely a second front end: `TextualUI` implements the same method
surface as the ANSI `UI` and posts to Textual widgets instead of printing.
"""
