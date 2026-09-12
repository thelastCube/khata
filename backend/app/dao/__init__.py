"""Data access layer. These modules are the ONLY place SQL is written.
Each DAO takes a sqlite3.Connection and returns domain models (app.models).
Entity DAOs land in Phase 1."""
