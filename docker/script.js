let selectedAvatar = null;

const avatarList = document.getElementById('avatarList');
const output = document.getElementById('output');
const videoResult = document.getElementById('videoResult');
const selectedAvatarImage = document.getElementById('selectedAvatarImage');
const selectedAvatarModel = document.getElementById('selectedAvatarModel');
const healthPill = document.getElementById('healthPill');

const avatarImageInput = document.getElementById('avatarImageInput');
const avatarNameInput = document.getElementById('avatarNameInput');
const targetAudioInput = document.getElementById('targetAudioInput');
const ttsText = document.getElementById('ttsText');
const useTtsToggle = document.getElementById('useTtsToggle');
const useSourceVoiceToggle = document.getElementById('useSourceVoiceToggle');
const trainAudioInput = document.getElementById('trainAudioInput');
const epochInput = document.getElementById('epochInput');
const avatarImageLabel = document.getElementById('avatarImageLabel');
const cartoonizedAvatarImage = document.getElementById('cartoonizedAvatarImage');

const targetAudioLabel = document.getElementById('targetAudioLabel');
const trainAudioLabel = document.getElementById('trainAudioLabel');

const toBase64 = file => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result);
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

const toBase64Payload = file => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result.split(',')[1]);
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

function log(message) {
  output.textContent += `${message}\n`;
  output.scrollTop = output.scrollHeight;
}

window.appendOutput = log;

async function getLogOffset(position = 'latest') {
  try {
    const response = await fetch(`/api/logs?offset=${encodeURIComponent(position)}`);
    const data = await response.json();
    return data.offset || 0;
  } catch {
    return 0;
  }
}

function startLogPolling(offset) {
  let nextOffset = offset;
  let stopped = false;

  const poll = async () => {
    if (stopped) {
      return;
    }

    try {
      const response = await fetch(`/api/logs?offset=${nextOffset}`);
      const data = await response.json();
      nextOffset = data.offset || nextOffset;
      (data.entries || []).forEach(line => log(line));
    } catch (err) {
      console.warn('Failed to poll logs', err);
    }
  };

  const timer = setInterval(poll, 1000);
  poll();

  return async () => {
    clearInterval(timer);
    await poll();
    stopped = true;
  };
}

async function withLogPolling(operation) {
  const stopPolling = startLogPolling(await getLogOffset());
  try {
    return await operation();
  } finally {
    await stopPolling();
  }
}

function logResult(result, options = {}) {
  const includeLogs = options.includeLogs !== false;
  if (!result || typeof result !== 'object') {
    log(result);
    return;
  }

  if (includeLogs && Array.isArray(result.logs) && result.logs.length) {
    result.logs.forEach(line => log(line));
  }

  if (result.status === 'error') {
    log(result.message || 'Operation failed.');
    if (result.details) {
      log(result.details);
    }
    if (result.trace) {
      log(result.trace);
    }
    return;
  }

  if (result.message) {
    log(result.message);
  }
}

function showVideoResult(videoUrl) {
  if (!videoResult || !videoUrl) {
    return;
  }

  const href = videoUrl.startsWith('/') ? videoUrl : `/${videoUrl}`;
  videoResult.hidden = false;
  videoResult.innerHTML = '';

  const video = document.createElement('video');
  video.controls = true;
  video.src = href;
  video.preload = 'metadata';

  const link = document.createElement('a');
  link.href = href;
  link.download = href.split('/').pop() || 'cartoon-talker-output.mp4';
  link.textContent = link.download;

  videoResult.append(video, link);
}

async function api(method, ...args) {
  return window.pywebview.api[method](...args);
}

function syncFileLabel(input, label, placeholder) {
  if (!label) {
    return;
  }
  const file = input.files && input.files[0];
  label.textContent = file ? file.name : placeholder;
}

function renderSelectedAvatar(avatar) {
  selectedAvatar = avatar;
  selectedAvatarModel.textContent = avatar
    ? (avatar.model ? `Model: ${avatar.model}` : 'No model attached.')
    : 'No avatar selected.';
}

