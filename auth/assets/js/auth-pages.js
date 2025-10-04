{{ ... }}
-    const host = window.location.hostname || ''
-    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === ''
-    // Production API on onrender currently expects legacy keys: name, mobile_number
-    if (!isLocal) {
-      fd.append('name', full_name)
-      fd.append('mobile_number', mobile)
-    }
-    const registerPath = isLocal ? '/auth/register' : '/register'
-    const resp = await backendFetch(registerPath, { method: 'POST', body: fd })
+    const registerPath = '/auth/register'
+    const resp = await backendFetch(registerPath, { method: 'POST', body: fd })
{{ ... }}
