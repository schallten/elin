#include <bits/stdc++.h>
#include <sstream>
#include <fstream>
#include <unordered_map>
using namespace std;
typedef long long ll;

vector<pair<int, string>>
    bytecode_program; // int stores index , string stores the instruction
vector<ll> variables;
vector<string> string_pool;      // Store string literals from pool
vector<ll> constant_pool;        // Store integer constants
vector<vector<ll>> array_pool;   // Store array literals/templates
stack<ll> eval_stack;          // Use ll to store indices/values

struct Frame {
  int return_pc;
  vector<ll> locals;
};
stack<Frame> call_stack;

// defintion of all integers
const int PUSH = 1;
const int LOAD = 2;
const int STORE = 3;
const int ADD = 4;
const int SUB = 5;
const int MUL = 6;
const int DIV = 7;
const int PRINT = 8;
const int HALT = 9;
const int CMP_EQ = 10;
const int CMP_NEQ = 11;
const int CMP_LT = 12;
const int CMP_LTE = 13;
const int CMP_GT = 14;
const int CMP_GTE = 15;
const int JMP = 16;
const int JZ = 17;
const int JNZ = 18;
const int PUSH_STR = 20;
const int PRINT_STR = 21;
const int PUSH_CONST = 22;
const int MAKE_ARR = 30;
const int ARR_GET = 31;
const int ARR_SET = 32;
const int ARR_LEN = 33;
const int PUSH_ARR = 34;
const int CALL = 40;
const int RET = 41;
const int LOAD_LOCAL = 42;
const int STORE_LOCAL = 43;
const int DUP = 60;
const int DROP = 61;
const int SWAP = 62;
const int NEG = 63;
const int NOT = 64;
const int NOP = 65;
const int INC = 66;
const int DEC = 67;
const int MOD = 55;
const int ABS = 56;
const int INPUT = 68;
const int READ = 69;
const int WRITE = 70;
const int FLUSH = 71;
const int STRLEN = 72;
const int STRCAT = 73;
const int SUBSTR = 74;
const int STRCMP = 75;
const int FOPEN = 76;
const int FREAD = 77;
const int FWRITE = 78;
const int FCLOSE = 79;
const int TIME = 80;
const int DELAY = 81;
const int RTC_READ = 82;
const int RTC_WRITE = 83;
const int RAND_OP = 84;
const int SRAND_OP = 85;
const int CALL_EXTERN_OP = 86;
const int TRACE = 90;

// --- Bump Allocator Opcodes (Item M1) ---
const int ALLOC_OP = 44;    // Allocate cells on heap, push handle
const int FREE_OP = 45;     // Invalidate a handle
const int LOAD_H_OP = 46;   // Read from heap via handle + index
const int STORE_H_OP = 47;  // Write to heap via handle + index
const int HEAP_LEN_OP = 48; // Push the size of a handle's block

#include <random>
static mt19937_64 rng(random_device{}());

bool debug_mode = false;
auto vm_boot_time = chrono::steady_clock::now();

// --- File I/O state ---
static unordered_map<ll, fstream*> open_files;
static ll next_fd = 1;

// --- FFI Registry (Item 17) ---
typedef ll (*ExternFn)(vector<ll>&);
static vector<ExternFn> extern_registry;

static ll extern_add(vector<ll>& args) {
  ll a = args.size() > 0 ? args[0] : 0;
  ll b = args.size() > 1 ? args[1] : 0;
  return a + b;
}

static ll extern_sub(vector<ll>& args) {
  ll a = args.size() > 0 ? args[0] : 0;
  ll b = args.size() > 1 ? args[1] : 0;
  return a - b;
}

static ll extern_mul(vector<ll>& args) {
  ll a = args.size() > 0 ? args[0] : 0;
  ll b = args.size() > 1 ? args[1] : 0;
  return a * b;
}

static ll extern_div(vector<ll>& args) {
  ll a = args.size() > 0 ? args[0] : 0;
  ll b = args.size() > 1 ? args[1] : 1;
  return b != 0 ? a / b : 0;
}

