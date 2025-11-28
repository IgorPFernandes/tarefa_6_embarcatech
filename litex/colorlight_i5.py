#!/usr/bin/env python3

#
# Este arquivo faz parte do Sistema de Placas LiteX.
#
# Copyright (c) 2021 Kazumoto Kojima <kkojima@rr.iij4u.or.jp>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.gen import *

from litex.build.io import DDROutput

from litex_boards.platforms import colorlight_i5

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.video import VideoHDMIPHY
from litex.soc.cores.led import LedChaser

from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.gpio import GPIOOut
from litex.build.generic_platform import Subsignal, Pins, IOStandard


from litex.soc.interconnect.csr import *

from litedram.modules import M12L64322A # Compatível com EM638325-6H.
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY

from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII

# Gerenciamento de Relógio (CLK_MGR) ----------------------------------------------------------------------------------------------

class _ClkMgr(LiteXModule):
    def __init__(self, placa, clk_sys_freq, use_int_osc=False, with_usb_clk=False, with_vid_clk=False, sdram_ratio="1:1"):
        self.rst_sig    = Signal()
        self.cd_sys_clk = ClockDomain()
        if sdram_ratio == "1:2":
            self.cd_sys2x_clk    = ClockDomain()
            self.cd_sys2x_ps_clk = ClockDomain()
        else:
            self.cd_sys_ps_clk = ClockDomain()

        # # #

        # Relógio Principal / Reset
        if not use_int_osc:
            clkin = placa.request("clk25")
            clkin_freq = 25e6
        else:
            clkin = Signal()
            divisor = 5
            self.specials += Instance("OSCG",
                p_DIV = divisor,
                o_OSC = clkin
            )
            clkin_freq = 310e6/divisor

        rst_n_sig = placa.request("cpu_reset_n")

        # PLL Principal
        self.pll_main = pll_unit = ECP5PLL()
        self.comb += pll_unit.reset.eq(~rst_n_sig | self.rst_sig)
        pll_unit.register_clkin(clkin, clkin_freq)
        pll_unit.create_clkout(self.cd_sys_clk,    clk_sys_freq)
        if sdram_ratio == "1:2":
            pll_unit.create_clkout(self.cd_sys2x_clk,    2*clk_sys_freq)
            pll_unit.create_clkout(self.cd_sys2x_ps_clk, 2*clk_sys_freq, phase=180) # 90° ideal, mas ajustado
        else:
           pll_unit.create_clkout(self.cd_sys_ps_clk, clk_sys_freq, phase=180) # 90° ideal, mas ajustado

        # PLL USB
        if with_usb_clk:
            self.pll_usb = pll_usb_unit = ECP5PLL()
            self.comb += pll_usb_unit.reset.eq(~rst_n_sig | self.rst_sig)
            pll_usb_unit.register_clkin(clkin, clkin_freq)
            self.cd_usb_12m = ClockDomain()
            self.cd_usb_48m = ClockDomain()
            pll_usb_unit.create_clkout(self.cd_usb_12m, 12e6, margin=0)
            pll_usb_unit.create_clkout(self.cd_usb_48m, 48e6, margin=0)

        # PLL Vídeo
        if with_vid_clk:
            self.pll_video = pll_vid_unit = ECP5PLL()
            self.comb += pll_vid_unit.reset.eq(~rst_n_sig | self.rst_sig)
            pll_vid_unit.register_clkin(clkin, clkin_freq)
            self.cd_hdmi_clk   = ClockDomain()
            self.cd_hdmi5x_clk = ClockDomain()
            pll_vid_unit.create_clkout(self.cd_hdmi_clk,    40e6, margin=0)
            pll_vid_unit.create_clkout(self.cd_hdmi5x_clk, 200e6, margin=0)

        # Relógio SDRAM (DDR)
        sdram_clk_out = ClockSignal("sys2x_ps_clk" if sdram_ratio == "1:2" else "sys_ps_clk")
        self.specials += DDROutput(1, 0, placa.request("sdram_clock"), sdram_clk_out)

# Sistema Base (BASE_SYS) ------------------------------------------------------------------------------------------

