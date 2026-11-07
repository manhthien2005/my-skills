"""Native editable PowerPoint charts (python-pptx) + mini sparklines for KPI tiles.

Careful OOXML compliance rules:
- Stacked column charts use XL_LABEL_POSITION.CENTER (OUTSIDE_END is invalid in OOXML for stacked series).
- Doughnut charts NEVER set data_labels.position (<c:dLblPos> is invalid inside <c:doughnutChart> in PowerPoint).
"""
from __future__ import annotations

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.util import Inches, Pt

from ..common import fmt_num
from .draw import Canvas, rgb


def _hl_index(spec: dict) -> int | None:
    h = spec.get('highlight')
    if h is None:
        return None
    if isinstance(h, int):
        return h
    try:
        return [str(x) for x in spec['categories']].index(str(h))
    except ValueError:
        return None


def _num_format(unit: str, values: list[float]) -> str:
    decimals = 0
    for v in values:
        if abs(v - round(v)) > 1e-6:
            decimals = max(decimals, 1 if abs(v * 10 - round(v * 10)) < 1e-6 else 2)
    base = '#,##0' if decimals == 0 else ('#,##0.0' if decimals == 1 else '#,##0.00')
    if not unit:
        return base
    if unit == '%':
        return f'{base}"%"'
    safe = unit.replace('"', '')
    return f'{base}"{safe}"' if safe in ('x', '×', '°', '°C', 'pp') else f'{base}" {safe}"'


