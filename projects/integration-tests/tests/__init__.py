"""Integration tests for GCOM system.

This package contains end-to-end integration tests that verify the full
communication flow: web-backend → mission-planner → SITL.

All tests hit the web-backend API, which forwards requests to mission-planner,
ensuring the complete integration path is tested.
"""
