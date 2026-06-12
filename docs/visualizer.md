# Visualizer

<div class="viz-app" markdown>

The ELIN Bytecode Visualizer lets you step through ELIN programs instruction by instruction, watching the stack, memory, and I/O in real time.

</div>

<div id="visualizer-container" class="viz-embed">
    <div class="viz-panel viz-source">
        <div class="panel-header">
            <span>Source / Bytecode</span>
            <div class="panel-controls">
                <button id="btn-load" title="Load .outz file">Load</button>
                <button id="btn-example" title="Load example">Example</button>
                <input type="file" id="file-input" accept=".outz" style="display:none">
            </div>
        </div>
        <textarea id="source-input" placeholder="Paste ELIN source here, or load a .outz file..."></textarea>
        <div id="bytecode-view" class="bytecode-output"></div>
    </div>

    <div class="viz-panel viz-eval">
        <div class="panel-header">
            <span>Evaluator / Stack</span>
        </div>
        <div id="eval-view">
            <div class="eval-section">
                <h4>Stack</h4>
                <div id="stack-view" class="stack-container"></div>
            </div>
            <div class="eval-section">
                <h4>Call Stack</h4>
                <div id="callstack-view" class="callstack-container"></div>
            </div>
        </div>
    </div>

    <div class="viz-panel viz-io">
        <div class="panel-header">
            <span>Memory / I/O</span>
        </div>
        <div id="io-view">
            <div class="eval-section">
                <h4>Variables</h4>
                <div id="vars-view" class="vars-container"></div>
            </div>
            <div class="eval-section">
                <h4>Output</h4>
                <div id="output-view" class="output-container"></div>
            </div>
        </div>
    </div>
</div>

<div class="viz-controls">
    <button id="btn-step" class="ctrl-btn">Step</button>
    <button id="btn-run" class="ctrl-btn">Run</button>
    <button id="btn-reset" class="ctrl-btn">Reset</button>
    <label>Speed: <input type="range" id="speed-slider" min="1" max="100" value="50"></label>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // Visualizer initialization is handled by visualizer.js
    // This script sets up the UI interactions
});
</script>
