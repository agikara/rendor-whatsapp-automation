document.addEventListener("DOMContentLoaded", () => {
    const FALLBACK_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='240' viewBox='0 0 400 240'%3E%3Crect fill='%23e5e7eb' width='400' height='240'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-size='20' font-family='Inter,Segoe UI,sans-serif'%3ENo preview%3C/text%3E%3C/svg%3E";

    const state = {
        users: [],
        filteredUsers: [],
        activeUserId: null,
        lastMessageId: null,
        pollHandle: null,
        baseTitle: document.title,
        lastRefreshed: null,
    };

    const elements = {
        userList: document.getElementById("user-list"),
        userSearch: document.getElementById("user-search"),
        refreshUsers: document.getElementById("refresh-users"),
        userListCount: document.getElementById("user-list-count"),
        chatWelcome: document.getElementById("chat-welcome"),
        chatWindow: document.getElementById("chat-window"),
        chatHeader: document.getElementById("chat-with-user"),
        chatSubtitle: document.getElementById("chat-subtitle"),
        chatRefresh: document.getElementById("chat-refresh"),
        messageList: document.getElementById("message-list"),
        replyForm: document.getElementById("reply-form"),
        replyMessageInput: document.getElementById("reply-message"),
        fileUpload: document.getElementById("file-upload"),
        notificationBanner: document.getElementById("dashboard-notification"),
        statsTotalUsers: document.getElementById("stats-total-users"),
        statsActiveChat: document.getElementById("stats-active-chat"),
    };

    const notificationSoundUrl = (elements.notificationBanner && elements.notificationBanner.dataset && elements.notificationBanner.dataset.soundUrl)
        ? elements.notificationBanner.dataset.soundUrl
        : "https://notificationsounds.com/storage/sounds/file-sounds-1152-pristine.mp3";
    const notificationAudio = new Audio(notificationSoundUrl);
    notificationAudio.preload = "auto";

    async function fetchUsers() {
        try {
            const response = await fetch("/dashboard/users");
            if (!response.ok) {
                throw new Error("Failed to fetch users");
            }
            state.users = await response.json();
            updateUserStats();
            applyUserFilter(elements.userSearch.value.trim());
        } catch (error) {
            console.error(error);
            elements.userList.innerHTML = '<li class="error">Failed to load users.</li>';
        }
    }

    function updateUserStats() {
        if (elements.statsTotalUsers) {
            elements.statsTotalUsers.textContent = state.users.length.toString();
        }
        if (elements.statsActiveChat) {
            const active = state.activeUserId
                ? state.users.find((user) => user.id === state.activeUserId)
                : null;
            elements.statsActiveChat.textContent = active ? active.whatsapp_id : "-";
        }
    }

    function applyUserFilter(filterValue) {
        const filter = filterValue.toLowerCase();
        state.filteredUsers = state.users.filter((user) =>
            !filter || user.whatsapp_id.toLowerCase().includes(filter)
        );
        renderUserList();
    }

    function renderUserList() {
        elements.userList.innerHTML = "";
        if (elements.userListCount) {
            elements.userListCount.textContent = state.filteredUsers.length.toString();
        }
        if (!state.filteredUsers.length) {
            elements.userList.innerHTML = '<li class="empty">No users found.</li>';
            return;
        }
        state.filteredUsers.forEach((user) => {
            const item = document.createElement("li");
            item.className = "user-list-item";
            item.dataset.userId = user.id;
            item.innerHTML = [
                '<div class="user-id">' + user.whatsapp_id + '</div>',
                '<div class="user-meta">#' + user.id + '</div>'
            ].join("");
            item.addEventListener("click", () => selectUser(user.id, user.whatsapp_id));
            if (state.activeUserId === user.id) {
                item.classList.add("active");
            }
            elements.userList.appendChild(item);
        });
    }

    function selectUser(userId, whatsappId) {
        state.activeUserId = userId;
        state.lastMessageId = null;
        state.lastRefreshed = null;
        updateUserStats();
        updateChatSubtitle("Loading conversation...");

        elements.chatWelcome.classList.add("hidden");
        elements.chatWindow.classList.remove("hidden");
        elements.chatHeader.textContent = "Chat with " + whatsappId;
        elements.messageList.innerHTML = '<li class="loading">Loading conversation...</li>';

        Array.prototype.forEach.call(document.querySelectorAll(".user-list-item"), (item) => {
            item.classList.toggle("active", item.dataset.userId === String(userId));
        });

        fetchMessages(userId, false);
    }

    async function fetchMessages(userId, notifyNew) {
        try {
            const response = await fetch("/dashboard/users/" + userId + "/messages");
            if (!response.ok) {
                throw new Error("Failed to fetch messages");
            }
            const messages = await response.json();
            renderMessages(messages, notifyNew);
            state.lastRefreshed = new Date();
            updateChatSubtitle("Updated " + state.lastRefreshed.toLocaleTimeString());
        } catch (error) {
            console.error(error);
            elements.messageList.innerHTML = '<li class="error">Failed to load messages.</li>';
            updateChatSubtitle("Failed to refresh messages");
        }
    }

    function renderMessages(messages, notifyNew) {
        elements.messageList.innerHTML = "";
        messages.forEach((message) => {
            const node = createMessageNode(message);
            elements.messageList.appendChild(node);
        });
        elements.messageList.scrollTop = elements.messageList.scrollHeight;

        if (!messages.length) {
            state.lastMessageId = null;
            return;
        }

        const latest = messages[messages.length - 1];
        if (notifyNew && state.lastMessageId && latest.id !== state.lastMessageId && latest.direction === "incoming") {
            triggerNotifications(latest);
        }
        state.lastMessageId = latest.id;
    }

    function createMessageNode(message) {
        const row = document.createElement("li");
        row.classList.add("message-row", message.direction);
        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

        const body = document.createElement("div");
        body.classList.add("message-body");

        if (message.message_type === "image") {
            const figure = document.createElement("figure");
            figure.classList.add("image-wrapper");
            const img = document.createElement("img");
            img.classList.add("chat-image");
            img.src = (message.content && message.content.indexOf("/static/uploads/") === 0)
                ? message.content
                : FALLBACK_IMAGE;
            img.alt = "Image message";
            figure.appendChild(img);
            body.appendChild(figure);
        } else if (message.message_type === "document") {
            const link = document.createElement("a");
            link.href = message.content;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "Open document";
            body.appendChild(link);
        } else {
            body.textContent = message.content || "";
        }

        bubble.appendChild(body);

        const meta = document.createElement("div");
        meta.classList.add("message-meta");
        const timestamp = document.createElement("span");
        timestamp.classList.add("message-timestamp");
        timestamp.textContent = formatTimestamp(message.timestamp);
        const typeBadge = document.createElement("span");
        typeBadge.classList.add("message-type");
        typeBadge.textContent = formatMessageType(message.message_type);
        meta.appendChild(timestamp);
        meta.appendChild(typeBadge);

        bubble.appendChild(meta);
        row.appendChild(bubble);
        return row;
    }

    function formatTimestamp(isoString) {
        if (!isoString) {
            return "";
        }
        const date = new Date(isoString);
        return date.toLocaleString();
    }

    function formatMessageType(type) {
        switch (type) {
            case "image":
                return "Image";
            case "document":
                return "Document";
            case "interactive":
                return "Interactive";
            default:
                return "Text";
        }
    }

    function triggerNotifications(message) {
        showDashboardNotification(
            message.message_type === "image"
                ? "New image received"
                : "New message received"
        );
        try {
            notificationAudio.currentTime = 0;
            notificationAudio.play();
        } catch (error) {
            console.warn("Unable to play notification sound", error);
        }
        if (navigator.vibrate) {
            navigator.vibrate([120, 60, 120]);
        }
        if (document.hidden) {
            document.title = "[New message]";
        }
        if (window.Notification && Notification.permission === "granted") {
            new Notification("WhatsApp Dashboard", {
                body: message.message_type === "image" ? "New image received" : message.content,
            });
        }
    }

    function showDashboardNotification(text) {
        if (!elements.notificationBanner) {
            return;
        }
        elements.notificationBanner.textContent = text;
        elements.notificationBanner.classList.add("visible");
        setTimeout(() => {
            elements.notificationBanner.classList.remove("visible");
        }, 5000);
    }

    function startPolling() {
        if (state.pollHandle) {
            clearInterval(state.pollHandle);
        }
        state.pollHandle = setInterval(() => {
            if (state.activeUserId) {
                fetchMessages(state.activeUserId, true);
            }
        }, 5000);
    }

    function resetTitle() {
        document.title = state.baseTitle;
    }

    function updateChatSubtitle(text) {
        if (elements.chatSubtitle) {
            elements.chatSubtitle.textContent = text;
        }
    }

    elements.replyForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!state.activeUserId) {
            return;
        }

        const text = elements.replyMessageInput.value;
        const file = elements.fileUpload.files[0];

        if (file) {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("caption", text || "");
            try {
                const response = await fetch("/dashboard/users/" + state.activeUserId + "/files", {
                    method: "POST",
                    body: formData,
                });
                if (!response.ok) {
                    throw new Error("Failed to send file");
                }
                elements.replyMessageInput.value = "";
                elements.fileUpload.value = "";
                fetchMessages(state.activeUserId, false);
            } catch (error) {
                console.error(error);
                alert("Failed to send file. Please try again.");
            }
            return;
        }

        if (!text.trim()) {
            return;
        }
        try {
            const response = await fetch("/dashboard/users/" + state.activeUserId + "/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text }),
            });
            if (!response.ok) {
                throw new Error("Failed to send message");
            }
            elements.replyMessageInput.value = "";
            fetchMessages(state.activeUserId, false);
        } catch (error) {
            console.error(error);
            alert("Failed to send message. Please try again.");
        }
    });

    elements.userSearch.addEventListener("input", (event) => {
        applyUserFilter(event.target.value);
    });

    elements.refreshUsers.addEventListener("click", () => {
        fetchUsers();
    });

    if (elements.chatRefresh) {
        elements.chatRefresh.addEventListener("click", () => {
            if (state.activeUserId) {
                updateChatSubtitle("Refreshing conversation...");
                fetchMessages(state.activeUserId, false);
            }
        });
    }

    window.addEventListener("focus", resetTitle);

    if (window.Notification && Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    fetchUsers();
    startPolling();
});
