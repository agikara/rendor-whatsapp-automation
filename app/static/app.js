document.addEventListener('DOMContentLoaded', () => {
    const userList = document.getElementById('user-list');
    const chatWelcome = document.getElementById('chat-welcome');
    const chatWindow = document.getElementById('chat-window');
    const chatHeader = document.getElementById('chat-with-user');
    const messageList = document.getElementById('message-list');
    const replyForm = document.getElementById('reply-form');
    const replyMessageInput = document.getElementById('reply-message');

    let activeUserId = null;

    // Fetch all users and populate the list
    async function fetchUsers() {
        try {
            const response = await fetch('/dashboard/users');
            if (!response.ok) {
                if (response.status === 401) {
                    alert('Authentication failed. Please check your credentials.');
                }
                throw new Error('Failed to fetch users');
            }
            const users = await response.json();
            userList.innerHTML = ''; // Clear loading message
            users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = user.whatsapp_id;
                li.dataset.userId = user.id;
                li.addEventListener('click', () => {
                    selectUser(user.id, user.whatsapp_id);
                });
                userList.appendChild(li);
            });
        } catch (error) {
            console.error(error);
            userList.innerHTML = '<li class="error">Failed to load users.</li>';
        }
    }

    // Handle user selection
    function selectUser(userId, whatsappId) {
        activeUserId = userId;
        chatWelcome.classList.add('hidden');
        chatWindow.classList.remove('hidden');

        // Highlight active user
        document.querySelectorAll('#user-list li').forEach(li => {
            li.classList.remove('active');
            if(li.dataset.userId == userId) {
                li.classList.add('active');
            }
        });

        chatHeader.textContent = `Chat with ${whatsappId}`;
        messageList.innerHTML = '<li>Loading messages...</li>';
        fetchMessages(userId);
    }

    // Fetch messages for a selected user
    async function fetchMessages(userId) {
        try {
            const response = await fetch(`/dashboard/users/${userId}/messages`);
            if (!response.ok) throw new Error('Failed to fetch messages');
            const messages = await response.json();
            renderMessages(messages);
        } catch (error) {
            console.error(error);
            messageList.innerHTML = '<li class="error">Failed to load messages.</li>';
        }
    }

    // Render messages in the chat window
    function renderMessages(messages) {
        messageList.innerHTML = '';
        messages.forEach(msg => {
            appendMessage(msg);
        });
        messageList.scrollTop = messageList.scrollHeight; // Scroll to bottom
    }

    // Append a single message to the chat window
    function appendMessage(msg) {
        const div = document.createElement('div');
        div.classList.add('message', msg.direction);
        div.textContent = msg.content;
        messageList.appendChild(div);
    }

    // Handle form submission to send a reply
    replyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!activeUserId) return;

        const text = replyMessageInput.value;
        if (!text.trim()) return;

        try {
            const response = await fetch(`/dashboard/users/${activeUserId}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const newMessage = await response.json();
            appendMessage(newMessage);
            messageList.scrollTop = messageList.scrollHeight;
            replyMessageInput.value = '';
        } catch (error) {
            console.error(error);
            alert('Failed to send message. Please try again.');
        }
    });

    // Initial fetch
    fetchUsers();
});
