// 8-bit ALU for verification concept testing
// Spec Reference: File 2 (RL Verification Gym Architecture.md) - 'ALU.v module'
//
// Operations:
//   000 - ADD
//   001 - SUB
//   010 - AND
//   011 - OR
//   100 - XOR
//   101 - NOT (operates on A only)
//   110 - SHL (shift A left by B[2:0])
//   111 - SHR (shift A right by B[2:0])

module alu #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]   a,
    input  wire [WIDTH-1:0]   b,
    input  wire [2:0]         op,
    output reg  [WIDTH-1:0]   result,
    output wire               zero,
    output wire               overflow,
    output wire               carry
);

    // Internal signals for arithmetic operations
    reg [WIDTH:0] add_result;
    reg [WIDTH:0] sub_result;
    reg           overflow_add;
    reg           overflow_sub;

    // Operation codes
    localparam OP_ADD = 3'b000;
    localparam OP_SUB = 3'b001;
    localparam OP_AND = 3'b010;
    localparam OP_OR  = 3'b011;
    localparam OP_XOR = 3'b100;
    localparam OP_NOT = 3'b101;
    localparam OP_SHL = 3'b110;
    localparam OP_SHR = 3'b111;

    // Compute arithmetic results
    always @(*) begin
        // Addition with carry
        add_result = {1'b0, a} + {1'b0, b};

        // Subtraction with borrow
        sub_result = {1'b0, a} - {1'b0, b};

        // Signed overflow detection for addition
        // Overflow occurs when adding two positives gives negative, or
        // adding two negatives gives positive
        overflow_add = (a[WIDTH-1] == b[WIDTH-1]) &&
                       (add_result[WIDTH-1] != a[WIDTH-1]);

        // Signed overflow detection for subtraction
        // Overflow occurs when subtracting negative from positive gives negative, or
        // subtracting positive from negative gives positive
        overflow_sub = (a[WIDTH-1] != b[WIDTH-1]) &&
                       (sub_result[WIDTH-1] != a[WIDTH-1]);
    end

    // Main ALU operation
    always @(*) begin
        case (op)
            OP_ADD: result = add_result[WIDTH-1:0];
            OP_SUB: result = sub_result[WIDTH-1:0];
            OP_AND: result = a & b;
            OP_OR:  result = a | b;
            OP_XOR: result = a ^ b;
            OP_NOT: result = ~a;
            OP_SHL: result = a << b[2:0];
            OP_SHR: result = a >> b[2:0];
            default: result = {WIDTH{1'b0}};
        endcase
    end

    // Zero flag: result is zero
    assign zero = (result == {WIDTH{1'b0}});

    // Overflow flag: only valid for ADD/SUB operations
    assign overflow = (op == OP_ADD) ? overflow_add :
                      (op == OP_SUB) ? overflow_sub : 1'b0;

    // Carry flag: carry/borrow from MSB
    assign carry = (op == OP_ADD) ? add_result[WIDTH] :
                   (op == OP_SUB) ? sub_result[WIDTH] : 1'b0;

endmodule
