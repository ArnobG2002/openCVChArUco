/* download-bg.js
 * Adds a "Download" button to every element that has a CSS background-image.
 * Usage: <script src="download-bg.js" defer></script>
 * Opt out on a specific element with data-no-download.
 */
(function () {
  "use strict";

  var SELECTOR = "[data-download-bg], .animatedSprite, .animatedSprite1";

  function bgUrl(el) {
    var bg = getComputedStyle(el).backgroundImage;
    if (!bg || bg === "none") return null;
    var m = /url\((['"]?)(.*?)\1\)/.exec(bg); // first layer only
    return m ? m[2] : null;
  }

  function fileName(url) {
    try {
      var p = new URL(url, location.href).pathname;
      return decodeURIComponent(p.substring(p.lastIndexOf("/") + 1)) || "image.png";
    } catch (e) {
      return "image.png";
    }
  }

  function makeButton(url) {
    var a = document.createElement("a");
    a.className = "bg-download-btn";
    a.href = url;
    a.download = fileName(url);
    a.title = "Download " + a.download;
    a.textContent = "⬇ Download sprite";
    // Cross-origin images ignore `download`; fetch as a blob instead.
    a.addEventListener("click", function (ev) {
      if (new URL(url, location.href).origin === location.origin) return; // native path
      ev.preventDefault();
      fetch(url, { mode: "cors" })
        .then(function (r) { return r.blob(); })
        .then(function (blob) {
          var obj = URL.createObjectURL(blob);
          var tmp = document.createElement("a");
          tmp.href = obj;
          tmp.download = a.download;
          tmp.click();
          setTimeout(function () { URL.revokeObjectURL(obj); }, 1000);
        })
        .catch(function () { window.open(url, "_blank"); });
    });
    return a;
  }

  function decorate(el) {
    if (el.dataset.noDownload || el.dataset.bgDownloadReady) return;
    var url = bgUrl(el);
    if (!url) return;
    el.dataset.bgDownloadReady = "1";

    var wrap = document.createElement("div");
    wrap.className = "bg-download-wrap";
    el.parentNode.insertBefore(wrap, el);
    wrap.appendChild(el);
    wrap.appendChild(makeButton(url));
  }

  function injectStyles() {
    var css = [
      ".bg-download-wrap{position:relative;display:inline-block;max-width:100%;width:100%;}",
      ".bg-download-btn{position:absolute;top:8px;right:15%;z-index:5;",
      "display:inline-flex;align-items:center;gap:.35em;",
      "padding:.35em .7em;border-radius:6px;font:500 13px/1.2 system-ui,sans-serif;",
      "background:rgba(0,0,0,.65);color:#fff;text-decoration:none;",
      "opacity:0;transition:opacity .15s ease;pointer-events:none;}",
      ".bg-download-wrap:hover .bg-download-btn,.bg-download-btn:focus{opacity:1;pointer-events:auto;}",
      ".bg-download-btn:hover{background:rgba(0,0,0,.85);color:#fff;}",
      "@media (hover:none){.bg-download-btn{opacity:1;pointer-events:auto;}}"
    ].join("");
    var s = document.createElement("style");
    s.textContent = css;
    document.head.appendChild(s);
  }

  function init() {
    injectStyles();
    document.querySelectorAll(SELECTOR).forEach(decorate);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
