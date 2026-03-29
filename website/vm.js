
const state = {
    lines: [],        // Raw source lines
    instructions: [], // Parsed instructions { op, args, originalLineIndex }
    stringPool: {},   // index -> string
    pc: 0,            // Program Counter
    stack: [],        // values (BigInt or String)
    vars: {},         // index -> { value, isString }
    halted: false,
    output: []
};

function reset() {
    stop();
    state.pc = 0;
    state.stack = [];
    state.vars = {};
    state.stringPool = {};
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

        const tokens = line.split(/\s+/);
        const opcode = parseInt(tokens[0], 10);

        let instruction = {
            op: opcode,
            args: [],
            lineIndex: i,
            text: line
        };

        if (opcode === 1) { // PUSH
            instruction.args = [tokens.length >= 5 ? BigInt(tokens[4]) : 0n];
        } else if ([2, 3, 8, 16, 17, 18, 20].includes(opcode)) {
            // LOAD, STORE, PRINT, JMP, JZ, JNZ, PUSH_STR
            instruction.args = [parseInt(tokens[1], 10)];
        }

        state.instructions.push(instruction);
    }

    document.getElementById('visualizer').style.display = 'block';
    renderCode();
    updateUI();
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
    const stackDiv = document.getElementById('stack-display');
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

    // Render Vars
    const varsDiv = document.getElementById('vars-display');
    varsDiv.innerHTML = '';
    Object.keys(state.vars).forEach(key => {
        const row = document.createElement('div');
        row.className = 'var-row';
        if (parseInt(key) === updatedVarIndex) row.classList.add('updated');
        const v = state.vars[key];
        const displayVal = v.isString ? `"${v.value}"` : v.value.toString();
        row.innerHTML = `<span>Idx ${key}</span><span>${displayVal}</span>`;
        varsDiv.appendChild(row);
    });

    document.getElementById('console-output').textContent = state.output.join('\n');
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
            state.stack.push(state.stringPool[instr.args[0]] || "");
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
            state.output.push(p ? p.value.toString() : "undefined");
            break;
        case 9: state.halted = true; break;
        case 16: state.pc = instr.args[0]; return updateUI();
        case 17: // JZ
            if (state.stack.pop() === 0n) { state.pc = instr.args[0]; return updateUI(); }
            break;
        case 18: // JNZ
            if (state.stack.pop() !== 0n) { state.pc = instr.args[0]; return updateUI(); }
            break;
    }
    state.pc++;
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
