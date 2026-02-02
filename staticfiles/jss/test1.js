<script>
document.addEventListener("DOMContentLoaded", function () {
  const replyButtons = document.querySelectorAll(".reply");

  replyButtons.forEach(button => {
    button.addEventListener("click", function () {
      // Remove any existing reply boxes
      document.querySelectorAll(".reply-input.temp-reply").forEach(el => el.remove());

      // Find the comment container where reply was clicked
      const commentContainer = button.closest(".comment.container");

      // Find or create the .replies container below this comment
      let repliesContainer = commentContainer.nextElementSibling;
      if (!repliesContainer || !repliesContainer.classList.contains("replies")) {
        repliesContainer = document.createElement("div");
        repliesContainer.className = "replies comments-wrp";
        commentContainer.after(repliesContainer);
      }

      // Clone the reply input template
      const template = document.querySelector(".reply-input-template");
      const clone = template.content.cloneNode(true);
      const inputBox = clone.querySelector(".reply-input");

      // Mark it as temporary so we can remove later
      inputBox.classList.add("temp-reply");

      // Append to the replies container
      repliesContainer.appendChild(inputBox);

      // OPTIONAL: Handle SEND click
      inputBox.querySelector("button").addEventListener("click", () => {
        const text = inputBox.querySelector("textarea").value.trim();
        if (!text) return alert("Write a reply!");
        // TODO: Submit reply via fetch or AJAX here
        alert("Reply: " + text);
        inputBox.remove();
      });
    });
  });
});
</script>
