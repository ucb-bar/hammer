/*********************************************************************
*  Filename      : SRAM1RW1024x16.v                                  *
*  SRAM name     : SRAM1RW1024x16                                    *
*  Word width    : 16     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 16


module SRAM1RW1024x16 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x16_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x16_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x16_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x16_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x16_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x16_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x16_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x16_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x16_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x16_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x16_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x16_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x16_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x16_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x16_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x16_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);


endmodule


module SRAM1RW1024x16_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x17.v                                  *
*  SRAM name     : SRAM1RW1024x17                                    *
*  Word width    : 17     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 17


module SRAM1RW1024x17 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x17_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x17_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x17_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x17_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x17_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x17_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x17_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x17_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x17_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x17_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x17_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x17_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x17_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x17_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x17_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x17_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x17_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);


endmodule


module SRAM1RW1024x17_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x32.v                                  *
*  SRAM name     : SRAM1RW1024x32                                    *
*  Word width    : 32     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 32


module SRAM1RW1024x32 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x32_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x32_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x32_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x32_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x32_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x32_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x32_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x32_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x32_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x32_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x32_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x32_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x32_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x32_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x32_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x32_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x32_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW1024x32_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW1024x32_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW1024x32_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW1024x32_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW1024x32_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW1024x32_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW1024x32_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW1024x32_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW1024x32_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW1024x32_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW1024x32_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW1024x32_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW1024x32_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW1024x32_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW1024x32_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);


endmodule


module SRAM1RW1024x32_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x37.v                                  *
*  SRAM name     : SRAM1RW1024x37                                  *
*  Word width    : 37     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 37


module SRAM1RW1024x37 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x37_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x37_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x37_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x37_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x37_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x37_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x37_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x37_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x37_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x37_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x37_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x37_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x37_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x37_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x37_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x37_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x37_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW1024x37_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW1024x37_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW1024x37_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW1024x37_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW1024x37_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW1024x37_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW1024x37_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW1024x37_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW1024x37_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW1024x37_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW1024x37_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW1024x37_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW1024x37_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW1024x37_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW1024x37_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW1024x37_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW1024x37_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW1024x37_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW1024x37_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW1024x37_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);


endmodule


module SRAM1RW1024x37_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x38.v                                  *
*  SRAM name     : SRAM1RW1024x38                                  *
*  Word width    : 38     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 38


module SRAM1RW1024x38 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x38_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x38_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x38_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x38_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x38_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x38_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x38_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x38_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x38_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x38_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x38_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x38_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x38_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x38_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x38_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x38_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x38_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW1024x38_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW1024x38_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW1024x38_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW1024x38_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW1024x38_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW1024x38_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW1024x38_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW1024x38_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW1024x38_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW1024x38_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW1024x38_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW1024x38_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW1024x38_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW1024x38_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW1024x38_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW1024x38_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW1024x38_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW1024x38_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW1024x38_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW1024x38_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW1024x38_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);


endmodule


module SRAM1RW1024x38_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x44.v                                  *
*  SRAM name     : SRAM1RW1024x44                                  *
*  Word width    : 44     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 44


module SRAM1RW1024x44 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x44_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x44_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x44_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x44_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x44_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x44_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x44_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x44_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x44_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x44_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x44_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x44_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x44_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x44_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x44_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x44_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x44_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW1024x44_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW1024x44_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW1024x44_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW1024x44_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW1024x44_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW1024x44_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW1024x44_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW1024x44_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW1024x44_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW1024x44_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW1024x44_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW1024x44_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW1024x44_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW1024x44_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW1024x44_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW1024x44_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW1024x44_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW1024x44_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW1024x44_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW1024x44_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW1024x44_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW1024x44_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW1024x44_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW1024x44_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW1024x44_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW1024x44_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW1024x44_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);


endmodule


module SRAM1RW1024x44_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x64.v                                  *
*  SRAM name     : SRAM1RW1024x64                                  *
*  Word width    : 64     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 64


module SRAM1RW1024x64 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x64_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x64_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x64_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x64_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x64_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x64_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x64_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x64_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW1024x64_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW1024x64_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW1024x64_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW1024x64_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW1024x64_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW1024x64_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW1024x64_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW1024x64_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW1024x64_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW1024x64_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW1024x64_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW1024x64_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW1024x64_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW1024x64_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW1024x64_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW1024x64_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW1024x64_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW1024x64_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW1024x64_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW1024x64_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW1024x64_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW1024x64_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW1024x64_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW1024x64_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW1024x64_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW1024x64_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW1024x64_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW1024x64_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW1024x64_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW1024x64_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW1024x64_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW1024x64_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW1024x64_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW1024x64_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW1024x64_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW1024x64_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW1024x64_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW1024x64_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW1024x64_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW1024x64_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW1024x64_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW1024x64_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);
SRAM1RW1024x64_1bit sram_IO50 ( CE, WEB,  A, OEB, CSB, I[50], O[50]);
SRAM1RW1024x64_1bit sram_IO51 ( CE, WEB,  A, OEB, CSB, I[51], O[51]);
SRAM1RW1024x64_1bit sram_IO52 ( CE, WEB,  A, OEB, CSB, I[52], O[52]);
SRAM1RW1024x64_1bit sram_IO53 ( CE, WEB,  A, OEB, CSB, I[53], O[53]);
SRAM1RW1024x64_1bit sram_IO54 ( CE, WEB,  A, OEB, CSB, I[54], O[54]);
SRAM1RW1024x64_1bit sram_IO55 ( CE, WEB,  A, OEB, CSB, I[55], O[55]);
SRAM1RW1024x64_1bit sram_IO56 ( CE, WEB,  A, OEB, CSB, I[56], O[56]);
SRAM1RW1024x64_1bit sram_IO57 ( CE, WEB,  A, OEB, CSB, I[57], O[57]);
SRAM1RW1024x64_1bit sram_IO58 ( CE, WEB,  A, OEB, CSB, I[58], O[58]);
SRAM1RW1024x64_1bit sram_IO59 ( CE, WEB,  A, OEB, CSB, I[59], O[59]);
SRAM1RW1024x64_1bit sram_IO60 ( CE, WEB,  A, OEB, CSB, I[60], O[60]);
SRAM1RW1024x64_1bit sram_IO61 ( CE, WEB,  A, OEB, CSB, I[61], O[61]);
SRAM1RW1024x64_1bit sram_IO62 ( CE, WEB,  A, OEB, CSB, I[62], O[62]);
SRAM1RW1024x64_1bit sram_IO63 ( CE, WEB,  A, OEB, CSB, I[63], O[63]);


endmodule


module SRAM1RW1024x64_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW1024x8.v                                  *
*  SRAM name     : SRAM1RW1024x8                                    *
*  Word width    : 8     bits                                        *
*  Word number   : 1024                                              *
*  Adress width  : 10    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 10
`define numWords 1024
`define wordLength 8


module SRAM1RW1024x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW1024x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW1024x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW1024x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW1024x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW1024x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW1024x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW1024x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW1024x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW1024x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW2048x8.v                                  *
*  SRAM name     : SRAM1RW2048x8                                    *
*  Word width    : 8     bits                                        *
*  Word number   : 2048                                             *
*  Adress width  : 11    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 11
`define numWords 2048
`define wordLength 8


module SRAM1RW2048x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW2048x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW2048x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW2048x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW2048x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW2048x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW2048x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW2048x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW2048x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW2048x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x12.v                                  *
*  SRAM name     : SRAM1RW128x12                                    *
*  Word width    : 12    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 12


module SRAM1RW128x12 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x12_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x12_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x12_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x12_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x12_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x12_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x12_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x12_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x12_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x12_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x12_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x12_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);


endmodule


module SRAM1RW128x12_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x14.v                                  *
*  SRAM name     : SRAM1RW128x14                                    *
*  Word width    : 14    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 14


module SRAM1RW128x14 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x14_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x14_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x14_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x14_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x14_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x14_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x14_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x14_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x14_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x14_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x14_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x14_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x14_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x14_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);


endmodule


module SRAM1RW128x14_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x22.v                                  *
*  SRAM name     : SRAM1RW128x22                                    *
*  Word width    : 22    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 22


module SRAM1RW128x22 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x22_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x22_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x22_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x22_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x22_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x22_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x22_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x22_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x22_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x22_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x22_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x22_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x22_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x22_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW128x22_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW128x22_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW128x22_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW128x22_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW128x22_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW128x22_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW128x22_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW128x22_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);


endmodule


module SRAM1RW128x22_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x40.v                                  *
*  SRAM name     : SRAM1RW128x40                                    *
*  Word width    : 40    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 40


module SRAM1RW128x40 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x40_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x40_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x40_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x40_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x40_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x40_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x40_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x40_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x40_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x40_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x40_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x40_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x40_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x40_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW128x40_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW128x40_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW128x40_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW128x40_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW128x40_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW128x40_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW128x40_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW128x40_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW128x40_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW128x40_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW128x40_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW128x40_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW128x40_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW128x40_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW128x40_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW128x40_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW128x40_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW128x40_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW128x40_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW128x40_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW128x40_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW128x40_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW128x40_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW128x40_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW128x40_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW128x40_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);


endmodule


module SRAM1RW128x40_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x46.v                                  *
*  SRAM name     : SRAM1RW128x46                                    *
*  Word width    : 46    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 46


module SRAM1RW128x46 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x46_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x46_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x46_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x46_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x46_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x46_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x46_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x46_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x46_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x46_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x46_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x46_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x46_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x46_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW128x46_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW128x46_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW128x46_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW128x46_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW128x46_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW128x46_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW128x46_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW128x46_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW128x46_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW128x46_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW128x46_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW128x46_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW128x46_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW128x46_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW128x46_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW128x46_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW128x46_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW128x46_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW128x46_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW128x46_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW128x46_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW128x46_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW128x46_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW128x46_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW128x46_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW128x46_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW128x46_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW128x46_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW128x46_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW128x46_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW128x46_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW128x46_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);


endmodule


module SRAM1RW128x46_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x48.v                                  *
*  SRAM name     : SRAM1RW128x48                                    *
*  Word width    : 48    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 48


module SRAM1RW128x48 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x48_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x48_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x48_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x48_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x48_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x48_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x48_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x48_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x48_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x48_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x48_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x48_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x48_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x48_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW128x48_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW128x48_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW128x48_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW128x48_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW128x48_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW128x48_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW128x48_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW128x48_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW128x48_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW128x48_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW128x48_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW128x48_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW128x48_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW128x48_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW128x48_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW128x48_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW128x48_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW128x48_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW128x48_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW128x48_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW128x48_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW128x48_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW128x48_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW128x48_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW128x48_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW128x48_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW128x48_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW128x48_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW128x48_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW128x48_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW128x48_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW128x48_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW128x48_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW128x48_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);


endmodule


module SRAM1RW128x48_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x64.v                                  *
*  SRAM name     : SRAM1RW128x64                                    *
*  Word width    : 64    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 64


module SRAM1RW128x64 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x64_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x64_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x64_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x64_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x64_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x64_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x64_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x64_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW128x64_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW128x64_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW128x64_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW128x64_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW128x64_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW128x64_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW128x64_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW128x64_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW128x64_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW128x64_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW128x64_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW128x64_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW128x64_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW128x64_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW128x64_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW128x64_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW128x64_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW128x64_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW128x64_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW128x64_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW128x64_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW128x64_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW128x64_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW128x64_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW128x64_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW128x64_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW128x64_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW128x64_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW128x64_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW128x64_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW128x64_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW128x64_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW128x64_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW128x64_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW128x64_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW128x64_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW128x64_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW128x64_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW128x64_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW128x64_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW128x64_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW128x64_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);
SRAM1RW128x64_1bit sram_IO50 ( CE, WEB,  A, OEB, CSB, I[50], O[50]);
SRAM1RW128x64_1bit sram_IO51 ( CE, WEB,  A, OEB, CSB, I[51], O[51]);
SRAM1RW128x64_1bit sram_IO52 ( CE, WEB,  A, OEB, CSB, I[52], O[52]);
SRAM1RW128x64_1bit sram_IO53 ( CE, WEB,  A, OEB, CSB, I[53], O[53]);
SRAM1RW128x64_1bit sram_IO54 ( CE, WEB,  A, OEB, CSB, I[54], O[54]);
SRAM1RW128x64_1bit sram_IO55 ( CE, WEB,  A, OEB, CSB, I[55], O[55]);
SRAM1RW128x64_1bit sram_IO56 ( CE, WEB,  A, OEB, CSB, I[56], O[56]);
SRAM1RW128x64_1bit sram_IO57 ( CE, WEB,  A, OEB, CSB, I[57], O[57]);
SRAM1RW128x64_1bit sram_IO58 ( CE, WEB,  A, OEB, CSB, I[58], O[58]);
SRAM1RW128x64_1bit sram_IO59 ( CE, WEB,  A, OEB, CSB, I[59], O[59]);
SRAM1RW128x64_1bit sram_IO60 ( CE, WEB,  A, OEB, CSB, I[60], O[60]);
SRAM1RW128x64_1bit sram_IO61 ( CE, WEB,  A, OEB, CSB, I[61], O[61]);
SRAM1RW128x64_1bit sram_IO62 ( CE, WEB,  A, OEB, CSB, I[62], O[62]);
SRAM1RW128x64_1bit sram_IO63 ( CE, WEB,  A, OEB, CSB, I[63], O[63]);


endmodule


module SRAM1RW128x64_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW128x8.v                                   *
*  SRAM name     : SRAM1RW128x8                                     *
*  Word width    : 8     bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 8


module SRAM1RW128x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW128x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW128x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW128x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW128x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW128x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW128x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW128x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW128x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW128x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x128.v                                 *
*  SRAM name     : SRAM1RW256x128                                   *
*  Word width    : 128   bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 128


module SRAM1RW256x128 (A,CE,WEB,OEB,CSB,BYTEMASK,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;
input [`wordLength/8-1:0]	BYTEMASK;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x128_1bit sram_IO0 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x128_1bit sram_IO1 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x128_1bit sram_IO2 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x128_1bit sram_IO3 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x128_1bit sram_IO4 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x128_1bit sram_IO5 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x128_1bit sram_IO6 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x128_1bit sram_IO7 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[7], O[7]);
SRAM1RW256x128_1bit sram_IO8 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[8], O[8]);
SRAM1RW256x128_1bit sram_IO9 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[9], O[9]);
SRAM1RW256x128_1bit sram_IO10 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[10], O[10]);
SRAM1RW256x128_1bit sram_IO11 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[11], O[11]);
SRAM1RW256x128_1bit sram_IO12 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[12], O[12]);
SRAM1RW256x128_1bit sram_IO13 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[13], O[13]);
SRAM1RW256x128_1bit sram_IO14 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[14], O[14]);
SRAM1RW256x128_1bit sram_IO15 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[15], O[15]);
SRAM1RW256x128_1bit sram_IO16 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[16], O[16]);
SRAM1RW256x128_1bit sram_IO17 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[17], O[17]);
SRAM1RW256x128_1bit sram_IO18 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[18], O[18]);
SRAM1RW256x128_1bit sram_IO19 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[19], O[19]);
SRAM1RW256x128_1bit sram_IO20 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[20], O[20]);
SRAM1RW256x128_1bit sram_IO21 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[21], O[21]);
SRAM1RW256x128_1bit sram_IO22 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[22], O[22]);
SRAM1RW256x128_1bit sram_IO23 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[23], O[23]);
SRAM1RW256x128_1bit sram_IO24 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[24], O[24]);
SRAM1RW256x128_1bit sram_IO25 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[25], O[25]);
SRAM1RW256x128_1bit sram_IO26 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[26], O[26]);
SRAM1RW256x128_1bit sram_IO27 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[27], O[27]);
SRAM1RW256x128_1bit sram_IO28 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[28], O[28]);
SRAM1RW256x128_1bit sram_IO29 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[29], O[29]);
SRAM1RW256x128_1bit sram_IO30 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[30], O[30]);
SRAM1RW256x128_1bit sram_IO31 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[31], O[31]);
SRAM1RW256x128_1bit sram_IO32 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[32], O[32]);
SRAM1RW256x128_1bit sram_IO33 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[33], O[33]);
SRAM1RW256x128_1bit sram_IO34 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[34], O[34]);
SRAM1RW256x128_1bit sram_IO35 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[35], O[35]);
SRAM1RW256x128_1bit sram_IO36 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[36], O[36]);
SRAM1RW256x128_1bit sram_IO37 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[37], O[37]);
SRAM1RW256x128_1bit sram_IO38 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[38], O[38]);
SRAM1RW256x128_1bit sram_IO39 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[39], O[39]);
SRAM1RW256x128_1bit sram_IO40 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[40], O[40]);
SRAM1RW256x128_1bit sram_IO41 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[41], O[41]);
SRAM1RW256x128_1bit sram_IO42 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[42], O[42]);
SRAM1RW256x128_1bit sram_IO43 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[43], O[43]);
SRAM1RW256x128_1bit sram_IO44 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[44], O[44]);
SRAM1RW256x128_1bit sram_IO45 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[45], O[45]);
SRAM1RW256x128_1bit sram_IO46 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[46], O[46]);
SRAM1RW256x128_1bit sram_IO47 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[47], O[47]);
SRAM1RW256x128_1bit sram_IO48 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[48], O[48]);
SRAM1RW256x128_1bit sram_IO49 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[49], O[49]);
SRAM1RW256x128_1bit sram_IO50 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[50], O[50]);
SRAM1RW256x128_1bit sram_IO51 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[51], O[51]);
SRAM1RW256x128_1bit sram_IO52 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[52], O[52]);
SRAM1RW256x128_1bit sram_IO53 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[53], O[53]);
SRAM1RW256x128_1bit sram_IO54 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[54], O[54]);
SRAM1RW256x128_1bit sram_IO55 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[55], O[55]);
SRAM1RW256x128_1bit sram_IO56 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[56], O[56]);
SRAM1RW256x128_1bit sram_IO57 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[57], O[57]);
SRAM1RW256x128_1bit sram_IO58 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[58], O[58]);
SRAM1RW256x128_1bit sram_IO59 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[59], O[59]);
SRAM1RW256x128_1bit sram_IO60 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[60], O[60]);
SRAM1RW256x128_1bit sram_IO61 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[61], O[61]);
SRAM1RW256x128_1bit sram_IO62 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[62], O[62]);
SRAM1RW256x128_1bit sram_IO63 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[63], O[63]);
SRAM1RW256x128_1bit sram_IO64 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[64], O[64]);
SRAM1RW256x128_1bit sram_IO65 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[65], O[65]);
SRAM1RW256x128_1bit sram_IO66 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[66], O[66]);
SRAM1RW256x128_1bit sram_IO67 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[67], O[67]);
SRAM1RW256x128_1bit sram_IO68 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[68], O[68]);
SRAM1RW256x128_1bit sram_IO69 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[69], O[69]);
SRAM1RW256x128_1bit sram_IO70 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[70], O[70]);
SRAM1RW256x128_1bit sram_IO71 ( CE, WEB | ~BYTEMASK[8],  A, OEB, CSB, I[71], O[71]);
SRAM1RW256x128_1bit sram_IO72 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[72], O[72]);
SRAM1RW256x128_1bit sram_IO73 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[73], O[73]);
SRAM1RW256x128_1bit sram_IO74 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[74], O[74]);
SRAM1RW256x128_1bit sram_IO75 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[75], O[75]);
SRAM1RW256x128_1bit sram_IO76 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[76], O[76]);
SRAM1RW256x128_1bit sram_IO77 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[77], O[77]);
SRAM1RW256x128_1bit sram_IO78 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[78], O[78]);
SRAM1RW256x128_1bit sram_IO79 ( CE, WEB | ~BYTEMASK[9],  A, OEB, CSB, I[79], O[79]);
SRAM1RW256x128_1bit sram_IO80 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[80], O[80]);
SRAM1RW256x128_1bit sram_IO81 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[81], O[81]);
SRAM1RW256x128_1bit sram_IO82 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[82], O[82]);
SRAM1RW256x128_1bit sram_IO83 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[83], O[83]);
SRAM1RW256x128_1bit sram_IO84 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[84], O[84]);
SRAM1RW256x128_1bit sram_IO85 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[85], O[85]);
SRAM1RW256x128_1bit sram_IO86 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[86], O[86]);
SRAM1RW256x128_1bit sram_IO87 ( CE, WEB | ~BYTEMASK[10],  A, OEB, CSB, I[87], O[87]);
SRAM1RW256x128_1bit sram_IO88 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[88], O[88]);
SRAM1RW256x128_1bit sram_IO89 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[89], O[89]);
SRAM1RW256x128_1bit sram_IO90 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[90], O[90]);
SRAM1RW256x128_1bit sram_IO91 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[91], O[91]);
SRAM1RW256x128_1bit sram_IO92 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[92], O[92]);
SRAM1RW256x128_1bit sram_IO93 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[93], O[93]);
SRAM1RW256x128_1bit sram_IO94 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[94], O[94]);
SRAM1RW256x128_1bit sram_IO95 ( CE, WEB | ~BYTEMASK[11],  A, OEB, CSB, I[95], O[95]);
SRAM1RW256x128_1bit sram_IO96 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[96], O[96]);
SRAM1RW256x128_1bit sram_IO97 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[97], O[97]);
SRAM1RW256x128_1bit sram_IO98 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[98], O[98]);
SRAM1RW256x128_1bit sram_IO99 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[99], O[99]);
SRAM1RW256x128_1bit sram_IO100 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[100], O[100]);
SRAM1RW256x128_1bit sram_IO101 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[101], O[101]);
SRAM1RW256x128_1bit sram_IO102 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[102], O[102]);
SRAM1RW256x128_1bit sram_IO103 ( CE, WEB | ~BYTEMASK[12],  A, OEB, CSB, I[103], O[103]);
SRAM1RW256x128_1bit sram_IO104 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[104], O[104]);
SRAM1RW256x128_1bit sram_IO105 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[105], O[105]);
SRAM1RW256x128_1bit sram_IO106 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[106], O[106]);
SRAM1RW256x128_1bit sram_IO107 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[107], O[107]);
SRAM1RW256x128_1bit sram_IO108 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[108], O[108]);
SRAM1RW256x128_1bit sram_IO109 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[109], O[109]);
SRAM1RW256x128_1bit sram_IO110 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[110], O[110]);
SRAM1RW256x128_1bit sram_IO111 ( CE, WEB | ~BYTEMASK[13],  A, OEB, CSB, I[111], O[111]);
SRAM1RW256x128_1bit sram_IO112 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[112], O[112]);
SRAM1RW256x128_1bit sram_IO113 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[113], O[113]);
SRAM1RW256x128_1bit sram_IO114 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[114], O[114]);
SRAM1RW256x128_1bit sram_IO115 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[115], O[115]);
SRAM1RW256x128_1bit sram_IO116 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[116], O[116]);
SRAM1RW256x128_1bit sram_IO117 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[117], O[117]);
SRAM1RW256x128_1bit sram_IO118 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[118], O[118]);
SRAM1RW256x128_1bit sram_IO119 ( CE, WEB | ~BYTEMASK[14],  A, OEB, CSB, I[119], O[119]);
SRAM1RW256x128_1bit sram_IO120 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[120], O[120]);
SRAM1RW256x128_1bit sram_IO121 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[121], O[121]);
SRAM1RW256x128_1bit sram_IO122 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[122], O[122]);
SRAM1RW256x128_1bit sram_IO123 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[123], O[123]);
SRAM1RW256x128_1bit sram_IO124 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[124], O[124]);
SRAM1RW256x128_1bit sram_IO125 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[125], O[125]);
SRAM1RW256x128_1bit sram_IO126 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[126], O[126]);
SRAM1RW256x128_1bit sram_IO127 ( CE, WEB | ~BYTEMASK[15],  A, OEB, CSB, I[127], O[127]);


endmodule


module SRAM1RW256x128_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x32.v                                  *
*  SRAM name     : SRAM1RW256x32                                    *
*  Word width    : 32    bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 32


module SRAM1RW256x32 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x32_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x32_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x32_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x32_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x32_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x32_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x32_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x32_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW256x32_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW256x32_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW256x32_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW256x32_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW256x32_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW256x32_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW256x32_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW256x32_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW256x32_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW256x32_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW256x32_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW256x32_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW256x32_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW256x32_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW256x32_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW256x32_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW256x32_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW256x32_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW256x32_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW256x32_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW256x32_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW256x32_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW256x32_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW256x32_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);


endmodule


module SRAM1RW256x32_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x46.v                                  *
*  SRAM name     : SRAM1RW256x46                                    *
*  Word width    : 46    bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 46


module SRAM1RW256x46 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x46_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x46_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x46_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x46_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x46_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x46_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x46_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x46_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW256x46_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW256x46_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW256x46_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW256x46_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW256x46_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW256x46_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW256x46_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW256x46_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW256x46_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW256x46_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW256x46_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW256x46_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW256x46_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW256x46_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW256x46_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW256x46_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW256x46_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW256x46_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW256x46_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW256x46_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW256x46_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW256x46_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW256x46_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW256x46_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW256x46_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW256x46_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW256x46_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW256x46_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW256x46_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW256x46_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW256x46_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW256x46_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW256x46_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW256x46_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW256x46_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW256x46_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW256x46_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW256x46_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);


endmodule


module SRAM1RW256x46_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x48.v                                  *
*  SRAM name     : SRAM1RW256x48                                    *
*  Word width    : 48    bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 48


module SRAM1RW256x48 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x48_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x48_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x48_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x48_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x48_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x48_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x48_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x48_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW256x48_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW256x48_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW256x48_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW256x48_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW256x48_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW256x48_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW256x48_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW256x48_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW256x48_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW256x48_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW256x48_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW256x48_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW256x48_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW256x48_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW256x48_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW256x48_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW256x48_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW256x48_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW256x48_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW256x48_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW256x48_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW256x48_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW256x48_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW256x48_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW256x48_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW256x48_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW256x48_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW256x48_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW256x48_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW256x48_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW256x48_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW256x48_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW256x48_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW256x48_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW256x48_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW256x48_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW256x48_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW256x48_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW256x48_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW256x48_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);


endmodule


module SRAM1RW256x48_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x64.v                                 *
*  SRAM name     : SRAM1RW256x64                                   *
*  Word width    : 64   bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 64


module SRAM1RW256x64 (A,CE,WEB,OEB,CSB,BYTEMASK,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;
input [`wordLength/8-1:0]	BYTEMASK;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x64_1bit sram_IO0 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x64_1bit sram_IO1 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x64_1bit sram_IO2 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x64_1bit sram_IO3 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x64_1bit sram_IO4 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x64_1bit sram_IO5 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x64_1bit sram_IO6 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x64_1bit sram_IO7 ( CE, WEB | ~BYTEMASK[0],  A, OEB, CSB, I[7], O[7]);
SRAM1RW256x64_1bit sram_IO8 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[8], O[8]);
SRAM1RW256x64_1bit sram_IO9 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[9], O[9]);
SRAM1RW256x64_1bit sram_IO10 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[10], O[10]);
SRAM1RW256x64_1bit sram_IO11 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[11], O[11]);
SRAM1RW256x64_1bit sram_IO12 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[12], O[12]);
SRAM1RW256x64_1bit sram_IO13 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[13], O[13]);
SRAM1RW256x64_1bit sram_IO14 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[14], O[14]);
SRAM1RW256x64_1bit sram_IO15 ( CE, WEB | ~BYTEMASK[1],  A, OEB, CSB, I[15], O[15]);
SRAM1RW256x64_1bit sram_IO16 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[16], O[16]);
SRAM1RW256x64_1bit sram_IO17 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[17], O[17]);
SRAM1RW256x64_1bit sram_IO18 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[18], O[18]);
SRAM1RW256x64_1bit sram_IO19 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[19], O[19]);
SRAM1RW256x64_1bit sram_IO20 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[20], O[20]);
SRAM1RW256x64_1bit sram_IO21 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[21], O[21]);
SRAM1RW256x64_1bit sram_IO22 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[22], O[22]);
SRAM1RW256x64_1bit sram_IO23 ( CE, WEB | ~BYTEMASK[2],  A, OEB, CSB, I[23], O[23]);
SRAM1RW256x64_1bit sram_IO24 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[24], O[24]);
SRAM1RW256x64_1bit sram_IO25 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[25], O[25]);
SRAM1RW256x64_1bit sram_IO26 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[26], O[26]);
SRAM1RW256x64_1bit sram_IO27 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[27], O[27]);
SRAM1RW256x64_1bit sram_IO28 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[28], O[28]);
SRAM1RW256x64_1bit sram_IO29 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[29], O[29]);
SRAM1RW256x64_1bit sram_IO30 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[30], O[30]);
SRAM1RW256x64_1bit sram_IO31 ( CE, WEB | ~BYTEMASK[3],  A, OEB, CSB, I[31], O[31]);
SRAM1RW256x64_1bit sram_IO32 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[32], O[32]);
SRAM1RW256x64_1bit sram_IO33 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[33], O[33]);
SRAM1RW256x64_1bit sram_IO34 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[34], O[34]);
SRAM1RW256x64_1bit sram_IO35 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[35], O[35]);
SRAM1RW256x64_1bit sram_IO36 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[36], O[36]);
SRAM1RW256x64_1bit sram_IO37 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[37], O[37]);
SRAM1RW256x64_1bit sram_IO38 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[38], O[38]);
SRAM1RW256x64_1bit sram_IO39 ( CE, WEB | ~BYTEMASK[4],  A, OEB, CSB, I[39], O[39]);
SRAM1RW256x64_1bit sram_IO40 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[40], O[40]);
SRAM1RW256x64_1bit sram_IO41 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[41], O[41]);
SRAM1RW256x64_1bit sram_IO42 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[42], O[42]);
SRAM1RW256x64_1bit sram_IO43 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[43], O[43]);
SRAM1RW256x64_1bit sram_IO44 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[44], O[44]);
SRAM1RW256x64_1bit sram_IO45 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[45], O[45]);
SRAM1RW256x64_1bit sram_IO46 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[46], O[46]);
SRAM1RW256x64_1bit sram_IO47 ( CE, WEB | ~BYTEMASK[5],  A, OEB, CSB, I[47], O[47]);
SRAM1RW256x64_1bit sram_IO48 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[48], O[48]);
SRAM1RW256x64_1bit sram_IO49 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[49], O[49]);
SRAM1RW256x64_1bit sram_IO50 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[50], O[50]);
SRAM1RW256x64_1bit sram_IO51 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[51], O[51]);
SRAM1RW256x64_1bit sram_IO52 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[52], O[52]);
SRAM1RW256x64_1bit sram_IO53 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[53], O[53]);
SRAM1RW256x64_1bit sram_IO54 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[54], O[54]);
SRAM1RW256x64_1bit sram_IO55 ( CE, WEB | ~BYTEMASK[6],  A, OEB, CSB, I[55], O[55]);
SRAM1RW256x64_1bit sram_IO56 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[56], O[56]);
SRAM1RW256x64_1bit sram_IO57 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[57], O[57]);
SRAM1RW256x64_1bit sram_IO58 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[58], O[58]);
SRAM1RW256x64_1bit sram_IO59 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[59], O[59]);
SRAM1RW256x64_1bit sram_IO60 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[60], O[60]);
SRAM1RW256x64_1bit sram_IO61 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[61], O[61]);
SRAM1RW256x64_1bit sram_IO62 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[62], O[62]);
SRAM1RW256x64_1bit sram_IO63 ( CE, WEB | ~BYTEMASK[7],  A, OEB, CSB, I[63], O[63]);


endmodule


module SRAM1RW256x64_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW256x8.v                                   *
*  SRAM name     : SRAM1RW256x8                                     *
*  Word width    : 8     bits                                        *
*  Word number   : 256                                               *
*  Adress width  : 8     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 8
`define numWords 256
`define wordLength 8


module SRAM1RW256x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW256x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW256x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW256x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW256x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW256x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW256x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW256x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW256x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW256x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW32x50.v                                   *
*  SRAM name     : SRAM1RW32x50                                     *
*  Word width    : 50    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 50


module SRAM1RW32x50 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW32x50_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW32x50_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW32x50_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW32x50_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW32x50_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW32x50_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW32x50_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW32x50_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW32x50_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW32x50_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW32x50_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW32x50_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW32x50_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW32x50_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW32x50_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW32x50_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW32x50_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW32x50_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW32x50_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW32x50_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW32x50_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW32x50_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW32x50_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW32x50_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW32x50_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW32x50_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW32x50_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW32x50_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW32x50_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW32x50_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW32x50_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW32x50_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW32x50_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW32x50_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW32x50_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW32x50_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW32x50_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW32x50_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW32x50_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW32x50_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW32x50_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW32x50_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW32x50_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW32x50_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW32x50_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW32x50_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW32x50_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW32x50_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW32x50_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW32x50_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);


endmodule


module SRAM1RW32x50_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW4096x16.v                                  *
*  SRAM name     : SRAM1RW4096x16                                    *
*  Word width    : 16     bits                                        *
*  Word number   : 4096                                              *
*  Adress width  : 12    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 12
`define numWords 4096
`define wordLength 16


module SRAM1RW4096x16 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW4096x16_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW4096x16_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW4096x16_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW4096x16_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW4096x16_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW4096x16_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW4096x16_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW4096x16_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW4096x16_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW4096x16_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW4096x16_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW4096x16_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW4096x16_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW4096x16_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW4096x16_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW4096x16_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);


endmodule


module SRAM1RW4096x16_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW4096x8.v                                  *
*  SRAM name     : SRAM1RW4096x8                                    *
*  Word width    : 8     bits                                        *
*  Word number   : 4096                                             *
*  Adress width  : 12    bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 12
`define numWords 4096
`define wordLength 8


module SRAM1RW4096x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW4096x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW4096x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW4096x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW4096x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW4096x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW4096x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW4096x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW4096x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW4096x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW512x128.v                                 *
*  SRAM name     : SRAM1RW512x128                                   *
*  Word width    : 128   bits                                        *
*  Word number   : 512                                               *
*  Adress width  : 9     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 9
`define numWords 512
`define wordLength 128


module SRAM1RW512x128 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW512x128_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW512x128_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW512x128_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW512x128_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW512x128_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW512x128_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW512x128_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW512x128_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW512x128_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW512x128_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW512x128_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW512x128_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW512x128_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW512x128_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW512x128_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW512x128_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW512x128_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW512x128_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW512x128_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW512x128_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW512x128_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW512x128_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW512x128_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW512x128_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW512x128_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW512x128_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW512x128_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW512x128_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW512x128_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW512x128_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW512x128_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW512x128_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW512x128_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW512x128_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW512x128_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW512x128_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW512x128_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW512x128_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW512x128_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW512x128_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW512x128_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW512x128_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW512x128_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW512x128_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW512x128_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW512x128_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW512x128_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW512x128_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW512x128_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW512x128_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);
SRAM1RW512x128_1bit sram_IO50 ( CE, WEB,  A, OEB, CSB, I[50], O[50]);
SRAM1RW512x128_1bit sram_IO51 ( CE, WEB,  A, OEB, CSB, I[51], O[51]);
SRAM1RW512x128_1bit sram_IO52 ( CE, WEB,  A, OEB, CSB, I[52], O[52]);
SRAM1RW512x128_1bit sram_IO53 ( CE, WEB,  A, OEB, CSB, I[53], O[53]);
SRAM1RW512x128_1bit sram_IO54 ( CE, WEB,  A, OEB, CSB, I[54], O[54]);
SRAM1RW512x128_1bit sram_IO55 ( CE, WEB,  A, OEB, CSB, I[55], O[55]);
SRAM1RW512x128_1bit sram_IO56 ( CE, WEB,  A, OEB, CSB, I[56], O[56]);
SRAM1RW512x128_1bit sram_IO57 ( CE, WEB,  A, OEB, CSB, I[57], O[57]);
SRAM1RW512x128_1bit sram_IO58 ( CE, WEB,  A, OEB, CSB, I[58], O[58]);
SRAM1RW512x128_1bit sram_IO59 ( CE, WEB,  A, OEB, CSB, I[59], O[59]);
SRAM1RW512x128_1bit sram_IO60 ( CE, WEB,  A, OEB, CSB, I[60], O[60]);
SRAM1RW512x128_1bit sram_IO61 ( CE, WEB,  A, OEB, CSB, I[61], O[61]);
SRAM1RW512x128_1bit sram_IO62 ( CE, WEB,  A, OEB, CSB, I[62], O[62]);
SRAM1RW512x128_1bit sram_IO63 ( CE, WEB,  A, OEB, CSB, I[63], O[63]);
SRAM1RW512x128_1bit sram_IO64 ( CE, WEB,  A, OEB, CSB, I[64], O[64]);
SRAM1RW512x128_1bit sram_IO65 ( CE, WEB,  A, OEB, CSB, I[65], O[65]);
SRAM1RW512x128_1bit sram_IO66 ( CE, WEB,  A, OEB, CSB, I[66], O[66]);
SRAM1RW512x128_1bit sram_IO67 ( CE, WEB,  A, OEB, CSB, I[67], O[67]);
SRAM1RW512x128_1bit sram_IO68 ( CE, WEB,  A, OEB, CSB, I[68], O[68]);
SRAM1RW512x128_1bit sram_IO69 ( CE, WEB,  A, OEB, CSB, I[69], O[69]);
SRAM1RW512x128_1bit sram_IO70 ( CE, WEB,  A, OEB, CSB, I[70], O[70]);
SRAM1RW512x128_1bit sram_IO71 ( CE, WEB,  A, OEB, CSB, I[71], O[71]);
SRAM1RW512x128_1bit sram_IO72 ( CE, WEB,  A, OEB, CSB, I[72], O[72]);
SRAM1RW512x128_1bit sram_IO73 ( CE, WEB,  A, OEB, CSB, I[73], O[73]);
SRAM1RW512x128_1bit sram_IO74 ( CE, WEB,  A, OEB, CSB, I[74], O[74]);
SRAM1RW512x128_1bit sram_IO75 ( CE, WEB,  A, OEB, CSB, I[75], O[75]);
SRAM1RW512x128_1bit sram_IO76 ( CE, WEB,  A, OEB, CSB, I[76], O[76]);
SRAM1RW512x128_1bit sram_IO77 ( CE, WEB,  A, OEB, CSB, I[77], O[77]);
SRAM1RW512x128_1bit sram_IO78 ( CE, WEB,  A, OEB, CSB, I[78], O[78]);
SRAM1RW512x128_1bit sram_IO79 ( CE, WEB,  A, OEB, CSB, I[79], O[79]);
SRAM1RW512x128_1bit sram_IO80 ( CE, WEB,  A, OEB, CSB, I[80], O[80]);
SRAM1RW512x128_1bit sram_IO81 ( CE, WEB,  A, OEB, CSB, I[81], O[81]);
SRAM1RW512x128_1bit sram_IO82 ( CE, WEB,  A, OEB, CSB, I[82], O[82]);
SRAM1RW512x128_1bit sram_IO83 ( CE, WEB,  A, OEB, CSB, I[83], O[83]);
SRAM1RW512x128_1bit sram_IO84 ( CE, WEB,  A, OEB, CSB, I[84], O[84]);
SRAM1RW512x128_1bit sram_IO85 ( CE, WEB,  A, OEB, CSB, I[85], O[85]);
SRAM1RW512x128_1bit sram_IO86 ( CE, WEB,  A, OEB, CSB, I[86], O[86]);
SRAM1RW512x128_1bit sram_IO87 ( CE, WEB,  A, OEB, CSB, I[87], O[87]);
SRAM1RW512x128_1bit sram_IO88 ( CE, WEB,  A, OEB, CSB, I[88], O[88]);
SRAM1RW512x128_1bit sram_IO89 ( CE, WEB,  A, OEB, CSB, I[89], O[89]);
SRAM1RW512x128_1bit sram_IO90 ( CE, WEB,  A, OEB, CSB, I[90], O[90]);
SRAM1RW512x128_1bit sram_IO91 ( CE, WEB,  A, OEB, CSB, I[91], O[91]);
SRAM1RW512x128_1bit sram_IO92 ( CE, WEB,  A, OEB, CSB, I[92], O[92]);
SRAM1RW512x128_1bit sram_IO93 ( CE, WEB,  A, OEB, CSB, I[93], O[93]);
SRAM1RW512x128_1bit sram_IO94 ( CE, WEB,  A, OEB, CSB, I[94], O[94]);
SRAM1RW512x128_1bit sram_IO95 ( CE, WEB,  A, OEB, CSB, I[95], O[95]);
SRAM1RW512x128_1bit sram_IO96 ( CE, WEB,  A, OEB, CSB, I[96], O[96]);
SRAM1RW512x128_1bit sram_IO97 ( CE, WEB,  A, OEB, CSB, I[97], O[97]);
SRAM1RW512x128_1bit sram_IO98 ( CE, WEB,  A, OEB, CSB, I[98], O[98]);
SRAM1RW512x128_1bit sram_IO99 ( CE, WEB,  A, OEB, CSB, I[99], O[99]);
SRAM1RW512x128_1bit sram_IO100 ( CE, WEB,  A, OEB, CSB, I[100], O[100]);
SRAM1RW512x128_1bit sram_IO101 ( CE, WEB,  A, OEB, CSB, I[101], O[101]);
SRAM1RW512x128_1bit sram_IO102 ( CE, WEB,  A, OEB, CSB, I[102], O[102]);
SRAM1RW512x128_1bit sram_IO103 ( CE, WEB,  A, OEB, CSB, I[103], O[103]);
SRAM1RW512x128_1bit sram_IO104 ( CE, WEB,  A, OEB, CSB, I[104], O[104]);
SRAM1RW512x128_1bit sram_IO105 ( CE, WEB,  A, OEB, CSB, I[105], O[105]);
SRAM1RW512x128_1bit sram_IO106 ( CE, WEB,  A, OEB, CSB, I[106], O[106]);
SRAM1RW512x128_1bit sram_IO107 ( CE, WEB,  A, OEB, CSB, I[107], O[107]);
SRAM1RW512x128_1bit sram_IO108 ( CE, WEB,  A, OEB, CSB, I[108], O[108]);
SRAM1RW512x128_1bit sram_IO109 ( CE, WEB,  A, OEB, CSB, I[109], O[109]);
SRAM1RW512x128_1bit sram_IO110 ( CE, WEB,  A, OEB, CSB, I[110], O[110]);
SRAM1RW512x128_1bit sram_IO111 ( CE, WEB,  A, OEB, CSB, I[111], O[111]);
SRAM1RW512x128_1bit sram_IO112 ( CE, WEB,  A, OEB, CSB, I[112], O[112]);
SRAM1RW512x128_1bit sram_IO113 ( CE, WEB,  A, OEB, CSB, I[113], O[113]);
SRAM1RW512x128_1bit sram_IO114 ( CE, WEB,  A, OEB, CSB, I[114], O[114]);
SRAM1RW512x128_1bit sram_IO115 ( CE, WEB,  A, OEB, CSB, I[115], O[115]);
SRAM1RW512x128_1bit sram_IO116 ( CE, WEB,  A, OEB, CSB, I[116], O[116]);
SRAM1RW512x128_1bit sram_IO117 ( CE, WEB,  A, OEB, CSB, I[117], O[117]);
SRAM1RW512x128_1bit sram_IO118 ( CE, WEB,  A, OEB, CSB, I[118], O[118]);
SRAM1RW512x128_1bit sram_IO119 ( CE, WEB,  A, OEB, CSB, I[119], O[119]);
SRAM1RW512x128_1bit sram_IO120 ( CE, WEB,  A, OEB, CSB, I[120], O[120]);
SRAM1RW512x128_1bit sram_IO121 ( CE, WEB,  A, OEB, CSB, I[121], O[121]);
SRAM1RW512x128_1bit sram_IO122 ( CE, WEB,  A, OEB, CSB, I[122], O[122]);
SRAM1RW512x128_1bit sram_IO123 ( CE, WEB,  A, OEB, CSB, I[123], O[123]);
SRAM1RW512x128_1bit sram_IO124 ( CE, WEB,  A, OEB, CSB, I[124], O[124]);
SRAM1RW512x128_1bit sram_IO125 ( CE, WEB,  A, OEB, CSB, I[125], O[125]);
SRAM1RW512x128_1bit sram_IO126 ( CE, WEB,  A, OEB, CSB, I[126], O[126]);
SRAM1RW512x128_1bit sram_IO127 ( CE, WEB,  A, OEB, CSB, I[127], O[127]);


endmodule


module SRAM1RW512x128_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW512x32.v                                  *
*  SRAM name     : SRAM1RW512x32                                    *
*  Word width    : 32    bits                                        *
*  Word number   : 512                                               *
*  Adress width  : 9     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 9
`define numWords 512
`define wordLength 32


module SRAM1RW512x32 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW512x32_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW512x32_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW512x32_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW512x32_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW512x32_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW512x32_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW512x32_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW512x32_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW512x32_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW512x32_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW512x32_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW512x32_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW512x32_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW512x32_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW512x32_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW512x32_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW512x32_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW512x32_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW512x32_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW512x32_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW512x32_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW512x32_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW512x32_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW512x32_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW512x32_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW512x32_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW512x32_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW512x32_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW512x32_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW512x32_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW512x32_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW512x32_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);


endmodule


module SRAM1RW512x32_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW512x64.v                                 *
*  SRAM name     : SRAM1RW512x64                                   *
*  Word width    : 64   bits                                        *
*  Word number   : 512                                               *
*  Adress width  : 9     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 9
`define numWords 512
`define wordLength 64


module SRAM1RW512x64 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW512x64_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW512x64_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW512x64_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW512x64_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW512x64_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW512x64_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW512x64_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW512x64_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW512x64_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW512x64_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW512x64_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW512x64_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW512x64_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW512x64_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW512x64_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW512x64_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW512x64_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW512x64_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW512x64_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW512x64_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW512x64_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW512x64_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW512x64_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW512x64_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW512x64_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW512x64_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW512x64_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW512x64_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW512x64_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW512x64_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW512x64_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW512x64_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW512x64_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW512x64_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW512x64_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW512x64_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW512x64_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW512x64_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW512x64_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW512x64_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW512x64_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW512x64_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW512x64_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW512x64_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW512x64_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW512x64_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW512x64_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW512x64_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW512x64_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW512x64_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);
SRAM1RW512x64_1bit sram_IO50 ( CE, WEB,  A, OEB, CSB, I[50], O[50]);
SRAM1RW512x64_1bit sram_IO51 ( CE, WEB,  A, OEB, CSB, I[51], O[51]);
SRAM1RW512x64_1bit sram_IO52 ( CE, WEB,  A, OEB, CSB, I[52], O[52]);
SRAM1RW512x64_1bit sram_IO53 ( CE, WEB,  A, OEB, CSB, I[53], O[53]);
SRAM1RW512x64_1bit sram_IO54 ( CE, WEB,  A, OEB, CSB, I[54], O[54]);
SRAM1RW512x64_1bit sram_IO55 ( CE, WEB,  A, OEB, CSB, I[55], O[55]);
SRAM1RW512x64_1bit sram_IO56 ( CE, WEB,  A, OEB, CSB, I[56], O[56]);
SRAM1RW512x64_1bit sram_IO57 ( CE, WEB,  A, OEB, CSB, I[57], O[57]);
SRAM1RW512x64_1bit sram_IO58 ( CE, WEB,  A, OEB, CSB, I[58], O[58]);
SRAM1RW512x64_1bit sram_IO59 ( CE, WEB,  A, OEB, CSB, I[59], O[59]);
SRAM1RW512x64_1bit sram_IO60 ( CE, WEB,  A, OEB, CSB, I[60], O[60]);
SRAM1RW512x64_1bit sram_IO61 ( CE, WEB,  A, OEB, CSB, I[61], O[61]);
SRAM1RW512x64_1bit sram_IO62 ( CE, WEB,  A, OEB, CSB, I[62], O[62]);
SRAM1RW512x64_1bit sram_IO63 ( CE, WEB,  A, OEB, CSB, I[63], O[63]);
SRAM1RW512x64_1bit sram_IO64 ( CE, WEB,  A, OEB, CSB, I[64], O[64]);
SRAM1RW512x64_1bit sram_IO65 ( CE, WEB,  A, OEB, CSB, I[65], O[65]);


endmodule


module SRAM1RW512x64_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW512x8.v                                   *
*  SRAM name     : SRAM1RW512x8                                     *
*  Word width    : 8     bits                                        *
*  Word number   : 512                                               *
*  Adress width  : 9     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 9
`define numWords 512
`define wordLength 8


module SRAM1RW512x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW512x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW512x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW512x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW512x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW512x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW512x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW512x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW512x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW512x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x128.v                                  *
*  SRAM name     : SRAM1RW64x128                                    *
*  Word width    : 128   bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 128


module SRAM1RW64x128 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x128_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x128_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x128_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x128_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x128_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x128_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x128_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x128_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x128_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x128_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x128_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x128_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x128_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x128_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x128_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x128_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x128_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x128_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x128_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x128_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW64x128_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW64x128_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW64x128_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW64x128_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW64x128_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW64x128_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW64x128_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW64x128_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW64x128_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW64x128_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW64x128_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW64x128_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW64x128_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW64x128_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);
SRAM1RW64x128_1bit sram_IO34 ( CE, WEB,  A, OEB, CSB, I[34], O[34]);
SRAM1RW64x128_1bit sram_IO35 ( CE, WEB,  A, OEB, CSB, I[35], O[35]);
SRAM1RW64x128_1bit sram_IO36 ( CE, WEB,  A, OEB, CSB, I[36], O[36]);
SRAM1RW64x128_1bit sram_IO37 ( CE, WEB,  A, OEB, CSB, I[37], O[37]);
SRAM1RW64x128_1bit sram_IO38 ( CE, WEB,  A, OEB, CSB, I[38], O[38]);
SRAM1RW64x128_1bit sram_IO39 ( CE, WEB,  A, OEB, CSB, I[39], O[39]);
SRAM1RW64x128_1bit sram_IO40 ( CE, WEB,  A, OEB, CSB, I[40], O[40]);
SRAM1RW64x128_1bit sram_IO41 ( CE, WEB,  A, OEB, CSB, I[41], O[41]);
SRAM1RW64x128_1bit sram_IO42 ( CE, WEB,  A, OEB, CSB, I[42], O[42]);
SRAM1RW64x128_1bit sram_IO43 ( CE, WEB,  A, OEB, CSB, I[43], O[43]);
SRAM1RW64x128_1bit sram_IO44 ( CE, WEB,  A, OEB, CSB, I[44], O[44]);
SRAM1RW64x128_1bit sram_IO45 ( CE, WEB,  A, OEB, CSB, I[45], O[45]);
SRAM1RW64x128_1bit sram_IO46 ( CE, WEB,  A, OEB, CSB, I[46], O[46]);
SRAM1RW64x128_1bit sram_IO47 ( CE, WEB,  A, OEB, CSB, I[47], O[47]);
SRAM1RW64x128_1bit sram_IO48 ( CE, WEB,  A, OEB, CSB, I[48], O[48]);
SRAM1RW64x128_1bit sram_IO49 ( CE, WEB,  A, OEB, CSB, I[49], O[49]);
SRAM1RW64x128_1bit sram_IO50 ( CE, WEB,  A, OEB, CSB, I[50], O[50]);
SRAM1RW64x128_1bit sram_IO51 ( CE, WEB,  A, OEB, CSB, I[51], O[51]);
SRAM1RW64x128_1bit sram_IO52 ( CE, WEB,  A, OEB, CSB, I[52], O[52]);
SRAM1RW64x128_1bit sram_IO53 ( CE, WEB,  A, OEB, CSB, I[53], O[53]);
SRAM1RW64x128_1bit sram_IO54 ( CE, WEB,  A, OEB, CSB, I[54], O[54]);
SRAM1RW64x128_1bit sram_IO55 ( CE, WEB,  A, OEB, CSB, I[55], O[55]);
SRAM1RW64x128_1bit sram_IO56 ( CE, WEB,  A, OEB, CSB, I[56], O[56]);
SRAM1RW64x128_1bit sram_IO57 ( CE, WEB,  A, OEB, CSB, I[57], O[57]);
SRAM1RW64x128_1bit sram_IO58 ( CE, WEB,  A, OEB, CSB, I[58], O[58]);
SRAM1RW64x128_1bit sram_IO59 ( CE, WEB,  A, OEB, CSB, I[59], O[59]);
SRAM1RW64x128_1bit sram_IO60 ( CE, WEB,  A, OEB, CSB, I[60], O[60]);
SRAM1RW64x128_1bit sram_IO61 ( CE, WEB,  A, OEB, CSB, I[61], O[61]);
SRAM1RW64x128_1bit sram_IO62 ( CE, WEB,  A, OEB, CSB, I[62], O[62]);
SRAM1RW64x128_1bit sram_IO63 ( CE, WEB,  A, OEB, CSB, I[63], O[63]);
SRAM1RW64x128_1bit sram_IO64 ( CE, WEB,  A, OEB, CSB, I[64], O[64]);
SRAM1RW64x128_1bit sram_IO65 ( CE, WEB,  A, OEB, CSB, I[65], O[65]);
SRAM1RW64x128_1bit sram_IO66 ( CE, WEB,  A, OEB, CSB, I[66], O[66]);
SRAM1RW64x128_1bit sram_IO67 ( CE, WEB,  A, OEB, CSB, I[67], O[67]);
SRAM1RW64x128_1bit sram_IO68 ( CE, WEB,  A, OEB, CSB, I[68], O[68]);
SRAM1RW64x128_1bit sram_IO69 ( CE, WEB,  A, OEB, CSB, I[69], O[69]);
SRAM1RW64x128_1bit sram_IO70 ( CE, WEB,  A, OEB, CSB, I[70], O[70]);
SRAM1RW64x128_1bit sram_IO71 ( CE, WEB,  A, OEB, CSB, I[71], O[71]);
SRAM1RW64x128_1bit sram_IO72 ( CE, WEB,  A, OEB, CSB, I[72], O[72]);
SRAM1RW64x128_1bit sram_IO73 ( CE, WEB,  A, OEB, CSB, I[73], O[73]);
SRAM1RW64x128_1bit sram_IO74 ( CE, WEB,  A, OEB, CSB, I[74], O[74]);
SRAM1RW64x128_1bit sram_IO75 ( CE, WEB,  A, OEB, CSB, I[75], O[75]);
SRAM1RW64x128_1bit sram_IO76 ( CE, WEB,  A, OEB, CSB, I[76], O[76]);
SRAM1RW64x128_1bit sram_IO77 ( CE, WEB,  A, OEB, CSB, I[77], O[77]);
SRAM1RW64x128_1bit sram_IO78 ( CE, WEB,  A, OEB, CSB, I[78], O[78]);
SRAM1RW64x128_1bit sram_IO79 ( CE, WEB,  A, OEB, CSB, I[79], O[79]);
SRAM1RW64x128_1bit sram_IO80 ( CE, WEB,  A, OEB, CSB, I[80], O[80]);
SRAM1RW64x128_1bit sram_IO81 ( CE, WEB,  A, OEB, CSB, I[81], O[81]);
SRAM1RW64x128_1bit sram_IO82 ( CE, WEB,  A, OEB, CSB, I[82], O[82]);
SRAM1RW64x128_1bit sram_IO83 ( CE, WEB,  A, OEB, CSB, I[83], O[83]);
SRAM1RW64x128_1bit sram_IO84 ( CE, WEB,  A, OEB, CSB, I[84], O[84]);
SRAM1RW64x128_1bit sram_IO85 ( CE, WEB,  A, OEB, CSB, I[85], O[85]);
SRAM1RW64x128_1bit sram_IO86 ( CE, WEB,  A, OEB, CSB, I[86], O[86]);
SRAM1RW64x128_1bit sram_IO87 ( CE, WEB,  A, OEB, CSB, I[87], O[87]);
SRAM1RW64x128_1bit sram_IO88 ( CE, WEB,  A, OEB, CSB, I[88], O[88]);
SRAM1RW64x128_1bit sram_IO89 ( CE, WEB,  A, OEB, CSB, I[89], O[89]);
SRAM1RW64x128_1bit sram_IO90 ( CE, WEB,  A, OEB, CSB, I[90], O[90]);
SRAM1RW64x128_1bit sram_IO91 ( CE, WEB,  A, OEB, CSB, I[91], O[91]);
SRAM1RW64x128_1bit sram_IO92 ( CE, WEB,  A, OEB, CSB, I[92], O[92]);
SRAM1RW64x128_1bit sram_IO93 ( CE, WEB,  A, OEB, CSB, I[93], O[93]);
SRAM1RW64x128_1bit sram_IO94 ( CE, WEB,  A, OEB, CSB, I[94], O[94]);
SRAM1RW64x128_1bit sram_IO95 ( CE, WEB,  A, OEB, CSB, I[95], O[95]);
SRAM1RW64x128_1bit sram_IO96 ( CE, WEB,  A, OEB, CSB, I[96], O[96]);
SRAM1RW64x128_1bit sram_IO97 ( CE, WEB,  A, OEB, CSB, I[97], O[97]);
SRAM1RW64x128_1bit sram_IO98 ( CE, WEB,  A, OEB, CSB, I[98], O[98]);
SRAM1RW64x128_1bit sram_IO99 ( CE, WEB,  A, OEB, CSB, I[99], O[99]);
SRAM1RW64x128_1bit sram_IO100 ( CE, WEB,  A, OEB, CSB, I[100], O[100]);
SRAM1RW64x128_1bit sram_IO101 ( CE, WEB,  A, OEB, CSB, I[101], O[101]);
SRAM1RW64x128_1bit sram_IO102 ( CE, WEB,  A, OEB, CSB, I[102], O[102]);
SRAM1RW64x128_1bit sram_IO103 ( CE, WEB,  A, OEB, CSB, I[103], O[103]);
SRAM1RW64x128_1bit sram_IO104 ( CE, WEB,  A, OEB, CSB, I[104], O[104]);
SRAM1RW64x128_1bit sram_IO105 ( CE, WEB,  A, OEB, CSB, I[105], O[105]);
SRAM1RW64x128_1bit sram_IO106 ( CE, WEB,  A, OEB, CSB, I[106], O[106]);
SRAM1RW64x128_1bit sram_IO107 ( CE, WEB,  A, OEB, CSB, I[107], O[107]);
SRAM1RW64x128_1bit sram_IO108 ( CE, WEB,  A, OEB, CSB, I[108], O[108]);
SRAM1RW64x128_1bit sram_IO109 ( CE, WEB,  A, OEB, CSB, I[109], O[109]);
SRAM1RW64x128_1bit sram_IO110 ( CE, WEB,  A, OEB, CSB, I[110], O[110]);
SRAM1RW64x128_1bit sram_IO111 ( CE, WEB,  A, OEB, CSB, I[111], O[111]);
SRAM1RW64x128_1bit sram_IO112 ( CE, WEB,  A, OEB, CSB, I[112], O[112]);
SRAM1RW64x128_1bit sram_IO113 ( CE, WEB,  A, OEB, CSB, I[113], O[113]);
SRAM1RW64x128_1bit sram_IO114 ( CE, WEB,  A, OEB, CSB, I[114], O[114]);
SRAM1RW64x128_1bit sram_IO115 ( CE, WEB,  A, OEB, CSB, I[115], O[115]);
SRAM1RW64x128_1bit sram_IO116 ( CE, WEB,  A, OEB, CSB, I[116], O[116]);
SRAM1RW64x128_1bit sram_IO117 ( CE, WEB,  A, OEB, CSB, I[117], O[117]);
SRAM1RW64x128_1bit sram_IO118 ( CE, WEB,  A, OEB, CSB, I[118], O[118]);
SRAM1RW64x128_1bit sram_IO119 ( CE, WEB,  A, OEB, CSB, I[119], O[119]);
SRAM1RW64x128_1bit sram_IO120 ( CE, WEB,  A, OEB, CSB, I[120], O[120]);
SRAM1RW64x128_1bit sram_IO121 ( CE, WEB,  A, OEB, CSB, I[121], O[121]);
SRAM1RW64x128_1bit sram_IO122 ( CE, WEB,  A, OEB, CSB, I[122], O[122]);
SRAM1RW64x128_1bit sram_IO123 ( CE, WEB,  A, OEB, CSB, I[123], O[123]);
SRAM1RW64x128_1bit sram_IO124 ( CE, WEB,  A, OEB, CSB, I[124], O[124]);
SRAM1RW64x128_1bit sram_IO125 ( CE, WEB,  A, OEB, CSB, I[125], O[125]);
SRAM1RW64x128_1bit sram_IO126 ( CE, WEB,  A, OEB, CSB, I[126], O[126]);
SRAM1RW64x128_1bit sram_IO127 ( CE, WEB,  A, OEB, CSB, I[127], O[127]);


endmodule


module SRAM1RW64x128_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x20.v                                   *
*  SRAM name     : SRAM1RW64x20                                     *
*  Word width    : 20    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 20


module SRAM1RW64x20 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x20_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x20_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x20_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x20_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x20_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x20_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x20_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x20_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x20_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x20_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x20_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x20_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x20_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x20_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x20_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x20_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x20_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x20_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x20_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x20_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);


endmodule


module SRAM1RW64x20_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x21.v                                   *
*  SRAM name     : SRAM1RW64x21                                     *
*  Word width    : 21    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 21


module SRAM1RW64x21 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x21_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x21_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x21_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x21_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x21_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x21_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x21_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x21_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x21_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x21_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x21_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x21_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x21_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x21_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x21_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x21_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x21_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x21_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x21_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x21_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW64x21_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);


endmodule


module SRAM1RW64x21_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x22.v                                   *
*  SRAM name     : SRAM1RW64x22                                     *
*  Word width    : 22    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 22


module SRAM1RW64x22 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x22_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x22_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x22_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x22_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x22_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x22_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x22_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x22_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x22_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x22_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x22_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x22_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x22_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x22_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x22_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x22_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x22_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x22_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x22_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x22_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW64x22_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW64x22_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);


endmodule


module SRAM1RW64x22_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x32.v                                   *
*  SRAM name     : SRAM1RW64x32                                     *
*  Word width    : 32    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 32


module SRAM1RW64x32 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x32_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x32_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x32_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x32_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x32_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x32_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x32_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x32_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x32_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x32_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x32_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x32_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x32_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x32_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x32_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x32_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x32_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x32_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x32_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x32_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW64x32_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW64x32_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW64x32_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW64x32_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW64x32_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW64x32_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW64x32_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW64x32_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW64x32_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW64x32_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW64x32_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW64x32_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);


endmodule


module SRAM1RW64x32_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x34.v                                   *
*  SRAM name     : SRAM1RW64x34                                     *
*  Word width    : 34    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 34


module SRAM1RW64x34 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x34_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x34_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x34_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x34_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x34_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x34_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x34_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x34_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);
SRAM1RW64x34_1bit sram_IO8 ( CE, WEB,  A, OEB, CSB, I[8], O[8]);
SRAM1RW64x34_1bit sram_IO9 ( CE, WEB,  A, OEB, CSB, I[9], O[9]);
SRAM1RW64x34_1bit sram_IO10 ( CE, WEB,  A, OEB, CSB, I[10], O[10]);
SRAM1RW64x34_1bit sram_IO11 ( CE, WEB,  A, OEB, CSB, I[11], O[11]);
SRAM1RW64x34_1bit sram_IO12 ( CE, WEB,  A, OEB, CSB, I[12], O[12]);
SRAM1RW64x34_1bit sram_IO13 ( CE, WEB,  A, OEB, CSB, I[13], O[13]);
SRAM1RW64x34_1bit sram_IO14 ( CE, WEB,  A, OEB, CSB, I[14], O[14]);
SRAM1RW64x34_1bit sram_IO15 ( CE, WEB,  A, OEB, CSB, I[15], O[15]);
SRAM1RW64x34_1bit sram_IO16 ( CE, WEB,  A, OEB, CSB, I[16], O[16]);
SRAM1RW64x34_1bit sram_IO17 ( CE, WEB,  A, OEB, CSB, I[17], O[17]);
SRAM1RW64x34_1bit sram_IO18 ( CE, WEB,  A, OEB, CSB, I[18], O[18]);
SRAM1RW64x34_1bit sram_IO19 ( CE, WEB,  A, OEB, CSB, I[19], O[19]);
SRAM1RW64x34_1bit sram_IO20 ( CE, WEB,  A, OEB, CSB, I[20], O[20]);
SRAM1RW64x34_1bit sram_IO21 ( CE, WEB,  A, OEB, CSB, I[21], O[21]);
SRAM1RW64x34_1bit sram_IO22 ( CE, WEB,  A, OEB, CSB, I[22], O[22]);
SRAM1RW64x34_1bit sram_IO23 ( CE, WEB,  A, OEB, CSB, I[23], O[23]);
SRAM1RW64x34_1bit sram_IO24 ( CE, WEB,  A, OEB, CSB, I[24], O[24]);
SRAM1RW64x34_1bit sram_IO25 ( CE, WEB,  A, OEB, CSB, I[25], O[25]);
SRAM1RW64x34_1bit sram_IO26 ( CE, WEB,  A, OEB, CSB, I[26], O[26]);
SRAM1RW64x34_1bit sram_IO27 ( CE, WEB,  A, OEB, CSB, I[27], O[27]);
SRAM1RW64x34_1bit sram_IO28 ( CE, WEB,  A, OEB, CSB, I[28], O[28]);
SRAM1RW64x34_1bit sram_IO29 ( CE, WEB,  A, OEB, CSB, I[29], O[29]);
SRAM1RW64x34_1bit sram_IO30 ( CE, WEB,  A, OEB, CSB, I[30], O[30]);
SRAM1RW64x34_1bit sram_IO31 ( CE, WEB,  A, OEB, CSB, I[31], O[31]);
SRAM1RW64x34_1bit sram_IO32 ( CE, WEB,  A, OEB, CSB, I[32], O[32]);
SRAM1RW64x34_1bit sram_IO33 ( CE, WEB,  A, OEB, CSB, I[33], O[33]);


endmodule


module SRAM1RW64x34_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM1RW64x8.v                                    *
*  SRAM name     : SRAM1RW64x8                                      *
*  Word width    : 8     bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 8


module SRAM1RW64x8 (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[`numAddr-1:0] 		A;
input 	[`wordLength-1:0] 	I;
output 	[`wordLength-1:0] 	O;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out;*/
wire 	[`wordLength-1:0] 	O;

wire 				RE;
wire 				WE;

SRAM1RW64x8_1bit sram_IO0 ( CE, WEB,  A, OEB, CSB, I[0], O[0]);
SRAM1RW64x8_1bit sram_IO1 ( CE, WEB,  A, OEB, CSB, I[1], O[1]);
SRAM1RW64x8_1bit sram_IO2 ( CE, WEB,  A, OEB, CSB, I[2], O[2]);
SRAM1RW64x8_1bit sram_IO3 ( CE, WEB,  A, OEB, CSB, I[3], O[3]);
SRAM1RW64x8_1bit sram_IO4 ( CE, WEB,  A, OEB, CSB, I[4], O[4]);
SRAM1RW64x8_1bit sram_IO5 ( CE, WEB,  A, OEB, CSB, I[5], O[5]);
SRAM1RW64x8_1bit sram_IO6 ( CE, WEB,  A, OEB, CSB, I[6], O[6]);
SRAM1RW64x8_1bit sram_IO7 ( CE, WEB,  A, OEB, CSB, I[7], O[7]);


endmodule


module SRAM1RW64x8_1bit (CE_i, WEB_i,  A_i, OEB_i, CSB_i, I_i, O_i);

input CSB_i;
input OEB_i;
input CE_i;
input WEB_i;

input 	[`numAddr-1:0] 	A_i;
input 	[0:0] I_i;

