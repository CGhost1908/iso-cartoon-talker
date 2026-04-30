(function () {
  if (window.pywebview && window.pywebview.api) {
    return;
  }

  const postJson = async (method, args) => {
    const response = await fetch(`/api/${method}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ args })
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      const details = [data.error || `Request failed: ${method}`, data.trace]
        .filter(Boolean)
        .join('\n');
      throw new Error(details);
    }

    return data.result;
  };

  const api = new Proxy({}, {
    get(_, method) {
      return (...args) => postJson(method, args);
    }
  });

  window.pywebview = { api };

  const dispatchReady = () => window.dispatchEvent(new Event('pywebviewready'));

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', dispatchReady, { once: true });
  } else {
    setTimeout(dispatchReady, 0);
  }
})();
