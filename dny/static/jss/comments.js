<script>
const data = {
  currentUser: {
    image: {
      png: "./images/avatars/image-juliusomo.png",
      webp: "./images/avatars/image-juliusomo.webp",
    },
    username: "{{ request.user.username }}",
  },
  comments: [
    {% for comment in comments %}
    {
      parent: 0,
      id: {{ comment.id }},
      content: "{{ comment.content|escapejs }}",
      createdAt: "{{ comment.time|timesince }} ago",
      score: 12,
      user: {
        image: {
          png: "./images/avatars/image-amyrobson.png",
          webp: "./images/avatars/image-amyrobson.webp",
        },
        username: "{{ comment.customer.username }}",
      },
      replies: [
        {% for reply in comment.replies.all %}
        {
          parent: {{ comment.id }},
          id: {{ reply.id }},
          content: "{{ reply.content|escapejs }}",
          createdAt: "{{ reply.time|timesince }} ago",
          replyingTo: "{{ reply.replying_to.customer.username }}",
          score: {{ reply.score }},
          user: {
            image: {
              png: "{{ reply.customer.profile.image.url }}",
              webp: "{{ reply.customer.profile.image.url }}",
            },
            username: "{{ reply.customer.username }}",
          }
        },
        {% endfor %}
      ]
    },
    {% endfor %}
  ]
};

const appendFrag = (frag, parent) => {
  const clone = frag.cloneNode(true);
  const tempDiv = document.createElement("div");
  tempDiv.appendChild(clone);
  parent.appendChild(tempDiv.firstElementChild);
  return parent.lastElementChild;
};

const addComment = (body, parentId, replyTo = undefined) => {
  const commentParent =
    parentId === 0
      ? data.comments
      : data.comments.find((c) => c.id == parentId).replies;

  const newComment = {
    parent: parentId,
    id: commentParent.length === 0 ? 1 : commentParent[commentParent.length - 1].id + 1,
    content: body,
    createdAt: "Now",
    replyingTo: replyTo,
    score: 0,
    replies: parentId === 0 ? [] : undefined,
    user: data.currentUser,
  };
  commentParent.push(newComment);
  initComments();
};

const deleteComment = (commentObject) => {
  if (commentObject.parent == 0) {
    data.comments = data.comments.filter((e) => e !== commentObject);
  } else {
    const parent = data.comments.find((e) => e.id === commentObject.parent);
    parent.replies = parent.replies.filter((e) => e !== commentObject);
  }
  initComments();
};

const promptDel = (commentObject) => {
  const modalWrp = document.querySelector(".modal-wrp");
  modalWrp.classList.remove("invisible");
  modalWrp.querySelector(".yes").addEventListener("click", () => {
    deleteComment(commentObject);
    modalWrp.classList.add("invisible");
  });
  modalWrp.querySelector(".no").addEventListener("click", () => {
    modalWrp.classList.add("invisible");
  });
};

const createCommentNode = (commentObject) => {
  const commentTemplate = document.querySelector(".comment-template");
  const commentNode = commentTemplate.content.cloneNode(true);

  commentNode.querySelector(".usr-name").textContent = commentObject.user.username;
  commentNode.querySelector(".usr-img").src = commentObject.user.image.webp;
  commentNode.querySelector(".score-number").textContent = commentObject.score;
  commentNode.querySelector(".cmnt-at").textContent = commentObject.createdAt;
  commentNode.querySelector(".c-body").textContent = commentObject.content;

  if (commentObject.replyingTo) {
    commentNode.querySelector(".reply-to").textContent = "@" + commentObject.replyingTo;
  }

  commentNode.querySelector(".score-plus").addEventListener("click", () => {
    commentObject.score++;
    initComments();
  });

  commentNode.querySelector(".score-minus").addEventListener("click", () => {
    commentObject.score = Math.max(0, commentObject.score - 1);
    initComments();
  });

  if (commentObject.user.username === data.currentUser.username) {
    commentNode.querySelector(".comment").classList.add("this-user");

    commentNode.querySelector(".delete").addEventListener("click", () => {
      promptDel(commentObject);
    });

    commentNode.querySelector(".edit").addEventListener("click", (e) => {
      const bodyEl = e.target.closest(".comment").querySelector(".c-body");
      const isEditable = bodyEl.getAttribute("contenteditable");
      if (!isEditable || isEditable === "false") {
        bodyEl.setAttribute("contenteditable", true);
        bodyEl.focus();
      } else {
        bodyEl.removeAttribute("contenteditable");
      }
    });
  }

  return commentNode;
};

const appendComment = (parent, commentNode, parentId) => {
  parent.appendChild(commentNode);
};

function initComments(commentList = data.comments, parent = document.querySelector(".comments-wrp")) {
  parent.innerHTML = "";
  commentList.forEach((element) => {
    const parentId = element.parent === 0 ? element.id : element.parent;
    const commentNode = createCommentNode(element);
    if (element.replies && element.replies.length > 0) {
      initComments(element.replies, commentNode.querySelector(".replies"));
    }
    appendComment(parent, commentNode, parentId);
  });
}

initComments();

const cmntInput = document.querySelector(".reply-input");
cmntInput.querySelector(".bu-primary").addEventListener("click", () => {
  const commentBody = cmntInput.querySelector(".cmnt-input").value.trim();
  if (commentBody.length === 0) return;
  addComment(commentBody, 0);
  cmntInput.querySelector(".cmnt-input").value = "";
});

// New reply input logic
document.addEventListener("DOMContentLoaded", function () {
  const replyButtons = document.querySelectorAll(".reply");

  replyButtons.forEach(button => {
    button.addEventListener("click", function () {
      document.querySelectorAll(".reply-input.temp-reply").forEach(el => el.remove());

      const commentContainer = button.closest(".comment.container");

      let repliesContainer = commentContainer.nextElementSibling;
      if (!repliesContainer || !repliesContainer.classList.contains("replies")) {
        repliesContainer = document.createElement("div");
        repliesContainer.className = "replies comments-wrp";
        commentContainer.after(repliesContainer);
      }

      const template = document.querySelector(".reply-input-template");
      const clone = template.content.cloneNode(true);
      const inputBox = clone.querySelector(".reply-input");
      inputBox.classList.add("temp-reply");

      repliesContainer.appendChild(inputBox);

      inputBox.querySelector("button").addEventListener("click", () => {
        const text = inputBox.querySelector("textarea").value.trim();
        if (!text) return alert("Write a reply!");
        alert("Reply: " + text); // Replace with fetch/AJAX if needed
        inputBox.remove();
      });
    });
  });
});
</script>
