// reads the .outz file and executes the instructions
// first it will read the whole file then store it in an indexed array
// so that goto commands ( will be executed later ) knows where to go

#include <bits/stdc++.h>
#include <sstream>
using namespace std;

vector<pair<int, string>>
    bytecode_program; // int stores index , string stores the instruction ,
                      // which are just space separated integers
vector<int> variables;
stack<int> eval_stack; // for evaluation , in simmple words , it stores the 
                       // values of variables and operands

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
// TODO : add loops and other things

class Printer{
    public:
        void print(int value) {
            cout << value << "\n";
        }
        void print(const string& message){
            cout << message << "\n";
        }
        void print_debug(const string& label, int value){
            cout << "[DEBUG] " << label << ": " << value << "\n";
        }
        void print_variables(){
            cout << "\n === Variables === " << "\n";
            for (int i=0;i<variables.size();i++){
                cout << "var[" << i << "] = " << variables[i]<< "\n";
            }
            cout << " ===== END ===== " << "\n";
        }
        void print_stack(){
            cout << "\n === Stack ===\n";
            stack<int> temp = eval_stack;
            vector<int> items;
            while (!temp.empty()) {
                items.push_back(temp.top());
                temp.pop();
            }
            reverse(items.begin(), items.end());
            for (int item : items) {
                cout << item << "\n";
            }
            cout << " ===== END ===== " << "\n";
        }
};

Printer printer;

bool is_comment(const string& line){
    size_t start = line.find_first_not_of(" \t\r\n"); // what this does is it ignores the leading spaces and tabs
    return (start == string::npos || line[start] == '#');
}

void execute() {
  // Executes the program line by line.
  // Each line in the bytecode_program contains space-separated integers
  // representing instructions and operands.
  for (auto it : bytecode_program) {
    string instruction_line = it.second;
    // Format of instructions:
    // 1 (PUSH): Followed by 4 tokens (e.g., "1 0 0 0 value"). The value is in
    // the 5th position. 2 (LOAD): Followed by 1 token (the variable index). 3
    // (STORE): Followed by 1 token (the variable index). 4 (ADD), 5 (SUB), 6
    // (MUL), 7 (DIV): Single token operations. 8 (PRINT): Single token
    // operation. 9 (HALT): Single token operation.
    if (is_comment(instruction_line)){
        continue;
    }
    
    istringstream iss(instruction_line); 
    // istringstream is like a "string reader"
    // It lets us read numbers from a string one at a time
    // Example: "1 2 3" becomes individual numbers: 1, then 2, then 3
    // This will store all the numbers from the instruction
    vector<int> tokens;
    int token;  // Temporary variable to hold each number

    // The >> operator reads one number at a time from the string
    // It keeps going until there are no more numbers to read
    // Example: "1 0 0 0 10" becomes tokens = [1, 0, 0, 0, 10]
    while (iss>>token){
        tokens.push_back(token);
    }

    if (tokens.empty()){
        continue;
    }
    
    int opcode = tokens[0];

    switch(opcode) {
        case PUSH:{
            int value = tokens[4];
            eval_stack.push(value);
            break;
        }

        case LOAD: {
            int var_index = tokens[1]; // load format is 2 var_index , so we load the vairables value onto the stack
            if (var_index < variables.size()){
                eval_stack.push(variables[var_index]);
            } // making sure variable exists before loading it 
            else{
                printer.print_debug("Variable not found", var_index);
            }
            break;
        }
        case STORE: {
            // STORE format: 3 var_index
            // Take the top value from stack and save it in a variable
            int var_index = tokens[1];
                
            // Make sure there's something on the stack
            if (!eval_stack.empty()) {
                // Get the top value (and remove it from stack)
                int value = eval_stack.top();
                eval_stack.pop();
                    
                // If the variables array isn't big enough, make it bigger
                if (var_index >= variables.size()) {
                    variables.resize(var_index + 1, 0);  // Fill new slots with 0
                }
                    
                // Store the value in the variable
                variables[var_index] = value;
            }
            break;
        }
        case ADD: {
            // this needs two numbers from stack so it pops -> adds -> push back
            if (eval_stack.size()>=2){
                int b = eval_stack.top(); eval_stack.pop();
                int a = eval_stack.top(); eval_stack.pop();
                eval_stack.push(a+b);
            }
            break;
        }
        case SUB: {
            // this needs two numbers from stack so it pops -> adds -> push back
            if (eval_stack.size()>=2){
                int b = eval_stack.top(); eval_stack.pop();
                int a = eval_stack.top(); eval_stack.pop();
                eval_stack.push(a-b);
            }
            break;
        }
        case MUL: {
            // this needs two numbers from stack so it pops -> adds -> push back
            if (eval_stack.size()>=2){
                int b = eval_stack.top(); eval_stack.pop();
                int a = eval_stack.top(); eval_stack.pop();
                eval_stack.push(a*b);
            }
            break;
        }
        case DIV: {
            // DIVIDE: a / b
            if (eval_stack.size() >= 2) {
                int b = eval_stack.top(); eval_stack.pop();
                int a = eval_stack.top(); eval_stack.pop();
                    
                // Check for division by zero (would crash the program!)
                if (b != 0) {
                    eval_stack.push(a / b);
                } else {
                    printer.print("Error: Division by zero");
                }
            }
            break;
        }

        case PRINT: {
            //print format : 8 var_index
            // prints value of variable
            int var_index = tokens[1];

            if (var_index < variables.size()){
                printer.print(variables[var_index]);
            }else{
                printer.print_debug("Variable not found", var_index);
            }
            break;
        }

        case HALT: {
            // HALT: stops the program
            return;
        }

        default: {
            printer.print_debug("Unknown opcode", opcode);
            break;
        }
    }
  }
}

int main() {

  // read the entire file line by line
  ifstream file("test.outz");
  string line;
  int index = 0;
  while (getline(file, line)) {
    bytecode_program.push_back(make_pair(index, line));
    index++;
  }
  file.close();

  printer.print("=== Execution Started ===");
  // Run the program!
  execute();
  // Print finish message
  printer.print("=== Execution Finished ===");

  return 0;
}