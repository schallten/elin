---
template: visualizer/main.html
---

# Visualizer

The ELIN Bytecode Visualizer lets you step through ELIN programs instruction by instruction, watching the stack, memory, and I/O in real time.

<section id="setup">
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
        <h2>Load Program</h2>
        <select id="example-select" onchange="loadExample(this.value)">
            <option value="">Select Example...</option>
            <option value="hello">Hello World</option>
            <option value="fib">Fibonacci (Recursive)</option>
            <option value="math">Math Operations</option>
            <option value="loop">Array Loop</option>
        </select>
    </div>
    
    <div class="input-container">
        <textarea id="source-input" class="input-area" placeholder="Paste .outz content here..." oninput="updateIntellisense()" onscroll="syncScroll()"></textarea>
        <div id="intellisense-overlay" class="intellisense-overlay"></div>
    </div>

    <div style="display: flex; gap: 10px; align-items: center;">
        <input type="file" id="file-input" accept=".outz" style="font-family: monospace; font-size: 0.8rem; color: #666;">
        <button onclick="loadFromInput()">Load Source</button>
    </div>
</section>

<section id="visualizer" style="display:none;">
    <div class="controls">
        <button onclick="step()">Step Into</button>
        <button id="btn-run" onclick="run()">Run All</button>
        <button onclick="reset()">Reset</button>

        <div style="display:inline-block; margin: 0 15px; padding-left: 15px; border-left: 1px solid var(--md-default-fg-color--lightest);">
            <label for="speed-slider" style="font-family:monospace; font-size:0.8rem;">Speed:</label>
            <input type="range" id="speed-slider" min="50" max="1500" step="50" value="600" oninput="updateSpeed(this.value)">
            <span id="speed-disp" style="font-family:monospace; font-size:0.8rem; min-width: 50px; display:inline-block;">600ms</span>
        </div>

        <span id="status" style="margin-left: auto; font-family: monospace; font-size: 0.8rem; color: var(--md-accent-fg-color);">READY</span>
    </div>

    <div id="action-display" class="action-display">
        Waiting to start...
    </div>

    <div class="viz-container">
        <div class="viz-panel" id="code-panel">
            <h3>Source Bytecode</h3>
            <div id="code-display"></div>
        </div>

        <div class="viz-panel" id="stack-panel">
            <h3>Evaluator</h3>
            <h4>Call Stack</h4>
            <div id="callstack-display"></div>
            <hr style="border: none; border-top: 1px solid var(--md-default-fg-color--lightest); margin: 20px 0;">
            <h4>Evaluation Stack</h4>
            <div id="stack-display"></div>
        </div>

        <div class="viz-panel" id="mem-panel">
            <h3>Memory / IO</h3>
            <h4>Global Variables</h4>
            <div id="vars-display"></div>
            <hr style="border: none; border-top: 1px solid var(--md-default-fg-color--lightest); margin: 20px 0;">
            <h4>Console Output</h4>
            <div id="console-output"></div>
        </div>
    </div>
</section>
