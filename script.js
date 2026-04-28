
let choosenAvatar, currentAvatarModel;

const useSourceVoiceCheckbox = document.querySelector('#use-source-voice-checkbox');

const progressPopup = document.querySelector('.progress-popup');
const overlay = document.querySelector('.overlay');
const closeTerminalButton = document.querySelector('.close-terminal-button');

const avatarsDiv = document.querySelector('.other-avatars');
const currentAvatar = document.querySelector('.current-avatar-photo');
const currentAvatarName = document.querySelector('.current-avatar-name');

const audioTtsCheckbox = document.getElementById('auido-tts-checkbox');

function refreshAvatars(){
    window.pywebview.api.get_avatars().then(avatars => {
        avatarsDiv.innerHTML = '<img class="mini-create-avatar" src="src/add-avatar.png" alt="Kullanıcı Resmi" width="100" height="100" onclick="openCreateAvatar()">';
        avatars.forEach(avatar => {
            const createMiniAvatar = document.createElement('img');
            createMiniAvatar.classList.add('mini-avatar-photo'); 
            createMiniAvatar.src = avatar['image']; 
            createMiniAvatar.setAttribute('avatar-name', avatar['name']);
            createMiniAvatar.setAttribute('voice-model', avatar['model'] || '');
            createMiniAvatar.onclick = function() {
                changeAvatar(this);
            };
            createMiniAvatar.width = '100';
            createMiniAvatar.height = '100';
            avatarsDiv.insertBefore(createMiniAvatar, avatarsDiv.firstChild);
        });
        const firstAvatarImg = avatarsDiv.querySelector('.mini-avatar-photo');
        if(firstAvatarImg){
            choosenAvatar = firstAvatarImg.getAttribute('avatar-name');
            currentAvatarName.textContent = firstAvatarImg.getAttribute('avatar-name');
            currentAvatar.src = firstAvatarImg.getAttribute('src');
            currentAvatar.setAttribute('voice-model', firstAvatarImg.getAttribute('voice-model'));
            prepareAiSection();
        }
    });
}


function prepareAiSection(){
    currentAvatarModel= currentAvatar.getAttribute('voice-model');
    if(currentAvatarModel){
        document.querySelector('.source-voice-name').textContent = 'Ses modeli mevcut.';
        document.querySelector('.source-voice-name').parentElement.classList.remove('disabled-voice-label');
    }else{
        document.querySelector('.source-voice-name').textContent = 'Ses modeli yok.';
        document.querySelector('.source-voice-name').onclick = function(){
            openEditMenu(document.querySelector(`img[avatar-name="${choosenAvatar}"]`));
        }
        document.querySelector('.source-voice-name').parentElement.classList.add('disabled-voice-label');
    }
}

 
window.addEventListener('pywebviewready', function() {
    refreshAvatars();
});


function changeAvatar(avatarElement){
    choosenAvatar = avatarElement.getAttribute('avatar-name');

    avatarsDiv.insertBefore(avatarElement, avatarsDiv.firstChild);
    currentAvatarName.textContent = avatarElement.getAttribute('avatar-name');
    currentAvatar.src = avatarElement.getAttribute('src');
    currentAvatar.setAttribute('voice-model', avatarElement.getAttribute('voice-model'));

    useSourceVoiceCheckbox.checked = false;
    useSourceVoiceCheckbox.parentElement.style.backgroundColor = '';

    prepareAiSection();
}



const createAvatarPhoto = document.querySelector('.create-avatar-photo');

