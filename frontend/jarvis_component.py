def get_jarvis_html(backend_url: str, student_id: str = '26BEC1185') -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICHIKA JARVIS INTERFACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --yellow: #FFD700;
            --gold: #FFB700;
            --cyan: #00e5ff;
            --blue: #0088ff;
            --dark-bg: #07070c;
            --glow: 0 0 15px #FFD700, 0 0 30px #00e5ff, 0 0 50px #FFB700;
            --hud-color: rgba(255, 215, 0, 0.75);
            --hud-blue: rgba(0, 229, 255, 0.6);
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }}
        body {{
            background-color: var(--dark-bg);
            color: var(--yellow);
            font-family: 'Rajdhani', sans-serif;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        /* Scanline Overlay */
        .scanlines {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.2));
            background-size: 100% 4px;
            pointer-events: none;
            z-index: 100;
            opacity: 0.3;
        }}
        
        /* Status Bar */
        .status-bar {{
            position: absolute;
            top: 0; width: 100%;
            display: flex;
            justify-content: space-between;
            padding: 15px 30px;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            letter-spacing: 2px;
            border-bottom: 1px solid var(--hud-color);
            background: linear-gradient(90deg, rgba(255,215,0,0.15) 0%, rgba(0,0,0,0) 50%, rgba(0,229,255,0.15) 100%);
            z-index: 10;
            text-shadow: 0 0 8px var(--yellow);
        }}
        .status-item span {{
            color: var(--cyan);
        }}
        
        /* Main Visual Container */
        .viewport {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        
        /* Arc Reactor Animation */
        .reactor-container {{
            position: relative;
            width: 320px;
            height: 320px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .reactor-ring {{
            position: absolute;
            border-radius: 50%;
            border: 2px solid transparent;
        }}
        .ring-1 {{
            width: 100%; height: 100%;
            border-top: 3px solid var(--yellow);
            border-bottom: 3px solid var(--yellow);
            animation: rotate-right 10s linear infinite;
            box-shadow: 0 0 20px var(--yellow) inset, 0 0 10px var(--yellow);
        }}
        .ring-2 {{
            width: 85%; height: 85%;
            border-left: 2px dashed var(--cyan);
            border-right: 2px dashed var(--cyan);
            animation: rotate-left 15s linear infinite;
            box-shadow: 0 0 15px var(--cyan);
        }}
        .ring-3 {{
            width: 70%; height: 70%;
            border: 2px solid var(--gold);
            box-shadow: 0 0 25px var(--cyan);
            animation: pulse-glow 3s infinite alternate;
        }}
        .reactor-core {{
            width: 50%; height: 50%;
            background: radial-gradient(circle, #ffffff 0%, var(--yellow) 30%, var(--cyan) 70%, var(--blue) 100%);
            border-radius: 50%;
            box-shadow: var(--glow);
            animation: pulse-glow 2s infinite alternate;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        /* HUD Elements */
        .hud-panel {{
            position: absolute;
            border: 1px solid var(--hud-color);
            background: rgba(0, 212, 255, 0.05);
            padding: 15px;
            box-shadow: inset 0 0 10px rgba(0, 212, 255, 0.2);
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
        }}
        .hud-left {{
            top: 20%; left: 30px;
            width: 200px;
            height: 300px;
        }}
        .hud-left::before {{
            content: 'SYSTEM DIAGNOSTICS\\A--\\A CPU: 34%\\A MEM: 12GB/64GB\\A NET: UPLINK SECURE\\A--\\A AI CORE: STABLE\\A PROTOCOL: OMEGA';
            white-space: pre-wrap;
            line-height: 2;
        }}
        
        /* History Panel */
        .history-panel {{
            position: absolute;
            right: 30px;
            top: 20px;
            bottom: 20px;
            width: 300px;
            border: 1px solid var(--hud-color);
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(5px);
            display: flex;
            flex-direction: column;
            z-index: 10;
        }}
        .history-header {{
            padding: 10px;
            border-bottom: 1px solid var(--hud-color);
            font-family: 'Orbitron', sans-serif;
            text-align: center;
            letter-spacing: 1px;
            background: rgba(0,212,255,0.1);
        }}
        .history-content {{
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        .history-content::-webkit-scrollbar {{
            width: 5px;
        }}
        .history-content::-webkit-scrollbar-thumb {{
            background: var(--cyan);
        }}
        .msg {{
            padding: 10px;
            border-radius: 4px;
            font-size: 1rem;
            line-height: 1.4;
            word-wrap: break-word;
        }}
        .msg.user {{
            align-self: flex-end;
            background: rgba(0, 136, 255, 0.2);
            border-right: 2px solid var(--blue);
            text-align: right;
            max-width: 90%;
        }}
        .msg.ai {{
            align-self: flex-start;
            background: rgba(0, 212, 255, 0.2);
            border-left: 2px solid var(--cyan);
            max-width: 90%;
            text-shadow: 0 0 2px var(--cyan);
        }}

        /* Center Text Typewriter */
        .typewriter-container {{
            position: absolute;
            top: 75%; left: 50%;
            transform: translate(-50%, -50%);
            width: 60%;
            text-align: center;
            z-index: 15;
            min-height: 100px;
            pointer-events: none;
        }}
        #ai-response {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            color: #fff;
            text-shadow: 0 0 10px var(--cyan);
            letter-spacing: 1px;
            line-height: 1.5;
        }}
        .cursor {{
            display: inline-block;
            width: 10px;
            height: 1.5rem;
            background: var(--cyan);
            animation: blink 1s step-end infinite;
            vertical-align: bottom;
            margin-left: 5px;
        }}

        /* Bottom Controls */
        .bottom-controls {{
            position: absolute;
            bottom: 0; left: 0; right: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: linear-gradient(0deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
            z-index: 20;
        }}
        
        .mic-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 15px;
        }}
        
        #mic-btn {{
            width: 70px; height: 70px;
            border-radius: 50%;
            background: transparent;
            border: 2px solid var(--cyan);
            color: var(--cyan);
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 0 15px rgba(0,212,255,0.5);
            transition: all 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        #mic-btn:hover {{
            box-shadow: var(--glow);
            background: rgba(0,212,255,0.1);
        }}
        #mic-btn.listening {{
            border-color: #00ff00;
            color: #00ff00;
            box-shadow: 0 0 20px #00ff00, 0 0 40px inset #00ff00;
            animation: vibrate 0.3s linear infinite;
        }}
        #mic-btn.processing {{
            border-color: #ffaa00;
            color: #ffaa00;
            box-shadow: 0 0 20px #ffaa00;
            animation: pulse-glow 1s infinite alternate;
        }}
        
        /* Waveform */
        .waveform {{
            display: flex;
            align-items: flex-end;
            height: 40px;
            gap: 4px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .waveform.active {{
            opacity: 1;
        }}
        .bar {{
            width: 8px;
            background: var(--cyan);
            box-shadow: 0 0 5px var(--cyan);
            border-radius: 4px 4px 0 0;
            height: 5px;
            transition: height 0.1s ease;
        }}

        /* Text Fallback */
        .text-input-container {{
            display: flex;
            width: 50%;
            max-width: 600px;
            gap: 10px;
            opacity: 0.7;
            transition: opacity 0.3s;
        }}
        .text-input-container:hover, .text-input-container:focus-within {{
            opacity: 1;
        }}
        #text-input {{
            flex: 1;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--cyan);
            color: var(--cyan);
            padding: 10px 15px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.1rem;
            outline: none;
            border-radius: 4px;
        }}
        #text-input:focus {{
            box-shadow: 0 0 10px rgba(0,212,255,0.5);
            background: rgba(0, 212, 255, 0.2);
        }}
        #send-btn {{
            background: transparent;
            border: 1px solid var(--cyan);
            color: var(--cyan);
            padding: 0 20px;
            font-family: 'Orbitron', sans-serif;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        #send-btn:hover {{
            background: var(--cyan);
            color: #000;
            box-shadow: 0 0 10px var(--cyan);
        }}

        #status-text {{
            position: absolute;
            top: -25px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            color: var(--cyan);
            letter-spacing: 2px;
            text-align: center;
            width: 100%;
        }}

        /* Animations */
        @keyframes rotate-right {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        @keyframes rotate-left {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(-360deg); }}
        }}
        @keyframes pulse-glow {{
            0% {{ opacity: 0.6; box-shadow: 0 0 10px var(--cyan); }}
            100% {{ opacity: 1; box-shadow: 0 0 30px var(--cyan), 0 0 50px var(--blue); }}
        }}
        @keyframes pulse-text {{
            0% {{ opacity: 0.7; }}
            50% {{ opacity: 1; text-shadow: 0 0 10px var(--cyan); }}
            100% {{ opacity: 0.7; }}
        }}
        @keyframes vibrate {{
            0% {{ transform: translate(0, 0); }}
            25% {{ transform: translate(2px, -2px); }}
            50% {{ transform: translate(0, 2px); }}
            75% {{ transform: translate(-2px, 0); }}
            100% {{ transform: translate(0, 0); }}
        }}
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0; }}
        }}
        
        /* SVGs */
        .icon {{
            width: 28px; height: 28px;
            fill: currentColor;
        }}
    </style>
