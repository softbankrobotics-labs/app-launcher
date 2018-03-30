$(function() {
    viewport = document.querySelector("meta[name=viewport]");
    if (viewport != null) {
      var legacyWidth = 1280;
      var windowWidth = window.screen.width;
      var scale = (windowWidth/legacyWidth).toFixed(3);
      init_str = "initial-scale=".concat(scale.toString());
      min_str = "minimum-scale=".concat(scale.toString());
      max_str = "maximum-scale=".concat(scale.toString());
      viewport.setAttribute("content", init_str.concat(",").concat(min_str).concat(",").concat(max_str));
    }
});