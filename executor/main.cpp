#include <bits/stdc++.h>
#include <sstream>
using namespace std;
typedef long long ll;

vector<pair<int, string>>
    bytecode_program; // int stores index , string stores the instruction
vector<ll> variables;
vector<string> string_pool;    // Store string literals from pool
vector<vector<ll>> array_pool; // Store array literals/templates
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
const int MAKE_ARR = 30;
const int ARR_GET = 31;
const int ARR_SET = 32;
const int ARR_LEN = 33;
const int PUSH_ARR = 34;
const int CALL = 40;
const int RET = 41;
const int LOAD_LOCAL = 42;
const int STORE_LOCAL = 43;

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
    case PRINT: {
      int var_index = (int)tokens[1];
      if (var_index < (int)variables.size()) {
        printer.print(variables[var_index]);
      } else {
        printer.print_debug("Variable not found", var_index);
      }
      break;
    }
    case PRINT_STR: {
      int var_index = (int)tokens[1];
      if (var_index < (int)variables.size()) {
        ll str_idx = variables[var_index];
        if (str_idx >= 0 && str_idx < (ll)string_pool.size()) {
          printer.print_str(string_pool[str_idx]);
        } else {
          printer.print_debug("Invalid string pool index", str_idx);
        }
      } else {
        printer.print_debug("Variable not found", var_index);
      }
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
    default:
      break;
    }
    pc++;
  }
}

int main(int argc, char *argv[]) {
  string filename = "test.outz";
  if (argc > 1) {
    filename = argv[1];
  }

  ifstream file(filename);
  if (!file.is_open()) {
    cout << "Error opening file: " << filename << "\n";
    return 1;
  }

  string line;
  int index = 0;
  while (getline(file, line)) {
    if (line.empty() || line[0] == '#')
      continue;

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
      if (s_idx >= string_pool.size())
        string_pool.resize(s_idx + 1);
      string_pool[s_idx] = s_val;
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

  printer.print_str("=== Execution Started ===");
  execute();
  printer.print_str("=== Execution Finished ===");
  return 0;
}