static void register_externals() {
  extern_registry.push_back(extern_add);  // 0
  extern_registry.push_back(extern_sub);  // 1
  extern_registry.push_back(extern_mul);  // 2
  extern_registry.push_back(extern_div);  // 3
}

// --- Bump Allocator (Item M1) ---
//
// The heap is one big flat array of ll values. When ELIN asks for N cells,
// we carve out N slots starting at the bump pointer and move the pointer forward.
//
// Each allocation gets a "handle" — just an integer ID. The handle table maps
// that ID to where the allocation lives in the heap, how big it is, and whether
// it's still valid.
//
// When you FREE a handle, we mark it invalid and add its ID to the free list.
// The next ALLOC reuses that ID. The actual memory stays where it is — the bump
// pointer never moves backward.
//
// This is dead simple: no splitting, no coalescing, no碎片. It just works.

static const ll HEAP_SIZE = 65536;        // 64K cells — plenty for now
static ll heap[HEAP_SIZE];                // the actual memory
static ll bump_ptr = 0;                   // next free slot in the heap

struct Handle {
  ll offset;     // where this handle's data starts in the heap
  ll size;       // how many cells it owns
  bool valid;    // false after FREE
};

static const ll MAX_HANDLES = 4096;
static Handle handle_table[MAX_HANDLES];
static ll next_handle = 1;                // handle 0 is reserved (null handle)
static vector<ll> free_list;              // IDs we can reuse

// allocate(size) -> handle
// Grabs N cells from the heap and returns an ID you can use to read/write them.
// Returns 0 (null handle) if the heap is full.
static ll heap_alloc(ll size) {
  // Not enough room? Bail out.
  if (bump_ptr + size > HEAP_SIZE) {
    return 0;
  }

  // Pick a handle ID — reuse one from the free list if available
  ll id;
  if (!free_list.empty()) {
    id = free_list.back();
    free_list.pop_back();
  } else {
    id = next_handle++;
    if (id >= MAX_HANDLES) return 0;
  }

  // Record where this allocation lives
  handle_table[id].offset = bump_ptr;
  handle_table[id].size = size;
  handle_table[id].valid = true;

  // Move the bump pointer past this allocation
  bump_ptr += size;

  return id;
}

// free(handle)
// Marks a handle as invalid so its slot can be reused later.
// The memory isn't actually zeroed or returned — the bump pointer only goes forward.
static void heap_free(ll id) {
  if (id <= 0 || id >= next_handle) return;
  if (!handle_table[id].valid) {
    cout << "[VM ERROR] Double free on handle " << id << "\n";
    return;
  }
  handle_table[id].valid = false;
  free_list.push_back(id);
}

// load_h(handle, index) -> value
// Reads one cell from inside a handle's block. Checks that the handle is valid
// and the index is within bounds before reading.
static ll heap_load(ll id, ll index) {
  if (id <= 0 || id >= next_handle || !handle_table[id].valid) {
    cout << "[VM ERROR] Use-after-free or invalid handle " << id << "\n";
    return 0;
  }
  if (index < 0 || index >= handle_table[id].size) {
    cout << "[VM ERROR] Out-of-bounds access on handle " << id
         << " (index " << index << ", size " << handle_table[id].size << ")\n";
    return 0;
  }
  return heap[handle_table[id].offset + index];
}

// store_h(handle, index, value)
// Writes one cell into a handle's block. Same safety checks as load.
static void heap_store(ll id, ll index, ll value) {
  if (id <= 0 || id >= next_handle || !handle_table[id].valid) {
    cout << "[VM ERROR] Use-after-free or invalid handle " << id << "\n";
    return;
  }
  if (index < 0 || index >= handle_table[id].size) {
    cout << "[VM ERROR] Out-of-bounds write on handle " << id
         << " (index " << index << ", size " << handle_table[id].size << ")\n";
    return;
  }
  heap[handle_table[id].offset + index] = value;
}

