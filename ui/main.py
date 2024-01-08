from ..tools.common import version_2_79_or_older
from ..tools.translations import t

class ToolPanel(object):
    bl_label = t('ToolPanel.label')
    bl_idname = '3D_VIEW_TS_vrc'
    bl_category = t('ToolPanel.category')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'


def layout_split(layout, factor=0.0, align=False):
    return layout.split(factor=factor, align=align)
