// Click-to-load YouTube facade: swaps the thumbnail button for the real
// privacy-enhanced iframe only when the viewer plays the video.
document.addEventListener("click", function (e) {
  var btn = e.target.closest(".yt-embed__facade");
  if (!btn) return;
  var iframe = document.createElement("iframe");
  iframe.src =
    "https://www.youtube-nocookie.com/embed/" +
    btn.getAttribute("data-yt-id") +
    "?autoplay=1";
  iframe.allow =
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
  iframe.allowFullscreen = true;
  iframe.title = "YouTube video";
  btn.replaceWith(iframe);
});
