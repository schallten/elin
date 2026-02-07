
const state = {
    lines: [],        // Raw source lines
    instructions: [], // Parsed instructions { op, args, originalLineIndex }
    pc: 0,            // Program Counter (index in instructions array)
    stack: [],
    vars: {},         // kv: index -> value
    halted: false,
    output: []
};

function reset() {
    stop();
    state.pc = 0;
    state.stack = [];
    state.vars = {};
    state.halted = false;
    state.output = [];
    state.lastExplanation = "";
    updateUI();
}

function loadFromInput() {
    const fileInput = document.getElementById('file-input');
    const textInput = document.getElementById('source-input');

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            parseSource(e.target.result);
        };
        reader.readAsText(file);
    } else {
        parseSource(textInput.value);
    }
}

function parseSource(source) {
    state.lines = source.split('\n');
    state.instructions = [];

    // Reset core state
    reset();

    // Parse loop
    for (let i = 0; i < state.lines.length; i++) {
        const line = state.lines[i].trim();
        if (!line || line.startsWith('#')) continue;

        const tokens = line.split(/\s+/);
        const opcode = parseInt(tokens[0], 10);

        let instruction = {
            op: opcode,
            args: [],
            lineIndex: i,
            text: line
        };

        // Parse args based on op
        if (opcode === 1) {
            // PUSH: 1 0 0 0 <val>
            // We expect 5 tokens usually, the last one is the value
            // But handle cases where value might be missing or different format?
            // main.py: "1 0 0 0 {value}"
            if (tokens.length >= 5) {
                instruction.args = [parseInt(tokens[4], 10)];
            }
        } else if ([2, 3, 8, 16, 17, 18].includes(opcode)) {
            // LOAD (2), STORE (3), PRINT (8), JMP (16), JZ (17), JNZ (18) take 1 arg
            if (tokens.length >= 2) {
                instruction.args = [parseInt(tokens[1], 10)];
            }
        }

        state.instructions.push(instruction);
    }

    // Show visualizer
    document.getElementById('visualizer').style.display = 'block';
    renderCode();
    updateUI();
}

function renderCode() {
    const display = document.getElementById('code-display');
    display.innerHTML = '';

    state.instructions.forEach((instr, idx) => {
        const div = document.createElement('div');
        div.className = 'line';
        div.id = `instr-${idx}`;
        div.textContent = `${instr.lineIndex + 1}: ${instr.text}`; // Line number 1-based
        display.appendChild(div);
    });
}



let runInterval = null;
let runSpeedMs = 600;

function updateSpeed(val) {
    runSpeedMs = parseInt(val, 10);
    document.getElementById('speed-disp').textContent = runSpeedMs + "ms";

    // If currently running, restart interval with new speed
    if (runInterval) {
        clearInterval(runInterval);
        runInterval = setInterval(() => {
            step();
        }, runSpeedMs);
    }
}

