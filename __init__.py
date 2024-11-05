def classFactory(iface):
    from .plugin import SurfaceRatioPlugin
    return SurfaceRatioPlugin(iface)