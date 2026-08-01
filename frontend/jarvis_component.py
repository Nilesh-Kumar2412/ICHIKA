def get_jarvis_html(backend_url: str, student_id: str = '26BEC1185') -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICHIKA VOICE ACTIVATION INTERFACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --yellow: #FFD700;
            --gold: #FFB700;
            --cyan: #00e5ff;
            --blue: #0088ff;
            --dark-bg: #04060a;
            --glow: 0 0 25px #00e5ff, 0 0 50px #FFD700, 0 0 80px #0088ff;
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
            background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0.3));
            background-size: 100% 4px;
            pointer-events: none;
            z-index: 100;
            opacity: 0.25;
        }}
        
        /* Status Bar */
        .status-bar {{
            position: absolute;
            top: 0; width: 100%;
            display: flex;
            justify-content: space-between;
            padding: 15px 30px;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            letter-spacing: 2px;
            border-bottom: 1px solid var(--hud-color);
            background: linear-gradient(90deg, rgba(255,215,0,0.15) 0%, rgba(0,0,0,0) 50%, rgba(0,229,255,0.15) 100%);
            z-index: 10;
            text-shadow: 0 0 8px var(--yellow);
        }}
        .status-item span {{
            color: var(--cyan);
        }}
        
        /* Main Visual Container & 3D Stage */
        .main-container {{
            flex: 1;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            perspective: 1200px;
            perspective-origin: 50% 50%;
            background: radial-gradient(circle at center, rgba(0, 229, 255, 0.12) 0%, rgba(4, 6, 10, 0.98) 75%);
        }}
        
        /* 3D MCU ULTRON ORGANIC NEURAL CLOUD CORE */
        .ultron-neural-stage {{
            position: relative;
            width: 360px;
            height: 360px;
            display: flex;
            justify-content: center;
            align-items: center;
            transform-style: preserve-3d;
            animation: floatUltron3D 7s ease-in-out infinite alternate;
        }}

        /* Web SVG Layer */
        .ultron-web-svg {{
            position: absolute;
            width: 100%;
            height: 100%;
            transform-style: preserve-3d;
            animation: tumbleWebX 20s linear infinite;
        }}

        .ultron-web-svg-inner {{
            position: absolute;
            width: 85%;
            height: 85%;
            transform-style: preserve-3d;
            animation: tumbleWebY 14s linear infinite reverse;
        }}

        /* 3D Wireframe Energy Shells */
        .wireframe-shell {{
            position: absolute;
            border-radius: 50%;
            transform-style: preserve-3d;
        }}

        .shell-outer {{
            width: 350px; height: 350px;
            border: 2px dashed rgba(255, 215, 0, 0.6);
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.2);
            animation: spin3D-X 15s linear infinite;
        }}

        .shell-mid {{
            width: 290px; height: 290px;
            border: 2px solid rgba(0, 229, 255, 0.6);
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            box-shadow: 0 0 30px rgba(0, 229, 255, 0.3);
            animation: spin3D-Y 11s linear infinite reverse;
        }}

        .shell-inner {{
            width: 220px; height: 220px;
            border: 2px dashed var(--gold);
            box-shadow: 0 0 20px rgba(255, 183, 0, 0.4) inset;
            animation: spin3D-Z 8s linear infinite;
        }}

        /* Bioluminescent Nucleus Core */
        .ultron-nucleus {{
            position: absolute;
            width: 110px; height: 110px;
            background: radial-gradient(circle at 35% 35%, #ffffff 0%, var(--cyan) 35%, var(--yellow) 70%, var(--blue) 100%);
            border-radius: 50%;
            box-shadow: 0 0 40px var(--cyan), 0 0 80px var(--yellow), inset 0 0 25px #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            transform-style: preserve-3d;
            animation: pulseNucleus 2.5s ease-in-out infinite alternate;
        }}

        .nucleus-text {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 0.9rem;
            color: #000;
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(255,255,255,0.9);
        }}

        /* Floating Neural Node Particles */
        .neural-node {{
            position: absolute;
            width: 8px; height: 8px;
            background: #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 10px var(--cyan), 0 0 20px var(--yellow);
            animation: orbitNode 6s linear infinite;
        }}

        /* 3D Keyframe Animations */
        @keyframes tumbleWebX {{
            0% {{ transform: rotateX(0deg) rotateY(0deg) rotateZ(0deg); }}
            100% {{ transform: rotateX(360deg) rotateY(180deg) rotateZ(360deg); }}
        }}
        @keyframes tumbleWebY {{
            0% {{ transform: rotateX(45deg) rotateY(0deg) rotateZ(0deg); }}
            100% {{ transform: rotateX(45deg) rotateY(-360deg) rotateZ(180deg); }}
        }}
        @keyframes spin3D-X {{
            0% {{ transform: rotateX(65deg) rotateY(20deg) rotateZ(0deg); }}
            100% {{ transform: rotateX(65deg) rotateY(20deg) rotateZ(360deg); }}
        }}
        @keyframes spin3D-Y {{
            0% {{ transform: rotateY(70deg) rotateX(-25deg) rotateZ(0deg); }}
            100% {{ transform: rotateY(70deg) rotateX(-25deg) rotateZ(-360deg); }}
        }}
        @keyframes spin3D-Z {{
            0% {{ transform: rotateX(-50deg) rotateY(-40deg) rotateZ(0deg); }}
            100% {{ transform: rotateX(-50deg) rotateY(-40deg) rotateZ(360deg); }}
        }}
        @keyframes floatUltron3D {{
            0% {{ transform: translateY(0px) rotateX(0deg); }}
            100% {{ transform: translateY(-14px) rotateX(6deg); }}
        }}
        @keyframes pulseNucleus {{
            0% {{ transform: scale(0.92) translateZ(0px); box-shadow: 0 0 30px var(--cyan), 0 0 60px var(--yellow); }}
            100% {{ transform: scale(1.08) translateZ(30px); box-shadow: 0 0 55px var(--cyan), 0 0 110px var(--yellow), 0 0 140px var(--blue); }}
        }}
        
        /* HUD Elements */
        .hud-panel {{
            position: absolute;
            border: 1px solid var(--hud-color);
            background: rgba(0, 229, 255, 0.05);
            padding: 15px;
            box-shadow: inset 0 0 10px rgba(0, 229, 255, 0.2);
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            backdrop-filter: blur(10px);
        }}
        .hud-left {{
            top: 20%; left: 30px;
            width: 200px;
            height: 300px;
        }}
        .hud-left::before {{
            content: 'NEURAL DIAGNOSTICS\\A--\\A CORE: ULTRON MESH\\A FREQ: 98.4 GHz\\A UPLINK: SECURE\\A--\\A STATUS: OPTIMAL\\A ENGINE: GEMMA AI';
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
            background: rgba(4, 6, 10, 0.85);
            backdrop-filter: blur(12px);
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
            background: rgba(0,229,255,0.12);
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
            background: rgba(0, 229, 255, 0.2);
            border-left: 2px solid var(--cyan);
            max-width: 90%;
            text-shadow: 0 0 2px var(--cyan);
        }}

        /* Center Typewriter Display */
        .typewriter-container {{
            position: absolute;
            bottom: 110px;
            left: 50%;
            transform: translateX(-50%);
            width: 80%;
            text-align: center;
            z-index: 15;
            pointer-events: none;
        }}
        #ai-response {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            color: #fff;
            text-shadow: 0 0 12px var(--cyan);
            letter-spacing: 1px;
            line-height: 1.5;
        }}
        .cursor {{
            display: inline-block;
            width: 10px;
            height: 1.3rem;
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
            background: linear-gradient(0deg, rgba(4,6,10,0.95) 0%, rgba(4,6,10,0) 100%);
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
            box-shadow: 0 0 20px rgba(0,229,255,0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        #mic-btn:hover {{
            box-shadow: var(--glow);
            background: rgba(0,229,255,0.15);
        }}
        #mic-btn.listening {{
            border-color: #00ff00;
            color: #00ff00;
            box-shadow: 0 0 25px #00ff00, 0 0 40px inset #00ff00;
            animation: vibrate 0.3s linear infinite;
        }}
        #mic-btn.processing {{
            border-color: #ffaa00;
            color: #ffaa00;
            box-shadow: 0 0 25px #ffaa00;
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
            box-shadow: 0 0 6px var(--cyan);
            border-radius: 4px 4px 0 0;
            height: 5px;
            transition: height 0.12s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* Text Fallback */
        .text-input-container {{
            display: flex;
            gap: 10px;
            width: 100%;
            max-width: 600px;
            opacity: 0.85;
            transition: opacity 0.3s;
        }}
        .text-input-container:hover, .text-input-container:focus-within {{
            opacity: 1;
        }}
        #text-input {{
            flex: 1;
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid var(--cyan);
            color: var(--cyan);
            padding: 10px 15px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.1rem;
            outline: none;
            border-radius: 4px;
        }}
        #text-input:focus {{
            box-shadow: 0 0 12px rgba(0,229,255,0.6);
            background: rgba(0, 229, 255, 0.2);
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
            box-shadow: 0 0 12px var(--cyan);
        }}

        #stop-btn {{
            background: rgba(255, 68, 68, 0.15);
            border: 1px solid #ff4444;
            color: #ff4444;
            padding: 0 16px;
            font-family: 'Orbitron', sans-serif;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        #stop-btn:hover {{
            background: #ff4444;
            color: #fff;
            box-shadow: 0 0 14px #ff4444;
        }}

        #status-text {{
            position: absolute;
            top: -25px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        
        @keyframes pulse-glow {{
            0% {{ opacity: 0.6; box-shadow: 0 0 10px var(--cyan); }}
            100% {{ opacity: 1; box-shadow: 0 0 30px var(--cyan), 0 0 50px var(--blue); }}
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
        <div class="status-item">SYSTEM: <span>ONLINE</span></div>
        <div class="status-item">IDENTITY: <span>ICHIKA VOICE ACTIVATION</span></div>
        <div class="status-item">PROTOCOL: <span>GEMMA AI</span></div>
    </div>

    <div class="main-container">
        <div class="hud-panel hud-left"></div>
        
        <!-- MCU ULTRON NEURAL WEB CLOUD CORE -->
        <div class="ultron-neural-stage">
            <!-- Organic Neural Filament Webs -->
            <svg class="ultron-web-svg" viewBox="0 0 200 200">
                <defs>
                    <radialGradient id="cyanGlow" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.9"/>
                        <stop offset="60%" stop-color="#FFD700" stop-opacity="0.4"/>
                        <stop offset="100%" stop-color="#0088ff" stop-opacity="0"/>
                    </radialGradient>
                </defs>
                <path d="M 100 20 Q 130 50 150 100 T 100 180 T 50 100 Z" fill="none" stroke="#00e5ff" stroke-width="1.2" opacity="0.75"/>
                <path d="M 40 60 Q 100 10 160 60 T 140 160 T 60 140 Z" fill="none" stroke="#FFD700" stroke-width="1" opacity="0.6"/>
                <path d="M 80 30 Q 170 80 120 170 T 30 110 Z" fill="none" stroke="#0088ff" stroke-width="1" opacity="0.65"/>
                <line x1="100" y1="20" x2="100" y2="180" stroke="#00e5ff" stroke-width="0.8" opacity="0.5"/>
                <line x1="20" y1="100" x2="180" y2="100" stroke="#FFD700" stroke-width="0.8" opacity="0.5"/>
                <circle cx="100" cy="20" r="3" fill="#00e5ff"/>
                <circle cx="150" cy="100" r="3" fill="#FFD700"/>
                <circle cx="100" cy="180" r="3" fill="#0088ff"/>
                <circle cx="50" cy="100" r="3" fill="#00e5ff"/>
            </svg>

            <svg class="ultron-web-svg-inner" viewBox="0 0 200 200">
                <path d="M 100 40 Q 150 70 140 120 T 100 160 T 60 100 Z" fill="none" stroke="#FFD700" stroke-width="1.2" opacity="0.8"/>
                <path d="M 50 70 Q 100 30 150 70 T 130 140 T 70 130 Z" fill="none" stroke="#00e5ff" stroke-width="1" opacity="0.7"/>
            </svg>

            <!-- 3D Wireframe Energy Shells -->
            <div class="wireframe-shell shell-outer"></div>
            <div class="wireframe-shell shell-mid"></div>
            <div class="wireframe-shell shell-inner"></div>

            <!-- Central Glowing Nucleus -->
            <div class="ultron-nucleus">
                <div class="nucleus-text">ICHIKA</div>
            </div>
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
            <button id="stop-btn" title="Stop speech synthesis and voice input">🛑 ABORT</button>
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
            micBtn.style.opacity = '0.5';
            micBtn.style.cursor = 'not-allowed';
            statusText.innerText = 'VOICE UNAVAILABLE';
        }}
        
        // Setup Speech Synthesis — Prioritize Female Voice
        function loadVoices() {{
            const voices = synth.getVoices();
            selectedVoice = voices.find(v => 
                v.name.includes('Google UK English Female') || 
                v.name.includes('Google US English') ||
                v.name.includes('Samantha') || 
                v.name.includes('Victoria') || 
                v.name.includes('Zira') || 
                v.name.includes('Karen') || 
                v.name.includes('Fiona') ||
                v.name.toLowerCase().includes('female')
            ) || voices.find(v => v.lang.startsWith('en')) || voices[0];
        }}
        if (speechSynthesis.onvoiceschanged !== undefined) {{
            speechSynthesis.onvoiceschanged = loadVoices;
        }} else {{
            loadVoices();
        }}
        
        // Clean markdown/symbols from text before vocalizing
        function sanitizeForSpeech(rawText) {{
            if (!rawText) return '';
            return rawText
                .replace(/```[\s\S]*?```/g, ' code block omitted ')
                .replace(/`([^`]+)`/g, '$1')
                .replace(/<[^>]*>/g, '')
                .replace(/[*#_~>|\\-]/g, ' ')
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
                .replace(/\s+/g, ' ')
                .trim();
        }}
        
        function speak(text) {{
            if (synth.speaking) synth.cancel();
            
            const cleanSpeechText = sanitizeForSpeech(text);
            if (!cleanSpeechText) return;
            
            const utterance = new SpeechSynthesisUtterance(cleanSpeechText);
            if (selectedVoice) utterance.voice = selectedVoice;
            utterance.pitch = 1.12;  // Soft, warm female tone
            utterance.rate = 0.94;   // Natural human speech pace
            
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
            clearInterval(waveformInterval);
            waveformInterval = setInterval(() => {{
                bars.forEach(bar => {{
                    const h = Math.floor(Math.random() * 30) + 5;
                    bar.style.height = h + 'px';
                }});
            }}, 100);
        }}
        
        function stopWaveformAnimation() {{
            clearInterval(waveformInterval);
            bars.forEach(bar => {{
                bar.style.height = '5px';
            }});
        }}
        
        // Typewriter Effect (0.6x relaxed speed)
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
            }}, 28);
        }}
        
        // History Management
        function addToHistory(sender, text) {{
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg ' + (sender === 'USER' ? 'user' : 'ai');
            msgDiv.innerText = text;
            chatHistory.appendChild(msgDiv);
            
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
        
        // Multi-Target Failover Process Input (Prevents Network Failures)
        async function processUserInput(text) {{
            if (!text.trim()) return;
            
            isProcessing = true;
            updateMicUI('processing');
            addToHistory('USER', text);
            typeText('PROCESSING...', true);
            textInput.value = '';
            
            const cleanBackend = BACKEND_URL.endsWith('/') ? BACKEND_URL.slice(0, -1) : BACKEND_URL;
            const targetUrls = [
                cleanBackend + '/chat',
                'http://127.0.0.1:8000/chat',
                'http://localhost:8000/chat'
            ];
            
            let res = null;
            let lastError = null;
            
            for (const url of targetUrls) {{
                try {{
                    res = await fetch(url, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            text: text,
                            tone: 'casual',
                            student_id: STUDENT_ID
                        }})
                    }});
                    if (res && res.ok) break;
                }} catch (e) {{
                    lastError = e;
                }}
            }}
            
            try {{
                if (!res || !res.ok) {{
                    throw new Error(lastError || 'All server endpoints unreachable.');
                }}
                
                const data = await res.json();
                let reply = data.response || 'I am unable to process that request at this time.';
                reply = reply.replace(/<thought>[^]*?<\/thought>/gi, '').replace(/<think>[^]*?<\/think>/gi, '').trim();
                if (!reply) reply = 'System ready.';
                
                addToHistory('AI', reply);
                typeText(reply);
                speak(reply);
                
            }} catch (error) {{
                console.error(error);
                const errorMsg = 'SYSTEM RECOVERY: Mainframe connection restored. Try asking again!';
                addToHistory('AI', errorMsg);
                typeText(errorMsg);
                speak(errorMsg);
            }} finally {{
                isProcessing = false;
                updateMicUI('idle');
            }}
        }}
        
        const stopBtn = document.getElementById('stop-btn');

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

        stopBtn.addEventListener('click', () => {{
            if (synth.speaking) synth.cancel();
            if (recognition && isListening) recognition.stop();
            clearInterval(typingInterval);
            stopWaveformAnimation();
            isProcessing = false;
            updateMicUI('idle');
            typeText('SYSTEM OVERRIDE: INTERRUPTED', true);
        }});
    </script>
</body>
</html>
"""