class Printer {
public:
  void print(ll value) { cout << value << "\n"; }
  void print_str(const string &message) { cout << message << "\n"; }
  void print_debug(const string &label, ll value) {
    cout << "[DEBUG] " << label << ": " << value << "\n";
  }
};

Printer printer;

bool is_comment(const string &line) {
  size_t start = line.find_first_not_of(" \t\r\n");
  return (start == string::npos || line[start] == '#');
}

void execute() {
  int pc = 0;
  while (pc < bytecode_program.size()) {
    string instruction_line = bytecode_program[pc].second;
    if (is_comment(instruction_line)) {
      pc++;
      continue;
    }

    istringstream iss(instruction_line);
    vector<ll> tokens;
    ll token;
    while (iss >> token) {
      tokens.push_back(token);
    }

    if (tokens.empty()) {
      pc++;
      continue;
    }

    int opcode = (int)tokens[0];

    if (debug_mode && opcode != TRACE) {
      cerr << "[TRACE] PC=" << pc << " OP=" << instruction_line;
      cerr << " | STACK=[";
      stack<ll> tmp = eval_stack;
      vector<ll> sv;
      while (!tmp.empty()) { sv.push_back(tmp.top()); tmp.pop(); }
      reverse(sv.begin(), sv.end());
      for (size_t i = 0; i < sv.size(); i++) {
        if (i) cerr << ",";
        cerr << sv[i];
      }
      cerr << "]";
      if (!call_stack.empty())
        cerr << " FRAME_DEPTH=" << call_stack.size();
      cerr << "\n";
    }

    switch (opcode) {
    case PUSH: {
      eval_stack.push(tokens[4]);
      break;
    }
    case PUSH_STR: {
      eval_stack.push(tokens[1]); // Push string index
      break;
    }
    case LOAD: {
      int var_index = (int)tokens[1];
      if (var_index < variables.size()) {
        eval_stack.push(variables[var_index]);
      } else {
        printer.print_debug("Variable not found", var_index);
      }
      break;
    }
    case STORE: {
      int var_index = (int)tokens[1];
      if (!eval_stack.empty()) {
        ll value = eval_stack.top();
        eval_stack.pop();
        if (var_index >= variables.size()) {
          variables.resize(var_index + 1, 0);
        }
        variables[var_index] = value;
      }
      break;
    }
    case ADD: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a + b);
      }
      break;
    }
    case SUB: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a - b);
      }
      break;
    }
    case MUL: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a * b);
      }
      break;
    }
    case DIV: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        if (b != 0)
          eval_stack.push(a / b);
        else
          printer.print_str("Error: Division by zero");
      }
      break;
    }
    case MOD: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        if (b != 0)
          eval_stack.push(a % b);
        else
          printer.print_str("Error: Modulo by zero");
      }
      break;
    }
    case ABS: {
      if (!eval_stack.empty()) {
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a < 0 ? -a : a);
      }
      break;
    }
    case PRINT: {
      if (!eval_stack.empty()) {
        ll value = eval_stack.top();
        eval_stack.pop();
        printer.print(value);
      }
      break;
    }
    case PRINT_STR: {
      if (!eval_stack.empty()) {
        ll str_idx = eval_stack.top();
        eval_stack.pop();
        if (str_idx >= 0 && str_idx < (ll)string_pool.size()) {
          printer.print_str(string_pool[str_idx]);
        } else {
          printer.print_debug("Invalid string pool index", str_idx);
        }
      }
      break;
    }
    case INPUT: {
      ll val;
      cin >> val;
      eval_stack.push(val);
      break;
    }
    case READ: {
      string input_line;
      getline(cin, input_line);
      string_pool.push_back(input_line);
      eval_stack.push((ll)string_pool.size() - 1);
      break;
    }
    case WRITE: {
      if (!eval_stack.empty()) {
        ll str_idx = eval_stack.top();
        eval_stack.pop();
        if (str_idx >= 0 && str_idx < (ll)string_pool.size()) {
          cout << string_pool[str_idx];
        } else {
          printer.print_debug("Invalid string pool index", str_idx);
        }
      }
      break;
    }
    case FLUSH: {
      cout.flush();
      break;
    }
    case STRLEN: {
      if (!eval_stack.empty()) {
        ll str_idx = eval_stack.top();
        eval_stack.pop();
        if (str_idx >= 0 && str_idx < (ll)string_pool.size()) {
          eval_stack.push((ll)string_pool[str_idx].size());
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case STRCAT: {
      if (eval_stack.size() >= 2) {
        ll b_idx = eval_stack.top(); eval_stack.pop();
        ll a_idx = eval_stack.top(); eval_stack.pop();
        if (a_idx >= 0 && a_idx < (ll)string_pool.size() &&
            b_idx >= 0 && b_idx < (ll)string_pool.size()) {
          string_pool.push_back(string_pool[a_idx] + string_pool[b_idx]);
          eval_stack.push((ll)string_pool.size() - 1);
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case SUBSTR: {
      if (eval_stack.size() >= 3) {
        ll len = eval_stack.top(); eval_stack.pop();
        ll off = eval_stack.top(); eval_stack.pop();
        ll str_idx = eval_stack.top(); eval_stack.pop();
        if (str_idx >= 0 && str_idx < (ll)string_pool.size()) {
          string s = string_pool[str_idx];
          if (off < 0) off = 0;
          if (off > (ll)s.size()) off = (ll)s.size();
          if (len < 0) len = 0;
          if (off + len > (ll)s.size()) len = (ll)s.size() - off;
          string_pool.push_back(s.substr(off, len));
          eval_stack.push((ll)string_pool.size() - 1);
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case STRCMP: {
      if (eval_stack.size() >= 2) {
        ll b_idx = eval_stack.top(); eval_stack.pop();
        ll a_idx = eval_stack.top(); eval_stack.pop();
        if (a_idx >= 0 && a_idx < (ll)string_pool.size() &&
            b_idx >= 0 && b_idx < (ll)string_pool.size()) {
          string &a = string_pool[a_idx];
          string &b = string_pool[b_idx];
          if (a < b) eval_stack.push(-1);
          else if (a > b) eval_stack.push(1);
          else eval_stack.push(0);
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case TIME: {
      auto now = chrono::steady_clock::now();
      ll ms = chrono::duration_cast<chrono::milliseconds>(now - vm_boot_time).count();
      eval_stack.push(ms);
      break;
    }
    case DELAY: {
      if (!eval_stack.empty()) {
        ll ms = eval_stack.top();
        eval_stack.pop();
        if (ms > 0) {
          this_thread::sleep_for(chrono::milliseconds(ms));
        }
      }
      break;
    }
    case RTC_READ: {
      eval_stack.push(0); // PC no-op
      break;
    }
    case RTC_WRITE: {
      if (!eval_stack.empty()) {
        eval_stack.pop(); // PC no-op
      }
      break;
    }
    case FOPEN: {
      if (eval_stack.empty()) { printer.print_str("Error: FOPEN requires path handle"); break; }
      ll path_idx = eval_stack.top(); eval_stack.pop();
      if (path_idx < 0 || path_idx >= (ll)string_pool.size()) {
        printer.print_str("Error: Invalid string index for FOPEN");
        eval_stack.push(0);
        break;
      }
      string path = string_pool[path_idx];
      fstream* fs = new fstream();
      fs->open(path, ios::in | ios::out | ios::app);
      if (!fs->is_open()) {
        // Try creating the file first
        ofstream create_f(path);
        create_f.close();
        fs->open(path, ios::in | ios::out | ios::app);
      }
      if (!fs->is_open()) {
        printer.print_str("Error: Unable to open file");
        delete fs;
        eval_stack.push(0);
        break;
      }
      ll fd = next_fd++;
      open_files[fd] = fs;
      eval_stack.push(fd);
      break;
    }
    case FREAD: {
      if (eval_stack.empty()) { printer.print_str("Error: FREAD requires fd"); break; }
      ll fd = eval_stack.top(); eval_stack.pop();
      auto it = open_files.find(fd);
      if (it == open_files.end()) {
        printer.print_str("Error: Invalid fd for FREAD");
        eval_stack.push(0);
        break;
      }
      fstream* fs = it->second;
      fs->clear();
      fs->seekg(0);
      string content((istreambuf_iterator<char>(*fs)), istreambuf_iterator<char>());
      string_pool.push_back(content);
      eval_stack.push((ll)string_pool.size() - 1);
      break;
    }
    case FWRITE: {
      if (eval_stack.size() < 2) { printer.print_str("Error: FWRITE requires fd and string handle"); break; }
      ll str_idx = eval_stack.top(); eval_stack.pop();
      ll fd = eval_stack.top(); eval_stack.pop();
      auto it = open_files.find(fd);
      if (it == open_files.end()) {
        printer.print_str("Error: Invalid fd for FWRITE");
        break;
      }
      if (str_idx < 0 || str_idx >= (ll)string_pool.size()) {
        printer.print_str("Error: Invalid string index for FWRITE");
        break;
      }
      *(it->second) << string_pool[str_idx];
      it->second->flush();
      break;
    }
    case FCLOSE: {
      if (eval_stack.empty()) { printer.print_str("Error: FCLOSE requires fd"); break; }
      ll fd = eval_stack.top(); eval_stack.pop();
      auto it = open_files.find(fd);
      if (it != open_files.end()) {
        it->second->close();
        delete it->second;
        open_files.erase(it);
      } else {
        printer.print_str("Error: Invalid fd for FCLOSE");
      }
      break;
    }
    case RAND_OP: {
      eval_stack.push((ll)rng());
      break;
    }
    case SRAND_OP: {
      if (!eval_stack.empty()) {
        ll seed = eval_stack.top();
        eval_stack.pop();
        rng.seed((unsigned long long)seed);
      }
      break;
    }
    case CALL_EXTERN_OP: {
      int func_id = (int)tokens[1];
      int argc = (int)tokens[2];
      vector<ll> args;
      for (int i = 0; i < argc; i++) {
        if (!eval_stack.empty()) {
          args.push_back(eval_stack.top());
          eval_stack.pop();
        }
      }
      reverse(args.begin(), args.end());
      if (func_id >= 0 && func_id < (int)extern_registry.size()) {
        ll result = extern_registry[func_id](args);
        eval_stack.push(result);
      } else {
        printer.print_debug("Invalid extern function ID", func_id);
        eval_stack.push(0);
      }
      break;
    }
    // --- Bump Allocator Opcodes (Item M1) ---
    case ALLOC_OP: {
      // Pop size from stack, allocate that many cells, push the handle
      if (!eval_stack.empty()) {
        ll size = eval_stack.top();
        eval_stack.pop();
        if (size <= 0) {
          printer.print_str("[VM ERROR] ALLOC size must be > 0");
          eval_stack.push(0);
        } else {
          ll handle = heap_alloc(size);
          eval_stack.push(handle);
        }
      }
      break;
    }
    case FREE_OP: {
      // Pop handle from stack, invalidate it
      if (!eval_stack.empty()) {
        ll handle = eval_stack.top();
        eval_stack.pop();
        heap_free(handle);
      }
      break;
    }
    case LOAD_H_OP: {
      // Pop index and handle, push heap[handle][index]
      if (eval_stack.size() >= 2) {
        ll index = eval_stack.top(); eval_stack.pop();
        ll handle = eval_stack.top(); eval_stack.pop();
        ll value = heap_load(handle, index);
        eval_stack.push(value);
      }
      break;
    }
    case STORE_H_OP: {
      // Pop value, index, and handle → set heap[handle][index] = value
      if (eval_stack.size() >= 3) {
        ll value  = eval_stack.top(); eval_stack.pop();
        ll index  = eval_stack.top(); eval_stack.pop();
        ll handle = eval_stack.top(); eval_stack.pop();
        heap_store(handle, index, value);
      }
      break;
    }
    case HEAP_LEN_OP: {
      // Pop handle, push its size
      if (!eval_stack.empty()) {
        ll handle = eval_stack.top();
        eval_stack.pop();
        if (handle > 0 && handle < next_handle && handle_table[handle].valid) {
          eval_stack.push(handle_table[handle].size);
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case TRACE: {
      debug_mode = !debug_mode;
      printer.print_str(debug_mode ? "[TRACE] Enabled" : "[TRACE] Disabled");
      break;
    }
    case HALT:
      return;
    case CMP_EQ: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a == b ? 1 : 0);
      }
      break;
    }
    case CMP_NEQ: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a != b ? 1 : 0);
      }
      break;
    }
    case CMP_LT: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a < b ? 1 : 0);
      }
      break;
    }
    case CMP_GT: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a > b ? 1 : 0);
      }
      break;
    }
    case CMP_LTE: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a <= b ? 1 : 0);
      }
      break;
    }
    case CMP_GTE: {
      if (eval_stack.size() >= 2) {
        ll b = eval_stack.top();
        eval_stack.pop();
        ll a = eval_stack.top();
        eval_stack.pop();
        eval_stack.push(a >= b ? 1 : 0);
      }
      break;
    }
    case JMP: {
      pc = (int)tokens[1];
      pc--;
      break;
    }
    case JZ: {
      int address = (int)tokens[1];
      if (!eval_stack.empty()) {
        ll value = eval_stack.top();
        eval_stack.pop();
        if (value == 0) {
          pc = address;
          pc--;
        }
      }
      break;
    }
    case JNZ: {
      int address = (int)tokens[1];
      if (!eval_stack.empty()) {
        ll value = eval_stack.top();
        eval_stack.pop();
        if (value != 0) {
          pc = address;
          pc--;
        }
      }
      break;
    }
    case MAKE_ARR: {
      int n = (int)tokens[1];
      vector<ll> arr;
      for (int i = 0; i < n; i++) {
        if (!eval_stack.empty()) {
          arr.push_back(eval_stack.top());
          eval_stack.pop();
        }
      }
      reverse(arr.begin(), arr.end());
      array_pool.push_back(arr);
      eval_stack.push((ll)array_pool.size() - 1);
      break;
    }
    case ARR_GET: {
      if (eval_stack.size() >= 2) {
        ll idx = eval_stack.top();
        eval_stack.pop();
        ll arr_ref = eval_stack.top();
        eval_stack.pop();
        if (arr_ref >= 0 && arr_ref < (ll)array_pool.size()) {
          if (idx >= 0 && idx < (ll)array_pool[arr_ref].size()) {
            eval_stack.push(array_pool[arr_ref][idx]);
          } else {
            printer.print_str("Error: Array index out of bounds");
            eval_stack.push(0);
          }
        } else {
          printer.print_str("Error: Invalid array reference");
          eval_stack.push(0);
        }
      }
      break;
    }
    case ARR_SET: {
      if (eval_stack.size() >= 3) {
        ll val = eval_stack.top();
        eval_stack.pop();
        ll idx = eval_stack.top();
        eval_stack.pop();
        ll arr_ref = eval_stack.top();
        eval_stack.pop();
        if (arr_ref >= 0 && arr_ref < (ll)array_pool.size()) {
          if (idx >= 0 && idx < (ll)array_pool[arr_ref].size()) {
            array_pool[arr_ref][idx] = val;
          } else {
            printer.print_str("Error: Array index out of bounds");
          }
        } else {
          printer.print_str("Error: Invalid array reference");
        }
      }
      break;
    }
    case ARR_LEN: {
      if (!eval_stack.empty()) {
        ll arr_ref = eval_stack.top();
        eval_stack.pop();
        if (arr_ref >= 0 && arr_ref < (ll)array_pool.size()) {
          eval_stack.push((ll)array_pool[arr_ref].size());
        } else {
          eval_stack.push(0);
        }
      }
      break;
    }
    case PUSH_ARR: {
      eval_stack.push(tokens[1]);
      break;
    }
    case CALL: {
      int addr = (int)tokens[1];
      int argc = (int)tokens[2];
      Frame f;
      f.return_pc = pc;
      for (int i = 0; i < argc; i++) {
        if (!eval_stack.empty()) {
          f.locals.push_back(eval_stack.top());
          eval_stack.pop();
        }
      }
      reverse(f.locals.begin(), f.locals.end());
      call_stack.push(f);
      pc = addr;
      pc--;
      break;
    }
    case RET: {
      ll ret_val = 0;
      if (!eval_stack.empty()) {
        ret_val = eval_stack.top();
        eval_stack.pop();
      }
      if (!call_stack.empty()) {
        Frame f = call_stack.top();
        call_stack.pop();
        pc = f.return_pc;
        eval_stack.push(ret_val);
      } else {
        return; // Halt if returning from main scope
      }
      break;
    }
    case LOAD_LOCAL: {
      int idx = (int)tokens[1];
      if (!call_stack.empty()) {
        Frame &f = call_stack.top();
        if (idx < f.locals.size()) {
          eval_stack.push(f.locals[idx]);
        } else {
          printer.print_debug("Local not found", idx);
          eval_stack.push(0);
        }
      } else {
        printer.print_str("Error: LOAD_LOCAL outside of function");
      }
      break;
    }
    case STORE_LOCAL: {
      int idx = (int)tokens[1];
      if (!call_stack.empty()) {
        Frame &f = call_stack.top();
        if (idx >= f.locals.size()) {
          f.locals.resize(idx + 1, 0);
        }
        if (!eval_stack.empty()) {
          f.locals[idx] = eval_stack.top();
          eval_stack.pop();
        }
      } else {
        printer.print_str("Error: STORE_LOCAL outside of function");
      }
      break;
    }
    case PUSH_CONST: {
      int idx = (int)tokens[1];
      if (idx >= 0 && idx < (int)constant_pool.size()) {
        eval_stack.push(constant_pool[idx]);
      } else {
        printer.print_debug("Invalid constant pool index", idx);
      }
      break;
    }
    case DUP: {
      if (!eval_stack.empty()) {
        eval_stack.push(eval_stack.top());
      }
      break;
    }
    case DROP: {
      if (!eval_stack.empty()) {
        eval_stack.pop();
      }
      break;
    }
    case SWAP: {
      if (eval_stack.size() >= 2) {
        ll a = eval_stack.top(); eval_stack.pop();
        ll b = eval_stack.top(); eval_stack.pop();
        eval_stack.push(a);
        eval_stack.push(b);
      }
      break;
    }
    case NEG: {
      if (!eval_stack.empty()) {
        ll a = eval_stack.top(); eval_stack.pop();
        eval_stack.push(-a);
      }
      break;
    }
    case NOT: {
      if (!eval_stack.empty()) {
        ll a = eval_stack.top(); eval_stack.pop();
        eval_stack.push(a == 0 ? 1 : 0);
      }
      break;
    }
    case NOP: {
      break;
    }
    case INC: {
      int idx = (int)tokens[1];
      if (!call_stack.empty()) {
        Frame &f = call_stack.top();
        if (idx >= (int)f.locals.size()) f.locals.resize(idx + 1, 0);
        f.locals[idx]++;
      } else {
        if (idx >= (int)variables.size()) variables.resize(idx + 1, 0);
        variables[idx]++;
      }
      break;
    }
    case DEC: {
      int idx = (int)tokens[1];
      if (!call_stack.empty()) {
        Frame &f = call_stack.top();
        if (idx >= (int)f.locals.size()) f.locals.resize(idx + 1, 0);
        f.locals[idx]--;
      } else {
        if (idx >= (int)variables.size()) variables.resize(idx + 1, 0);
        variables[idx]--;
      }
      break;
    }
    default:
      break;
    }
    pc++;
  }
}