function updateCreateAvatarPhoto(){
    const input = document.getElementById('create-avatar-photo-input');
    const file = input.files[0];
    if(file){
        const reader = new FileReader();
        reader.onload = function(e) {
            createAvatarPhoto.src = e.target.result;
            document.querySelector('.undo-cartoonize').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

function cartoonizeAvatar() {
    const input = document.getElementById('create-avatar-photo-input');
    const file = input.files[0];

    if(!file){
        alert("❌ Lütfen bir avatar fotoğrafı seçin.");
        return;
    }

    document.querySelector('.progress-popup').style.display = 'flex';
    document.querySelector('.overlay').style.display = 'flex';

    const reader = new FileReader();
    reader.onload = function(e) {
        const base64Image = e.target.result;

        const img = new Image();
        img.onload = function() {
            const width = img.width;
            const height = img.height;

            try{
                pywebview.api.cartoonize_avatar(
                    base64Image,
                    width,
                    height
                ).then(result => {
                    createAvatarPhoto.src = result + '?t=' + new Date().getTime();
                    document.querySelector('.undo-cartoonize').style.display = 'flex';
                    document.querySelector('.overlay').style.display = 'none';
                    document.querySelector('.progress-popup').style.display = 'none';
                });
            }catch(error){
                console.error("Cartoonize error:", error);
                document.querySelector('.overlay').style.display = 'none';
                document.querySelector('.progress-popup').style.display = 'none';
                alert("❌ Cartoonize işlemi başarısız oldu. Lütfen tekrar deneyin.");
            }
        };
        img.src = base64Image;
    };
    reader.readAsDataURL(file);
}

function createAvatar(){
    const avatarName = document.getElementById('create-avatar-name-input').value;
    if(!avatarName){
        alert("❌ Lütfen avatar ismini girin.");
        return;
    }

    let nameIsAvailable = true;
    document.querySelectorAll('.mini-avatar-photo').forEach(avatar => {
        console.log(avatarName === avatar.getAttribute('avatar-name'))
        if(avatarName === avatar.getAttribute('avatar-name')){
            nameIsAvailable = false;
            return;
        }
    });

    if(!nameIsAvailable){
        alert("❌ Bu avatar ismi kullaniliyor.");
        return;
    }

    const createAvatarPhoto = document.querySelector('.create-avatar-photo');

    const avatarPhoto = createAvatarPhoto.src;
    if(!avatarPhoto || avatarPhoto.includes('/src/null-avatar.jpg')){
        alert("❌ Lütfen bir avatar fotoğrafı seçin.");
        return;
    }

    async function getImageBase64FromImg(imgElement) {
        const response = await fetch(imgElement.src);
        const blob = await response.blob();

        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    getImageBase64FromImg(createAvatarPhoto).then(base64Image => {
        pywebview.api.create_avatar(avatarName, base64Image).then(() => {
            createAvatarPhoto.src = 'src/null-avatar.jpg';
            refreshAvatars();
            goToHome();
        });
    });
}

function convertAudioToBase64(){
    const input = document.getElementById('create-avatar-audio-input');
    if (input.files.length === 0) {
        alert('Lütfen bir ses dosyası seçin!');
        return;
    }

    const file = input.files[0];
    const reader = new FileReader();

    reader.onload = function(e) {
        const base64Audio = e.target.result;
        console.log('Base64 audio:', base64Audio);

        try {
            const result = window.pywebview.api.get_voice_embedding(base64Audio);
            console.log('Voice embedding:', result);
        } catch (e) {
            console.error('Error calling get_voice_embedding:', e);
        }
    };

    reader.readAsDataURL(file); 
}


function getBase64ImageResolution(base64Image) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = function() {
            resolve({
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        };
        img.onerror = reject;
        img.src = base64Image;
    });
}

async function run(){
    document.getElementById('output').innerText = "";
    closeTerminalButton.style.display = 'none';

    const image = currentAvatar.src;
    const targetVoiceFile = document.getElementById('target-voice').files[0];

    if(!image){
        document.getElementById('output').innerText = "❌ Lütfen bir avatar seçin.";
        return;
    }
    
    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = error => reject(error);
            reader.readAsDataURL(file);
        });
    }

    let targetVoiceBase64 = null;

    if(audioTtsCheckbox.checked){
        const ttsText = document.querySelector('.tts-input').value;
        if(!ttsText || ttsText.trim().length < 1){
            document.getElementById('output').innerText = "❌ Lütfen TTS için bir metin girin.";
            return;
        }else{
            document.querySelector('.start-btn').disabled = true;
            document.getElementById('output').innerText = "⏳ TTS işlemi başlatıldı.";
            progressPopup.style.display = 'flex';
            overlay.style.display = 'flex';
            document.querySelector('.start-btn').disabled = true;
            await window.pywebview.api.run_tts(ttsText).then(result => {
                if(result.status === 'ok'){
                    document.getElementById('output').innerText = "✅ TTS işlemi başarılı.";
                    targetVoiceBase64 = result.audio;                    
                }else{
                    document.getElementById('output').innerText = "❌ TTS işlemi başarısız oldu.";
                    document.querySelector('.start-btn').disabled = false;
                    return;
                }
            });
        }
    }else{
        if(!targetVoiceFile){
            document.getElementById('output').innerText = "❌ Lütfen ses dosyalarını seçin.";
            return;
        }else{
            targetVoiceBase64 = await fileToBase64(targetVoiceFile);

            overlay.style.display = 'flex';
            progressPopup.style.display = 'flex';
            document.querySelector('.start-btn').disabled = true;
        }
    }

    let width, height;
    
    getBase64ImageResolution(image).then(size => {
        width = size.width;
        height = size.height;
    });

    const useSourceVoice = document.getElementById('use-source-voice-checkbox').checked;
    let sourceVoiceModel = null;
    if(useSourceVoice){
        sourceVoiceModel = document.querySelector('.current-avatar-photo').getAttribute('voice-model');
    }

    document.getElementById('output').innerText = "⏳ İşlem başlatılıyor...";

    try {
        const result = await window.pywebview.api.run_cartoon_talker(
            image,
            targetVoiceBase64,
            sourceVoiceModel,
            width,
            height
        );

        document.getElementById('output').innerText = result;
        document.querySelector('.start-btn').disabled = false;
        closeTerminalButton.style.display = 'block';
    } catch (error) {
        document.querySelector('.start-btn').disabled = false;
        closeTerminalButton.style.display = 'block';
    }
}