output 	[0:0] O_i;

reg 	[0:0]O_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out;


// Write Mode
wire RE;
wire WE;
and u1 (RE, ~CSB_i,  WEB_i);
and u2 (WE, ~CSB_i, ~WEB_i);


always @ (posedge CE_i) 
	if (RE)
		data_out = memory[A_i];
always @ (posedge CE_i) 
	if (WE)
		memory[A_i] = I_i;
		

always @ (posedge CE_i)
	if (!OEB_i) 
		O_i = data_out;
	else
		O_i =  1'bz;


endmodule


/*********************************************************************
*  Filename      : SRAM2RW128x16.v                                      *
*  SRAM name     : SRAM2RW128x16                                        *
*  Word width    : 16    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 16



module SRAM2RW128x16 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW128x16_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW128x16_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW128x16_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW128x16_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW128x16_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW128x16_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW128x16_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW128x16_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW128x16_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW128x16_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW128x16_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW128x16_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW128x16_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW128x16_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW128x16_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW128x16_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);


endmodule


module SRAM2RW128x16_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW128x32.v                                      *
*  SRAM name     : SRAM2RW128x32                                        *
*  Word width    : 32    bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 32



module SRAM2RW128x32 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW128x32_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW128x32_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW128x32_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW128x32_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW128x32_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW128x32_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW128x32_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW128x32_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW128x32_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW128x32_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW128x32_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW128x32_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW128x32_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW128x32_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW128x32_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW128x32_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW128x32_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW128x32_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW128x32_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW128x32_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW128x32_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW128x32_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW128x32_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW128x32_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW128x32_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW128x32_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW128x32_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW128x32_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW128x32_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW128x32_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW128x32_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW128x32_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);


endmodule


module SRAM2RW128x32_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW128x4.v                                       *
*  SRAM name     : SRAM2RW128x4                                         *
*  Word width    : 4     bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 4



module SRAM2RW128x4 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW128x4_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW128x4_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW128x4_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW128x4_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);


endmodule


module SRAM2RW128x4_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW128x8.v                                       *
*  SRAM name     : SRAM2RW128x8                                         *
*  Word width    : 8     bits                                        *
*  Word number   : 128                                               *
*  Adress width  : 7     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 7
`define numWords 128
`define wordLength 8



module SRAM2RW128x8 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW128x8_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW128x8_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW128x8_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW128x8_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW128x8_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW128x8_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW128x8_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW128x8_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);


endmodule


module SRAM2RW128x8_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW16x16.v                                       *
*  SRAM name     : SRAM2RW16x16                                         *
*  Word width    : 16    bits                                        *
*  Word number   : 16                                                *
*  Adress width  : 4     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 4
`define numWords 16
`define wordLength 16



module SRAM2RW16x16 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW16x16_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW16x16_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW16x16_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW16x16_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW16x16_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW16x16_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW16x16_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW16x16_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW16x16_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW16x16_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW16x16_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW16x16_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW16x16_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW16x16_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW16x16_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW16x16_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);


endmodule


module SRAM2RW16x16_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW16x32.v                                       *
*  SRAM name     : SRAM2RW16x32                                         *
*  Word width    : 32    bits                                        *
*  Word number   : 16                                                *
*  Adress width  : 4     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 4
`define numWords 16
`define wordLength 32



module SRAM2RW16x32 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW16x32_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW16x32_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW16x32_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW16x32_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW16x32_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW16x32_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW16x32_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW16x32_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW16x32_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW16x32_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW16x32_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW16x32_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW16x32_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW16x32_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW16x32_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW16x32_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW16x32_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW16x32_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW16x32_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW16x32_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW16x32_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW16x32_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW16x32_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW16x32_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW16x32_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW16x32_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW16x32_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW16x32_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW16x32_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW16x32_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW16x32_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW16x32_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);


endmodule


module SRAM2RW16x32_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW16x4.v                                        *
*  SRAM name     : SRAM2RW16x4                                          *
*  Word width    : 4     bits                                        *
*  Word number   : 16                                                *
*  Adress width  : 4     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 4
`define numWords 16
`define wordLength 4



module SRAM2RW16x4 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW16x4_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW16x4_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW16x4_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW16x4_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);


endmodule


module SRAM2RW16x4_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW16x8.v                                        *
*  SRAM name     : SRAM2RW16x8                                          *
*  Word width    : 8     bits                                        *
*  Word number   : 16                                                *
*  Adress width  : 4     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 4
`define numWords 16
`define wordLength 8



module SRAM2RW16x8 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW16x8_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW16x8_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW16x8_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW16x8_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW16x8_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW16x8_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW16x8_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW16x8_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);


endmodule


module SRAM2RW16x8_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x16.v                                       *
*  SRAM name     : SRAM2RW32x16                                         *
*  Word width    : 16    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 16



module SRAM2RW32x16 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x16_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x16_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x16_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x16_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x16_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x16_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x16_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x16_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW32x16_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW32x16_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW32x16_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW32x16_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW32x16_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW32x16_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW32x16_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW32x16_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);


endmodule


module SRAM2RW32x16_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x22.v                                       *
*  SRAM name     : SRAM2RW32x22                                         *
*  Word width    : 22    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 22



module SRAM2RW32x22 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x22_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x22_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x22_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x22_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x22_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x22_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x22_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x22_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW32x22_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW32x22_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW32x22_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW32x22_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW32x22_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW32x22_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW32x22_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW32x22_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW32x22_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW32x22_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW32x22_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW32x22_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW32x22_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW32x22_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);


endmodule


module SRAM2RW32x22_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x32.v                                       *
*  SRAM name     : SRAM2RW32x32                                         *
*  Word width    : 32    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 32



module SRAM2RW32x32 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x32_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x32_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x32_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x32_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x32_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x32_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x32_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x32_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW32x32_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW32x32_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW32x32_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW32x32_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW32x32_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW32x32_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW32x32_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW32x32_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW32x32_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW32x32_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW32x32_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW32x32_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW32x32_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW32x32_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW32x32_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW32x32_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW32x32_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW32x32_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW32x32_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW32x32_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW32x32_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW32x32_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW32x32_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW32x32_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);


endmodule


module SRAM2RW32x32_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x33.v                                       *
*  SRAM name     : SRAM2RW32x33                                         *
*  Word width    : 33    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 33



module SRAM2RW32x33 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x33_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x33_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x33_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x33_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x33_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x33_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x33_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x33_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW32x33_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW32x33_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW32x33_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW32x33_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW32x33_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW32x33_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW32x33_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW32x33_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW32x33_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW32x33_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW32x33_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW32x33_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW32x33_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW32x33_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW32x33_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW32x33_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW32x33_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW32x33_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW32x33_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW32x33_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW32x33_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW32x33_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW32x33_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW32x33_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);
SRAM2RW32x33_1bit sram_IO32 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[32], I2[32], O1[32], O2[32]);


endmodule


module SRAM2RW32x33_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x39.v                                       *
*  SRAM name     : SRAM2RW32x39                                         *
*  Word width    : 39    bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 39



module SRAM2RW32x39 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x39_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x39_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x39_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x39_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x39_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x39_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x39_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x39_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW32x39_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW32x39_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW32x39_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW32x39_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW32x39_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW32x39_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW32x39_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW32x39_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW32x39_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW32x39_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW32x39_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW32x39_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW32x39_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW32x39_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW32x39_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW32x39_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW32x39_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW32x39_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW32x39_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW32x39_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW32x39_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW32x39_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW32x39_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW32x39_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);
SRAM2RW32x39_1bit sram_IO32 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[32], I2[32], O1[32], O2[32]);
SRAM2RW32x39_1bit sram_IO33 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[33], I2[33], O1[33], O2[33]);
SRAM2RW32x39_1bit sram_IO34 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[34], I2[34], O1[34], O2[34]);
SRAM2RW32x39_1bit sram_IO35 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[35], I2[35], O1[35], O2[35]);
SRAM2RW32x39_1bit sram_IO36 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[36], I2[36], O1[36], O2[36]);
SRAM2RW32x39_1bit sram_IO37 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[37], I2[37], O1[37], O2[37]);
SRAM2RW32x39_1bit sram_IO38 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[38], I2[38], O1[38], O2[38]);


endmodule


module SRAM2RW32x39_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x4.v                                        *
*  SRAM name     : SRAM2RW32x4                                          *
*  Word width    : 4     bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 4



module SRAM2RW32x4 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x4_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x4_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x4_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x4_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);


endmodule


module SRAM2RW32x4_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW32x8.v                                        *
*  SRAM name     : SRAM2RW32x8                                          *
*  Word width    : 8     bits                                        *
*  Word number   : 32                                                *
*  Adress width  : 5     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 5
`define numWords 32
`define wordLength 8



module SRAM2RW32x8 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW32x8_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW32x8_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW32x8_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW32x8_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW32x8_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW32x8_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW32x8_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW32x8_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);


endmodule


module SRAM2RW32x8_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW64x16.v                                       *
*  SRAM name     : SRAM2RW64x16                                         *
*  Word width    : 16    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 16



module SRAM2RW64x16 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW64x16_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW64x16_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW64x16_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW64x16_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW64x16_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW64x16_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW64x16_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW64x16_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW64x16_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW64x16_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW64x16_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW64x16_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW64x16_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW64x16_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW64x16_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW64x16_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);


endmodule


module SRAM2RW64x16_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW64x24.v                                       *
*  SRAM name     : SRAM2RW64x24                                         *
*  Word width    : 24    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 24



module SRAM2RW64x24 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW64x24_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW64x24_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW64x24_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW64x24_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW64x24_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW64x24_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW64x24_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW64x24_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW64x24_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW64x24_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW64x24_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW64x24_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW64x24_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW64x24_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW64x24_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW64x24_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW64x24_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW64x24_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW64x24_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW64x24_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW64x24_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW64x24_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW64x24_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW64x24_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);


endmodule


module SRAM2RW64x24_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW64x32.v                                       *
*  SRAM name     : SRAM2RW64x32                                         *
*  Word width    : 32    bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 32



module SRAM2RW64x32 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW64x32_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW64x32_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW64x32_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW64x32_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW64x32_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW64x32_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW64x32_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW64x32_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);
SRAM2RW64x32_1bit sram_IO8 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[8], I2[8], O1[8], O2[8]);
SRAM2RW64x32_1bit sram_IO9 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[9], I2[9], O1[9], O2[9]);
SRAM2RW64x32_1bit sram_IO10 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[10], I2[10], O1[10], O2[10]);
SRAM2RW64x32_1bit sram_IO11 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[11], I2[11], O1[11], O2[11]);
SRAM2RW64x32_1bit sram_IO12 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[12], I2[12], O1[12], O2[12]);
SRAM2RW64x32_1bit sram_IO13 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[13], I2[13], O1[13], O2[13]);
SRAM2RW64x32_1bit sram_IO14 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[14], I2[14], O1[14], O2[14]);
SRAM2RW64x32_1bit sram_IO15 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[15], I2[15], O1[15], O2[15]);
SRAM2RW64x32_1bit sram_IO16 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[16], I2[16], O1[16], O2[16]);
SRAM2RW64x32_1bit sram_IO17 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[17], I2[17], O1[17], O2[17]);
SRAM2RW64x32_1bit sram_IO18 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[18], I2[18], O1[18], O2[18]);
SRAM2RW64x32_1bit sram_IO19 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[19], I2[19], O1[19], O2[19]);
SRAM2RW64x32_1bit sram_IO20 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[20], I2[20], O1[20], O2[20]);
SRAM2RW64x32_1bit sram_IO21 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[21], I2[21], O1[21], O2[21]);
SRAM2RW64x32_1bit sram_IO22 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[22], I2[22], O1[22], O2[22]);
SRAM2RW64x32_1bit sram_IO23 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[23], I2[23], O1[23], O2[23]);
SRAM2RW64x32_1bit sram_IO24 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[24], I2[24], O1[24], O2[24]);
SRAM2RW64x32_1bit sram_IO25 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[25], I2[25], O1[25], O2[25]);
SRAM2RW64x32_1bit sram_IO26 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[26], I2[26], O1[26], O2[26]);
SRAM2RW64x32_1bit sram_IO27 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[27], I2[27], O1[27], O2[27]);
SRAM2RW64x32_1bit sram_IO28 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[28], I2[28], O1[28], O2[28]);
SRAM2RW64x32_1bit sram_IO29 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[29], I2[29], O1[29], O2[29]);
SRAM2RW64x32_1bit sram_IO30 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[30], I2[30], O1[30], O2[30]);
SRAM2RW64x32_1bit sram_IO31 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[31], I2[31], O1[31], O2[31]);


endmodule


module SRAM2RW64x32_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW64x4.v                                        *
*  SRAM name     : SRAM2RW64x4                                          *
*  Word width    : 4     bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 4



module SRAM2RW64x4 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW64x4_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW64x4_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW64x4_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW64x4_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);


endmodule


module SRAM2RW64x4_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
/*********************************************************************
*  Filename      : SRAM2RW64x8.v                                        *
*  SRAM name     : SRAM2RW64x8                                          *
*  Word width    : 8     bits                                        *
*  Word number   : 64                                                *
*  Adress width  : 6     bits                                        *
**********************************************************************/

