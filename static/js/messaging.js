/**
 * Messaging System JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
	// Scroll to bottom of chat container
	const scrollChatToBottom = () => {
		const chatContainer = document.getElementById('chatContainer');
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	};

	// Initial scroll to bottom
	scrollChatToBottom();

	// Auto-resize textarea
	const messageTextarea = document.querySelector('.message-form textarea');
	if (messageTextarea) {
		messageTextarea.addEventListener('input', function () {
			this.style.height = 'auto';
			this.style.height = (this.scrollHeight) + 'px';
		});

		// Focus on textarea when page loads
		messageTextarea.focus();
	}

	// AJAX form submission for sending messages
	const messageForm = document.getElementById('messageForm');
	if (messageForm) {
		messageForm.addEventListener('submit', function (e) {
			e.preventDefault();

			const formData = new FormData(this);
			const content = formData.get('content').trim();

			if (!content) return;

			fetch(this.action, {
				method: 'POST',
				body: formData,
				headers: {
					'X-Requested-With': 'XMLHttpRequest',
					'X-CSRFToken': formData.get('csrfmiddlewaretoken')
				}
			})
				.then(response => response.json())
				.then(data => {
					if (data.success) {
						// Add message to chat
						const messageHTML = `
                        <div class="message-wrapper message-out">
                            <div class="message-bubble">
                                <div class="message-content">${data.message.content}</div>
                                <div class="message-info">
                                    <small class="text-muted">${data.message.timestamp}</small>
                                </div>
                            </div>
                        </div>
                    `;

						const chatContainer = document.getElementById('chatContainer');
						chatContainer.insertAdjacentHTML('beforeend', messageHTML);
						scrollChatToBottom();

						// Clear input
						messageTextarea.value = '';
						messageTextarea.style.height = 'auto';
					}
				})
				.catch(error => {
					console.error('Error sending message:', error);
				});
		});
	}

	// Search functionality for recipient list
	const recipientSearch = document.getElementById('recipientSearch');
	if (recipientSearch) {
		const recipientItems = document.querySelectorAll('.recipient-item');

		recipientSearch.addEventListener('input', function () {
			const searchTerm = this.value.toLowerCase();

			recipientItems.forEach(item => {
				const text = item.textContent.toLowerCase();
				if (text.includes(searchTerm)) {
					item.style.display = '';
				} else {
					item.style.display = 'none';
				}
			});
		});
	}

	// Mark messages as read via AJAX
	const markMessageRead = (messageId) => {
		fetch(`/messages/read/${messageId}/`, {
			method: 'POST',
			headers: {
				'X-Requested-With': 'XMLHttpRequest',
				'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
			}
		})
			.then(response => response.json())
			.catch(error => {
				console.error('Error marking message as read:', error);
			});
	};

	// Real-time messaging with WebSockets (if available)
	if (window.WebSocket && document.getElementById('chatContainer')) {
		const conversationId = document.querySelector('input[name="conversation_id"]').value;

		// This would be implemented with Django Channels in a full implementation
		console.log('WebSocket would connect to conversation:', conversationId);

		// Example of how the WebSocket handling would work:
		/*
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
			    
				const chatContainer = document.getElementById('chatContainer');
				chatContainer.insertAdjacentHTML('beforeend', messageHTML);
				scrollChatToBottom();
			    
				// Mark as read
				markMessageRead(data.message.id);
			}
		};
	    
		chatSocket.onclose = function(e) {
			console.error('Chat socket closed unexpectedly');
		};
		*/
	}
});