function updateUI(highlightStack = false, updatedVarIndex = -1) {
    // 1. Highlight current line
    document.querySelectorAll('.line').forEach(el => el.classList.remove('active'));
    if (!state.halted && state.pc < state.instructions.length) {
        const curr = document.getElementById(`instr-${state.pc}`);
        if (curr) {
            curr.classList.add('active');
            curr.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // 2. Render Stack
    const stackDiv = document.getElementById('stack-display');
    // We want to preserve existing elements to let CSS transitions work if possible,
    // but full re-render is safer for correctness. 
    // To animate "push", we can mark the new top element.
    const oldHtml = stackDiv.innerHTML;
    stackDiv.innerHTML = '';

    for (let i = state.stack.length - 1; i >= 0; i--) {
        const item = document.createElement('div');
        item.className = 'stack-item';
        item.textContent = state.stack[i];

        // If this is the top item and we just pushed (highlightStack true), add 'new' class
        if (highlightStack && i === state.stack.length - 1) {
            item.classList.add('new');
        }

        stackDiv.appendChild(item);
    }

    if (state.stack.length === 0) {
        stackDiv.innerHTML = '<div style="color:#888; font-style:italic; padding:5px;">Empty</div>';
    }

    // 3. Render Vars
    const varsDiv = document.getElementById('vars-display');
    varsDiv.innerHTML = '';
    Object.keys(state.vars).forEach(key => {
        const row = document.createElement('div');
        row.className = 'var-row';
        if (parseInt(key) === updatedVarIndex) {
            row.classList.add('updated');
        }
        row.innerHTML = `<span>Idx ${key}</span><span>${state.vars[key]}</span>`;
        varsDiv.appendChild(row);
    });

    // 4. Console
    const consoleDiv = document.getElementById('console-output');
    consoleDiv.textContent = state.output.join('\n');
    consoleDiv.scrollTop = consoleDiv.scrollHeight;

    // 5. Status
    const statusSpan = document.getElementById('status');
    const runBtn = document.getElementById('btn-run');

    if (state.halted) {
        statusSpan.textContent = "HALTED";
        statusSpan.style.color = "red";
        if (runInterval) stop();
    } else if (runInterval) {
        statusSpan.textContent = "RUNNING...";
        statusSpan.style.color = "blue";
    } else {
        statusSpan.textContent = "READY";
        statusSpan.style.color = "var(--accent-color)";
    }

    // 6. Action Explanation
    const actionDiv = document.getElementById('action-display');
    if (state.lastExplanation) {
        actionDiv.innerHTML = state.lastExplanation;
    } else {
        actionDiv.textContent = "Waiting to start...";
    }
}

function getExplanation(instr) {
    if (!instr) return "End of program";

    switch (instr.op) {
        case 1: // PUSH
            return `<strong>PUSH</strong> Value <span style="font-weight:bold">${instr.args[0]}</span> onto the stack.`;
        case 2: // LOAD
            return `<strong>LOAD</strong> Retrieve value from variable Index ${instr.args[0]} and push to stack.`;
        case 3: // STORE
            return `<strong>STORE</strong> Pop top value from stack and store into variable Index ${instr.args[0]}.`;
        case 4: // ADD
            return `<strong>ADD</strong> Pop top two values, add them, and push the result.`;
        case 5: // SUB
            return `<strong>SUB</strong> Pop top two values, subtract top from second, push result.`;
        case 6: // MUL
            return `<strong>MUL</strong> Pop top two values, multiply them, push result.`;
        case 7: // DIV
            return `<strong>DIV</strong> Pop top two values, divide second by top, push integer result.`;
        case 8: // PRINT
            return `<strong>PRINT</strong> Output value of variable Index ${instr.args[0]} to console.`;
        case 9: // HALT
            return `<strong>HALT</strong> Stop execution.`;
        case 10: // CMP_EQ
            return `<strong>CMP_EQ</strong> Pop two values, push 1 if equal (==), 0 otherwise.`;
        case 11: // CMP_NEQ
            return `<strong>CMP_NEQ</strong> Pop two values, push 1 if not equal (!=), 0 otherwise.`;
        case 12: // CMP_LT
            return `<strong>CMP_LT</strong> Pop two values, push 1 if first < second, 0 otherwise.`;
        case 13: // CMP_LTE
            return `<strong>CMP_LTE</strong> Pop two values, push 1 if first <= second, 0 otherwise.`;
        case 14: // CMP_GT
            return `<strong>CMP_GT</strong> Pop two values, push 1 if first > second, 0 otherwise.`;
        case 15: // CMP_GTE
            return `<strong>CMP_GTE</strong> Pop two values, push 1 if first >= second, 0 otherwise.`;
        case 16: // JMP
            return `<strong>JMP</strong> Jump to instruction at index ${instr.args[0]}.`;
        case 17: // JZ
            return `<strong>JZ</strong> Pop value. If 0, jump to instruction at index ${instr.args[0]}.`;
        case 18: // JNZ
            return `<strong>JNZ</strong> Pop value. If not 0, jump to instruction at index ${instr.args[0]}.`;
        default:
            return `<strong>UNKNOWN</strong> Opcode ${instr.op}`;
    }
}

function step() {
    if (state.halted || state.pc >= state.instructions.length) {
        stop();
        state.lastExplanation = getExplanation(null); // Set explanation for end of program
        updateUI();
        return;
    }

    const instr = state.instructions[state.pc];
    state.lastExplanation = getExplanation(instr); // Store for UI

    let highlightStack = false;
    let updatedVarIndex = -1;

    switch (instr.op) {
        case 1: // PUSH
            state.stack.push(instr.args[0]);
            highlightStack = true;
            break;
        case 2: // LOAD <index>
            const val = state.vars[instr.args[0]];
            if (val === undefined) {
                console.error("Runtime Error: Loading undefined var");
                state.stack.push(0);
            } else {
                state.stack.push(val);
            }
            highlightStack = true;
            break;
        case 3: // STORE <index>
            const valStore = state.stack.pop();
            state.vars[instr.args[0]] = valStore;
            updatedVarIndex = instr.args[0];
            break;
        case 4: // ADD
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a + b);
                highlightStack = true;
            }
            break;
        case 5: // SUB
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a - b);
                highlightStack = true;
            }
            break;
        case 6: // MUL
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a * b);
                highlightStack = true;
            }
            break;
        case 7: // DIV
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(Math.floor(a / b));
                highlightStack = true;
            }
            break;
        case 8: // PRINT <index>
            const valPrint = state.vars[instr.args[0]];
            state.output.push(valPrint !== undefined ? valPrint : "undefined");
            break;
        case 9: // HALT
            state.halted = true;
            break;
        case 10: // CMP_EQ (==)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a === b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 11: // CMP_NEQ (!=)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a !== b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 12: // CMP_LT (<)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a < b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 13: // CMP_LTE (<=)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a <= b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 14: // CMP_GT (>)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a > b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 15: // CMP_GTE (>=)
            {
                const b = state.stack.pop();
                const a = state.stack.pop();
                state.stack.push(a >= b ? 1 : 0);
                highlightStack = true;
            }
            break;
        case 16: // JMP <address>
            state.pc = instr.args[0];
            updateUI(highlightStack, updatedVarIndex);
            // We do *not* increment PC here, because we already set it.
            // But the main look increments PC at the end.
            // To prevent double increment, we must modify logic or decrement it here.
            // Let's modify logic below.
            return; // Return early since we manually set PC
        case 17: // JZ <address>
            {
                const cond = state.stack.pop();
                if (cond === 0) {
                    state.pc = instr.args[0];
                    updateUI(highlightStack, updatedVarIndex);
                    return; // Jump taken
                }
                highlightStack = true; // Stack changed (pop)
            }
            break;
        case 18: // JNZ <address>
            {
                const cond = state.stack.pop();
                if (cond !== 0) {
                    state.pc = instr.args[0];
                    updateUI(highlightStack, updatedVarIndex);
                    return; // Jump taken
                }
                highlightStack = true; // Stack changed (pop)
            }
            break;
        default:
            console.warn("Unknown opcode:", instr.op);
            break;
    }

    if (!state.halted) {
        state.pc++;
    }

    updateUI(highlightStack, updatedVarIndex);
}

function run() {
    if (runInterval) return; // Already running

    // Check if we are at the end, if so reset
    if (state.halted || state.pc >= state.instructions.length) {
        reset();
    }

    // Change button text to "Pause"
    const runBtn = document.getElementById('btn-run');
    if (runBtn) runBtn.textContent = "Pause";
    if (runBtn) runBtn.onclick = stop;

    // Execute first step immediately? optional.

    runInterval = setInterval(() => {
        step();
    }, runSpeedMs);

    updateUI(); // active state update
}

function stop() {
    if (runInterval) {
        clearInterval(runInterval);
        runInterval = null;
    }

    const runBtn = document.getElementById('btn-run');
    if (runBtn) runBtn.textContent = "Run All";
    if (runBtn) runBtn.onclick = run;

    updateUI();
}
