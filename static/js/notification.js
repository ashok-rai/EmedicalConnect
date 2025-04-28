/**
 * Notifications JavaScript
 * Handles loading and displaying notifications in the header dropdown
 */

document.addEventListener('DOMContentLoaded', function () {
	// Get notification elements
	const notificationsDropdown = document.getElementById('notifications-dropdown');
	const notificationCount = document.getElementById('notification-count');
	const notificationsToggle = document.getElementById('notificationsDropdown');

	if (!notificationsDropdown || !notificationsToggle) return;

	// Function to load notifications
	function loadNotifications() {
		fetch('/messages/api/notifications/')
			.then(response => response.json())
			.then(data => {
				// Update notification count
				const unreadCount = data.unread_count || 0;
				if (unreadCount > 0) {
					notificationCount.textContent = unreadCount;
					notificationCount.classList.remove('d-none');
				} else {
					notificationCount.classList.add('d-none');
				}

				// Clear existing notifications except the "See all" link
				const seeAllLink = notificationsDropdown.querySelector('a[href*="notification_list"]');
				notificationsDropdown.innerHTML = '';

				if (seeAllLink) {
					const li = document.createElement('li');
					li.appendChild(seeAllLink);
					notificationsDropdown.appendChild(li);
				}

				// Add notifications to dropdown
				if (data.notifications && data.notifications.length > 0) {
					// Add divider if "See all" link exists
					if (seeAllLink) {
						const divider = document.createElement('li');
						divider.innerHTML = '<hr class="dropdown-divider">';
						notificationsDropdown.insertBefore(divider, notificationsDropdown.firstChild);
					}

					// Add notifications
					data.notifications.forEach(notification => {
						const li = document.createElement('li');
						let iconClass = 'fas fa-bell';

						switch (notification.notification_type) {
							case 'message':
								iconClass = 'fas fa-envelope';
								break;
							case 'appointment':
								iconClass = 'fas fa-calendar-check';
								break;
							case 'prescription':
								iconClass = 'fas fa-prescription';
								break;
							case 'medical_record':
								iconClass = 'fas fa-file-medical';
								break;
						}

						li.innerHTML = `
                            <a class="dropdown-item notification-item ${notification.is_read ? '' : 'unread'}" href="${notification.related_url || '#'}">
                                <div class="d-flex align-items-center">
                                    <div class="flex-shrink-0 me-2">
                                        <i class="${iconClass} ${notification.is_read ? 'text-muted' : 'text-primary'}"></i>
                                    </div>
                                    <div class="flex-grow-1 ms-2">
                                        <p class="mb-0 small fw-${notification.is_read ? 'normal' : 'bold'}">${notification.title}</p>
                                        <small class="text-muted">${notification.time_ago}</small>
                                    </div>
                                </div>
                            </a>
                        `;
						notificationsDropdown.insertBefore(li, notificationsDropdown.firstChild);
					});
				} else {
					// No notifications
					const li = document.createElement('li');
					li.innerHTML = `
                        <div class="dropdown-item text-center p-3">
                            <i class="fas fa-bell-slash text-muted mb-2"></i>
                            <p class="mb-0 small">No new notifications</p>
                        </div>
                    `;
					notificationsDropdown.insertBefore(li, notificationsDropdown.firstChild);
				}
			})
			.catch(error => {
				console.error('Error loading notifications:', error);
			});
	}

	// Load notifications when dropdown is shown
	notificationsToggle.addEventListener('show.bs.dropdown', loadNotifications);

	// Mark notifications as read when clicking on them
	notificationsDropdown.addEventListener('click', function (e) {
		const notificationItem = e.target.closest('.notification-item.unread');
		if (notificationItem) {
			// Make AJAX request to mark as read
			const notificationId = notificationItem.dataset.id;
			if (notificationId) {
				fetch(`/messages/api/notifications/${notificationId}/read/`, {
					method: 'POST',
					headers: {
						'X-Requested-With': 'XMLHttpRequest',
						'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
					}
				})
					.catch(error => {
						console.error('Error marking notification as read:', error);
					});
			}
		}
	});
});