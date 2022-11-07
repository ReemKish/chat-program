def adjust_lightness(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    r, g, b = colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])
    return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))