function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("community-feed-page");
    if (!page) {
        return;
    }

    const feedUrl = page.dataset.feedUrl;
    const commentsTemplate = page.dataset.commentsTemplate;
    const reactTemplate = page.dataset.reactTemplate;

    const feedList = document.getElementById("feed-list");
    const feedStatus = document.getElementById("feed-status");
    const loadMoreBtn = document.getElementById("load-more-btn");

    let offset = 0;
    const limit = 10;
    let total = 0;
    let isLoading = false;

    function buildUrlFromTemplate(template, postId) {
        return template.replace("/0/", `/${postId}/`);
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatReactionLabel(type, counts, myReaction) {
        const count = counts && counts[type] ? counts[type] : 0;
        const isActive = myReaction === type;
        const labels = {
            LIKE: "Like",
            LOVE: "Love",
            WOW: "Wow",
        };

        return `
            <button
                type="button"
                class="feed-reaction-btn ${isActive ? "active" : ""}"
                data-post-id="${counts.__postId}"
                data-reaction-type="${type}"
            >
                ${labels[type]} (${count})
            </button>
        `;
    }

    function renderPost(post) {
        const proofHtml = post.run.proof_file
            ? `
                <div class="feed-proof">
                    <img src="${post.run.proof_file}" alt="Proof uploaded for ${escapeHtml(post.quest.name)}" loading="lazy">
                </div>
            `
            : "";

        const noteHtml = post.run.note
            ? `<p class="feed-note">${escapeHtml(post.run.note)}</p>`
            : "";

        const counts = Object.assign({}, post.reaction_counts || {}, { __postId: post.post_id });

        return `
            <article class="page-card feed-post" id="post-${post.post_id}">
                <div class="feed-post-header">
                    <div class="feed-post-meta">
                        <div class="feed-user-line">${escapeHtml(post.user.username)}</div>
                        <div class="feed-sub-line">
                            ${escapeHtml(post.quest.name)} in ${escapeHtml(post.city.name)}
                        </div>
                        <div class="feed-sub-line">
                            ${new Date(post.created_at).toLocaleString()}
                        </div>
                    </div>

                    <span class="feed-chip">${escapeHtml(post.quest.type || "Quest")}</span>
                </div>

                <div class="feed-badge-row">
                    <span class="feed-chip">⏱ ${post.run.time_minutes ?? "—"} min</span>
                    <span class="feed-chip">👣 ${post.run.steps ?? 0} steps</span>
                    <span class="feed-chip">📏 ${post.run.distance_km ?? "0"} km</span>
                    <span class="feed-chip">👥 Group ${post.run.group_size ?? "—"}</span>
                </div>

                ${noteHtml}
                ${proofHtml}

                <div class="feed-actions">
                    <div class="feed-reaction-group">
                        ${formatReactionLabel("LIKE", counts, post.my_reaction)}
                        ${formatReactionLabel("LOVE", counts, post.my_reaction)}
                        ${formatReactionLabel("WOW", counts, post.my_reaction)}
                    </div>

                    <button
                        type="button"
                        class="btn btn-sm btn-outline-secondary toggle-comments-btn"
                        data-post-id="${post.post_id}"
                    >
                        Comments (${post.comment_count ?? 0})
                    </button>
                </div>

                <div class="feed-comments-wrap" id="comments-wrap-${post.post_id}">
                    <div class="feed-comments-list" id="comments-list-${post.post_id}"></div>

                    <form class="feed-comment-form" data-post-id="${post.post_id}">
                        <textarea
                            class="form-control"
                            name="text"
                            rows="2"
                            placeholder="Write a comment..."
                        ></textarea>
                        <button type="submit" class="btn btn-primary btn-sm">Post</button>
                    </form>
                </div>
            </article>
        `;
    }

    function setStatus(message, type) {
        feedStatus.className = `alert alert-${type} border mb-4`;
        feedStatus.textContent = message;
    }

    function renderEmptyState() {
        feedList.innerHTML = `
            <div class="page-card feed-empty">
                No public posts for this city yet.
            </div>
        `;
    }

    async function loadFeed(reset = false) {
        if (isLoading) {
            return;
        }

        isLoading = true;
        loadMoreBtn.classList.add("d-none");

        if (reset) {
            offset = 0;
            total = 0;
            feedList.innerHTML = "";
            setStatus("Loading community posts...", "light");
        }

        try {
            const response = await fetch(`${feedUrl}?limit=${limit}&offset=${offset}`);
            const data = await response.json();

            if (!response.ok) {
                setStatus(data.error || "Unable to load feed.", "danger");
                isLoading = false;
                return;
            }

            total = data.meta.total || 0;
            const posts = data.results || [];

            if (reset && posts.length === 0) {
                renderEmptyState();
                setStatus("No posts found for your selected city yet.", "light");
                isLoading = false;
                return;
            }

            const html = posts.map(renderPost).join("");
            feedList.insertAdjacentHTML("beforeend", html);

            offset += posts.length;

            if (offset < total) {
                loadMoreBtn.classList.remove("d-none");
            }

            setStatus(`Showing ${offset} of ${total} posts.`, "success");
        } catch (error) {
            setStatus("Unexpected error while loading the feed.", "danger");
        }

        isLoading = false;
    }

    async function loadComments(postId) {
        const listEl = document.getElementById(`comments-list-${postId}`);
        if (!listEl || listEl.dataset.loaded === "true") {
            return;
        }

        listEl.innerHTML = `<div class="text-muted small">Loading comments...</div>`;

        try {
            const response = await fetch(buildUrlFromTemplate(commentsTemplate, postId));
            const data = await response.json();

            if (!response.ok) {
                listEl.innerHTML = `<div class="text-danger small">${escapeHtml(data.error || "Unable to load comments.")}</div>`;
                return;
            }

            const comments = data.results || [];

            if (comments.length === 0) {
                listEl.innerHTML = `<div class="text-muted small">No comments yet.</div>`;
                listEl.dataset.loaded = "true";
                return;
            }

            listEl.innerHTML = comments.map(function (comment) {
                return `
                    <div class="feed-comment">
                        <div class="feed-comment-user">${escapeHtml(comment.user.username)}</div>
                        <div class="feed-comment-text">${escapeHtml(comment.text)}</div>
                    </div>
                `;
            }).join("");

            listEl.dataset.loaded = "true";
        } catch (error) {
            listEl.innerHTML = `<div class="text-danger small">Unexpected error while loading comments.</div>`;
        }
    }

    async function submitComment(postId, form) {
        const textarea = form.querySelector("textarea");
        const text = textarea ? textarea.value.trim() : "";

        if (!text) {
            return;
        }

        try {
            const response = await fetch(buildUrlFromTemplate(commentsTemplate, postId), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams({ text }),
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Unable to post comment.");
                return;
            }

            const listEl = document.getElementById(`comments-list-${postId}`);
            const existingEmpty = listEl.querySelector(".text-muted.small");
            if (existingEmpty) {
                existingEmpty.remove();
            }

            listEl.insertAdjacentHTML("beforeend", `
                <div class="feed-comment">
                    <div class="feed-comment-user">${escapeHtml(data.user.username)}</div>
                    <div class="feed-comment-text">${escapeHtml(data.text)}</div>
                </div>
            `);

            listEl.dataset.loaded = "true";
            textarea.value = "";
        } catch (error) {
            alert("Unexpected error while posting comment.");
        }
    }

    async function setReaction(postId, reactionType) {
        try {
            const response = await fetch(buildUrlFromTemplate(reactTemplate, postId), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams({ reaction_type: reactionType }),
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Unable to set reaction.");
                return;
            }

            const postEl = document.getElementById(`post-${postId}`);
            const buttons = postEl.querySelectorAll(".feed-reaction-btn");

            buttons.forEach(function (button) {
                const type = button.dataset.reactionType;
                const count = data.counts && data.counts[type] ? data.counts[type] : 0;
                const labels = {
                    LIKE: "Like",
                    LOVE: "Love",
                    WOW: "Wow",
                };

                button.textContent = `${labels[type]} (${count})`;
                button.classList.toggle("active", data.my_reaction === type);
            });
        } catch (error) {
            alert("Unexpected error while setting reaction.");
        }
    }

    page.addEventListener("click", function (event) {
        const reactionButton = event.target.closest(".feed-reaction-btn");
        if (reactionButton) {
            const postId = reactionButton.dataset.postId;
            const reactionType = reactionButton.dataset.reactionType;
            setReaction(postId, reactionType);
            return;
        }

        const toggleButton = event.target.closest(".toggle-comments-btn");
        if (toggleButton) {
            const postId = toggleButton.dataset.postId;
            const wrap = document.getElementById(`comments-wrap-${postId}`);
            wrap.classList.toggle("open");

            if (wrap.classList.contains("open")) {
                loadComments(postId);
            }
        }
    });

    page.addEventListener("submit", function (event) {
        const form = event.target.closest(".feed-comment-form");
        if (!form) {
            return;
        }

        event.preventDefault();
        submitComment(form.dataset.postId, form);
    });

    loadMoreBtn.addEventListener("click", function () {
        loadFeed(false);
    });

    loadFeed(true);
});