class BaseSystem(SoCCore):
    def __init__(self, placa_nome="i5", rev="7.0", toolchain="trellis", clk_frequencia=60e6,
        use_eth                = False,
        use_ethbone            = False,
        ip_local               = "",
        ip_remoto              = "",
        eth_physic             = 0,
        with_led_chaser        = True,
        use_internal_osc       = False,
        sdram_ratio            = "1:1",
        with_video_terminal    = False,
        with_video_framebuffer = False,
        **kwds):
        placa_nome = placa_nome.lower()
        assert placa_nome in ["i5", "i9"]
        plataforma = colorlight_i5.Platform(board=placa_nome, revision=rev, toolchain=toolchain)

        # Gerenciamento de Relógio (CLK_MGR) --------------------------------------------------------------------------------------
        with_usb_clk   = kwds.get("uart_name", None) == "usb_acm"
        with_vid_clk = with_video_terminal or with_video_framebuffer
        self.clock_manager = _ClkMgr(plataforma, clk_frequencia,
            use_int_osc      = use_internal_osc,
            with_usb_clk     = with_usb_clk,
            with_vid_clk     = with_vid_clk,
            sdram_ratio      = sdram_ratio
        )

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, plataforma, int(clk_frequencia), ident = "LiteX System on Colorlight " + placa_nome.upper() + " Board", **kwds)

        # LEDs -------------------------------------------------------------------------------------
        if with_led_chaser:
            led_pins = plataforma.request_all("user_led_n")
            self.leds_controller = LedChaser(pads=led_pins, sys_clk_freq=clk_frequencia)

        # Periférico SPI (N2 Header) - PINAGENS ALTERADAS ------------------------------------------
        spi_pinagem = [
            ("spi_perif", 0,
                Subsignal("clk",  Pins("F2")), # Era G20
                Subsignal("mosi", Pins("E2")), # Era L18
                Subsignal("miso", Pins("D2")), # Era M18
                Subsignal("cs_n", Pins("C2")), # Era N17
                IOStandard("LVCMOS33")
            ),
            ("lora_reset_pin", 0, Pins("G2"), IOStandard("LVCMOS33")) # Era L20
        ]

        plataforma.add_extension(spi_pinagem)

        self.spi = SPIMaster(pads=plataforma.request("spi_perif"), data_width=8, sys_clk_freq=clk_frequencia, spi_clk_freq=1e6)
        self.add_csr("spi")

        self.submodules.rst_lora = GPIOOut(plataforma.request("lora_reset_pin"))
        self.add_csr("rst_lora")

        # Periférico I2C (J1 Header) - PINAGENS ALTERADAS ------------------------------------------
        i2c_pinagem = [
            ("i2c_bus", 0,
                Subsignal("scl", Pins("H18")), # Era F3
                Subsignal("sda", Pins("J18")), # Era G3
                IOStandard("LVCMOS33")
            )
        ]

        plataforma.add_extension(i2c_pinagem)

        self.submodules.i2c_master = I2CMaster(pads=plataforma.request("i2c_bus"))
        self.add_csr("i2c_master")


        # Flash SPI --------------------------------------------------------------------------------
        if placa_nome == "i5":
            from litespi.modules import GD25Q16 as ModuloFlashSPI
        if placa_nome == "i9":
            from litespi.modules import W25Q64 as ModuloFlashSPI

        from litespi.opcodes import SpiNorFlashOpCodes as Codes
        self.add_spi_flash(mode="1x", module=ModuloFlashSPI(Codes.READ_1_1_1))

        # SDRAM SDR --------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            sdrphy_cls = HalfRateGENSDRPHY if sdram_ratio == "1:2" else GENSDRPHY
            self.sdrphy = sdrphy_cls(plataforma.request("sdram"))
            self.add_sdram("sdram",
                phy           = self.sdrphy,
                module        = M12L64322A(clk_frequencia, sdram_ratio),
                l2_cache_size = kwds.get("l2_size", 8192)
            )

        # Ethernet / Etherbone ---------------------------------------------------------------------
        if use_eth or use_ethbone:
            self.ethphy = LiteEthPHYRGMII(
                clock_pads = self.plataforma.request("eth_clocks", eth_physic),
                pads       = self.plataforma.request("eth", eth_physic),
                tx_delay = 0)
            if use_eth:
                self.add_ethernet(phy=self.ethphy)
            if use_ethbone:
                self.add_etherbone(phy=self.ethphy)

        if ip_local:
            local_ip_split = ip_local.split(".")
            self.add_constant("IP_LOCAL_1", int(local_ip_split[0]))
            self.add_constant("IP_LOCAL_2", int(local_ip_split[1]))
            self.add_constant("IP_LOCAL_3", int(local_ip_split[2]))
            self.add_constant("IP_LOCAL_4", int(local_ip_split[3]))

        if ip_remoto:
            remote_ip_split = ip_remoto.split(".")
            self.add_constant("IP_REMOTO_1", int(remote_ip_split[0]))
            self.add_constant("IP_REMOTO_2", int(remote_ip_split[1]))
            self.add_constant("IP_REMOTO_3", int(remote_ip_split[2]))
            self.add_constant("IP_REMOTO_4", int(remote_ip_split[3]))

        # Vídeo ------------------------------------------------------------------------------------
        if with_video_terminal or with_video_framebuffer:
            self.video_physic = VideoHDMIPHY(plataforma.request("gpdi"), clock_domain="hdmi_clk")
            if with_video_terminal:
                self.add_video_terminal(phy=self.video_physic, timings="800x600@60Hz", clock_domain="hdmi_clk")
            if with_video_framebuffer:
                self.add_video_framebuffer(phy=self.video_physic, timings="800x600@60Hz", clock_domain="hdmi_clk")

