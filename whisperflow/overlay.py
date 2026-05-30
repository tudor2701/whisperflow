"""Floating recording indicator — a small click-through pill with animated bars.

Built on AppKit (PyObjC, already a dependency via rumps). All methods must be
called on the main thread; WhisperFlowApp drives them from a rumps.Timer.

Critical: the panel must never steal keyboard focus, otherwise the Cmd+V paste
would land in the overlay instead of the user's text field. Hence a
non-activating panel shown via orderFrontRegardless (never makeKey...).
"""

import math

from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
)
import objc

# style mask bits (not all exposed as constants in every PyObjC build)
_NS_BORDERLESS = 0
_NS_NONACTIVATING_PANEL = 1 << 7  # NSWindowStyleMaskNonactivatingPanel
_NS_STATUS_WINDOW_LEVEL = 25       # above normal/floating windows

_WIDTH = 96.0
_HEIGHT = 34.0
_MARGIN_BOTTOM = 90.0
_N_BARS = 4


class _WaveView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(_WaveView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._level = 0.0
        self._phase = 0.0
        return self

    def setLevel_(self, lvl):
        self._level = float(lvl)

    def tick(self):
        self._phase += 0.35
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        b = self.bounds()
        w = b.size.width
        h = b.size.height
        radius = h / 2.0

        # dark translucent pill background
        bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.11, 0.11, 0.13, 0.9)
        pill = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(b, radius, radius)
        bg.set()
        pill.fill()

        # animated bars, scaled by mic level
        accent = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.45, 0.78, 1.0, 0.95)
        accent.set()

        bar_w = 5.0
        gap = 6.0
        group_w = _N_BARS * bar_w + (_N_BARS - 1) * gap
        x0 = (w - group_w) / 2.0
        cy = h / 2.0
        level = max(0.04, min(1.0, self._level * 6.0))  # boost: raw RMS is small
        max_bar = h * 0.62

        for i in range(_N_BARS):
            osc = 0.5 + 0.5 * math.sin(self._phase + i * 0.9)
            bar_h = max(4.0, max_bar * level * (0.4 + 0.6 * osc))
            x = x0 + i * (bar_w + gap)
            rect = NSMakeRect(x, cy - bar_h / 2.0, bar_w, bar_h)
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                rect, bar_w / 2.0, bar_w / 2.0
            ).fill()


class Overlay:
    def __init__(self):
        self._panel = None
        self._view = None
        self._visible = False

    def _build(self):
        screen = NSScreen.mainScreen().frame()
        x = (screen.size.width - _WIDTH) / 2.0
        y = _MARGIN_BOTTOM
        frame = NSMakeRect(x, y, _WIDTH, _HEIGHT)

        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            _NS_BORDERLESS | _NS_NONACTIVATING_PANEL,
            NSBackingStoreBuffered,
            False,
        )
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setLevel_(_NS_STATUS_WINDOW_LEVEL)
        panel.setIgnoresMouseEvents_(True)
        panel.setFloatingPanel_(True)
        panel.setBecomesKeyOnlyIfNeeded_(True)
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        view = _WaveView.alloc().initWithFrame_(NSMakeRect(0, 0, _WIDTH, _HEIGHT))
        panel.setContentView_(view)
        self._panel = panel
        self._view = view

    def show(self, level: float) -> None:
        if self._panel is None:
            self._build()
        self._view.setLevel_(level)
        self._view.tick()
        if not self._visible:
            self._panel.orderFrontRegardless()
            self._visible = True

    def hide(self) -> None:
        if self._panel is not None and self._visible:
            self._panel.orderOut_(None)
            self._visible = False
