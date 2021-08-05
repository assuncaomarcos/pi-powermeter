#!/usr/bin/env python
"""
================================================
Script that measures the voltage of an ADC and
a differential ADC anc computes the amount of
power drawn by four USB ports
================================================
Author: Marcos Dias de Assuncao
"""

from __future__ import absolute_import, unicode_literals
from argparse import ArgumentParser
import time
import signal
import sys

_r = [0.1, 0.1, 0.1]   # Values of the shunt resistors
_machines = ["pi-1", "pi-2", "pi-3"]

try:
    from ADCPi import ADCPi
    from ADCDifferentialPi import ADCDifferentialPi
except ImportError:
    print("Failed to import ADCPi from python system path")
    print("Importing from parent folder instead")
    try:
        import sys
        sys.path.append('..')
        from ADCPi import ADCPi
        from ADCDifferentialPi import ADCDifferentialPi
    except ImportError:
        raise ImportError(
            "Failed to import library from parent folder")

def parse_options():
    """Parse the command line options for the measurement application"""
    parser = ArgumentParser(description='Measures the power drawn by USB ports.')
    parser.add_argument('--frequency', dest='frequency', type=int, default=200,
                        help='the measurement frequency in milliseconds')

    parser.add_argument('--output', dest='output', type=str, required=True,
                        help='the path to the output file')

    args = parser.parse_args()
    return args

def measure(interval, out_file):
    '''
    Main program function
    '''

    # Differential ADC measuring the voltage drop across shunt resistors
    adc_diff = ADCDifferentialPi(0x68, 0x69, 16)
    adc_diff.set_conversion_mode(1)
    adc_diff.set_pga(1)

    # ADC measuring the value of the input voltage
    adc_in = ADCPi(0x6A, 0x6B, 16)
    adc_in.set_conversion_mode(1)
    adc_in.set_pga(1)

    out = open(out_file, 'w')
    out.write("timestamp " + (len(_machines) * "%s " % tuple(_machines)) + "\n")
    try:
        while True:
           in_volt = adc_in.read_voltage(1) # No need to measure every input
           power = []

           # irst measure and then compute the power
           for i in range(len(_machines)):
              power.append((adc_diff.read_voltage(i + 1) * in_volt) / _r[i])

           out.write(((len(_machines) + 1) * "%f " + "\n") % ((time.time(), ) + tuple(power)))
           time.sleep(interval)
    finally:
       out.close()


def signal_handler(signal, frame):
   print('Stopping...')
   sys.exit(0)


def main():
   opts = parse_options()
   signal.signal(signal.SIGINT, signal_handler)
   print("Measuring... (Press Ctrl+C to stop)")
   measure(opts.frequency / 1000.0, opts.output)


if __name__ == "__main__":
    main()