# Construção (EXECUTAR) --------------------------------------------------------------------------------------------

def executar_main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=colorlight_i5.Platform, description="LiteX SoC no Colorlight I5.")
    parser.add_target_argument("--board",            default="i5",             help="Tipo de Placa (i5).")
    parser.add_target_argument("--revision",         default="7.0",            help="Revisão da Placa (7.0).")
    parser.add_target_argument("--sys-clk-freq",     default=60e6, type=float, help="Frequência do relógio do sistema.")
    ethopts = parser.target_group.add_mutually_exclusive_group()
    ethopts.add_argument("--with-ethernet",   action="store_true",      help="Habilitar suporte Ethernet.")
    ethopts.add_argument("--with-etherbone",  action="store_true",      help="Habilitar suporte Etherbone.")
    parser.add_target_argument("--remote-ip", default="192.168.1.100",  help="Endereço IP Remoto.")
    parser.add_target_argument("--local-ip",  default="192.168.1.50",   help="Endereço IP Local.")
    sdopts = parser.target_group.add_mutually_exclusive_group()
    sdopts.add_argument("--with-spi-sdcard",  action="store_true", help="Habilitar suporte SPI-mode SDCard.")
    sdopts.add_argument("--with-sdcard",      action="store_true", help="Habilitar suporte SDCard.")
    parser.add_target_argument("--eth-phy",          default=0, type=int, help="PHY Ethernet (0 ou 1).")
    parser.add_target_argument("--use-internal-osc", action="store_true", help="Usar oscilador interno.")
    parser.add_target_argument("--sdram-rate",       default="1:1",       help="Taxa SDRAM (1:1 Full Rate ou 1:2 Half Rate).")
    viopts = parser.target_group.add_mutually_exclusive_group()
    viopts.add_argument("--with-video-terminal",    action="store_true", help="Habilitar Terminal de Vídeo (HDMI).")
    viopts.add_argument("--with-video-framebuffer", action="store_true", help="Habilitar Framebuffer de Vídeo (HDMI).")
    args = parser.parse_args()

    soc_inst = BaseSystem(placa_nome=args.board, rev=args.revision,
        toolchain              = args.toolchain,
        clk_frequencia         = args.sys_clk_freq,
        use_eth                = args.with_ethernet,
        use_ethbone            = args.with_etherbone,
        ip_local               = args.local_ip,
        ip_remoto              = args.remote_ip,
        eth_physic             = args.eth_phy,
        use_internal_osc       = args.use_internal_osc,
        sdram_ratio            = args.sdram_rate,
        with_video_terminal    = args.with_video_terminal,
        with_video_framebuffer = args.with_video_framebuffer,
        **parser.soc_argdict
    )
    soc_inst.plataforma.add_extension(colorlight_i5._sdcard_pmod_io)
    if args.with_spi_sdcard:
        soc_inst.add_spi_sdcard()
    if args.with_sdcard:
        soc_inst.add_sdcard()

    construtor = Builder(soc_inst, **parser.builder_argdict)
    if args.build:
        construtor.build(**parser.toolchain_argdict)

    if args.load:
        programador = soc_inst.plataforma.create_programmer()
        programador.load_bitstream(construtor.get_bitstream_filename(mode="sram"))

if __name__ == "__main__":
    executar_main()