async function sendFile() {
    const input = document.getElementById('create-avatar-audio-input');
    if (!input.files.length) {
        alert('Dosya seç!');
        return;
    }
    
    const file = input.files[0];
    const reader = new FileReader();

    reader.onload = async function(e) {
        const base64 = e.target.result;
        const response = await window.pywebview.api.processBase64Audio(base64).then(result => {
            window.pywebview.api.run_tts(result);
        });
        alert(response);
    }

    reader.readAsDataURL(file);
}

const createAvatarSection = document.querySelector('.create-avatar-section');
const runAiSection = document.querySelector('.run-ai-section');

function goToHome(){
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    runAiSection.style.display = 'flex';
}

function openCreateAvatar(){
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    createAvatarSection.style.display = 'flex';
}

// const sourceVoiceInput = document.getElementById('source-voice');
const targetVoiceInput = document.getElementById('target-voice');

// sourceVoiceInput.addEventListener('change', function(){
//     if(sourceVoiceInput.value){
//         const parts = sourceVoiceInput.value.split(`\\`);
//         document.querySelector('.source-voice-name').textContent = parts[parts.length - 1];
//         sourceVoiceInput.parentElement.style.backgroundColor = 'rgb(143, 195, 143)';
//     }else{
//         document.querySelector('.source-voice-name').textContent = 'Ses dosyası yok';
//         sourceVoiceInput.parentElement.style.backgroundColor = '';
//     }
// });

useSourceVoiceCheckbox.addEventListener('change', function(){
    useSourceVoiceCheckbox.parentElement.style.backgroundColor = useSourceVoiceCheckbox.checked ? 'rgb(143, 195, 143)' : '';
});