</head>
<body>
    <div class="scanlines"></div>
    
    <div class="status-bar">
        <span>ICHIKA v4.0</span>
        <span>JARVIS MODE</span>
        <span>ONLINE</span>
    </div>

    <div class="main-container">
        <div class="hud-panel hud-left"></div>
        
        <div class="reactor-container">
            <div class="reactor-ring ring-1"></div>
            <div class="reactor-ring ring-2"></div>
            <div class="reactor-ring ring-3"></div>
            <div class="reactor-core"></div>
        </div>

        <div class="typewriter-container">
            <span id="ai-response">SYSTEM INITIALIZED. STANDING BY.</span><span class="cursor"></span>
        </div>
        
        <div class="history-panel">
            <div class="history-header">COMMS LINK</div>
            <div class="history-content" id="chat-history">
                <!-- Messages go here -->
            </div>
        </div>
    </div>

    <div class="bottom-controls">
        <div class="mic-container">
            <div class="waveform" id="waveform-left">
                <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
            </div>
            
            <div style="position:relative; display:flex; justify-content:center;">
                <div id="status-text">AWAITING</div>
                <button id="mic-btn" title="Click to speak">
                    <svg class="icon" viewBox="0 0 24 24">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                </button>
            </div>
            
            <div class="waveform" id="waveform-right">
                <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
            </div>
        </div>
        
        <div class="text-input-container">
            <input type="text" id="text-input" placeholder="MANUAL OVERRIDE: TYPE COMMAND HERE..." autocomplete="off">
            <button id="send-btn">EXECUTE</button>
        </div>
    </div>

    <script>
        const BACKEND_URL = "{backend_url}";
        const STUDENT_ID = "{student_id}";
        
        // UI Elements
        const micBtn = document.getElementById('mic-btn');
        const statusText = document.getElementById('status-text');
        const textInput = document.getElementById('text-input');
        const sendBtn = document.getElementById('send-btn');
        const aiResponseEl = document.getElementById('ai-response');
        const chatHistory = document.getElementById('chat-history');
        const waveforms = document.querySelectorAll('.waveform');
        const bars = document.querySelectorAll('.bar');
        
        // State
        let isListening = false;
        let isProcessing = false;
        let recognition = null;
        let synth = window.speechSynthesis;
        let selectedVoice = null;
        let typingInterval = null;
        let waveformInterval = null;
        
        // Setup Speech Recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {{
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {{
                isListening = true;
                updateMicUI('listening');
                typeText('LISTENING...');
            }};
            
            recognition.onresult = (event) => {{
                let interimTranscript = '';
                let finalTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    if (event.results[i].isFinal) {{
                        finalTranscript += event.results[i][0].transcript;
                    }} else {{
                        interimTranscript += event.results[i][0].transcript;
                    }}
                }}
                
                if (interimTranscript) {{
                    typeText(interimTranscript, true);
                }}
                
                if (finalTranscript) {{
                    processUserInput(finalTranscript);
                }}
            }};
            
            recognition.onerror = (event) => {{
                console.error('Speech recognition error', event.error);
                updateMicUI('idle');
                typeText('ERROR: VOICE INPUT FAILED');
                isListening = false;
            }};
            
            recognition.onend = () => {{
                isListening = false;
                if (!isProcessing) {{
                    updateMicUI('idle');
                }}
            }};
        }} else {{
            console.warn('Speech recognition not supported in this browser.');
            micBtn.style.opacity = '0.5';
            micBtn.style.cursor = 'not-allowed';
            statusText.innerText = 'VOICE UNAVAILABLE';
        }}
        
        // Setup Speech Synthesis
        function loadVoices() {{
            const voices = synth.getVoices();
            // Try to find a deep/robotic/UK voice
            selectedVoice = voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('Daniel') || v.name.includes('David')) || voices[0];
        }}
        if (speechSynthesis.onvoiceschanged !== undefined) {{
            speechSynthesis.onvoiceschanged = loadVoices;
        }} else {{
            loadVoices();
        }}
        
        function speak(text) {{
            if (synth.speaking) synth.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            if (selectedVoice) utterance.voice = selectedVoice;
            utterance.pitch = 0.7;
            utterance.rate = 1.0;
            
            utterance.onstart = () => {{
                waveforms.forEach(w => w.classList.add('active'));
                startWaveformAnimation();
            }};
            
            utterance.onend = () => {{
                waveforms.forEach(w => w.classList.remove('active'));
                stopWaveformAnimation();
            }};
            
            synth.speak(utterance);
        }}
        
        // Waveform Animation
        function startWaveformAnimation() {{
            waveformInterval = setInterval(() => {{
                bars.forEach(bar => {{
                    const height = Math.floor(Math.random() * 30) + 5;
                    bar.style.height = height + 'px';
                }});
            }}, 100);
        }}
        
        function stopWaveformAnimation() {{
            clearInterval(waveformInterval);
            bars.forEach(bar => {{
                bar.style.height = '5px';
            }});
        }}
        
        // Typewriter Effect
        function typeText(text, instant = false) {{
            clearInterval(typingInterval);
            if (instant) {{
                aiResponseEl.innerText = text;
                return;
            }}
            
            aiResponseEl.innerText = '';
            let i = 0;
            typingInterval = setInterval(() => {{
                if (i < text.length) {{
                    aiResponseEl.innerText += text.charAt(i);
                    i++;
                }} else {{
                    clearInterval(typingInterval);
                }}
            }}, 30);
        }}
        
        // History Management
        function addToHistory(sender, text) {{
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg ' + (sender === 'USER' ? 'user' : 'ai');
            msgDiv.innerText = text;
            chatHistory.appendChild(msgDiv);
            
            // Keep only last 10 messages
            while (chatHistory.children.length > 10) {{
                chatHistory.removeChild(chatHistory.firstChild);
            }}
            
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }}
        
        // UI Updates
        function updateMicUI(state) {{
            micBtn.className = '';
            if (state === 'idle') {{
                statusText.innerText = 'AWAITING';
                statusText.style.color = 'var(--cyan)';
            }} else if (state === 'listening') {{
                micBtn.classList.add('listening');
                statusText.innerText = 'LISTENING...';
                statusText.style.color = '#00ff00';
            }} else if (state === 'processing') {{
                micBtn.classList.add('processing');
                statusText.innerText = 'PROCESSING...';
                statusText.style.color = '#ffaa00';
            }}
        }}
        
        // Process Input
        async function processUserInput(text) {{
            if (!text.trim()) return;
            
            isProcessing = true;
            updateMicUI('processing');
            addToHistory('USER', text);
            typeText('PROCESSING...', true);
            textInput.value = '';
            
            try {{
                const res = await fetch(BACKEND_URL + '/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        text: text,
                        tone: 'casual',
                        student_id: STUDENT_ID
                    }})
                }});
                
                const data = await res.json();
                const reply = data.response || 'I am unable to process that request at this time.';
                
                addToHistory('AI', reply);
                typeText(reply);
                speak(reply);
                
            }} catch (error) {{
                console.error(error);
                const errorMsg = 'CONNECTION LOST. UNABLE TO REACH MAINFRAME.';
                addToHistory('AI', errorMsg);
                typeText(errorMsg);
                speak(errorMsg);
            }} finally {{
                isProcessing = false;
                updateMicUI('idle');
            }}
        }}
        
        // Event Listeners
        micBtn.addEventListener('click', () => {{
            if (!recognition) return;
            if (isListening) {{
                recognition.stop();
            }} else {{
                try {{
                    recognition.start();
                }} catch (e) {{
                    console.error(e);
                }}
            }}
        }});
        
        sendBtn.addEventListener('click', () => {{
            processUserInput(textInput.value);
        }});
        
        textInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                processUserInput(textInput.value);
            }}
        }});
    </script>
</body>
</html>
"""
