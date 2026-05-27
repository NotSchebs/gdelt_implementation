"""
GDELT GUI Module - Clean re-export of the modular GdeltApp.

The actual implementation is split across organized modules:

Core:
- core/gdelt_app_impl.py: Main GdeltApp orchestrator
- core/gdelt_api.py: GDELT API client
- core/constants.py: Configuration constants
- core/filters.py: Filters window
- core/plotter.py: Timeline plotting

Managers:
- managers/date_range_manager.py: Date handling
- managers/data_manager.py: Data fetching & processing
- managers/export_manager.py: File export
- managers/search_manager.py: Search operations

UI:
- ui/control_panel_ui.py: Control panel UI building
- ui/dialog_manager.py: Dialog windows
- ui/logger.py: Logging to UI panel
"""

from .core.gdelt_app_impl import GdeltApp

__all__ = ["GdeltApp"]