targetVoiceInput.addEventListener('change', function(){
    if(targetVoiceInput.value){
        const parts = targetVoiceInput.value.split(`\\`);
        document.querySelector('.target-voice-name').textContent = parts[parts.length - 1];
        targetVoiceInput.parentElement.style.backgroundColor = 'rgb(143, 195, 143)';
    }else{
        document.querySelector('.target-voice-name').textContent = 'Ses dosyası yok';
        targetVoiceInput.parentElement.style.backgroundColor = '';
    }
});


let lastRightClick;
const menu = document.querySelector('.context-menu');

document.addEventListener('contextmenu', function(event) {
    if(event.target.classList.contains('mini-avatar-photo')) {
        event.preventDefault();
        lastRightClick = event.target;

        if(menu.classList.contains('hidden')){
            const menuHeight = menu.offsetHeight;
            menu.style.top = `${event.pageY - menuHeight}px`;
            menu.classList.remove('hidden');
        }else{
            menu.classList.add('hidden');
            setTimeout(() => {
                const menuHeight = menu.offsetHeight;
                menu.style.top = `${event.pageY - menuHeight}px`;
                menu.classList.remove('hidden');
            }, 300);
        }
            
    } else {
        menu.classList.add('hidden');
    }
});

document.addEventListener('click', function() {
    menu.classList.add('hidden');
});

const editSection = document.querySelector('.edit-section');

function openEditMenu(avatarElement){
    if(avatarElement){
        lastRightClick = avatarElement;
    }

    if(!lastRightClick) return;

    const avatarName = lastRightClick.getAttribute('avatar-name');
    const avatarImage = lastRightClick.getAttribute('src');
    const avatarModel = lastRightClick.getAttribute('voice-model');

    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    editSection.style.display = 'flex';

    editSection.querySelector('.title').textContent = avatarName;
    editSection.querySelector('#edit-avatar-name-input').value = avatarName;
    editSection.querySelector('.edit-avatar-photo').src = avatarImage;

    if(avatarModel){
        editSection.querySelector('.edit-avatar-model-available').textContent = "Ses modeli mevcut.";
        editSection.querySelector('.edit-avatar-model').style.display = 'block';
        editSection.querySelector('.edit-avatar-model').textContent = avatarModel;
    }else{
        editSection.querySelector('.edit-avatar-model-available').textContent = "Ses modeli mevcut değil.";
        editSection.querySelector('.edit-avatar-model').style.display = 'none';
        editSection.querySelector('.edit-avatar-model').textContent = '';
    }
}

const trainVoiceInput = document.querySelector('#train-voice');
trainVoiceInput.addEventListener('change', function(){
    if(trainVoiceInput.value){
        const parts = trainVoiceInput.value.split(`\\`);
        document.querySelector('.train-voice-name').textContent = parts[parts.length - 1];
        trainVoiceInput.parentElement.style.backgroundColor = 'rgb(143, 195, 143)';
    }else{
        document.querySelector('.train-voice-name').textContent = '';
        trainVoiceInput.parentElement.style.backgroundColor = '';
    }
});

const startVoiceTrainButton = document.querySelector('.start-voice-train');

const epochsRange = document.querySelector('.epochs input[type="range"]');
const epochsNumber = document.querySelector('.epochs input[type="number"]');

epochsRange.addEventListener('change', function(){
    epochsNumber.value = epochsRange.value;
});

epochsNumber.addEventListener('change', function(){
    epochsRange.value = epochsNumber.value;
});

trainVoiceInput.addEventListener('change', function(){
    if(trainVoiceInput.value.length >= 1){
        startVoiceTrainButton.disabled = false;
    }else{
        startVoiceTrainButton.disabled = true;
    }
});

