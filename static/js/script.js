
var socket = io();
var running = true;

document.getElementById('startButton').addEventListener('click', startRecording);
document.getElementById('stopButton').addEventListener('click', stopRecording);

let audioContext, microphone, processor, mediaRecorder;
let audioChunks = [];
let isRecording = false;
let silenceStart = null;
let isSilent = true;
const threshold = 50;
const silenceDuration = 2000; // 静默检测，单位毫秒
const lookbackFrames = 0.5 * 44100 / 1024; // 0.5秒的帧数

async function startRecording() {
    isRecording = true;
    document.getElementById('startButton').disabled = true;
    document.getElementById('stopButton').disabled = false;
    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("麦克风访问成功，录音开始");
    audioContext = new AudioContext();
    microphone = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(1024, 1, 1);
    microphone.connect(processor);
    processor.connect(audioContext.destination);
    processor.onaudioprocess = processAudio;

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.start();
    console.log("MediaRecorder启动");
}

function processAudio(e) {
    const inputBuffer = e.inputBuffer.getChannelData(0);
    const volume = Math.sqrt(inputBuffer.reduce((acc, val) => acc + val * val, 0) / inputBuffer.length) * 1000;
    

    if (volume < threshold) {
        console.log(`音量: ${volume.toFixed(2)}`);
        if (silenceStart === null) {
            silenceStart = Date.now();
            console.log("静默开始");
        } else if (Date.now() - silenceStart >= silenceDuration) {
            if (!isSilent) {
                console.log("静默超过2秒，保存录音");
                saveRecording();
                isSilent = true;
            }
        }
    } else {
        if (silenceStart !== null) {
            console.log("声音检测到，结束静默");
        }
        silenceStart = null;
        if (isSilent && audioChunks.length > lookbackFrames) {
            audioChunks = audioChunks.slice(-lookbackFrames);
        }
        isSilent = false;
    }
}

// 1. 戴耳机采用下面这种
// function saveRecording() {
//     mediaRecorder.stop();
//     mediaRecorder.onstop = async () => {
//         const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
//         const reader = new FileReader();
//         reader.readAsDataURL(audioBlob);
//         reader.onloadend = () => {
//             const base64AudioMessage = reader.result.split(',')[1];
//             socket.emit('audio', base64AudioMessage);
//             console.log("发送录音到服务器...");
//         };
//         audioChunks = [];
//         mediaRecorder.start();
//         console.log("MediaRecorder重启");
//     };
// }

// 2. 外放音采用下面这种。
let count = 1; // 用于记录调用次数（因为收音会收到机器和用户两者的声音）

function saveRecording() {
    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            if (count % 2 !== 0) { // 奇次时发送
                const base64AudioMessage = reader.result.split(',')[1];
                socket.emit('audio', base64AudioMessage);
                console.log("发送录音到服务器...");
            } else {
                console.log("偶次不发送录音");
            }
            count++; // 每次调用后计数器递增
        };
        audioChunks = [];
        mediaRecorder.start();
        console.log("MediaRecorder重启");
    };
}


function stopRecording() {
    processor.disconnect();
    mediaRecorder.stop();
    document.getElementById('startButton').disabled = false;
    document.getElementById('stopButton').disabled = true;
    console.log("录音停止，用户操作");
}


socket.on('stream', function(data) {
    var img = document.getElementById('video');
    img.src = 'data:image/jpeg;base64,' + data.image;
});

// // .js中
// socket.on('text', function(data) {
//     var textContainer = document.getElementById('text-container');
//     var newMessage = document.createElement('div');
//     newMessage.classList.add('message');
//     newMessage.textContent = data.message;
//     textContainer.appendChild(newMessage);
//     textContainer.scrollTop = textContainer.scrollHeight;
// });

// .js中
socket.on('text', function(data) {
    var textContainer = document.getElementById('text-container');
    var newMessage = document.createElement('div');
    
    if (data.message) {
        newMessage.classList.add('message');
        newMessage.textContent = data.message;
    } else if (data.usermessage) {
        newMessage.classList.add('usermessage');
        newMessage.textContent = data.usermessage;
    }

    textContainer.appendChild(newMessage);
    textContainer.scrollTop = textContainer.scrollHeight;
});




function toggleApp() {
    var controlButton = document.getElementById('control-button');
    if (running) {
        fetch('/stop')
            .then(response => response.json())
            .then(data => {
                console.log('App stopped:', data);
                alert('The application has been stopped.');
                controlButton.innerHTML = '<span>▶️ Resume</span>';
                running = false;
            })
            .catch((error) => {
                console.error('Error stopping the app:', error);
            });
    } else {
        fetch('/resume')
            .then(response => response.json())
            .then(data => {
                console.log('App resumed:', data);
                alert('The application has resumed.');
                controlButton.innerHTML = '<span>⏹ Stop</span>';
                running = true;
            })
            .catch((error) => {
                console.error('Error resuming the app:', error);
            });
    }
}

function setInterval() {
    var intervalInput = document.getElementById('interval-input').value;
    fetch('/set_interval', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ interval: parseInt(intervalInput) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'interval updated') {
            alert('Capture interval updated to ' + data.interval + ' seconds.');
        } else {
            alert('Failed to update interval: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error setting interval:', error);
    });
}
