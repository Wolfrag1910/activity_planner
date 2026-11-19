// Quick preview of an event.
//
// Tapping an event card asks the server for its preview (htmx, see the hx-get
// on the card) and puts it inside the <dialog id="preview"> at the bottom of
// base.html. This file opens and closes that dialog. The dialog is a bottom
// sheet on phones and a side panel on desktop (CSS in app.css).
//
// Without JavaScript, the cards are plain links to the event page.

(function () {
  var dialog = document.getElementById("preview");
  if (!dialog) return;
  var answerChanged = false;

  // A preview arrived: open the dialog (it moves keyboard focus inside).
  document.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target.id === "preview-body" && !dialog.open) dialog.showModal();
  });

  // Close with the X button, or by tapping the dimmed area around the panel.
  dialog.addEventListener("click", function (event) {
    if (event.target.closest("[data-close-preview]") || event.target === dialog) dialog.close();
  });

  // The server says an answer was saved inside the preview (HX-Trigger: answerSaved).
  document.body.addEventListener("answerSaved", function () {
    answerChanged = true;
  });

  // When the preview closes after an answer changed, reload the page underneath
  // so its lists show the new answer.
  dialog.addEventListener("close", function () {
    document.getElementById("preview-body").innerHTML = "";
    if (answerChanged) window.location.reload();
  });
})();
