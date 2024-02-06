import bpy

from .. import globs
from .main import ToolPanel, layout_split
from ..tools import settings as Settings
from ..tools.register import register_wrap
from ..tools.translations import t, DownloadTranslations