`timescale 1ns/100fs

`define numAddr 6
`define numWords 64
`define wordLength 8



module SRAM2RW64x8 (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[`numAddr-1:0] 		A1;
input 	[`numAddr-1:0] 		A2;
input 	[`wordLength-1:0] 	I1;
input 	[`wordLength-1:0] 	I2;
output 	[`wordLength-1:0] 	O1;
output 	[`wordLength-1:0] 	O2;

/*reg   [`wordLength-1:0]   	memory[`numWords-1:0];*/
/*reg  	[`wordLength-1:0]	data_out1;*/
/*reg  	[`wordLength-1:0]	data_out2;*/
wire 	[`wordLength-1:0] 	O1;
wire  	[`wordLength-1:0]	O2;
	
wire 				RE1;
wire 				RE2;	
wire 				WE1;	
wire 				WE2;

SRAM2RW64x8_1bit sram_IO0 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[0], I2[0], O1[0], O2[0]);
SRAM2RW64x8_1bit sram_IO1 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[1], I2[1], O1[1], O2[1]);
SRAM2RW64x8_1bit sram_IO2 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[2], I2[2], O1[2], O2[2]);
SRAM2RW64x8_1bit sram_IO3 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[3], I2[3], O1[3], O2[3]);
SRAM2RW64x8_1bit sram_IO4 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[4], I2[4], O1[4], O2[4]);
SRAM2RW64x8_1bit sram_IO5 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[5], I2[5], O1[5], O2[5]);
SRAM2RW64x8_1bit sram_IO6 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[6], I2[6], O1[6], O2[6]);
SRAM2RW64x8_1bit sram_IO7 ( CE1, CE2, WEB1, WEB2,  A1, A2, OEB1, OEB2, CSB1, CSB2, I1[7], I2[7], O1[7], O2[7]);