def add_native_chart(cv: Canvas, spec: dict, x: float, y: float, w: float, h: float, lang: str = 'vi'):
    """Insert a native PowerPoint chart styled with the active theme tokens."""
    kind = spec.get('type', 'column')
    cats = [str(c) for c in (spec.get('categories') or [])]
    series_list = spec.get('series') or []
    unit = spec.get('unit', '')
    pal = cv.t['colors']['series']
    hl = _hl_index(spec)

    xl_type = {
        'column': XL_CHART_TYPE.COLUMN_CLUSTERED,
        'stacked': XL_CHART_TYPE.COLUMN_STACKED,
        'bar': XL_CHART_TYPE.BAR_CLUSTERED,
        'line': XL_CHART_TYPE.LINE_MARKERS,
        'donut': XL_CHART_TYPE.DOUGHNUT,
    }.get(kind, XL_CHART_TYPE.COLUMN_CLUSTERED)

    data = CategoryChartData()
    data.categories = cats
    if kind == 'donut':
        se0 = series_list[0] if series_list else {'name': '', 'values': []}
        data.add_series(str(se0.get('name') or spec.get('title') or 'Series'), [float(v or 0) for v in se0.get('values', [])])
    else:
        for idx, se in enumerate(series_list):
            data.add_series(str(se.get('name') or f'Series {idx + 1}'), [float(v or 0) for v in se.get('values', [])])

    gf = cv._track(cv.s.shapes.add_chart(xl_type, Inches(x), Inches(y), Inches(w), Inches(h), data))
    ch = gf.chart
    ch.has_title = False
    ch.font.name = cv.f['body']
    ch.font.size = Pt(10.5)
    ch.font.color.rgb = rgb(cv.c['ink'])

    plot = ch.plots[0]
    if kind in ('column', 'stacked', 'bar'):
        plot.gap_width = 85 if len(series_list) == 1 or kind == 'stacked' else 110
        if kind == 'stacked':
            plot.overlap = 100
        elif len(series_list) > 1:
            plot.overlap = -12
    if kind == 'donut':
        try:
            plot.VaryByCategories = True
        except Exception:
            pass

    # Legend
    multi = len(series_list) > 1
    if kind == 'donut':
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = True
        ch.legend.font.name = cv.f['body']
        ch.legend.font.size = Pt(11)
        ch.legend.font.color.rgb = rgb(cv.c['ink'])
    elif multi:
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = True
        ch.legend.font.name = cv.f['body']
        ch.legend.font.size = Pt(10.5)
        ch.legend.font.color.rgb = rgb(cv.c['muted'])
    else:
        ch.has_legend = False

    # Series & point styling
    all_series_vals = [float(v or 0) for se in series_list for v in se.get('values', [])]
    num_fmt = _num_format(unit, all_series_vals)
    raw_fmt = _num_format('', all_series_vals)
    for si, ser in enumerate(plot.series):
        col_hex = (series_list[si].get('color') if si < len(series_list) else None) or pal[si % len(pal)]
        if kind == 'line':
            ser.format.line.color.rgb = rgb(col_hex)
            ser.format.line.width = Pt(2.75)
            ser.smooth = False
            ser.marker.style = XL_MARKER_STYLE.CIRCLE
            ser.marker.size = 8
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = rgb(col_hex)
            ser.marker.format.line.color.rgb = rgb(cv.c['bg'])
            ser.marker.format.line.width = Pt(1.2)
        elif kind == 'donut':
            for pi, pt in enumerate(ser.points):
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = rgb(pal[pi % len(pal)])
                pt.format.line.color.rgb = rgb(cv.c['bg'])
                pt.format.line.width = Pt(1.5)
        else:
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = rgb(col_hex)
            ser.format.line.fill.background()
            if hl is not None and len(series_list) == 1 and kind in ('column', 'bar'):
                muted_bar = cv.c['surface_alt'] if cv.dark else cv.c['line']
                for pi, pt in enumerate(ser.points):
                    pt.format.fill.solid()
                    pt.format.fill.fore_color.rgb = rgb(cv.c['accent_strong'] if pi == hl else muted_bar)

    # Data labels
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.name = cv.f['body']
    dl.font.bold = True
    if kind == 'donut':
        # Never set dl.position on DOUGHNUT: <c:dLblPos> is invalid OOXML for doughnut charts.
        dl.show_percentage = True
        dl.show_value = False
        dl.show_category_name = False
        dl.font.size = Pt(10.5)
        dl.font.color.rgb = rgb('#FFFFFF')
    elif kind == 'stacked':
        dl.position = XL_LABEL_POSITION.CENTER
        dl.show_value = True
        dl.number_format = raw_fmt
        dl.number_format_is_linked = False
        dl.font.size = Pt(9.5)
        dl.font.color.rgb = rgb('#FFFFFF')
    elif kind == 'line':
        dl.position = XL_LABEL_POSITION.ABOVE
        dl.show_value = True
        dl.number_format = num_fmt
        dl.number_format_is_linked = False
        dl.font.size = Pt(9.5)
        dl.font.color.rgb = rgb(cv.c['ink'])
    else:
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        dl.show_value = True
        dl.number_format = num_fmt
        dl.number_format_is_linked = False
        dl.font.size = Pt(10 if not multi else 9)
        dl.font.color.rgb = rgb(cv.c['ink'])

    # Axes styling (not present on doughnut)
    if kind != 'donut':
        cat_ax = ch.category_axis
        cat_ax.has_major_gridlines = False
        cat_ax.format.line.color.rgb = rgb(cv.c['line'])
        cat_ax.format.line.width = Pt(1.0)
        cat_ax.tick_labels.font.name = cv.f['body']
        cat_ax.tick_labels.font.size = Pt(10.5)
        cat_ax.tick_labels.font.bold = True
        cat_ax.tick_labels.font.color.rgb = rgb(cv.c['ink'] if kind == 'bar' else cv.c['muted'])

        val_ax = ch.value_axis
        all_vals = [float(v or 0) for se in series_list for v in se.get('values', [])]
        if all_vals and min(all_vals) >= 0:
            val_ax.minimum_scale = 0.0
        val_ax.has_major_gridlines = kind != 'bar'
        if val_ax.has_major_gridlines:
            val_ax.major_gridlines.format.line.color.rgb = rgb(cv.c['line'])
            val_ax.major_gridlines.format.line.width = Pt(0.75)
        val_ax.format.line.fill.background()
        val_ax.tick_labels.font.name = cv.f['body']
        val_ax.tick_labels.font.size = Pt(9.5)
        val_ax.tick_labels.font.color.rgb = rgb(cv.c['subtle'])
        val_ax.tick_labels.number_format = 'General'
        val_ax.tick_labels.number_format_is_linked = False
        if kind == 'bar':
            val_ax.visible = False

    # Doughnut center summary label (centered horizontally over plot hole with BOTTOM legend)
    if kind == 'donut':
        vals = [float(v or 0) for v in (series_list[0].get('values', []) if series_list else [])]
        total = sum(vals)
        center = spec.get('center_label') or fmt_num(total, lang, unit)
        hole_cx = x + w * 0.50
        hole_cy = y + h * 0.435
        cv.text(hole_cx - 1.15, hole_cy - 0.34, 2.3, 0.46, str(center), 20, color=cv.c['ink'], bold=True,
                font='display', align='c', anchor='m', min_size=13, check=False)
        if spec.get('center_caption'):
            cv.text(hole_cx - 1.15, hole_cy + 0.12, 2.3, 0.28, str(spec['center_caption']), 9.5, color=cv.c['muted'],
                    align='c', anchor='t', min_size=8, check=False)
    return gf


def draw_sparkline(cv: Canvas, values: list, x: float, y: float, w: float, h: float, color: str):
    """Draw a clean editable vector sparkline using straight connectors + terminal dot."""
    if not values or len(values) < 2:
        return
    nums = [float(v) for v in values]
    lo, hi = min(nums), max(nums)
    rng = (hi - lo) or 1.0
    pts = [(x + w * i / (len(nums) - 1), y + h - h * (v - lo) / rng) for i, v in enumerate(nums)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        cv.line(x1, y1, x2, y2, color, width=1.8)
    lx, ly = pts[-1]
    cv.oval(lx - 0.045, ly - 0.045, 0.09, 0.09, fill=color)
