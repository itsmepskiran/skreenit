// Recruiter Dashboard - simplified bootstrapping using assets/js/api-services.js
import { auth } from './api-services.js';

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
