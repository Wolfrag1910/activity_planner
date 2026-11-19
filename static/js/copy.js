// "Copy link" buttons: <button data-copy="#some-input" data-copied-text="Copied">.
// Copies the input's text to the clipboard and briefly shows the "copied" label.
document.addEventListener("click", function (event) {
  var button = event.target.closest("[data-copy]");
  if (!button) return;
  var field = document.querySelector(button.getAttribute("data-copy"));
  if (!field) return;
  var original = button.textContent;
  function done() {
    button.textContent = button.getAttribute("data-copied-text") || original;
    setTimeout(function () { button.textContent = original; }, 2000);
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(field.value).then(done);
  } else {
    field.select();
    document.execCommand("copy");
    done();
  }
});
