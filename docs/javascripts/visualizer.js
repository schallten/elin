// ELIN Bytecode Visualizer - Adapted for MkDocs

const examples = {
    hello: `# Hello World in ELIN Bytecode
STR 0 Hello, World!
1 0 0 0 0
3 0
21 0
9`,
    fib: `# Fibonacci (Recursive Example)
# Simplified bytecode representation
1 0 0 0 10
3 0
# logic here...
9`,
    math: `# Math Operations
1 0 0 0 10
1 0 0 0 20
4
3 0
8 0
9`,
    loop: `# Array Loop
STR 0 Element: 
1 0 0 0 5
30 3
3 0
1 0 0 0 0
3 1
9`
};

const state = {
    lines: [],
    instructions: [],
    stringPool: {},
    arrayPool: {},
    pc: 0,
    stack: [],
    vars: {},
    callStack: [],
    halted: false,
    output: []
};

let runInterval = null;
let runSpeedMs = 600;

function reset() {
    stop();
    state.pc = 0;
    state.stack = [];
    state.vars = {};
    state.stringPool = {};
    state.arrayPool = {};
    state.callStack = [];
    state.halted = false;
    state.output = [];
    state.lastExplanation = "";
    updateUI();
}

function parseSource(source) {
    state.lines = source.split('\n');
    state.instructions = [];
    reset();

    for (let i = 0; i < state.lines.length; i++) {
        const line = state.lines[i].trim();
        if (!line || line.startsWith('#')) continue;

        if (line.startsWith('STR ')) {
            const parts = line.split(' ');
            const idx = parseInt(parts[1], 10);
            const val = parts.slice(2).join(' ');
            state.stringPool[idx] = val;
            continue;
        }

        if (line.startsWith('ARR ')) {
            const parts = line.split(' ');
            const idx = parseInt(parts[1], 10);
            const valStr = parts.slice(2).join(' ');
            const vals = valStr.split(',').filter(v => v !== "").map(v => BigInt(v));
            state.arrayPool[idx] = vals;
            continue;
        }

        const tokens = line.split(/\s+/);
        const opcode = parseInt(tokens[0], 10);

        let instruction = {
            op: opcode,
            args: [],
            lineIndex: i,
            text: line
        };

        if (opcode === 1) {
            instruction.args = [tokens.length >= 5 ? BigInt(tokens[4]) : 0n];
        } else if ([2, 3, 8, 16, 17, 18, 20, 21, 30, 31, 32, 33, 34, 40, 41, 42, 43, 66, 67].includes(opcode)) {
            instruction.args = tokens.slice(1).map(t => parseInt(t, 10));
        }

        state.instructions.push(instruction);
    }

    renderCode();
    updateUI();
}

function renderCode() {
    const container = document.getElementById('bytecode-view');
    if (!container) return;
    container.innerHTML = '';
    state.instructions.forEach((instr, idx) => {
        const div = document.createElement('div');
        div.className = 'line';
        div.id = `instr-${idx}`;
        div.onclick = () => { state.pc = idx; updateUI(); };
        div.innerHTML = `<span style="color:#888; width:30px; display:inline-block;">${idx}</span> ${instr.text}`;
        container.appendChild(div);
    });
}