async function refreshAvatars() {
  avatarList.innerHTML = '';
  const avatars = await api('get_avatars');
  const selectedId = selectedAvatar ? selectedAvatar.id : null;

  if (!avatars.length) {
    avatarList.innerHTML = '<p class="muted">No avatars yet.</p>';
    renderSelectedAvatar(null);
    return;
  }

  avatars.forEach(avatar => {
    const item = document.createElement('div');
    item.className = 'avatar-item';
    item.dataset.avatarId = String(avatar.id);
    if (selectedAvatar && selectedAvatar.id === avatar.id) {
      item.classList.add('active');
    }

    item.innerHTML = `
      <img class="avatar-thumb" src="${avatar.image}" alt="${avatar.name}">
      <div>
        <strong>${avatar.name}</strong>
        <div class="muted">${avatar.model ? 'Voice model ready' : 'No voice model'}</div>
      </div>
    `;

    item.addEventListener('click', () => {
      document.querySelectorAll('.avatar-item').forEach(node => node.classList.remove('active'));
      item.classList.add('active');
      renderSelectedAvatar(avatar);
    });

    avatarList.appendChild(item);
  });

  const nextSelected = selectedId
    ? avatars.find(avatar => avatar.id === selectedId) || avatars[0]
    : avatars[0];
  renderSelectedAvatar(nextSelected);
  const activeItem = Array.from(avatarList.children).find(node => Number(node.dataset.avatarId) === nextSelected.id);
  if (activeItem) {
    activeItem.classList.add('active');
  } else {
    avatarList.firstElementChild?.classList.add('active');
  }
}

async function readFileAsDataUrl(input) {
  const file = input.files && input.files[0];
  if (!file) {
    throw new Error('Please choose a file first.');
  }
  return toBase64(file);
}

async function runHealthCheck() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    healthPill.textContent = data.status === 'ok' ? 'Ready' : 'Starting...';
  } catch {
    healthPill.textContent = 'Offline';
  }
}

document.getElementById('refreshBtn').addEventListener('click', refreshAvatars);

avatarImageInput.addEventListener('change', async () => {
  syncFileLabel(avatarImageInput, avatarImageLabel, 'Choose image');
  // Show the original preview immediately
  const file = avatarImageInput.files && avatarImageInput.files[0];
  if (file) {
    try {
      const dataUrl = await toBase64(file);
      selectedAvatarImage.src = dataUrl;
      // clear any previous cartoonized preview when a new file is selected
      if (cartoonizedAvatarImage) {
        cartoonizedAvatarImage.removeAttribute('src');
      }
    } catch (err) {
      console.error('Failed to read image for preview', err);
    }
  } else {
    selectedAvatarImage.removeAttribute('src');
    if (cartoonizedAvatarImage) cartoonizedAvatarImage.removeAttribute('src');
  }
});

targetAudioInput.addEventListener('change', () => {
  syncFileLabel(targetAudioInput, targetAudioLabel, 'Choose target audio');
});

trainAudioInput.addEventListener('change', () => {
  syncFileLabel(trainAudioInput, trainAudioLabel, 'Choose training audio');
});

document.getElementById('createAvatarBtn').addEventListener('click', async () => {
  const avatarName = avatarNameInput.value.trim();
  if (!avatarName) {
    alert('Avatar name is required.');
    return;
  }
  // Prefer the cartoonized image if available; otherwise use the uploaded file
  let image;
  const cartoonizedPath = avatarImageInput.dataset.cartoonized;
  if (cartoonizedPath) {
    try {
      const res = await fetch(cartoonizedPath);
      if (!res.ok) throw new Error('Failed to fetch cartoonized image');
      const blob = await res.blob();
      image = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch (err) {
      console.warn('Could not load cartoonized image, falling back to original', err);
      image = await readFileAsDataUrl(avatarImageInput);
    }
  } else {
    image = await readFileAsDataUrl(avatarImageInput);
  }

  await api('create_avatar', avatarName, image);
  avatarNameInput.value = '';
  avatarImageInput.value = '';
  syncFileLabel(avatarImageInput, avatarImageLabel, 'Choose image');
  await refreshAvatars();
  log('Avatar created.');
});

document.getElementById('cartoonizeBtn').addEventListener('click', async () => {
  try {
    const file = avatarImageInput.files && avatarImageInput.files[0];
    if (!file) {
      alert('Choose an image first.');
      return;
    }

    const dataUrl = await toBase64(file);
    const dims = await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve({ width: img.width, height: img.height });
      img.onerror = reject;
      img.src = dataUrl;
    });

    const result = await withLogPolling(() => api('cartoonize_avatar', dataUrl, dims.width, dims.height));
    logResult(result, { includeLogs: false });

    if (result && result.status === 'error') {
      return;
    }

    const resultPath = result && typeof result === 'object' ? result.image : result;
    avatarImageInput.dataset.cartoonized = resultPath;
    // server returns a path relative to the app root (e.g. /tmp/cartoonize_photo.png)
    let url = resultPath || '';
    if (url && !url.startsWith('/')) {
      url = '/' + url;
    }
    if (cartoonizedAvatarImage && url) {
      cartoonizedAvatarImage.src = url;
    }
  } catch (err) {
    log(err.message || String(err));
  }
});

