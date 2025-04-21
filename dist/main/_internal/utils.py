import os, sys

def resource_path(relative_path):
    """
    Get the absolute path to a resource, working in both dev and PyInstaller bundles.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)
