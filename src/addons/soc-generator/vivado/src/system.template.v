`timescale 1ns/1ps

module system
(
  input wire CLK100MHZ,
  input wire ck_rst,

  // Sliding switches
  input wire sw_0,
  input wire sw_1,
  input wire sw_2,
  input wire sw_3,

  // RGB LEDs, 3 pins each
  output wire led0_r,
  output wire led0_g,
  output wire led0_b,
  output wire led1_r,
  output wire led1_g,
  output wire led1_b,
  output wire led2_r,
  output wire led2_g,
  output wire led2_b,
  output wire led3_r,
  output wire led3_g,
  output wire led3_b,

  // Green LEDs
  output wire led_0,
  output wire led_1,
  output wire led_2,
  output wire led_3,

  // Buttons
  inout wire btn_0,
  inout wire btn_1,
  inout wire btn_2,
  inout wire btn_3,

  // Pmod (GPIO) connectors
  inout wire ja_0,
  inout wire ja_1,
  inout wire ja_2,
  inout wire ja_3,
  inout wire ja_4,
  inout wire ja_5,
  inout wire ja_6,
  inout wire ja_7,

  // Dedicated QSPI interface
  output wire qspi_cs,
  output wire qspi_sck,
  inout wire [3:0] qspi_dq,

  // UART0 (GPIO 16,17)
  output wire uart_rxd_out,
  input wire uart_txd_in,

  // Arduino (aka chipkit) shield digital IO pins, 14 is not connected to the
  // chip, used for debug.
  inout wire [19:0] ck_io,

  // Dedicated SPI pins on 6 pin header standard on later arduino models
  // connected to SPI2 (on FPGA)
  inout wire ck_miso,
  inout wire ck_mosi,
  inout wire ck_ss,
  inout wire ck_sck,

  // JD (used for JTAG connection)
  inout wire jd_0, // TDO
  inout wire jd_1, // TRST_n
  inout wire jd_2, // TCK
  inout wire jd_4, // TDI
  inout wire jd_5, // TMS
  input wire jd_6 // SRST_n
);

  wire clk_out1;
  wire hfclk;
  wire mmcm_locked;

  wire reset_core;
  wire reset_bus;
  wire reset_periph;
  wire reset_intcon_n;
  wire reset_periph_n;

  // All wires connected to the chip top
  wire dut_clock;
  wire dut_reset;
  wire dut_io_pads_jtag_TCK_i_ival;
  wire dut_io_pads_jtag_TCK_o_oval;
  wire dut_io_pads_jtag_TCK_o_oe;
  wire dut_io_pads_jtag_TCK_o_ie;
  wire dut_io_pads_jtag_TCK_o_pue;
  wire dut_io_pads_jtag_TCK_o_ds;
  wire dut_io_pads_jtag_TMS_i_ival;
  wire dut_io_pads_jtag_TMS_o_oval;
  wire dut_io_pads_jtag_TMS_o_oe;
  wire dut_io_pads_jtag_TMS_o_ie;
  wire dut_io_pads_jtag_TMS_o_pue;
  wire dut_io_pads_jtag_TMS_o_ds;
  wire dut_io_pads_jtag_TDI_i_ival;
  wire dut_io_pads_jtag_TDI_o_oval;
  wire dut_io_pads_jtag_TDI_o_oe;
  wire dut_io_pads_jtag_TDI_o_ie;
  wire dut_io_pads_jtag_TDI_o_pue;
  wire dut_io_pads_jtag_TDI_o_ds;
  wire dut_io_pads_jtag_TDO_i_ival;
  wire dut_io_pads_jtag_TDO_o_oval;
  wire dut_io_pads_jtag_TDO_o_oe;
  wire dut_io_pads_jtag_TDO_o_ie;
  wire dut_io_pads_jtag_TDO_o_pue;
  wire dut_io_pads_jtag_TDO_o_ds;
  wire dut_io_pads_jtag_TRST_n_i_ival;
  wire dut_io_pads_jtag_TRST_n_o_oval;
  wire dut_io_pads_jtag_TRST_n_o_oe;
  wire dut_io_pads_jtag_TRST_n_o_ie;
  wire dut_io_pads_jtag_TRST_n_o_pue;
  wire dut_io_pads_jtag_TRST_n_o_ds;
  wire dut_io_pads_gpio_0_i_ival;
  wire dut_io_pads_gpio_0_o_oval;
  wire dut_io_pads_gpio_0_o_oe;
  wire dut_io_pads_gpio_0_o_ie;
  wire dut_io_pads_gpio_0_o_pue;
  wire dut_io_pads_gpio_0_o_ds;
  wire dut_io_pads_gpio_1_i_ival;
  wire dut_io_pads_gpio_1_o_oval;
  wire dut_io_pads_gpio_1_o_oe;
  wire dut_io_pads_gpio_1_o_ie;
  wire dut_io_pads_gpio_1_o_pue;
  wire dut_io_pads_gpio_1_o_ds;
  wire dut_io_pads_gpio_2_i_ival;
  wire dut_io_pads_gpio_2_o_oval;
  wire dut_io_pads_gpio_2_o_oe;
  wire dut_io_pads_gpio_2_o_ie;
  wire dut_io_pads_gpio_2_o_pue;
  wire dut_io_pads_gpio_2_o_ds;
  wire dut_io_pads_gpio_3_i_ival;
  wire dut_io_pads_gpio_3_o_oval;
  wire dut_io_pads_gpio_3_o_oe;
  wire dut_io_pads_gpio_3_o_ie;
  wire dut_io_pads_gpio_3_o_pue;
  wire dut_io_pads_gpio_3_o_ds;
  wire dut_io_pads_gpio_4_i_ival;
  wire dut_io_pads_gpio_4_o_oval;
  wire dut_io_pads_gpio_4_o_oe;
  wire dut_io_pads_gpio_4_o_ie;
  wire dut_io_pads_gpio_4_o_pue;
  wire dut_io_pads_gpio_4_o_ds;
  wire dut_io_pads_gpio_5_i_ival;
  wire dut_io_pads_gpio_5_o_oval;
  wire dut_io_pads_gpio_5_o_oe;
  wire dut_io_pads_gpio_5_o_ie;
  wire dut_io_pads_gpio_5_o_pue;
  wire dut_io_pads_gpio_5_o_ds;
  wire dut_io_pads_gpio_6_i_ival;
  wire dut_io_pads_gpio_6_o_oval;
  wire dut_io_pads_gpio_6_o_oe;
  wire dut_io_pads_gpio_6_o_ie;
  wire dut_io_pads_gpio_6_o_pue;
  wire dut_io_pads_gpio_6_o_ds;
  wire dut_io_pads_gpio_7_i_ival;
  wire dut_io_pads_gpio_7_o_oval;
  wire dut_io_pads_gpio_7_o_oe;
  wire dut_io_pads_gpio_7_o_ie;
  wire dut_io_pads_gpio_7_o_pue;
  wire dut_io_pads_gpio_7_o_ds;
  wire dut_io_pads_gpio_8_i_ival;
  wire dut_io_pads_gpio_8_o_oval;
  wire dut_io_pads_gpio_8_o_oe;
  wire dut_io_pads_gpio_8_o_ie;
  wire dut_io_pads_gpio_8_o_pue;
  wire dut_io_pads_gpio_8_o_ds;
  wire dut_io_pads_gpio_9_i_ival;
  wire dut_io_pads_gpio_9_o_oval;
  wire dut_io_pads_gpio_9_o_oe;
  wire dut_io_pads_gpio_9_o_ie;
  wire dut_io_pads_gpio_9_o_pue;
  wire dut_io_pads_gpio_9_o_ds;
  wire dut_io_pads_gpio_10_i_ival;
  wire dut_io_pads_gpio_10_o_oval;
  wire dut_io_pads_gpio_10_o_oe;
  wire dut_io_pads_gpio_10_o_ie;
  wire dut_io_pads_gpio_10_o_pue;
  wire dut_io_pads_gpio_10_o_ds;
  wire dut_io_pads_gpio_11_i_ival;
  wire dut_io_pads_gpio_11_o_oval;
  wire dut_io_pads_gpio_11_o_oe;
  wire dut_io_pads_gpio_11_o_ie;
  wire dut_io_pads_gpio_11_o_pue;
  wire dut_io_pads_gpio_11_o_ds;
  wire dut_io_pads_gpio_12_i_ival;
  wire dut_io_pads_gpio_12_o_oval;
  wire dut_io_pads_gpio_12_o_oe;
  wire dut_io_pads_gpio_12_o_ie;
  wire dut_io_pads_gpio_12_o_pue;
  wire dut_io_pads_gpio_12_o_ds;
  wire dut_io_pads_gpio_13_i_ival;
  wire dut_io_pads_gpio_13_o_oval;
  wire dut_io_pads_gpio_13_o_oe;
  wire dut_io_pads_gpio_13_o_ie;
  wire dut_io_pads_gpio_13_o_pue;
  wire dut_io_pads_gpio_13_o_ds;
  wire dut_io_pads_gpio_14_i_ival;
  wire dut_io_pads_gpio_14_o_oval;
  wire dut_io_pads_gpio_14_o_oe;
  wire dut_io_pads_gpio_14_o_ie;
  wire dut_io_pads_gpio_14_o_pue;
  wire dut_io_pads_gpio_14_o_ds;
  wire dut_io_pads_gpio_15_i_ival;
  wire dut_io_pads_gpio_15_o_oval;
  wire dut_io_pads_gpio_15_o_oe;
  wire dut_io_pads_gpio_15_o_ie;
  wire dut_io_pads_gpio_15_o_pue;
  wire dut_io_pads_gpio_15_o_ds;
  wire dut_io_pads_gpio_16_i_ival;
  wire dut_io_pads_gpio_16_o_oval;
  wire dut_io_pads_gpio_16_o_oe;
  wire dut_io_pads_gpio_16_o_ie;
  wire dut_io_pads_gpio_16_o_pue;
  wire dut_io_pads_gpio_16_o_ds;
  wire dut_io_pads_gpio_17_i_ival;
  wire dut_io_pads_gpio_17_o_oval;
  wire dut_io_pads_gpio_17_o_oe;
  wire dut_io_pads_gpio_17_o_ie;
  wire dut_io_pads_gpio_17_o_pue;
  wire dut_io_pads_gpio_17_o_ds;
  wire dut_io_pads_gpio_18_i_ival;
  wire dut_io_pads_gpio_18_o_oval;
  wire dut_io_pads_gpio_18_o_oe;
  wire dut_io_pads_gpio_18_o_ie;
  wire dut_io_pads_gpio_18_o_pue;
  wire dut_io_pads_gpio_18_o_ds;
  wire dut_io_pads_gpio_19_i_ival;
  wire dut_io_pads_gpio_19_o_oval;
  wire dut_io_pads_gpio_19_o_oe;
  wire dut_io_pads_gpio_19_o_ie;
  wire dut_io_pads_gpio_19_o_pue;
  wire dut_io_pads_gpio_19_o_ds;
  wire dut_io_pads_gpio_20_i_ival;
  wire dut_io_pads_gpio_20_o_oval;
  wire dut_io_pads_gpio_20_o_oe;
  wire dut_io_pads_gpio_20_o_ie;
  wire dut_io_pads_gpio_20_o_pue;
  wire dut_io_pads_gpio_20_o_ds;
  wire dut_io_pads_gpio_21_i_ival;
  wire dut_io_pads_gpio_21_o_oval;
  wire dut_io_pads_gpio_21_o_oe;
  wire dut_io_pads_gpio_21_o_ie;
  wire dut_io_pads_gpio_21_o_pue;
  wire dut_io_pads_gpio_21_o_ds;
  wire dut_io_pads_gpio_22_i_ival;
  wire dut_io_pads_gpio_22_o_oval;
  wire dut_io_pads_gpio_22_o_oe;
  wire dut_io_pads_gpio_22_o_ie;
  wire dut_io_pads_gpio_22_o_pue;
  wire dut_io_pads_gpio_22_o_ds;
  wire dut_io_pads_gpio_23_i_ival;
  wire dut_io_pads_gpio_23_o_oval;
  wire dut_io_pads_gpio_23_o_oe;
  wire dut_io_pads_gpio_23_o_ie;
  wire dut_io_pads_gpio_23_o_pue;
  wire dut_io_pads_gpio_23_o_ds;
  wire dut_io_pads_gpio_24_i_ival;
  wire dut_io_pads_gpio_24_o_oval;
  wire dut_io_pads_gpio_24_o_oe;
  wire dut_io_pads_gpio_24_o_ie;
  wire dut_io_pads_gpio_24_o_pue;
  wire dut_io_pads_gpio_24_o_ds;
  wire dut_io_pads_gpio_25_i_ival;
  wire dut_io_pads_gpio_25_o_oval;
  wire dut_io_pads_gpio_25_o_oe;
  wire dut_io_pads_gpio_25_o_ie;
  wire dut_io_pads_gpio_25_o_pue;
  wire dut_io_pads_gpio_25_o_ds;
  wire dut_io_pads_gpio_26_i_ival;
  wire dut_io_pads_gpio_26_o_oval;
  wire dut_io_pads_gpio_26_o_oe;
  wire dut_io_pads_gpio_26_o_ie;
  wire dut_io_pads_gpio_26_o_pue;
  wire dut_io_pads_gpio_26_o_ds;
  wire dut_io_pads_gpio_27_i_ival;
  wire dut_io_pads_gpio_27_o_oval;
  wire dut_io_pads_gpio_27_o_oe;
  wire dut_io_pads_gpio_27_o_ie;
  wire dut_io_pads_gpio_27_o_pue;
  wire dut_io_pads_gpio_27_o_ds;
  wire dut_io_pads_gpio_28_i_ival;
  wire dut_io_pads_gpio_28_o_oval;
  wire dut_io_pads_gpio_28_o_oe;
  wire dut_io_pads_gpio_28_o_ie;
  wire dut_io_pads_gpio_28_o_pue;
  wire dut_io_pads_gpio_28_o_ds;
  wire dut_io_pads_gpio_29_i_ival;
  wire dut_io_pads_gpio_29_o_oval;
  wire dut_io_pads_gpio_29_o_oe;
  wire dut_io_pads_gpio_29_o_ie;
  wire dut_io_pads_gpio_29_o_pue;
  wire dut_io_pads_gpio_29_o_ds;
  wire dut_io_pads_qspi_sck_i_ival;
  wire dut_io_pads_qspi_sck_o_oval;
  wire dut_io_pads_qspi_sck_o_oe;
  wire dut_io_pads_qspi_sck_o_ie;
  wire dut_io_pads_qspi_sck_o_pue;
  wire dut_io_pads_qspi_sck_o_ds;
  wire dut_io_pads_qspi_dq_0_i_ival;
  wire dut_io_pads_qspi_dq_0_o_oval;
  wire dut_io_pads_qspi_dq_0_o_oe;
  wire dut_io_pads_qspi_dq_0_o_ie;
  wire dut_io_pads_qspi_dq_0_o_pue;
  wire dut_io_pads_qspi_dq_0_o_ds;
  wire dut_io_pads_qspi_dq_1_i_ival;
  wire dut_io_pads_qspi_dq_1_o_oval;
  wire dut_io_pads_qspi_dq_1_o_oe;
  wire dut_io_pads_qspi_dq_1_o_ie;
  wire dut_io_pads_qspi_dq_1_o_pue;
  wire dut_io_pads_qspi_dq_1_o_ds;
  wire dut_io_pads_qspi_dq_2_i_ival;
  wire dut_io_pads_qspi_dq_2_o_oval;
  wire dut_io_pads_qspi_dq_2_o_oe;
  wire dut_io_pads_qspi_dq_2_o_ie;
  wire dut_io_pads_qspi_dq_2_o_pue;
  wire dut_io_pads_qspi_dq_2_o_ds;
  wire dut_io_pads_qspi_dq_3_i_ival;
  wire dut_io_pads_qspi_dq_3_o_oval;
  wire dut_io_pads_qspi_dq_3_o_oe;
  wire dut_io_pads_qspi_dq_3_o_ie;
  wire dut_io_pads_qspi_dq_3_o_pue;
  wire dut_io_pads_qspi_dq_3_o_ds;
  wire dut_io_pads_qspi_cs_0_i_ival;
  wire dut_io_pads_qspi_cs_0_o_oval;
  wire dut_io_pads_qspi_cs_0_o_oe;
  wire dut_io_pads_qspi_cs_0_o_ie;
  wire dut_io_pads_qspi_cs_0_o_pue;
  wire dut_io_pads_qspi_cs_0_o_ds;
  wire dut_io_pads_aon_erst_n_i_ival;
  wire dut_io_pads_aon_erst_n_o_oval;
  wire dut_io_pads_aon_erst_n_o_oe;
  wire dut_io_pads_aon_erst_n_o_ie;
  wire dut_io_pads_aon_erst_n_o_pue;
  wire dut_io_pads_aon_erst_n_o_ds;
  wire dut_io_pads_aon_lfextclk_i_ival;
  wire dut_io_pads_aon_lfextclk_o_oval;
  wire dut_io_pads_aon_lfextclk_o_oe;
  wire dut_io_pads_aon_lfextclk_o_ie;
  wire dut_io_pads_aon_lfextclk_o_pue;
  wire dut_io_pads_aon_lfextclk_o_ds;
  wire dut_io_pads_aon_pmu_dwakeup_n_i_ival;
  wire dut_io_pads_aon_pmu_dwakeup_n_o_oval;
  wire dut_io_pads_aon_pmu_dwakeup_n_o_oe;
  wire dut_io_pads_aon_pmu_dwakeup_n_o_ie;
  wire dut_io_pads_aon_pmu_dwakeup_n_o_pue;
  wire dut_io_pads_aon_pmu_dwakeup_n_o_ds;
  wire dut_io_pads_aon_pmu_vddpaden_i_ival;
  wire dut_io_pads_aon_pmu_vddpaden_o_oval;
  wire dut_io_pads_aon_pmu_vddpaden_o_oe;
  wire dut_io_pads_aon_pmu_vddpaden_o_ie;
  wire dut_io_pads_aon_pmu_vddpaden_o_pue;
  wire dut_io_pads_aon_pmu_vddpaden_o_ds;

  //=================================================
  // Clock & Reset

  wire SRST_n; // From FTDI Chip

  mmcm ip_mmcm
  (
    .clk_in1(CLK100MHZ),
    .clk_out1(clk_out1), // 8.388 MHz = 32.768 kHz * 256
    .clk_out2(hfclk), // 65 MHz
    .resetn(ck_rst),
    .locked(mmcm_locked)
  );

  wire slowclk;
  clkdivider slowclkgen
  (
    .clk(clk_out1),
    .reset(~mmcm_locked),
    .clk_out(slowclk)
  );

  reset_sys ip_reset_sys
  (
    .slowest_sync_clk(clk_out1),
    .ext_reset_in(ck_rst & SRST_n), // Active-low
    .aux_reset_in(1'b1),
    .mb_debug_sys_rst(1'b0),
    .dcm_locked(mmcm_locked),
    .mb_reset(reset_core),
    .bus_struct_reset(reset_bus),
    .peripheral_reset(reset_periph),
    .interconnect_aresetn(reset_intcon_n),
    .peripheral_aresetn(reset_periph_n)
  );

  //=================================================
  // SPI Interface

  wire [3:0] qspi_ui_dq_o, qspi_ui_dq_oe;
  wire [3:0] qspi_ui_dq_i;

  PULLUP qspi_pullup[3:0]
  (
    .O(qspi_dq)
  );

  IOBUF qspi_iobuf[3:0]
  (
    .IO(qspi_dq),
    .O(qspi_ui_dq_i),
    .I(qspi_ui_dq_o),
    .T(~qspi_ui_dq_oe)
  );

  //=================================================
  // IOBUF instantiation for GPIOs.
  // Convert an inout to input, output, and drive wires.
  // _o = output wire
  // _io = inout (for external connection)
  // _i = input data
  // _oe = output enabled (true to drive, false to tristate)
  // TODO: automatically generate these

  wire btn_0_o;
  wire btn_0_io;
  wire btn_0_i;
  wire btn_0_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_btn_0
  (
    .O(btn_0_o),
    .IO(btn_0_io),
    .I(btn_0_i),
    .T(~btn_0_oe)
  );

  wire btn_1_o;
  wire btn_1_io;
  wire btn_1_i;
  wire btn_1_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_btn_1
  (
    .O(btn_1_o),
    .IO(btn_1_io),
    .I(btn_1_i),
    .T(~btn_1_oe)
  );

  wire btn_2_o;
  wire btn_2_io;
  wire btn_2_i;
  wire btn_2_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_btn_2
  (
    .O(btn_2_o),
    .IO(btn_2_io),
    .I(btn_2_i),
    .T(~btn_2_oe)
  );

  wire btn_3_o;
  wire btn_3_io;
  wire btn_3_i;
  wire btn_3_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_btn_3
  (
    .O(btn_3_o),
    .IO(btn_3_io),
    .I(btn_3_i),
    .T(~btn_3_oe)
  );

  wire ja_0_o;
  wire ja_0_io;
  wire ja_0_i;
  wire ja_0_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_0
  (
    .O(ja_0_o),
    .IO(ja_0_io),
    .I(ja_0_i),
    .T(~ja_0_oe)
  );

  wire ja_1_o;
  wire ja_1_io;
  wire ja_1_i;
  wire ja_1_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_1
  (
    .O(ja_1_o),
    .IO(ja_1_io),
    .I(ja_1_i),
    .T(~ja_1_oe)
  );

  wire ja_2_o;
  wire ja_2_io;
  wire ja_2_i;
  wire ja_2_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_2
  (
    .O(ja_2_o),
    .IO(ja_2_io),
    .I(ja_2_i),
    .T(~ja_2_oe)
  );

  wire ja_3_o;
  wire ja_3_io;
  wire ja_3_i;
  wire ja_3_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_3
  (
    .O(ja_3_o),
    .IO(ja_3_io),
    .I(ja_3_i),
    .T(~ja_3_oe)
  );

  wire ja_4_o;
  wire ja_4_io;
  wire ja_4_i;
  wire ja_4_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_4
  (
    .O(ja_4_o),
    .IO(ja_4_io),
    .I(ja_4_i),
    .T(~ja_4_oe)
  );

  wire ja_5_o;
  wire ja_5_io;
  wire ja_5_i;
  wire ja_5_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_5
  (
    .O(ja_5_o),
    .IO(ja_5_io),
    .I(ja_5_i),
    .T(~ja_5_oe)
  );

  wire ja_6_o;
  wire ja_6_io;
  wire ja_6_i;
  wire ja_6_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_6
  (
    .O(ja_6_o),
    .IO(ja_6_io),
    .I(ja_6_i),
    .T(~ja_6_oe)
  );

  wire ja_7_o;
  wire ja_7_io;
  wire ja_7_i;
  wire ja_7_oe;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_ja_7
  (
    .O(ja_7_o),
    .IO(ja_7_io),
    .I(ja_7_i),
    .T(~ja_7_oe)
  );

  wire gpio_0;
  wire gpio_1;
  wire gpio_2;
  wire gpio_3;
  wire gpio_4;
  wire gpio_5;
  wire gpio_6;
  wire gpio_7;
  wire gpio_8;
  wire gpio_9;
  wire gpio_10;
  wire gpio_11;
  wire gpio_12;
  wire gpio_13;
  wire gpio_14;
  wire gpio_15;
  wire gpio_16;
  wire gpio_17;
  wire gpio_18;
  wire gpio_19;
  wire gpio_20;
  wire gpio_21;
  wire gpio_22;
  wire gpio_23;
  wire gpio_25;
  wire gpio_26;
  wire gpio_27;
  wire gpio_28;
  wire gpio_29;
  wire gpio_30;
  wire gpio_31;

  wire iobuf_gpio_0_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_0
  (
    .O(iobuf_gpio_0_o),
    .IO(gpio_0),
    .I(dut_io_pads_gpio_0_o_oval),
    .T(~dut_io_pads_gpio_0_o_oe)
  );
  assign dut_io_pads_gpio_0_i_ival = iobuf_gpio_0_o & dut_io_pads_gpio_0_o_ie;

  wire iobuf_gpio_1_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_1
  (
    .O(iobuf_gpio_1_o),
    .IO(gpio_1),
    .I(dut_io_pads_gpio_1_o_oval),
    .T(~dut_io_pads_gpio_1_o_oe)
  );
  assign dut_io_pads_gpio_1_i_ival = iobuf_gpio_1_o & dut_io_pads_gpio_1_o_ie;

  wire iobuf_gpio_2_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_2
  (
    .O(iobuf_gpio_2_o),
    .IO(gpio_2),
    .I(dut_io_pads_gpio_2_o_oval),
    .T(~dut_io_pads_gpio_2_o_oe)
  );
  assign dut_io_pads_gpio_2_i_ival = iobuf_gpio_2_o & dut_io_pads_gpio_2_o_ie;

  wire iobuf_gpio_3_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_3
  (
    .O(iobuf_gpio_3_o),
    .IO(gpio_3),
    .I(dut_io_pads_gpio_3_o_oval),
    .T(~dut_io_pads_gpio_3_o_oe)
  );
  assign dut_io_pads_gpio_3_i_ival = iobuf_gpio_3_o & dut_io_pads_gpio_3_o_ie;

  wire iobuf_gpio_4_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_4
  (
    .O(iobuf_gpio_4_o),
    .IO(gpio_4),
    .I(dut_io_pads_gpio_4_o_oval),
    .T(~dut_io_pads_gpio_4_o_oe)
  );
  assign dut_io_pads_gpio_4_i_ival = iobuf_gpio_4_o & dut_io_pads_gpio_4_o_ie;

  wire iobuf_gpio_5_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_5
  (
    .O(iobuf_gpio_5_o),
    .IO(gpio_5),
    .I(dut_io_pads_gpio_5_o_oval),
    .T(~dut_io_pads_gpio_5_o_oe)
  );
  assign dut_io_pads_gpio_5_i_ival = iobuf_gpio_5_o & dut_io_pads_gpio_5_o_ie;

  assign dut_io_pads_gpio_6_i_ival = 1'b0;

  assign dut_io_pads_gpio_7_i_ival = 1'b0;

  assign dut_io_pads_gpio_8_i_ival = 1'b0;

  wire iobuf_gpio_9_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_9
  (
    .O(iobuf_gpio_9_o),
    .IO(gpio_9),
    .I(dut_io_pads_gpio_9_o_oval),
    .T(~dut_io_pads_gpio_9_o_oe)
  );
  assign dut_io_pads_gpio_9_i_ival = iobuf_gpio_9_o & dut_io_pads_gpio_9_o_ie;

  wire iobuf_gpio_10_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_10
  (
    .O(iobuf_gpio_10_o),
    .IO(gpio_10),
    .I(dut_io_pads_gpio_10_o_oval),
    .T(~dut_io_pads_gpio_10_o_oe)
  );
  assign dut_io_pads_gpio_10_i_ival = iobuf_gpio_10_o & dut_io_pads_gpio_10_o_ie;

  wire iobuf_gpio_11_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_11
  (
    .O(iobuf_gpio_11_o),
    .IO(gpio_11),
    .I(dut_io_pads_gpio_11_o_oval),
    .T(~dut_io_pads_gpio_11_o_oe)
  );
  assign dut_io_pads_gpio_11_i_ival = iobuf_gpio_11_o & dut_io_pads_gpio_11_o_ie;

  wire iobuf_gpio_12_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_12
  (
    .O(iobuf_gpio_12_o),
    .IO(gpio_12),
    .I(dut_io_pads_gpio_12_o_oval),
    .T(~dut_io_pads_gpio_12_o_oe)
  );
  assign dut_io_pads_gpio_12_i_ival = iobuf_gpio_12_o & dut_io_pads_gpio_12_o_ie;

  wire iobuf_gpio_13_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_13
  (
    .O(iobuf_gpio_13_o),
    .IO(gpio_13),
    .I(dut_io_pads_gpio_13_o_oval),
    .T(~dut_io_pads_gpio_13_o_oe)
  );
  assign dut_io_pads_gpio_13_i_ival = iobuf_gpio_13_o & dut_io_pads_gpio_13_o_ie;

  wire iobuf_gpio_14_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_14
  (
    .O(iobuf_gpio_14_o),
    .IO(gpio_14),
    .I(dut_io_pads_gpio_14_o_oval),
    .T(~dut_io_pads_gpio_14_o_oe)
  );
  assign dut_io_pads_gpio_14_i_ival = iobuf_gpio_14_o & dut_io_pads_gpio_14_o_ie;

  wire iobuf_gpio_16_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_16
  (
    .O(iobuf_gpio_16_o),
    .IO(gpio_16),
    .I(dut_io_pads_gpio_16_o_oval),
    .T(~dut_io_pads_gpio_16_o_oe)
  );
  // This GPIO input is shared between FTDI TX pin and Arduino shield pin using SW[3]
  // see below for details
  assign dut_io_pads_gpio_16_i_ival = sw_3 ? (iobuf_gpio_16_o & dut_io_pads_gpio_16_o_ie) : (uart_txd_in & dut_io_pads_gpio_16_o_ie);

  wire iobuf_gpio_17_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_17
  (
    .O(iobuf_gpio_17_o),
    .IO(gpio_17),
    .I(dut_io_pads_gpio_17_o_oval),
    .T(~dut_io_pads_gpio_17_o_oe)
  );
  assign dut_io_pads_gpio_17_i_ival = iobuf_gpio_17_o & dut_io_pads_gpio_17_o_ie;
  assign uart_rxd_out = (dut_io_pads_gpio_17_o_oval & dut_io_pads_gpio_17_o_oe);

  wire iobuf_gpio_18_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_18
  (
    .O(iobuf_gpio_18_o),
    .IO(gpio_18),
    .I(dut_io_pads_gpio_18_o_oval),
    .T(~dut_io_pads_gpio_18_o_oe)
  );
  assign dut_io_pads_gpio_18_i_ival = iobuf_gpio_18_o & dut_io_pads_gpio_18_o_ie;

  wire iobuf_gpio_19_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_19
  (
    .O(iobuf_gpio_19_o),
    .IO(gpio_19),
    .I(dut_io_pads_gpio_19_o_oval),
    .T(~dut_io_pads_gpio_19_o_oe)
  );
  assign dut_io_pads_gpio_19_i_ival = iobuf_gpio_19_o & dut_io_pads_gpio_19_o_ie;

  wire iobuf_gpio_20_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_20
  (
    .O(iobuf_gpio_20_o),
    .IO(gpio_20),
    .I(dut_io_pads_gpio_20_o_oval),
    .T(~dut_io_pads_gpio_20_o_oe)
  );
  assign dut_io_pads_gpio_20_i_ival = iobuf_gpio_20_o & dut_io_pads_gpio_20_o_ie;

  wire iobuf_gpio_21_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_21
  (
    .O(iobuf_gpio_21_o),
    .IO(gpio_21),
    .I(dut_io_pads_gpio_21_o_oval),
    .T(~dut_io_pads_gpio_21_o_oe)
  );
  assign dut_io_pads_gpio_21_i_ival = iobuf_gpio_21_o & dut_io_pads_gpio_21_o_ie;

  wire iobuf_gpio_22_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_22
  (
    .O(iobuf_gpio_22_o),
    .IO(gpio_22),
    .I(dut_io_pads_gpio_22_o_oval),
    .T(~dut_io_pads_gpio_22_o_oe)
  );
  assign dut_io_pads_gpio_22_i_ival = iobuf_gpio_22_o & dut_io_pads_gpio_22_o_ie;

  wire iobuf_gpio_23_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_23
  (
    .O(iobuf_gpio_23_o),
    .IO(gpio_23),
    .I(dut_io_pads_gpio_23_o_oval),
    .T(~dut_io_pads_gpio_23_o_oe)
  );
  assign dut_io_pads_gpio_23_i_ival = iobuf_gpio_23_o & dut_io_pads_gpio_23_o_ie;

  wire iobuf_gpio_25_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_25
  (
    .O(iobuf_gpio_25_o),
    .IO(gpio_25),
    .I(dut_io_pads_gpio_25_o_oval),
    .T(~dut_io_pads_gpio_25_o_oe)
  );
  assign dut_io_pads_gpio_25_i_ival = iobuf_gpio_25_o & dut_io_pads_gpio_25_o_ie;

  wire iobuf_gpio_26_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_26
  (
    .O(iobuf_gpio_26_o),
    .IO(gpio_26),
    .I(dut_io_pads_gpio_26_o_oval),
    .T(~dut_io_pads_gpio_26_o_oe)
  );
  assign dut_io_pads_gpio_26_i_ival = iobuf_gpio_26_o & dut_io_pads_gpio_26_o_ie;

  wire iobuf_gpio_27_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_27
  (
    .O(iobuf_gpio_27_o),
    .IO(gpio_27),
    .I(dut_io_pads_gpio_27_o_oval),
    .T(~dut_io_pads_gpio_27_o_oe)
  );
  assign dut_io_pads_gpio_27_i_ival = iobuf_gpio_27_o & dut_io_pads_gpio_27_o_ie;

  wire iobuf_gpio_28_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_28
  (
    .O(iobuf_gpio_28_o),
    .IO(gpio_28),
    .I(dut_io_pads_gpio_28_o_oval),
    .T(~dut_io_pads_gpio_28_o_oe)
  );
  assign dut_io_pads_gpio_28_i_ival = iobuf_gpio_28_o & dut_io_pads_gpio_28_o_ie;

  wire iobuf_gpio_29_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_gpio_29
  (
    .O(iobuf_gpio_29_o),
    .IO(gpio_29),
    .I(dut_io_pads_gpio_29_o_oval),
    .T(~dut_io_pads_gpio_29_o_oe)
  );
  assign dut_io_pads_gpio_29_i_ival = iobuf_gpio_29_o & dut_io_pads_gpio_29_o_ie;

  //=================================================
  // JTAG IOBUFs

  wire iobuf_jtag_TCK_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_jtag_TCK
  (
    .O(iobuf_jtag_TCK_o),
    .IO(jd_2),
    .I(dut_io_pads_jtag_TCK_o_oval),
    .T(~dut_io_pads_jtag_TCK_o_oe)
  );
  assign dut_io_pads_jtag_TCK_i_ival = iobuf_jtag_TCK_o & dut_io_pads_jtag_TCK_o_ie;
  PULLUP pullup_TCK (.O(jd_2));

  wire iobuf_jtag_TMS_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_jtag_TMS
  (
    .O(iobuf_jtag_TMS_o),
    .IO(jd_5),
    .I(dut_io_pads_jtag_TMS_o_oval),
    .T(~dut_io_pads_jtag_TMS_o_oe)
  );
  assign dut_io_pads_jtag_TMS_i_ival = iobuf_jtag_TMS_o & dut_io_pads_jtag_TMS_o_ie;
  PULLUP pullup_TMS (.O(jd_5));

  wire iobuf_jtag_TDI_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_jtag_TDI
  (
    .O(iobuf_jtag_TDI_o),
    .IO(jd_4),
    .I(dut_io_pads_jtag_TDI_o_oval),
    .T(~dut_io_pads_jtag_TDI_o_oe)
  );
  assign dut_io_pads_jtag_TDI_i_ival = iobuf_jtag_TDI_o & dut_io_pads_jtag_TDI_o_ie;
  PULLUP pullup_TDI (.O(jd_4));

  wire iobuf_jtag_TDO_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_jtag_TDO
  (
    .O(iobuf_jtag_TDO_o),
    .IO(jd_0),
    .I(dut_io_pads_jtag_TDO_o_oval),
    .T(~dut_io_pads_jtag_TDO_o_oe)
  );
  assign dut_io_pads_jtag_TDO_i_ival = iobuf_jtag_TDO_o & dut_io_pads_jtag_TDO_o_ie;

  wire iobuf_jtag_TRST_n_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_jtag_TRST_n
  (
    .O(iobuf_jtag_TRST_n_o),
    .IO(jd_1),
    .I(dut_io_pads_jtag_TRST_n_o_oval),
    .T(~dut_io_pads_jtag_TRST_n_o_oe)
  );
  assign dut_io_pads_jtag_TRST_n_i_ival = iobuf_jtag_TRST_n_o & dut_io_pads_jtag_TRST_n_o_ie;
  PULLUP pullup_TRST_n(.O(jd_1));

  // Mimic putting a pullup on this line (part of reset vote).
  assign SRST_n = jd_6;
  PULLUP pullup_SRST_n(.O(SRST_n));

  //=================================================
  // Assignment of IOBUF "IO" pins to package pins

  // Pins IO0-IO13
  // Shield header row 0: PD0-PD7

  // FTDI UART TX/RX are not connected to ck_io[1,2]
  // the way they are on Arduino boards.  We copy outgoing
  // data to both places, switch 3 (sw[3]) determines whether
  // input to UART comes from FTDI chip or gpio_16 (shield pin PD0)

  assign ck_io[0] = gpio_16; // UART0 RX
  assign ck_io[1] = gpio_17; // UART0 TX
  assign ck_io[2] = gpio_18;
  assign ck_io[3] = gpio_19; // PWM1(1)
  assign ck_io[4] = gpio_20; // PWM1(0)
  assign ck_io[5] = gpio_21; // PWM1(2)
  assign ck_io[6] = gpio_22; // PWM1(3)
  assign ck_io[7] = gpio_23;
  // Header row 1: PB0-PB5
  assign ck_io[8] = gpio_0; // PWM0(0)
  assign ck_io[9] = gpio_1; // PWM0(1)
  assign ck_io[10] = gpio_2; // SPI1 CS(0) / PWM0(2)
  assign ck_io[11] = gpio_3; // SPI1 MOSI / PWM0(3)
  assign ck_io[12] = gpio_4; // SPI1 MISO
  assign ck_io[13] = gpio_5; // SPI1 SCK

  // Header row 3: A0-A5 (we don't support using them as analog inputs)
  // just treat them as regular digital GPIOs
  assign ck_io[14] = uart_txd_in; //gpio_9;  // A0 = <unconnected> CS(1)
  assign ck_io[15] = gpio_9; // A1 = CS(2)
  assign ck_io[16] = gpio_10; // A2 = CS(3) / PWM2(0)
  assign ck_io[17] = gpio_11; // A3 = PWM2(1)
  assign ck_io[18] = gpio_12; // A4 = PWM2(2) / SDA
  assign ck_io[19] = gpio_13; // A5 = PWM2(3) / SCL

  // Only 19 out of 20 shield pins connected to GPIO pads
  // Shield pin A5 (pin 14) left unconnected
  // The buttons are connected to some extra GPIO pads not connected on the
  // HiFive1 board

  assign btn_0 = btn_0_io;
  assign btn_1 = gpio_30;
  assign btn_2 = gpio_31;

  assign ja_0 = ja_0_io;
  assign ja_1 = ja_1_io;
  assign ja_2 = ja_2_io;
  assign ja_3 = ja_3_io;
  assign ja_4 = ja_4_io;
  assign ja_5 = ja_5_io;
  assign ja_6 = ja_6_io;
  assign ja_7 = ja_7_io;

  // SPI2 pins mapped to 6 pin ICSP connector (standard on later arduinos)
  // These are connected to some extra GPIO pads not connected on the HiFive1
  // board
  assign ck_ss = gpio_26;
  assign ck_mosi = gpio_27;
  assign ck_miso = gpio_28;
  assign ck_sck = gpio_29;

  // Instantiate the top-level Verilog module here.
  // Do not alter the following line (auto-generated by PLSI).
  // ***PLSI_REPLACE_ME***
  // End auto-generated section.

  // Assign reasonable values to otherwise unconnected inputs to chip top

  wire iobuf_dwakeup_o;
  IOBUF
  #(
    .DRIVE(12),
    .IBUF_LOW_PWR("TRUE"),
    .IOSTANDARD("DEFAULT"),
    .SLEW("SLOW")
  )
  IOBUF_dwakeup_n
  (
    .O(iobuf_dwakeup_o),
    .IO(btn_3),
    .I(~dut_io_pads_aon_pmu_dwakeup_n_o_oval),
    .T(~dut_io_pads_aon_pmu_dwakeup_n_o_oe)
  );
  assign dut_io_pads_aon_pmu_dwakeup_n_i_ival = (~iobuf_dwakeup_o) & dut_io_pads_aon_pmu_dwakeup_n_o_ie;

  assign dut_io_pads_aon_erst_n_i_ival = ~reset_periph;
  assign dut_io_pads_aon_lfextclk_i_ival = slowclk;

  assign dut_io_pads_aon_pmu_vddpaden_i_ival = 1'b1;

  assign qspi_cs = dut_io_pads_qspi_cs_0_o_oval;
  assign qspi_ui_dq_o = {
    dut_io_pads_qspi_dq_3_o_oval,
    dut_io_pads_qspi_dq_2_o_oval,
    dut_io_pads_qspi_dq_1_o_oval,
    dut_io_pads_qspi_dq_0_o_oval
  };
  assign qspi_ui_dq_oe = {
    dut_io_pads_qspi_dq_3_o_oe,
    dut_io_pads_qspi_dq_2_o_oe,
    dut_io_pads_qspi_dq_1_o_oe,
    dut_io_pads_qspi_dq_0_o_oe
  };
  assign dut_io_pads_qspi_dq_0_i_ival = qspi_ui_dq_i[0];
  assign dut_io_pads_qspi_dq_1_i_ival = qspi_ui_dq_i[1];
  assign dut_io_pads_qspi_dq_2_i_ival = qspi_ui_dq_i[2];
  assign dut_io_pads_qspi_dq_3_i_ival = qspi_ui_dq_i[3];
  assign qspi_sck = dut_io_pads_qspi_sck_o_oval;
endmodule

// Divide clock by 256, used to generate 32.768 kHz clock for AON block
module clkdivider
(
  input wire clk,
  input wire reset,
  output reg clk_out
);

  reg [7:0] counter;

  always @(posedge clk)
  begin
    if (reset)
    begin
      counter <= 8'd0;
      clk_out <= 1'b0;
    end
    else if (counter == 8'hff)
    begin
      counter <= 8'd0;
      clk_out <= ~clk_out;
    end
    else
    begin
      counter <= counter+1;
    end
  end
endmodule