document.getElementById('runBtn').addEventListener('click', async () => {
  if (!selectedAvatar) {
    alert('Select an avatar first.');
    return;
  }

  let audioPayload = null;
  if (useTtsToggle.checked) {
    const text = ttsText.value.trim();
    if (!text) {
      alert('Type some text for TTS.');
      return;
    }
    const ttsResult = await api('run_tts', text);
    if (ttsResult.status !== 'ok') {
      log(ttsResult.message || 'TTS failed.');
      if (ttsResult.details) {
        log(ttsResult.details);
      }
      return;
    }
    audioPayload = ttsResult.audio;
    log('TTS completed.');
  } else {
    const targetFile = targetAudioInput.files && targetAudioInput.files[0];
    if (!targetFile) {
      alert('Choose target audio or enable TTS.');
      return;
    }
    audioPayload = await toBase64Payload(targetFile);
  }

  const image = selectedAvatar.image;
  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
    img.src = image;
  });

  const modelPath = useSourceVoiceToggle.checked ? (selectedAvatar.model || '') : '';
  let result;
  try {
    result = await withLogPolling(() => api('run_cartoon_talker', image, audioPayload, modelPath, img.width, img.height));
  } catch (err) {
    log(err.message || String(err));
    return;
  }
  if (result && typeof result === 'object') {
    logResult(result, { includeLogs: false });
    if (result.video) {
      showVideoResult(result.video);
      log(`Output: ${result.video}`);
    }
  } else {
    log(result);
  }
});

document.getElementById('trainBtn').addEventListener('click', async () => {
  if (!selectedAvatar) {
    alert('Select an avatar first.');
    return;
  }

  const file = trainAudioInput.files && trainAudioInput.files[0];
  if (!file) {
    alert('Choose training audio.');
    return;
  }

  const payload = await toBase64Payload(file);
  const epoch = Number(epochInput.value || 1000);
  let result;
  try {
    result = await withLogPolling(() => api('voice_train', payload, epoch, selectedAvatar.name));
  } catch (err) {
    log(err.message || String(err));
    return;
  }

  if (result.status === 'ok') {
    logResult(result, { includeLogs: false });
    await api('save_model_to_database', result.path, selectedAvatar.name);
    await refreshAvatars();
  } else {
    logResult(result, { includeLogs: false });
  }
});

document.getElementById('renameBtn').addEventListener('click', async () => {
  if (!selectedAvatar) {
    return;
  }
  const nextName = prompt('New avatar name', selectedAvatar.name);
  if (!nextName || !nextName.trim()) {
    return;
  }
  await api('change_avatar_name', selectedAvatar.name, nextName.trim());
  await refreshAvatars();
});

document.getElementById('deleteBtn').addEventListener('click', async () => {
  if (!selectedAvatar) {
    return;
  }
  if (!confirm(`Delete ${selectedAvatar.name}?`)) {
    return;
  }
  await api('delete_avatar', selectedAvatar.name);
  selectedAvatar = null;
  renderSelectedAvatar(null);
  await refreshAvatars();
});

window.addEventListener('pywebviewready', async () => {
  await runHealthCheck();
  await refreshAvatars();
});

runHealthCheck();
syncFileLabel(avatarImageInput, avatarImageLabel, 'Choose image');
syncFileLabel(targetAudioInput, targetAudioLabel, 'Choose target audio');
syncFileLabel(trainAudioInput, trainAudioLabel, 'Choose training audio');
