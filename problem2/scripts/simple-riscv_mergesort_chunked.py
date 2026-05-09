# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This is the RISC-V equivalent to `simple.py` (which is designed to run using the
X86 ISA). More detailed documentation can be found in `simple.py`.
"""

import os
import argparse

# Parse command line arguments FIRST (before importing m5)
parser = argparse.ArgumentParser(description='RISC-V Merge Sort Chunked Simulation')
parser.add_argument('--l1i_size', type=str, default='32KiB', help='L1 instruction cache size')
parser.add_argument('--l1d_size', type=str, default='64KiB', help='L1 data cache size')
parser.add_argument('--l2_size', type=str, default='512KiB', help='L2 cache size')
parser.add_argument('--l1_assoc', type=int, default=8, help='L1 cache associativity')
parser.add_argument('--l2_assoc', type=int, default=16, help='L2 cache associativity')
args = parser.parse_args()

# NOW import m5 and set the output directory
import m5
from m5.objects import *

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]
system.cpu = RiscvTimingSimpleCPU()



system.cpu.createInterruptController()

# FIXED: Create mem_ctrl FIRST, then connect everything
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]

class L1Cache(Cache):
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    def __init__(self, size, assoc):
        super(L1Cache, self).__init__()
        self.size = size
        self.assoc = assoc

class L2Cache(Cache):
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    def __init__(self, size, assoc):
        super(L2Cache, self).__init__()
        self.size = size
        self.assoc = assoc

# Create caches + buses (mem_ctrl already exists)
system.membus = SystemXBar()
system.l2_xbar = SystemXBar()

system.cpu.icache = L1Cache(args.l1i_size, args.l1_assoc)
system.cpu.dcache = L1Cache(args.l1d_size, args.l1_assoc)
system.l2cache = L2Cache(args.l2_size, args.l2_assoc)

# L1 → L2_XBar
system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side
system.cpu.icache.mem_side = system.l2_xbar.cpu_side_ports
system.cpu.dcache.mem_side = system.l2_xbar.cpu_side_ports

# L2 → Main bus
system.l2cache.cpu_side = system.l2_xbar.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# Main bus → DRAM (NOW mem_ctrl exists)
system.mem_ctrl.port = system.membus.mem_side_ports


system.system_port = system.membus.cpu_side_ports

import os

thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "mergesort_c",
)

if not os.path.exists(binary):
    print(f"Binary not found: {binary}")
    print("Please compile mergesort_chunked.c first")
    exit(1)

# Set up the workload
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

m5.stats.reset()
root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation!")
print(f"Binary: {binary}")
print(f"L1I: {args.l1i_size}, L1D: {args.l1d_size}, L2: {args.l2_size}")
print(f"L1 Assoc: {args.l1_assoc}, L2 Assoc: {args.l2_assoc}")

exit_event = m5.simulate()
m5.stats.dump()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
