/**
 * Conversation JavaScript
 * Handles message sending and real-time updates for conversations
 */

document.addEventListener('DOMContentLoaded', function () {
	// Get message elements
	const messageForm = document.getElementById('messageForm');
	const chatContainer = document.getElementById('chatContainer');
	const messageTextarea = document.querySelector('.message-form textarea');

	if (!messageForm || !chatContainer) return;

	// Scroll to bottom of chat container
	function scrollToBottom() {
		chatContainer.scrollTop = chatContainer.scrollHeight;
	}

	// Initial scroll to bottom
	scrollToBottom();

	// Auto-resize textarea
	if (messageTextarea) {
		messageTextarea.addEventListener('input', function () {
			this.style.height = 'auto';
			this.style.height = (this.scrollHeight) + 'px';
		});

		// Focus on textarea when page loads
		messageTextarea.focus();
	}

	// Handle form submission with AJAX
	messageForm.addEventListener('submit', function (e) {
		e.preventDefault();

		const formData = new FormData(this);
		const content = formData.get('content').trim();

		if (!content) return;

		// Show sending indicator
		const tempId = 'msg-' + Date.now();
		const timestamp = new Date().toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: 'numeric',
			minute: 'numeric',
			hour12: true
		});

		const messageHTML = `
            <div class="message-wrapper message-out" id="${tempId}">
                <div class="message-bubble">
                    <div class="message-content">${content}</div>
                    <div class="message-info">
                        <small class="text-muted">${timestamp}</small>
                        <small class="ms-2 text-secondary"><i class="fas fa-clock"></i></small>
                    </div>
                </div>
            </div>
        `;

		chatContainer.insertAdjacentHTML('beforeend', messageHTML);
		scrollToBottom();

		// Reset textarea
		messageTextarea.value = '';
		messageTextarea.style.height = 'auto';

		// Send AJAX request
		// Get CSRF token
		const csrfToken = document.querySelector('#csrf-form [name=csrfmiddlewaretoken]').value;

		fetch(messageForm.action, {
			method: 'POST',
			body: formData,
			headers: {
				'X-Requested-With': 'XMLHttpRequest',
				'X-CSRFToken': csrfToken
			}
		})
			.then(response => {
				if (!response.ok) {
					throw new Error('Network response was not ok');
				}
				return response.json();
			})
			.then(data => {
				if (data.success) {
					// Replace temporary message with confirmed message
					const tempMessage = document.getElementById(tempId);
					if (tempMessage) {
						const confirmedHTML = `
                        <div class="message-wrapper message-out">
                            <div class="message-bubble">
                                <div class="message-content">${data.message.content}</div>
                                <div class="message-info">
                                    <small class="text-muted">${data.message.timestamp}</small>
                                </div>
                            </div>
                        </div>
                    `;
						tempMessage.outerHTML = confirmedHTML;
					}
				} else {
					// Show error for the message
					const tempMessage = document.getElementById(tempId);
					if (tempMessage) {
						const messageInfo = tempMessage.querySelector('.message-info');
						if (messageInfo) {
							messageInfo.innerHTML = `
                            <small class="text-danger">Error sending message</small>
                            <button class="btn btn-sm text-danger retry-btn" data-content="${content}">
                                <i class="fas fa-redo-alt"></i>
                            </button>
                        `;
						}
					}
				}
			})
			.catch(error => {
				console.error('Error sending message:', error);

				// Show error for the message
				const tempMessage = document.getElementById(tempId);
				if (tempMessage) {
					const messageInfo = tempMessage.querySelector('.message-info');
					if (messageInfo) {
						messageInfo.innerHTML = `
                        <small class="text-danger">Error sending message</small>
                        <button class="btn btn-sm text-danger retry-btn" data-content="${content}">
                            <i class="fas fa-redo-alt"></i>
                        </button>
                    `;
					}
				}
			});
	});

	// Handle retry button clicks
	chatContainer.addEventListener('click', function (e) {
		const retryBtn = e.target.closest('.retry-btn');
		if (retryBtn) {
			const content = retryBtn.dataset.content;
			if (content) {
				messageTextarea.value = content;
				messageForm.dispatchEvent(new Event('submit'));

				// Remove the failed message
				const messageWrapper = retryBtn.closest('.message-wrapper');
				if (messageWrapper) {
					messageWrapper.remove();
				}
			}
		}
	});

	// Real-time updates with WebSockets (commented out for now)
	// This would be implemented with Django Channels in a full implementation
	/*
	const conversationId = document.querySelector('input[name="conversation_id"]').value;
    
	const chatSocket = new WebSocket(
		'ws://' + window.location.host + '/ws/chat/' + conversationId + '/'
	);
    
	chatSocket.onmessage = function(e) {
		const data = JSON.parse(e.data);
	    
		if (data.message) {
			// Add received message to chat
			const messageHTML = `
				<div class="message-wrapper message-in">
					<div class="message-bubble">
						<div class="message-content">${data.message.content}</div>
						<div class="message-info">
							<small class="text-muted">${data.message.timestamp}</small>
						</div>
					</div>
				</div>
			`;
		    
			chatContainer.insertAdjacentHTML('beforeend', messageHTML);
			scrollToBottom();
		    
			// Mark as read
			fetch('/messages/read/' + data.message.id + '/', {
				method: 'POST',
				headers: {
					'X-Requested-With': 'XMLHttpRequest',
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
				}
			});
		}
	};
    
	chatSocket.onclose = function(e) {
		console.error('Chat socket closed unexpectedly');
	};
	*/

	// For demonstration purposes, simulate receiving a message every 30 seconds
	// This would be replaced by WebSockets in production
	/*
	setInterval(function() {
		// Simulate random incoming messages for demo purposes
		const messages = [
			"How are you feeling today?",
			"Have you been taking your medication as prescribed?",
			"Your test results look good.",
			"Would you like to schedule a follow-up appointment?",
			"Please let me know if you have any questions about your treatment."
		];
	    
		const randomMessage = messages[Math.floor(Math.random() * messages.length)];
		const timestamp = new Date().toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: 'numeric',
			minute: 'numeric',
			hour12: true
		});
	    
		const messageHTML = `
			<div class="message-wrapper message-in">
				<div class="message-bubble">
					<div class="message-content">${randomMessage}</div>
					<div class="message-info">
						<small class="text-muted">${timestamp}</small>
					</div>
				</div>
			</div>
		`;
	    
		chatContainer.insertAdjacentHTML('beforeend', messageHTML);
		scrollToBottom();
	}, 30000);
	*/
});