endmodule


module SRAM2RW64x8_1bit (CE1_i, CE2_i, WEB1_i, WEB2_i,  A1_i, A2_i, OEB1_i, OEB2_i, CSB1_i, CSB2_i, I1_i, I2_i, O1_i, O2_i);

input 	CSB1_i, CSB2_i;
input 	OEB1_i, OEB2_i;
input 	CE1_i, CE2_i;
input 	WEB1_i, WEB2_i;

input 	[`numAddr-1:0] 	A1_i, A2_i;
input 	[0:0] I1_i, I2_i;

output 	[0:0] O1_i, O2_i;

reg 	[0:0] O1_i, O2_i;
reg    	[0:0]  	memory[`numWords-1:0];
reg  	[0:0]	data_out1, data_out2;


wire RE1;
wire WE1;
wire RE2;
wire WE2;
and u1 (RE1, ~CSB1_i,  WEB1_i);
and u2 (WE1, ~CSB1_i, ~WEB1_i);
and u3 (RE2, ~CSB2_i,  WEB2_i);
and u4 (WE2, ~CSB2_i, ~WEB2_i);

//Primary ports

always @ (posedge CE1_i) 
	if (RE1)
		data_out1 = memory[A1_i];
always @ (posedge CE1_i) 
	if (WE1)
		memory[A1_i] = I1_i;
		

always @ (data_out1 or OEB1_i)
	if (!OEB1_i) 
		O1_i = data_out1;
	else
		O1_i =  1'bz;

//Dual ports	
always @ (posedge CE2_i)
  	if (RE2)
		data_out2 = memory[A2_i];
always @ (posedge CE2_i)
	if (WE2)
		memory[A2_i] = I2_i;
		
always @ (data_out2 or OEB2_i)
	if (!OEB2_i) 
		O2_i = data_out2;
	else
		O2_i = 1'bz;

endmodule
