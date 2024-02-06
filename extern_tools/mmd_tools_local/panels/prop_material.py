# -*- coding: utf-8 -*-

import bpy
from bpy.types import Panel

from mmd_tools_local import register_wrap
from mmd_tools_local.core.material import FnMaterial


ICON_FILE_FOLDER = 'FILE_FOLDER'
if bpy.app.version < (2, 80, 0):
    ICON_FILE_FOLDER = 'FILESEL'