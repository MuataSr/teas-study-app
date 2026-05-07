/**
 * tutor-canvas.js — AI Tutor Canvas Renderer
 * Renders structured drawing commands from the AI tutor into hand-drawn style illustrations.
 * Convention: <div class="tutor-canvas" data-commands='[{...}]'></div>
 *
 * No toolbar, no student interaction — tutor has full control.
 * Uses Fabric.js for canvas management, rough.js for hand-drawn aesthetics.
 */
(function () {
  "use strict";

  var ROUGHNESS = 1.0;
  var DEFAULT_COLOR = "#2D3436";
  var ACCENT_COLOR = "#e74c3c";
  var BG_LIGHT = "#FAFAF7";
  var BG_DARK = "#1e1e2e";
  var DPR = Math.max(1, window.devicePixelRatio || 1);

  // ── Helpers ──

  function isDark() {
    return document.documentElement.classList.contains("dark");
  }

  function bgColor() {
    return isDark() ? BG_DARK : BG_LIGHT;
  }

  function textColor() {
    return isDark() ? "#e0e0e0" : DEFAULT_COLOR;
  }

  function resolveColor(c) {
    if (!c) return textColor();
    return c;
  }

  // ── Render Engine ──

  function renderCanvas(container, commands) {
    var W = parseInt(container.dataset.width) || 760;
    var H = parseInt(container.dataset.height) || 320;

    var canvas = document.createElement("canvas");
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    canvas.style.display = "block";
    canvas.style.borderRadius = "8px";
    canvas.style.margin = "0 auto";

    container.innerHTML = "";
    container.appendChild(canvas);

    var fc = new fabric.StaticCanvas(canvas, {
      width: W,
      height: H,
      backgroundColor: bgColor(),
      selection: false,
      renderOnAddRemove: false
    });

    var rc = rough.canvas(canvas);
    var objects = [];

    commands.forEach(function (cmd) {
      var style = {
        stroke: resolveColor(cmd.color),
        strokeWidth: cmd.strokeWidth || 2,
        fill: cmd.fill || (cmd.filled ? "rgba(46,204,113,0.15)" : undefined),
        fillStyle: cmd.fillStyle || "solid",
        roughness: cmd.roughness || ROUGHNESS,
        bowing: cmd.bowing || 1
      };

      switch (cmd.type) {
        case "line":
          var ln = rc.line(cmd.x1 || 0, cmd.y1 || 0, cmd.x2 || 100, cmd.y2 || 100, style);
          if (ln) objects.push(ln);
          break;

        case "rectangle":
        case "rect":
          var rx = cmd.x || 0, ry = cmd.y || 0;
          var rw = cmd.w || cmd.width || 100, rh = cmd.h || cmd.height || 60;
          var rct = rc.rectangle(rx, ry, rw, rh, style);
          if (rct) objects.push(rct);
          break;

        case "ellipse":
        case "circle":
          var ex = cmd.x || 50, ey = cmd.y || 50;
          var ew = cmd.w || cmd.width || (cmd.radius ? cmd.radius * 2 : 80);
          var eh = cmd.h || cmd.height || (cmd.radius ? cmd.radius * 2 : 80);
          var el = rc.ellipse(ex + ew / 2, ey + eh / 2, ew, eh, style);
          if (el) objects.push(el);
          break;

        case "arc":
          var ar = rc.arc(
            cmd.cx || 100, cmd.cy || 100,
            cmd.width || 80, cmd.height || 80,
            cmd.start || 0, cmd.stop || Math.PI,
            cmd.closed || false, style
          );
          if (ar) objects.push(ar);
          break;

        case "path":
          var pa = rc.path(cmd.d || "M 0 0 L 100 100", style);
          if (pa) objects.push(pa);
          break;

        case "text":
          var txt = new fabric.Text(cmd.content || "", {
            left: cmd.x || 0,
            top: cmd.y || 0,
            fontSize: cmd.fontSize || 16,
            fill: resolveColor(cmd.color),
            fontFamily: cmd.fontFamily || "'Libre Baskerville', Georgia, serif",
            fontWeight: cmd.fontWeight || "normal",
            fontStyle: cmd.italic ? "italic" : "normal"
          });
          objects.push(txt);
          break;

        case "label":
          // Text with optional background box
          var labelSize = (cmd.fontSize || 14) * 1.4;
          var labelW = (cmd.content || "").length * labelSize * 0.6 + 16;
          var labelH = labelSize + 12;
          var lx = cmd.x || 0, ly = cmd.y || 0;

          if (cmd.box !== false) {
            var lb = rc.rectangle(lx - 8, ly - 4, labelW, labelH, {
              stroke: "none",
              fill: cmd.boxColor || (isDark() ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.04)"),
              roughness: 0.3,
              bowing: 0.5
            });
            if (lb) objects.push(lb);
          }

          var lt = new fabric.Text(cmd.content || "", {
            left: lx,
            top: ly,
            fontSize: cmd.fontSize || 14,
            fill: resolveColor(cmd.color),
            fontFamily: "'Source Sans 3', sans-serif",
            fontWeight: cmd.fontWeight || "600"
          });
          objects.push(lt);
          break;

        case "arrow":
          // Line + arrowhead
          var ax1 = cmd.x1 || 0, ay1 = cmd.y1 || 0;
          var ax2 = cmd.x2 || 100, ay2 = cmd.y2 || 100;
          var angle = Math.atan2(ay2 - ay1, ax2 - ax1);
          var headLen = cmd.headLength || 12;

          var arrowLine = rc.line(ax1, ay1, ax2, ay2, style);
          if (arrowLine) objects.push(arrowLine);

          // Arrowhead as two short lines
          var aStyle = Object.assign({}, style, { roughness: 0.5 });
          var h1 = rc.line(
            ax2, ay2,
            ax2 - headLen * Math.cos(angle - Math.PI / 6),
            ay2 - headLen * Math.sin(angle - Math.PI / 6),
            aStyle
          );
          var h2 = rc.line(
            ax2, ay2,
            ax2 - headLen * Math.cos(angle + Math.PI / 6),
            ay2 - headLen * Math.sin(angle + Math.PI / 6),
            aStyle
          );
          if (h1) objects.push(h1);
          if (h2) objects.push(h2);
          break;

        case "grid":
          // Coordinate grid
          var gw = cmd.w || W, gh = cmd.h || H;
          var gx = cmd.x || 0, gy = cmd.y || 0;
          var gStep = cmd.step || 40;
          var gColor = cmd.gridColor || (isDark() ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)");
          var gStyle = { stroke: gColor, strokeWidth: 1, roughness: 0, bowing: 0 };

          for (var xi = gx; xi <= gx + gw; xi += gStep) {
            var vl = rc.line(xi, gy, xi, gy + gh, gStyle);
            if (vl) objects.push(vl);
          }
          for (var yi = gy; yi <= gy + gh; yi += gStep) {
            var hl = rc.line(gx, yi, gx + gw, yi, gStyle);
            if (hl) objects.push(hl);
          }
          break;

        case "plot":
          // Plot points on a line/curve (hand-drawn connected dots)
          var pts = cmd.points || [];
          if (pts.length > 1) {
            var plotStyle = Object.assign({}, style, { roughness: cmd.roughness || 0.8 });
            var plotColor = resolveColor(cmd.color || ACCENT_COLOR);
            plotStyle.stroke = plotColor;

            // Draw connected segments
            for (var pi = 0; pi < pts.length - 1; pi++) {
              var seg = rc.line(pts[pi][0], pts[pi][1], pts[pi + 1][0], pts[pi + 1][1], plotStyle);
              if (seg) objects.push(seg);
            }

            // Draw dots at each point
            if (cmd.dots !== false) {
              pts.forEach(function (pt) {
                var dot = new fabric.Circle({
                  left: pt[0] - 4,
                  top: pt[1] - 4,
                  radius: 4,
                  fill: plotColor,
                  originX: "left",
                  originY: "top"
                });
                objects.push(dot);
              });
            }
          }
          break;

        default:
          console.warn("[tutor-canvas] Unknown command type:", cmd.type);
      }
    });

    // Add all objects to fabric canvas
    objects.forEach(function (obj) {
      fc.add(obj);
    });

    fc.renderAll();
    return fc;
  }

  // ── Auto-Discovery & Rendering ──

  function renderAllCanvases() {
    var containers = document.querySelectorAll(".tutor-canvas:not([data-rendered])");
    containers.forEach(function (el) {
      var raw = el.dataset.commands;
      if (!raw) return;

      try {
        var commands = JSON.parse(raw);
        if (Array.isArray(commands) && commands.length > 0) {
          renderCanvas(el, commands);
          el.setAttribute("data-rendered", "true");
        }
      } catch (e) {
        console.error("[tutor-canvas] Parse error:", e);
        el.innerHTML = '<em style="color:var(--text-secondary);font-size:13px;">(Canvas data error)</em>';
        el.setAttribute("data-rendered", "error");
      }
    });
  }

  // ── Static API (for dynamic content) ──

  window.MU2 = window.MU2 || {};
  window.MU2.tutorCanvas = {
    render: renderCanvas,
    renderAll: renderAllCanvases
  };

  // ── Init ──

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderAllCanvases);
  } else {
    renderAllCanvases();
  }

  // Re-render after dynamic content loads (AJAX, tutor responses)
  document.addEventListener("mu2:content-updated", renderAllCanvases);
})();
