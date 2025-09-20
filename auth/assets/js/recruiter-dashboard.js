// Recruiter Dashboard - simplified bootstrapping using assets/js/api-services.js
import { auth, jobService, applicationService, notificationService, realtimeService, analyticsService } from './api-services.js';

// Keep your existing class implementation; this is a thin loader
// For now, just ensure auth redirect to login subdomain if not authenticated
(async function init() {
  try {
    const user = await auth.getCurrentUser();
    if (!user) {
      window.location.href = 'https://login.skreenit.com/';
      return;
    }
  } catch (e) {
    window.location.href = 'https://login.skreenit.com/';
    return;
  }
})();