function updateUI(highlightStack = false, updatedVarIndex = -1) {
    // Highlight active line
    document.querySelectorAll('.line').forEach(el => el.classList.remove('active'));
    if (!state.halted && state.pc < state.instructions.length) {
        const curr = document.getElementById(`instr-${state.pc}`);
        if (curr) {
            curr.classList.add('active');
            curr.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // Render Stack
    const stackDiv = document.getElementById('stack-view');
    if (stackDiv) {
        stackDiv.innerHTML = '';
        for (let i = state.stack.length - 1; i >= 0; i--) {
            const item = document.createElement('div');
            item.className = 'stack-item';
            const val = state.stack[i];
            item.textContent = typeof val === 'string' ? `"${val}"` : val.toString();
            if (highlightStack && i === state.stack.length - 1) item.classList.add('new');
            stackDiv.appendChild(item);
        }
        if (state.stack.length === 0) stackDiv.innerHTML = '<div style="color:#888; font-style:italic;">Empty</div>';
    }

    // Render Call Stack
    const callStackDiv = document.getElementById('callstack-view');
    if (callStackDiv) {
        callStackDiv.innerHTML = '';
        for (let i = state.callStack.length - 1; i >= 0; i--) {
            const frame = state.callStack[i];
            const item = document.createElement('div');
            item.className = 'stack-item frame';
            item.innerHTML = `<span>Frame ${i} (Ret: ${frame.returnPc})</span> <div style='font-size:0.8em'>Locals: ${JSON.stringify(frame.locals.map(v => v.toString()))}</div>`;
            callStackDiv.appendChild(item);
        }
        if (state.callStack.length === 0) callStackDiv.innerHTML = '<div style="color:#888; font-style:italic;">Top Level</div>';
    }

    // Render Variables
    const varsDiv = document.getElementById('vars-view');
    if (varsDiv) {
        varsDiv.innerHTML = '';
        for (const [idx, val] of Object.entries(state.vars)) {
            const item = document.createElement('div');
            item.className = 'var-item';
            item.textContent = `Var ${idx}: ${val.value.toString()}`;
            if (updatedVarIndex == idx) item.classList.add('updated');
            varsDiv.appendChild(item);
        }
        if (Object.keys(state.vars).length === 0) varsDiv.innerHTML = '<div style="color:#888; font-style:italic;">No variables</div>';
    }

    // Render Output
    const outputDiv = document.getElementById('output-view');
    if (outputDiv) {
        outputDiv.textContent = state.output.join('\n');
    }
}

function getExplanation(instr) {
    if (!instr) return "End of program";
    switch (instr.op) {
        case 1: return `<strong>PUSH</strong> numeric value <span style="font-weight:bold">${instr.args[0]}</span> onto the stack.`;
        case 2: return `<strong>LOAD</strong> Retrieve value from variable Index ${instr.args[0]} and push to stack.`;
        case 3: return `<strong>STORE</strong> Pop top value from stack and store into variable Index ${instr.args[0]}.`;
        case 4: return `<strong>ADD</strong> Pop top two values, add them, and push the result.`;
        case 8: return `<strong>PRINT</strong> Output value of variable Index ${instr.args[0]} to console.`;
        case 9: return `<strong>HALT</strong> Stop execution.`;
        case 20:
            const s = state.stringPool[instr.args[0]] || "";
            return `<strong>PUSH_STR</strong> index ${instr.args[0]} ("${s}").`;
        case 16: return `<strong>JMP</strong> Jump to instruction at index ${instr.args[0]}.`;
        case 17: return `<strong>JZ</strong> Pop value. If 0, jump to index ${instr.args[0]}.`;
        case 18: return `<strong>JNZ</strong> Pop value. If !0, jump to index ${instr.args[0]}.`;
        case 30: return `<strong>MAKE_ARR</strong> Create array of size ${instr.args[0]} from stack.`;
        case 31: return `<strong>ARR_GET</strong> Get value from array at index.`;
        case 32: return `<strong>ARR_SET</strong> Set value in array at index.`;
        case 33: return `<strong>ARR_LEN</strong> Pushes array length to stack.`;
        case 34: return `<strong>PUSH_ARR</strong> Push array pool index ${instr.args[0]} to stack.`;
        case 40: return `<strong>CALL</strong> Jump to ${instr.args[0]} and push frame with ${instr.args[1]} args.`;
        case 41: return `<strong>RET</strong> Pop frame and return with top stack value.`;
        case 42: return `<strong>LOAD_LOCAL</strong> Retrieve local variable Index ${instr.args[0]}.`;
        case 43: return `<strong>STORE_LOCAL</strong> Save value to local variable Index ${instr.args[0]}.`;
        case 55: return `<strong>MOD</strong> Pop b, pop a, push a % b.`;
        case 56: return `<strong>ABS</strong> Pop value, push its absolute value.`;
        case 60: return `<strong>DUP</strong> Duplicate the top value on the stack.`;
        case 61: return `<strong>DROP</strong> Discard the top value on the stack.`;
        case 62: return `<strong>SWAP</strong> Exchange the top two stack values.`;
        case 63: return `<strong>NEG</strong> Negate the top value (a -> -a).`;
        case 64: return `<strong>NOT</strong> Logical NOT (0 -> 1, else 0).`;
        case 66: return `<strong>INC</strong> Increment variable Index ${instr.args[0]} by 1.`;
        case 67: return `<strong>DEC</strong> Decrement variable Index ${instr.args[0]} by 1.`;
        case 68: return `<strong>INPUT</strong> Read integer from stdin.`;
        case 69: return `<strong>READ</strong> Read line to string pool.`;
        case 70: return `<strong>WRITE</strong> Print string handle without newline.`;
        case 71: return `<strong>FLUSH</strong> Flush stdout.`;
        case 72: return `<strong>STRLEN</strong> Push length of string handle.`;
        case 73: return `<strong>STRCAT</strong> Concatenate two string handles.`;
        case 74: return `<strong>SUBSTR</strong> Extract substring from handle.`;
        case 75: return `<strong>STRCMP</strong> Compare two string handles.`;
        case 76: return `<strong>FOPEN</strong> Open file, push fd.`;
        case 77: return `<strong>FREAD</strong> Read line from fd.`;
        case 78: return `<strong>FWRITE</strong> Write string to fd.`;
        case 79: return `<strong>FCLOSE</strong> Close fd.`;
        case 80: return `<strong>TIME</strong> Push ms since boot.`;
        case 81: return `<strong>DELAY</strong> Sleep for N ms.`;
        case 82: return `<strong>RTC_READ</strong> Read RTC memory.`;
        case 83: return `<strong>RTC_WRITE</strong> Write RTC memory.`;
        case 90: return `<strong>TRACE</strong> Toggle debug trace mode.`;
        default: return `<strong>OP ${instr.op}</strong> Executing internal instruction.`;
    }
}

function step() {
    if (state.halted || state.pc >= state.instructions.length) return stop();

    const instr = state.instructions[state.pc];
    state.lastExplanation = getExplanation(instr);
    let highlightStack = false;
    let updatedVarIndex = -1;

    switch (instr.op) {
        case 1: // PUSH
            state.stack.push(instr.args[0]);
            highlightStack = true;
            break;
        case 20: // PUSH_STR
            state.stack.push(BigInt(instr.args[0]));
            highlightStack = true;
            break;
        case 2: // LOAD
            const v = state.vars[instr.args[0]];
            state.stack.push(v ? v.value : 0n);
            highlightStack = true;
            break;
        case 3: // STORE
            const val = state.stack.pop();
            state.vars[instr.args[0]] = { value: val, isString: typeof val === 'string' };
            updatedVarIndex = instr.args[0];
            break;
        case 4: // ADD
            const b = state.stack.pop();
            const a = state.stack.pop();
            state.stack.push(a + b);
            highlightStack = true;
            break;
        case 8: // PRINT
            const p = state.vars[instr.args[0]];
            state.output.push(p ? p.value.toString() : "0");
            break;
        case 21: // PRINT_STR
            const ps = state.vars[instr.args[0]];
            if (ps) {
                const strIdx = Number(ps.value);
                state.output.push(state.stringPool[strIdx] || "");
            }
            break;
        case 9: state.halted = true; break;
        case 16: state.pc = instr.args[0]; return updateUI();
        case 17: // JZ
            if (state.stack.pop() === 0n) { state.pc = instr.args[0]; return updateUI(); }
            break;
        case 18: // JNZ
            if (state.stack.pop() !== 0n) { state.pc = instr.args[0]; return updateUI(); }
            break;
        case 30: // MAKE_ARR
            const n = instr.args[0];
            const arr = [];
            for (let i = 0; i < n; i++) arr.push(state.stack.pop());
            arr.reverse();
            const newIdx = Object.keys(state.arrayPool).length;
            state.arrayPool[newIdx] = arr;
            state.stack.push(BigInt(newIdx));
            highlightStack = true;
            break;
        case 31: // ARR_GET
            const idxGet = Number(state.stack.pop());
            const refGet = Number(state.stack.pop());
            const arrayGet = state.arrayPool[refGet];
            state.stack.push(arrayGet ? arrayGet[idxGet] : 0n);
            highlightStack = true;
            break;
        case 32: // ARR_SET
            const valSet = state.stack.pop();
            const idxSet = Number(state.stack.pop());
            const refSet = Number(state.stack.pop());
            if (state.arrayPool[refSet]) state.arrayPool[refSet][idxSet] = valSet;
            break;
        case 33: // ARR_LEN
            const refLen = Number(state.stack.pop());
            state.stack.push(state.arrayPool[refLen] ? BigInt(state.arrayPool[refLen].length) : 0n);
            highlightStack = true;
            break;
        case 34: // PUSH_ARR
            state.stack.push(BigInt(instr.args[0]));
            highlightStack = true;
            break;
        case 40: // CALL
            const addr = instr.args[0];
            const argc = instr.args[1];
            const frame = { returnPc: state.pc, locals: [] };
            for (let i = 0; i < argc; i++) frame.locals.push(state.stack.pop());
            frame.locals.reverse();
            state.callStack.push(frame);
            state.pc = addr;
            return updateUI();
        case 41: // RET
            const retVal = state.stack.length > 0 ? state.stack.pop() : 0n;
            const poppedFrame = state.callStack.pop();
            if (poppedFrame) {
                state.pc = poppedFrame.returnPc;
                state.stack.push(retVal);
                highlightStack = true;
            } else {
                state.halted = true;
            }
            break;
        case 42: // LOAD_LOCAL
            const curFrameIdx = state.callStack.length - 1;
            if (curFrameIdx >= 0) {
                const lval = state.callStack[curFrameIdx].locals[instr.args[0]];
                state.stack.push(lval !== undefined ? lval : 0n);
                highlightStack = true;
            }
            break;
        case 43: // STORE_LOCAL
            const curFrameIdxSt = state.callStack.length - 1;
            if (curFrameIdxSt >= 0) {
                const valSt = state.stack.pop();
                state.callStack[curFrameIdxSt].locals[instr.args[0]] = valSt;
            }
            break;
        case 55: { // MOD
            const b = state.stack.pop();
            const a = state.stack.pop();
            state.stack.push(b !== 0n ? a % b : 0n);
            highlightStack = true;
            break;
        }
        case 56: { // ABS
            const a = state.stack.pop();
            state.stack.push(a < 0n ? -a : a);
            highlightStack = true;
            break;
        }
        case 60: { // DUP
            const val = state.stack[state.stack.length - 1];
            state.stack.push(val !== undefined ? val : 0n);
            highlightStack = true;
            break;
        }
        case 61: // DROP
            state.stack.pop();
            break;
        case 62: { // SWAP
            const a = state.stack.pop();
            const b = state.stack.pop();
            state.stack.push(a);
            state.stack.push(b);
            highlightStack = true;
            break;
        }
        case 63: { // NEG
            const a = state.stack.pop();
            state.stack.push(-a);
            highlightStack = true;
            break;
        }
        case 64: { // NOT
            const a = state.stack.pop();
            state.stack.push(a === 0n ? 1n : 0n);
            highlightStack = true;
            break;
        }
        case 66: { // INC
            const idx = instr.args[0];
            const v = state.vars[idx];
            state.vars[idx] = { value: (v ? v.value : 0n) + 1n, isString: false };
            break;
        }
        case 67: { // DEC
            const idx = instr.args[0];
            const v = state.vars[idx];
            state.vars[idx] = { value: (v ? v.value : 0n) - 1n, isString: false };
            break;
        }
        case 68: { // INPUT
            const val = prompt("Enter an integer:");
            state.stack.push(BigInt(val || 0));
            highlightStack = true;
            break;
        }
        case 69: { // READ
            const val = prompt("Enter a string:");
            const idx = Object.keys(state.stringPool).length;
            state.stringPool[idx] = val || "";
            state.stack.push(BigInt(idx));
            highlightStack = true;
            break;
        }
        case 70: { // WRITE
            const sIdx = Number(state.stack.pop());
            state.output.push(state.stringPool[sIdx] || "");
            break;
        }
        case 71: // FLUSH
            break;
        case 72: { // STRLEN
            const sIdx = Number(state.stack.pop());
            const s = state.stringPool[sIdx] || "";
            state.stack.push(BigInt(s.length));
            highlightStack = true;
            break;
        }
        case 73: { // STRCAT
            const bIdx = Number(state.stack.pop());
            const aIdx = Number(state.stack.pop());
            const sA = state.stringPool[aIdx] || "";
            const sB = state.stringPool[bIdx] || "";
            const newIdx = Object.keys(state.stringPool).length;
            state.stringPool[newIdx] = sA + sB;
            state.stack.push(BigInt(newIdx));
            highlightStack = true;
            break;
        }
        case 74: { // SUBSTR
            const len = Number(state.stack.pop());
            const off = Number(state.stack.pop());
            const sIdx = Number(state.stack.pop());
            const s = state.stringPool[sIdx] || "";
            const sub = s.substring(off, off + len);
            const newIdx = Object.keys(state.stringPool).length;
            state.stringPool[newIdx] = sub;
            state.stack.push(BigInt(newIdx));
            highlightStack = true;
            break;
        }
        case 75: { // STRCMP
            const bIdx = Number(state.stack.pop());
            const aIdx = Number(state.stack.pop());
            const sA = state.stringPool[aIdx] || "";
            const sB = state.stringPool[bIdx] || "";
            let res = 0n;
            if (sA < sB) res = -1n;
            else if (sA > sB) res = 1n;
            state.stack.push(res);
            highlightStack = true;
            break;
        }
        case 76: // FOPEN (stub)
            state.stack.pop();
            state.stack.push(0n);
            highlightStack = true;
            break;
        case 77: // FREAD (stub)
            state.stack.pop();
            state.stack.push(0n);
            highlightStack = true;
            break;
        case 78: // FWRITE (stub)
            state.stack.pop();
            state.stack.pop();
            break;
        case 79: // FCLOSE (stub)
            state.stack.pop();
            break;
        case 80: // TIME
            state.stack.push(BigInt(Date.now()));
            highlightStack = true;
            break;
        case 81: // DELAY (stub)
            state.stack.pop();
            break;
        case 82: // RTC_READ (stub)
            state.stack.push(0n);
            highlightStack = true;
            break;
        case 83: // RTC_WRITE (stub)
            state.stack.pop();
            break;
        case 90: // TRACE
            break;
    }
    state.pc++;
    updateUI(highlightStack, updatedVarIndex);
}

function run() {
    if (runInterval) return;
    if (state.halted || state.pc >= state.instructions.length) reset();

    const runBtn = document.getElementById('btn-run');
    if (runBtn) runBtn.textContent = "Pause";
    if (runBtn) runBtn.onclick = stop;

    runInterval = setInterval(step, runSpeedMs);
    updateUI();
}

function stop() {
    if (runInterval) {
        clearInterval(runInterval);
        runInterval = null;
    }
    const runBtn = document.getElementById('btn-run');
    if (runBtn) runBtn.textContent = "Run";
    if (runBtn) runBtn.onclick = run;
    updateUI();
}

function loadExample(key) {
    if (!key || !examples[key]) return;
    const input = document.getElementById('source-input');
    if (input) {
        input.value = examples[key];
        parseSource(examples[key]);
    }
}

function loadFromInput() {
    const src = document.getElementById('source-input');
    if (src && src.value) parseSource(src.value);
}

function updateSpeed(val) {
    runSpeedMs = parseInt(val, 10);
    if (runInterval) {
        stop();
        run();
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('btn-load');
    const exampleBtn = document.getElementById('btn-example');
    const stepBtn = document.getElementById('btn-step');
    const runBtn = document.getElementById('btn-run');
    const resetBtn = document.getElementById('btn-reset');
    const speedSlider = document.getElementById('speed-slider');
    const fileInput = document.getElementById('file-input');
    const sourceInput = document.getElementById('source-input');

    if (loadBtn && fileInput) {
        loadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    if (sourceInput) sourceInput.value = ev.target.result;
                    parseSource(ev.target.result);
                };
                reader.readAsText(file);
            }
        });
    }

    if (exampleBtn) {
        exampleBtn.addEventListener('click', () => {
            const examplesList = Object.keys(examples);
            const randomExample = examplesList[Math.floor(Math.random() * examplesList.length)];
            loadExample(randomExample);
        });
    }

    if (stepBtn) stepBtn.addEventListener('click', step);
    if (runBtn) runBtn.addEventListener('click', run);
    if (resetBtn) resetBtn.addEventListener('click', reset);
    if (speedSlider) speedSlider.addEventListener('input', (e) => updateSpeed(e.target.value));
    if (sourceInput) sourceInput.addEventListener('input', loadFromInput);
});
