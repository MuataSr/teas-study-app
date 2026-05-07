/**
 * scratchpad.js — TEAS Study Buddy Scratchpad
 * Fabric.js + Rough.js for hand-drawn math sketching
 * Zero framework dependencies, ~100KB total
 */

(function () {
  "use strict";

  // ── Config ──
  const ROUGHNESS = 1.2;
  const STROKE_COLOR = "#2D3436";
  const GRID_COLOR_LIGHT = "rgba(0,0,0,0.04)";
  const GRID_COLOR_DARK = "rgba(255,255,255,0.06)";
  const SHAPE_FILL_ALPHA = "12";

  let canvas, fabricCanvas;
  let activeTool = "pencil";
  let shapeStart = null;
  let undoStack = [];
  const MAX_UNDO = 40;

  // ── Init ──
  window.MU2Scratchpad = {
    init(canvasId) {
      const el = document.getElementById(canvasId);
      if (!el) return;

      canvas = el;
      // Use container width, or viewport as fallback
      const container = canvas.parentElement;
      const rect = container ? container.getBoundingClientRect() : null;
      const w = rect ? Math.min(rect.width, 800) : Math.min(window.innerWidth * 0.9, 800);
      const h = Math.min(window.innerHeight * 0.55, 500);

      canvas.width = w;
      canvas.height = h;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";

      fabricCanvas = new fabric.Canvas(canvasId, {
        isDrawingMode: true,
        width: w,
        height: h,
        backgroundColor: "transparent",
        selection: false,
      });

      fabricCanvas.freeDrawingBrush.color = STROKE_COLOR;
      fabricCanvas.freeDrawingBrush.width = 2;

      this._drawGrid();
      this._bindEvents();
      undoStack = [];
      this._saveState();
    },

    // ── Grid (subtle dot grid, not distracting lines) ──
    _drawGrid() {
      const w = fabricCanvas.width;
      const h = fabricCanvas.height;
      const spacing = 24;
      const isDark = document.documentElement.classList.contains("dark");
      const color = isDark ? GRID_COLOR_DARK : GRID_COLOR_LIGHT;

      // Remove old grid
      const objs = fabricCanvas.getObjects("circle").filter(
        (o) => o._isGridDot
      );
      objs.forEach((o) => fabricCanvas.remove(o));

      for (let x = spacing; x < w; x += spacing) {
        for (let y = spacing; y < h; y += spacing) {
          const dot = new fabric.Circle({
            left: x,
            top: y,
            radius: 0.7,
            fill: color,
            selectable: false,
            evented: false,
            _isGridDot: true,
          });
          fabricCanvas.add(dot);
        }
      }
      fabricCanvas.renderAll();
    },

    // ── Tool Selection ──
    setTool(tool) {
      activeTool = tool;
      shapeStart = null;

      // Highlight active button
      document.querySelectorAll(".sp-tool").forEach((btn) => {
        btn.classList.toggle("sp-tool-active", btn.dataset.tool === tool);
      });

      if (tool === "pencil" || tool === "eraser") {
        fabricCanvas.isDrawingMode = true;
        if (tool === "eraser") {
          fabricCanvas.freeDrawingBrush.color = this._eraserColor();
          fabricCanvas.freeDrawingBrush.width = 18;
        } else {
          fabricCanvas.freeDrawingBrush.color = STROKE_COLOR;
          fabricCanvas.freeDrawingBrush.width = 2;
        }
      } else {
        fabricCanvas.isDrawingMode = false;
      }
    },

    _eraserColor() {
      return document.documentElement.classList.contains("dark")
        ? "#1a1a2e"
        : "#FFFFFF";
    },

    // ── Rough.js Shape Helpers ──
    _roughLine(x1, y1, x2, y2) {
      const rc = rough.canvas(canvas);
      const gen = rc.generator;
      const shape = gen.line(x1, y1, x2, y2, {
        roughness: ROUGHNESS,
        stroke: STROKE_COLOR,
        strokeWidth: 2,
      });
      return this._roughToSVG(shape);
    },

    _roughRect(x1, y1, x2, y2) {
      const rc = rough.canvas(canvas);
      const gen = rc.generator;
      const left = Math.min(x1, x2);
      const top = Math.min(y1, y2);
      const w = Math.abs(x2 - x1);
      const h = Math.abs(y2 - y1);
      if (w < 4 && h < 4) return null;
      const shape = gen.rectangle(left, top, w, h, {
        roughness: ROUGHNESS,
        stroke: STROKE_COLOR,
        strokeWidth: 2,
        fill: STROKE_COLOR,
        fillStyle: "solid",
        fillWeight: 0.3,
      });
      return this._roughToSVG(shape);
    },

    _roughCircle(cx, cy, x2, y2) {
      const rc = rough.canvas(canvas);
      const gen = rc.generator;
      const rx = Math.abs(x2 - cx) / 2;
      const ry = Math.abs(y2 - cy) / 2;
      const left = Math.min(cx, x2);
      const top = Math.min(cy, y2);
      if (rx < 4 && ry < 4) return null;
      const shape = gen.ellipse(
        left + rx,
        top + ry,
        rx * 2,
        ry * 2,
        {
          roughness: ROUGHNESS,
          stroke: STROKE_COLOR,
          strokeWidth: 2,
          fill: STROKE_COLOR,
          fillStyle: "solid",
          fillWeight: 0.3,
        }
      );
      return this._roughToSVG(shape);
    },

    _roughToSVG(shape) {
      // Convert rough.js shape to fabric.js SVG group
      const svgStr = `<svg xmlns="http://www.w3.org/2000/svg">${shape}</svg>`;
      return svgStr;
    },

    _addRoughShape(svgStr) {
      if (!svgStr) return;
      fabric.loadSVGFromString(svgStr, (objects, options) => {
        const group = fabric.util.groupSVGElements(objects, options);
        group.set({
          selectable: true,
          evented: true,
          _isScratchpadShape: true,
        });
        fabricCanvas.add(group);
        fabricCanvas.renderAll();
        this._saveState();
      });
    },

    // ── Event Binding ──
    _bindEvents() {
      // Shape drawing (mouse:down → move → up)
      fabricCanvas.on("mouse:down", (opt) => {
        if (fabricCanvas.isDrawingMode) return;
        if (activeTool === "text") {
          this._addTextAt(opt.pointer);
          return;
        }
        shapeStart = opt.pointer;
      });

      fabricCanvas.on("mouse:move", (opt) => {
        if (!shapeStart || fabricCanvas.isDrawingMode) return;
        // Remove preview shapes
        const previews = fabricCanvas.getObjects().filter(
          (o) => o._isPreview
        );
        previews.forEach((o) => fabricCanvas.remove(o));

        let svg = null;
        const p = opt.pointer;
        if (activeTool === "line") {
          svg = this._roughLine(shapeStart.x, shapeStart.y, p.x, p.y);
        } else if (activeTool === "rect") {
          svg = this._roughRect(shapeStart.x, shapeStart.y, p.x, p.y);
        } else if (activeTool === "circle") {
          svg = this._roughCircle(shapeStart.x, shapeStart.y, p.x, p.y);
        }

        if (svg) {
          fabric.loadSVGFromString(svg, (objects, options) => {
            const group = fabric.util.groupSVGElements(objects, options);
            group.set({ selectable: false, evented: false, _isPreview: true });
            fabricCanvas.add(group);
            fabricCanvas.renderAll();
          });
        }
      });

      fabricCanvas.on("mouse:up", () => {
        if (!shapeStart || fabricCanvas.isDrawingMode) return;

        // Remove preview, add final shape
        const previews = fabricCanvas.getObjects().filter(
          (o) => o._isPreview
        );
        previews.forEach((o) => fabricCanvas.remove(o));

        // Re-draw final shape at last position
        const lastPointer = fabricCanvas.getPointer(
          fabricCanvas.getPointer(null)
        );
        // The last mouse:move already drew it, just finalize
        // Actually, mouse:up fires after last move, so grab the last preview position
        // Simpler: just save state (shape is already on canvas from move)
        shapeStart = null;
        this._saveState();
      });

      // Undo on path completion (drawing mode)
      fabricCanvas.on("path:created", () => {
        this._saveState();
      });
    },

    // ── Text Tool ──
    _addTextAt(pointer) {
      const isDark = document.documentElement.classList.contains("dark");
      const text = new fabric.IText("Type here", {
        left: pointer.x,
        top: pointer.y,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        fontSize: 16,
        fill: isDark ? "#e0e0e0" : STROKE_COLOR,
        editable: true,
        _isScratchpadShape: true,
      });
      fabricCanvas.add(text);
      fabricCanvas.setActiveObject(text);
      text.enterEditing();
      this._saveState();
    },

    // ── Undo ──
    undo() {
      if (undoStack.length <= 1) return; // keep initial state
      undoStack.pop(); // remove current
      const prev = undoStack[undoStack.length - 1];
      fabricCanvas.loadFromJSON(prev, () => {
        // Re-apply non-selectable flags to grid dots
        fabricCanvas.getObjects().forEach((o) => {
          if (o._isGridDot) {
            o.set({ selectable: false, evented: false });
          }
        });
        fabricCanvas.renderAll();
      });
    },

    // ── Clear ──
    clear() {
      const gridDots = fabricCanvas.getObjects().filter((o) => o._isGridDot);
      fabricCanvas.clear();
      gridDots.forEach((d) => fabricCanvas.add(d));
      fabricCanvas.renderAll();
      this._saveState();
    },

    // ── State Management ──
    _saveState() {
      const json = JSON.stringify(fabricCanvas.toJSON());
      undoStack.push(json);
      if (undoStack.length > MAX_UNDO) undoStack.shift();
    },

    // ── Export ──
    toDataURL() {
      return fabricCanvas.toDataURL({ format: "png", multiplier: 2 });
    },

    toJSON() {
      return fabricCanvas.toJSON();
    },

    // ── Redraw on theme change ──
    redrawGrid() {
      this._drawGrid();
    },

    // ── Resize ──
    resize() {
      const container = canvas.parentElement;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const w = Math.min(rect.width, 800);
      const h = Math.min(window.innerHeight * 0.55, 500);
      fabricCanvas.setDimensions({ width: w, height: h });
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      this._drawGrid();
    },
  };
})();