int main(int argc, char *argv[]) {
  string filename = "test.outz";
  for (int i = 1; i < argc; i++) {
    string arg = argv[i];
    if (arg == "--debug" || arg == "-d") {
      debug_mode = true;
    } else if (arg[0] != '-') {
      filename = arg;
    }
  }

  ifstream file(filename);
  if (!file.is_open()) {
    cout << "Error opening file: " << filename << "\n";
    return 1;
  }

  string line;
  int index = 0;
  bool header_done = false;
  while (getline(file, line)) {
    if (line.empty() || line[0] == '#')
      continue;

    if (!header_done) {
      if (line.substr(0, 7) == "VERSION") {
        int ver;
        istringstream(line) >> std::skipws >> std::ws;
        (istringstream(line) >> std::skipws >> std::ws >> std::hex).clear();
        istringstream vss(line);
        string _d;
        vss >> _d >> ver;
        if (ver != 1) {
          cerr << "Error: Unsupported .outz version " << ver << " (expected 1)\n";
          return 1;
        }
        continue;
      }
      if (line.substr(0, 11) == "CONST_COUNT") {
        int cnt; istringstream(line) >> std::skipws >> std::ws;
        string _d; istringstream(line) >> _d >> cnt;
        constant_pool.resize(cnt);
        continue;
      }
      if (line.substr(0, 9) == "STR_COUNT") {
        int cnt; istringstream(line) >> std::skipws >> std::ws;
        string _d; istringstream(line) >> _d >> cnt;
        string_pool.resize(cnt);
        continue;
      }
      if (line.substr(0, 9) == "ARR_COUNT") {
        int cnt; istringstream(line) >> std::skipws >> std::ws;
        string _d; istringstream(line) >> _d >> cnt;
        array_pool.resize(cnt);
        continue;
      }
      header_done = true;
    }

    if (line.substr(0, 4) == "STR ") {
      // Format: STR index value (value can have spaces)
      istringstream iss(line);
      string dummy;
      int s_idx;
      string s_val;
      iss >> dummy >> s_idx;
      getline(iss, s_val);
      if (!s_val.empty() && s_val[0] == ' ')
        s_val = s_val.substr(1);
      if (s_idx >= (int)string_pool.size())
        string_pool.resize(s_idx + 1);
      string_pool[s_idx] = s_val;
      continue;
    }

    if (line.substr(0, 6) == "CONST ") {
      istringstream iss(line);
      string dummy;
      int c_idx;
      ll c_val;
      iss >> dummy >> c_idx >> c_val;
      if (c_idx >= (int)constant_pool.size())
        constant_pool.resize(c_idx + 1);
      constant_pool[c_idx] = c_val;
      continue;
    }

    if (line.substr(0, 4) == "ARR ") {
      istringstream iss(line);
      string dummy;
      int a_idx;
      string a_vals_str;
      iss >> dummy >> a_idx;
      getline(iss, a_vals_str);
      if (!a_vals_str.empty() && a_vals_str[0] == ' ')
        a_vals_str = a_vals_str.substr(1);

      vector<ll> vals;
      stringstream ss(a_vals_str);
      string v;
      while (getline(ss, v, ',')) {
        if (!v.empty()) {
          vals.push_back(stoll(v));
        }
      }
      if (a_idx >= (int)array_pool.size())
        array_pool.resize(a_idx + 1);
      array_pool[a_idx] = vals;
      continue;
    }

    bytecode_program.push_back(make_pair(index++, line));
  }
  file.close();

  register_externals();

  printer.print_str("=== Execution Started ===");
  execute();
  printer.print_str("=== Execution Finished ===");
  return 0;
}