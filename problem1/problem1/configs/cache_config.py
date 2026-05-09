# Cache Configuration Script for gem5
import os
import m5
from m5.objects import *

class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    def __init__(self, options=None):
        super(L1Cache, self).__init__()
    def connectCPU(self, cpu):
        raise NotImplementedError
    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports

class L1ICache(L1Cache):
    def __init__(self, options):
        super(L1ICache, self).__init__(options)
        self.size = options.l1i_size if options and options.l1i_size else '16kB'
        if options and options.l1i_assoc:
            self.assoc = options.l1i_assoc
    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

class L1DCache(L1Cache):
    def __init__(self, options):
        super(L1DCache, self).__init__(options)
        self.size = options.l1d_size if options and options.l1d_size else '16kB'
        if options and options.l1d_assoc:
            self.assoc = options.l1d_assoc
    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port

class L2Cache(Cache):
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    def __init__(self, options):
        super(L2Cache, self).__init__()
        self.size = options.l2_size if options and options.l2_size else '256kB'
        if options and options.l2_assoc:
            self.assoc = options.l2_assoc
    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports
    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]
system.cpu = RiscvTimingSimpleCPU()

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--l1i_size", type="string", default="16kB")
parser.add_option("--l1i_assoc", type="int", default=4)
parser.add_option("--l1d_size", type="string", default="16kB")
parser.add_option("--l1d_assoc", type="int", default=4)
parser.add_option("--l2_size", type="string", default="256kB")
parser.add_option("--l2_assoc", type="int", default=8)
parser.add_option("--binary", type="string", default="", help="Path to binary to execute")
(options, args) = parser.parse_args()

system.cpu.icache = L1ICache(options)
system.cpu.dcache = L1DCache(options)
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)
system.l2bus = L2XBar()
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)
system.l2cache = L2Cache(options)
system.l2cache.connectCPUSideBus(system.l2bus)
system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)
system.cpu.createInterruptController()
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports
system.system_port = system.membus.cpu_side_ports

thispath = os.path.dirname(os.path.realpath(__file__))
if options.binary:
    binary = options.binary
else:
    binary = os.path.join(thispath, "../../gem5/tests/test-progs/hello/bin/riscv/linux/hello")
system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()
print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %d because %s" % (m5.curTick(), exit_event.getCause()))
