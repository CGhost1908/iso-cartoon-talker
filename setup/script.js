
const term = new Terminal({
    cols: 80,
    rows: 24,
    cursorBlink: true
});
term.open(document.getElementById('terminal'));

window.appendOutput = function(text) {
    term.write(text + '\r\n');
};

function startInstallation(){
    pywebview.api.install_iso();
    document.getElementById('1').style.display = 'none';
    document.getElementById('2').style.display = 'flex';
}

function raiseError(message){
    document.querySelector('.error-text').textContent = message;
    document.getElementById('2').style.display = 'none';
    document.getElementById('3').style.display = 'flex';
}

function closeInstaller(){
    pywebview.api.close();
}

function showFinishPage(){
    document.getElementById('2').style.display = 'none';
    document.getElementById('4').style.display = 'flex';
}