function closeEditSection(){
    epochsNumber.value = '100';
    trainVoiceInput.value = '';
    document.querySelector('.train-voice-name').textContent = '';
    trainVoiceInput.parentElement.style.backgroundColor = '';
    startVoiceTrainButton.disabled = true;
    refreshAvatars()
    goToHome();
}

let lastModelPath = null;

function startVoiceTrain(){
    const avatarName = editSection.querySelector('.title').textContent;

    // progressText.textContent = 'Epochs confige yazılıyor.';
    progressPopup.style.display = 'flex';
    overlay.style.display = 'flex';

    const epoch = epochsNumber.value;

    // progressText.textContent = 'Ses dosyası base64 formatına çeviriliyor.';
    const file = trainVoiceInput.files[0];
    if(!file) return;

    const reader = new FileReader();
    reader.onload = function(e){
        const base64Data = e.target.result.split(',')[1];
        // progressText.textContent = 'Model eğitiliyor. Bu işlem uzun sürebilir.';
        pywebview.api.voice_train(base64Data, epoch, avatarName).then(trainResult => {
            if(trainResult.status === 'ok'){
                // progressText.textContent = 'Islem baslatiliyor.';
                progressPopup.style.display = 'none';
                overlay.style.display = 'none';
                lastModelPath = trainResult.path;
                document.querySelector('.edit-section .save-changes-button').classList.add('blinking-button');
            }else{
                // progressText.textContent = trainResult.message;
                console.log('Training result:', trainResult.message);
            }
            closeTerminalButton.style.display = 'block';
        });
    };
    reader.readAsDataURL(file);
}

const editAvatarNameInput = document.querySelector('#edit-avatar-name-input');

function saveEditChanges(){
    const avatarName = editSection.querySelector('.title').textContent;

    if(lastModelPath){
        pywebview.api.save_model_to_database(lastModelPath, avatarName);
        document.querySelector('.edit-section .save-changes-button').classList.remove('blinking-button');
        lastModelPath = null;
    }

    if(editAvatarNameInput.value != avatarName){
        pywebview.api.change_avatar_name(avatarName, editAvatarNameInput.value).then(result => {
            refreshAvatars();
        });
    }

    // closeEditSection();
}


function deleteAvatar(){
    pywebview.api.delete_avatar(lastRightClick.getAttribute('avatar-name')).then(() => {
        refreshAvatars();
        closeEditSection();
    });
}

audioTtsCheckbox.addEventListener('change', function(){
    if(audioTtsCheckbox.checked){
        document.querySelector('.hedef-ses-text').style.color = '#000';
        document.querySelector('.tts-text').style.color = '#55e868';

        document.getElementById('target-voice').parentElement.style.display = 'none';
        document.querySelector('.target-voice-name').style.opacity  = '0';
        document.querySelector('.target-voice-name').style.pointerEvents = 'none';

        document.querySelector('.tts-input').style.display = 'flex';
    }else{
        document.querySelector('.hedef-ses-text').style.color = '#0056b3';
        document.querySelector('.tts-text').style.color = '#000';

        document.getElementById('target-voice').parentElement.style.display = 'flex';
        document.querySelector('.target-voice-name').style.opacity  = '1';
        document.querySelector('.target-voice-name').style.pointerEvents = 'auto';

        document.querySelector('.tts-input').style.display = 'none';
    }
});


// function appendOutput(text) {
//     const term = document.getElementById('terminal');
//     term.innerHTML += text + "\\n";

//     term.scrollTop = term.scrollHeight;
// }


const term = new Terminal({
    cols: 80,
    rows: 24,
    cursorBlink: true
});
term.open(document.getElementById('terminal'));

window.appendOutput = function(text) {
    term.write(text + '\r\n');
};


function closeTerminal(){
    progressPopup.style.display = 'none';
    overlay.style.display = 'none';
    document.querySelectorAll('.progress-popup p').forEach(p => {
        p.remove();
    });
    closeTerminalButton.style.display = 'none';
}