// With JavaScript on, "Going" saves on tap, so the Save button is only needed for Maybe and No.
document.documentElement.classList.add("js");

// Event page: choosing "Going" saves the answer straight away (one tap).
// Choosing Maybe or No shows the quick reasons first; the member then presses "Save my answer".
document.addEventListener("change", function (event) {
  var input = event.target;
  if (input.name !== "answer" || input.value !== "going") return;
  var form = input.closest("[data-answer-form]");
  if (form && form.requestSubmit) form.requestSubmit();
});
